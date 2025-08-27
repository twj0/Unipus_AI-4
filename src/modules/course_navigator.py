#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课程导航模块 - 处理课程选择和导航
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs

from src.automation.browser_manager import BrowserManager
from src.utils.logger import LoggerMixin

class CourseNavigator(LoggerMixin):
    """课程导航器"""
    
    def __init__(self, browser_manager: BrowserManager):
        """
        初始化课程导航器
        
        Args:
            browser_manager: 浏览器管理器
        """
        self.browser = browser_manager
        self.current_course_info = {}
        
        self.logger.info("课程导航器初始化完成")
    
    async def navigate_to_course(self, course_name: str = None) -> bool:
        """
        导航到指定课程
        
        Args:
            course_name: 课程名称，如果为None则选择第一个课程
        
        Returns:
            导航是否成功
        """
        try:
            self.logger.info(f"开始导航到课程: {course_name or '默认课程'}")
            
            # 1. 确保在主页
            if not await self._ensure_on_homepage():
                return False
            
            # 2. 查找并点击目标课程
            if not await self._select_course(course_name):
                return False
            
            # 3. 等待课程页面加载
            if not await self._wait_for_course_page():
                return False
            
            # 4. 点击继续学习按钮
            if not await self._click_continue_learning():
                return False
            
            # 5. 等待学习界面加载
            if not await self._wait_for_learning_interface():
                return False
            
            self.logger.info("课程导航成功")
            return True
            
        except Exception as e:
            self.logger.error(f"课程导航失败: {e}")
            return False
    
    async def _ensure_on_homepage(self) -> bool:
        """确保在主页"""
        try:
            current_url = self.browser.page.url
            
            if "uai.unipus.cn/home" not in current_url:
                self.logger.info("导航到主页")
                if not await self.browser.navigate_to("https://uai.unipus.cn/home"):
                    return False
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 检查是否有课程列表
            course_selectors = [
                ".course-card",
                ".course-item",
                "p[title*='大学英语']",
                "div:has-text('新一代大学英语')"
            ]
            
            for selector in course_selectors:
                if await self.browser.wait_for_element(selector, timeout=10):
                    self.logger.info("主页加载成功")
                    return True
            
            self.logger.error("主页课程列表未加载")
            return False
            
        except Exception as e:
            self.logger.error(f"确保在主页失败: {e}")
            return False
    
    async def _select_course(self, course_name: str = None) -> bool:
        """选择课程"""
        try:
            # 获取所有课程元素
            courses = await self._get_available_courses()
            
            if not courses:
                self.logger.error("未找到可用课程")
                return False
            
            self.logger.info(f"找到 {len(courses)} 个课程")
            
            # 选择目标课程
            target_course = None
            
            if course_name:
                # 根据名称匹配课程
                for course in courses:
                    if course_name in course.get('name', ''):
                        target_course = course
                        break
            
            if not target_course:
                # 选择第一个课程
                target_course = courses[0]
                self.logger.info(f"选择默认课程: {target_course.get('name')}")
            
            # 点击课程
            if await self.browser.click_element(target_course['selector']):
                self.current_course_info = target_course
                self.logger.info(f"成功点击课程: {target_course.get('name')}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"选择课程失败: {e}")
            return False
    
    async def _get_available_courses(self) -> List[Dict[str, Any]]:
        """获取可用课程列表"""
        try:
            courses = []
            
            # 执行JavaScript获取课程信息
            script = """
            () => {
                const courses = [];
                
                // 查找课程元素的多种选择器
                const selectors = [
                    'p[title*="大学英语"]',
                    'p[title*="综合教程"]',
                    '.course-title',
                    '.course-name',
                    'div:has-text("新一代大学英语")'
                ];
                
                selectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach((element, index) => {
                            const name = element.textContent.trim() || element.title || '';
                            if (name && name.length > 0) {
                                courses.push({
                                    name: name,
                                    selector: selector + ':nth-of-type(' + (index + 1) + ')',
                                    element_text: name
                                });
                            }
                        });
                    } catch (e) {
                        console.log('选择器错误:', selector, e);
                    }
                });
                
                // 去重
                const uniqueCourses = [];
                const seen = new Set();
                
                courses.forEach(course => {
                    if (!seen.has(course.name)) {
                        seen.add(course.name);
                        uniqueCourses.push(course);
                    }
                });
                
                return uniqueCourses;
            }
            """
            
            courses = await self.browser.execute_script(script)
            
            if courses:
                self.logger.info(f"JavaScript获取到 {len(courses)} 个课程")
                return courses
            
            # 备用方法：直接查找元素
            fallback_selectors = [
                "p[title*='大学英语']",
                "p[title*='综合教程']",
                ".course-card",
                ".course-item"
            ]
            
            for selector in fallback_selectors:
                elements = await self.browser.page.query_selector_all(selector)
                if elements:
                    for i, element in enumerate(elements):
                        text = await element.text_content()
                        if text and text.strip():
                            courses.append({
                                'name': text.strip(),
                                'selector': f"{selector}:nth-of-type({i+1})",
                                'element_text': text.strip()
                            })
                    break
            
            return courses
            
        except Exception as e:
            self.logger.error(f"获取课程列表失败: {e}")
            return []
    
    async def _wait_for_course_page(self) -> bool:
        """等待课程页面加载"""
        try:
            # 等待URL变化
            await asyncio.sleep(3)
            
            current_url = self.browser.page.url
            self.logger.info(f"当前URL: {current_url}")
            
            # 检查是否跳转到课程详情页
            if "resource-detail" in current_url:
                self.logger.info("已跳转到课程详情页")
                
                # 等待页面内容加载
                content_selectors = [
                    "button:has-text('继续学习')",
                    ".continue-btn",
                    ".course-content",
                    ".learning-progress"
                ]
                
                for selector in content_selectors:
                    if await self.browser.wait_for_element(selector, timeout=15):
                        self.logger.info("课程页面内容加载完成")
                        return True
                
                # 即使没有找到特定元素，也等待一段时间
                await asyncio.sleep(5)
                return True
            
            self.logger.warning("未跳转到课程详情页")
            return False
            
        except Exception as e:
            self.logger.error(f"等待课程页面失败: {e}")
            return False
    
    async def _click_continue_learning(self) -> bool:
        """点击继续学习按钮"""
        try:
            # 查找继续学习按钮
            continue_selectors = [
                "button:has-text('继续学习')",
                "button:has-text('开始学习')",
                ".continue-btn",
                ".start-learning-btn",
                "a:has-text('继续学习')"
            ]
            
            for selector in continue_selectors:
                if await self.browser.click_element(selector, timeout=10):
                    self.logger.info("继续学习按钮点击成功")
                    await asyncio.sleep(3)
                    return True
            
            self.logger.warning("未找到继续学习按钮，尝试其他方式")
            
            # 尝试点击任何包含"学习"文本的按钮
            script = """
            () => {
                const buttons = document.querySelectorAll('button, a, div[role="button"]');
                for (const btn of buttons) {
                    const text = btn.textContent.trim();
                    if (text.includes('学习') || text.includes('开始') || text.includes('继续')) {
                        if (btn.offsetParent !== null && !btn.disabled) {
                            btn.click();
                            return true;
                        }
                    }
                }
                return false;
            }
            """
            
            clicked = await self.browser.execute_script(script)
            if clicked:
                self.logger.info("通过JavaScript点击学习按钮成功")
                await asyncio.sleep(3)
                return True
            
            self.logger.error("无法找到继续学习按钮")
            return False
            
        except Exception as e:
            self.logger.error(f"点击继续学习按钮失败: {e}")
            return False
    
    async def _wait_for_learning_interface(self) -> bool:
        """等待学习界面加载"""
        try:
            # 等待页面跳转
            await asyncio.sleep(5)
            
            current_url = self.browser.page.url
            self.logger.info(f"学习界面URL: {current_url}")
            
            # 检查是否跳转到学习界面
            if "ucontent.unipus.cn" in current_url:
                self.logger.info("已跳转到学习界面")
                
                # 等待学习内容加载
                learning_selectors = [
                    "textarea",
                    "input[type='radio']",
                    "input[type='checkbox']",
                    "input[type='text']",
                    "video",
                    ".question-content",
                    ".directions"
                ]
                
                # 等待任一学习元素出现
                for selector in learning_selectors:
                    if await self.browser.wait_for_element(selector, timeout=20):
                        self.logger.info(f"学习界面加载完成，检测到: {selector}")
                        
                        # 处理可能的弹窗
                        await self._handle_learning_popups()
                        
                        return True
                
                # 即使没有检测到特定元素，也认为加载成功
                self.logger.info("学习界面基本加载完成")
                await self._handle_learning_popups()
                return True
            
            self.logger.warning("未跳转到学习界面")
            return False
            
        except Exception as e:
            self.logger.error(f"等待学习界面失败: {e}")
            return False
    
    async def _handle_learning_popups(self) -> None:
        """处理学习界面的弹窗"""
        try:
            # 处理学习截止时间弹窗等
            popup_script = """
            (function() {
                let handledCount = 0;
                
                // 查找并处理弹窗
                const popupTexts = ['我知道了', '知道了', '确定', '确认', '继续', '开始'];
                const allButtons = document.querySelectorAll('button, span, div[role="button"]');
                
                allButtons.forEach(btn => {
                    const text = btn.textContent.trim();
                    if (popupTexts.some(popupText => text.includes(popupText)) && 
                        btn.offsetParent !== null && !btn.disabled) {
                        btn.click();
                        handledCount++;
                        console.log('处理学习弹窗:', text);
                    }
                });
                
                return handledCount;
            })();
            """
            
            handled_count = await self.browser.execute_script(popup_script)
            
            if handled_count and handled_count > 0:
                self.logger.info(f"处理了 {handled_count} 个学习界面弹窗")
                await asyncio.sleep(2)
            
        except Exception as e:
            self.logger.warning(f"处理学习界面弹窗失败: {e}")
    
    def get_current_course_info(self) -> Dict[str, Any]:
        """获取当前课程信息"""
        return self.current_course_info.copy()
    
    async def get_current_page_info(self) -> Dict[str, Any]:
        """获取当前页面信息"""
        try:
            current_url = self.browser.page.url
            page_title = await self.browser.page.title()
            
            # 解析URL获取课程和单元信息
            url_info = self._parse_learning_url(current_url)
            
            return {
                'url': current_url,
                'title': page_title,
                'course_info': self.current_course_info,
                'url_info': url_info
            }
            
        except Exception as e:
            self.logger.error(f"获取页面信息失败: {e}")
            return {}
    
    def _parse_learning_url(self, url: str) -> Dict[str, Any]:
        """解析学习界面URL"""
        try:
            # 提取单元信息
            unit_match = re.search(r'/u(\d+)/', url)
            unit = f"Unit {unit_match.group(1)}" if unit_match else ""
            
            # 提取任务信息
            task = ""
            if 'iexplore1' in url:
                task = 'iExplore 1'
            elif 'iexplore2' in url:
                task = 'iExplore 2'
            elif 'unittest' in url:
                task = 'Unit test'
            elif 'iprepare' in url:
                task = 'iPrepare'
            elif 'iproduce' in url:
                task = 'iProduce'
            
            return {
                'unit': unit,
                'task': task,
                'full_url': url
            }
            
        except Exception as e:
            self.logger.warning(f"解析URL失败: {e}")
            return {}
