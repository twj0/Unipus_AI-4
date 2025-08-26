#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理模块
"""

import asyncio
import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid

from src.config.settings import Settings
from src.utils.logger import LoggerMixin

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消

class TaskType(Enum):
    """任务类型枚举"""
    VIDEO = "video"          # 视频任务
    QUESTION = "question"    # 题目任务
    NAVIGATION = "navigation" # 导航任务
    LOGIN = "login"          # 登录任务
    CUSTOM = "custom"        # 自定义任务

@dataclass
class Task:
    """任务数据类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.CUSTOM
    status: TaskStatus = TaskStatus.PENDING
    url: str = ""
    unit: str = ""
    lesson: str = ""
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3
    progress: float = 0.0
    metadata: Dict = field(default_factory=dict)

class TaskManager(LoggerMixin):
    """任务管理器"""
    
    def __init__(self, settings: Settings):
        """
        初始化任务管理器
        
        Args:
            settings: 配置对象
        """
        self.settings = settings
        self.tasks: List[Task] = []
        self.current_task: Optional[Task] = None
        self.running = False
        self.paused = False
        
        # 事件回调
        self.on_task_started: Optional[Callable[[Task], None]] = None
        self.on_task_completed: Optional[Callable[[Task], None]] = None
        self.on_task_failed: Optional[Callable[[Task], None]] = None
        self.on_progress_updated: Optional[Callable[[Task], None]] = None
        
        self.logger.info("任务管理器初始化完成")
    
    def add_task(self, task: Task) -> str:
        """
        添加任务
        
        Args:
            task: 任务对象
        
        Returns:
            任务ID
        """
        self.tasks.append(task)
        self.logger.info(f"添加任务: {task.name} ({task.id})")
        return task.id
    
    def create_task(
        self,
        name: str,
        description: str = "",
        task_type: TaskType = TaskType.CUSTOM,
        url: str = "",
        unit: str = "",
        lesson: str = "",
        priority: int = 0,
        **metadata
    ) -> str:
        """
        创建并添加任务
        
        Args:
            name: 任务名称
            description: 任务描述
            task_type: 任务类型
            url: 目标URL
            unit: 单元
            lesson: 课程
            priority: 优先级
            **metadata: 额外元数据
        
        Returns:
            任务ID
        """
        task = Task(
            name=name,
            description=description,
            task_type=task_type,
            url=url,
            unit=unit,
            lesson=lesson,
            priority=priority,
            metadata=metadata
        )
        
        return self.add_task(task)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务对象
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def remove_task(self, task_id: str) -> bool:
        """
        移除任务
        
        Args:
            task_id: 任务ID
        
        Returns:
            是否移除成功
        """
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.CANCELLED
                del self.tasks[i]
                self.logger.info(f"移除任务: {task.name} ({task_id})")
                return True
        return False
    
    def update_task_status(self, task_id: str, status: TaskStatus, error_message: str = ""):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误消息
        """
        task = self.get_task(task_id)
        if not task:
            return
        
        old_status = task.status
        task.status = status
        task.error_message = error_message
        
        if status == TaskStatus.RUNNING:
            task.started_at = time.time()
            if self.on_task_started:
                self.on_task_started(task)
        elif status == TaskStatus.COMPLETED:
            task.completed_at = time.time()
            task.progress = 100.0
            if self.on_task_completed:
                self.on_task_completed(task)
        elif status == TaskStatus.FAILED:
            task.completed_at = time.time()
            if self.on_task_failed:
                self.on_task_failed(task)
        
        self.logger.debug(f"任务状态更新: {task.name} {old_status.value} -> {status.value}")
    
    def update_task_progress(self, task_id: str, progress: float):
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
        """
        task = self.get_task(task_id)
        if not task:
            return
        
        task.progress = max(0, min(100, progress))
        
        if self.on_progress_updated:
            self.on_progress_updated(task)
    
    def get_pending_tasks(self) -> List[Task]:
        """获取等待中的任务"""
        return [task for task in self.tasks if task.status == TaskStatus.PENDING]
    
    def get_running_tasks(self) -> List[Task]:
        """获取运行中的任务"""
        return [task for task in self.tasks if task.status == TaskStatus.RUNNING]
    
    def get_completed_tasks(self) -> List[Task]:
        """获取已完成的任务"""
        return [task for task in self.tasks if task.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[Task]:
        """获取失败的任务"""
        return [task for task in self.tasks if task.status == TaskStatus.FAILED]
    
    def get_tasks_by_type(self, task_type: TaskType) -> List[Task]:
        """
        按类型获取任务
        
        Args:
            task_type: 任务类型
        
        Returns:
            任务列表
        """
        return [task for task in self.tasks if task.task_type == task_type]
    
    def get_tasks_by_unit(self, unit: str) -> List[Task]:
        """
        按单元获取任务
        
        Args:
            unit: 单元名称
        
        Returns:
            任务列表
        """
        return [task for task in self.tasks if task.unit == unit]
    
    def clear_completed_tasks(self):
        """清除已完成的任务"""
        before_count = len(self.tasks)
        self.tasks = [task for task in self.tasks if task.status != TaskStatus.COMPLETED]
        after_count = len(self.tasks)
        
        removed_count = before_count - after_count
        if removed_count > 0:
            self.logger.info(f"清除了 {removed_count} 个已完成的任务")
    
    def clear_failed_tasks(self):
        """清除失败的任务"""
        before_count = len(self.tasks)
        self.tasks = [task for task in self.tasks if task.status != TaskStatus.FAILED]
        after_count = len(self.tasks)
        
        removed_count = before_count - after_count
        if removed_count > 0:
            self.logger.info(f"清除了 {removed_count} 个失败的任务")
    
    def retry_failed_tasks(self):
        """重试失败的任务"""
        failed_tasks = self.get_failed_tasks()
        for task in failed_tasks:
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                task.retry_count += 1
                task.error_message = ""
                self.logger.info(f"重试任务: {task.name} (第{task.retry_count}次)")
    
    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个要执行的任务
        
        Returns:
            下一个任务
        """
        pending_tasks = self.get_pending_tasks()
        if not pending_tasks:
            return None
        
        # 按优先级排序
        pending_tasks.sort(key=lambda t: (-t.priority, t.created_at))
        return pending_tasks[0]
    
    async def execute_task(self, task: Task, executor: Callable) -> bool:
        """
        执行任务
        
        Args:
            task: 任务对象
            executor: 执行器函数
        
        Returns:
            是否执行成功
        """
        try:
            self.current_task = task
            self.update_task_status(task.id, TaskStatus.RUNNING)
            
            # 执行任务
            result = await executor(task)
            
            if result:
                self.update_task_status(task.id, TaskStatus.COMPLETED)
                return True
            else:
                self.update_task_status(task.id, TaskStatus.FAILED, "任务执行失败")
                return False
                
        except Exception as e:
            self.update_task_status(task.id, TaskStatus.FAILED, str(e))
            self.logger.error(f"任务执行异常: {task.name} - {e}")
            return False
        finally:
            self.current_task = None
    
    def pause(self):
        """暂停任务执行"""
        self.paused = True
        self.logger.info("任务管理器已暂停")
    
    def resume(self):
        """恢复任务执行"""
        self.paused = False
        self.logger.info("任务管理器已恢复")
    
    def stop(self):
        """停止任务管理器"""
        self.running = False
        self.paused = False
        
        # 取消运行中的任务
        for task in self.get_running_tasks():
            task.status = TaskStatus.CANCELLED
        
        self.logger.info("任务管理器已停止")
    
    def get_statistics(self) -> Dict:
        """获取任务统计信息"""
        total = len(self.tasks)
        pending = len(self.get_pending_tasks())
        running = len(self.get_running_tasks())
        completed = len(self.get_completed_tasks())
        failed = len(self.get_failed_tasks())
        cancelled = len([t for t in self.tasks if t.status == TaskStatus.CANCELLED])
        
        return {
            'total': total,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed,
            'cancelled': cancelled,
            'success_rate': (completed / total * 100) if total > 0 else 0
        }
    
    def get_task_count(self) -> int:
        """获取任务总数"""
        return len(self.tasks)
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.running and not self.paused
    
    def export_tasks(self) -> List[Dict]:
        """导出任务数据"""
        return [
            {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'type': task.task_type.value,
                'status': task.status.value,
                'url': task.url,
                'unit': task.unit,
                'lesson': task.lesson,
                'priority': task.priority,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'error_message': task.error_message,
                'retry_count': task.retry_count,
                'progress': task.progress,
                'metadata': task.metadata
            }
            for task in self.tasks
        ]
