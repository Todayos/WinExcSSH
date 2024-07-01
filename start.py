# encoding: utf-8

"""
@Author: Cooper
@File: start.py    
@Modify Time: 2024/7/1 11:31  
@Description: 
"""

from WinExcSSH.config.config import Config
from WinExcSSH.core.service import Service
from WinExcSSH.units.logger import logger


def start():
    config = Config()
    connect_info: dict = {
        "ip": config.host_info["IP"],
        "port": config.host_info["Port"],
        "username": config.user_info["Username"],
        "password": config.user_info["Password"]
    }
    service = Service(**connect_info)
    service.init()
    service.connect()
    success, result = service.checker_service(service_keywords=config.process_keywords, log=False)
    logger.info(result)
    service.execute(path=config.tfiif_path, command=config.stop_command)
    service.execute(path=config.tfiif_path, command=config.start_command)
    service.dispose()


if __name__ == "__main__":
    start()