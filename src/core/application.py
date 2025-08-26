#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序主类
"""

import asyncio
import sys
from typing import Optional
from pathlib import Path

from src.config.settings import Settings
from src.utils.logger import LoggerMixin
from src.automation.browser_manager import BrowserManager
from src.automation.ucampus_automation import UCampusAutomation
from src.ui.gui_interface import GUIInterface
from src.ui.cli_interface import CLIInterface
from src.core.task_manager import TaskManager
from src.data.question_bank import QuestionBank
from src.intelligence.smart_answering import SmartAnsweringStrategy

class UCampusApplication(LoggerMixin):
    """U校园自动化应用程序主类"""
    
    def __init__(self, settings: Settings):
        """
        初始化应用程序
        
        Args:
            settings: 配置对象
        """
        self.settings = settings
        self.browser_manager: Optional[BrowserManager] = None
        self.automation: Optional[UCampusAutomation] = None
        self.task_manager: Optional[TaskManager] = None
        self.question_bank: Optional[QuestionBank] = None
        self.smart_answering: Optional[SmartAnsweringStrategy] = None
        
        self.logger.info(f"初始化 {settings.app_name} v{settings.version}")
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化各个组件"""
        try:
            # 初始化题库
            self.question_bank = QuestionBank(self.settings)
            
            # 初始化任务管理器
            self.task_manager = TaskManager(self.settings)
            
            self.logger.info("组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    async def _initialize_browser(self):
        """初始化浏览器"""
        if self.browser_manager is None:
            self.browser_manager = BrowserManager(self.settings)
            await self.browser_manager.start()
            
            # 初始化自动化模块
            self.automation = UCampusAutomation(
                self.browser_manager,
                self.settings,
                self.question_bank
            )

            # 初始化智能答题策略
            self.smart_answering = SmartAnsweringStrategy(
                self.browser_manager,
                self.settings
            )
    
    def run_gui(self):
        """运行GUI模式"""
        try:
            self.logger.info("启动GUI界面")
            gui = GUIInterface(self.settings, self)
            gui.run()
            
        except Exception as e:
            self.logger.error(f"GUI模式运行失败: {e}")
            raise
    
    def run_cli(self):
        """运行CLI模式"""
        try:
            self.logger.info("启动CLI界面")
            cli = CLIInterface(self.settings, self)
            cli.run()
            
        except Exception as e:
            self.logger.error(f"CLI模式运行失败: {e}")
            raise
    
    async def run_auto(self):
        """运行自动模式"""
        try:
            self.logger.info("启动自动模式")
            
            # 初始化浏览器
            await self._initialize_browser()
            
            # 执行自动化任务
            await self.automation.run_auto_mode()
            
        except Exception as e:
            self.logger.error(f"自动模式运行失败: {e}")
            raise
        finally:
            await self.cleanup()
    
    def run_test(self):
        """运行测试模式"""
        try:
            self.logger.info("启动测试模式")
            
            # 运行各种测试
            self._run_component_tests()
            
        except Exception as e:
            self.logger.error(f"测试模式运行失败: {e}")
            raise
    
    def _run_component_tests(self):
        """运行组件测试"""
        self.logger.info("开始组件测试")
        
        # 测试配置
        self.logger.info("测试配置模块...")
        assert self.settings.app_name == "U校园自动化框架"
        self.logger.info("✅ 配置模块测试通过")
        
        # 测试题库
        self.logger.info("测试题库模块...")
        assert self.question_bank is not None
        self.logger.info("✅ 题库模块测试通过")
        
        # 测试任务管理器
        self.logger.info("测试任务管理器...")
        assert self.task_manager is not None
        self.logger.info("✅ 任务管理器测试通过")
        
        self.logger.info("所有组件测试通过")
    
    async def start_automation(self, target_url: Optional[str] = None):
        """
        启动自动化任务
        
        Args:
            target_url: 目标URL
        """
        try:
            # 初始化浏览器
            await self._initialize_browser()
            
            # 导航到目标页面
            if target_url:
                await self.automation.navigate_to(target_url)
            else:
                await self.automation.navigate_to_login()
            
            # 开始自动化流程
            await self.automation.start_automation()
            
        except Exception as e:
            self.logger.error(f"启动自动化失败: {e}")
            raise
    
    async def stop_automation(self):
        """停止自动化任务"""
        try:
            if self.automation:
                await self.automation.stop_automation()
            self.logger.info("自动化任务已停止")

        except Exception as e:
            self.logger.error(f"停止自动化失败: {e}")

    async def start_intelligent_answering(self, target_url: Optional[str] = None):
        """
        启动智能答题模式

        Args:
            target_url: 目标URL
        """
        try:
            # 初始化浏览器
            await self._initialize_browser()

            # 导航到目标页面
            if target_url:
                await self.automation.navigate_to(target_url)
            else:
                await self.automation.navigate_to_login()
                # 登录
                if not await self.automation.login():
                    raise RuntimeError("登录失败")

            self.logger.info("开始智能答题模式")

            # 使用智能答题策略处理题目
            result = await self.smart_answering.process_question_intelligently()

            if result['success']:
                self.logger.success(f"智能答题成功: {result['strategy']}")
                return result
            else:
                self.logger.warning(f"智能答题失败: {result.get('reason', 'unknown')}")
                return result

        except Exception as e:
            self.logger.error(f"智能答题失败: {e}")
            raise

    async def batch_intelligent_answering(self, unit_range: Optional[range] = None):
        """
        批量智能答题

        Args:
            unit_range: 单元范围，例如 range(1, 5) 表示Unit 1到Unit 4
        """
        try:
            # 初始化浏览器
            await self._initialize_browser()

            # 登录
            await self.automation.navigate_to_login()
            if not await self.automation.login():
                raise RuntimeError("登录失败")

            self.logger.info("开始批量智能答题")

            # 如果没有指定范围，默认处理Unit 1-8
            if unit_range is None:
                unit_range = range(1, 9)

            results = []

            for unit_num in unit_range:
                self.logger.info(f"处理 Unit {unit_num}")

                # 构造单元URL（这里需要根据实际的U校园URL结构调整）
                unit_url = f"{self.settings.ucampus_base_url}/#/course/unit/u{unit_num}"

                try:
                    # 导航到单元页面
                    await self.automation.navigate_to(unit_url)
                    await asyncio.sleep(3)

                    # 查找并处理该单元的所有任务
                    tasks = await self._find_unit_tasks()

                    for task_info in tasks:
                        try:
                            self.logger.info(f"处理任务: {task_info['name']}")

                            # 导航到任务页面
                            await self.automation.navigate_to(task_info['url'])
                            await asyncio.sleep(2)

                            # 智能处理题目
                            result = await self.smart_answering.process_question_intelligently()
                            result['unit'] = f"Unit {unit_num}"
                            result['task'] = task_info['name']
                            results.append(result)

                            # 等待一下再处理下一个任务
                            await asyncio.sleep(2)

                        except Exception as e:
                            self.logger.error(f"处理任务失败: {task_info['name']} - {e}")
                            results.append({
                                'success': False,
                                'unit': f"Unit {unit_num}",
                                'task': task_info['name'],
                                'error': str(e)
                            })

                except Exception as e:
                    self.logger.error(f"处理Unit {unit_num}失败: {e}")
                    results.append({
                        'success': False,
                        'unit': f"Unit {unit_num}",
                        'error': str(e)
                    })

            # 统计结果
            successful = sum(1 for r in results if r.get('success', False))
            total = len(results)

            self.logger.info(f"批量智能答题完成: {successful}/{total} 成功")

            return {
                'total': total,
                'successful': successful,
                'results': results,
                'success_rate': successful / total if total > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"批量智能答题失败: {e}")
            raise

    async def _find_unit_tasks(self) -> List[Dict[str, str]]:
        """查找单元中的所有任务"""
        try:
            tasks = await self.browser_manager.execute_script("""
                const tasks = [];

                // 查找任务链接
                const taskSelectors = [
                    'a[href*="iexplore"]',
                    'a[href*="unittest"]',
                    '.task-link',
                    '.lesson-link',
                    '[class*="task"] a',
                    '[class*="lesson"] a'
                ];

                for (const selector of taskSelectors) {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        const href = el.href;
                        const text = el.textContent.trim();

                        if (href && text && !tasks.some(t => t.url === href)) {
                            tasks.push({
                                name: text,
                                url: href
                            });
                        }
                    });
                }

                return tasks;
            """)

            return tasks or []

        except Exception as e:
            self.logger.error(f"查找单元任务失败: {e}")
            return []
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.smart_answering:
                await self.smart_answering.cleanup()

            if self.automation:
                await self.automation.cleanup()

            if self.browser_manager:
                await self.browser_manager.close()

            self.logger.info("资源清理完成")

        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")
    
    def get_status(self) -> dict:
        """获取应用状态"""
        status = {
            "app_name": self.settings.app_name,
            "version": self.settings.version,
            "browser_running": self.browser_manager is not None and self.browser_manager.is_running(),
            "automation_running": self.automation is not None and self.automation.is_running(),
            "task_count": self.task_manager.get_task_count() if self.task_manager else 0,
            "intelligent_answering_available": self.smart_answering is not None
        }

        # 添加智能答题统计
        if self.smart_answering:
            status["smart_answering_stats"] = self.smart_answering.get_strategy_stats()

        return status
    
    def __del__(self):
        """析构函数"""
        try:
            # 如果有异步资源需要清理，在这里处理
            if hasattr(self, 'browser_manager') and self.browser_manager:
                # 注意：这里不能直接调用async方法
                # 需要在适当的地方调用cleanup()
                pass
        except Exception:
            pass
