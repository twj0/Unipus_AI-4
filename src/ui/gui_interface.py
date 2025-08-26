#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI界面模块
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import asyncio
import threading
from typing import Optional, TYPE_CHECKING

from src.config.settings import Settings
from src.utils.logger import LoggerMixin
from src.core.task_manager import Task, TaskStatus, TaskType

if TYPE_CHECKING:
    from src.core.application import UCampusApplication

class GUIInterface(LoggerMixin):
    """GUI界面类"""
    
    def __init__(self, settings: Settings, app: 'UCampusApplication'):
        """
        初始化GUI界面
        
        Args:
            settings: 配置对象
            app: 应用程序实例
        """
        self.settings = settings
        self.app = app
        self.root: Optional[tk.Tk] = None
        self.running = False
        
        # 界面组件
        self.status_label: Optional[tk.Label] = None
        self.start_button: Optional[tk.Button] = None
        self.stop_button: Optional[tk.Button] = None
        self.log_text: Optional[scrolledtext.ScrolledText] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.task_tree: Optional[ttk.Treeview] = None
        
        # 配置变量
        self.video_speed_var: Optional[tk.DoubleVar] = None
        self.auto_submit_var: Optional[tk.BooleanVar] = None
        self.headless_var: Optional[tk.BooleanVar] = None
        
        self.logger.info("GUI界面初始化完成")
    
    def run(self):
        """运行GUI界面"""
        try:
            self.logger.info("启动GUI界面")
            
            # 创建主窗口
            self.root = tk.Tk()
            self.root.title(f"{self.settings.app_name} v{self.settings.version}")
            self.root.geometry(f"{self.settings.ui.window_width}x{self.settings.ui.window_height}")
            
            # 设置窗口图标和属性
            self.root.resizable(True, True)
            if self.settings.ui.always_on_top:
                self.root.attributes('-topmost', True)
            
            # 创建界面
            self._create_widgets()
            self._setup_layout()
            self._bind_events()
            
            # 设置关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # 启动界面
            self.running = True
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"GUI运行失败: {e}")
            raise
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建笔记本控件（标签页）
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 主控制页面
        self._create_control_tab(notebook)
        
        # 任务管理页面
        self._create_task_tab(notebook)
        
        # 配置页面
        self._create_config_tab(notebook)
        
        # 日志页面
        self._create_log_tab(notebook)
    
    def _create_control_tab(self, parent):
        """创建主控制页面"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="主控制")
        
        # 状态显示
        status_frame = ttk.LabelFrame(frame, text="状态信息")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = tk.Label(status_frame, text="就绪", font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 控制按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = tk.Button(
            button_frame, 
            text="🚀 开始自动化", 
            font=("Arial", 12),
            bg="#4CAF50", 
            fg="white",
            command=self._on_start_clicked
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = tk.Button(
            button_frame, 
            text="⏹️ 停止", 
            font=("Arial", 12),
            bg="#f44336", 
            fg="white",
            command=self._on_stop_clicked,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 智能答题控制
        smart_frame = ttk.LabelFrame(frame, text="智能答题")
        smart_frame.pack(fill=tk.X, pady=(0, 10))

        self.smart_start_button = tk.Button(
            smart_frame,
            text="🧠 智能答题",
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            command=self._on_smart_answering_clicked
        )
        self.smart_start_button.pack(side=tk.LEFT, padx=(5, 5), pady=5)

        self.batch_smart_button = tk.Button(
            smart_frame,
            text="🚀 批量智能答题",
            font=("Arial", 12),
            bg="#FF9800",
            fg="white",
            command=self._on_batch_smart_clicked
        )
        self.batch_smart_button.pack(side=tk.LEFT, padx=(5, 5), pady=5)

        # 快捷操作
        quick_frame = ttk.LabelFrame(frame, text="快捷操作")
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        quick_buttons = [
            ("📚 打开U校园", self._open_ucampus),
            ("🔄 重新加载题库", self._reload_question_bank),
            ("📊 查看统计", self._show_statistics),
            ("📸 截图", self._take_screenshot)
        ]

        for i, (text, command) in enumerate(quick_buttons):
            btn = tk.Button(quick_frame, text=text, command=command)
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")

        quick_frame.grid_columnconfigure(0, weight=1)
        quick_frame.grid_columnconfigure(1, weight=1)
        
        # URL输入
        url_frame = ttk.LabelFrame(frame, text="目标URL")
        url_frame.pack(fill=tk.X)
        
        self.url_entry = tk.Entry(url_frame, font=("Arial", 10))
        self.url_entry.pack(fill=tk.X, padx=10, pady=10)
        self.url_entry.insert(0, self.settings.ucampus_base_url)
    
    def _create_task_tab(self, parent):
        """创建任务管理页面"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="任务管理")
        
        # 任务列表
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview
        columns = ("name", "type", "status", "progress", "unit")
        self.task_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.task_tree.heading("name", text="任务名称")
        self.task_tree.heading("type", text="类型")
        self.task_tree.heading("status", text="状态")
        self.task_tree.heading("progress", text="进度")
        self.task_tree.heading("unit", text="单元")
        
        # 设置列宽
        self.task_tree.column("name", width=200)
        self.task_tree.column("type", width=80)
        self.task_tree.column("status", width=80)
        self.task_tree.column("progress", width=80)
        self.task_tree.column("unit", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 任务操作按钮
        task_button_frame = ttk.Frame(frame)
        task_button_frame.pack(fill=tk.X)
        
        task_buttons = [
            ("➕ 添加任务", self._add_task),
            ("❌ 删除任务", self._remove_task),
            ("🔄 重试失败", self._retry_failed_tasks),
            ("🗑️ 清除完成", self._clear_completed_tasks)
        ]
        
        for text, command in task_buttons:
            btn = tk.Button(task_button_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)
    
    def _create_config_tab(self, parent):
        """创建配置页面"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="配置")
        
        # 创建滚动框架
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 视频配置
        video_frame = ttk.LabelFrame(scrollable_frame, text="视频设置")
        video_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 播放速度
        speed_frame = ttk.Frame(video_frame)
        speed_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(speed_frame, text="播放速度:").pack(side=tk.LEFT)
        self.video_speed_var = tk.DoubleVar(value=self.settings.video.default_speed)
        speed_scale = tk.Scale(
            speed_frame, 
            from_=1.0, 
            to=4.0, 
            resolution=0.25,
            orient=tk.HORIZONTAL,
            variable=self.video_speed_var
        )
        speed_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 答题配置
        answer_frame = ttk.LabelFrame(scrollable_frame, text="答题设置")
        answer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_submit_var = tk.BooleanVar(value=self.settings.answer.auto_submit)
        auto_submit_check = tk.Checkbutton(
            answer_frame, 
            text="自动提交答案", 
            variable=self.auto_submit_var
        )
        auto_submit_check.pack(anchor=tk.W, padx=10, pady=5)
        
        # 浏览器配置
        browser_frame = ttk.LabelFrame(scrollable_frame, text="浏览器设置")
        browser_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.headless_var = tk.BooleanVar(value=self.settings.browser.headless)
        headless_check = tk.Checkbutton(
            browser_frame, 
            text="无头模式（后台运行）", 
            variable=self.headless_var
        )
        headless_check.pack(anchor=tk.W, padx=10, pady=5)
        
        # 保存按钮
        save_button = tk.Button(
            scrollable_frame, 
            text="💾 保存配置", 
            command=self._save_config
        )
        save_button.pack(pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_log_tab(self, parent):
        """创建日志页面"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="日志")
        
        # 日志显示
        self.log_text = scrolledtext.ScrolledText(
            frame, 
            wrap=tk.WORD, 
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 日志控制按钮
        log_button_frame = ttk.Frame(frame)
        log_button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        log_buttons = [
            ("🗑️ 清除日志", self._clear_log),
            ("💾 保存日志", self._save_log),
            ("🔄 刷新", self._refresh_log)
        ]
        
        for text, command in log_buttons:
            btn = tk.Button(log_button_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5)
    
    def _setup_layout(self):
        """设置布局"""
        pass
    
    def _bind_events(self):
        """绑定事件"""
        # 绑定任务管理器事件
        if self.app.task_manager:
            self.app.task_manager.on_task_started = self._on_task_started
            self.app.task_manager.on_task_completed = self._on_task_completed
            self.app.task_manager.on_task_failed = self._on_task_failed
            self.app.task_manager.on_progress_updated = self._on_progress_updated
        
        # 定期更新界面
        self._update_interface()
    
    def _on_start_clicked(self):
        """开始按钮点击事件"""
        try:
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("错误", "请输入目标URL")
                return
            
            # 在新线程中启动自动化
            thread = threading.Thread(
                target=self._run_automation_async, 
                args=(url,),
                daemon=True
            )
            thread.start()
            
            # 更新按钮状态
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self._update_status("正在启动自动化...")
            
        except Exception as e:
            self.logger.error(f"启动自动化失败: {e}")
            messagebox.showerror("错误", f"启动失败: {e}")
    
    def _on_stop_clicked(self):
        """停止按钮点击事件"""
        try:
            # 停止自动化
            asyncio.create_task(self.app.stop_automation())

            # 更新按钮状态
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.smart_start_button.config(state=tk.NORMAL)
            self.batch_smart_button.config(state=tk.NORMAL)
            self._update_status("已停止")

        except Exception as e:
            self.logger.error(f"停止自动化失败: {e}")

    def _on_smart_answering_clicked(self):
        """智能答题按钮点击事件"""
        try:
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("错误", "请输入目标URL")
                return

            # 在新线程中启动智能答题
            thread = threading.Thread(
                target=self._run_smart_answering_async,
                args=(url,),
                daemon=True
            )
            thread.start()

            # 更新按钮状态
            self.smart_start_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            self.batch_smart_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self._update_status("正在智能答题...")

        except Exception as e:
            self.logger.error(f"启动智能答题失败: {e}")
            messagebox.showerror("错误", f"启动失败: {e}")

    def _on_batch_smart_clicked(self):
        """批量智能答题按钮点击事件"""
        try:
            # 弹出对话框让用户选择单元范围
            dialog = tk.Toplevel(self.root)
            dialog.title("批量智能答题设置")
            dialog.geometry("300x200")
            dialog.transient(self.root)
            dialog.grab_set()

            # 单元范围选择
            tk.Label(dialog, text="选择单元范围:", font=("Arial", 12)).pack(pady=10)

            range_frame = tk.Frame(dialog)
            range_frame.pack(pady=10)

            tk.Label(range_frame, text="从 Unit").pack(side=tk.LEFT)
            start_var = tk.StringVar(value="1")
            start_entry = tk.Entry(range_frame, textvariable=start_var, width=5)
            start_entry.pack(side=tk.LEFT, padx=5)

            tk.Label(range_frame, text="到 Unit").pack(side=tk.LEFT)
            end_var = tk.StringVar(value="8")
            end_entry = tk.Entry(range_frame, textvariable=end_var, width=5)
            end_entry.pack(side=tk.LEFT, padx=5)

            def start_batch():
                try:
                    start_unit = int(start_var.get())
                    end_unit = int(end_var.get())

                    if start_unit < 1 or end_unit < start_unit or end_unit > 20:
                        messagebox.showerror("错误", "请输入有效的单元范围 (1-20)")
                        return

                    dialog.destroy()

                    # 在新线程中启动批量智能答题
                    thread = threading.Thread(
                        target=self._run_batch_smart_answering_async,
                        args=(range(start_unit, end_unit + 1),),
                        daemon=True
                    )
                    thread.start()

                    # 更新按钮状态
                    self.batch_smart_button.config(state=tk.DISABLED)
                    self.smart_start_button.config(state=tk.DISABLED)
                    self.start_button.config(state=tk.DISABLED)
                    self.stop_button.config(state=tk.NORMAL)
                    self._update_status("正在批量智能答题...")

                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数字")
                except Exception as e:
                    messagebox.showerror("错误", f"启动失败: {e}")

            # 按钮
            button_frame = tk.Frame(dialog)
            button_frame.pack(pady=20)

            tk.Button(button_frame, text="开始", command=start_batch, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            self.logger.error(f"启动批量智能答题失败: {e}")
            messagebox.showerror("错误", f"启动失败: {e}")
    
    def _run_automation_async(self, url: str):
        """异步运行自动化"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.app.start_automation(url))
        except Exception as e:
            self.logger.error(f"自动化运行失败: {e}")
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.smart_start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.batch_smart_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self._update_status("就绪"))

    def _run_smart_answering_async(self, url: str):
        """异步运行智能答题"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.app.start_intelligent_answering(url))

            # 显示结果
            if result['success']:
                message = f"智能答题成功！\n策略: {result['strategy']}\n答案: {result.get('answer', 'N/A')}"
                self.root.after(0, lambda: messagebox.showinfo("成功", message))
            else:
                message = f"智能答题失败\n原因: {result.get('reason', 'unknown')}"
                self.root.after(0, lambda: messagebox.showwarning("失败", message))

        except Exception as e:
            self.logger.error(f"智能答题运行失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"智能答题失败: {e}"))
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.smart_start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.batch_smart_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self._update_status("就绪"))

    def _run_batch_smart_answering_async(self, unit_range: range):
        """异步运行批量智能答题"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.app.batch_intelligent_answering(unit_range))

            # 显示结果
            message = f"""批量智能答题完成！

总任务数: {result['total']}
成功数: {result['successful']}
成功率: {result['success_rate']:.1%}

详细结果请查看日志。"""

            self.root.after(0, lambda: messagebox.showinfo("完成", message))

        except Exception as e:
            self.logger.error(f"批量智能答题运行失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"批量智能答题失败: {e}"))
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.batch_smart_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.smart_start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self._update_status("就绪"))
    
    def _update_status(self, status: str):
        """更新状态显示"""
        if self.status_label:
            self.status_label.config(text=status)
    
    def _update_progress(self, progress: float):
        """更新进度条"""
        if self.progress_bar:
            self.progress_bar['value'] = progress
    
    def _update_interface(self):
        """更新界面"""
        try:
            # 更新任务列表
            self._update_task_list()
            
            # 更新日志
            self._update_log_display()
            
            # 定期更新
            if self.running and self.root:
                self.root.after(1000, self._update_interface)
                
        except Exception as e:
            self.logger.debug(f"更新界面失败: {e}")
    
    def _update_task_list(self):
        """更新任务列表"""
        if not self.task_tree or not self.app.task_manager:
            return
        
        # 清除现有项目
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # 添加任务
        for task in self.app.task_manager.tasks:
            self.task_tree.insert("", "end", values=(
                task.name,
                task.task_type.value,
                task.status.value,
                f"{task.progress:.1f}%",
                task.unit
            ))
    
    def _update_log_display(self):
        """更新日志显示"""
        # 这里可以实现日志显示更新
        pass
    
    def _on_task_started(self, task: Task):
        """任务开始事件"""
        self._update_status(f"正在执行: {task.name}")
    
    def _on_task_completed(self, task: Task):
        """任务完成事件"""
        self._update_status(f"已完成: {task.name}")
    
    def _on_task_failed(self, task: Task):
        """任务失败事件"""
        self._update_status(f"失败: {task.name}")
    
    def _on_progress_updated(self, task: Task):
        """进度更新事件"""
        self._update_progress(task.progress)
    
    def _open_ucampus(self):
        """打开U校园"""
        import webbrowser
        webbrowser.open(self.settings.ucampus_base_url)
    
    def _reload_question_bank(self):
        """重新加载题库"""
        if self.app.question_bank:
            asyncio.create_task(self.app.question_bank.reload_question_bank())
            messagebox.showinfo("信息", "题库重新加载完成")
    
    def _show_statistics(self):
        """显示统计信息"""
        if self.app.task_manager:
            stats = self.app.task_manager.get_statistics()
            message = f"""任务统计:
总任务数: {stats['total']}
等待中: {stats['pending']}
运行中: {stats['running']}
已完成: {stats['completed']}
失败: {stats['failed']}
成功率: {stats['success_rate']:.1f}%"""
            messagebox.showinfo("统计信息", message)
    
    def _take_screenshot(self):
        """截图"""
        if self.app.browser_manager:
            asyncio.create_task(self.app.browser_manager.take_screenshot())
            messagebox.showinfo("信息", "截图已保存")
    
    def _add_task(self):
        """添加任务"""
        # 这里可以实现添加任务的对话框
        messagebox.showinfo("信息", "添加任务功能待实现")
    
    def _remove_task(self):
        """删除任务"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的任务")
            return
        
        # 实现删除逻辑
        messagebox.showinfo("信息", "删除任务功能待实现")
    
    def _retry_failed_tasks(self):
        """重试失败的任务"""
        if self.app.task_manager:
            self.app.task_manager.retry_failed_tasks()
            messagebox.showinfo("信息", "已重试失败的任务")
    
    def _clear_completed_tasks(self):
        """清除已完成的任务"""
        if self.app.task_manager:
            self.app.task_manager.clear_completed_tasks()
            messagebox.showinfo("信息", "已清除完成的任务")
    
    def _save_config(self):
        """保存配置"""
        try:
            # 更新配置
            self.settings.video.default_speed = self.video_speed_var.get()
            self.settings.answer.auto_submit = self.auto_submit_var.get()
            self.settings.browser.headless = self.headless_var.get()
            
            # 保存到文件
            self.settings.save_config()
            
            messagebox.showinfo("信息", "配置已保存")
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def _clear_log(self):
        """清除日志"""
        if self.log_text:
            self.log_text.delete(1.0, tk.END)
    
    def _save_log(self):
        """保存日志"""
        if not self.log_text:
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("信息", "日志已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")
    
    def _refresh_log(self):
        """刷新日志"""
        # 实现日志刷新逻辑
        pass
    
    def _on_closing(self):
        """窗口关闭事件"""
        try:
            if messagebox.askokcancel("退出", "确定要退出程序吗？"):
                self.running = False
                
                # 停止自动化
                if self.app:
                    asyncio.create_task(self.app.cleanup())
                
                self.root.destroy()
                
        except Exception as e:
            self.logger.error(f"关闭窗口失败: {e}")
            self.root.destroy()
