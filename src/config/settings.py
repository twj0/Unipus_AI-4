#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

@dataclass
class BrowserConfig:
    """浏览器配置"""
    name: str = "chromium"  # chromium, firefox, webkit
    headless: bool = False
    slow_mo: int = 100
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = ""
    
@dataclass
class DelayConfig:
    """延迟配置"""
    page_load: float = 2.0
    element_wait: float = 1.0
    click_delay: float = 0.5
    type_delay: float = 0.1
    video_check: float = 3.0
    retry_delay: float = 2.0

@dataclass
class VideoConfig:
    """视频配置"""
    auto_play: bool = True
    default_speed: float = 2.0
    speed_options: list = field(default_factory=lambda: [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0])
    muted: bool = True
    skip_ads: bool = True

@dataclass
class AnswerConfig:
    """答题配置"""
    auto_submit: bool = True
    show_preview: bool = True
    confirm_delay: float = 0.5
    max_retries: int = 3
    skip_completed: bool = True

@dataclass
class UIConfig:
    """界面配置"""
    theme: str = "light"  # light, dark
    language: str = "zh"  # zh, en
    window_width: int = 800
    window_height: int = 600
    always_on_top: bool = False

@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    rotation: str = "10 MB"
    retention: str = "7 days"
    console_output: bool = True
    file_output: bool = True

class Settings:
    """配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_file = config_file or self.project_root / "config" / "config.yaml"
        
        # 基础配置
        self.app_name = "U校园自动化框架"
        self.version = "1.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 加载配置文件
        self._load_config()
        
        # 初始化各模块配置
        self.browser = BrowserConfig(**self.config.get("browser", {}))
        self.delays = DelayConfig(**self.config.get("delays", {}))
        self.video = VideoConfig(**self.config.get("video", {}))
        self.answer = AnswerConfig(**self.config.get("answer", {}))
        self.ui = UIConfig(**self.config.get("ui", {}))
        self.log = LogConfig(**self.config.get("log", {}))
        
        # U校园相关配置
        self.ucampus_base_url = "https://ucontent.unipus.cn"
        self.ucampus_login_url = "https://sso.unipus.cn/sso/login"
        
        # 用户凭据
        self.username = os.getenv("UCAMPUS_USERNAME", "")
        self.password = os.getenv("UCAMPUS_PASSWORD", "")
        
        # 题库配置
        self.question_bank_url = "https://raw.githubusercontent.com/twj0/Unipus_AI-4/refs/heads/main/U%E6%A0%A1%E5%9B%AD%20%E6%96%B0%E4%B8%80%E4%BB%A3%E5%A4%A7%E5%AD%A6%E8%8B%B1%E8%AF%AD%20%E7%BB%BC%E5%90%88%E6%95%99%E7%A8%8B1%E8%8B%B1%E8%AF%AD%E9%A2%98%E5%BA%93.json"
        self.local_question_bank = self.project_root / "data" / "question_bank.json"
        
        # 数据目录
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.screenshots_dir = self.project_root / "screenshots"
        
        # 创建必要目录
        self._create_directories()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
            else:
                self.config = {}
                # 创建默认配置文件
                self._create_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config = {}
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "browser": {
                "name": "chromium",
                "headless": False,
                "slow_mo": 100,
                "timeout": 30000
            },
            "delays": {
                "page_load": 2.0,
                "element_wait": 1.0,
                "click_delay": 0.5,
                "type_delay": 0.1
            },
            "video": {
                "auto_play": True,
                "default_speed": 2.0,
                "muted": True
            },
            "answer": {
                "auto_submit": True,
                "show_preview": True,
                "max_retries": 3
            },
            "ui": {
                "theme": "light",
                "language": "zh",
                "window_width": 800,
                "window_height": 600
            },
            "log": {
                "level": "INFO",
                "console_output": True,
                "file_output": True
            }
        }
        
        try:
            os.makedirs(self.config_file.parent, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
            self.config = default_config
        except Exception as e:
            print(f"创建默认配置文件失败: {e}")
    
    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.screenshots_dir,
            self.project_root / "config",
            self.project_root / "tampermonkey"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = {
                "browser": {
                    "name": self.browser.name,
                    "headless": self.browser.headless,
                    "slow_mo": self.browser.slow_mo,
                    "timeout": self.browser.timeout
                },
                "delays": {
                    "page_load": self.delays.page_load,
                    "element_wait": self.delays.element_wait,
                    "click_delay": self.delays.click_delay,
                    "type_delay": self.delays.type_delay
                },
                "video": {
                    "auto_play": self.video.auto_play,
                    "default_speed": self.video.default_speed,
                    "muted": self.video.muted
                },
                "answer": {
                    "auto_submit": self.answer.auto_submit,
                    "show_preview": self.answer.show_preview,
                    "max_retries": self.answer.max_retries
                },
                "ui": {
                    "theme": self.ui.theme,
                    "language": self.ui.language,
                    "window_width": self.ui.window_width,
                    "window_height": self.ui.window_height
                },
                "log": {
                    "level": self.log.level,
                    "console_output": self.log.console_output,
                    "file_output": self.log.file_output
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
