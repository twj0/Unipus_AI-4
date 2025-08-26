#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能答案提取器
通过试答和响应分析自动获取正确答案
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.automation.browser_manager import BrowserManager
from src.utils.logger import LoggerMixin

class QuestionType(Enum):
    """题目类型枚举"""
    MULTIPLE_CHOICE = "multiple_choice"    # 选择题
    FILL_BLANK = "fill_blank"             # 填空题
    TRANSLATION = "translation"           # 翻译题
    ESSAY = "essay"                       # 作文题
    UNKNOWN = "unknown"                   # 未知类型

@dataclass
class QuestionInfo:
    """题目信息"""
    question_id: str
    question_type: QuestionType
    question_text: str
    options: List[str] = None
    correct_answer: str = ""
    explanation: str = ""
    unit: str = ""
    task: str = ""
    sub_task: str = ""

class AnswerExtractor(LoggerMixin):
    """智能答案提取器"""
    
    def __init__(self, browser_manager: BrowserManager):
        """
        初始化答案提取器
        
        Args:
            browser_manager: 浏览器管理器
        """
        self.browser = browser_manager
        self.extracted_answers = {}
        self.network_responses = []
        
        # 答案提取模式
        self.answer_patterns = {
            'correct_answer': [
                r'正确答案[：:]\s*([A-D])',
                r'答案[：:]\s*([A-D])',
                r'"correct"[：:]\s*"([A-D])"',
                r'"answer"[：:]\s*"([^"]+)"',
                r'正确答案[：:]\s*(.+?)(?:\n|$)',
            ],
            'explanation': [
                r'解析[：:]\s*(.+?)(?:\n|$)',
                r'解释[：:]\s*(.+?)(?:\n|$)',
                r'"explanation"[：:]\s*"([^"]+)"',
            ]
        }
        
        self.logger.info("智能答案提取器初始化完成")
    
    async def setup_network_monitoring(self):
        """设置网络监控"""
        try:
            if not self.browser.page:
                return False
            
            # 清空之前的响应记录
            self.network_responses.clear()
            
            # 监听网络响应
            async def handle_response(response):
                try:
                    # 只关注API响应
                    if any(keyword in response.url for keyword in ['api', 'ajax', 'submit', 'check', 'answer']):
                        content_type = response.headers.get('content-type', '')
                        
                        if 'application/json' in content_type:
                            try:
                                response_data = await response.json()
                                self.network_responses.append({
                                    'url': response.url,
                                    'status': response.status,
                                    'data': response_data,
                                    'timestamp': asyncio.get_event_loop().time()
                                })
                                self.logger.debug(f"捕获API响应: {response.url}")
                            except Exception as e:
                                self.logger.debug(f"解析JSON响应失败: {e}")
                        
                        elif 'text/html' in content_type:
                            try:
                                response_text = await response.text()
                                if len(response_text) < 10000:  # 避免处理过大的HTML
                                    self.network_responses.append({
                                        'url': response.url,
                                        'status': response.status,
                                        'data': response_text,
                                        'timestamp': asyncio.get_event_loop().time()
                                    })
                            except Exception as e:
                                self.logger.debug(f"获取HTML响应失败: {e}")
                                
                except Exception as e:
                    self.logger.debug(f"处理响应失败: {e}")
            
            self.browser.page.on('response', handle_response)
            self.logger.info("网络监控设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置网络监控失败: {e}")
            return False
    
    async def detect_question_type(self) -> QuestionType:
        """检测题目类型"""
        try:
            # 检查是否有单选/多选按钮
            radio_buttons = await self.browser.execute_script("""
                return document.querySelectorAll('input[type="radio"]').length;
            """)
            
            checkbox_buttons = await self.browser.execute_script("""
                return document.querySelectorAll('input[type="checkbox"]').length;
            """)
            
            if radio_buttons > 0 or checkbox_buttons > 0:
                return QuestionType.MULTIPLE_CHOICE
            
            # 检查是否有文本输入框
            text_inputs = await self.browser.execute_script("""
                return document.querySelectorAll('input[type="text"]').length;
            """)
            
            if text_inputs > 0:
                return QuestionType.FILL_BLANK
            
            # 检查是否有文本区域
            textareas = await self.browser.execute_script("""
                return document.querySelectorAll('textarea').length;
            """)
            
            if textareas > 0:
                # 通过文本区域大小判断是翻译题还是作文题
                textarea_info = await self.browser.execute_script("""
                    const textarea = document.querySelector('textarea');
                    if (textarea) {
                        return {
                            rows: textarea.rows || 0,
                            placeholder: textarea.placeholder || '',
                            className: textarea.className || ''
                        };
                    }
                    return null;
                """)
                
                if textarea_info:
                    placeholder = textarea_info.get('placeholder', '').lower()
                    class_name = textarea_info.get('className', '').lower()
                    
                    if any(keyword in placeholder + class_name for keyword in ['translation', '翻译', 'translate']):
                        return QuestionType.TRANSLATION
                    else:
                        return QuestionType.ESSAY
            
            return QuestionType.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"检测题目类型失败: {e}")
            return QuestionType.UNKNOWN
    
    async def extract_question_info(self) -> QuestionInfo:
        """提取题目信息"""
        try:
            # 获取页面基本信息
            page_info = await self.browser.execute_script("""
                return {
                    url: window.location.href,
                    hash: window.location.hash,
                    title: document.title
                };
            """)
            
            # 解析单元和任务信息
            hash_str = page_info.get('hash', '')
            unit_match = re.search(r'/u(\d+)/', hash_str)
            unit = f"Unit {unit_match.group(1)}" if unit_match else ""
            
            task = ""
            if 'iexplore1' in hash_str:
                task = 'iExplore 1: Learning before class' if 'before' in hash_str else 'iExplore 1: Reviewing after class'
            elif 'iexplore2' in hash_str:
                task = 'iExplore 2: Learning before class' if 'before' in hash_str else 'iExplore 2: Reviewing after class'
            elif 'unittest' in hash_str:
                task = 'Unit test'
            
            # 检测题目类型
            question_type = await self.detect_question_type()
            
            # 提取题目文本
            question_text = await self.browser.execute_script("""
                // 尝试多种选择器获取题目文本
                const selectors = [
                    '.question-content',
                    '.question-text',
                    '.problem-content',
                    '.item-content',
                    '[class*="question"]',
                    '[class*="problem"]'
                ];
                
                for (const selector of selectors) {
                    const element = document.querySelector(selector);
                    if (element && element.textContent.trim()) {
                        return element.textContent.trim();
                    }
                }
                
                // 如果没找到，尝试获取主要内容区域的文本
                const mainContent = document.querySelector('main, .main-content, .content');
                if (mainContent) {
                    return mainContent.textContent.trim().substring(0, 500);
                }
                
                return '';
            """)
            
            # 提取选项（如果是选择题）
            options = []
            if question_type == QuestionType.MULTIPLE_CHOICE:
                options = await self.browser.execute_script("""
                    const options = [];
                    const labels = document.querySelectorAll('label');
                    
                    labels.forEach(label => {
                        const input = label.querySelector('input[type="radio"], input[type="checkbox"]');
                        if (input) {
                            const text = label.textContent.trim();
                            if (text) {
                                options.push(text);
                            }
                        }
                    });
                    
                    return options;
                """)
            
            # 生成题目ID
            question_id = f"{unit}_{task}_{hash(question_text[:100])}"
            
            return QuestionInfo(
                question_id=question_id,
                question_type=question_type,
                question_text=question_text,
                options=options,
                unit=unit,
                task=task
            )
            
        except Exception as e:
            self.logger.error(f"提取题目信息失败: {e}")
            return QuestionInfo(
                question_id="unknown",
                question_type=QuestionType.UNKNOWN,
                question_text=""
            )
    
    async def perform_trial_answer(self, question_info: QuestionInfo) -> bool:
        """执行试答"""
        try:
            self.logger.info(f"开始试答: {question_info.question_type.value}")
            
            if question_info.question_type == QuestionType.MULTIPLE_CHOICE:
                return await self._trial_multiple_choice()
            elif question_info.question_type == QuestionType.FILL_BLANK:
                return await self._trial_fill_blank()
            elif question_info.question_type == QuestionType.TRANSLATION:
                return await self._trial_translation()
            elif question_info.question_type == QuestionType.ESSAY:
                return await self._trial_essay()
            else:
                self.logger.warning("未知题目类型，跳过试答")
                return False
                
        except Exception as e:
            self.logger.error(f"试答失败: {e}")
            return False
    
    async def _trial_multiple_choice(self) -> bool:
        """试答选择题"""
        try:
            # 随机选择一个选项
            result = await self.browser.execute_script("""
                const inputs = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                if (inputs.length > 0) {
                    const randomIndex = Math.floor(Math.random() * inputs.length);
                    inputs[randomIndex].click();
                    return true;
                }
                return false;
            """)
            
            if result:
                await asyncio.sleep(0.5)  # 等待一下
                self.logger.debug("已随机选择选项")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"试答选择题失败: {e}")
            return False
    
    async def _trial_fill_blank(self) -> bool:
        """试答填空题"""
        try:
            # 在所有文本输入框中填入占位符
            result = await self.browser.execute_script("""
                const inputs = document.querySelectorAll('input[type="text"]');
                let filled = 0;
                
                inputs.forEach((input, index) => {
                    input.value = `placeholder_${index + 1}`;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    filled++;
                });
                
                return filled > 0;
            """)
            
            if result:
                await asyncio.sleep(0.5)
                self.logger.debug("已填入占位符文本")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"试答填空题失败: {e}")
            return False
    
    async def _trial_translation(self) -> bool:
        """试答翻译题"""
        try:
            # 在文本区域填入占位符翻译
            result = await self.browser.execute_script("""
                const textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.value = 'This is a placeholder translation.';
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            """)
            
            if result:
                await asyncio.sleep(0.5)
                self.logger.debug("已填入占位符翻译")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"试答翻译题失败: {e}")
            return False
    
    async def _trial_essay(self) -> bool:
        """试答作文题"""
        try:
            # 在文本区域填入占位符作文
            result = await self.browser.execute_script("""
                const textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.value = 'This is a placeholder essay content.';
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            """)
            
            if result:
                await asyncio.sleep(0.5)
                self.logger.debug("已填入占位符作文")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"试答作文题失败: {e}")
            return False
    
    async def submit_trial_answer(self) -> bool:
        """提交试答"""
        try:
            # 查找并点击提交按钮
            submit_selectors = [
                'button[type="submit"]',
                '.submit-btn',
                '.btn-submit',
                '.btn-primary',
                'button:contains("提交")',
                'button:contains("Submit")',
                '[class*="submit"]'
            ]
            
            for selector in submit_selectors:
                result = await self.browser.click_element(selector)
                if result:
                    self.logger.info("试答已提交")
                    await asyncio.sleep(2)  # 等待响应
                    return True
            
            self.logger.warning("未找到提交按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"提交试答失败: {e}")
            return False
    
    async def extract_correct_answer_from_response(self, question_info: QuestionInfo) -> Optional[str]:
        """从响应中提取正确答案"""
        try:
            self.logger.info("开始从响应中提取正确答案")
            
            # 等待一下确保所有响应都被捕获
            await asyncio.sleep(1)
            
            # 分析网络响应
            for response in self.network_responses:
                answer = await self._analyze_response_data(response, question_info)
                if answer:
                    self.logger.success(f"从网络响应中提取到答案: {answer}")
                    return answer
            
            # 分析页面内容
            answer = await self._analyze_page_content(question_info)
            if answer:
                self.logger.success(f"从页面内容中提取到答案: {answer}")
                return answer
            
            self.logger.warning("未能从响应中提取到正确答案")
            return None
            
        except Exception as e:
            self.logger.error(f"提取正确答案失败: {e}")
            return None
    
    async def _analyze_response_data(self, response: Dict, question_info: QuestionInfo) -> Optional[str]:
        """分析响应数据"""
        try:
            data = response.get('data')
            if not data:
                return None
            
            # 如果是JSON数据
            if isinstance(data, dict):
                # 查找常见的答案字段
                answer_fields = ['correct_answer', 'answer', 'correctAnswer', 'result', 'solution']
                for field in answer_fields:
                    if field in data:
                        answer = data[field]
                        if isinstance(answer, str) and answer.strip():
                            return answer.strip()
                
                # 递归查找嵌套的答案
                answer = self._find_answer_in_dict(data)
                if answer:
                    return answer
            
            # 如果是HTML文本
            elif isinstance(data, str):
                answer = self._extract_answer_from_html(data, question_info)
                if answer:
                    return answer
            
            return None
            
        except Exception as e:
            self.logger.debug(f"分析响应数据失败: {e}")
            return None
    
    def _find_answer_in_dict(self, data: Dict, max_depth: int = 3) -> Optional[str]:
        """在字典中递归查找答案"""
        if max_depth <= 0:
            return None
        
        try:
            for key, value in data.items():
                key_lower = str(key).lower()
                
                # 检查键名是否包含答案相关词汇
                if any(keyword in key_lower for keyword in ['answer', 'correct', 'solution', 'result']):
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                
                # 递归查找
                if isinstance(value, dict):
                    answer = self._find_answer_in_dict(value, max_depth - 1)
                    if answer:
                        return answer
                elif isinstance(value, list) and len(value) > 0:
                    for item in value:
                        if isinstance(item, dict):
                            answer = self._find_answer_in_dict(item, max_depth - 1)
                            if answer:
                                return answer
            
            return None
            
        except Exception:
            return None
    
    def _extract_answer_from_html(self, html: str, question_info: QuestionInfo) -> Optional[str]:
        """从HTML中提取答案"""
        try:
            # 使用正则表达式匹配答案模式
            for pattern in self.answer_patterns['correct_answer']:
                match = re.search(pattern, html, re.IGNORECASE | re.MULTILINE)
                if match:
                    answer = match.group(1).strip()
                    if answer:
                        return answer
            
            return None
            
        except Exception:
            return None
    
    async def _analyze_page_content(self, question_info: QuestionInfo) -> Optional[str]:
        """分析页面内容"""
        try:
            # 获取页面中可能包含答案的元素
            page_content = await self.browser.execute_script("""
                // 查找可能包含答案的元素
                const selectors = [
                    '.correct-answer',
                    '.answer-display',
                    '.result-content',
                    '.feedback',
                    '.explanation',
                    '[class*="correct"]',
                    '[class*="answer"]',
                    '[class*="result"]'
                ];
                
                const results = [];
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => {
                        if (el.textContent.trim()) {
                            results.push(el.textContent.trim());
                        }
                    });
                }
                
                return results;
            """)
            
            if page_content:
                for content in page_content:
                    # 使用正则表达式提取答案
                    for pattern in self.answer_patterns['correct_answer']:
                        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                        if match:
                            answer = match.group(1).strip()
                            if answer:
                                return answer
            
            return None
            
        except Exception as e:
            self.logger.debug(f"分析页面内容失败: {e}")
            return None
    
    async def extract_answer_for_question(self, max_retries: int = 3) -> Optional[Tuple[QuestionInfo, str]]:
        """为当前题目提取答案"""
        try:
            # 设置网络监控
            await self.setup_network_monitoring()
            
            # 提取题目信息
            question_info = await self.extract_question_info()
            if question_info.question_type == QuestionType.UNKNOWN:
                self.logger.warning("无法识别题目类型")
                return None
            
            self.logger.info(f"开始提取答案: {question_info.unit} - {question_info.task}")
            
            for attempt in range(max_retries):
                try:
                    self.logger.info(f"第 {attempt + 1} 次尝试提取答案")
                    
                    # 清空网络响应记录
                    self.network_responses.clear()
                    
                    # 执行试答
                    if not await self.perform_trial_answer(question_info):
                        self.logger.warning("试答失败，跳过此次尝试")
                        continue
                    
                    # 提交试答
                    if not await self.submit_trial_answer():
                        self.logger.warning("提交试答失败，跳过此次尝试")
                        continue
                    
                    # 提取正确答案
                    correct_answer = await self.extract_correct_answer_from_response(question_info)
                    if correct_answer:
                        question_info.correct_answer = correct_answer
                        self.logger.success(f"成功提取答案: {correct_answer}")
                        return question_info, correct_answer
                    
                    # 如果没有提取到答案，等待一下再重试
                    if attempt < max_retries - 1:
                        self.logger.info("未提取到答案，等待后重试")
                        await asyncio.sleep(2)
                        
                        # 刷新页面重新开始
                        await self.browser.page.reload()
                        await asyncio.sleep(3)
                
                except Exception as e:
                    self.logger.error(f"第 {attempt + 1} 次尝试失败: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
            
            self.logger.error("所有尝试都失败了，无法提取答案")
            return None
            
        except Exception as e:
            self.logger.error(f"提取答案过程失败: {e}")
            return None
