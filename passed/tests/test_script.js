// U校园脚本测试文件
// 用于在浏览器控制台中测试脚本功能

console.log('🎓 U校园脚本测试开始');

// 测试页面检测
function testPageDetection() {
    console.log('📍 测试页面检测功能...');
    
    const url = window.location.href;
    const hash = window.location.hash;
    
    console.log('当前URL:', url);
    console.log('当前Hash:', hash);
    
    // 解析单元信息
    const unitMatch = hash.match(/\/u(\d+)\//);
    const unit = unitMatch ? `Unit ${unitMatch[1]}` : '未识别';
    
    // 解析任务信息
    let task = '未识别';
    if (hash.includes('iexplore1')) {
        task = hash.includes('before') ? 'iExplore 1: Learning before class' : 'iExplore 1: Reviewing after class';
    } else if (hash.includes('iexplore2')) {
        task = hash.includes('before') ? 'iExplore 2: Learning before class' : 'iExplore 2: Reviewing after class';
    } else if (hash.includes('unittest')) {
        task = 'Unit test';
    }
    
    console.log('✅ 页面信息:', { unit, task });
    return { unit, task };
}

// 测试元素检测
function testElementDetection() {
    console.log('🔍 测试元素检测功能...');
    
    const elements = {
        video: document.querySelector('video'),
        radioButtons: document.querySelectorAll('input[type="radio"]'),
        checkboxes: document.querySelectorAll('input[type="checkbox"]'),
        textInputs: document.querySelectorAll('input[type="text"]'),
        textareas: document.querySelectorAll('textarea'),
        submitButtons: document.querySelectorAll('button[type="submit"], .submit-btn, .btn-primary')
    };
    
    console.log('发现的元素:');
    Object.entries(elements).forEach(([key, value]) => {
        if (value && (value.length !== undefined ? value.length > 0 : true)) {
            console.log(`  ✅ ${key}:`, value.length || 1);
        } else {
            console.log(`  ❌ ${key}: 未找到`);
        }
    });
    
    return elements;
}

// 测试答案匹配
function testAnswerMatching() {
    console.log('📝 测试答案匹配功能...');
    
    const testAnswers = {
        multipleChoice: "A B C D",
        fillBlanks: "1. answer1\n2. answer2\n3. answer3",
        translation: "This is a translation example."
    };
    
    Object.entries(testAnswers).forEach(([type, answer]) => {
        console.log(`${type}:`, answer);
        
        if (answer.match(/^[ABCD\s]+$/)) {
            console.log('  ✅ 识别为选择题');
        } else if (answer.includes('\n') && answer.match(/^\d+\./m)) {
            console.log('  ✅ 识别为填空题');
        } else {
            console.log('  ✅ 识别为翻译/作文题');
        }
    });
}

// 测试视频控制
function testVideoControl() {
    console.log('🎬 测试视频控制功能...');
    
    const video = document.querySelector('video');
    if (!video) {
        console.log('  ❌ 未找到视频元素');
        return;
    }
    
    console.log('  ✅ 找到视频元素');
    console.log('  当前播放状态:', video.paused ? '暂停' : '播放');
    console.log('  当前播放速度:', video.playbackRate);
    console.log('  视频时长:', video.duration);
    console.log('  当前时间:', video.currentTime);
    
    // 测试速度调节
    const originalSpeed = video.playbackRate;
    video.playbackRate = 2.0;
    console.log('  ✅ 播放速度已设置为 2x');
    
    setTimeout(() => {
        video.playbackRate = originalSpeed;
        console.log('  ✅ 播放速度已恢复');
    }, 1000);
}

// 测试题目填写
function testQuestionFilling() {
    console.log('✏️ 测试题目填写功能...');
    
    // 测试选择题
    const radioButtons = document.querySelectorAll('input[type="radio"]');
    if (radioButtons.length > 0) {
        console.log(`  找到 ${radioButtons.length} 个单选按钮`);
        
        // 模拟选择第一个选项
        if (radioButtons[0]) {
            radioButtons[0].checked = true;
            radioButtons[0].dispatchEvent(new Event('change', { bubbles: true }));
            console.log('  ✅ 已选择第一个选项（测试）');
            
            // 恢复
            setTimeout(() => {
                radioButtons[0].checked = false;
                console.log('  ✅ 已恢复选择状态');
            }, 1000);
        }
    }
    
    // 测试文本输入
    const textInputs = document.querySelectorAll('input[type="text"]');
    if (textInputs.length > 0) {
        console.log(`  找到 ${textInputs.length} 个文本输入框`);
        
        if (textInputs[0]) {
            const originalValue = textInputs[0].value;
            textInputs[0].value = 'test answer';
            textInputs[0].dispatchEvent(new Event('input', { bubbles: true }));
            console.log('  ✅ 已填写测试答案');
            
            // 恢复
            setTimeout(() => {
                textInputs[0].value = originalValue;
                console.log('  ✅ 已恢复原始内容');
            }, 1000);
        }
    }
}

// 测试按钮点击
function testButtonClicking() {
    console.log('🖱️ 测试按钮点击功能...');
    
    const buttons = document.querySelectorAll('button, .btn');
    console.log(`  找到 ${buttons.length} 个按钮`);
    
    buttons.forEach((btn, index) => {
        if (btn.textContent) {
            console.log(`  按钮 ${index + 1}: "${btn.textContent.trim()}"`);
        }
    });
    
    // 查找提交按钮
    const submitSelectors = [
        'button[type="submit"]',
        '.submit-btn',
        '.btn-submit',
        '.btn-primary'
    ];
    
    submitSelectors.forEach(selector => {
        const submitBtn = document.querySelector(selector);
        if (submitBtn) {
            console.log(`  ✅ 找到提交按钮: ${selector}`);
        }
    });
}

// 运行所有测试
function runAllTests() {
    console.log('🚀 开始运行所有测试...\n');
    
    try {
        testPageDetection();
        console.log('');
        
        testElementDetection();
        console.log('');
        
        testAnswerMatching();
        console.log('');
        
        testVideoControl();
        console.log('');
        
        testQuestionFilling();
        console.log('');
        
        testButtonClicking();
        console.log('');
        
        console.log('✅ 所有测试完成！');
        
    } catch (error) {
        console.error('❌ 测试过程中出现错误:', error);
    }
}

// 创建测试按钮
function createTestButton() {
    const button = document.createElement('button');
    button.innerHTML = '🧪 运行测试';
    button.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 99999;
        padding: 10px 15px;
        background: #FF9800;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 14px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    `;
    
    button.onclick = runAllTests;
    document.body.appendChild(button);
    
    console.log('🧪 测试按钮已创建，点击运行测试');
}

// 自动运行
if (window.location.href.includes('ucontent.unipus.cn')) {
    console.log('✅ 检测到U校园页面，创建测试按钮');
    setTimeout(createTestButton, 1000);
} else {
    console.log('ℹ️ 不在U校园页面，直接运行测试');
    runAllTests();
}

// 导出测试函数供手动调用
window.ucampusTest = {
    runAllTests,
    testPageDetection,
    testElementDetection,
    testAnswerMatching,
    testVideoControl,
    testQuestionFilling,
    testButtonClicking
};

console.log('💡 提示：可以通过 ucampusTest.runAllTests() 手动运行测试');
