// ==UserScript==
// @name         U校园全自动助手 (版本 19.0 - 精准提交版)
// @namespace    http://tampermonkey.net/
// @version      19.0.0
// @description  [终极形态] 引入精准提交逻辑！在每个子任务完成后立即提交，完美模拟人工操作流程。修复所有已知提交流程问题，实现无懈可击的全自动挂机。
// @author       twj0
// @match        *://ucontent.unipus.cn/*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_deleteValue
// @grant        GM_xmlhttpRequest
// @connect      raw.githubusercontent.com
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    // --- Configuration & State Management ---
    const COURSE_MAPS = {
        '新一代大学英语 综合教程1': 'https://raw.githubusercontent.com/twj0/Unipus_AI-4/main/U%E6%A0%A1%E5%9B%AD%20%E6%96%B0%E4%B8%80%E4%BB%A3%E5%A4%A7%E5%AD%A6%E8%8B%B1%E8%AF%AD%20%E7%BB%BC%E5%90%88%E6%95%99%E7%A8%8B1%E8%8B%B1%E8%AF%AD%E9%A2%98%E5%BA%93.json',
    };

    let isAutomationRunning = false;
    let isProcessing = false;
    let urlObserver = null;
    let lastAnsweredSubTask = '';

    // --- Course Structure (The "Task Map") ---
    const COURSE_DATA = {
        "UNIT_STRUCTURE": [
            // Unit 1 - 精确定义每一个子任务
            { id: "1-1", name: "Setting the scene", type: 'standalone', method: 'video' },
            { id: "1-2", name: "iExplore 1: Learning before class", type: 'composite', children: [
                { name: "Reading in detail", method: 'skip' },
                { name: "Vocabulary", method: 'vocabulary' },
                { name: "Reading comprehension", method: 'quiz', needsSubmit: true },
                { name: "Dealing with vocabulary", method: 'quiz', needsSubmit: true }
            ]},
            { id: "1-3", name: "iExplore 1: Reviewing after class", type: 'composite', children: [
                { name: "Gems of the language", method: 'video' },
                { name: "Repeating after me", method: 'skip' },
                { name: "Application", method: 'quiz', needsSubmit: true }
            ]},
            { id: "1-4", name: "iExplore 2: Learning before class", type: 'composite', children: [
                { name: "Reading in detail", method: 'skip' },
                { name: "Vocabulary", method: 'vocabulary' },
                { name: "Reading comprehension", method: 'quiz', needsSubmit: true },
                { name: "Dealing with vocabulary", method: 'quiz', needsSubmit: true }
            ]},
            { id: "1-5", name: "iExplore 2: Reviewing after class", type: 'composite', children: [ { name: "Repeating after me", method: 'skip' } ]},
            { id: "1-6", name: "Unit project", type: 'standalone', method: 'skip' },
            { id: "1-7", name: "Unit test", type: 'composite', children: [
                { name: "Part I", method: 'quiz', needsSubmit: true },
                { name: "Part II", method: 'quiz', needsSubmit: true },
                { name: "Part III", method: 'quiz', needsSubmit: true }
            ]},
            // 在此为其他单元添加详细的任务地图
        ],
        "QUESTION_BANK": {}
    };
    
    // --- Remote Loader & UI & Utilities ---
    function loadRemoteQuestionBank(courseName) {
        const url = COURSE_MAPS[courseName];
        if (!url) { log(`错误：未找到课程 "${courseName}" 的题库URL。`, 'error'); return; }
        log(`正在从远程加载 [${courseName}] 的题库...`, 'info');
        GM_xmlhttpRequest({
            method: 'GET', url: url,
            onload: function(response) {
                if (response.status === 200) {
                    try {
                        COURSE_DATA.QUESTION_BANK = JSON.parse(response.responseText);
                        log(`题库加载成功！包含 ${Object.keys(COURSE_DATA.QUESTION_BANK).length} 个单元。`, 'success');
                    } catch (e) { log('题库文件解析失败，请检查JSON格式。', 'error'); console.error(e); }
                } else { log(`获取题库失败，状态码: ${response.status}`, 'error'); }
            },
            onerror: function(error) { log('网络错误，无法加载远程题库。', 'error'); console.error(error); }
        });
    }

    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    const log = (message, type = 'info') => {
        const logContainer = document.getElementById('uca-log-container');
        if (!logContainer) return;
        const colors = { info: '#0ea5e9', success: '#22c55e', error: '#ef4444', warn: '#f97316' };
        const entry = document.createElement('div');
        entry.innerHTML = `<span style="color: #94a3b8;">[${new Date().toLocaleTimeString()}]</span> ${message}`;
        entry.style.color = colors[type] || '#64748b';
        entry.style.marginBottom = '5px';
        entry.style.fontSize = '12px';
        entry.style.fontFamily = 'monospace';
        logContainer.appendChild(entry);
        logContainer.scrollTop = logContainer.scrollHeight;
    };

    function robustClick(element) {
        if (!element) return;
        element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }

    function createControlPanel() {
        if (document.getElementById('uca-container')) return;
        const container = document.createElement('div');
        container.id = 'uca-container';
        container.style.cssText = `position: fixed; top: 20px; left: 20px; z-index: 99999; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2); width: 350px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; transition: all 0.3s ease; overflow: hidden;`;
        const titleBar = document.createElement('div');
        titleBar.textContent = 'U校园助手 v19.0';
        titleBar.style.cssText = `padding: 10px 15px; cursor: move; background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%); color: white; font-weight: 600; user-select: none; text-shadow: 0 1px 2px rgba(0,0,0,0.2);`;
        const content = document.createElement('div');
        content.style.padding = '15px';
        const selectLabel = document.createElement('label');
        selectLabel.textContent = '选择课程题库:';
        selectLabel.style.cssText = `display: block; font-size: 13px; color: #334155; margin-bottom: 8px;`;
        const courseSelect = document.createElement('select');
        courseSelect.id = 'uca-course-select';
        courseSelect.style.cssText = `width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; margin-bottom: 15px;`;
        Object.keys(COURSE_MAPS).forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            courseSelect.appendChild(option);
        });
        courseSelect.onchange = (e) => loadRemoteQuestionBank(e.target.value);
        content.appendChild(selectLabel);
        content.appendChild(courseSelect);
        const startStopButton = document.createElement('button');
        startStopButton.id = 'uca-start-stop-btn';
        startStopButton.textContent = '▶️ 开始自动学习';
        startStopButton.style.cssText = `width: 100%; padding: 12px; border: none; border-radius: 8px; background-color: #2563eb; color: white; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.2s ease;`;
        startStopButton.onclick = toggleAutomation;
        content.appendChild(startStopButton);
        const logSection = document.createElement('div');
        logSection.style.marginTop = '15px';
        const logLabel = document.createElement('label');
        logLabel.textContent = '操作日志:';
        logLabel.style.cssText = `display: block; font-size: 12px; color: #334155; margin-bottom: 5px;`;
        const logContainer = document.createElement('div');
        logContainer.id = 'uca-log-container';
        logContainer.style.cssText = `height: 200px; background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; overflow-y: auto; font-size: 12px; line-height: 1.5; color: #475569;`;
        logSection.appendChild(logLabel);
        logSection.appendChild(logContainer);
        content.appendChild(logSection);
        container.appendChild(titleBar);
        container.appendChild(content);
        document.body.appendChild(container);
        makeDraggable(container, titleBar);
        loadRemoteQuestionBank(courseSelect.value);
    }

    function makeDraggable(element, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        handle.onmousedown = (e) => {
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = () => { document.onmouseup = null; document.onmousemove = null; };
            document.onmousemove = (e) => {
                pos1 = pos3 - e.clientX;
                pos2 = pos4 - e.clientY;
                pos3 = e.clientX;
                pos4 = e.clientY;
                element.style.top = (element.offsetTop - pos2) + "px";
                element.style.left = (element.offsetLeft - pos1) + "px";
            };
        };
    }

    function toggleAutomation() {
        isAutomationRunning = !isAutomationRunning;
        const button = document.getElementById('uca-start-stop-btn');
        if (isAutomationRunning) {
            button.textContent = '⏹️ 停止自动化';
            button.style.backgroundColor = '#dc2626';
            log('自动化已启动...', 'success');
            GM_deleteValue('lastProcessedTaskName');
            lastAnsweredSubTask = '';
            startObserver();
            setTimeout(main, 1500);
        } else {
            button.textContent = '▶️ 开始自动学习';
            button.style.backgroundColor = '#2563eb';
            log('自动化已暂停。', 'warn');
            isProcessing = false;
            stopObserver();
        }
    }

    // --- Answering Engine & Task Handlers ---
    async function getPageContextAndAnswers() {
        const mainTaskElement = document.querySelector('.pc-menu-activity .pc-menu-node-name');
        const mainTaskContent = mainTaskElement ? mainTaskElement.getAttribute('title') : document.querySelector('.pc-menu-activity .pc-menu-node-name .node-name')?.textContent;
        if (!mainTaskContent) { log('无法识别主任务信息，答题终止。', 'error'); return null; }
        const unitIdMatch = mainTaskContent.match(/(\d+)-\d+/);
        if (!unitIdMatch) { log(`无法从 "${mainTaskContent}" 中解析单元ID。`, 'error'); return null; }
        const unitId = unitIdMatch[1];
        const unitKey = `Unit ${unitId}`;
        const activeSubTaskElement = document.querySelector('.pc-header-tab-activity .pc-tab-view-container[title], .pc-header-tab-activity .pc-tab-view-container > span');
        let activeSubTaskName = activeSubTaskElement ? (activeSubTaskElement.getAttribute('title') || activeSubTaskElement.textContent) : null;
        if (!activeSubTaskName && document.querySelector('.question-common-abs-test-part-name')) {
             activeSubTaskName = document.querySelector('.question-common-abs-test-part-name').textContent.trim();
        }
        if (!activeSubTaskName) { activeSubTaskName = 'Part I'; }
        if (lastAnsweredSubTask === `${mainTaskContent}-${activeSubTaskName}`) { return 'answered'; }
        const taskMapEntry = COURSE_DATA.UNIT_STRUCTURE.find(t => mainTaskContent.includes(t.id));
        const mainTaskKey = taskMapEntry ? taskMapEntry.name : mainTaskContent;
        const answers = COURSE_DATA.QUESTION_BANK[unitKey]?.[mainTaskKey]?.[activeSubTaskName];
        if (!answers) { log(`在题库中未找到答案: ${unitKey} -> ${mainTaskKey} -> ${activeSubTaskName}`, 'warn'); return null; }
        log(`已为 "${activeSubTaskName}" 找到答案。`, 'success');
        return { answers, mainTaskContent, activeSubTaskName };
    }

    async function doAnswer() {
        if (Object.keys(COURSE_DATA.QUESTION_BANK).length === 0) {
            log('题库为空，正在等待远程加载...', 'warn');
            await sleep(3000);
            if (Object.keys(COURSE_DATA.QUESTION_BANK).length === 0) { log('题库加载失败，无法答题。', 'error'); return; }
        }
        const context = await getPageContextAndAnswers();
        if (!context || context === 'answered') return;

        const { answers, mainTaskContent, activeSubTaskName } = context;
        const choiceQuestions = document.querySelectorAll('.question-common-abs-reply, .question-common-abs-banked-cloze');
        const textInputs = document.querySelectorAll('textarea.question-inputbox-input');
        const fillInBlanks = document.querySelectorAll('.fe-scoop .comp-abs-input input');
        let answered = false;

        if (choiceQuestions.length > 0 && typeof answers === 'string' && /^[A-Z](?:\s*[A-Z])*$/.test(answers.trim())) {
            const answerLetters = answers.trim().replace(/\s+/g, '');
            for (let i = 0; i < Math.min(choiceQuestions.length, answerLetters.length); i++) {
                const options = choiceQuestions[i].querySelectorAll('.option');
                for (const option of options) {
                    if (option.querySelector('.caption')?.textContent.trim() === answerLetters[i] && !option.classList.contains('selected')) {
                        robustClick(option); await sleep(200 + Math.random() * 100); answered = true; break;
                    }
                }
            }
        } else if (textInputs.length > 0 && typeof answers === 'string') {
            const answerLines = answers.split('\n').map(line => line.replace(/^\d+\.?\)?\s*/, '').trim()).filter(Boolean);
            for (let i = 0; i < Math.min(textInputs.length, answerLines.length); i++) {
                const input = textInputs[i];
                if (!input.value) {
                    input.value = answerLines[i];
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    await sleep(200);
                    answered = true;
                }
            }
        } else if (fillInBlanks.length > 0 && typeof answers === 'string') {
            const answerLines = answers.split('\n').map(line => line.replace(/^\d+\.?\)?\s*/, '').trim()).filter(Boolean);
            for (let i = 0; i < Math.min(fillInBlanks.length, answerLines.length); i++) {
                const input = fillInBlanks[i];
                if (!input.value) {
                    input.value = answerLines[i];
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    await sleep(200);
                    answered = true;
                }
            }
        }
        if (answered) {
            log(`应用答案: ${activeSubTaskName}`, "success");
            lastAnsweredSubTask = `${mainTaskContent}-${activeSubTaskName}`;
        }
    }
    
    async function handleVideoTask() {
        const video = document.querySelector('video');
        if (!video) return true;
        log("处理方法: 视频 (快进至结尾)", 'info');
        return new Promise(async (resolve) => {
            video.muted = true;
            const onCanPlay = async () => {
                video.removeEventListener('canplay', onCanPlay, true);
                video.currentTime = video.duration > 2 ? video.duration - 1.5 : 0;
                try { await video.play(); } catch(e) { log('视频播放失败，但仍将继续。', 'warn');}
                log("视频已快进到结尾。", 'success');
                resolve(true);
            };
            if (video.readyState >= 2) await onCanPlay();
            else video.addEventListener('canplay', onCanPlay, { once: true });
            setTimeout(() => resolve(true), 5000);
        });
    }

    async function handleSkippableTask(taskName) {
        log(`处理方法: 跳过 ("${taskName}")`, 'info');
        await sleep(2000 + Math.random() * 1000);
        return true;
    }

    async function handleVocabularyTask() {
        log("处理方法: 单词卡 (自动翻页)", 'info');
        if (!document.querySelector('.vocabulary-wrapper')) return true;
        let maxClicks = 50;
        while (maxClicks-- > 0) {
            if (!isAutomationRunning) return false;
            const nextButton = document.querySelector('.vocActions .next:not(.swiper-button-disabled)');
            if (!nextButton) { log("单词卡已翻完。", 'success'); return true; }
            robustClick(nextButton);
            await sleep(600 + Math.random() * 400);
        }
        log("单词卡点击次数达到上限，继续。", 'warn');
        return true;
    }

    // --- Core Automation Engine: The Task Scheduler ---
    async function main() {
        if (isProcessing || !isAutomationRunning) return;
        isProcessing = true;
        
        try {
            await sleep(3000);

            const currentMainTaskName = document.querySelector('.pc-menu-activity .pc-menu-node-name')?.getAttribute('title');
            if (!currentMainTaskName) { throw new Error("无法识别当前主任务。"); }
            
            const lastProcessed = GM_getValue('lastProcessedTaskName', '');
            if (currentMainTaskName === lastProcessed && location.href === GM_getValue('lastUrl', '')) {
                log(`检测到可能卡在任务: "${currentMainTaskName}"。强制导航。`, 'warn');
                await navigateToNextMainTask();
                return;
            }
            if (currentMainTaskName !== lastProcessed) { lastAnsweredSubTask = ''; }
            
            log(`开始处理主任务: "${currentMainTaskName}"`, 'success');

            const taskData = COURSE_DATA.UNIT_STRUCTURE.find(t => currentMainTaskName.includes(t.id));
            if (!taskData) {
                log(`未在任务地图中找到 "${currentMainTaskName}"，将尝试顺序导航。`, 'warn');
                await navigateToNextMainTask();
                return;
            }

            if (taskData.type === 'standalone') {
                await executeMethod(taskData.method, taskData.name);
                if (taskData.needsSubmit) {
                    await completeAndNavigateTaskInternal();
                }
            } else if (taskData.type === 'composite' && taskData.children) {
                const subTaskElements = Array.from(document.querySelectorAll('.pc-header-tabs-container .pc-tab-view-container'));
                
                for (const subTaskConfig of taskData.children) {
                    if (!isAutomationRunning) return;

                    const subTaskElement = subTaskElements.find(el => el.getAttribute('title') === subTaskConfig.name);

                    if (!subTaskElement) {
                        log(`未在页面上找到子任务Tab: "${subTaskConfig.name}"，跳过。`, 'warn');
                        continue;
                    }

                    log(`- 开始处理子任务: "${subTaskConfig.name}" (方法: ${subTaskConfig.method})`, 'info');
                    robustClick(subTaskElement);
                    await sleep(2500);
                    await executeMethod(subTaskConfig.method, subTaskConfig.name);
                    
                    if (subTaskConfig.needsSubmit) {
                        await completeAndNavigateTaskInternal();
                        await sleep(1500);
                    }
                }
            }

            log(`主任务 "${currentMainTaskName}" 所有部分已处理。`, 'info');
            await completeAndNavigateTaskInternal();
            
            await GM_setValue('lastProcessedTaskName', currentMainTaskName);
            await GM_setValue('lastUrl', location.href);
            await navigateToNextMainTask();

        } catch (error) {
            log(`主流程发生严重错误: ${error.message}`, 'error');
            console.error(error);
            toggleAutomation();
        } finally {
            isProcessing = false;
        }
    }

    async function executeMethod(method, name) {
        switch (method) {
            case 'video':
                await handleVideoTask();
                break;
            case 'skip':
                await handleSkippableTask(name);
                break;
            case 'vocabulary':
                await handleVocabularyTask();
                break;
            case 'quiz':
                await doAnswer();
                break;
            default:
                log(`未知的任务方法: "${method}"`, 'warn');
        }
    }

    async function completeAndNavigateTaskInternal() {
        await sleep(1000);
        const nextQuestionBtn = Array.from(document.querySelectorAll('button.ant-btn-primary')).find(btn => btn.textContent.includes('下一题'));
        if (nextQuestionBtn && !nextQuestionBtn.disabled) {
            log('找到“下一题”按钮，点击...', 'info');
            robustClick(nextQuestionBtn);
            await sleep(2000);
        }

        const submitSelectors = [
            '.question-common-course-page .btn',
            '.ant-btn-primary.ant-btn-lg',
            'button.ant-btn-primary:not([disabled])'
        ];

        for (const selector of submitSelectors) {
            const btn = document.querySelector(selector);
            if (btn && btn.offsetParent !== null && /提交|继续学习|查看/.test(btn.textContent)) {
                log(`找到提交/导航按钮: "${btn.textContent.trim()}"，点击...`, "info");
                robustClick(btn);
                await sleep(1500);
                const confirmationButton = document.querySelector('.ant-modal-confirm-btns .ant-btn-primary');
                if (confirmationButton) {
                    log("检测到提交确认弹窗，点击确定...", 'info');
                    robustClick(confirmationButton);
                    await sleep(1500);
                }
                return true;
            }
        }
        return false;
    }
    
    async function navigateToNextMainTask() {
        await sleep(2000);
        log("顺序导航到下一个主任务...", 'info');
        const allMainTasks = Array.from(document.querySelectorAll('.pc-slider-menu-micro'));
        const currentMainTask = document.querySelector('.pc-menu-activity');
        const currentIndex = currentMainTask ? allMainTasks.indexOf(currentMainTask) : -1;
        if (currentIndex === -1) { log("无法定位当前主任务，导航失败。", 'error'); return; }
        const nextIndex = currentIndex + 1;
        if (nextIndex < allMainTasks.length) {
            const nextTaskElement = allMainTasks[nextIndex];
            const taskName = nextTaskElement.querySelector('.pc-menu-node-name')?.getAttribute('title');
            log(`找到下一个任务: "${taskName}"。准备跳转...`, 'success');
            robustClick(nextTaskElement);
        } else {
            log("🎉 恭喜！所有已配置的任务均已完成。", 'success');
            document.getElementById('uca-start-stop-btn').textContent = '🎉 全部完成！';
            toggleAutomation();
        }
    }

    function startObserver() {
        if (urlObserver) return;
        let lastUrl = location.href;
        const observerCallback = () => {
            if (location.href !== lastUrl) {
                lastUrl = location.href;
                log("检测到页面跳转，准备执行下一步...", "info");
                if (!isProcessing && isAutomationRunning) {
                    setTimeout(main, 1500);
                }
            }
        };
        urlObserver = new MutationObserver(observerCallback);
        urlObserver.observe(document.body, { childList: true, subtree: true });
        log('页面监视器已启动。', 'info');
    }

    function stopObserver() {
        if (urlObserver) { urlObserver.disconnect(); urlObserver = null; }
        log('页面监视器已停止。', 'warn');
    }
    
    const initInterval = setInterval(() => {
        if (document.body) {
            clearInterval(initInterval);
            createControlPanel();
            log('U校园助手(精准提交版)已加载。');
        }
    }, 100);

})();