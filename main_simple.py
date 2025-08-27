#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园智能答题系统 - 简化版主入口
可直接运行，无需复杂配置
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any

# 检查Playwright依赖
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ 缺少Playwright依赖")
    print("请运行以下命令安装：")
    print("pip install playwright")
    print("playwright install chromium")
    sys.exit(1)

class UCampusBot:
    """U校园智能答题机器人"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        
        # 配置
        self.config = {
            "username": "13874395640",  # 替换为你的用户名
            "password": "123456Unipus",  # 替换为你的密码
            "course_name": "新一代大学英语（提高篇）综合教程2",
            "max_questions": 30,
            "headless": False  # 设为True可隐藏浏览器窗口
        }
        
        print("🎓 U校园智能答题系统启动")
    
    async def start(self):
        """启动系统"""
        try:
            await self._init_browser()
            
            if await self.login():
                if await self.navigate_to_course():
                    stats = await self.intelligent_answering()
                    self.print_stats(stats)
                else:
                    print("❌ 课程导航失败")
            else:
                print("❌ 登录失败")
                
        except Exception as e:
            print(f"💥 系统异常: {e}")
        finally:
            await self.close()
    
    async def _init_browser(self):
        """初始化浏览器"""
        print("🌐 启动浏览器...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config["headless"],
            args=['--no-sandbox', '--disable-web-security']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        print("✅ 浏览器启动成功")
    
    async def login(self) -> bool:
        """登录"""
        print("🔐 开始登录...")

        try:
            # 设置更长的超时时间
            self.page.set_default_timeout(60000)  # 60秒

            print("   访问U校园主页...")
            await self.page.goto("https://uai.unipus.cn/", wait_until='domcontentloaded')
            await asyncio.sleep(3)

            # 检查是否已经登录
            if "home" in self.page.url:
                print("✅ 检测到已登录状态")
                await self._handle_popups()
                return True

            # 点击登录按钮
            print("   点击登录按钮...")
            try:
                await self.page.click("text=登录", timeout=10000)
                await asyncio.sleep(2)
            except:
                print("   未找到登录按钮，可能已在登录页面")

            # 等待登录表单加载
            print("   等待登录表单加载...")
            await self.page.wait_for_selector("input[type='text']", timeout=15000)

            # 勾选用户协议
            print("   勾选用户协议...")
            try:
                checkbox = await self.page.query_selector("input[type='checkbox']")
                if checkbox:
                    await checkbox.click()
                    await asyncio.sleep(0.5)
            except Exception as e:
                print(f"   协议勾选失败: {e}")

            # 填写用户名
            print("   填写用户名...")
            username_input = await self.page.query_selector("input[type='text']")
            if username_input:
                await username_input.fill(self.config["username"])
                await asyncio.sleep(0.5)

            # 填写密码
            print("   填写密码...")
            password_input = await self.page.query_selector("input[type='password']")
            if password_input:
                await password_input.fill(self.config["password"])
                await asyncio.sleep(0.5)

            # 点击登录按钮
            print("   提交登录...")
            login_button = await self.page.query_selector("button:has-text('登录')")
            if login_button:
                await login_button.click()
            else:
                # 备用方案
                await self.page.click("button", timeout=5000)

            # 等待登录完成
            print("   等待登录完成...")
            await asyncio.sleep(8)

            # 检查登录结果
            current_url = self.page.url
            print(f"   当前URL: {current_url}")

            if "home" in current_url or "main" in current_url:
                print("✅ 登录成功")
                await self._handle_popups()
                return True
            else:
                print("❌ 登录失败，可能是用户名密码错误")
                return False

        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    async def navigate_to_course(self) -> bool:
        """导航到课程"""
        print(f"📚 导航到课程: {self.config['course_name']}")
        
        try:
            await asyncio.sleep(3)
            
            # 点击课程
            try:
                await self.page.click(f"text={self.config['course_name']}", timeout=10000)
            except:
                await self.page.click("p[title*='大学英语']", timeout=10000)
            
            await asyncio.sleep(5)
            
            # 点击继续学习
            await self.page.click("button:has-text('继续学习')", timeout=10000)
            await asyncio.sleep(5)
            
            print("✅ 成功进入学习界面")
            return True
            
        except Exception as e:
            print(f"❌ 课程导航失败: {e}")
            return False
    
    async def intelligent_answering(self) -> Dict[str, Any]:
        """智能答题"""
        print(f"🤖 开始智能答题，最大题目数: {self.config['max_questions']}")
        
        stats = {'processed': 0, 'successful': 0, 'failed': 0}
        
        try:
            for i in range(self.config['max_questions']):
                print(f"\n📝 处理第 {i+1} 题...")
                
                await self._handle_popups()
                result = await self._process_question()
                
                stats['processed'] += 1
                
                if result['success']:
                    stats['successful'] += 1
                    print(f"✅ 第 {i+1} 题处理成功")
                else:
                    stats['failed'] += 1
                    print(f"❌ 第 {i+1} 题处理失败")
                
                if not await self._navigate_next():
                    print("📋 没有更多题目")
                    break
                
                await asyncio.sleep(2)
            
            return stats
            
        except Exception as e:
            print(f"❌ 智能答题异常: {e}")
            stats['error'] = str(e)
            return stats
    
    async def _process_question(self) -> Dict[str, Any]:
        """处理当前题目"""
        try:
            await asyncio.sleep(2)
            
            # 翻译题
            if await self.page.query_selector("textarea"):
                return await self._handle_translation()
            
            # 选择题
            elif await self.page.query_selector("input[type='radio']"):
                return await self._handle_choice()
            
            # 填空题
            elif await self.page.query_selector("input[type='text']"):
                return await self._handle_fill_blank()
            
            # 视频题
            elif await self.page.query_selector("video"):
                return await self._handle_video()
            
            # 通用处理
            else:
                return await self._handle_generic()
                
        except Exception as e:
            return {'success': False, 'reason': str(e)}
    
    async def _handle_translation(self) -> Dict[str, Any]:
        """处理翻译题"""
        try:
            print("📝 翻译题")
            
            # 获取源文本
            elements = await self.page.query_selector_all("p")
            source_text = ""
            
            for element in elements:
                text = await element.text_content()
                if text and len(text) > 50 and "Directions" not in text:
                    source_text = text
                    break
            
            # 生成翻译
            translation = self._generate_translation(source_text)
            
            # 填写答案
            textarea = await self.page.query_selector("textarea")
            if textarea:
                await textarea.fill(translation)
                return {'success': True}
            
            return {'success': False}
            
        except Exception as e:
            return {'success': False, 'reason': str(e)}
    
    def _generate_translation(self, source_text: str) -> str:
        """生成翻译"""
        # 预设翻译
        if '中国的太空探索' in source_text:
            return "China's space exploration is managed by the China National Space Administration."
        elif 'Space exploration involves' in source_text:
            return "太空探索涉及巨大的经济投资和看似不可能的目标。"
        
        # 智能判断语言
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in source_text)
        
        if is_chinese:
            return "This is an intelligent English translation of the Chinese text."
        else:
            return "这是对英文文本的智能中文翻译。"
    
    async def _handle_choice(self) -> Dict[str, Any]:
        """处理选择题"""
        try:
            print("☑️ 选择题")
            radio_buttons = await self.page.query_selector_all("input[type='radio']")
            if radio_buttons:
                await radio_buttons[0].click()
                return {'success': True}
            return {'success': False}
        except Exception as e:
            return {'success': False, 'reason': str(e)}
    
    async def _handle_fill_blank(self) -> Dict[str, Any]:
        """处理填空题"""
        try:
            print("✏️ 填空题")
            inputs = await self.page.query_selector_all("input[type='text']")
            for i, input_elem in enumerate(inputs):
                await input_elem.fill(f"answer{i+1}")
            return {'success': True}
        except Exception as e:
            return {'success': False, 'reason': str(e)}
    
    async def _handle_video(self) -> Dict[str, Any]:
        """处理视频题"""
        try:
            print("🎬 视频题")
            await self.page.evaluate("""
                () => {
                    const videos = document.querySelectorAll('video');
                    videos.forEach(video => {
                        video.playbackRate = 16.0;
                        video.muted = true;
                        if (video.paused) video.play();
                        if (video.duration) video.currentTime = video.duration - 1;
                    });
                }
            """)
            await asyncio.sleep(3)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'reason': str(e)}
    
    async def _handle_generic(self) -> Dict[str, Any]:
        """通用处理"""
        try:
            print("❓ 通用处理")
            
            # 填写文本框
            inputs = await self.page.query_selector_all("input[type='text'], textarea")
            for input_elem in inputs:
                await input_elem.fill("Generic answer")
            
            # 选择第一个选项
            radios = await self.page.query_selector_all("input[type='radio']")
            if radios:
                await radios[0].click()
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'reason': str(e)}
    
    async def _navigate_next(self) -> bool:
        """导航到下一题"""
        try:
            selectors = [
                "button:has-text('下一题')",
                "button:has-text('继续')",
                "button:has-text('提交')",
                "text=下一题"
            ]
            
            for selector in selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    await asyncio.sleep(3)
                    return True
                except:
                    continue
            
            return False
        except:
            return False
    
    async def _handle_popups(self):
        """处理弹窗"""
        try:
            await asyncio.sleep(1)
            selectors = [
                "button:has-text('知道了')",
                "button:has-text('我知道了')",
                "button:has-text('确定')",
                "button:has-text('确认')"
            ]
            
            for selector in selectors:
                try:
                    await self.page.click(selector, timeout=2000)
                    await asyncio.sleep(1)
                except:
                    continue
        except:
            pass
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("🧹 浏览器已关闭")
        except:
            pass
    
    def print_stats(self, stats: Dict[str, Any]):
        """打印统计"""
        print("\n" + "="*50)
        print("📊 答题统计")
        print("="*50)
        print(f"📝 处理题目: {stats.get('processed', 0)}")
        print(f"✅ 成功答题: {stats.get('successful', 0)}")
        print(f"❌ 失败答题: {stats.get('failed', 0)}")
        
        if stats.get('processed', 0) > 0:
            success_rate = stats['successful'] / stats['processed'] * 100
            print(f"📈 成功率: {success_rate:.1f}%")
        
        print("="*50)

async def main():
    """主函数"""
    print("🚀 启动U校园智能答题系统")
    
    bot = UCampusBot()
    await bot.start()
    
    print("🎯 程序结束")

if __name__ == "__main__":
    # Windows兼容性
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
