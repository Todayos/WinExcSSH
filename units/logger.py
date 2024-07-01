import logging
import os


file_path = os.path.dirname(__file__)


# 创建一个Logger对象
logger = logging.getLogger()
logger.setLevel(logging.INFO)

log_path = os.path.join(os.path.dirname(file_path), "logs/tfs.log")
# if not os.path.exists(log_path):
#     os.mkdir(log_path)

# 创建一个文件处理器
file_handler = logging.FileHandler(log_path, mode="a")

# 创建一个日志格式化器
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 将文件处理器添加到Logger中
logger.addHandler(file_handler)