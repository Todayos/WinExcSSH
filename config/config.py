# encoding: utf-8

"""
@Author: Cooper
@File: config.py    
@Modify Time: 2024/7/1 11:20  
@Description: 
"""

import os
from WinExcSSH.units.yaml_helper import YamlHelper


class Config:

    def __init__(self):
        self.config = YamlHelper.parser_yaml(yaml_path=os.path.join(os.path.dirname(__file__), "config.yml"))
        self.host_info: dict = self.config["HostInfo"]
        self.user_info: dict = self.config["UserInfo"]
        self.tfiif_path: str = self.config["TfiifPath"]
        self.process_keywords: list = self.config["PceKeys"]
        self.start_command: str = self.config["StartCommand"]
        self.stop_command: str = self.config["StopCommand"]
