#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园智能答题系统简化测试脚本
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.automation.browser_manager import BrowserManager
    from src.config.settings import Settings
    from src.modules.login_handler import LoginHandler
    from src.modules.course_navigator import CourseNavigator
    from src.modules.automation_controller import AutomationController
    print("✅ 所有模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

class SimpleTestRunner:
    """简化测试运行器"""
    
    def __init__(self):
        self.settings = Settings()
        self.browser_manager = None
        self.test_results = []
    
    async def run_basic_test(self):
        """运行基础测试"""
        print("🧪 开始U校园智能答题系统基础测试")
        print("=" * 60)
        
        try:
            # 测试1：浏览器初始化
            await self._test_browser_initialization()
            
            # 测试2：登录功能
            await self._test_login_functionality()
            
            # 测试3：课程导航
            await self._test_course_navigation()
            
            # 测试4：智能答题
            await self._test_intelligent_answering()
            
            # 生成测试报告
            self._generate_simple_report()
            
        except Exception as e:
            print(f"💥 测试过程异常: {e}")
        finally:
            await self._cleanup()
    
    async def _test_browser_initialization(self):
        """测试浏览器初始化"""
        print("\n🌐 测试浏览器初始化...")
        
        try:
            self.browser_manager = BrowserManager(self.settings)
            await self.browser_manager.start()
            
            if self.browser_manager.is_running():
                self._add_result("浏览器初始化", True, "浏览器启动成功")
            else:
                self._add_result("浏览器初始化", False, "浏览器启动失败")
                
        except Exception as e:
            self._add_result("浏览器初始化", False, f"异常: {e}")
    
    async def _test_login_functionality(self):
        """测试登录功能"""
        print("\n🔐 测试登录功能...")
        
        if not self.browser_manager or not self.browser_manager.is_running():
            self._add_result("登录功能", False, "浏览器未运行")
            return
        
        try:
            login_handler = LoginHandler(self.browser_manager)
            
            # 测试登录页面访问
            success = await login_handler._navigate_to_login_page()
            
            if success:
                self._add_result("登录页面访问", True, "成功访问登录页面")
                
                # 测试登录表单填写（不实际提交）
                print("   📝 测试登录表单填写...")
                form_success = await login_handler._fill_login_form("test_user", "test_pass")
                
                if form_success:
                    self._add_result("登录表单填写", True, "表单填写功能正常")
                else:
                    self._add_result("登录表单填写", False, "表单填写失败")
            else:
                self._add_result("登录页面访问", False, "无法访问登录页面")
                
        except Exception as e:
            self._add_result("登录功能", False, f"异常: {e}")
    
    async def _test_course_navigation(self):
        """测试课程导航"""
        print("\n📚 测试课程导航...")
        
        if not self.browser_manager or not self.browser_manager.is_running():
            self._add_result("课程导航", False, "浏览器未运行")
            return
        
        try:
            course_navigator = CourseNavigator(self.browser_manager)
            
            # 测试主页访问
            success = await course_navigator._ensure_on_homepage()
            
            if success:
                self._add_result("主页访问", True, "成功访问主页")
                
                # 测试课程列表获取
                courses = await course_navigator._get_available_courses()
                
                if courses:
                    self._add_result("课程列表获取", True, f"找到 {len(courses)} 个课程")
                else:
                    self._add_result("课程列表获取", False, "未找到课程")
            else:
                self._add_result("主页访问", False, "无法访问主页")
                
        except Exception as e:
            self._add_result("课程导航", False, f"异常: {e}")
    
    async def _test_intelligent_answering(self):
        """测试智能答题"""
        print("\n🤖 测试智能答题...")
        
        if not self.browser_manager or not self.browser_manager.is_running():
            self._add_result("智能答题", False, "浏览器未运行")
            return
        
        try:
            automation_controller = AutomationController(self.browser_manager, self.settings)
            
            # 测试页面分析功能
            analysis_result = await automation_controller.question_analyzer.analyze_current_page()
            
            if analysis_result.get('success', False):
                page_type = analysis_result.get('page_type', 'unknown')
                self._add_result("页面分析", True, f"成功分析页面类型: {page_type}")
                
                # 测试答题策略
                if page_type != 'unknown':
                    self._add_result("答题策略", True, f"支持 {page_type} 类型题目")
                else:
                    self._add_result("答题策略", False, "未识别题目类型")
            else:
                self._add_result("页面分析", False, "页面分析失败")
                
        except Exception as e:
            self._add_result("智能答题", False, f"异常: {e}")
    
    def _add_result(self, test_name: str, success: bool, details: str):
        """添加测试结果"""
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'details': details
        })
        
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}: {details}")
    
    def _generate_simple_report(self):
        """生成简单报告"""
        print("\n" + "=" * 60)
        print("📊 U校园智能答题系统测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 测试概览:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过测试: {passed_tests}")
        print(f"   失败测试: {failed_tests}")
        print(f"   通过率: {pass_rate:.1f}%")
        
        print(f"\n📋 功能状态:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test_name']}: {result['details']}")
        
        print(f"\n💡 系统评估:")
        if pass_rate >= 80:
            print("   🎉 系统功能完整，可以正常使用")
        elif pass_rate >= 60:
            print("   👍 系统基本功能正常，部分功能需要优化")
        else:
            print("   ⚠️ 系统存在较多问题，需要进一步调试")
        
        print("=" * 60)
    
    async def _cleanup(self):
        """清理资源"""
        try:
            if self.browser_manager:
                await self.browser_manager.close()
            print("🧹 资源清理完成")
        except Exception as e:
            print(f"清理资源失败: {e}")

async def main():
    """主函数"""
    try:
        print("🚀 启动U校园智能答题系统简化测试")
        
        # 创建测试运行器
        test_runner = SimpleTestRunner()
        
        # 运行基础测试
        await test_runner.run_basic_test()
        
        print("\n🎯 测试完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n💥 测试异常: {e}")

if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行测试
    asyncio.run(main())
