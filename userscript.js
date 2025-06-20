// ==UserScript==
// @name         U校园全自动助手 (v22.0 - 最终版)
// @namespace    http://tampermonkey.net/
// @version      22.0.0
// @description  [最终版] 引入“激活-执行”统一输入引擎，完美解决所有填空题（选词填空与直接输入）的提交问题。这套代码已具备完全的自动化能力。
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
    let lazyUrlCheckerInterval = null;
    let lastAnsweredSubTask = '';

    // --- Course Structure (The "Mechanical Task Map") ---
    const COURSE_DATA = {
        "GENERIC_UNIT_STRUCTURE": [
            { id_suffix: "-1", name: "Setting the scene", type: 'standalone', actions: [{ type: 'video' }] },
            { id_suffix: "-2", name: "iExplore 1: Learning before class", type: 'composite', children: [
                { name: "Reading in detail", actions: [{ type: 'skip' }] },
                { name: "Vocabulary", actions: [{ type: 'vocabulary' }] },
                { name: "Reading comprehension", actions: [{ type: 'quiz' }, { type: 'click', text: '提 交' }] },
                { name: "Dealing with vocabulary", actions: [{ type: 'quiz' }, { type: 'click', text: '提 交' }] }
            ]},
            { id_suffix: "-3", name: "iExplore 1: Reviewing after class", type: 'composite', children: [
                { name: "Gems of the language", actions: [{ type: 'video' }] },
                { name: "Repeating after me", actions: [{ type: 'skip' }] },
                { name: "Application", actions: [{ type: 'quiz' }, { type: 'click', text: '提 交' }] }
            ]},
            { id_suffix: "-4", name: "iExplore 2: Learning before class", type: 'composite', children: [
                { name: "Reading in detail", actions: [{ type: 'skip' }] },
                { name: "Vocabulary", actions: [{ type: 'vocabulary' }] },
                { name: "Reading comprehension", actions: [{ type: 'quiz' }, { type: 'click', text: '提 交' }] },
                { name: "Dealing with vocabulary", actions: [{ type: 'quiz' }, { type: 'click', text: '提 交' }] }
            ]},
            { id_suffix: "-5", name: "iExplore 2: Reviewing after class", type: 'composite', children: [ { name: "Repeating after me", actions: [{ type: 'skip' }] } ]},
            { id_suffix: "-6", name: "Unit project", type: 'standalone', actions: [{ type: 'skip' }] },
            { id_suffix: "-7", name: "Unit test", type: 'composite', children: [
                { name: "Part I", actions: [{ type: 'quiz' }, { type: 'click', text: '提 交' }] },
                { name: "Part II", actions: [{ type: 'quiz' }, { type: 'click', text: '提 交' }] },
                { name: "Part III", actions: [
                    { type: 'quiz' },
                    { type: 'click', text: '下一题' },
                    { type: 'quiz' },
                    { type: 'click', text: '提 交' }
                ]}
            ]},
        ],
        "QUESTION_BANK": {}
    };

    // --- Remote Loader & UI & Utilities ---
    function loadRemoteQuestionBank(courseName) { const url = COURSE_MAPS[courseName]; if (!url) { log(`错误：未找到课程 "${courseName}" 的题库URL。`, 'error'); return; } log(`正在从远程加载 [${courseName}] 的题库...`, 'info'); GM_xmlhttpRequest({ method: 'GET', url: url, onload: function(response) { if (response.status === 200) { try { COURSE_DATA.QUESTION_BANK = JSON.parse(response.responseText); log(`题库加载成功！`, 'success'); } catch (e) { log('题库文件解析失败。', 'error'); console.error(e); } } else { log(`获取题库失败: ${response.status}`, 'error'); } }, onerror: function(error) { log('网络错误，无法加载远程题库。', 'error'); console.error(error); } }); }
    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
    const log = (message, type = 'info') => { const logContainer = document.getElementById('uca-log-container'); if (!logContainer) return; const colors = { info: '#0ea5e9', success: '#22c55e', error: '#ef4444', warn: '#f97316' }; const entry = document.createElement('div'); entry.innerHTML = `<span style="color: #94a3b8;">[${new Date().toLocaleTimeString()}]</span> ${message}`; entry.style.color = colors[type] || '#64748b'; entry.style.marginBottom = '5px'; entry.style.fontSize = '12px'; entry.style.fontFamily = 'monospace'; logContainer.appendChild(entry); logContainer.scrollTop = logContainer.scrollHeight; };
    function robustClick(element) { if (!element) return; element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true })); element.dispatchEvent(new MouseEvent('click', { bubbles: true })); }
    function createControlPanel() { if (document.getElementById('uca-container')) return; const container = document.createElement('div'); container.id = 'uca-container'; container.style.cssText = `position: fixed; top: 20px; left: 20px; z-index: 99999; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2); width: 350px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; transition: all 0.3s ease; overflow: hidden;`; const titleBar = document.createElement('div'); titleBar.textContent = 'U校园助手 v22.0'; titleBar.style.cssText = `padding: 10px 15px; cursor: move; background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%); color: white; font-weight: 600; user-select: none; text-shadow: 0 1px 2px rgba(0,0,0,0.2);`; const content = document.createElement('div'); content.style.padding = '15px'; const selectLabel = document.createElement('label'); selectLabel.textContent = '选择课程题库:'; selectLabel.style.cssText = `display: block; font-size: 13px; color: #334155; margin-bottom: 8px;`; const courseSelect = document.createElement('select'); courseSelect.id = 'uca-course-select'; courseSelect.style.cssText = `width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; margin-bottom: 15px;`; Object.keys(COURSE_MAPS).forEach(name => courseSelect.add(new Option(name, name))); courseSelect.onchange = (e) => loadRemoteQuestionBank(e.target.value); content.appendChild(selectLabel); content.appendChild(courseSelect); const startStopButton = document.createElement('button'); startStopButton.id = 'uca-start-stop-btn'; startStopButton.textContent = '▶️ 开始自动学习'; startStopButton.style.cssText = `width: 100%; padding: 12px; border: none; border-radius: 8px; background-color: #2563eb; color: white; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.2s ease;`; startStopButton.onclick = toggleAutomation; content.appendChild(startStopButton); const logSection = document.createElement('div'); logSection.style.marginTop = '15px'; const logLabel = document.createElement('label'); logLabel.textContent = '操作日志:'; logLabel.style.cssText = `display: block; font-size: 12px; color: #334155; margin-bottom: 5px;`; const logContainer = document.createElement('div'); logContainer.id = 'uca-log-container'; logContainer.style.cssText = `height: 200px; background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; overflow-y: auto; font-size: 12px; line-height: 1.5; color: #475569;`; logSection.appendChild(logLabel); logSection.appendChild(logContainer); content.appendChild(logSection); container.appendChild(titleBar); container.appendChild(content); document.body.appendChild(container); makeDraggable(container, titleBar); loadRemoteQuestionBank(courseSelect.value); }
    function makeDraggable(element, handle) { let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0; const dragMouseDown = (e) => { e.preventDefault(); pos3 = e.clientX; pos4 = e.clientY; element.style.transition = 'none'; document.onmouseup = closeDragElement; document.onmousemove = elementDrag; }; const elementDrag = (e) => { e.preventDefault(); pos1 = pos3 - e.clientX; pos2 = pos4 - e.clientY; pos3 = e.clientX; pos4 = e.clientY; element.style.top = (element.offsetTop - pos2) + "px"; element.style.left = (element.offsetLeft - pos1) + "px"; }; const closeDragElement = () => { element.style.transition = 'all 0.3s ease'; document.onmouseup = null; document.onmousemove = null; }; handle.onmousedown = dragMouseDown; }
    function toggleAutomation() { isAutomationRunning = !isAutomationRunning; const button = document.getElementById('uca-start-stop-btn'); if (isAutomationRunning) { button.textContent = '⏹️ 停止自动化'; button.style.backgroundColor = '#dc2626'; log('自动化已启动...', 'success'); GM_deleteValue('lastProcessedTaskName'); lastAnsweredSubTask = ''; startLazyUrlChecker(); setTimeout(main, 1500); } else { button.textContent = '▶️ 开始自动学习'; button.style.backgroundColor = '#2563eb'; log('自动化已暂停。', 'warn'); isProcessing = false; stopLazyUrlChecker(); } }

    async function getPageContextAndAnswers() {
        const mainTaskElement = document.querySelector('.pc-menu-activity .pc-menu-node-name');
        const mainTaskContent = mainTaskElement?.getAttribute('title')?.trim();
        if (!mainTaskContent) { log('无法识别主任务。', 'error'); return null; }
        const unitTaskMatch = mainTaskContent.match(/^(\d+)-(\d+)/);
        if (!unitTaskMatch) { log(`无法从 "${mainTaskContent}" 解析单元ID。`, 'error'); return null; }
        const unitId = unitTaskMatch[1]; const taskId = unitTaskMatch[2]; const unitKey = `Unit ${unitId}`; const taskSuffixToFind = `-${taskId}`;
        const activeSubTaskElement = document.querySelector('.pc-header-tab-activity .pc-tab-view-container[title], .pc-header-tab-activity .pc-tab-view-container > span');
        let activeSubTaskName = activeSubTaskElement ? (activeSubTaskElement.getAttribute('title') || activeSubTaskElement.textContent.trim()) : null;
        if (!activeSubTaskName && document.querySelector('.question-common-abs-test-part-name')) { activeSubTaskName = document.querySelector('.question-common-abs-test-part-name').textContent.trim(); }
        if (!activeSubTaskName) { activeSubTaskName = 'Part I'; }
        if (lastAnsweredSubTask === `${mainTaskContent}-${activeSubTaskName}`) { return 'answered'; }
        const taskMapEntry = COURSE_DATA.GENERIC_UNIT_STRUCTURE.find(t => t.id_suffix === taskSuffixToFind);
        const mainTaskKey = taskMapEntry ? taskMapEntry.name : mainTaskContent;
        const subTaskAnswersObject = COURSE_DATA.QUESTION_BANK[unitKey]?.[mainTaskKey];
        let answers = null; let matchedKey = null;
        if (subTaskAnswersObject) {
            if (subTaskAnswersObject[activeSubTaskName]) { answers = subTaskAnswersObject[activeSubTaskName]; matchedKey = activeSubTaskName; }
            else { const availableKeys = Object.keys(subTaskAnswersObject); matchedKey = availableKeys.find(key => key.startsWith(activeSubTaskName)); if (matchedKey) { answers = subTaskAnswersObject[matchedKey]; log(`模糊匹配成功: "${activeSubTaskName}" -> "${matchedKey}"`, 'info'); } }
        }
        if (!answers) { log(`题库未找到答案: ${unitKey} -> ${mainTaskKey} -> ${activeSubTaskName}`, 'warn'); return null; }
        log(`已为 "${matchedKey || activeSubTaskName}" 找到答案。`, 'success');
        return { answers, mainTaskContent, activeSubTaskName };
    }

    /**
     * [UPDATED] The new Unified Input Engine for all question types.
     */
    async function doAnswer() {
        // --- Part 1: Get Answers and Check Question Type ---
        if (Object.keys(COURSE_DATA.QUESTION_BANK).length === 0) { log('题库为空...', 'warn'); await sleep(3000); if (Object.keys(COURSE_DATA.QUESTION_BANK).length === 0) { log('题库加载失败', 'error'); return; } }
        const context = await getPageContextAndAnswers(); if (!context) return; if (context === 'answered') { log('此部分已作答', 'info'); return; }
        const { answers, mainTaskContent, activeSubTaskName } = context;

        // --- Part 2: Handle Multiple Choice ---
        const choiceQuestions = document.querySelectorAll('.question-common-abs-reply, .question-common-abs-banked-cloze');
        if (choiceQuestions.length > 0 && typeof answers === 'string' && /^[A-Z](?:\s*[A-Z])*$/.test(answers.trim())) {
            log('检测到选择题...', 'info');
            const answerLetters = answers.trim().replace(/\s+/g, '');
            for (let i = 0; i < Math.min(choiceQuestions.length, answerLetters.length); i++) {
                if (choiceQuestions[i].querySelector('.option.selected')) continue;
                for (const option of choiceQuestions[i].querySelectorAll('.option')) {
                    if (option.querySelector('.caption')?.textContent.trim() === answerLetters[i]) {
                        robustClick(option); await sleep(250); break;
                    }
                }
            }
            log(`应用答案: ${activeSubTaskName}`, "success");
            lastAnsweredSubTask = `${mainTaskContent}-${activeSubTaskName}`;
            return;
        }

        // --- Part 3: Handle All Fill-in-the-Blank Types (Unified Engine) ---
        const fillInBlanks = document.querySelectorAll('textarea, input:not([type="checkbox"]):not([type="radio"])');
        if (fillInBlanks.length > 0 && typeof answers === 'string') {
            log('检测到填空题，启动统一输入引擎...', 'info');
            const answerLines = answers.split('\n').map(l => l.replace(/^\d+\.?\)?\s*/, '').trim()).filter(Boolean);

            for (let i = 0; i < Math.min(fillInBlanks.length, answerLines.length); i++) {
                const blank = fillInBlanks[i];
                const answerText = answerLines[i];
                if (blank.value === answerText) continue;

                // Step 1: Activate the input field by clicking it first.
                log(`- 激活第 ${i + 1} 个填空处...`, 'info');
                robustClick(blank);
                await sleep(200);

                // Step 2: Try to find the answer in a word bank.
                const wordBankSelector = '.question-common-abs-filling-blank-filling span, .selectable-word';
                const wordBankOptions = Array.from(document.querySelectorAll(wordBankSelector));
                const targetWordElement = wordBankOptions.find(el => el.textContent.trim() === answerText);

                if (targetWordElement) {
                    // Strategy A: Word bank found, click it.
                    log(`-- 在词库中找到 "${answerText}"，点击它。`, 'success');
                    robustClick(targetWordElement);
                } else {
                    // Strategy B: No word bank, type directly.
                    log(`-- 未在词库中找到 "${answerText}"，直接输入。`, 'info');
                    blank.value = answerText;
                    blank.dispatchEvent(new Event('input', { bubbles: true }));
                }
                await sleep(300); // Brief pause after filling each blank
            }
            log(`应用答案: ${activeSubTaskName}`, "success");
            if (activeSubTaskName !== "Part III") { lastAnsweredSubTask = `${mainTaskContent}-${activeSubTaskName}`; }
        }
    }

    async function handleVideoTask() { const video = document.querySelector('video'); if (!video) return; log("处理视频...", 'info'); video.muted = true; await sleep(500); const onCanPlay = () => { if (video.duration) { video.currentTime = video.duration - 1.5; video.play().catch(e => log('视频播放被阻止', 'warn')); log("视频已快进。", 'success'); } }; if (video.readyState >= 2) { onCanPlay(); } else { video.addEventListener('canplay', onCanPlay, { once: true }); } await sleep(2500); }
    async function handleSkippableTask(taskName) { log(`跳过任务: "${taskName}"`, 'info'); await sleep(2000); }
    async function handleVocabularyTask() { log("处理单词卡...", 'info'); const progressContainer = document.querySelector('div.ratio'); if (progressContainer) { log('检测到进度条，使用进度追踪模式。', 'info'); const spans = progressContainer.querySelectorAll('span'); if (spans.length === 2) { let currentCount = parseInt(spans[0].textContent, 10); let totalCount = parseInt(spans[1].textContent.replace('/', ''), 10); if (!isNaN(currentCount) && !isNaN(totalCount)) { for (let i = currentCount; i < totalCount; i++) { if (!isAutomationRunning) return; log(`处理单词卡: ${i} / ${totalCount}...`); const nextButton = document.querySelector('.vocActions .next:not(.swiper-button-disabled)'); if (!nextButton) { log('“下一张”按钮消失，提前结束。', 'warn'); break; } robustClick(nextButton); const expectedNext = i + 1; let waitTimeout = 5000; while (waitTimeout > 0) { const newCurrent = parseInt(document.querySelector('div.ratio span:first-child')?.textContent || `${i}`, 10); if (newCurrent === expectedNext) break; await sleep(100); waitTimeout -= 100; } if (waitTimeout <= 0) { log('等待卡片更新超时。', 'error'); break; } } log(`进度追踪完成，共处理 ${totalCount} 张卡片。`, 'success'); await sleep(2000); return; } } } log('未检测到进度条或解析失败，使用备用观察者模式。', 'warn'); let maxClicks = 150; while (maxClicks-- > 0) { if (!isAutomationRunning) return; const nextButton = document.querySelector('.vocActions .next:not(.swiper-button-disabled)'); if (!nextButton) { log("单词卡已翻完。", 'success'); break; } robustClick(nextButton); await sleep(700); } if (maxClicks <= 0) log("单词卡点击次数达到上限。", 'warn'); log("单词卡任务后等待2秒以稳定页面...", "info"); await sleep(2000); }
    async function main() { if (isProcessing || !isAutomationRunning) return; isProcessing = true; try { await sleep(3500); const mainTaskNameElement = document.querySelector('.pc-menu-activity .pc-menu-node-name'); const currentMainTaskName = mainTaskNameElement?.getAttribute('title')?.trim(); if (!currentMainTaskName) throw new Error("无法识别当前主任务。"); const lastProcessed = GM_getValue('lastProcessedTaskName', ''); if (currentMainTaskName === lastProcessed && location.href === GM_getValue('lastUrl', '')) { log(`检测到卡在任务: "${currentMainTaskName}"。强制导航。`, 'warn'); await navigateToNextMainTask(); return; } if (currentMainTaskName !== lastProcessed) { lastAnsweredSubTask = ''; } const unitTaskMatch = currentMainTaskName.match(/^(\d+)-(\d+)/); if (!unitTaskMatch) { log(`无法从任务 "${currentMainTaskName}" 解析出 单元-任务ID，尝试导航。`, 'warn'); await navigateToNextMainTask(); return; } const unitId = unitTaskMatch[1]; const taskId = unitTaskMatch[2]; const taskSuffixToFind = `-${taskId}`; log(`读取 [Unit ${unitId}] 任务地图: "${currentMainTaskName}" (模板后缀: ${taskSuffixToFind})`, 'success'); const taskData = COURSE_DATA.GENERIC_UNIT_STRUCTURE.find(t => t.id_suffix === taskSuffixToFind); if (!taskData) { log(`未在地图中找到后缀为 "${taskSuffixToFind}" 的执行模板，尝试导航。`, 'warn'); await navigateToNextMainTask(); return; } if (taskData.type === 'standalone') { log(`执行独立任务: ${taskData.name}`); await executeActions(taskData.actions, taskData); } else if (taskData.type === 'composite' && taskData.children) { log(`执行复合任务: ${taskData.name}`); for (const subTaskConfig of taskData.children) { if (!isAutomationRunning) return; const subTaskElements = Array.from(document.querySelectorAll('.pc-header-tabs-container .pc-tab-view-container')); const subTaskElement = subTaskElements.find(el => (el.getAttribute('title') || el.textContent.trim()) === subTaskConfig.name); if (subTaskElements.length > 0 && !subTaskElement) { log(`- 未找到子任务Tab: "${subTaskConfig.name}"，跳过。`, 'warn'); continue; } if (subTaskElement) { log(`- 切换到: "${subTaskConfig.name}"`, 'info'); robustClick(subTaskElement); await waitForSubTaskActive(subTaskConfig.name); } else { log(`- 处理无Tab子任务: "${subTaskConfig.name}"`, 'info'); } await executeActions(subTaskConfig.actions, subTaskConfig); } } log(`任务 "${currentMainTaskName}" 已按计划执行完毕。`, 'info'); await GM_setValue('lastProcessedTaskName', currentMainTaskName); await GM_setValue('lastUrl', location.href); await navigateToNextMainTask(); } catch (error) { log(`主流程错误: ${error.message}`, 'error'); console.error(error); toggleAutomation(); } finally { isProcessing = false; } }
    async function executeActions(actions, config) { if (!actions || actions.length === 0) return; log(`- 执行动作序列...`, 'info'); for (const action of actions) { if (!isAutomationRunning) { log('自动化已停止，中止动作序列。', 'warn'); return; } log(`-- 动作: ${action.type}` + (action.text ? ` (${action.text})` : '')); switch (action.type) { case 'video': await handleVideoTask(); break; case 'skip': await handleSkippableTask(config.name); break; case 'vocabulary': await handleVocabularyTask(); break; case 'quiz': await doAnswer(); break; case 'click': const success = await handleSpecificClick(action.text); if (!success) { log(`点击动作失败，中止序列。`, 'error'); return; } break; default: log(`未知动作类型: "${action.type}"`, 'warn'); } await sleep(1500); } }
    async function handleSpecificClick(buttonText) { log(`正在查找按钮 [${buttonText}]...`, 'info'); const selector = '.btn, button.ant-btn, .btn_learn_goon'; const maxWaitTime = 7000; const interval = 500; let elapsedTime = 0; let primaryButtonClicked = false; while (elapsedTime < maxWaitTime) { if (!isAutomationRunning) return false; const buttons = document.querySelectorAll(selector); for (const btn of buttons) { if (btn && btn.textContent.includes(buttonText) && !btn.disabled && btn.offsetParent !== null) { btn.scrollIntoView({ behavior: 'smooth', block: 'center' }); await sleep(400); log(`点击按钮: "${btn.textContent.trim()}"`, "success"); robustClick(btn); await sleep(2000); const confirmButton = document.querySelector('.ant-modal-confirm-btns .ant-btn-primary'); if (confirmButton && confirmButton.offsetParent !== null) { log("点击确认弹窗", 'info'); robustClick(confirmButton); } primaryButtonClicked = true; break; } } if (primaryButtonClicked) break; await sleep(interval); elapsedTime += interval; } if (!primaryButtonClicked) { log(`未找到可用的 [${buttonText}] 按钮。`, 'warn'); return false; } await sleep(1000); log('检查是否存在“继续学习”按钮...', 'info'); const continueButtonText = '继续学习'; const continueMaxWait = 3000; let continueElapsedTime = 0; while (continueElapsedTime < continueMaxWait) { const continueButton = Array.from(document.querySelectorAll(selector)).find(btn => btn.textContent.includes(continueButtonText) && !btn.disabled && btn.offsetParent !== null); if (continueButton) { log('发现并点击“继续学习”按钮。', 'success'); robustClick(continueButton); return true; } await sleep(500); continueElapsedTime += 500; } log('未发现“继续学习”按钮，正常继续。', 'info'); return true; }
    async function navigateToNextMainTask() { await sleep(2500); log("导航到下一个主任务...", 'info'); const allMainTasks = Array.from(document.querySelectorAll('.pc-slider-menu-micro')); const currentMainTask = document.querySelector('.pc-menu-activity'); const currentIndex = currentMainTask ? allMainTasks.indexOf(currentMainTask) : -1; if (currentIndex === -1) { log("无法定位当前主任务以进行导航。", 'error'); return; } const nextIndex = currentIndex + 1; if (nextIndex < allMainTasks.length) { const nextTaskElement = allMainTasks[nextIndex]; const taskTitle = nextTaskElement.getAttribute('title') || nextTaskElement.textContent.trim(); log(`点击: ${taskTitle}`); robustClick(nextTaskElement); } else { log("🎉 恭喜！课程已全部完成。", 'success'); toggleAutomation(); } }
    function startLazyUrlChecker() { if (lazyUrlCheckerInterval) return; let lastUrl = location.href; lazyUrlCheckerInterval = setInterval(() => { if (location.href !== lastUrl) { log("检测到URL变化，准备执行...", "info"); lastUrl = location.href; if (!isProcessing && isAutomationRunning) { setTimeout(main, 1500); } } }, 1000); log('低资源URL检查器已启动。', 'info'); }
    function stopLazyUrlChecker() { if (lazyUrlCheckerInterval) { clearInterval(lazyUrlCheckerInterval); lazyUrlCheckerInterval = null; } log('低资源URL检查器已停止。', 'warn'); }
    function startOptimizedModalObserver() { const modalObserver = new MutationObserver((mutations) => { for (const mutation of mutations) { if (mutation.addedNodes.length > 0) { for (const node of mutation.addedNodes) { if (node.nodeType === 1) { const confirmButton = node.querySelector('.ant-modal-confirm-btns .ant-btn-primary'); if (confirmButton && confirmButton.offsetParent !== null && confirmButton.textContent.includes('确 定')) { log('检测到弹窗被添加，正在点击...', 'info'); robustClick(confirmButton); return; } } } } } }); modalObserver.observe(document.body, { childList: true, subtree: true }); log('优化的弹窗监视器已启动。', 'info'); }
    async function waitForSubTaskActive(taskName) { log(`- 等待 "${taskName}" 加载完成...`, 'info'); const maxWaitTime = 10000; const interval = 250; let elapsedTime = 0; while (elapsedTime < maxWaitTime) { const activeTab = document.querySelector('.pc-header-tab-activity .pc-tab-view-container'); if (activeTab) { const activeName = activeTab.getAttribute('title') || activeTab.textContent.trim(); if (activeName === taskName) { log(`- "${taskName}" 已激活。`, 'success'); await sleep(500); return; } } await sleep(interval); elapsedTime += interval; } throw new Error(`等待 "${taskName}" 超时。`); }
    const initInterval = setInterval(() => { if (document.body) { clearInterval(initInterval); createControlPanel(); startOptimizedModalObserver(); log('U校园助手(v22.0)已加载。'); } }, 100);

})();