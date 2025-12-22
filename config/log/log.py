import logging
from logging.handlers import RotatingFileHandler
import os

"""
日志管理器
"""
logg = ''

class LogManager:
    def __init__(self, log_file_path: str, log_level: int = logging.DEBUG):
        self.log_file_path = log_file_path
        self.log_level = log_level
        self.logger = self.setup_logger()
        self.logger.info("日志初始化完成")

        
    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(self.log_level)

        if self.log_file_path:  # 如果指定了日志文件路径
            # 创建日志文件
            file_dir = os.path.dirname(self.log_file_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)

        if not logger.handlers:
            # 使用 RotatingFileHandler 实现日志轮转
            file_handler = RotatingFileHandler(
                self.log_file_path,
                maxBytes=1024*1024,  # 每个日志文件最大1MB
                backupCount=3,  # 保留3个备份文件
                encoding='utf-8'  # 设置编码为UTF-8
            )
            file_handler.setLevel(self.log_level)

            console_handler = logging.StreamHandler()
            
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)


            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        
        return logger

        # @property
        # def get_logger(self):
        #     return self.logger

