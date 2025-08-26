#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能答案缓存管理系统
"""

import json
import sqlite3
import hashlib
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from src.intelligence.answer_extractor import QuestionInfo, QuestionType
from src.utils.logger import LoggerMixin

@dataclass
class CacheEntry:
    """缓存条目"""
    question_id: str
    unit: str
    task: str
    sub_task: str
    question_type: str
    question_text: str
    correct_answer: str
    confidence: float = 1.0
    created_at: float = 0.0
    updated_at: float = 0.0
    access_count: int = 0
    last_accessed: float = 0.0
    verified: bool = False
    metadata: Dict[str, Any] = None

class AnswerCache(LoggerMixin):
    """智能答案缓存管理器"""
    
    def __init__(self, cache_dir: Path):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据库文件路径
        self.db_path = self.cache_dir / "answer_cache.db"
        self.json_backup_path = self.cache_dir / "answer_cache_backup.json"
        
        # 缓存配置
        self.max_cache_size = 10000  # 最大缓存条目数
        self.cache_ttl = 30 * 24 * 3600  # 缓存有效期30天
        self.auto_backup_interval = 3600  # 自动备份间隔1小时
        
        # 内存缓存
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.last_backup_time = 0
        
        # 初始化数据库
        self._init_database()
        
        # 加载缓存到内存
        self._load_cache_to_memory()
        
        self.logger.info(f"答案缓存管理器初始化完成，缓存目录: {cache_dir}")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建答案缓存表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS answer_cache (
                        question_id TEXT PRIMARY KEY,
                        unit TEXT NOT NULL,
                        task TEXT NOT NULL,
                        sub_task TEXT,
                        question_type TEXT NOT NULL,
                        question_text TEXT NOT NULL,
                        correct_answer TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        access_count INTEGER DEFAULT 0,
                        last_accessed REAL DEFAULT 0,
                        verified BOOLEAN DEFAULT FALSE,
                        metadata TEXT
                    )
                """)
                
                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_unit_task ON answer_cache (unit, task)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_question_type ON answer_cache (question_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON answer_cache (created_at)")
                
                # 创建统计表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cache_stats (
                        id INTEGER PRIMARY KEY,
                        total_entries INTEGER DEFAULT 0,
                        total_hits INTEGER DEFAULT 0,
                        total_misses INTEGER DEFAULT 0,
                        last_cleanup REAL DEFAULT 0,
                        created_at REAL NOT NULL
                    )
                """)
                
                conn.commit()
                self.logger.debug("数据库初始化完成")
                
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _load_cache_to_memory(self):
        """加载缓存到内存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM answer_cache")
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                for row in rows:
                    data = dict(zip(columns, row))
                    
                    # 解析metadata
                    metadata = {}
                    if data.get('metadata'):
                        try:
                            metadata = json.loads(data['metadata'])
                        except:
                            pass
                    
                    cache_entry = CacheEntry(
                        question_id=data['question_id'],
                        unit=data['unit'],
                        task=data['task'],
                        sub_task=data['sub_task'] or '',
                        question_type=data['question_type'],
                        question_text=data['question_text'],
                        correct_answer=data['correct_answer'],
                        confidence=data['confidence'],
                        created_at=data['created_at'],
                        updated_at=data['updated_at'],
                        access_count=data['access_count'],
                        last_accessed=data['last_accessed'],
                        verified=bool(data['verified']),
                        metadata=metadata
                    )
                    
                    self.memory_cache[data['question_id']] = cache_entry
                
                self.logger.info(f"加载了 {len(self.memory_cache)} 个缓存条目到内存")
                
        except Exception as e:
            self.logger.error(f"加载缓存到内存失败: {e}")
    
    def _generate_question_id(self, question_info: QuestionInfo) -> str:
        """生成题目ID"""
        try:
            # 使用题目文本的前200个字符生成哈希
            text_sample = question_info.question_text[:200]
            content = f"{question_info.unit}_{question_info.task}_{text_sample}"
            
            # 生成MD5哈希
            hash_obj = hashlib.md5(content.encode('utf-8'))
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"生成题目ID失败: {e}")
            return f"unknown_{int(time.time())}"
    
    async def store_answer(self, question_info: QuestionInfo, correct_answer: str, confidence: float = 1.0) -> bool:
        """
        存储答案到缓存
        
        Args:
            question_info: 题目信息
            correct_answer: 正确答案
            confidence: 置信度
        
        Returns:
            是否存储成功
        """
        try:
            question_id = self._generate_question_id(question_info)
            current_time = time.time()
            
            # 创建缓存条目
            cache_entry = CacheEntry(
                question_id=question_id,
                unit=question_info.unit,
                task=question_info.task,
                sub_task=getattr(question_info, 'sub_task', ''),
                question_type=question_info.question_type.value,
                question_text=question_info.question_text,
                correct_answer=correct_answer,
                confidence=confidence,
                created_at=current_time,
                updated_at=current_time,
                access_count=0,
                last_accessed=0,
                verified=False,
                metadata={}
            )
            
            # 存储到内存缓存
            self.memory_cache[question_id] = cache_entry
            
            # 存储到数据库
            await self._store_to_database(cache_entry)
            
            self.logger.info(f"答案已缓存: {question_info.unit} - {question_info.task}")
            
            # 检查是否需要自动备份
            await self._auto_backup()
            
            return True
            
        except Exception as e:
            self.logger.error(f"存储答案失败: {e}")
            return False
    
    async def _store_to_database(self, cache_entry: CacheEntry):
        """存储到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(cache_entry.metadata) if cache_entry.metadata else None
                
                cursor.execute("""
                    INSERT OR REPLACE INTO answer_cache (
                        question_id, unit, task, sub_task, question_type,
                        question_text, correct_answer, confidence,
                        created_at, updated_at, access_count, last_accessed,
                        verified, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_entry.question_id,
                    cache_entry.unit,
                    cache_entry.task,
                    cache_entry.sub_task,
                    cache_entry.question_type,
                    cache_entry.question_text,
                    cache_entry.correct_answer,
                    cache_entry.confidence,
                    cache_entry.created_at,
                    cache_entry.updated_at,
                    cache_entry.access_count,
                    cache_entry.last_accessed,
                    cache_entry.verified,
                    metadata_json
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"存储到数据库失败: {e}")
            raise
    
    async def get_answer(self, question_info: QuestionInfo) -> Optional[str]:
        """
        从缓存获取答案
        
        Args:
            question_info: 题目信息
        
        Returns:
            缓存的答案，如果没有则返回None
        """
        try:
            question_id = self._generate_question_id(question_info)
            
            # 从内存缓存查找
            cache_entry = self.memory_cache.get(question_id)
            if cache_entry:
                # 更新访问统计
                cache_entry.access_count += 1
                cache_entry.last_accessed = time.time()
                
                # 异步更新数据库统计
                await self._update_access_stats(question_id)
                
                self.logger.info(f"从缓存获取答案: {cache_entry.correct_answer}")
                return cache_entry.correct_answer
            
            # 尝试模糊匹配
            fuzzy_answer = await self._fuzzy_match_answer(question_info)
            if fuzzy_answer:
                self.logger.info(f"通过模糊匹配获取答案: {fuzzy_answer}")
                return fuzzy_answer
            
            self.logger.debug("缓存中未找到答案")
            return None
            
        except Exception as e:
            self.logger.error(f"获取缓存答案失败: {e}")
            return None
    
    async def _update_access_stats(self, question_id: str):
        """更新访问统计"""
        try:
            cache_entry = self.memory_cache.get(question_id)
            if cache_entry:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE answer_cache 
                        SET access_count = ?, last_accessed = ?
                        WHERE question_id = ?
                    """, (cache_entry.access_count, cache_entry.last_accessed, question_id))
                    conn.commit()
                    
        except Exception as e:
            self.logger.debug(f"更新访问统计失败: {e}")
    
    async def _fuzzy_match_answer(self, question_info: QuestionInfo) -> Optional[str]:
        """模糊匹配答案"""
        try:
            # 在相同单元和任务中查找相似题目
            candidates = []
            
            for cache_entry in self.memory_cache.values():
                if (cache_entry.unit == question_info.unit and 
                    cache_entry.task == question_info.task and
                    cache_entry.question_type == question_info.question_type.value):
                    
                    # 计算文本相似度
                    similarity = self._calculate_text_similarity(
                        question_info.question_text,
                        cache_entry.question_text
                    )
                    
                    if similarity > 0.8:  # 相似度阈值
                        candidates.append((cache_entry, similarity))
            
            if candidates:
                # 选择相似度最高的
                best_match = max(candidates, key=lambda x: x[1])
                cache_entry, similarity = best_match
                
                self.logger.info(f"找到模糊匹配答案，相似度: {similarity:.2f}")
                
                # 更新访问统计
                cache_entry.access_count += 1
                cache_entry.last_accessed = time.time()
                
                return cache_entry.correct_answer
            
            return None
            
        except Exception as e:
            self.logger.debug(f"模糊匹配失败: {e}")
            return None
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        try:
            # 简单的基于字符的相似度计算
            if not text1 or not text2:
                return 0.0
            
            # 移除空白字符并转换为小写
            text1 = ''.join(text1.split()).lower()
            text2 = ''.join(text2.split()).lower()
            
            if text1 == text2:
                return 1.0
            
            # 计算最长公共子序列
            def lcs_length(s1, s2):
                m, n = len(s1), len(s2)
                dp = [[0] * (n + 1) for _ in range(m + 1)]
                
                for i in range(1, m + 1):
                    for j in range(1, n + 1):
                        if s1[i-1] == s2[j-1]:
                            dp[i][j] = dp[i-1][j-1] + 1
                        else:
                            dp[i][j] = max(dp[i-1][j], dp[i][j-1])
                
                return dp[m][n]
            
            lcs_len = lcs_length(text1, text2)
            max_len = max(len(text1), len(text2))
            
            return lcs_len / max_len if max_len > 0 else 0.0
            
        except Exception:
            return 0.0
    
    async def verify_answer(self, question_id: str, is_correct: bool) -> bool:
        """
        验证答案正确性
        
        Args:
            question_id: 题目ID
            is_correct: 答案是否正确
        
        Returns:
            是否更新成功
        """
        try:
            cache_entry = self.memory_cache.get(question_id)
            if not cache_entry:
                return False
            
            # 更新验证状态和置信度
            cache_entry.verified = True
            if is_correct:
                cache_entry.confidence = min(1.0, cache_entry.confidence + 0.1)
            else:
                cache_entry.confidence = max(0.1, cache_entry.confidence - 0.2)
            
            cache_entry.updated_at = time.time()
            
            # 更新数据库
            await self._store_to_database(cache_entry)
            
            self.logger.info(f"答案验证完成: {question_id}, 正确: {is_correct}")
            return True
            
        except Exception as e:
            self.logger.error(f"验证答案失败: {e}")
            return False
    
    async def cleanup_cache(self):
        """清理过期缓存"""
        try:
            current_time = time.time()
            expired_ids = []
            
            # 查找过期条目
            for question_id, cache_entry in self.memory_cache.items():
                if current_time - cache_entry.created_at > self.cache_ttl:
                    expired_ids.append(question_id)
            
            # 删除过期条目
            for question_id in expired_ids:
                del self.memory_cache[question_id]
            
            # 从数据库删除
            if expired_ids:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    placeholders = ','.join(['?'] * len(expired_ids))
                    cursor.execute(f"DELETE FROM answer_cache WHERE question_id IN ({placeholders})", expired_ids)
                    conn.commit()
                
                self.logger.info(f"清理了 {len(expired_ids)} 个过期缓存条目")
            
            # 如果缓存过大，删除最少使用的条目
            if len(self.memory_cache) > self.max_cache_size:
                # 按访问次数和最后访问时间排序
                sorted_entries = sorted(
                    self.memory_cache.items(),
                    key=lambda x: (x[1].access_count, x[1].last_accessed)
                )
                
                # 删除最少使用的条目
                to_remove = len(self.memory_cache) - self.max_cache_size
                for i in range(to_remove):
                    question_id = sorted_entries[i][0]
                    del self.memory_cache[question_id]
                
                # 从数据库删除
                remove_ids = [sorted_entries[i][0] for i in range(to_remove)]
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    placeholders = ','.join(['?'] * len(remove_ids))
                    cursor.execute(f"DELETE FROM answer_cache WHERE question_id IN ({placeholders})", remove_ids)
                    conn.commit()
                
                self.logger.info(f"清理了 {to_remove} 个最少使用的缓存条目")
            
        except Exception as e:
            self.logger.error(f"清理缓存失败: {e}")
    
    async def _auto_backup(self):
        """自动备份"""
        try:
            current_time = time.time()
            if current_time - self.last_backup_time > self.auto_backup_interval:
                await self.backup_to_json()
                self.last_backup_time = current_time
                
        except Exception as e:
            self.logger.debug(f"自动备份失败: {e}")
    
    async def backup_to_json(self):
        """备份到JSON文件"""
        try:
            backup_data = {
                'version': '1.0',
                'created_at': time.time(),
                'entries': []
            }
            
            for cache_entry in self.memory_cache.values():
                entry_dict = asdict(cache_entry)
                backup_data['entries'].append(entry_dict)
            
            with open(self.json_backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"缓存已备份到: {self.json_backup_path}")
            
        except Exception as e:
            self.logger.error(f"备份到JSON失败: {e}")
    
    async def restore_from_json(self):
        """从JSON文件恢复"""
        try:
            if not self.json_backup_path.exists():
                self.logger.warning("备份文件不存在")
                return False
            
            with open(self.json_backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            entries = backup_data.get('entries', [])
            restored_count = 0
            
            for entry_dict in entries:
                try:
                    cache_entry = CacheEntry(**entry_dict)
                    self.memory_cache[cache_entry.question_id] = cache_entry
                    await self._store_to_database(cache_entry)
                    restored_count += 1
                except Exception as e:
                    self.logger.debug(f"恢复条目失败: {e}")
            
            self.logger.info(f"从备份恢复了 {restored_count} 个缓存条目")
            return True
            
        except Exception as e:
            self.logger.error(f"从JSON恢复失败: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            total_entries = len(self.memory_cache)
            verified_entries = sum(1 for entry in self.memory_cache.values() if entry.verified)
            
            # 按单元统计
            unit_stats = {}
            for entry in self.memory_cache.values():
                unit = entry.unit
                if unit not in unit_stats:
                    unit_stats[unit] = 0
                unit_stats[unit] += 1
            
            # 按题型统计
            type_stats = {}
            for entry in self.memory_cache.values():
                q_type = entry.question_type
                if q_type not in type_stats:
                    type_stats[q_type] = 0
                type_stats[q_type] += 1
            
            return {
                'total_entries': total_entries,
                'verified_entries': verified_entries,
                'verification_rate': verified_entries / total_entries if total_entries > 0 else 0,
                'unit_stats': unit_stats,
                'type_stats': type_stats,
                'cache_size_mb': self._get_cache_size_mb(),
                'last_backup': self.last_backup_time
            }
            
        except Exception as e:
            self.logger.error(f"获取缓存统计失败: {e}")
            return {}
    
    def _get_cache_size_mb(self) -> float:
        """获取缓存大小（MB）"""
        try:
            if self.db_path.exists():
                size_bytes = self.db_path.stat().st_size
                return size_bytes / (1024 * 1024)
            return 0.0
        except:
            return 0.0
