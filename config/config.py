# encoding: utf-8
"""Load portable settings without committing local credentials."""

import json
import os
from pathlib import Path

if __package__ and "." in __package__:
    from ..units.yaml_helper import YamlHelper
else:
    from units.yaml_helper import YamlHelper


def environment_setting(name):
    """Prefer the current project prefix while accepting legacy environments."""
    return os.environ.get(f"SSH_SERVICE_RUNNER_{name}", os.environ.get(f"WINEXCSSH_{name}"))


class Config:
    def __init__(self, config_path=None):
        config_dir = Path(__file__).resolve().parent
        selected_path = config_path or environment_setting("CONFIG")
        if selected_path is None:
            local_path = config_dir / "config.local.yml"
            selected_path = local_path if local_path.is_file() else config_dir / "config.yml"
        self.config_path = Path(selected_path).expanduser()
        self.config = YamlHelper.parser_yaml(self.config_path)
        if not isinstance(self.config, dict):
            raise ValueError("Configuration must be a YAML mapping.")

        for section in ("HostInfo", "UserInfo"):
            value = self.config.setdefault(section, {})
            if not isinstance(value, dict):
                raise ValueError(f"{section} must be a YAML mapping.")

        environment_fields = {
            "HOST": ("HostInfo", "IP"),
            "PORT": ("HostInfo", "Port"),
            "USERNAME": ("UserInfo", "Username"),
            "PASSWORD": ("UserInfo", "Password"),
            "SERVICE_PATH": (None, "ServicePath"),
            "START_COMMAND": (None, "StartCommand"),
            "STOP_COMMAND": (None, "StopCommand"),
        }
        for variable, (section, key) in environment_fields.items():
            value = environment_setting(variable)
            if value is not None:
                target = self.config if section is None else self.config[section]
                target[key] = value
        keywords = environment_setting("PROCESS_KEYWORDS")
        if keywords is not None:
            try:
                self.config["PceKeys"] = json.loads(keywords)
            except json.JSONDecodeError:
                raise ValueError("SSH_SERVICE_RUNNER_PROCESS_KEYWORDS must be a JSON array of strings.") from None

        self.host_info: dict = self.config["HostInfo"]
        self.user_info: dict = self.config["UserInfo"]
        self.host_info.setdefault("Port", 22)
        self.user_info.setdefault("Password", "")
        self.service_path = self.config.get("ServicePath")
        self.process_keywords = self.config.get("PceKeys", [])
        self.start_command = self.config.get("StartCommand")
        self.stop_command = self.config.get("StopCommand")
        self._validate()

    def _validate(self):
        required_strings = {
            "HostInfo.IP": self.host_info.get("IP"),
            "UserInfo.Username": self.user_info.get("Username"),
            "ServicePath": self.service_path,
            "StartCommand": self.start_command,
            "StopCommand": self.stop_command,
        }
        for field, value in required_strings.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field} must be a non-empty string. "
                    "Update your local configuration or SSH_SERVICE_RUNNER_* environment variables."
                )
        port = self.host_info["Port"]
        if isinstance(port, bool) or not isinstance(port, (str, int)):
            raise ValueError("HostInfo.Port must be an integer between 1 and 65535.")
        try:
            port = int(port)
        except ValueError:
            raise ValueError("HostInfo.Port must be an integer between 1 and 65535.") from None
        if not 1 <= port <= 65535:
            raise ValueError("HostInfo.Port must be an integer between 1 and 65535.")
        self.host_info["Port"] = port
        if not isinstance(self.user_info["Password"], str):
            raise ValueError("UserInfo.Password must be a string; quote passwords in YAML.")
        if not isinstance(self.process_keywords, list) or any(
            not isinstance(keyword, str) or not keyword.strip()
            for keyword in self.process_keywords
        ):
            raise ValueError("PceKeys must be a list of non-empty strings (an empty list is allowed).")
