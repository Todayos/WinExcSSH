# encoding: utf-8

"""
@Author: Cooper
@File: service.py
@Modify Time: 2024/7/1 11:32
@Description:
"""
import paramiko
if __package__ and "." in __package__:
    from ..units.logger import logger
else:
    from units.logger import logger


class Service:

    def __init__(self, ip: str, port: int, username: str, password: str, timeout: int = 10):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.ssh_client = None
        self.timeout = timeout

    def init(self):
        if self.ssh_client is None:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return self.ssh_client

    def connect(self):
        if self.ssh_client is None:
            raise Exception("SSH client is not initialized.")
        try:
            self.ssh_client.connect(self.ip, self.port, self.username, self.password, timeout=self.timeout)
        except paramiko.ssh_exception.AuthenticationException:
            raise Exception("SSH authentication failed. Check your username and password.")

    def checker_service(self, service_keywords: list, log: bool = True, decode: str = "UTF-8"):
        check: dict = {}
        success: bool = True
        for keyword in service_keywords:
            command = f"ps -ef|grep {keyword}"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            result = stdout.read().decode(decode)
            lines = result.split("\n")
            nums = len([i for i in lines if i])
            if log:
                logger.info(command)
                for line in lines:
                    if not line:
                        continue
                    logger.info(line)
            if nums > 2:
                check.update({keyword: nums - 2})
            else:
                success = False
                check.update({keyword: False})
        return success, check

    def execute(self, path: str, command: str, decode: str = "UTF-8", log: bool = True):
        command_str = f"cd {path} ; {command}"
        stdin, stdout, stderr = self.ssh_client.exec_command(command_str)
        result = stdout.read().decode(decode)
        if log:
            logger.info(result)
        return result

    def dispose(self):
        self.ssh_client.close()
