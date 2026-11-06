# encoding: utf-8

"""
@Author: Cooper
@File: yaml_helper.py
@Modify Time: 2024/3/21 10:24
@Description:
"""

import os
import yaml


class YamlHelper:

    def __init__(self):
        pass

    @staticmethod
    def parser_yaml(yaml_path: str):
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
        with open(yaml_path, mode="r", encoding="utf-8") as f:
            yaml_data = f.read()
        yaml_config = yaml.safe_load(yaml_data)
        return yaml_config

