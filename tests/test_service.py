"""Regression checks for the existing SSH command and restart behavior."""

from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from core.service import Service
import start as launcher


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = Service("ssh.example.com", 22, "deploy", "test-only-password")

    def test_connect_requires_initialization_with_english_error(self):
        with self.assertRaisesRegex(Exception, "SSH client is not initialized"):
            self.service.connect()

    @patch("core.service.paramiko.SSHClient")
    def test_init_and_connect_preserve_connection_arguments(self, client_class):
        client = client_class.return_value
        self.assertIs(self.service.init(), client)
        self.assertIs(self.service.init(), client)
        client_class.assert_called_once_with()
        self.service.connect()
        client.connect.assert_called_once_with("ssh.example.com", 22, "deploy", "test-only-password", timeout=10)

    def test_authentication_error_is_english(self):
        from paramiko.ssh_exception import AuthenticationException

        self.service.ssh_client = Mock()
        self.service.ssh_client.connect.side_effect = AuthenticationException()
        with self.assertRaisesRegex(Exception, "SSH authentication failed"):
            self.service.connect()

    def test_process_count_heuristic_and_commands_are_preserved(self):
        self.service.ssh_client = Mock()
        self.service.ssh_client.exec_command.side_effect = [
            (None, BytesIO(b"worker\ngrep\nshell\n"), None),
            (None, BytesIO(b"grep\nshell\n"), None),
        ]
        result = self.service.checker_service(["worker", "missing"], log=False)
        self.assertEqual(result, (False, {"worker": 1, "missing": False}))
        self.assertEqual(self.service.ssh_client.exec_command.call_args_list,
                         [call("ps -ef|grep worker"), call("ps -ef|grep missing")])

    def test_execute_preserves_remote_shell_command_and_output(self):
        self.service.ssh_client = Mock()
        self.service.ssh_client.exec_command.return_value = (None, BytesIO(b"started\n"), None)
        result = self.service.execute("/opt/my-service", "./start.sh", log=False)
        self.assertEqual(result, "started\n")
        self.service.ssh_client.exec_command.assert_called_once_with("cd /opt/my-service ; ./start.sh")
        self.service.dispose()
        self.service.ssh_client.close.assert_called_once_with()


class LauncherTests(unittest.TestCase):
    @patch.object(launcher, "Service")
    @patch.object(launcher, "Config")
    def test_restart_order_is_preserved_when_process_check_fails(self, config_class, service_class):
        config_class.return_value = SimpleNamespace(
            host_info={"IP": "ssh.example.com", "Port": 22},
            user_info={"Username": "deploy", "Password": "test-only-password"},
            process_keywords=["worker"],
            service_path="/opt/my-service",
            start_command="./start.sh",
            stop_command="./stop.sh",
        )
        service = service_class.return_value
        service.checker_service.return_value = (False, {"worker": False})
        launcher.start()
        service_class.assert_called_once_with(ip="ssh.example.com", port=22, username="deploy", password="test-only-password")
        self.assertEqual(service.method_calls, [
            call.init(), call.connect(),
            call.checker_service(service_keywords=["worker"], log=False),
            call.execute(path="/opt/my-service", command="./stop.sh"),
            call.execute(path="/opt/my-service", command="./start.sh"),
            call.dispose(),
        ])

    @patch.object(launcher, "Service")
    @patch.object(launcher, "Config", side_effect=ValueError("Configuration is incomplete."))
    def test_invalid_configuration_does_not_create_an_ssh_client(self, config_class, service_class):
        with self.assertRaisesRegex(ValueError, "Configuration is incomplete"):
            launcher.start()
        service_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
