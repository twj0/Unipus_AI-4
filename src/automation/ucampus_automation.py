#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园自动化模块
"""

import asyncio
import re
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse, parse_qs

from src.automation.browser_manager import BrowserManager
from src.config.settings import Settings
from src.utils.logger import LoggerMixin
from src.data.question_bank import QuestionBank

class UCampusAutomation(LoggerMixin):
    """U校园自动化处理类"""
    
    def __init__(self, browser_manager: BrowserManager, settings: Settings, question_bank: QuestionBank):
        """
        初始化U校园自动化
        
        Args:
            browser_manager: 浏览器管理器
            settings: 配置对象
            question_bank: 题库对象
        """
        self.browser = browser_manager
        self.settings = settings
        self.question_bank = question_bank
        self._running = False
        self._current_task = None
        
        # 选择器配置
        self.selectors = {
            # 登录相关
            "username_input": 'input[name="username"], input[type="text"]',
            "password_input": 'input[name="password"], input[type="password"]',
            "login_button": 'button[type="submit"], .login-btn, .btn-login',
            
            # 视频相关
            "video": "video",
            "play_button": ".anticon-play, [aria-label='play'], .play-btn, .video-play-btn",
            "pause_button": ".anticon-pause, [aria-label='pause'], .pause-btn",
            
            # 题目相关
            "radio_buttons": 'input[type="radio"]',
            "checkboxes": 'input[type="checkbox"]',
            "text_inputs": 'input[type="text"]',
            "textareas": "textarea",
            "submit_button": 'button[type="submit"], .submit-btn, .btn-submit, .btn-primary',
            
            # 弹窗相关
            "popup_close": '.sec-tips .iKnow, .ant-btn.system-info-cloud-ok-button, .modal .close',
            "know_buttons": '.iKnow, [class*="know"], button[class*="ok"]',
            
            # 导航相关
            "continue_button": '.continue-btn, .next-btn, .btn-continue',
            "unit_links": '.unit-link, .chapter-link',
            "task_links": '.task-link, .lesson-link'
        }
        
        self.logger.info("U校园自动化模块初始化完成")
    
    async def navigate_to_login(self) -> bool:
        """导航到登录页面"""
        try:
            self.logger.info("导航到登录页面")
            return await self.browser.navigate_to(self.settings.ucampus_login_url)
        except Exception as e:
            self.logger.error(f"导航到登录页面失败: {e}")
            return False
    
    async def navigate_to(self, url: str) -> bool:
        """导航到指定页面"""
        try:
            self.logger.info(f"导航到页面: {url}")
            return await self.browser.navigate_to(url)
        except Exception as e:
            self.logger.error(f"导航失败: {e}")
            return False
    
    async def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        登录U校园
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            是否登录成功
        """
        try:
            username = username or self.settings.username
            password = password or self.settings.password
            
            if not username or not password:
                self.logger.error("用户名或密码为空")
                return False
            
            self.logger.info("开始登录...")
            
            # 等待登录页面加载
            await asyncio.sleep(2)
            
            # 输入用户名
            if await self.browser.wait_for_element(self.selectors["username_input"]):
                await self.browser.type_text(self.selectors["username_input"], username)
                self.logger.debug("用户名输入完成")
            else:
                self.logger.warning("未找到用户名输入框")
            
            # 输入密码
            if await self.browser.wait_for_element(self.selectors["password_input"]):
                await self.browser.type_text(self.selectors["password_input"], password)
                self.logger.debug("密码输入完成")
            else:
                self.logger.warning("未找到密码输入框")
            
            # 点击登录按钮
            if await self.browser.click_element(self.selectors["login_button"]):
                self.logger.debug("登录按钮点击完成")
            else:
                self.logger.warning("未找到登录按钮")
            
            # 等待登录完成
            await asyncio.sleep(3)
            
            # 检查是否登录成功
            current_url = await self.browser.execute_script("return window.location.href")
            if current_url and "sso.unipus.cn" not in current_url:
                self.logger.info("登录成功")
                return True
            else:
                self.logger.warning("登录可能失败，仍在登录页面")
                return False
                
        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            return False
    
    async def handle_popups(self) -> bool:
        """处理弹窗"""
        try:
            handled = False
            
            # 处理各种弹窗
            popup_selectors = [
                '.sec-tips .iKnow',  # 鼠标取词弹窗
                '.ant-btn.ant-btn-primary.system-info-cloud-ok-button',  # 系统信息弹窗
                '.modal .close',  # 模态框关闭按钮
                '.popup .close',  # 弹窗关闭按钮
            ]
            
            for selector in popup_selectors:
                if await self.browser.click_element(selector):
                    self.logger.debug(f"关闭弹窗: {selector}")
                    handled = True
                    await asyncio.sleep(0.5)
            
            # 处理"我知道了"按钮
            know_buttons = await self.browser.execute_script("""
                return Array.from(document.querySelectorAll('*')).filter(el => 
                    el.textContent && el.textContent.includes('我知道了') && 
                    el.offsetParent !== null
                ).map(el => el.tagName + (el.className ? '.' + el.className.split(' ').join('.') : ''))
            """)
            
            if know_buttons:
                for selector in know_buttons[:3]:  # 限制处理数量
                    if await self.browser.click_element(selector):
                        self.logger.debug(f"点击'我知道了'按钮: {selector}")
                        handled = True
                        await asyncio.sleep(0.5)
            
            return handled
            
        except Exception as e:
            self.logger.debug(f"处理弹窗失败: {e}")
            return False
    
    async def get_page_info(self) -> Dict[str, str]:
        """获取当前页面信息"""
        try:
            # 获取URL和hash
            page_info = await self.browser.execute_script("""
                return {
                    url: window.location.href,
                    hash: window.location.hash,
                    title: document.title
                }
            """)
            
            if not page_info:
                return {}
            
            # 解析单元信息
            hash_str = page_info.get('hash', '')
            unit_match = re.search(r'/u(\d+)/', hash_str)
            unit = f"Unit {unit_match.group(1)}" if unit_match else ""
            
            # 解析任务信息
            task = ""
            if 'iexplore1' in hash_str:
                task = 'iExplore 1: Learning before class' if 'before' in hash_str else 'iExplore 1: Reviewing after class'
            elif 'iexplore2' in hash_str:
                task = 'iExplore 2: Learning before class' if 'before' in hash_str else 'iExplore 2: Reviewing after class'
            elif 'unittest' in hash_str:
                task = 'Unit test'
            
            result = {
                'url': page_info.get('url', ''),
                'hash': hash_str,
                'title': page_info.get('title', ''),
                'unit': unit,
                'task': task
            }
            
            self.logger.debug(f"页面信息: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"获取页面信息失败: {e}")
            return {}
    
    async def handle_video(self) -> bool:
        """处理视频播放"""
        try:
            # 检查是否有视频
            if not await self.browser.wait_for_element(self.selectors["video"], timeout=2000):
                return False
            
            self.logger.info("发现视频，开始处理")
            
            # 处理弹窗
            await self.handle_popups()
            
            # 设置视频播放速度
            await self.browser.execute_script(f"""
                const video = document.querySelector('video');
                if (video) {{
                    video.playbackRate = {self.settings.video.default_speed};
                    if (video.paused) {{
                        video.play().catch(e => console.log('播放失败:', e));
                    }}
                }}
            """)
            
            # 尝试点击播放按钮
            await self.browser.click_element(self.selectors["play_button"])
            
            self.logger.info(f"视频开始播放，速度: {self.settings.video.default_speed}x")
            
            # 监控视频播放完成
            while True:
                # 定期处理弹窗
                await self.handle_popups()
                
                # 检查视频是否播放完成
                video_ended = await self.browser.execute_script("""
                    const video = document.querySelector('video');
                    return video ? video.ended : true;
                """)
                
                if video_ended:
                    self.logger.info("视频播放完成")
                    break
                
                await asyncio.sleep(self.settings.delays.video_check)
            
            return True
            
        except Exception as e:
            self.logger.error(f"处理视频失败: {e}")
            return False
    
    async def handle_questions(self) -> bool:
        """处理题目"""
        try:
            # 获取页面信息
            page_info = await self.get_page_info()
            unit = page_info.get('unit', '')
            task = page_info.get('task', '')
            
            if not unit or not task:
                self.logger.warning("无法识别页面单元或任务")
                return False
            
            self.logger.info(f"处理题目: {unit} - {task}")
            
            # 检测题目类型
            has_radio = await self.browser.wait_for_element(self.selectors["radio_buttons"], timeout=1000)
            has_checkbox = await self.browser.wait_for_element(self.selectors["checkboxes"], timeout=1000)
            has_text = await self.browser.wait_for_element(self.selectors["text_inputs"], timeout=1000)
            has_textarea = await self.browser.wait_for_element(self.selectors["textareas"], timeout=1000)
            
            if not (has_radio or has_checkbox or has_text or has_textarea):
                self.logger.warning("未发现题目元素")
                return False
            
            # 获取答案
            answer = await self.question_bank.get_answer(unit, task)
            if not answer:
                self.logger.warning(f"未找到答案: {unit} - {task}")
                return False
            
            self.logger.info("找到答案，开始填写")
            
            # 根据答案类型处理
            if re.match(r'^[ABCD\s]+$', answer):
                # 选择题
                await self._handle_multiple_choice(answer)
            elif '\n' in answer and re.search(r'^\d+[\.)]\s*', answer, re.MULTILINE):
                # 填空题
                await self._handle_fill_blanks(answer)
            else:
                # 翻译或作文题
                await self._handle_text_answer(answer)
            
            # 等待一下再提交
            await asyncio.sleep(self.settings.delays.answer_fill)
            
            # 自动提交
            if self.settings.answer.auto_submit:
                if await self.browser.click_element(self.selectors["submit_button"]):
                    self.logger.info("答案已提交")
                else:
                    self.logger.warning("未找到提交按钮")
            
            return True
            
        except Exception as e:
            self.logger.error(f"处理题目失败: {e}")
            return False
    
    async def _handle_multiple_choice(self, answers: str):
        """处理选择题"""
        try:
            choices = answers.split()
            self.logger.debug(f"处理选择题: {choices}")
            
            for i, choice in enumerate(choices):
                if choice in 'ABCD':
                    # 尝试多种选择器
                    selectors = [
                        f'input[value="{choice}"]',
                        f'input[data-option="{choice}"]',
                        f'.option-{choice.lower()} input',
                        f'label:has-text("{choice}") input'
                    ]
                    
                    clicked = False
                    for selector in selectors:
                        if await self.browser.click_element(selector):
                            clicked = True
                            break
                    
                    if not clicked:
                        # 按索引点击
                        radio_buttons = await self.browser.execute_script("""
                            return Array.from(document.querySelectorAll('input[type="radio"], input[type="checkbox"]'))
                                .map((el, index) => index);
                        """)
                        
                        if i < len(radio_buttons):
                            await self.browser.execute_script(f"""
                                const inputs = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                                if (inputs[{i}]) {{
                                    inputs[{i}].click();
                                }}
                            """)
                    
                    await asyncio.sleep(self.settings.delays.click_delay)
                    
        except Exception as e:
            self.logger.error(f"处理选择题失败: {e}")
    
    async def _handle_fill_blanks(self, answers: str):
        """处理填空题"""
        try:
            lines = answers.split('\n')
            clean_answers = []
            
            for line in lines:
                # 移除编号
                clean_line = re.sub(r'^\d+[\.)]\s*', '', line.strip())
                if clean_line:
                    clean_answers.append(clean_line)
            
            self.logger.debug(f"处理填空题: {clean_answers}")
            
            # 获取所有输入框
            inputs = await self.browser.execute_script("""
                return Array.from(document.querySelectorAll('input[type="text"], textarea'))
                    .map((el, index) => index);
            """)
            
            for i, answer in enumerate(clean_answers):
                if i < len(inputs):
                    await self.browser.execute_script(f"""
                        const inputs = document.querySelectorAll('input[type="text"], textarea');
                        if (inputs[{i}]) {{
                            inputs[{i}].value = '{answer}';
                            inputs[{i}].dispatchEvent(new Event('input', {{ bubbles: true }}));
                            inputs[{i}].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    """)
                    
                    await asyncio.sleep(self.settings.delays.type_delay)
                    
        except Exception as e:
            self.logger.error(f"处理填空题失败: {e}")
    
    async def _handle_text_answer(self, answer: str):
        """处理文本答案（翻译、作文等）"""
        try:
            self.logger.debug("处理文本答案")
            
            # 查找文本区域
            if await self.browser.wait_for_element(self.selectors["textareas"]):
                await self.browser.type_text(self.selectors["textareas"], answer)
            else:
                # 尝试富文本编辑器
                await self.browser.execute_script(f"""
                    const editor = document.querySelector('.editor-content, [contenteditable="true"]');
                    if (editor) {{
                        editor.innerHTML = '{answer}';
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                """)
                
        except Exception as e:
            self.logger.error(f"处理文本答案失败: {e}")
    
    async def process_current_page(self) -> bool:
        """处理当前页面"""
        try:
            self.logger.info("开始处理当前页面")
            
            # 处理弹窗
            await self.handle_popups()
            
            # 等待页面加载
            await asyncio.sleep(self.settings.delays.page_load)
            
            # 检查是否有视频
            if await self.browser.wait_for_element(self.selectors["video"], timeout=2000):
                return await self.handle_video()
            
            # 检查是否有题目
            has_questions = await self.browser.execute_script("""
                return document.querySelector('input[type="radio"], input[type="checkbox"], input[type="text"], textarea') !== null;
            """)
            
            if has_questions:
                return await self.handle_questions()
            
            self.logger.warning("未发现可处理的内容")
            return False
            
        except Exception as e:
            self.logger.error(f"处理页面失败: {e}")
            return False
    
    async def start_automation(self):
        """开始自动化处理"""
        try:
            self._running = True
            self.logger.info("开始自动化处理")
            
            while self._running:
                # 处理当前页面
                success = await self.process_current_page()
                
                if success:
                    # 等待一下再继续
                    await asyncio.sleep(2)
                    
                    # 尝试点击继续按钮
                    if await self.browser.click_element(self.selectors["continue_button"]):
                        self.logger.info("点击继续按钮")
                        await asyncio.sleep(3)
                    else:
                        # 没有继续按钮，可能已完成
                        self.logger.info("未找到继续按钮，可能已完成当前任务")
                        break
                else:
                    # 处理失败，等待一下再重试
                    await asyncio.sleep(5)
                
                # 检查是否需要停止
                if not self._running:
                    break
                    
        except Exception as e:
            self.logger.error(f"自动化处理失败: {e}")
        finally:
            self._running = False
    
    async def stop_automation(self):
        """停止自动化处理"""
        self._running = False
        self.logger.info("停止自动化处理")
    
    async def run_auto_mode(self):
        """运行自动模式"""
        try:
            # 导航到登录页面
            if not await self.navigate_to_login():
                raise RuntimeError("无法访问登录页面")
            
            # 登录
            if not await self.login():
                raise RuntimeError("登录失败")
            
            # 开始自动化处理
            await self.start_automation()
            
        except Exception as e:
            self.logger.error(f"自动模式运行失败: {e}")
            raise
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running
    
    async def cleanup(self):
        """清理资源"""
        try:
            await self.stop_automation()
            self.logger.info("U校园自动化模块清理完成")
        except Exception as e:
            self.logger.error(f"清理失败: {e}")
