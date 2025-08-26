#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题库管理模块
"""

import json
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import httpx

from src.config.settings import Settings
from src.utils.logger import LoggerMixin

class QuestionBank(LoggerMixin):
    """题库管理类"""
    
    def __init__(self, settings: Settings):
        """
        初始化题库
        
        Args:
            settings: 配置对象
        """
        self.settings = settings
        self.question_data: Dict[str, Any] = {}
        self.local_file = settings.local_question_bank
        self.remote_url = settings.question_bank_url
        
        # 内置题库数据
        self.builtin_data = {
            "Unit 1": {
                "iExplore 1: Learning before class": {
                    "Reading comprehension": "A B A B A",
                    "Dealing with vocabulary": "A B A A A B"
                },
                "iExplore 1: Reviewing after class": {
                    "Application": "1. To say is easier than to do.\n2. Mary wanted to make a lot of money, buy stock, and retire early.\n3. She stayed up late either studying her English or going to parties."
                },
                "Unit test": {
                    "Part I": "1) prevails\n2) a variety of\n3) interact\n4) hanging out\n5) scale\n6) In contrast\n7) crucial\n8) engage\n9) in person\n10) directly",
                    "Part II": "B A C B A A"
                }
            },
            "Unit 2": {
                "iExplore 1: Learning before class": {
                    "Reading comprehension": "B A C D B",
                    "Dealing with vocabulary": "B C A B C A"
                },
                "Unit test": {
                    "Part I": "1) campus\n2) transform\n3) unique\n4) passion\n5) incredible\n6) approach\n7) academic\n8) potential\n9) definitely\n10) amazing",
                    "Part II": "A B C A B C"
                }
            }
        }
        
        self.logger.info("题库管理器初始化完成")
        
        # 异步加载题库
        asyncio.create_task(self.load_question_bank())
    
    async def load_question_bank(self):
        """加载题库数据"""
        try:
            self.logger.info("开始加载题库...")
            
            # 首先尝试加载本地文件
            if await self._load_local_file():
                self.logger.info("本地题库加载成功")
                return
            
            # 本地文件不存在或加载失败，尝试从远程下载
            if await self._download_remote_file():
                self.logger.info("远程题库下载成功")
                return
            
            # 都失败了，使用内置数据
            self.question_data = self.builtin_data.copy()
            self.logger.warning("使用内置题库数据")
            
        except Exception as e:
            self.logger.error(f"加载题库失败: {e}")
            self.question_data = self.builtin_data.copy()
    
    async def _load_local_file(self) -> bool:
        """加载本地题库文件"""
        try:
            if not self.local_file.exists():
                return False
            
            with open(self.local_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                self.question_data = data
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"加载本地文件失败: {e}")
            return False
    
    async def _download_remote_file(self) -> bool:
        """下载远程题库文件"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.remote_url)
                response.raise_for_status()
                
                data = response.json()
                
                if isinstance(data, dict):
                    self.question_data = data
                    
                    # 保存到本地
                    await self._save_local_file()
                    return True
                
                return False
                
        except Exception as e:
            self.logger.debug(f"下载远程文件失败: {e}")
            return False
    
    async def _save_local_file(self):
        """保存题库到本地文件"""
        try:
            # 确保目录存在
            self.local_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.local_file, 'w', encoding='utf-8') as f:
                json.dump(self.question_data, f, ensure_ascii=False, indent=2)
                
            self.logger.debug("题库已保存到本地")
            
        except Exception as e:
            self.logger.warning(f"保存本地文件失败: {e}")
    
    async def get_answer(self, unit: str, task: str, sub_task: Optional[str] = None) -> Optional[str]:
        """
        获取答案
        
        Args:
            unit: 单元名称
            task: 任务名称
            sub_task: 子任务名称
        
        Returns:
            答案字符串
        """
        try:
            if not self.question_data:
                await self.load_question_bank()
            
            # 查找答案
            unit_data = self.question_data.get(unit)
            if not unit_data:
                self.logger.debug(f"未找到单元: {unit}")
                return None
            
            task_data = unit_data.get(task)
            if not task_data:
                self.logger.debug(f"未找到任务: {unit} - {task}")
                return None
            
            if sub_task:
                answer = task_data.get(sub_task)
                if answer:
                    self.logger.debug(f"找到答案: {unit} - {task} - {sub_task}")
                    return answer
            
            # 如果没有指定子任务或子任务未找到，尝试常见的子任务
            common_sub_tasks = [
                "Reading comprehension",
                "Dealing with vocabulary", 
                "Application",
                "Part I",
                "Part II",
                "Part III"
            ]
            
            for sub in common_sub_tasks:
                answer = task_data.get(sub)
                if answer:
                    self.logger.debug(f"找到答案: {unit} - {task} - {sub}")
                    return answer
            
            # 如果task_data是字符串，直接返回
            if isinstance(task_data, str):
                self.logger.debug(f"找到答案: {unit} - {task}")
                return task_data
            
            self.logger.debug(f"未找到答案: {unit} - {task} - {sub_task}")
            return None
            
        except Exception as e:
            self.logger.error(f"获取答案失败: {e}")
            return None
    
    def add_answer(self, unit: str, task: str, sub_task: str, answer: str):
        """
        添加答案
        
        Args:
            unit: 单元名称
            task: 任务名称
            sub_task: 子任务名称
            answer: 答案内容
        """
        try:
            if unit not in self.question_data:
                self.question_data[unit] = {}
            
            if task not in self.question_data[unit]:
                self.question_data[unit][task] = {}
            
            self.question_data[unit][task][sub_task] = answer
            
            self.logger.info(f"添加答案: {unit} - {task} - {sub_task}")
            
            # 异步保存到本地
            asyncio.create_task(self._save_local_file())
            
        except Exception as e:
            self.logger.error(f"添加答案失败: {e}")
    
    def get_all_units(self) -> list:
        """获取所有单元列表"""
        return list(self.question_data.keys())
    
    def get_unit_tasks(self, unit: str) -> list:
        """获取单元的所有任务"""
        unit_data = self.question_data.get(unit, {})
        return list(unit_data.keys())
    
    def get_task_sub_tasks(self, unit: str, task: str) -> list:
        """获取任务的所有子任务"""
        task_data = self.question_data.get(unit, {}).get(task, {})
        if isinstance(task_data, dict):
            return list(task_data.keys())
        return []
    
    def search_answers(self, keyword: str) -> list:
        """
        搜索包含关键词的答案
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            匹配的答案列表
        """
        results = []
        
        try:
            for unit, unit_data in self.question_data.items():
                for task, task_data in unit_data.items():
                    if isinstance(task_data, dict):
                        for sub_task, answer in task_data.items():
                            if isinstance(answer, str) and keyword.lower() in answer.lower():
                                results.append({
                                    'unit': unit,
                                    'task': task,
                                    'sub_task': sub_task,
                                    'answer': answer
                                })
                    elif isinstance(task_data, str) and keyword.lower() in task_data.lower():
                        results.append({
                            'unit': unit,
                            'task': task,
                            'sub_task': '',
                            'answer': task_data
                        })
            
        except Exception as e:
            self.logger.error(f"搜索答案失败: {e}")
        
        return results
    
    def get_statistics(self) -> dict:
        """获取题库统计信息"""
        try:
            stats = {
                'total_units': len(self.question_data),
                'total_tasks': 0,
                'total_answers': 0,
                'units': {}
            }
            
            for unit, unit_data in self.question_data.items():
                unit_stats = {
                    'tasks': len(unit_data),
                    'answers': 0
                }
                
                for task, task_data in unit_data.items():
                    if isinstance(task_data, dict):
                        unit_stats['answers'] += len(task_data)
                    else:
                        unit_stats['answers'] += 1
                
                stats['units'][unit] = unit_stats
                stats['total_tasks'] += unit_stats['tasks']
                stats['total_answers'] += unit_stats['answers']
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}
    
    async def reload_question_bank(self):
        """重新加载题库"""
        self.logger.info("重新加载题库")
        await self.load_question_bank()
    
    async def update_from_remote(self):
        """从远程更新题库"""
        self.logger.info("从远程更新题库")
        if await self._download_remote_file():
            self.logger.info("题库更新成功")
        else:
            self.logger.warning("题库更新失败")
