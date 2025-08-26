#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器管理模块
"""

import asyncio
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from src.config.settings import Settings
from src.utils.logger import LoggerMixin

class BrowserManager(LoggerMixin):
    """浏览器管理器"""
    
    def __init__(self, settings: Settings):
        """
        初始化浏览器管理器
        
        Args:
            settings: 配置对象
        """
        self.settings = settings
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._running = False
        
        self.logger.info("浏览器管理器初始化完成")
    
    async def start(self):
        """启动浏览器"""
        try:
            self.logger.info("启动浏览器...")
            
            # 启动Playwright
            self.playwright = await async_playwright().start()
            
            # 选择浏览器类型
            browser_type = getattr(self.playwright, self.settings.browser.name)
            
            # 浏览器启动参数
            launch_options = {
                "headless": self.settings.browser.headless,
                "slow_mo": self.settings.browser.slow_mo,
                "args": [
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            }
            
            # 启动浏览器
            self.browser = await browser_type.launch(**launch_options)
            
            # 创建浏览器上下文
            context_options = {
                "viewport": {
                    "width": self.settings.browser.viewport_width,
                    "height": self.settings.browser.viewport_height
                },
                "user_agent": self.settings.browser.user_agent or None,
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai"
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # 设置默认超时
            self.context.set_default_timeout(self.settings.browser.timeout)
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 设置页面事件监听
            self._setup_page_listeners()
            
            self._running = True
            self.logger.info(f"浏览器启动成功: {self.settings.browser.name}")
            
        except Exception as e:
            self.logger.error(f"浏览器启动失败: {e}")
            await self.close()
            raise
    
    def _setup_page_listeners(self):
        """设置页面事件监听"""
        if not self.page:
            return
        
        # 监听页面加载
        self.page.on("load", lambda: self.logger.debug("页面加载完成"))
        
        # 监听页面错误
        self.page.on("pageerror", lambda error: self.logger.warning(f"页面错误: {error}"))
        
        # 监听控制台消息
        self.page.on("console", self._handle_console_message)
        
        # 监听请求
        self.page.on("request", lambda request: self.logger.debug(f"请求: {request.method} {request.url}"))
        
        # 监听响应
        self.page.on("response", lambda response: self.logger.debug(f"响应: {response.status} {response.url}"))
    
    def _handle_console_message(self, msg):
        """处理控制台消息"""
        level = msg.type
        text = msg.text
        
        if level == "error":
            self.logger.warning(f"页面控制台错误: {text}")
        elif level == "warning":
            self.logger.debug(f"页面控制台警告: {text}")
        else:
            self.logger.debug(f"页面控制台: {text}")
    
    async def navigate_to(self, url: str, wait_until: str = "networkidle") -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            wait_until: 等待条件
        
        Returns:
            是否导航成功
        """
        try:
            if not self.page:
                raise RuntimeError("浏览器未启动")
            
            self.logger.info(f"导航到: {url}")
            
            response = await self.page.goto(url, wait_until=wait_until)
            
            if response and response.status >= 400:
                self.logger.warning(f"页面响应状态码: {response.status}")
                return False
            
            # 等待页面加载
            await asyncio.sleep(self.settings.delays.page_load)
            
            self.logger.info("页面导航成功")
            return True
            
        except Exception as e:
            self.logger.error(f"页面导航失败: {e}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: Optional[float] = None) -> bool:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
        
        Returns:
            元素是否出现
        """
        try:
            if not self.page:
                return False
            
            timeout = timeout or self.settings.delays.element_wait * 1000
            
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
            
        except Exception as e:
            self.logger.debug(f"等待元素失败: {selector} - {e}")
            return False
    
    async def click_element(self, selector: str, timeout: Optional[float] = None) -> bool:
        """
        点击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间
        
        Returns:
            是否点击成功
        """
        try:
            if not self.page:
                return False
            
            # 等待元素出现
            if not await self.wait_for_element(selector, timeout):
                return False
            
            # 点击元素
            await self.page.click(selector)
            
            # 点击延迟
            await asyncio.sleep(self.settings.delays.click_delay)
            
            self.logger.debug(f"点击元素成功: {selector}")
            return True
            
        except Exception as e:
            self.logger.warning(f"点击元素失败: {selector} - {e}")
            return False
    
    async def type_text(self, selector: str, text: str, clear: bool = True) -> bool:
        """
        输入文本
        
        Args:
            selector: 元素选择器
            text: 输入文本
            clear: 是否先清空
        
        Returns:
            是否输入成功
        """
        try:
            if not self.page:
                return False
            
            # 等待元素出现
            if not await self.wait_for_element(selector):
                return False
            
            # 清空输入框
            if clear:
                await self.page.fill(selector, "")
            
            # 输入文本
            await self.page.type(selector, text, delay=self.settings.delays.type_delay * 1000)
            
            self.logger.debug(f"输入文本成功: {selector}")
            return True
            
        except Exception as e:
            self.logger.warning(f"输入文本失败: {selector} - {e}")
            return False
    
    async def get_element_text(self, selector: str) -> Optional[str]:
        """
        获取元素文本
        
        Args:
            selector: 元素选择器
        
        Returns:
            元素文本
        """
        try:
            if not self.page:
                return None
            
            if not await self.wait_for_element(selector):
                return None
            
            text = await self.page.text_content(selector)
            return text.strip() if text else None
            
        except Exception as e:
            self.logger.debug(f"获取元素文本失败: {selector} - {e}")
            return None
    
    async def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript脚本
        
        Args:
            script: JavaScript代码
            *args: 脚本参数
        
        Returns:
            脚本执行结果
        """
        try:
            if not self.page:
                return None
            
            result = await self.page.evaluate(script, *args)
            return result
            
        except Exception as e:
            self.logger.warning(f"执行脚本失败: {e}")
            return None
    
    async def take_screenshot(self, path: Optional[str] = None) -> Optional[str]:
        """
        截图
        
        Args:
            path: 保存路径
        
        Returns:
            截图路径
        """
        try:
            if not self.page:
                return None
            
            if path is None:
                import time
                timestamp = int(time.time())
                path = self.settings.screenshots_dir / f"screenshot_{timestamp}.png"
            
            await self.page.screenshot(path=path)
            self.logger.info(f"截图保存: {path}")
            return str(path)
            
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return None
    
    def is_running(self) -> bool:
        """检查浏览器是否运行中"""
        return self._running and self.browser is not None
    
    async def close(self):
        """关闭浏览器"""
        try:
            self._running = False
            
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self.logger.info("浏览器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭浏览器失败: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
