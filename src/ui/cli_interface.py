#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI界面模块
"""

import asyncio
import sys
from typing import TYPE_CHECKING
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.live import Live
import click

from src.config.settings import Settings
from src.utils.logger import LoggerMixin
from src.core.task_manager import TaskStatus, TaskType

if TYPE_CHECKING:
    from src.core.application import UCampusApplication

class CLIInterface(LoggerMixin):
    """CLI界面类"""
    
    def __init__(self, settings: Settings, app: 'UCampusApplication'):
        """
        初始化CLI界面
        
        Args:
            settings: 配置对象
            app: 应用程序实例
        """
        self.settings = settings
        self.app = app
        self.console = Console()
        self.running = False
        
        self.logger.info("CLI界面初始化完成")
    
    def run(self):
        """运行CLI界面"""
        try:
            self.running = True
            self.console.print(f"[bold green]🎓 {self.settings.app_name} v{self.settings.version}[/bold green]")
            self.console.print("[dim]命令行界面模式[/dim]\n")
            
            # 显示主菜单
            self._show_main_menu()
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]用户中断程序[/yellow]")
        except Exception as e:
            self.logger.error(f"CLI运行失败: {e}")
            self.console.print(f"[red]错误: {e}[/red]")
        finally:
            self.running = False
    
    def _show_main_menu(self):
        """显示主菜单"""
        while self.running:
            self.console.print("\n[bold cyan]主菜单[/bold cyan]")
            
            menu_options = [
                "1. 🚀 开始自动化",
                "2. 🧠 智能答题",
                "3. 📋 任务管理",
                "4. ⚙️ 配置设置",
                "5. 📊 查看统计",
                "6. 📚 题库管理",
                "7. 🔧 系统信息",
                "0. 🚪 退出程序"
            ]
            
            for option in menu_options:
                self.console.print(f"  {option}")
            
            choice = Prompt.ask("\n请选择操作", choices=["0", "1", "2", "3", "4", "5", "6", "7"])

            if choice == "0":
                if Confirm.ask("确定要退出吗？"):
                    break
            elif choice == "1":
                self._automation_menu()
            elif choice == "2":
                self._intelligent_answering_menu()
            elif choice == "3":
                self._task_menu()
            elif choice == "4":
                self._config_menu()
            elif choice == "5":
                self._show_statistics()
            elif choice == "6":
                self._question_bank_menu()
            elif choice == "7":
                self._show_system_info()
    
    def _automation_menu(self):
        """自动化菜单"""
        self.console.print("\n[bold cyan]自动化控制[/bold cyan]")
        
        options = [
            "1. 🌐 自动登录并开始",
            "2. 🎯 指定URL开始",
            "3. ⏹️ 停止自动化",
            "4. 📸 截图",
            "0. 🔙 返回主菜单"
        ]
        
        for option in options:
            self.console.print(f"  {option}")
        
        choice = Prompt.ask("\n请选择操作", choices=["0", "1", "2", "3", "4"])
        
        if choice == "1":
            self._start_auto_login()
        elif choice == "2":
            self._start_with_url()
        elif choice == "3":
            self._stop_automation()
        elif choice == "4":
            self._take_screenshot()

    def _intelligent_answering_menu(self):
        """智能答题菜单"""
        self.console.print("\n[bold cyan]智能答题系统[/bold cyan]")

        options = [
            "1. 🧠 单题智能答题",
            "2. 🚀 批量智能答题",
            "3. 📊 查看智能答题统计",
            "4. 🔧 智能答题设置",
            "0. 🔙 返回主菜单"
        ]

        for option in options:
            self.console.print(f"  {option}")

        choice = Prompt.ask("\n请选择操作", choices=["0", "1", "2", "3", "4"])

        if choice == "1":
            self._single_intelligent_answering()
        elif choice == "2":
            self._batch_intelligent_answering()
        elif choice == "3":
            self._show_intelligent_stats()
        elif choice == "4":
            self._intelligent_settings()

    def _single_intelligent_answering(self):
        """单题智能答题"""
        url = Prompt.ask("请输入题目页面URL", default=self.settings.ucampus_base_url)

        if not url:
            self.console.print("[red]URL不能为空[/red]")
            return

        self.console.print(f"[yellow]正在进行智能答题: {url}[/yellow]")

        try:
            result = asyncio.run(self._run_intelligent_answering_async(url))

            if result['success']:
                self.console.print(f"[green]✅ 智能答题成功！[/green]")
                self.console.print(f"   策略: {result['strategy']}")
                self.console.print(f"   答案: {result.get('answer', 'N/A')}")
                if result.get('submitted'):
                    self.console.print("   状态: 已提交")
            else:
                self.console.print(f"[red]❌ 智能答题失败[/red]")
                self.console.print(f"   原因: {result.get('reason', 'unknown')}")

        except Exception as e:
            self.console.print(f"[red]智能答题失败: {e}[/red]")

    def _batch_intelligent_answering(self):
        """批量智能答题"""
        self.console.print("\n[bold cyan]批量智能答题设置[/bold cyan]")

        start_unit = Prompt.ask("起始单元", default="1")
        end_unit = Prompt.ask("结束单元", default="8")

        try:
            start_num = int(start_unit)
            end_num = int(end_unit)

            if start_num < 1 or end_num < start_num or end_num > 20:
                self.console.print("[red]请输入有效的单元范围 (1-20)[/red]")
                return

            if not Confirm.ask(f"确定要处理 Unit {start_num} 到 Unit {end_num} 吗？"):
                return

            self.console.print(f"[yellow]开始批量智能答题: Unit {start_num} - {end_num}[/yellow]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            ) as progress:

                task = progress.add_task("批量智能答题中...", total=100)

                result = asyncio.run(self._run_batch_intelligent_answering_async(range(start_num, end_num + 1)))

                progress.update(task, completed=100)

                # 显示结果
                table = Table(title="批量智能答题结果")
                table.add_column("项目", style="cyan")
                table.add_column("数量", style="green")

                table.add_row("总任务数", str(result['total']))
                table.add_row("成功数", str(result['successful']))
                table.add_row("失败数", str(result['total'] - result['successful']))
                table.add_row("成功率", f"{result['success_rate']:.1%}")

                self.console.print(table)

        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
        except Exception as e:
            self.console.print(f"[red]批量智能答题失败: {e}[/red]")

    def _show_intelligent_stats(self):
        """显示智能答题统计"""
        if not self.app.smart_answering:
            self.console.print("[red]智能答题系统未初始化[/red]")
            return

        stats = self.app.smart_answering.get_strategy_stats()

        # 策略统计
        strategy_stats = stats.get('strategy_stats', {})
        table = Table(title="智能答题策略统计")
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="green")

        table.add_row("缓存命中", str(strategy_stats.get('cache_hits', 0)))
        table.add_row("缓存未命中", str(strategy_stats.get('cache_misses', 0)))
        table.add_row("提取尝试", str(strategy_stats.get('extractions_attempted', 0)))
        table.add_row("提取成功", str(strategy_stats.get('extractions_successful', 0)))
        table.add_row("答案验证", str(strategy_stats.get('answers_verified', 0)))
        table.add_row("缓存命中率", f"{stats.get('cache_hit_rate', 0):.1%}")
        table.add_row("提取成功率", f"{stats.get('extraction_success_rate', 0):.1%}")

        self.console.print(table)

        # 缓存统计
        cache_stats = stats.get('cache_stats', {})
        if cache_stats:
            cache_table = Table(title="答案缓存统计")
            cache_table.add_column("项目", style="cyan")
            cache_table.add_column("数量", style="green")

            cache_table.add_row("总缓存条目", str(cache_stats.get('total_entries', 0)))
            cache_table.add_row("已验证条目", str(cache_stats.get('verified_entries', 0)))
            cache_table.add_row("验证率", f"{cache_stats.get('verification_rate', 0):.1%}")
            cache_table.add_row("缓存大小", f"{cache_stats.get('cache_size_mb', 0):.2f} MB")

            self.console.print(cache_table)

    def _intelligent_settings(self):
        """智能答题设置"""
        self.console.print("\n[bold cyan]智能答题设置[/bold cyan]")

        if not self.app.smart_answering:
            self.console.print("[red]智能答题系统未初始化[/red]")
            return

        options = [
            "1. 设置提取重试次数",
            "2. 设置置信度阈值",
            "3. 启用/禁用模糊匹配",
            "4. 启用/禁用自动验证",
            "5. 清理缓存",
            "0. 返回"
        ]

        for option in options:
            self.console.print(f"  {option}")

        choice = Prompt.ask("\n请选择操作", choices=["0", "1", "2", "3", "4", "5"])

        if choice == "1":
            retries = Prompt.ask("设置最大提取重试次数", default="3")
            try:
                self.app.smart_answering.max_extraction_retries = int(retries)
                self.console.print(f"[green]✅ 已设置重试次数为: {retries}[/green]")
            except ValueError:
                self.console.print("[red]请输入有效数字[/red]")

        elif choice == "2":
            threshold = Prompt.ask("设置置信度阈值 (0.0-1.0)", default="0.7")
            try:
                value = float(threshold)
                if 0.0 <= value <= 1.0:
                    self.app.smart_answering.confidence_threshold = value
                    self.console.print(f"[green]✅ 已设置置信度阈值为: {threshold}[/green]")
                else:
                    self.console.print("[red]置信度阈值必须在0.0-1.0之间[/red]")
            except ValueError:
                self.console.print("[red]请输入有效数字[/red]")

        elif choice == "3":
            current = self.app.smart_answering.enable_fuzzy_matching
            new_value = Confirm.ask(f"启用模糊匹配 (当前: {'启用' if current else '禁用'})", default=current)
            self.app.smart_answering.enable_fuzzy_matching = new_value
            self.console.print(f"[green]✅ 模糊匹配已{'启用' if new_value else '禁用'}[/green]")

        elif choice == "4":
            current = self.app.smart_answering.auto_verify_answers
            new_value = Confirm.ask(f"启用自动验证 (当前: {'启用' if current else '禁用'})", default=current)
            self.app.smart_answering.auto_verify_answers = new_value
            self.console.print(f"[green]✅ 自动验证已{'启用' if new_value else '禁用'}[/green]")

        elif choice == "5":
            if Confirm.ask("确定要清理缓存吗？这将删除所有缓存的答案"):
                asyncio.run(self.app.smart_answering.answer_cache.cleanup_cache())
                self.console.print("[green]✅ 缓存已清理[/green]")

    async def _run_intelligent_answering_async(self, url: str):
        """异步运行智能答题"""
        return await self.app.start_intelligent_answering(url)

    async def _run_batch_intelligent_answering_async(self, unit_range: range):
        """异步运行批量智能答题"""
        return await self.app.batch_intelligent_answering(unit_range)

    def _start_auto_login(self):
        """自动登录并开始"""
        if not self.settings.username or not self.settings.password:
            self.console.print("[red]错误: 请先在配置中设置用户名和密码[/red]")
            return
        
        self.console.print("[yellow]正在启动自动化...[/yellow]")
        
        try:
            # 在新的事件循环中运行
            asyncio.run(self._run_automation_async())
        except Exception as e:
            self.console.print(f"[red]自动化失败: {e}[/red]")
    
    def _start_with_url(self):
        """指定URL开始"""
        url = Prompt.ask("请输入目标URL", default=self.settings.ucampus_base_url)
        
        if not url:
            self.console.print("[red]URL不能为空[/red]")
            return
        
        self.console.print(f"[yellow]正在导航到: {url}[/yellow]")
        
        try:
            asyncio.run(self._run_automation_with_url(url))
        except Exception as e:
            self.console.print(f"[red]自动化失败: {e}[/red]")
    
    async def _run_automation_async(self):
        """异步运行自动化"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("初始化浏览器...", total=100)
            
            try:
                # 启动自动化
                progress.update(task, description="启动浏览器...", advance=20)
                await self.app.start_automation()
                
                progress.update(task, description="自动化完成", completed=100)
                self.console.print("[green]✅ 自动化执行完成[/green]")
                
            except Exception as e:
                progress.update(task, description=f"失败: {e}", completed=100)
                raise
    
    async def _run_automation_with_url(self, url: str):
        """使用指定URL运行自动化"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("导航到页面...", total=100)
            
            try:
                progress.update(task, advance=50)
                await self.app.start_automation(url)
                
                progress.update(task, completed=100)
                self.console.print("[green]✅ 自动化执行完成[/green]")
                
            except Exception as e:
                progress.update(task, description=f"失败: {e}", completed=100)
                raise
    
    def _stop_automation(self):
        """停止自动化"""
        try:
            asyncio.run(self.app.stop_automation())
            self.console.print("[yellow]⏹️ 自动化已停止[/yellow]")
        except Exception as e:
            self.console.print(f"[red]停止失败: {e}[/red]")
    
    def _take_screenshot(self):
        """截图"""
        try:
            if self.app.browser_manager:
                asyncio.run(self.app.browser_manager.take_screenshot())
                self.console.print("[green]📸 截图已保存[/green]")
            else:
                self.console.print("[red]浏览器未启动[/red]")
        except Exception as e:
            self.console.print(f"[red]截图失败: {e}[/red]")
    
    def _task_menu(self):
        """任务管理菜单"""
        self.console.print("\n[bold cyan]任务管理[/bold cyan]")
        
        options = [
            "1. 📋 查看任务列表",
            "2. ➕ 添加任务",
            "3. ❌ 删除任务",
            "4. 🔄 重试失败任务",
            "5. 🗑️ 清除完成任务",
            "0. 🔙 返回主菜单"
        ]
        
        for option in options:
            self.console.print(f"  {option}")
        
        choice = Prompt.ask("\n请选择操作", choices=["0", "1", "2", "3", "4", "5"])
        
        if choice == "1":
            self._show_task_list()
        elif choice == "2":
            self._add_task()
        elif choice == "3":
            self._remove_task()
        elif choice == "4":
            self._retry_failed_tasks()
        elif choice == "5":
            self._clear_completed_tasks()
    
    def _show_task_list(self):
        """显示任务列表"""
        if not self.app.task_manager:
            self.console.print("[red]任务管理器未初始化[/red]")
            return
        
        tasks = self.app.task_manager.tasks
        
        if not tasks:
            self.console.print("[yellow]暂无任务[/yellow]")
            return
        
        table = Table(title="任务列表")
        table.add_column("ID", style="dim")
        table.add_column("名称", style="cyan")
        table.add_column("类型", style="magenta")
        table.add_column("状态", style="green")
        table.add_column("进度", style="blue")
        table.add_column("单元", style="yellow")
        
        for task in tasks:
            status_color = {
                TaskStatus.PENDING: "yellow",
                TaskStatus.RUNNING: "blue",
                TaskStatus.COMPLETED: "green",
                TaskStatus.FAILED: "red",
                TaskStatus.CANCELLED: "dim"
            }.get(task.status, "white")
            
            table.add_row(
                task.id[:8],
                task.name,
                task.task_type.value,
                f"[{status_color}]{task.status.value}[/{status_color}]",
                f"{task.progress:.1f}%",
                task.unit
            )
        
        self.console.print(table)
    
    def _add_task(self):
        """添加任务"""
        self.console.print("\n[bold cyan]添加新任务[/bold cyan]")
        
        name = Prompt.ask("任务名称")
        description = Prompt.ask("任务描述", default="")
        
        # 选择任务类型
        type_options = [t.value for t in TaskType]
        task_type_str = Prompt.ask("任务类型", choices=type_options, default="custom")
        task_type = TaskType(task_type_str)
        
        url = Prompt.ask("目标URL", default="")
        unit = Prompt.ask("单元", default="")
        
        if self.app.task_manager:
            task_id = self.app.task_manager.create_task(
                name=name,
                description=description,
                task_type=task_type,
                url=url,
                unit=unit
            )
            self.console.print(f"[green]✅ 任务已添加: {task_id}[/green]")
        else:
            self.console.print("[red]任务管理器未初始化[/red]")
    
    def _remove_task(self):
        """删除任务"""
        if not self.app.task_manager or not self.app.task_manager.tasks:
            self.console.print("[yellow]暂无任务可删除[/yellow]")
            return
        
        # 显示任务列表供选择
        self._show_task_list()
        
        task_id = Prompt.ask("请输入要删除的任务ID（前8位）")
        
        # 查找匹配的任务
        matching_tasks = [t for t in self.app.task_manager.tasks if t.id.startswith(task_id)]
        
        if not matching_tasks:
            self.console.print("[red]未找到匹配的任务[/red]")
            return
        
        if len(matching_tasks) > 1:
            self.console.print("[red]找到多个匹配的任务，请输入更长的ID[/red]")
            return
        
        task = matching_tasks[0]
        if Confirm.ask(f"确定要删除任务 '{task.name}' 吗？"):
            if self.app.task_manager.remove_task(task.id):
                self.console.print("[green]✅ 任务已删除[/green]")
            else:
                self.console.print("[red]删除失败[/red]")
    
    def _retry_failed_tasks(self):
        """重试失败的任务"""
        if self.app.task_manager:
            failed_count = len(self.app.task_manager.get_failed_tasks())
            if failed_count == 0:
                self.console.print("[yellow]没有失败的任务[/yellow]")
                return
            
            if Confirm.ask(f"确定要重试 {failed_count} 个失败的任务吗？"):
                self.app.task_manager.retry_failed_tasks()
                self.console.print("[green]✅ 已重试失败的任务[/green]")
        else:
            self.console.print("[red]任务管理器未初始化[/red]")
    
    def _clear_completed_tasks(self):
        """清除完成的任务"""
        if self.app.task_manager:
            completed_count = len(self.app.task_manager.get_completed_tasks())
            if completed_count == 0:
                self.console.print("[yellow]没有已完成的任务[/yellow]")
                return
            
            if Confirm.ask(f"确定要清除 {completed_count} 个已完成的任务吗？"):
                self.app.task_manager.clear_completed_tasks()
                self.console.print("[green]✅ 已清除完成的任务[/green]")
        else:
            self.console.print("[red]任务管理器未初始化[/red]")
    
    def _config_menu(self):
        """配置菜单"""
        self.console.print("\n[bold cyan]配置设置[/bold cyan]")
        
        options = [
            "1. 👤 用户凭据",
            "2. 🎬 视频设置",
            "3. 📝 答题设置",
            "4. 🌐 浏览器设置",
            "5. 💾 保存配置",
            "0. 🔙 返回主菜单"
        ]
        
        for option in options:
            self.console.print(f"  {option}")
        
        choice = Prompt.ask("\n请选择操作", choices=["0", "1", "2", "3", "4", "5"])
        
        if choice == "1":
            self._config_credentials()
        elif choice == "2":
            self._config_video()
        elif choice == "3":
            self._config_answer()
        elif choice == "4":
            self._config_browser()
        elif choice == "5":
            self._save_config()
    
    def _config_credentials(self):
        """配置用户凭据"""
        self.console.print("\n[bold cyan]用户凭据设置[/bold cyan]")
        
        current_username = self.settings.username or "未设置"
        self.console.print(f"当前用户名: [cyan]{current_username}[/cyan]")
        
        username = Prompt.ask("新用户名", default=self.settings.username)
        password = Prompt.ask("新密码", password=True)
        
        self.settings.username = username
        self.settings.password = password
        
        self.console.print("[green]✅ 用户凭据已更新[/green]")
    
    def _config_video(self):
        """配置视频设置"""
        self.console.print("\n[bold cyan]视频设置[/bold cyan]")
        
        self.console.print(f"当前播放速度: [cyan]{self.settings.video.default_speed}x[/cyan]")
        
        speed = Prompt.ask(
            "播放速度 (1.0-4.0)", 
            default=str(self.settings.video.default_speed)
        )
        
        try:
            speed_float = float(speed)
            if 1.0 <= speed_float <= 4.0:
                self.settings.video.default_speed = speed_float
                self.console.print("[green]✅ 视频设置已更新[/green]")
            else:
                self.console.print("[red]播放速度必须在1.0-4.0之间[/red]")
        except ValueError:
            self.console.print("[red]无效的播放速度[/red]")
    
    def _config_answer(self):
        """配置答题设置"""
        self.console.print("\n[bold cyan]答题设置[/bold cyan]")
        
        auto_submit = Confirm.ask(
            "是否自动提交答案", 
            default=self.settings.answer.auto_submit
        )
        
        self.settings.answer.auto_submit = auto_submit
        self.console.print("[green]✅ 答题设置已更新[/green]")
    
    def _config_browser(self):
        """配置浏览器设置"""
        self.console.print("\n[bold cyan]浏览器设置[/bold cyan]")
        
        headless = Confirm.ask(
            "是否使用无头模式", 
            default=self.settings.browser.headless
        )
        
        self.settings.browser.headless = headless
        self.console.print("[green]✅ 浏览器设置已更新[/green]")
    
    def _save_config(self):
        """保存配置"""
        try:
            self.settings.save_config()
            self.console.print("[green]✅ 配置已保存到文件[/green]")
        except Exception as e:
            self.console.print(f"[red]保存配置失败: {e}[/red]")
    
    def _show_statistics(self):
        """显示统计信息"""
        if not self.app.task_manager:
            self.console.print("[red]任务管理器未初始化[/red]")
            return
        
        stats = self.app.task_manager.get_statistics()
        
        table = Table(title="系统统计")
        table.add_column("项目", style="cyan")
        table.add_column("数量", style="green")
        
        table.add_row("总任务数", str(stats['total']))
        table.add_row("等待中", str(stats['pending']))
        table.add_row("运行中", str(stats['running']))
        table.add_row("已完成", str(stats['completed']))
        table.add_row("失败", str(stats['failed']))
        table.add_row("成功率", f"{stats['success_rate']:.1f}%")
        
        self.console.print(table)
    
    def _question_bank_menu(self):
        """题库管理菜单"""
        self.console.print("\n[bold cyan]题库管理[/bold cyan]")
        
        options = [
            "1. 📊 题库统计",
            "2. 🔍 搜索答案",
            "3. ➕ 添加答案",
            "4. 🔄 重新加载",
            "5. ⬇️ 从远程更新",
            "0. 🔙 返回主菜单"
        ]
        
        for option in options:
            self.console.print(f"  {option}")
        
        choice = Prompt.ask("\n请选择操作", choices=["0", "1", "2", "3", "4", "5"])
        
        if choice == "1":
            self._show_question_bank_stats()
        elif choice == "2":
            self._search_answers()
        elif choice == "3":
            self._add_answer()
        elif choice == "4":
            self._reload_question_bank()
        elif choice == "5":
            self._update_question_bank()
    
    def _show_question_bank_stats(self):
        """显示题库统计"""
        if not self.app.question_bank:
            self.console.print("[red]题库未初始化[/red]")
            return
        
        stats = self.app.question_bank.get_statistics()
        
        table = Table(title="题库统计")
        table.add_column("单元", style="cyan")
        table.add_column("任务数", style="green")
        table.add_column("答案数", style="blue")
        
        for unit, unit_stats in stats.get('units', {}).items():
            table.add_row(
                unit,
                str(unit_stats['tasks']),
                str(unit_stats['answers'])
            )
        
        self.console.print(table)
        self.console.print(f"\n[bold]总计: {stats['total_units']} 个单元, {stats['total_answers']} 个答案[/bold]")
    
    def _search_answers(self):
        """搜索答案"""
        if not self.app.question_bank:
            self.console.print("[red]题库未初始化[/red]")
            return
        
        keyword = Prompt.ask("请输入搜索关键词")
        results = self.app.question_bank.search_answers(keyword)
        
        if not results:
            self.console.print("[yellow]未找到匹配的答案[/yellow]")
            return
        
        table = Table(title=f"搜索结果: {keyword}")
        table.add_column("单元", style="cyan")
        table.add_column("任务", style="green")
        table.add_column("子任务", style="blue")
        table.add_column("答案", style="yellow")
        
        for result in results[:10]:  # 限制显示数量
            table.add_row(
                result['unit'],
                result['task'],
                result['sub_task'],
                result['answer'][:50] + "..." if len(result['answer']) > 50 else result['answer']
            )
        
        self.console.print(table)
        
        if len(results) > 10:
            self.console.print(f"[dim]还有 {len(results) - 10} 个结果未显示[/dim]")
    
    def _add_answer(self):
        """添加答案"""
        if not self.app.question_bank:
            self.console.print("[red]题库未初始化[/red]")
            return
        
        self.console.print("\n[bold cyan]添加新答案[/bold cyan]")
        
        unit = Prompt.ask("单元名称")
        task = Prompt.ask("任务名称")
        sub_task = Prompt.ask("子任务名称")
        answer = Prompt.ask("答案内容")
        
        self.app.question_bank.add_answer(unit, task, sub_task, answer)
        self.console.print("[green]✅ 答案已添加[/green]")
    
    def _reload_question_bank(self):
        """重新加载题库"""
        if not self.app.question_bank:
            self.console.print("[red]题库未初始化[/red]")
            return
        
        self.console.print("[yellow]正在重新加载题库...[/yellow]")
        
        try:
            asyncio.run(self.app.question_bank.reload_question_bank())
            self.console.print("[green]✅ 题库重新加载完成[/green]")
        except Exception as e:
            self.console.print(f"[red]重新加载失败: {e}[/red]")
    
    def _update_question_bank(self):
        """从远程更新题库"""
        if not self.app.question_bank:
            self.console.print("[red]题库未初始化[/red]")
            return
        
        self.console.print("[yellow]正在从远程更新题库...[/yellow]")
        
        try:
            asyncio.run(self.app.question_bank.update_from_remote())
            self.console.print("[green]✅ 题库更新完成[/green]")
        except Exception as e:
            self.console.print(f"[red]更新失败: {e}[/red]")
    
    def _show_system_info(self):
        """显示系统信息"""
        status = self.app.get_status()
        
        panel_content = f"""
[bold cyan]应用信息[/bold cyan]
名称: {status['app_name']}
版本: {status['version']}

[bold cyan]运行状态[/bold cyan]
浏览器: {'🟢 运行中' if status['browser_running'] else '🔴 未运行'}
自动化: {'🟢 运行中' if status['automation_running'] else '🔴 未运行'}
任务数量: {status['task_count']}

[bold cyan]配置信息[/bold cyan]
浏览器类型: {self.settings.browser.name}
无头模式: {'是' if self.settings.browser.headless else '否'}
视频速度: {self.settings.video.default_speed}x
自动提交: {'是' if self.settings.answer.auto_submit else '否'}
        """
        
        panel = Panel(panel_content.strip(), title="系统信息", border_style="blue")
        self.console.print(panel)
