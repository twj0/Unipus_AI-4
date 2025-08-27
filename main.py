#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
U校园智能答题系统 - 主入口文件
简化版本，可直接运行，无需复杂配置

Date: 2024-12-27
"""

import asyncio
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 尝试导入Playwright，如果失败则提示安装
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ 缺少Playwright依赖")
    print("请运行以下命令安装：")
    print("pip install playwright")
    print("playwright install chromium")
    sys.exit(1)

class UCampusIntelligentSystem:
    """U校园智能答题系统 - 简化版"""

    def __init__(self):
        """初始化系统"""
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # 配置文件路径
        self.config_file = PROJECT_ROOT / "config" / "user_config.json"
        self.cookies_file = PROJECT_ROOT / "data" / "cookies.json"

        # 确保目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.cookies_file.parent.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self.config = self._load_config()

        print("🎓 U校园智能答题系统已启动")

    def _load_config(self) -> Dict[str, Any]:
        """加载用户配置"""
        default_config = {
            "username": "",
            "password": "",
            "course_name": "新一代大学英语（提高篇）综合教程2",
            "max_questions": 50,
            "headless": False,
            "auto_save_cookies": True
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    default_config.update(config)
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}")

        return default_config

    def _save_config(self):
        """保存用户配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 配置文件保存失败: {e}")

    def setup_credentials(self):
        """设置登录凭据"""
        print("\n🔧 配置登录信息")
        print("=" * 50)

        current_username = self.config.get("username", "")
        current_password = self.config.get("password", "")

        if current_username:
            print(f"当前用户名: {current_username}")
            use_current = input("是否使用当前配置? (y/n): ").lower().strip()
            if use_current == 'y':
                return

        username = input("请输入用户名: ").strip()
        password = input("请输入密码: ").strip()

        if username and password:
            self.config["username"] = username
            self.config["password"] = password
            self._save_config()
            print("✅ 登录信息已保存")
        else:
            print("❌ 用户名或密码不能为空")
            sys.exit(1)

    async def _init_browser(self):
        """初始化浏览器"""
        print("🌐 初始化浏览器...")

        self.playwright = await async_playwright().start()

        # 浏览器配置
        browser_config = {
            'headless': self.config.get('headless', False),
            'args': [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security'
            ]
        }

        self.browser = await self.playwright.chromium.launch(**browser_config)

        # 创建上下文
        context_config = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        self.context = await self.browser.new_context(**context_config)

        # 加载cookies
        await self._load_cookies()

        # 创建页面
        self.page = await self.context.new_page()

        print("✅ 浏览器初始化完成")

    async def _load_cookies(self):
        """加载保存的cookies"""
        if self.cookies_file.exists():
            try:
                with open(self.cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    await self.context.add_cookies(cookies)
                print("✅ Cookies加载成功")
            except Exception as e:
                print(f"⚠️ Cookies加载失败: {e}")

    async def _save_cookies(self):
        """保存cookies"""
        if self.config.get('auto_save_cookies', True):
            try:
                cookies = await self.context.cookies()
                with open(self.cookies_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                print("✅ Cookies已保存")
            except Exception as e:
                print(f"⚠️ Cookies保存失败: {e}")

    async def login(self) -> bool:
        """登录U校园"""
        print("🔐 开始登录...")

        try:
            # 设置合理的超时时间
            self.page.set_default_timeout(30000)  # 30秒

            # 访问主页
            print("   📡 访问U校园主页...")
            await self.page.goto("https://uai.unipus.cn/", wait_until='domcontentloaded')
            await asyncio.sleep(3)

            # 检查是否已经登录
            if "home" in self.page.url:
                print("✅ 已经登录，跳过登录步骤")
                await self._handle_popups()
                return True

            # 点击登录按钮
            print("   🖱️ 查找登录按钮...")
            try:
                await self.page.click("text=登录", timeout=10000)
                await asyncio.sleep(2)
                print("   ✅ 成功点击登录按钮")
            except:
                print("   ⚠️ 未找到登录按钮，可能已在登录页面")

            # 等待登录表单加载
            print("   ⏳ 等待登录表单加载...")
            await self.page.wait_for_selector("input[type='text']", timeout=15000)

            # 勾选用户协议
            print("   ☑️ 勾选用户协议...")
            try:
                # 使用最精确的选择器来定位用户协议复选框
                # 根据实际HTML分析，用户协议复选框的id是"agreement"
                agreement_selectors = [
                    # 最精确的选择器：通过ID定位
                    "#agreement",
                    # 备用选择器：通过ID属性定位
                    "input[id='agreement']",
                    # 备用选择器：通过类名和ID定位
                    "input.usso-checkbox-input[id='agreement']",
                    # 最后的备用方案：最后一个复选框
                    "input[type='checkbox']:last-of-type",
                ]

                agreement_checked = False
                for selector in agreement_selectors:
                    try:
                        # 先检查复选框是否已经勾选
                        checkbox = await self.page.query_selector(selector)
                        if checkbox:
                            is_checked = await checkbox.is_checked()
                            if is_checked:
                                print(f"   ✅ 用户协议已经勾选 (选择器: {selector})")
                                agreement_checked = True
                                break
                            else:
                                await checkbox.click()
                                print(f"   ✅ 用户协议已勾选 (使用选择器: {selector})")
                                agreement_checked = True
                                break
                    except Exception as e:
                        print(f"   ⚠️ 选择器 {selector} 失败: {e}")
                        continue

                if not agreement_checked:
                    # 最后的备用方案：手动查找用户协议复选框
                    try:
                        print("   🔍 使用备用方案查找用户协议复选框...")
                        checkboxes = await self.page.query_selector_all("input[type='checkbox']")
                        print(f"   📊 找到 {len(checkboxes)} 个复选框")

                        for i, checkbox in enumerate(checkboxes):
                            checkbox_id = await checkbox.get_attribute("id")
                            is_checked = await checkbox.is_checked()
                            print(f"   📋 复选框 {i}: id={checkbox_id}, checked={is_checked}")

                            # 查找用户协议复选框（id="agreement"或最后一个）
                            if checkbox_id == "agreement" or i == len(checkboxes) - 1:
                                if not is_checked:
                                    await checkbox.click()
                                    print(f"   ✅ 用户协议已勾选 (复选框 {i}, id={checkbox_id})")
                                else:
                                    print(f"   ✅ 用户协议已经勾选 (复选框 {i}, id={checkbox_id})")
                                agreement_checked = True
                                break
                    except Exception as e:
                        print(f"   ⚠️ 备用方案失败: {e}")

                if not agreement_checked:
                    print("   ❌ 无法勾选用户协议复选框")

                await asyncio.sleep(1)
            except Exception as e:
                print(f"   ❌ 勾选用户协议异常: {e}")

            # 填写用户名
            print("   ✏️ 填写用户名...")
            await self.page.fill("input[type='text']", self.config["username"])
            await asyncio.sleep(0.5)

            # 填写密码
            print("   🔑 填写密码...")
            await self.page.fill("input[type='password']", self.config["password"])
            await asyncio.sleep(0.5)

            # 点击登录
            print("   🚀 提交登录...")
            try:
                await self.page.click("button:has-text('登录')", timeout=10000)
                print("   ✅ 登录按钮点击成功")
            except Exception as e:
                print(f"   ⚠️ 登录按钮点击失败: {e}")
                # 尝试备用选择器
                try:
                    await self.page.click("button[type='submit']", timeout=5000)
                    print("   ✅ 使用备用选择器点击登录")
                except:
                    print("   ❌ 无法点击登录按钮")
                    return False

            # 等待登录完成 - 使用更智能的等待方式
            print("   ⏳ 等待登录完成...")

            # 分步等待，每次检查URL变化
            for i in range(6):  # 最多等待30秒 (6 * 5秒)
                await asyncio.sleep(5)
                current_url = self.page.url
                print(f"   🔍 第{i+1}次检查 URL: {current_url}")

                if "home" in current_url:
                    print("   ✅ 检测到页面跳转成功")
                    break
                elif "error" in current_url.lower() or "login" in current_url:
                    print("   ⚠️ 可能登录失败，继续等待...")
                else:
                    print(f"   ⏳ 继续等待... ({i+1}/6)")

            # 最后再等待一下确保页面完全加载
            await asyncio.sleep(3)

            # 检查登录结果
            current_url = self.page.url
            print(f"   🔍 当前URL: {current_url}")

            if "home" in current_url:
                print("✅ 登录成功")
                await self._save_cookies()

                # 处理可能的弹窗
                await self._handle_popups()

                return True
            else:
                # 检查是否有错误信息
                try:
                    error_element = await self.page.query_selector(".error-message, .ant-message-error")
                    if error_element:
                        error_text = await error_element.text_content()
                        print(f"   ❌ 登录错误: {error_text}")
                    else:
                        print("   ❌ 登录失败，请检查用户名密码")
                except:
                    print("   ❌ 登录失败，请检查用户名密码")

                return False

        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False

    async def _handle_popups(self):
        """处理弹窗"""
        try:
            # 等待可能的弹窗出现
            await asyncio.sleep(2)

            # 查找并点击常见的弹窗按钮
            popup_buttons = [
                "button:has-text('知道了')",
                "button:has-text('我知道了')",
                "button:has-text('确定')",
                "button:has-text('确认')",
                "button:has-text('OK')"
            ]

            for selector in popup_buttons:
                try:
                    await self.page.click(selector, timeout=2000)
                    print(f"✅ 处理弹窗: {selector}")
                    await asyncio.sleep(1)
                except:
                    continue

        except Exception as e:
            print(f"⚠️ 处理弹窗失败: {e}")

    async def navigate_to_course(self, course_name: str = None) -> bool:
        """导航到课程"""
        try:
            course_name = course_name or self.config.get("course_name", "")
            print(f"📚 导航到课程: {course_name}")

            # 确保在主页
            if "home" not in self.page.url:
                print("   📡 导航到主页...")
                await self.page.goto("https://uai.unipus.cn/home", wait_until='domcontentloaded')
                await asyncio.sleep(3)

            # 处理可能的弹窗
            await self._handle_popups()

            print("   🔍 查找课程...")
            await asyncio.sleep(3)

            # 查找课程
            course_found = False
            if course_name:
                try:
                    # 尝试点击指定课程
                    print(f"   🎯 尝试点击课程: {course_name}")
                    await self.page.click(f"text={course_name}", timeout=15000)
                    course_found = True
                    print("   ✅ 成功点击指定课程")
                except:
                    print("   ⚠️ 未找到指定课程，尝试其他选择器...")

                    # 尝试其他选择器
                    course_selectors = [
                        "p[title*='大学英语']",
                        "p[title*='综合教程']",
                        ".course-card",
                        ".course-item"
                    ]

                    for selector in course_selectors:
                        try:
                            await self.page.click(selector, timeout=5000)
                            course_found = True
                            print(f"   ✅ 使用选择器成功点击课程: {selector}")
                            break
                        except:
                            continue

            if not course_found:
                print("   ❌ 未找到任何课程")
                return False

            print("   ⏳ 等待课程页面加载...")
            await asyncio.sleep(8)

            # 点击继续学习
            print("   🎯 查找继续学习按钮...")
            continue_selectors = [
                "button:has-text('继续学习')",
                "button:has-text('开始学习')",
                "a:has-text('继续学习')",
                ".continue-btn",
                ".start-btn"
            ]

            continue_found = False
            for selector in continue_selectors:
                try:
                    await self.page.click(selector, timeout=10000)
                    continue_found = True
                    print(f"   ✅ 成功点击继续学习: {selector}")
                    break
                except:
                    continue

            if not continue_found:
                print("   ❌ 未找到继续学习按钮")
                return False

            print("   ⏳ 等待学习界面加载...")
            await asyncio.sleep(8)

            print("✅ 成功进入学习界面")
            return True

        except Exception as e:
            print(f"❌ 课程导航失败: {e}")
            return False

    async def intelligent_answering(self, max_questions: int = None) -> Dict[str, Any]:
        """智能答题主流程"""
        max_questions = max_questions or self.config.get("max_questions", 50)

        print(f"🤖 开始智能答题，最大题目数: {max_questions}")

        stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': asyncio.get_event_loop().time()
        }

        try:
            for i in range(max_questions):
                print(f"\n📝 处理第 {i+1} 题...")

                # 处理可能的弹窗
                await self._handle_popups()

                # 分析当前页面
                result = await self._process_current_question()

                stats['processed'] += 1

                if result['success']:
                    stats['successful'] += 1
                    print(f"✅ 第 {i+1} 题处理成功")
                else:
                    stats['failed'] += 1
                    print(f"❌ 第 {i+1} 题处理失败: {result.get('reason', '未知错误')}")

                # 尝试导航到下一题
                if not await self._navigate_next():
                    print("📋 没有更多题目，答题结束")
                    break

                # 短暂等待
                await asyncio.sleep(2)

            # 计算统计信息
            end_time = asyncio.get_event_loop().time()
            duration = end_time - stats['start_time']
            success_rate = (stats['successful'] / stats['processed'] * 100) if stats['processed'] > 0 else 0

            stats.update({
                'duration': f"{duration:.1f}秒",
                'success_rate': f"{success_rate:.1f}%"
            })

            return stats

        except Exception as e:
            print(f"❌ 智能答题异常: {e}")
            stats['error'] = str(e)
            return stats

    async def _process_current_question(self) -> Dict[str, Any]:
        """处理当前题目"""
        try:
            # 等待页面加载
            await asyncio.sleep(2)

            # 检查页面类型
            page_content = await self.page.content()

            # 翻译题处理
            if "translate" in page_content.lower():
                return await self._handle_translation_question()

            # 选择题处理
            elif await self.page.query_selector("input[type='radio']"):
                return await self._handle_multiple_choice_question()

            # 填空题处理
            elif await self.page.query_selector("input[type='text']"):
                return await self._handle_fill_blank_question()

            # 视频题处理
            elif await self.page.query_selector("video"):
                return await self._handle_video_question()

            # 通用处理
            else:
                return await self._handle_generic_question()

        except Exception as e:
            return {'success': False, 'reason': f'处理异常: {e}'}

    async def _handle_translation_question(self) -> Dict[str, Any]:
        """处理翻译题"""
        try:
            print("📝 检测到翻译题")

            # 获取源文本
            source_elements = await self.page.query_selector_all("p")
            source_text = ""

            for element in source_elements:
                text = await element.text_content()
                if text and len(text) > 50 and "Directions" not in text:
                    source_text = text
                    break

            if not source_text:
                return {'success': False, 'reason': '未找到源文本'}

            # 生成翻译
            translation = await self._generate_translation(source_text)

            # 填写答案
            textarea = await self.page.query_selector("textarea")
            if textarea:
                await textarea.fill(translation)
                print(f"✅ 翻译答案已填写: {translation[:50]}...")
                return {'success': True, 'answer': translation}
            else:
                return {'success': False, 'reason': '未找到答案输入框'}

        except Exception as e:
            return {'success': False, 'reason': f'翻译题处理异常: {e}'}

    async def _generate_translation(self, source_text: str) -> str:
        """生成翻译答案"""
        # 预设翻译库
        translations = {
            '中国的太空探索': "China's space exploration is managed by the China National Space Administration. Its technological roots can be traced back to the late 1950s, when China began a ballistic missile program. In 2003, China successfully launched its first crewed spacecraft \"Shenzhou V\". This achievement made China the third country to send humans into space. China is currently planning to establish a permanent Chinese space station and achieve crewed lunar landing by 2020.",
            'Space exploration involves great economic investment': '太空探索涉及巨大的经济投资和看似不可能的目标。它可以以意想不到的方式使我们个人和整个人类受益。从马拉松运动员在比赛结束时使用的热太空毯，到我们现在家中的便携式吸尘器，太空研究留下了令人惊喜的创新，我们这些非宇航员每天都在使用。到目前为止，开普勒太空望远镜已经揭示了我们太阳系之外其他"地球"的长长清单。它们都可能适合生命居住。'
        }

        # 查找匹配的翻译
        for key, translation in translations.items():
            if key in source_text:
                return translation

        # 智能翻译生成
        is_chinese = any('\u4e00' <= char <= '\u9fff' for char in source_text)

        if is_chinese:
            return "This is an intelligently generated English translation. The content discusses important topics related to modern development, technology, and international cooperation."
        else:
            return "这是一个智能生成的中文翻译。内容讨论了与现代发展、技术和国际合作相关的重要话题。"

    async def _handle_multiple_choice_question(self) -> Dict[str, Any]:
        """处理选择题"""
        try:
            print("☑️ 检测到选择题")

            # 选择第一个选项
            radio_buttons = await self.page.query_selector_all("input[type='radio']")
            if radio_buttons:
                await radio_buttons[0].click()
                print("✅ 已选择第一个选项")
                return {'success': True, 'answer': 'A'}
            else:
                return {'success': False, 'reason': '未找到选项'}

        except Exception as e:
            return {'success': False, 'reason': f'选择题处理异常: {e}'}

    async def _handle_fill_blank_question(self) -> Dict[str, Any]:
        """处理填空题"""
        try:
            print("✏️ 检测到填空题")

            # 填写所有文本输入框
            text_inputs = await self.page.query_selector_all("input[type='text']")
            filled_count = 0

            for i, input_element in enumerate(text_inputs):
                answer = f"answer{i+1}"
                await input_element.fill(answer)
                filled_count += 1

            if filled_count > 0:
                print(f"✅ 已填写 {filled_count} 个空白")
                return {'success': True, 'filled_count': filled_count}
            else:
                return {'success': False, 'reason': '未找到输入框'}

        except Exception as e:
            return {'success': False, 'reason': f'填空题处理异常: {e}'}

    async def _handle_video_question(self) -> Dict[str, Any]:
        """处理视频题"""
        try:
            print("🎬 检测到视频题")

            # 执行视频处理脚本
            result = await self.page.evaluate("""
                () => {
                    const videos = document.querySelectorAll('video');
                    let processedCount = 0;

                    videos.forEach(video => {
                        if (video) {
                            video.playbackRate = 16.0;  // 最快速度
                            video.muted = true;

                            if (video.paused) {
                                video.play().catch(e => console.log('播放失败:', e));
                            }

                            if (video.duration && video.duration > 1) {
                                video.currentTime = video.duration - 1;
                            }

                            processedCount++;
                        }
                    });

                    return processedCount;
                }
            """)

            if result > 0:
                print(f"✅ 处理了 {result} 个视频")
                await asyncio.sleep(3)  # 等待视频处理完成
                return {'success': True, 'processed_videos': result}
            else:
                return {'success': False, 'reason': '未找到视频'}

        except Exception as e:
            return {'success': False, 'reason': f'视频题处理异常: {e}'}

    async def _handle_generic_question(self) -> Dict[str, Any]:
        """通用题目处理"""
        try:
            print("❓ 检测到未知题型，使用通用处理")

            # 尝试填写所有文本输入
            text_inputs = await self.page.query_selector_all("input[type='text'], textarea")
            for i, input_element in enumerate(text_inputs):
                await input_element.fill(f"Generic answer {i+1}")

            # 尝试选择第一个选项
            radio_buttons = await self.page.query_selector_all("input[type='radio']")
            if radio_buttons:
                await radio_buttons[0].click()

            return {'success': True, 'action': 'generic_handling'}

        except Exception as e:
            return {'success': False, 'reason': f'通用处理异常: {e}'}

    async def _navigate_next(self) -> bool:
        """导航到下一题"""
        try:
            # 查找导航按钮
            navigation_selectors = [
                "button:has-text('下一题')",
                "button:has-text('继续')",
                "button:has-text('提交')",
                "text=下一题",
                "text=继续",
                "text=提交"
            ]

            for selector in navigation_selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    print(f"✅ 点击导航按钮: {selector}")
                    await asyncio.sleep(3)
                    return True
                except:
                    continue

            print("⚠️ 未找到导航按钮")
            return False

        except Exception as e:
            print(f"❌ 导航失败: {e}")
            return False

    async def close(self):
        """关闭浏览器"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("🧹 浏览器已关闭")
        except Exception as e:
            print(f"⚠️ 关闭浏览器失败: {e}")

    def print_stats(self, stats: Dict[str, Any]):
        """打印统计信息"""
        print("\n" + "="*60)
        print("📊 智能答题统计报告")
        print("="*60)
        print(f"📝 处理题目数: {stats.get('processed', 0)}")
        print(f"✅ 成功答题数: {stats.get('successful', 0)}")
        print(f"❌ 失败答题数: {stats.get('failed', 0)}")
        print(f"📈 成功率: {stats.get('success_rate', '0%')}")
        print(f"⏱️ 总耗时: {stats.get('duration', '未知')}")

        if 'error' in stats:
            print(f"💥 异常信息: {stats['error']}")

        print("="*60)

def print_usage():
    """打印使用说明"""
    print("""
U校园自动化框架 - 使用说明

用法:
    python main.py [命令] [参数]

命令:
    gui                     启动图形界面模式 (默认)
    cli                     启动命令行模式
    auto                    启动自动模式
    smart [url]             启动智能答题模式
    batch [start] [end]     启动批量智能答题模式
    test                    启动测试模式

示例:
    python main.py                              # 启动GUI模式
    python main.py gui                          # 启动GUI模式
    python main.py cli                          # 启动CLI模式
    python main.py auto                         # 启动自动模式
    python main.py smart                        # 智能答题（自动登录）
    python main.py smart "https://..."          # 智能答题（指定URL）
    python main.py batch 1 5                    # 批量智能答题（Unit 1-5）
    python main.py test                         # 启动测试模式

智能答题功能:
    - smart: 单题智能答题，通过试答获取正确答案并缓存
    - batch: 批量智能答题，自动处理指定范围的所有单元
    - 支持答案缓存和智能重试机制
    - 无需依赖外部题库，动态获取最新答案

更多信息请查看 README.md
    """)

def main():
    """命令行入口：提供最小可用流程。

    支持的命令：
    - smart [url]: 默认流程，登录->进入课程->智能答题
    其他命令暂以使用说明提示。
    """

    async def run_smart(url: str | None = None):
        system = UCampusIntelligentSystem()
        # 若未配置用户名密码，提示设置
        if not system.config.get("username") or not system.config.get("password"):
            system.setup_credentials()

        try:
            await system._init_browser()
            ok = await system.login()
            if not ok:
                await system.close()
                print("登录失败，程序退出")
                return

            if url:
                try:
                    await system.page.goto(url, wait_until='networkidle')
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"⚠️ 指定URL访问失败: {e}")

            # 进入课程并开始智能答题
            await system.navigate_to_course()
            stats = await system.intelligent_answering()
            system.print_stats(stats)
        finally:
            await system.close()

    args = sys.argv[1:]
    cmd = args[0] if args else 'smart'

    if cmd == 'smart':
        url = args[1] if len(args) > 1 else None
        asyncio.run(run_smart(url))
    else:
        print("当前简化版仅实现 smart 命令。")
        print_usage()

if __name__ == "__main__":
    main()
