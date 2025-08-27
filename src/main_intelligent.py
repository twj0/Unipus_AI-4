#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园智能答题系统主程序
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.automation.browser_manager import BrowserManager
from src.config.settings import Settings
from src.modules.login_handler import LoginHandler
from src.modules.course_navigator import CourseNavigator
from src.modules.automation_controller import AutomationController
from src.utils.logger import LoggerMixin

class UCampusIntelligentSystem(LoggerMixin):
    """U校园智能答题系统主类"""
    
    def __init__(self):
        """初始化系统"""
        # 加载配置
        self.settings = Settings()
        
        # 初始化组件
        self.browser_manager = None
        self.login_handler = None
        self.course_navigator = None
        self.automation_controller = None
        
        # 系统状态
        self.is_running = False
        self.start_time = None
        
        self.logger.info("🚀 U校园智能答题系统初始化完成")
    
    async def run(self, username: str, password: str, course_name: str = None, max_questions: int = 50) -> Dict[str, Any]:
        """
        运行智能答题系统
        
        Args:
            username: 用户名
            password: 密码
            course_name: 课程名称
            max_questions: 最大题目数
        
        Returns:
            运行结果
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("🎯 启动U校园智能答题系统")
            self.logger.info("=" * 60)
            
            self.is_running = True
            self.start_time = time.time()
            
            # 第一步：初始化浏览器
            await self._initialize_browser()
            
            # 第二步：执行登录
            login_success = await self._perform_login(username, password)
            if not login_success:
                return self._create_error_result("登录失败")
            
            # 第三步：导航到课程
            if course_name:
                nav_success = await self._navigate_to_course(course_name)
                if not nav_success:
                    return self._create_error_result("课程导航失败")
            
            # 第四步：开始智能答题
            automation_result = await self._start_automation(max_questions)
            
            # 第五步：生成最终报告
            final_result = self._generate_final_result(automation_result)
            
            self.logger.info("=" * 60)
            self.logger.info("✅ U校园智能答题系统运行完成")
            self.logger.info("=" * 60)
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"系统运行异常: {e}")
            return self._create_error_result(f"系统异常: {e}")
        finally:
            await self._cleanup()
    
    async def _initialize_browser(self) -> None:
        """初始化浏览器"""
        try:
            self.logger.info("🌐 初始化浏览器...")
            
            self.browser_manager = BrowserManager(self.settings)
            await self.browser_manager.start()
            
            # 初始化其他组件
            self.login_handler = LoginHandler(self.browser_manager)
            self.course_navigator = CourseNavigator(self.browser_manager)
            self.automation_controller = AutomationController(self.browser_manager, self.settings)
            
            self.logger.info("✅ 浏览器初始化成功")
            
        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {e}")
            raise
    
    async def _perform_login(self, username: str, password: str) -> bool:
        """执行登录"""
        try:
            self.logger.info("🔐 开始登录流程...")
            
            login_success = await self.login_handler.login(username, password)
            
            if login_success:
                self.logger.info("✅ 登录成功")
                return True
            else:
                self.logger.error("❌ 登录失败")
                return False
                
        except Exception as e:
            self.logger.error(f"登录过程异常: {e}")
            return False
    
    async def _navigate_to_course(self, course_name: str) -> bool:
        """导航到课程"""
        try:
            self.logger.info(f"📚 导航到课程: {course_name}")
            
            nav_success = await self.course_navigator.navigate_to_course(course_name)
            
            if nav_success:
                self.logger.info("✅ 课程导航成功")
                return True
            else:
                self.logger.error("❌ 课程导航失败")
                return False
                
        except Exception as e:
            self.logger.error(f"课程导航异常: {e}")
            return False
    
    async def _start_automation(self, max_questions: int) -> Dict[str, Any]:
        """开始自动化答题"""
        try:
            self.logger.info(f"🤖 开始自动化答题，最大题目数: {max_questions}")
            
            automation_result = await self.automation_controller.start_automation(max_questions)
            
            return automation_result
            
        except Exception as e:
            self.logger.error(f"自动化答题异常: {e}")
            return {
                'success': False,
                'error': str(e),
                'report': {}
            }
    
    def _generate_final_result(self, automation_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终结果"""
        end_time = time.time()
        total_duration = end_time - (self.start_time or end_time)
        
        report = automation_result.get('report', {})
        
        # 输出详细报告
        self.logger.info("📊 最终报告:")
        self.logger.info(f"   总题目数: {report.get('total_questions', 0)}")
        self.logger.info(f"   成功答题: {report.get('successful_answers', 0)}")
        self.logger.info(f"   失败答题: {report.get('failed_answers', 0)}")
        self.logger.info(f"   成功率: {report.get('success_rate', '0%')}")
        self.logger.info(f"   总耗时: {total_duration:.1f}秒")
        self.logger.info(f"   错误数: {report.get('errors_count', 0)}")
        
        return {
            'success': automation_result.get('success', True),
            'total_duration': f"{total_duration:.1f}秒",
            'automation_report': report,
            'system_info': {
                'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time)),
                'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'browser': self.settings.browser.name if self.settings else 'unknown'
            }
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'success': False,
            'error': error_message,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    async def _cleanup(self) -> None:
        """清理资源"""
        try:
            self.is_running = False
            
            if self.browser_manager:
                await self.browser_manager.close()
                
            self.logger.info("🧹 资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")

async def main():
    """主函数"""
    try:
        # 配置参数
        config = {
            'username': '13874395640',  # 替换为实际用户名
            'password': '123456Unipus',  # 替换为实际密码
            'course_name': '新一代大学英语（提高篇）综合教程2',
            'max_questions': 30
        }
        
        # 创建并运行系统
        system = UCampusIntelligentSystem()
        result = await system.run(
            username=config['username'],
            password=config['password'],
            course_name=config['course_name'],
            max_questions=config['max_questions']
        )
        
        # 输出最终结果
        print("\n" + "=" * 60)
        print("🎉 U校园智能答题系统运行结果")
        print("=" * 60)
        
        if result['success']:
            print("✅ 系统运行成功")
            automation_report = result.get('automation_report', {})
            print(f"📊 处理题目: {automation_report.get('total_questions', 0)}")
            print(f"✅ 成功答题: {automation_report.get('successful_answers', 0)}")
            print(f"❌ 失败答题: {automation_report.get('failed_answers', 0)}")
            print(f"📈 成功率: {automation_report.get('success_rate', '0%')}")
            print(f"⏱️ 总耗时: {result.get('total_duration', '未知')}")
        else:
            print("❌ 系统运行失败")
            print(f"错误信息: {result.get('error', '未知错误')}")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
    except Exception as e:
        print(f"\n💥 程序异常: {e}")

if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行主程序
    asyncio.run(main())
