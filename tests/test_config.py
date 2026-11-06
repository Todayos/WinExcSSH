"""Configuration checks that never contact a remote server."""

import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from config import config as config_module
from config.config import Config
from units.yaml_helper import YamlHelper


class ConfigTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.default_path = self.directory / "config.yml"
        self.data = {
            "HostInfo": {"IP": "ssh.example.com", "Port": 22},
            "UserInfo": {"Username": "deploy", "Password": ""},
            "PceKeys": ["my-service"],
            "ServicePath": "/opt/my-service",
            "StartCommand": "./start.sh",
            "StopCommand": "./stop.sh",
        }
        self.write(self.default_path, self.data)
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith(("SSH_SERVICE_RUNNER_", "WINEXCSSH_"))}
        environment_patch = patch.dict(os.environ, environment, clear=True)
        environment_patch.start()
        self.addCleanup(environment_patch.stop)
        file_patch = patch.object(config_module, "__file__", str(self.directory / "config.py"))
        file_patch.start()
        self.addCleanup(file_patch.stop)

    def write(self, path, data):
        path.write_text(yaml.safe_dump(data), encoding="utf-8")

    def test_default_file_is_relative_to_module(self):
        config = Config()
        self.assertEqual(config.config_path, self.default_path)
        self.assertEqual(config.host_info["IP"], "ssh.example.com")
        self.assertEqual(config.service_path, "/opt/my-service")

    def test_local_file_takes_precedence(self):
        data = copy.deepcopy(self.data)
        data["HostInfo"]["IP"] = "local.example.com"
        self.write(self.directory / "config.local.yml", data)
        self.assertEqual(Config().host_info["IP"], "local.example.com")

    def test_selected_local_file_is_not_merged_with_default_settings(self):
        data = copy.deepcopy(self.data)
        del data["ServicePath"]
        self.write(self.directory / "config.local.yml", data)
        with self.assertRaisesRegex(ValueError, "ServicePath must be a non-empty string"):
            Config()

    def test_explicit_path_takes_precedence_over_environment_and_local_file(self):
        self.write(self.directory / "config.local.yml", self.data)
        os.environ["SSH_SERVICE_RUNNER_CONFIG"] = str(self.directory / "missing.yml")
        self.assertEqual(Config(self.default_path).config_path, self.default_path)

    def test_environment_selects_a_complete_file(self):
        path = self.directory / "custom.yml"
        data = copy.deepcopy(self.data)
        data["HostInfo"]["IP"] = "custom.example.com"
        self.write(path, data)
        os.environ["SSH_SERVICE_RUNNER_CONFIG"] = str(path)
        self.assertEqual(Config().host_info["IP"], "custom.example.com")

    def test_environment_overrides_all_settings(self):
        os.environ.update({
            "SSH_SERVICE_RUNNER_HOST": "environment.example.com",
            "SSH_SERVICE_RUNNER_PORT": "2222",
            "SSH_SERVICE_RUNNER_USERNAME": "operator",
            "SSH_SERVICE_RUNNER_PASSWORD": "test-only-password",
            "SSH_SERVICE_RUNNER_PROCESS_KEYWORDS": '["worker", "scheduler"]',
            "SSH_SERVICE_RUNNER_SERVICE_PATH": "/srv/service",
            "SSH_SERVICE_RUNNER_START_COMMAND": "./run.sh",
            "SSH_SERVICE_RUNNER_STOP_COMMAND": "./halt.sh",
        })
        config = Config()
        self.assertEqual(config.host_info, {"IP": "environment.example.com", "Port": 2222})
        self.assertEqual(config.user_info, {"Username": "operator", "Password": "test-only-password"})
        self.assertEqual(config.process_keywords, ["worker", "scheduler"])
        self.assertEqual(config.service_path, "/srv/service")
        self.assertEqual(config.start_command, "./run.sh")
        self.assertEqual(config.stop_command, "./halt.sh")

    def test_legacy_environment_is_supported_but_current_prefix_wins(self):
        os.environ["WINEXCSSH_HOST"] = "legacy.example.com"
        self.assertEqual(Config().host_info["IP"], "legacy.example.com")
        os.environ["SSH_SERVICE_RUNNER_HOST"] = "current.example.com"
        self.assertEqual(Config().host_info["IP"], "current.example.com")

    def test_empty_password_override_takes_precedence(self):
        data = copy.deepcopy(self.data)
        data["UserInfo"]["Password"] = "test-only-file-password"
        self.write(self.default_path, data)
        os.environ["WINEXCSSH_PASSWORD"] = "test-only-legacy-password"
        os.environ["SSH_SERVICE_RUNNER_PASSWORD"] = ""
        self.assertEqual(Config().user_info["Password"], "")

    def test_defaults_preserve_empty_password_and_process_checks(self):
        data = copy.deepcopy(self.data)
        del data["HostInfo"]["Port"]
        del data["UserInfo"]["Password"]
        del data["PceKeys"]
        self.write(self.default_path, data)
        config = Config()
        self.assertEqual(config.host_info["Port"], 22)
        self.assertEqual(config.user_info["Password"], "")
        self.assertEqual(config.process_keywords, [])

    def test_invalid_ports_are_rejected_without_echoing_values(self):
        for value in (True, 0, 65536, 22.5, "invalid-port", None):
            with self.subTest(value=value):
                data = copy.deepcopy(self.data)
                data["HostInfo"]["Port"] = value
                self.write(self.default_path, data)
                with self.assertRaisesRegex(ValueError, "HostInfo.Port must be an integer"):
                    Config()

    def test_required_fields_are_validated(self):
        for section, key in (("HostInfo", "IP"), ("UserInfo", "Username"),
                             (None, "ServicePath"), (None, "StartCommand"), (None, "StopCommand")):
            with self.subTest(key=key):
                data = copy.deepcopy(self.data)
                target = data if section is None else data[section]
                target[key] = " "
                self.write(self.default_path, data)
                with self.assertRaisesRegex(ValueError, "must be a non-empty string"):
                    Config()

    def test_invalid_structure_and_password_are_rejected(self):
        invalid = [[], None, {**self.data, "HostInfo": []}, {**self.data, "UserInfo": []}]
        password_data = copy.deepcopy(self.data)
        password_data["UserInfo"]["Password"] = 246810
        invalid.append(password_data)
        for data in invalid:
            with self.subTest(data_type=type(data).__name__):
                self.write(self.default_path, data)
                with self.assertRaises(ValueError) as result:
                    Config()
                self.assertNotIn("246810", str(result.exception))
                self.assertTrue(str(result.exception).isascii())

    def test_invalid_process_keywords_are_rejected(self):
        for value in ("worker", [1], [""], None):
            with self.subTest(value=value):
                data = copy.deepcopy(self.data)
                data["PceKeys"] = value
                self.write(self.default_path, data)
                with self.assertRaisesRegex(ValueError, "PceKeys must be a list"):
                    Config()

    def test_process_environment_requires_json_array(self):
        for value in ("not-json", '"worker"', '[""]'):
            with self.subTest(value=value):
                os.environ["SSH_SERVICE_RUNNER_PROCESS_KEYWORDS"] = value
                with self.assertRaises(ValueError):
                    Config()

    def test_missing_config_has_english_error(self):
        with self.assertRaisesRegex(FileNotFoundError, "Configuration file not found"):
            Config(self.directory / "missing.yml")

    def test_yaml_python_tags_are_not_loaded(self):
        self.default_path.write_text("!!python/tuple [1, 2]", encoding="utf-8")
        with self.assertRaises(yaml.constructor.ConstructorError):
            YamlHelper.parser_yaml(self.default_path)


if __name__ == "__main__":
    unittest.main()
