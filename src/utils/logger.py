#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional

def setup_logger(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
    console_output: bool = True,
    file_output: bool = True
) -> logger:
    """
    设置日志记录器
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        rotation: 日志轮转大小
        retention: 日志保留时间
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
    
    Returns:
        配置好的logger实例
    """
    
    # 移除默认处理器
    logger.remove()
    
    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 控制台输出
    if console_output:
        logger.add(
            sys.stdout,
            format=log_format,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # 文件输出
    if file_output:
        if log_file is None:
            project_root = Path(__file__).parent.parent.parent
            logs_dir = project_root / "logs"
            logs_dir.mkdir(exist_ok=True)
            log_file = logs_dir / "ucampus.log"
        
        logger.add(
            log_file,
            format=log_format,
            level=level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )
    
    return logger

class LoggerMixin:
    """日志混入类"""
    
    @property
    def logger(self):
        """获取logger实例"""
        if not hasattr(self, '_logger'):
            self._logger = logger.bind(name=self.__class__.__name__)
        return self._logger
