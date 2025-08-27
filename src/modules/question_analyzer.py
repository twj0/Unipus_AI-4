#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题目分析模块 - 分析和识别各种题目类型
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
from enum import Enum

from src.automation.browser_manager import BrowserManager
from src.utils.logger import LoggerMixin

class QuestionType(Enum):
    """题目类型枚举"""
    TRANSLATION = "translation"
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    VIDEO = "video"
    AUDIO_RECORDING = "audio_recording"
    DRAG_DROP = "drag_drop"
    MATCHING = "matching"
    SORTING = "sorting"
    IMAGE_ANNOTATION = "image_annotation"
    UNKNOWN = "unknown"
    LOADING = "loading"

class QuestionAnalyzer(LoggerMixin):
    """题目分析器"""
    
    def __init__(self, browser_manager: BrowserManager):
        """
        初始化题目分析器
        
        Args:
            browser_manager: 浏览器管理器
        """
        self.browser = browser_manager
        self.logger.info("题目分析器初始化完成")
    
    async def analyze_current_page(self) -> Dict[str, Any]:
        """
        分析当前页面的题目类型和内容
        
        Returns:
            分析结果字典
        """
        try:
            self.logger.info("开始分析当前页面")
            
            # 1. 基础页面信息
            page_info = await self._get_basic_page_info()
            
            # 2. 检测页面状态
            page_status = await self._detect_page_status()
            
            if page_status == "loading":
                return {
                    'success': True,
                    'page_type': QuestionType.LOADING.value,
                    'status': 'loading',
                    'message': '页面加载中'
                }
            
            # 3. 分析题目类型
            question_type = await self._detect_question_type()
            
            # 4. 提取题目内容
            question_content = await self._extract_question_content(question_type)
            
            # 5. 分析交互元素
            interactive_elements = await self._analyze_interactive_elements(question_type)
            
            result = {
                'success': True,
                'page_type': question_type.value,
                'page_info': page_info,
                'question_info': question_content,
                'interactive_elements': interactive_elements,
                'analysis_timestamp': asyncio.get_event_loop().time()
            }
            
            self.logger.info(f"页面分析完成，题目类型: {question_type.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"页面分析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'page_type': QuestionType.UNKNOWN.value
            }
    
    async def _get_basic_page_info(self) -> Dict[str, Any]:
        """获取基础页面信息"""
        try:
            return {
                'url': self.browser.page.url,
                'title': await self.browser.page.title(),
                'ready_state': await self.browser.execute_script("document.readyState")
            }
        except Exception as e:
            self.logger.warning(f"获取基础页面信息失败: {e}")
            return {}
    
    async def _detect_page_status(self) -> str:
        """检测页面状态"""
        try:
            # 检查是否在加载中
            loading_script = """
            () => {
                const bodyText = document.body.textContent;
                const loadingIndicators = [
                    '初始化', '加载中', 'loading', 'Loading',
                    '请稍候', '正在加载'
                ];
                
                for (const indicator of loadingIndicators) {
                    if (bodyText.includes(indicator)) {
                        return true;
                    }
                }
                
                // 检查loading元素
                const loadingElements = document.querySelectorAll('[class*="loading"], [class*="Loading"]');
                return loadingElements.length > 0;
            }
            """
            
            is_loading = await self.browser.execute_script(loading_script)
            
            if is_loading:
                return "loading"
            
            return "ready"
            
        except Exception as e:
            self.logger.warning(f"检测页面状态失败: {e}")
            return "unknown"
    
    async def _detect_question_type(self) -> QuestionType:
        """检测题目类型"""
        try:
            # 执行JavaScript检测题目类型
            detection_script = """
            () => {
                const elements = {
                    videos: document.querySelectorAll('video').length,
                    textareas: document.querySelectorAll('textarea').length,
                    textInputs: document.querySelectorAll('input[type="text"]').length,
                    radioButtons: document.querySelectorAll('input[type="radio"]').length,
                    checkboxes: document.querySelectorAll('input[type="checkbox"]:not([class*="agreement"])').length,
                    audioElements: document.querySelectorAll('audio, [class*="record"], [class*="microphone"]').length,
                    dragElements: document.querySelectorAll('[draggable="true"], [class*="drag"], [class*="drop"]').length,
                    canvasElements: document.querySelectorAll('canvas').length,
                    imageElements: document.querySelectorAll('img[class*="question"], img[class*="annotation"]').length
                };
                
                // 检查页面文本内容
                const bodyText = document.body.textContent.toLowerCase();
                const directions = document.querySelector('[class*="direction"], .directions, [ref*="direction"]');
                const directionsText = directions ? directions.textContent.toLowerCase() : '';
                
                return {
                    elements: elements,
                    bodyText: bodyText.substring(0, 500),
                    directionsText: directionsText,
                    hasTranslateKeyword: bodyText.includes('translate') || directionsText.includes('translate'),
                    hasRecordKeyword: bodyText.includes('record') || bodyText.includes('录音'),
                    hasDragKeyword: bodyText.includes('drag') || bodyText.includes('拖拽') || bodyText.includes('连线'),
                    hasMatchKeyword: bodyText.includes('match') || bodyText.includes('匹配'),
                    hasSortKeyword: bodyText.includes('sort') || bodyText.includes('排序')
                };
            }
            """
            
            detection_result = await self.browser.execute_script(detection_script)
            
            if not detection_result:
                return QuestionType.UNKNOWN
            
            elements = detection_result.get('elements', {})
            
            # 根据元素和关键词判断题目类型
            
            # 视频题
            if elements.get('videos', 0) > 0:
                return QuestionType.VIDEO
            
            # 录音题
            if (elements.get('audioElements', 0) > 0 or 
                detection_result.get('hasRecordKeyword', False)):
                return QuestionType.AUDIO_RECORDING
            
            # 翻译题
            if (elements.get('textareas', 0) > 0 and 
                detection_result.get('hasTranslateKeyword', False)):
                return QuestionType.TRANSLATION
            
            # 拖拽连线题
            if (elements.get('dragElements', 0) > 0 or 
                detection_result.get('hasDragKeyword', False)):
                return QuestionType.DRAG_DROP
            
            # 匹配题
            if detection_result.get('hasMatchKeyword', False):
                return QuestionType.MATCHING
            
            # 排序题
            if detection_result.get('hasSortKeyword', False):
                return QuestionType.SORTING
            
            # 图片标注题
            if (elements.get('canvasElements', 0) > 0 or 
                elements.get('imageElements', 0) > 0):
                return QuestionType.IMAGE_ANNOTATION
            
            # 选择题
            if (elements.get('radioButtons', 0) > 0 or 
                elements.get('checkboxes', 0) > 0):
                return QuestionType.MULTIPLE_CHOICE
            
            # 填空题
            if elements.get('textInputs', 0) > 0:
                return QuestionType.FILL_BLANK
            
            # 翻译题（仅基于textarea）
            if elements.get('textareas', 0) > 0:
                return QuestionType.TRANSLATION
            
            return QuestionType.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"检测题目类型失败: {e}")
            return QuestionType.UNKNOWN
    
    async def _extract_question_content(self, question_type: QuestionType) -> Dict[str, Any]:
        """提取题目内容"""
        try:
            content_script = """
            () => {
                const result = {
                    directions: '',
                    questionText: '',
                    sourceText: '',
                    options: [],
                    mediaElements: []
                };
                
                // 提取指令
                const directionSelectors = [
                    '.directions', '[class*="direction"]', '[ref*="direction"]',
                    'p:contains("Directions")', 'div:contains("指令")'
                ];
                
                for (const selector of directionSelectors) {
                    try {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim()) {
                            result.directions = element.textContent.trim();
                            break;
                        }
                    } catch (e) {}
                }
                
                // 提取题目文本
                const questionSelectors = [
                    '.question-text', '[class*="question"]', '.content',
                    'p', 'div[class*="text"]'
                ];
                
                for (const selector of questionSelectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            const text = element.textContent.trim();
                            if (text.length > 20 && !text.includes('Directions')) {
                                result.questionText = text;
                                break;
                            }
                        }
                        if (result.questionText) break;
                    } catch (e) {}
                }
                
                // 提取源文本（用于翻译题）
                const textElements = document.querySelectorAll('p, div');
                for (const element of textElements) {
                    const text = element.textContent.trim();
                    if (text.length > 50 && 
                        !text.includes('Directions') && 
                        !text.includes('请输入') &&
                        !text.includes('答案')) {
                        result.sourceText = text;
                        break;
                    }
                }
                
                // 提取选项
                const optionElements = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                optionElements.forEach((input, index) => {
                    const label = input.nextElementSibling || input.parentElement;
                    const optionText = label ? label.textContent.trim() : '';
                    result.options.push({
                        value: input.value || String.fromCharCode(65 + index), // A, B, C, D
                        text: optionText,
                        type: input.type
                    });
                });
                
                // 提取媒体元素信息
                const videos = document.querySelectorAll('video');
                videos.forEach(video => {
                    result.mediaElements.push({
                        type: 'video',
                        src: video.src,
                        duration: video.duration || 0
                    });
                });
                
                const audios = document.querySelectorAll('audio');
                audios.forEach(audio => {
                    result.mediaElements.push({
                        type: 'audio',
                        src: audio.src,
                        duration: audio.duration || 0
                    });
                });
                
                return result;
            }
            """
            
            content = await self.browser.execute_script(content_script)
            
            if content:
                # 根据题目类型补充特定信息
                if question_type == QuestionType.TRANSLATION:
                    content['question_type'] = 'translation'
                    content['target_language'] = self._detect_target_language(content.get('directions', ''))
                elif question_type == QuestionType.MULTIPLE_CHOICE:
                    content['question_type'] = 'multiple_choice'
                    content['is_multiple_select'] = len([opt for opt in content.get('options', []) if opt.get('type') == 'checkbox']) > 0
                elif question_type == QuestionType.VIDEO:
                    content['question_type'] = 'video'
                else:
                    content['question_type'] = question_type.value
                
                return content
            
            return {'question_type': question_type.value}
            
        except Exception as e:
            self.logger.error(f"提取题目内容失败: {e}")
            return {'question_type': question_type.value}
    
    def _detect_target_language(self, directions: str) -> str:
        """检测翻译目标语言"""
        directions_lower = directions.lower()
        
        if 'chinese' in directions_lower or '中文' in directions_lower:
            return 'zh'
        elif 'english' in directions_lower or '英文' in directions_lower:
            return 'en'
        else:
            return 'auto'
    
    async def _analyze_interactive_elements(self, question_type: QuestionType) -> Dict[str, Any]:
        """分析交互元素"""
        try:
            elements_script = """
            () => {
                return {
                    textareas: Array.from(document.querySelectorAll('textarea')).map((el, i) => ({
                        index: i,
                        placeholder: el.placeholder,
                        maxLength: el.maxLength,
                        selector: 'textarea:nth-of-type(' + (i + 1) + ')'
                    })),
                    textInputs: Array.from(document.querySelectorAll('input[type="text"]')).map((el, i) => ({
                        index: i,
                        placeholder: el.placeholder,
                        selector: 'input[type="text"]:nth-of-type(' + (i + 1) + ')'
                    })),
                    radioButtons: Array.from(document.querySelectorAll('input[type="radio"]')).map((el, i) => ({
                        index: i,
                        name: el.name,
                        value: el.value,
                        selector: 'input[type="radio"]:nth-of-type(' + (i + 1) + ')'
                    })),
                    checkboxes: Array.from(document.querySelectorAll('input[type="checkbox"]:not([class*="agreement"])')).map((el, i) => ({
                        index: i,
                        name: el.name,
                        value: el.value,
                        selector: 'input[type="checkbox"]:not([class*="agreement"]):nth-of-type(' + (i + 1) + ')'
                    })),
                    buttons: Array.from(document.querySelectorAll('button')).map((el, i) => ({
                        index: i,
                        text: el.textContent.trim(),
                        disabled: el.disabled,
                        selector: 'button:nth-of-type(' + (i + 1) + ')'
                    })),
                    videos: Array.from(document.querySelectorAll('video')).map((el, i) => ({
                        index: i,
                        src: el.src,
                        duration: el.duration,
                        selector: 'video:nth-of-type(' + (i + 1) + ')'
                    }))
                };
            }
            """
            
            elements = await self.browser.execute_script(elements_script)
            
            # 分类按钮
            if elements:
                submit_buttons = [btn for btn in elements.get('buttons', []) 
                                if any(keyword in btn.get('text', '').lower() 
                                      for keyword in ['提交', '检查', '判分', '完成', 'submit', 'check'])]
                
                navigation_buttons = [btn for btn in elements.get('buttons', []) 
                                    if any(keyword in btn.get('text', '').lower() 
                                          for keyword in ['下一题', '继续', 'next', 'continue'])]
                
                elements['submit_buttons'] = submit_buttons
                elements['navigation_buttons'] = navigation_buttons
            
            return elements or {}
            
        except Exception as e:
            self.logger.error(f"分析交互元素失败: {e}")
            return {}
    
    async def get_question_id(self, question_info: Dict[str, Any]) -> str:
        """生成题目唯一ID"""
        try:
            import hashlib
            
            # 获取页面URL信息
            url = self.browser.page.url
            
            # 提取关键信息
            content_parts = [
                url,
                question_info.get('directions', ''),
                question_info.get('questionText', ''),
                question_info.get('sourceText', ''),
                str(len(question_info.get('options', [])))
            ]
            
            content = '_'.join(filter(None, content_parts))
            
            # 生成MD5哈希
            question_id = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            return question_id
            
        except Exception as e:
            self.logger.error(f"生成题目ID失败: {e}")
            return f"unknown_{int(asyncio.get_event_loop().time())}"
