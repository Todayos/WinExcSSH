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
            raise FileNotFoundError(f"文件路径【{yaml_path}】不存在, 请确认该路径是否正确")
        with open(yaml_path, mode="r", encoding="utf-8") as f:
            yaml_data = f.read()
        yaml_config = yaml.load(yaml_data, Loader=yaml.FullLoader)
        return yaml_config

