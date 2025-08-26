#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能答题系统使用示例
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import Settings
from src.automation.browser_manager import BrowserManager
from src.intelligence.smart_answering import SmartAnsweringStrategy

async def example_single_intelligent_answering():
    """单题智能答题示例"""
    print("🧠 单题智能答题示例")
    print("=" * 50)
    
    # 初始化配置
    settings = Settings()
    
    # 初始化浏览器管理器
    browser_manager = BrowserManager(settings)
    
    try:
        # 启动浏览器
        await browser_manager.start()
        print("✅ 浏览器启动成功")
        
        # 初始化智能答题策略
        smart_answering = SmartAnsweringStrategy(browser_manager, settings)
        print("✅ 智能答题策略初始化完成")
        
        # 导航到题目页面（这里使用示例URL，实际使用时请替换）
        test_url = "https://ucontent.unipus.cn/course/..."  # 替换为实际的题目URL
        print(f"🌐 导航到页面: {test_url}")
        
        success = await browser_manager.navigate_to(test_url)
        if not success:
            print("❌ 页面导航失败")
            return
        
        print("✅ 页面导航成功")
        
        # 执行智能答题
        print("🚀 开始智能答题...")
        result = await smart_answering.process_question_intelligently()
        
        # 显示结果
        if result['success']:
            print(f"✅ 智能答题成功！")
            print(f"   策略: {result['strategy']}")
            print(f"   答案: {result.get('answer', 'N/A')}")
            print(f"   已提交: {'是' if result.get('submitted', False) else '否'}")
        else:
            print(f"❌ 智能答题失败")
            print(f"   原因: {result.get('reason', 'unknown')}")
            if 'error' in result:
                print(f"   错误: {result['error']}")
        
        # 显示统计信息
        stats = smart_answering.get_strategy_stats()
        print("\n📊 统计信息:")
        print(f"   缓存命中率: {stats.get('cache_hit_rate', 0):.1%}")
        print(f"   提取成功率: {stats.get('extraction_success_rate', 0):.1%}")
        
        cache_stats = stats.get('cache_stats', {})
        if cache_stats:
            print(f"   缓存条目数: {cache_stats.get('total_entries', 0)}")
            print(f"   已验证条目: {cache_stats.get('verified_entries', 0)}")
        
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
    
    finally:
        # 清理资源
        await smart_answering.cleanup()
        await browser_manager.close()
        print("🧹 资源清理完成")

async def example_batch_intelligent_answering():
    """批量智能答题示例"""
    print("\n🚀 批量智能答题示例")
    print("=" * 50)
    
    # 初始化配置
    settings = Settings()
    
    # 初始化浏览器管理器
    browser_manager = BrowserManager(settings)
    
    try:
        # 启动浏览器
        await browser_manager.start()
        print("✅ 浏览器启动成功")
        
        # 初始化智能答题策略
        smart_answering = SmartAnsweringStrategy(browser_manager, settings)
        print("✅ 智能答题策略初始化完成")
        
        # 登录U校园（需要配置用户名密码）
        login_url = "https://sso.unipus.cn/"
        print(f"🔐 导航到登录页面: {login_url}")
        
        await browser_manager.navigate_to(login_url)
        
        # 这里需要实现登录逻辑，或者手动登录后继续
        print("⚠️  请手动登录后按回车继续...")
        input()
        
        # 定义要处理的单元范围
        unit_range = range(1, 4)  # Unit 1 到 Unit 3
        print(f"📚 处理单元范围: Unit {unit_range.start} - Unit {unit_range.stop - 1}")
        
        # 批量处理结果
        results = []
        
        for unit_num in unit_range:
            print(f"\n📖 处理 Unit {unit_num}")
            
            # 构造单元URL（需要根据实际情况调整）
            unit_url = f"https://ucontent.unipus.cn/course/unit/u{unit_num}"
            
            try:
                # 导航到单元页面
                await browser_manager.navigate_to(unit_url)
                await asyncio.sleep(2)
                
                # 查找单元中的任务
                tasks = await browser_manager.execute_script("""
                    const tasks = [];
                    const taskLinks = document.querySelectorAll('a[href*="iexplore"], a[href*="unittest"]');
                    
                    taskLinks.forEach(link => {
                        tasks.push({
                            name: link.textContent.trim(),
                            url: link.href
                        });
                    });
                    
                    return tasks;
                """)
                
                print(f"   找到 {len(tasks)} 个任务")
                
                # 处理每个任务
                for task in tasks:
                    print(f"   🎯 处理任务: {task['name']}")
                    
                    try:
                        # 导航到任务页面
                        await browser_manager.navigate_to(task['url'])
                        await asyncio.sleep(2)
                        
                        # 智能答题
                        result = await smart_answering.process_question_intelligently()
                        result['unit'] = f"Unit {unit_num}"
                        result['task'] = task['name']
                        results.append(result)
                        
                        if result['success']:
                            print(f"      ✅ 成功 - 策略: {result['strategy']}")
                        else:
                            print(f"      ❌ 失败 - 原因: {result.get('reason', 'unknown')}")
                        
                        # 等待一下再处理下一个
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        print(f"      ❌ 任务处理失败: {e}")
                        results.append({
                            'success': False,
                            'unit': f"Unit {unit_num}",
                            'task': task['name'],
                            'error': str(e)
                        })
            
            except Exception as e:
                print(f"   ❌ 单元处理失败: {e}")
                results.append({
                    'success': False,
                    'unit': f"Unit {unit_num}",
                    'error': str(e)
                })
        
        # 统计结果
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        
        print(f"\n📊 批量处理结果:")
        print(f"   总任务数: {total}")
        print(f"   成功数: {successful}")
        print(f"   失败数: {total - successful}")
        print(f"   成功率: {successful / total * 100:.1f}%" if total > 0 else "   成功率: 0%")
        
        # 显示详细结果
        print(f"\n📋 详细结果:")
        for result in results:
            status = "✅" if result.get('success', False) else "❌"
            unit = result.get('unit', 'Unknown')
            task = result.get('task', 'Unknown')
            strategy = result.get('strategy', result.get('reason', result.get('error', 'Unknown')))
            print(f"   {status} {unit} - {task} ({strategy})")
        
    except Exception as e:
        print(f"❌ 批量示例执行失败: {e}")
    
    finally:
        # 清理资源
        await smart_answering.cleanup()
        await browser_manager.close()
        print("🧹 资源清理完成")

async def example_cache_management():
    """缓存管理示例"""
    print("\n💾 缓存管理示例")
    print("=" * 50)
    
    # 初始化配置
    settings = Settings()
    
    # 直接使用缓存管理器
    from src.intelligence.answer_cache import AnswerCache
    from src.intelligence.answer_extractor import QuestionInfo, QuestionType
    
    cache = AnswerCache(settings.data_dir / "intelligent_cache")
    
    # 创建示例题目
    question1 = QuestionInfo(
        question_id="example_1",
        question_type=QuestionType.MULTIPLE_CHOICE,
        question_text="What is the capital of China?",
        unit="Unit 1",
        task="iExplore 1: Learning before class"
    )
    
    question2 = QuestionInfo(
        question_id="example_2",
        question_type=QuestionType.FILL_BLANK,
        question_text="Fill in the blanks: Beijing is the _____ of China.",
        unit="Unit 1",
        task="iExplore 1: Learning before class"
    )
    
    # 存储答案
    print("📝 存储示例答案...")
    await cache.store_answer(question1, "A", confidence=0.9)
    await cache.store_answer(question2, "capital", confidence=0.8)
    print("✅ 答案存储完成")
    
    # 获取答案
    print("\n🔍 获取缓存答案...")
    answer1 = await cache.get_answer(question1)
    answer2 = await cache.get_answer(question2)
    
    print(f"   问题1答案: {answer1}")
    print(f"   问题2答案: {answer2}")
    
    # 验证答案
    print("\n✅ 验证答案...")
    question_id1 = cache._generate_question_id(question1)
    await cache.verify_answer(question_id1, is_correct=True)
    print("   问题1验证为正确")
    
    # 显示缓存统计
    print("\n📊 缓存统计:")
    stats = cache.get_cache_stats()
    
    print(f"   总缓存条目: {stats.get('total_entries', 0)}")
    print(f"   已验证条目: {stats.get('verified_entries', 0)}")
    print(f"   验证率: {stats.get('verification_rate', 0):.1%}")
    print(f"   缓存大小: {stats.get('cache_size_mb', 0):.2f} MB")
    
    # 按单元统计
    unit_stats = stats.get('unit_stats', {})
    if unit_stats:
        print(f"\n📚 按单元统计:")
        for unit, count in unit_stats.items():
            print(f"   {unit}: {count} 个答案")
    
    # 按题型统计
    type_stats = stats.get('type_stats', {})
    if type_stats:
        print(f"\n📝 按题型统计:")
        for q_type, count in type_stats.items():
            print(f"   {q_type}: {count} 个答案")
    
    # 备份缓存
    print("\n💾 备份缓存...")
    await cache.backup_to_json()
    print("✅ 缓存备份完成")

async def example_custom_extraction():
    """自定义答案提取示例"""
    print("\n🔧 自定义答案提取示例")
    print("=" * 50)
    
    # 初始化配置
    settings = Settings()
    
    # 初始化浏览器管理器
    browser_manager = BrowserManager(settings)
    
    try:
        # 启动浏览器
        await browser_manager.start()
        print("✅ 浏览器启动成功")
        
        # 创建自定义答案提取器
        from src.intelligence.answer_extractor import AnswerExtractor
        
        extractor = AnswerExtractor(browser_manager)
        
        # 添加自定义答案模式
        extractor.answer_patterns['custom'] = [
            r'自定义答案[：:]\s*(.+?)(?:\n|$)',
            r'Custom Answer[：:]\s*(.+?)(?:\n|$)',
        ]
        
        print("✅ 自定义答案模式已添加")
        
        # 导航到测试页面
        test_url = "data:text/html,<html><body><div>自定义答案: A B C D</div></body></html>"
        await browser_manager.navigate_to(test_url)
        
        # 测试自定义提取
        html_content = await browser_manager.execute_script("return document.body.innerHTML")
        
        # 使用自定义模式提取答案
        for pattern in extractor.answer_patterns['custom']:
            import re
            match = re.search(pattern, html_content, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).strip()
                print(f"✅ 自定义提取成功: {answer}")
                break
        else:
            print("❌ 自定义提取失败")
        
    except Exception as e:
        print(f"❌ 自定义提取示例失败: {e}")
    
    finally:
        await browser_manager.close()
        print("🧹 资源清理完成")

async def main():
    """主函数"""
    print("🎓 U校园智能答题系统示例")
    print("=" * 60)
    
    examples = [
        ("1", "单题智能答题", example_single_intelligent_answering),
        ("2", "批量智能答题", example_batch_intelligent_answering),
        ("3", "缓存管理", example_cache_management),
        ("4", "自定义提取", example_custom_extraction),
        ("0", "退出", None)
    ]
    
    while True:
        print("\n📋 请选择示例:")
        for code, name, _ in examples:
            print(f"   {code}. {name}")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "0":
            print("👋 再见！")
            break
        
        # 查找对应的示例函数
        example_func = None
        for code, name, func in examples:
            if code == choice:
                example_func = func
                break
        
        if example_func:
            try:
                await example_func()
            except KeyboardInterrupt:
                print("\n⚠️  示例被用户中断")
            except Exception as e:
                print(f"\n❌ 示例执行失败: {e}")
        else:
            print("❌ 无效选择，请重试")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断，再见！")
