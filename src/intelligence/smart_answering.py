#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能答题策略管理器
整合答案提取和缓存功能，实现完整的智能答题流程
"""

import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

from src.automation.browser_manager import BrowserManager
from src.intelligence.answer_extractor import AnswerExtractor, QuestionInfo, QuestionType
from src.intelligence.answer_cache import AnswerCache
from src.config.settings import Settings
from src.utils.logger import LoggerMixin

class SmartAnsweringStrategy(LoggerMixin):
    """智能答题策略管理器"""
    
    def __init__(self, browser_manager: BrowserManager, settings: Settings):
        """
        初始化智能答题策略
        
        Args:
            browser_manager: 浏览器管理器
            settings: 配置对象
        """
        self.browser = browser_manager
        self.settings = settings
        
        # 初始化组件
        self.answer_extractor = AnswerExtractor(browser_manager)
        self.answer_cache = AnswerCache(settings.data_dir / "intelligent_cache")
        
        # 策略配置
        self.max_extraction_retries = 3
        self.enable_fuzzy_matching = True
        self.auto_verify_answers = True
        self.confidence_threshold = 0.7
        
        # 统计信息
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'extractions_attempted': 0,
            'extractions_successful': 0,
            'answers_verified': 0
        }
        
        self.logger.info("智能答题策略管理器初始化完成")
    
    async def process_question_intelligently(self) -> Dict[str, Any]:
        """
        智能处理当前题目
        
        Returns:
            处理结果字典
        """
        try:
            self.logger.info("开始智能处理题目")
            
            # 第一阶段：尝试从缓存获取答案
            result = await self._try_cached_answer()
            if result['success']:
                return result
            
            # 第二阶段：智能提取答案
            result = await self._extract_answer_intelligently()
            if result['success']:
                return result
            
            # 第三阶段：回退策略
            result = await self._fallback_strategy()
            return result
            
        except Exception as e:
            self.logger.error(f"智能处理题目失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'strategy': 'error'
            }
    
    async def _try_cached_answer(self) -> Dict[str, Any]:
        """尝试从缓存获取答案"""
        try:
            self.logger.info("第一阶段：尝试从缓存获取答案")
            
            # 提取当前题目信息
            question_info = await self.answer_extractor.extract_question_info()
            if question_info.question_type == QuestionType.UNKNOWN:
                self.logger.warning("无法识别题目类型")
                self.stats['cache_misses'] += 1
                return {'success': False, 'reason': 'unknown_question_type'}
            
            # 从缓存查找答案
            cached_answer = await self.answer_cache.get_answer(question_info)
            if cached_answer:
                self.logger.success(f"从缓存获取到答案: {cached_answer}")
                self.stats['cache_hits'] += 1
                
                # 填写答案
                success = await self._fill_answer(question_info, cached_answer)
                if success:
                    # 提交答案
                    submit_success = await self._submit_answer()
                    if submit_success and self.auto_verify_answers:
                        # 验证答案正确性
                        await self._verify_answer_correctness(question_info, cached_answer)
                    
                    return {
                        'success': True,
                        'strategy': 'cached',
                        'answer': cached_answer,
                        'question_info': question_info,
                        'submitted': submit_success
                    }
            
            self.stats['cache_misses'] += 1
            return {'success': False, 'reason': 'no_cached_answer'}
            
        except Exception as e:
            self.logger.error(f"缓存查找失败: {e}")
            self.stats['cache_misses'] += 1
            return {'success': False, 'reason': f'cache_error: {e}'}
    
    async def _extract_answer_intelligently(self) -> Dict[str, Any]:
        """智能提取答案"""
        try:
            self.logger.info("第二阶段：智能提取答案")
            self.stats['extractions_attempted'] += 1
            
            # 使用答案提取器获取答案
            extraction_result = await self.answer_extractor.extract_answer_for_question(
                max_retries=self.max_extraction_retries
            )
            
            if extraction_result:
                question_info, correct_answer = extraction_result
                self.logger.success(f"成功提取答案: {correct_answer}")
                self.stats['extractions_successful'] += 1
                
                # 存储到缓存
                await self.answer_cache.store_answer(
                    question_info, 
                    correct_answer, 
                    confidence=0.8  # 提取的答案初始置信度
                )
                
                # 重新加载页面准备正式答题
                await self._reload_page_for_answering()
                
                # 填写正确答案
                success = await self._fill_answer(question_info, correct_answer)
                if success:
                    # 提交答案
                    submit_success = await self._submit_answer()
                    
                    return {
                        'success': True,
                        'strategy': 'extracted',
                        'answer': correct_answer,
                        'question_info': question_info,
                        'submitted': submit_success
                    }
            
            return {'success': False, 'reason': 'extraction_failed'}
            
        except Exception as e:
            self.logger.error(f"智能提取失败: {e}")
            return {'success': False, 'reason': f'extraction_error: {e}'}
    
    async def _fallback_strategy(self) -> Dict[str, Any]:
        """回退策略"""
        try:
            self.logger.info("第三阶段：执行回退策略")
            
            # 提取题目信息
            question_info = await self.answer_extractor.extract_question_info()
            
            # 根据题目类型使用不同的回退策略
            if question_info.question_type == QuestionType.MULTIPLE_CHOICE:
                return await self._fallback_multiple_choice(question_info)
            elif question_info.question_type == QuestionType.FILL_BLANK:
                return await self._fallback_fill_blank(question_info)
            elif question_info.question_type == QuestionType.TRANSLATION:
                return await self._fallback_translation(question_info)
            else:
                return await self._fallback_generic(question_info)
                
        except Exception as e:
            self.logger.error(f"回退策略失败: {e}")
            return {'success': False, 'reason': f'fallback_error: {e}'}
    
    async def _fallback_multiple_choice(self, question_info: QuestionInfo) -> Dict[str, Any]:
        """选择题回退策略"""
        try:
            self.logger.info("使用选择题回退策略")
            
            # 智能选择策略：优先选择A，然后是B
            options = ['A', 'B', 'C', 'D']
            
            for option in options:
                success = await self.browser.execute_script(f"""
                    const inputs = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                    for (let input of inputs) {{
                        if (input.value === '{option}' || 
                            input.getAttribute('data-option') === '{option}' ||
                            input.closest('label').textContent.trim().startsWith('{option}')) {{
                            input.click();
                            return true;
                        }}
                    }}
                    return false;
                """)
                
                if success:
                    self.logger.info(f"回退策略选择了选项: {option}")
                    
                    # 提交答案
                    submit_success = await self._submit_answer()
                    
                    return {
                        'success': True,
                        'strategy': 'fallback_choice',
                        'answer': option,
                        'question_info': question_info,
                        'submitted': submit_success
                    }
            
            return {'success': False, 'reason': 'no_options_found'}
            
        except Exception as e:
            self.logger.error(f"选择题回退策略失败: {e}")
            return {'success': False, 'reason': f'fallback_choice_error: {e}'}
    
    async def _fallback_fill_blank(self, question_info: QuestionInfo) -> Dict[str, Any]:
        """填空题回退策略"""
        try:
            self.logger.info("使用填空题回退策略")
            
            # 使用通用占位符
            success = await self.browser.execute_script("""
                const inputs = document.querySelectorAll('input[type="text"]');
                let filled = 0;
                
                inputs.forEach((input, index) => {
                    input.value = `answer${index + 1}`;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    filled++;
                });
                
                return filled > 0;
            """)
            
            if success:
                # 提交答案
                submit_success = await self._submit_answer()
                
                return {
                    'success': True,
                    'strategy': 'fallback_fill',
                    'answer': 'placeholder_answers',
                    'question_info': question_info,
                    'submitted': submit_success
                }
            
            return {'success': False, 'reason': 'no_inputs_found'}
            
        except Exception as e:
            self.logger.error(f"填空题回退策略失败: {e}")
            return {'success': False, 'reason': f'fallback_fill_error: {e}'}
    
    async def _fallback_translation(self, question_info: QuestionInfo) -> Dict[str, Any]:
        """翻译题回退策略"""
        try:
            self.logger.info("使用翻译题回退策略")
            
            # 使用通用翻译占位符
            placeholder_translation = "This is a placeholder translation. Please provide the correct translation."
            
            success = await self.browser.execute_script(f"""
                const textarea = document.querySelector('textarea');
                if (textarea) {{
                    textarea.value = '{placeholder_translation}';
                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
                return false;
            """)
            
            if success:
                # 提交答案
                submit_success = await self._submit_answer()
                
                return {
                    'success': True,
                    'strategy': 'fallback_translation',
                    'answer': placeholder_translation,
                    'question_info': question_info,
                    'submitted': submit_success
                }
            
            return {'success': False, 'reason': 'no_textarea_found'}
            
        except Exception as e:
            self.logger.error(f"翻译题回退策略失败: {e}")
            return {'success': False, 'reason': f'fallback_translation_error: {e}'}
    
    async def _fallback_generic(self, question_info: QuestionInfo) -> Dict[str, Any]:
        """通用回退策略"""
        try:
            self.logger.info("使用通用回退策略")
            
            # 尝试点击第一个可交互元素
            success = await self.browser.execute_script("""
                const interactiveElements = document.querySelectorAll(
                    'input, button, select, textarea, [role="button"], [onclick]'
                );
                
                for (let element of interactiveElements) {
                    if (element.offsetParent !== null && !element.disabled) {
                        element.click();
                        return true;
                    }
                }
                
                return false;
            """)
            
            if success:
                await asyncio.sleep(1)
                
                # 尝试提交
                submit_success = await self._submit_answer()
                
                return {
                    'success': True,
                    'strategy': 'fallback_generic',
                    'answer': 'generic_interaction',
                    'question_info': question_info,
                    'submitted': submit_success
                }
            
            return {'success': False, 'reason': 'no_interactive_elements'}
            
        except Exception as e:
            self.logger.error(f"通用回退策略失败: {e}")
            return {'success': False, 'reason': f'fallback_generic_error: {e}'}
    
    async def _fill_answer(self, question_info: QuestionInfo, answer: str) -> bool:
        """填写答案"""
        try:
            if question_info.question_type == QuestionType.MULTIPLE_CHOICE:
                return await self._fill_multiple_choice_answer(answer)
            elif question_info.question_type == QuestionType.FILL_BLANK:
                return await self._fill_blank_answer(answer)
            elif question_info.question_type in [QuestionType.TRANSLATION, QuestionType.ESSAY]:
                return await self._fill_text_answer(answer)
            else:
                self.logger.warning(f"不支持的题目类型: {question_info.question_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"填写答案失败: {e}")
            return False
    
    async def _fill_multiple_choice_answer(self, answer: str) -> bool:
        """填写选择题答案"""
        try:
            # 如果答案是多个选项，分别处理
            choices = answer.split() if ' ' in answer else [answer]
            
            for i, choice in enumerate(choices):
                choice = choice.strip()
                if choice in 'ABCD':
                    success = await self.browser.execute_script(f"""
                        const selectors = [
                            'input[value="{choice}"]',
                            'input[data-option="{choice}"]',
                            '.option-{choice.lower()} input',
                            'label:contains("{choice}") input'
                        ];
                        
                        for (const selector of selectors) {{
                            const element = document.querySelector(selector);
                            if (element) {{
                                element.click();
                                return true;
                            }}
                        }}
                        
                        // 按索引选择
                        const inputs = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                        if (inputs[{i}]) {{
                            inputs[{i}].click();
                            return true;
                        }}
                        
                        return false;
                    """)
                    
                    if success:
                        await asyncio.sleep(0.3)
                    else:
                        self.logger.warning(f"无法选择选项: {choice}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"填写选择题答案失败: {e}")
            return False
    
    async def _fill_blank_answer(self, answer: str) -> bool:
        """填写填空题答案"""
        try:
            lines = answer.split('\n')
            
            success = await self.browser.execute_script(f"""
                const inputs = document.querySelectorAll('input[type="text"]');
                const answers = {json.dumps(lines)};
                let filled = 0;
                
                for (let i = 0; i < inputs.length && i < answers.length; i++) {{
                    const cleanAnswer = answers[i].replace(/^\\d+[\\.)\\s]*/, '').trim();
                    if (cleanAnswer) {{
                        inputs[i].value = cleanAnswer;
                        inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        filled++;
                    }}
                }}
                
                return filled > 0;
            """)
            
            return success
            
        except Exception as e:
            self.logger.error(f"填写填空题答案失败: {e}")
            return False
    
    async def _fill_text_answer(self, answer: str) -> bool:
        """填写文本答案"""
        try:
            success = await self.browser.execute_script(f"""
                const textarea = document.querySelector('textarea');
                if (textarea) {{
                    textarea.value = {json.dumps(answer)};
                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
                return false;
            """)
            
            return success
            
        except Exception as e:
            self.logger.error(f"填写文本答案失败: {e}")
            return False
    
    async def _submit_answer(self) -> bool:
        """提交答案"""
        try:
            if not self.settings.answer.auto_submit:
                self.logger.info("自动提交已禁用")
                return True
            
            submit_selectors = [
                'button[type="submit"]',
                '.submit-btn',
                '.btn-submit',
                '.btn-primary',
                'button:contains("提交")',
                'button:contains("Submit")'
            ]
            
            for selector in submit_selectors:
                success = await self.browser.click_element(selector)
                if success:
                    self.logger.info("答案已提交")
                    await asyncio.sleep(2)  # 等待提交完成
                    return True
            
            self.logger.warning("未找到提交按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"提交答案失败: {e}")
            return False
    
    async def _reload_page_for_answering(self):
        """重新加载页面准备答题"""
        try:
            self.logger.info("重新加载页面准备正式答题")
            await self.browser.page.reload()
            await asyncio.sleep(3)  # 等待页面加载
            
        except Exception as e:
            self.logger.error(f"重新加载页面失败: {e}")
    
    async def _verify_answer_correctness(self, question_info: QuestionInfo, answer: str):
        """验证答案正确性"""
        try:
            # 这里可以实现答案正确性验证逻辑
            # 例如检查页面是否显示"正确"或"错误"的提示
            
            await asyncio.sleep(2)  # 等待结果显示
            
            # 检查页面反馈
            feedback = await self.browser.execute_script("""
                const feedbackSelectors = [
                    '.correct', '.success', '.right',
                    '.incorrect', '.error', '.wrong',
                    '[class*="correct"]', '[class*="success"]',
                    '[class*="incorrect"]', '[class*="error"]'
                ];
                
                for (const selector of feedbackSelectors) {
                    const element = document.querySelector(selector);
                    if (element && element.offsetParent !== null) {
                        return {
                            text: element.textContent.trim(),
                            className: element.className
                        };
                    }
                }
                
                return null;
            """)
            
            if feedback:
                text = feedback.get('text', '').lower()
                className = feedback.get('className', '').lower()
                
                is_correct = any(keyword in text + className for keyword in 
                               ['correct', 'right', 'success', '正确', '对'])
                
                # 更新缓存中的验证信息
                question_id = self.answer_cache._generate_question_id(question_info)
                await self.answer_cache.verify_answer(question_id, is_correct)
                
                self.stats['answers_verified'] += 1
                self.logger.info(f"答案验证完成: {'正确' if is_correct else '错误'}")
            
        except Exception as e:
            self.logger.debug(f"验证答案正确性失败: {e}")
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        try:
            cache_stats = self.answer_cache.get_cache_stats()
            
            total_attempts = self.stats['cache_hits'] + self.stats['cache_misses']
            cache_hit_rate = self.stats['cache_hits'] / total_attempts if total_attempts > 0 else 0
            
            extraction_success_rate = (self.stats['extractions_successful'] / 
                                     self.stats['extractions_attempted'] 
                                     if self.stats['extractions_attempted'] > 0 else 0)
            
            return {
                'strategy_stats': self.stats,
                'cache_hit_rate': cache_hit_rate,
                'extraction_success_rate': extraction_success_rate,
                'cache_stats': cache_stats
            }
            
        except Exception as e:
            self.logger.error(f"获取策略统计失败: {e}")
            return {}
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.answer_cache.cleanup_cache()
            await self.answer_cache.backup_to_json()
            self.logger.info("智能答题策略清理完成")
            
        except Exception as e:
            self.logger.error(f"清理失败: {e}")
