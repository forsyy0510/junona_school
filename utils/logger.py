"""
Централизованная система логирования
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name='site_junona', log_file='logs/app.log', level=logging.INFO):
    """
    Настраивает и возвращает логгер
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу лога
        level: Уровень логирования
    
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logger()

