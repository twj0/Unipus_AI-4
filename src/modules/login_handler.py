#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录处理模块 - 处理U校园登录流程
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from src.automation.browser_manager import BrowserManager
from src.utils.logger import LoggerMixin

class LoginHandler(LoggerMixin):
    """登录处理器"""
    
    def __init__(self, browser_manager: BrowserManager):
        """
        初始化登录处理器
        
        Args:
            browser_manager: 浏览器管理器
        """
        self.browser = browser_manager
        self.session_file = Path("data/session_data/login_session.json")
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("登录处理器初始化完成")
    
    async def login(self, username: str, password: str, save_session: bool = True) -> bool:
        """
        执行登录流程
        
        Args:
            username: 用户名
            password: 密码
            save_session: 是否保存会话
        
        Returns:
            登录是否成功
        """
        try:
            self.logger.info("开始登录流程")
            
            # 1. 尝试使用保存的会话
            if save_session and await self._try_saved_session():
                self.logger.info("使用保存的会话登录成功")
                return True
            
            # 2. 执行完整登录流程
            success = await self._perform_full_login(username, password)
            
            if success and save_session:
                # 3. 保存会话信息
                await self._save_session()
            
            return success
            
        except Exception as e:
            self.logger.error(f"登录流程异常: {e}")
            return False
    
    async def _try_saved_session(self) -> bool:
        """尝试使用保存的会话"""
        try:
            if not self.session_file.exists():
                return False
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # 检查会话是否过期
            import time
            if time.time() - session_data.get('timestamp', 0) > 86400:  # 24小时
                self.logger.info("保存的会话已过期")
                return False
            
            # 设置cookies
            if 'cookies' in session_data:
                await self.browser.context.add_cookies(session_data['cookies'])
            
            # 验证会话是否有效
            await self.browser.navigate_to("https://uai.unipus.cn/home")
            
            # 检查是否已登录
            if await self._check_login_status():
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"使用保存会话失败: {e}")
            return False
    
    async def _perform_full_login(self, username: str, password: str) -> bool:
        """执行完整登录流程"""
        try:
            # 1. 访问登录页面
            if not await self._navigate_to_login_page():
                return False
            
            # 2. 处理用户协议
            await self._handle_user_agreement()
            
            # 3. 填写登录信息
            if not await self._fill_login_form(username, password):
                return False
            
            # 4. 提交登录
            if not await self._submit_login():
                return False
            
            # 5. 处理登录后弹窗
            await self._handle_post_login_popups()
            
            # 6. 验证登录结果
            return await self._check_login_status()
            
        except Exception as e:
            self.logger.error(f"完整登录流程失败: {e}")
            return False
    
    async def _navigate_to_login_page(self) -> bool:
        """导航到登录页面"""
        try:
            self.logger.info("访问U校园主页")
            
            # 访问主页
            if not await self.browser.navigate_to("https://uai.unipus.cn/"):
                return False
            
            # 点击登录按钮
            login_selectors = [
                "text=登录",
                "button:has-text('登录')",
                ".login-btn",
                "a[href*='login']"
            ]
            
            for selector in login_selectors:
                if await self.browser.click_element(selector, timeout=5):
                    self.logger.info("点击登录按钮成功")
                    break
            else:
                self.logger.error("未找到登录按钮")
                return False
            
            # 等待登录表单加载
            await asyncio.sleep(3)
            
            # 验证登录页面是否加载
            login_form_selectors = [
                "input[type='text']",
                "input[placeholder*='用户名']",
                "input[placeholder*='手机号']",
                "input[placeholder*='邮箱']"
            ]
            
            for selector in login_form_selectors:
                if await self.browser.wait_for_element(selector, timeout=10):
                    self.logger.info("登录页面加载成功")
                    return True
            
            self.logger.error("登录页面加载失败")
            return False
            
        except Exception as e:
            self.logger.error(f"导航到登录页面失败: {e}")
            return False
    
    async def _handle_user_agreement(self) -> None:
        """处理用户协议复选框"""
        try:
            # 查找未勾选的用户协议复选框
            agreement_selectors = [
                "input[type='checkbox']:not([checked])",
                "input[type='checkbox'][data-has-listeners]",
                ".help-block input[type='checkbox']"
            ]
            
            for selector in agreement_selectors:
                if await self.browser.click_element(selector, timeout=3):
                    self.logger.info("已勾选用户协议")
                    await asyncio.sleep(0.5)
                    break
            
        except Exception as e:
            self.logger.warning(f"处理用户协议失败: {e}")
    
    async def _fill_login_form(self, username: str, password: str) -> bool:
        """填写登录表单"""
        try:
            # 填写用户名
            username_selectors = [
                "input[placeholder*='手机号']",
                "input[placeholder*='邮箱']", 
                "input[placeholder*='用户名']",
                "input[type='text']:first-of-type"
            ]
            
            username_filled = False
            for selector in username_selectors:
                if await self.browser.type_text(selector, username):
                    self.logger.info("用户名填写成功")
                    username_filled = True
                    break
            
            if not username_filled:
                self.logger.error("用户名填写失败")
                return False
            
            # 填写密码
            password_selectors = [
                "input[type='password']",
                "input[placeholder*='密码']"
            ]
            
            password_filled = False
            for selector in password_selectors:
                if await self.browser.type_text(selector, password):
                    self.logger.info("密码填写成功")
                    password_filled = True
                    break
            
            if not password_filled:
                self.logger.error("密码填写失败")
                return False
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            self.logger.error(f"填写登录表单失败: {e}")
            return False
    
    async def _submit_login(self) -> bool:
        """提交登录"""
        try:
            # 查找登录按钮
            login_button_selectors = [
                "button:has-text('登录')",
                "button:has-text('登 录')",
                ".login-btn",
                "input[type='submit']",
                "button[type='submit']"
            ]
            
            for selector in login_button_selectors:
                if await self.browser.click_element(selector, timeout=5):
                    self.logger.info("登录按钮点击成功")
                    break
            else:
                self.logger.error("未找到登录按钮")
                return False
            
            # 等待页面跳转
            await asyncio.sleep(5)
            return True
            
        except Exception as e:
            self.logger.error(f"提交登录失败: {e}")
            return False
    
    async def _handle_post_login_popups(self) -> None:
        """处理登录后的弹窗"""
        try:
            # 执行弹窗处理脚本
            popup_script = """
            (function() {
                let handledCount = 0;
                
                // 弹窗选择器
                const popupSelectors = [
                    'button:contains("知道了")',
                    'button:contains("我知道了")',
                    'button:contains("确定")',
                    'button:contains("确认")',
                    'button:contains("OK")',
                    '.ant-btn-primary',
                    '.confirm-btn',
                    '.ok-btn'
                ];
                
                // 处理所有按钮
                const allButtons = document.querySelectorAll('button, span, div[role="button"]');
                allButtons.forEach(btn => {
                    const text = btn.textContent.trim();
                    if ((text.includes('知道了') || text.includes('确定') || 
                         text.includes('确认') || text.includes('我同意')) && 
                        btn.offsetParent !== null && !btn.disabled) {
                        btn.click();
                        handledCount++;
                        console.log('处理弹窗:', text);
                    }
                });
                
                return handledCount;
            })();
            """
            
            handled_count = await self.browser.execute_script(popup_script)
            
            if handled_count and handled_count > 0:
                self.logger.info(f"处理了 {handled_count} 个登录后弹窗")
                await asyncio.sleep(2)
            
        except Exception as e:
            self.logger.warning(f"处理登录后弹窗失败: {e}")
    
    async def _check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 检查当前URL
            current_url = self.browser.page.url
            if "uai.unipus.cn/home" in current_url:
                self.logger.info("登录成功 - URL验证通过")
                return True
            
            # 检查用户信息元素
            user_info_selectors = [
                "text*='同学'",
                "text*='你好'",
                ".user-info",
                ".username"
            ]
            
            for selector in user_info_selectors:
                if await self.browser.wait_for_element(selector, timeout=5):
                    self.logger.info("登录成功 - 用户信息验证通过")
                    return True
            
            self.logger.warning("登录状态验证失败")
            return False
            
        except Exception as e:
            self.logger.error(f"检查登录状态失败: {e}")
            return False
    
    async def _save_session(self) -> None:
        """保存会话信息"""
        try:
            # 获取cookies
            cookies = await self.browser.context.cookies()
            
            # 保存会话数据
            session_data = {
                'timestamp': time.time(),
                'cookies': cookies,
                'url': self.browser.page.url
            }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info("会话信息已保存")
            
        except Exception as e:
            self.logger.warning(f"保存会话信息失败: {e}")
