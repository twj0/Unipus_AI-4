#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园自动化框架安装脚本
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """打印横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║               🎓 U校园自动化框架安装程序                      ║
    ║                                                              ║
    ║                    Version 1.0.0                            ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"   当前版本: Python {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python版本检查通过: {version.major}.{version.minor}.{version.micro}")
    return True

def check_system():
    """检查系统信息"""
    print("🔍 检查系统信息...")
    
    system = platform.system()
    architecture = platform.architecture()[0]
    
    print(f"   操作系统: {system}")
    print(f"   架构: {architecture}")
    
    supported_systems = ["Windows", "Darwin", "Linux"]
    if system not in supported_systems:
        print(f"⚠️  警告: 未测试的操作系统 {system}")
    else:
        print("✅ 系统兼容性检查通过")
    
    return True

def install_dependencies():
    """安装依赖包"""
    print("📦 安装Python依赖包...")
    
    try:
        # 升级pip
        print("   升级pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # 安装依赖
        print("   安装项目依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        
        print("✅ Python依赖安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ 未找到requirements.txt文件")
        return False

def install_playwright():
    """安装Playwright浏览器"""
    print("🌐 安装Playwright浏览器...")
    
    try:
        # 安装浏览器
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                      check=True, capture_output=True)
        
        print("✅ Playwright浏览器安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 浏览器安装失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    print("📁 创建项目目录...")
    
    directories = [
        "data",
        "logs", 
        "screenshots",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   创建目录: {directory}")
    
    print("✅ 目录创建完成")
    return True

def create_env_file():
    """创建环境变量文件"""
    print("⚙️  创建环境配置文件...")
    
    env_file = Path(".env")
    if env_file.exists():
        print("   .env文件已存在，跳过创建")
        return True
    
    env_content = """# U校园自动化框架环境变量配置

# U校园登录凭据
UCAMPUS_USERNAME=your_username
UCAMPUS_PASSWORD=your_password

# 调试模式
DEBUG=false

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# 浏览器设置
BROWSER_HEADLESS=false
BROWSER_SLOW_MO=100

# 视频设置
VIDEO_SPEED=2.0
VIDEO_MUTED=true

# 答题设置
AUTO_SUBMIT=true
MAX_RETRIES=3
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ 环境配置文件创建完成")
        print("   请编辑 .env 文件设置您的用户名和密码")
        return True
        
    except Exception as e:
        print(f"❌ 创建环境文件失败: {e}")
        return False

def test_installation():
    """测试安装"""
    print("🧪 测试安装...")
    
    try:
        # 测试导入主要模块
        import playwright
        import yaml
        import requests
        import loguru
        
        print("✅ 模块导入测试通过")
        
        # 测试配置加载
        from src.config.settings import Settings
        settings = Settings()
        print("✅ 配置加载测试通过")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def print_usage_instructions():
    """打印使用说明"""
    instructions = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                        🎉 安装完成！                         ║
    ╠══════════════════════════════════════════════════════════════╣
    ║                                                              ║
    ║  📝 下一步操作:                                               ║
    ║                                                              ║
    ║  1. 编辑 .env 文件，设置您的U校园用户名和密码                  ║
    ║                                                              ║
    ║  2. 运行程序:                                                 ║
    ║     • GUI模式:    python main.py                            ║
    ║     • CLI模式:    python main.py cli                        ║
    ║     • 自动模式:   python main.py auto                       ║
    ║     • 测试模式:   python main.py test                       ║
    ║                                                              ║
    ║  3. 查看文档:                                                 ║
    ║     • README.md - 详细使用说明                               ║
    ║     • config/config.yaml - 配置文件说明                     ║
    ║                                                              ║
    ║  🔧 油猴脚本:                                                 ║
    ║     • tampermonkey/ucampus_helper.js - 完整版脚本            ║
    ║     • tampermonkey/ucampus_simple.js - 简化版脚本            ║
    ║                                                              ║
    ║  📞 获取帮助:                                                 ║
    ║     • 查看 README.md 中的故障排除部分                        ║
    ║     • 提交 GitHub Issue                                      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(instructions)

def main():
    """主函数"""
    print_banner()
    
    # 检查步骤
    steps = [
        ("检查Python版本", check_python_version),
        ("检查系统信息", check_system),
        ("安装Python依赖", install_dependencies),
        ("安装Playwright浏览器", install_playwright),
        ("创建项目目录", create_directories),
        ("创建环境配置", create_env_file),
        ("测试安装", test_installation)
    ]
    
    print("🚀 开始安装...\n")
    
    for step_name, step_func in steps:
        print(f"📋 {step_name}")
        if not step_func():
            print(f"\n❌ 安装失败: {step_name}")
            sys.exit(1)
        print()
    
    print_usage_instructions()

if __name__ == "__main__":
    main()
