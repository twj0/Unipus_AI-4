#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能答题系统测试
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.intelligence.answer_extractor import AnswerExtractor, QuestionInfo, QuestionType
from src.intelligence.answer_cache import AnswerCache, CacheEntry
from src.intelligence.smart_answering import SmartAnsweringStrategy
from src.automation.browser_manager import BrowserManager
from src.config.settings import Settings

class TestAnswerExtractor:
    """答案提取器测试"""
    
    @pytest.fixture
    async def mock_browser_manager(self):
        """模拟浏览器管理器"""
        browser = Mock(spec=BrowserManager)
        browser.page = Mock()
        browser.execute_script = AsyncMock()
        return browser
    
    @pytest.fixture
    def answer_extractor(self, mock_browser_manager):
        """答案提取器实例"""
        return AnswerExtractor(mock_browser_manager)
    
    @pytest.mark.asyncio
    async def test_detect_question_type_multiple_choice(self, answer_extractor):
        """测试检测选择题类型"""
        answer_extractor.browser.execute_script.side_effect = [
            5,  # radio buttons
            0,  # checkbox buttons
            0,  # text inputs
            0   # textareas
        ]
        
        question_type = await answer_extractor.detect_question_type()
        assert question_type == QuestionType.MULTIPLE_CHOICE
    
    @pytest.mark.asyncio
    async def test_detect_question_type_fill_blank(self, answer_extractor):
        """测试检测填空题类型"""
        answer_extractor.browser.execute_script.side_effect = [
            0,  # radio buttons
            0,  # checkbox buttons
            3,  # text inputs
            0   # textareas
        ]
        
        question_type = await answer_extractor.detect_question_type()
        assert question_type == QuestionType.FILL_BLANK
    
    @pytest.mark.asyncio
    async def test_extract_question_info(self, answer_extractor):
        """测试提取题目信息"""
        # 模拟页面信息
        page_info = {
            'url': 'https://ucontent.unipus.cn/course',
            'hash': '#/course/unit/u1/iexplore1/before',
            'title': 'U校园课程'
        }
        
        answer_extractor.browser.execute_script.side_effect = [
            page_info,  # 页面信息
            QuestionType.MULTIPLE_CHOICE.value,  # 题目类型检测的各个步骤
            5, 0, 0, 0,  # detect_question_type
            "What is the capital of China?",  # 题目文本
            ["A. Beijing", "B. Shanghai", "C. Guangzhou", "D. Shenzhen"]  # 选项
        ]
        
        # 模拟detect_question_type方法
        with patch.object(answer_extractor, 'detect_question_type', return_value=QuestionType.MULTIPLE_CHOICE):
            question_info = await answer_extractor.extract_question_info()
        
        assert question_info.unit == "Unit 1"
        assert question_info.task == "iExplore 1: Learning before class"
        assert question_info.question_type == QuestionType.MULTIPLE_CHOICE
        assert "capital of China" in question_info.question_text
    
    @pytest.mark.asyncio
    async def test_perform_trial_answer_multiple_choice(self, answer_extractor):
        """测试选择题试答"""
        question_info = QuestionInfo(
            question_id="test_id",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="Test question"
        )
        
        answer_extractor.browser.execute_script.return_value = True
        
        result = await answer_extractor.perform_trial_answer(question_info)
        assert result is True
    
    def test_extract_answer_from_html(self, answer_extractor):
        """测试从HTML提取答案"""
        html_content = """
        <div class="feedback">
            <p>正确答案: A</p>
            <p>解析: 这是正确答案的解释</p>
        </div>
        """
        
        question_info = QuestionInfo(
            question_id="test_id",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="Test question"
        )
        
        answer = answer_extractor._extract_answer_from_html(html_content, question_info)
        assert answer == "A"

class TestAnswerCache:
    """答案缓存测试"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """临时缓存目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def answer_cache(self, temp_cache_dir):
        """答案缓存实例"""
        return AnswerCache(temp_cache_dir)
    
    @pytest.fixture
    def sample_question_info(self):
        """示例题目信息"""
        return QuestionInfo(
            question_id="test_question_1",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What is the capital of China?",
            unit="Unit 1",
            task="iExplore 1: Learning before class"
        )
    
    @pytest.mark.asyncio
    async def test_store_and_get_answer(self, answer_cache, sample_question_info):
        """测试存储和获取答案"""
        correct_answer = "A"
        
        # 存储答案
        success = await answer_cache.store_answer(sample_question_info, correct_answer, confidence=0.9)
        assert success is True
        
        # 获取答案
        retrieved_answer = await answer_cache.get_answer(sample_question_info)
        assert retrieved_answer == correct_answer
    
    @pytest.mark.asyncio
    async def test_fuzzy_matching(self, answer_cache):
        """测试模糊匹配"""
        # 存储原始答案
        original_question = QuestionInfo(
            question_id="original",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What is the capital city of China?",
            unit="Unit 1",
            task="iExplore 1: Learning before class"
        )
        
        await answer_cache.store_answer(original_question, "A", confidence=0.9)
        
        # 查找相似题目
        similar_question = QuestionInfo(
            question_id="similar",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What is the capital of China?",  # 稍有不同
            unit="Unit 1",
            task="iExplore 1: Learning before class"
        )
        
        # 应该能通过模糊匹配找到答案
        answer = await answer_cache.get_answer(similar_question)
        assert answer == "A"
    
    @pytest.mark.asyncio
    async def test_verify_answer(self, answer_cache, sample_question_info):
        """测试答案验证"""
        # 存储答案
        await answer_cache.store_answer(sample_question_info, "A", confidence=0.8)
        
        # 获取question_id
        question_id = answer_cache._generate_question_id(sample_question_info)
        
        # 验证答案正确
        success = await answer_cache.verify_answer(question_id, is_correct=True)
        assert success is True
        
        # 检查置信度是否提高
        cache_entry = answer_cache.memory_cache[question_id]
        assert cache_entry.confidence > 0.8
        assert cache_entry.verified is True
    
    def test_calculate_text_similarity(self, answer_cache):
        """测试文本相似度计算"""
        text1 = "What is the capital of China?"
        text2 = "What is the capital city of China?"
        
        similarity = answer_cache._calculate_text_similarity(text1, text2)
        assert 0.8 < similarity < 1.0  # 应该有较高的相似度
        
        # 完全相同的文本
        similarity_same = answer_cache._calculate_text_similarity(text1, text1)
        assert similarity_same == 1.0
        
        # 完全不同的文本
        text3 = "How old are you?"
        similarity_diff = answer_cache._calculate_text_similarity(text1, text3)
        assert similarity_diff < 0.3  # 应该有较低的相似度
    
    def test_get_cache_stats(self, answer_cache):
        """测试获取缓存统计"""
        stats = answer_cache.get_cache_stats()
        
        assert 'total_entries' in stats
        assert 'verified_entries' in stats
        assert 'verification_rate' in stats
        assert 'unit_stats' in stats
        assert 'type_stats' in stats

class TestSmartAnsweringStrategy:
    """智能答题策略测试"""
    
    @pytest.fixture
    def mock_browser_manager(self):
        """模拟浏览器管理器"""
        browser = Mock(spec=BrowserManager)
        browser.page = Mock()
        browser.execute_script = AsyncMock()
        browser.click_element = AsyncMock()
        return browser
    
    @pytest.fixture
    def mock_settings(self, temp_cache_dir):
        """模拟设置"""
        settings = Mock(spec=Settings)
        settings.data_dir = temp_cache_dir
        settings.answer = Mock()
        settings.answer.auto_submit = True
        return settings
    
    @pytest.fixture
    def temp_cache_dir(self):
        """临时缓存目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def smart_answering(self, mock_browser_manager, mock_settings):
        """智能答题策略实例"""
        return SmartAnsweringStrategy(mock_browser_manager, mock_settings)
    
    @pytest.mark.asyncio
    async def test_try_cached_answer_success(self, smart_answering):
        """测试缓存答案成功"""
        # 模拟从缓存获取答案
        sample_question = QuestionInfo(
            question_id="cached_question",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="Cached question",
            unit="Unit 1",
            task="Test task"
        )
        
        with patch.object(smart_answering.answer_extractor, 'extract_question_info', return_value=sample_question):
            with patch.object(smart_answering.answer_cache, 'get_answer', return_value="A"):
                with patch.object(smart_answering, '_fill_answer', return_value=True):
                    with patch.object(smart_answering, '_submit_answer', return_value=True):
                        result = await smart_answering._try_cached_answer()
        
        assert result['success'] is True
        assert result['strategy'] == 'cached'
        assert result['answer'] == 'A'
    
    @pytest.mark.asyncio
    async def test_try_cached_answer_miss(self, smart_answering):
        """测试缓存未命中"""
        sample_question = QuestionInfo(
            question_id="uncached_question",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="Uncached question",
            unit="Unit 1",
            task="Test task"
        )
        
        with patch.object(smart_answering.answer_extractor, 'extract_question_info', return_value=sample_question):
            with patch.object(smart_answering.answer_cache, 'get_answer', return_value=None):
                result = await smart_answering._try_cached_answer()
        
        assert result['success'] is False
        assert result['reason'] == 'no_cached_answer'
    
    @pytest.mark.asyncio
    async def test_fill_multiple_choice_answer(self, smart_answering):
        """测试填写选择题答案"""
        smart_answering.browser.execute_script.return_value = True
        
        result = await smart_answering._fill_multiple_choice_answer("A B C")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_fill_blank_answer(self, smart_answering):
        """测试填写填空题答案"""
        smart_answering.browser.execute_script.return_value = True
        
        answer = "1) first answer\n2) second answer\n3) third answer"
        result = await smart_answering._fill_blank_answer(answer)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_submit_answer(self, smart_answering):
        """测试提交答案"""
        smart_answering.browser.click_element.return_value = True
        
        result = await smart_answering._submit_answer()
        assert result is True
    
    def test_get_strategy_stats(self, smart_answering):
        """测试获取策略统计"""
        # 模拟一些统计数据
        smart_answering.stats['cache_hits'] = 10
        smart_answering.stats['cache_misses'] = 5
        smart_answering.stats['extractions_attempted'] = 3
        smart_answering.stats['extractions_successful'] = 2
        
        with patch.object(smart_answering.answer_cache, 'get_cache_stats', return_value={'total_entries': 15}):
            stats = smart_answering.get_strategy_stats()
        
        assert 'strategy_stats' in stats
        assert 'cache_hit_rate' in stats
        assert 'extraction_success_rate' in stats
        assert 'cache_stats' in stats
        
        assert stats['cache_hit_rate'] == 10 / 15  # 10 hits out of 15 total attempts
        assert stats['extraction_success_rate'] == 2 / 3  # 2 successful out of 3 attempts

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_intelligent_answering_flow(self):
        """测试完整的智能答题流程"""
        # 这个测试需要更复杂的模拟，暂时跳过
        pytest.skip("需要完整的浏览器环境")
    
    @pytest.mark.asyncio
    async def test_cache_persistence(self):
        """测试缓存持久化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            # 创建第一个缓存实例
            cache1 = AnswerCache(cache_dir)
            
            question_info = QuestionInfo(
                question_id="persistence_test",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text="Persistence test question",
                unit="Unit 1",
                task="Test task"
            )
            
            # 存储答案
            await cache1.store_answer(question_info, "A", confidence=0.9)
            
            # 创建第二个缓存实例（模拟重启）
            cache2 = AnswerCache(cache_dir)
            
            # 应该能够获取之前存储的答案
            answer = await cache2.get_answer(question_info)
            assert answer == "A"

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
