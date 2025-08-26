#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园自动化框架 - 主入口文件
Author: AI Assistant
Date: 2024-12-26
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.application import UCampusApplication
from src.utils.logger import setup_logger
from src.config.settings import Settings

def main():
    """主函数"""
    try:
        # 设置日志
        logger = setup_logger()
        logger.info("🎓 U校园自动化框架启动")
        
        # 加载配置
        settings = Settings()
        logger.info(f"配置加载完成: {settings.app_name} v{settings.version}")
        
        # 创建应用实例
        app = UCampusApplication(settings)
        
        # 启动应用
        if len(sys.argv) > 1:
            # 命令行模式
            command = sys.argv[1]
            if command == "gui":
                logger.info("启动GUI模式")
                app.run_gui()
            elif command == "cli":
                logger.info("启动CLI模式")
                app.run_cli()
            elif command == "auto":
                logger.info("启动自动模式")
                asyncio.run(app.run_auto())
            elif command == "smart":
                logger.info("启动智能答题模式")
                url = sys.argv[2] if len(sys.argv) > 2 else None
                asyncio.run(app.start_intelligent_answering(url))
            elif command == "batch":
                logger.info("启动批量智能答题模式")
                start_unit = int(sys.argv[2]) if len(sys.argv) > 2 else 1
                end_unit = int(sys.argv[3]) if len(sys.argv) > 3 else 8
                asyncio.run(app.batch_intelligent_answering(range(start_unit, end_unit + 1)))
            elif command == "test":
                logger.info("启动测试模式")
                app.run_test()
            else:
                print(f"未知命令: {command}")
                print_usage()
        else:
            # 默认启动GUI模式
            logger.info("启动默认GUI模式")
            app.run_gui()
            
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        raise
    finally:
        logger.info("程序退出")

def print_usage():
    """打印使用说明"""
    print("""
U校园自动化框架 - 使用说明

用法:
    python main.py [命令] [参数]

命令:
    gui                     启动图形界面模式 (默认)
    cli                     启动命令行模式
    auto                    启动自动模式
    smart [url]             启动智能答题模式
    batch [start] [end]     启动批量智能答题模式
    test                    启动测试模式

示例:
    python main.py                              # 启动GUI模式
    python main.py gui                          # 启动GUI模式
    python main.py cli                          # 启动CLI模式
    python main.py auto                         # 启动自动模式
    python main.py smart                        # 智能答题（自动登录）
    python main.py smart "https://..."          # 智能答题（指定URL）
    python main.py batch 1 5                    # 批量智能答题（Unit 1-5）
    python main.py test                         # 启动测试模式

智能答题功能:
    - smart: 单题智能答题，通过试答获取正确答案并缓存
    - batch: 批量智能答题，自动处理指定范围的所有单元
    - 支持答案缓存和智能重试机制
    - 无需依赖外部题库，动态获取最新答案

更多信息请查看 README.md
    """)

if __name__ == "__main__":
    main()
