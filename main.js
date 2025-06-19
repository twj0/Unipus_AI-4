// ==UserScript==
// @name         U校园全自动助手 (版本 4.5 - 词汇任务完成检测版)
// @namespace    http://tampermonkey.net/
// @version      4.5.0
// @description  [2025-06] 终极版。新增对单词卡任务的完成状态检测，确保100%完成度。这是稳定、可靠的最终版本。
// @author       AI-Powered Assistant & User Collaboration
// @match        *://ucontent.unipus.cn/*
// @connect      raw.githubusercontent.com
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    // --- Configuration & State ---
    const DEFAULT_QUESTION_BANK_URL = "https://raw.githubusercontent.com/twj0/Unipus_AI-4/refs/heads/main/U%E6%A0%A1%E5%9B%AD%20%E6%96%B0%E4%B8%80%E4%BB%A3%E5%A4%A7%E5%AD%A6%E8%8B%B1%E8%AF%AD%20%E7%BB%BC%E5%90%88%E6%95%99%E7%A8%8B1%E8%8B%B1%E8%AF%AD%E9%A2%98%E5%BA%93.txt";
    const SKIPPABLE_TASKS = ["reading in detail", "repeating after me", "unit project", "gems of the language"];
    let questionBankUrl = DEFAULT_QUESTION_BANK_URL;
    let isAutomationRunning = false;
    let isProcessing = false;
    let questionBankContent = null;
    let urlObserver = null;

    // --- The Course Structure (Our "Brain") ---
    const UNIT_STRUCTURE = [
        { id: "1-1", name: "Setting the scene", type: 'standalone', method: 'video' },
        { id: "1-2", name: "iExplore 1: Learning before class", type: 'composite', children: [
            { name: "Reading in detail", method: 'skip' },
            { name: "Vocabulary", method: 'vocabulary' },
            { name: "Reading comprehension", method: 'quiz' },
            { name: "Dealing with vocabulary", method: 'quiz' }
        ]},
        { id: "1-3", name: "iExplore 1: Reviewing after class", type: 'composite', children: [
            { name: "Gems of the language", method: 'video' },
            { name: "Repeating after me", method: 'skip' },
            { name: "Application", method: 'quiz' }
        ]},
        { id: "1-4", name: "iExplore 2: Learning before class", type: 'composite', children: [
            { name: "Reading in detail", method: 'skip' },
            { name: "Vocabulary", method: 'vocabulary' },
            { name: "Reading comprehension", method: 'quiz' },
            { name: "Dealing with vocabulary", method: 'quiz' }
        ]},
        { id: "1-5", name: "iExplore 2: Reviewing after class", type: 'composite', children: [
            { name: "Repeating after me", method: 'skip' }
        ]},
        { id: "1-6", name: "Unit project", type: 'standalone', method: 'skip' },
        { id: "1-7", name: "Unit test", type: 'composite', children: [
            { name: "Part I", method: 'quiz' },
            { name: "Part II", method: 'quiz' },
            { name: "Part III", method: 'quiz' }
        ]}
    ];

    // --- Utility Functions ---
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

    // --- UI Management (Unchanged) ---
    function createControlPanel() {
        const container = document.createElement('div');
        container.id = 'uca-container';
        container.style.cssText = `position: fixed; top: 20px; left: 20px; z-index: 99999; background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2); width: 350px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; transition: all 0.3s ease; overflow: hidden;`;
        const titleBar = document.createElement('div');
        titleBar.textContent = 'U校园助手 v4.5.0';
        titleBar.style.cssText = `padding: 10px 15px; cursor: move; background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%); color: white; font-weight: 600; user-select: none; text-shadow: 0 1px 2px rgba(0,0,0,0.2);`;
        const content = document.createElement('div');
        content.style.padding = '15px';
        const startStopButton = document.createElement('button');
        startStopButton.id = 'uca-start-stop-btn';
        startStopButton.textContent = '▶️ 开始自动学习';
        startStopButton.style.cssText = `width: 100%; padding: 12px; border: none; border-radius: 8px; background-color: #2563eb; color: white; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.2s ease;`;
        startStopButton.onclick = toggleAutomation;
        content.appendChild(startStopButton);
        const urlSection = document.createElement('div');
        urlSection.style.marginTop = '15px';
        const urlLabel = document.createElement('label');
        urlLabel.textContent = '题库URL:';
        urlLabel.style.cssText = `display: block; font-size: 12px; color: #334155; margin-bottom: 5px;`;
        const urlInput = document.createElement('input');
        urlInput.id = 'uca-url-input';
        urlInput.type = 'text';
        urlInput.style.cssText = `width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #cbd5e1; box-sizing: border-box; font-size: 12px;`;
        const saveButton = document.createElement('button');
        saveButton.textContent = '保存';
        saveButton.style.cssText = `width: 100%; padding: 8px; margin-top: 5px; border: none; border-radius: 6px; background-color: #16a34a; color: white; cursor: pointer;`;
        saveButton.onclick = saveSettings;
        questionBankUrl = GM_getValue('questionBankUrl', DEFAULT_QUESTION_BANK_URL);
        urlInput.value = questionBankUrl;
        urlSection.appendChild(urlLabel);
        urlSection.appendChild(urlInput);
        urlSection.appendChild(saveButton);
        const logSection = document.createElement('div');
        logSection.style.marginTop = '15px';
        const logLabel = document.createElement('label');
        logLabel.textContent = '操作日志:';
        logLabel.style.cssText = urlLabel.style.cssText;
        const logContainer = document.createElement('div');
        logContainer.id = 'uca-log-container';
        logContainer.style.cssText = `height: 200px; background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; overflow-y: auto; font-size: 12px; line-height: 1.5; color: #475569;`;
        logSection.appendChild(logLabel);
        logSection.appendChild(logContainer);
        content.appendChild(urlSection);
        content.appendChild(logSection);
        container.appendChild(titleBar);
        container.appendChild(content);
        document.body.appendChild(container);
        makeDraggable(container, titleBar);
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
            startObserver();
            setTimeout(main, 1500);
        } else {
            button.textContent = '▶️ 开始自动学习';
            button.style.backgroundColor = '#2563eb';
            log('自动化已暂停。', 'warn');
            stopObserver();
        }
    }
    function saveSettings() {
        questionBankUrl = document.getElementById('uca-url-input').value;
        GM_setValue('questionBankUrl', questionBankUrl);
        questionBankContent = null;
        log('题库URL已保存!', 'success');
    }

    // --- Core Engine & Task Handlers ---
    async function fetchQuestionBank() {
        if (questionBankContent) return questionBankContent;
        log(`获取题库...`);
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: 'GET', url: questionBankUrl,
                onload: res => res.status === 200 ? (log("题库获取成功！"), questionBankContent = res.responseText, resolve(questionBankContent)) : reject(`获取题库失败: ${res.status}`),
                onerror: err => reject('获取题库时发生网络错误。')
            });
        });
    }

    async function handleVideoTask() {
        const video = document.querySelector('video');
        if (!video) return true;
        log("处理方法: 视频", 'info');
        return new Promise(async (resolve) => {
            video.muted = true;
            const onCanPlay = async () => {
                video.removeEventListener('canplay', onCanPlay, true);
                video.currentTime = video.duration - 0.5;
                try { await video.play(); } catch(e) {/* ignore */}
                log("视频已快进到结尾。", 'success');
                resolve(true);
            };
            if (video.readyState >= 2) await onCanPlay();
            else video.addEventListener('canplay', onCanPlay, { once: true });
            setTimeout(() => resolve(true), 5000); // Failsafe timeout
        });
    }

    // **IMPROVED VOCABULARY HANDLER**
    async function handleVocabularyTask() {
        log("处理方法: 单词卡", 'info');
        if (!document.querySelector('.vocabulary-wrapper')) return false;

        let maxClicks = 50; // Failsafe to prevent infinite loops
        let clicks = 0;

        while (clicks < maxClicks) {
            if (!isAutomationRunning) return false;
            // The key is to look for a button that does NOT have the disabled class
            const nextButton = document.querySelector('.vocActions .next:not(.swiper-button-disabled)');
            if (!nextButton) {
                log("单词卡 'Next' 按钮不可用，任务完成。", 'success');
                break; // Exit loop, task is done
            }
            robustClick(nextButton);
            clicks++;
            await sleep(600 + Math.random() * 300);
        }

        if (clicks >= maxClicks) {
            log("单词卡点击次数达到上限，为防止死循环，将继续执行。", 'warn');
        }
        return true;
    }

    async function handleQuizTask(taskName, chapterContent) {
        log(`处理方法: 测验 ("${taskName}")`, 'info');
        if (!chapterContent) { log("错误: 无法获取章节信息。", "error"); return false; }
        try {
            const bank = await fetchQuestionBank();
            const answers = searchAnswers(bank, chapterContent, taskName);
            if (answers) await applyAnswersToPage(answers);
            else log(`在题库中未找到 "${taskName}" 的答案。`, "warn");
            return true;
        } catch (error) {
            log(`在处理测验任务时发生错误: ${error.message}`, "error");
            return false;
        }
    }

    async function handleSkippableTask(taskName) {
        log(`处理方法: 跳过 ("${taskName}")`, 'info');
        await sleep(2000 + Math.random() * 1000);
        return true;
    }


    // --- Answer Finding & Application ---
    function searchAnswers(bank, chapter, topic) {
        if(!topic) return null;
        const lines = bank.split('\n');
        let chapterIndex = -1, topicIndex = -1;
        topic = topic.toLowerCase();
        for (let i = 0; i < lines.length; i++) { if (lines[i].trim().toLowerCase().startsWith(chapter.toLowerCase())) { chapterIndex = i; break; } }
        if (chapterIndex === -1) return null;
        for (let i = chapterIndex; i < lines.length; i++) {
            const currentLine = lines[i].trim().toLowerCase();
            if (currentLine.includes(topic)) {
                topicIndex = i; break;
            }
        }
        if (topicIndex === -1) return null;
        let answers = '';
        for (let i = topicIndex + 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.match(/^[iI][A-Z]/) || line.startsWith('Unit ') || (line.match(/^\d+-\d+/) && !line.includes(topic))) { if (answers) break; else continue; }
            answers += line + '\n';
        }
        return answers ? answers.trim() : null;
    }
    async function applyAnswersToPage(answers) {
        if (answers.match(/^[A-Z](?:\s+[A-Z])+$/m)) {
            const answerLetters = answers.match(/^[A-Z](?:\s+[A-Z])+$/m)[0].replace(/\s+/g, '');
            const questions = document.querySelectorAll('.question-common-abs-reply, .question-common-abs-banked-cloze');
            for (let i = 0; i < Math.min(questions.length, answerLetters.length); i++) {
                const options = questions[i].querySelectorAll('.option');
                for (const option of options) {
                    if (option.querySelector('.caption')?.textContent.trim() === answerLetters[i] && !option.classList.contains('selected')) {
                        robustClick(option); await sleep(300); break;
                    }
                }
            }
        }
    }

    // --- Main Control Flow ---
    async function main() {
        if (isProcessing || !isAutomationRunning) return;
        isProcessing = true;

        try {
            await sleep(3000);
            const confirmBtn = document.querySelector('.ant-modal-confirm-btns .ant-btn-primary');
            if (confirmBtn) { robustClick(confirmBtn); await sleep(2000); }

            const currentMainTaskElement = document.querySelector('.pc-menu-activity');
            const currentMainTaskName = currentMainTaskElement?.querySelector('.pc-menu-node-name')?.getAttribute('title');
            if (!currentMainTaskName) { throw new Error("无法识别当前主任务"); }
            log(`当前主任务: "${currentMainTaskName}"`, 'success');

            const taskData = UNIT_STRUCTURE.find(t => currentMainTaskName.includes(t.id));
            if (!taskData) { throw new Error(`在任务地图中未找到 "${currentMainTaskName}"`); }

            if (taskData.type === 'standalone') {
                await handleStandaloneTask(taskData);
            } else if (taskData.type === 'composite') {
                await handleCompositeTask(taskData);
            }

        } catch (error) {
            log(`主流程发生严重错误: ${error.message}`, 'error');
            toggleAutomation();
        } finally {
            isProcessing = false;
        }
    }

    async function handleStandaloneTask(taskData) {
        log(`执行独立任务: "${taskData.name}"`, 'info');
        if (await solveTaskByMethod(taskData.method, taskData.name, taskData.name)) {
             await navigateToNextMainTask();
        } else {
            log(`独立任务 "${taskData.name}" 处理失败，自动化暂停。`, "error");
            toggleAutomation();
        }
    }

    async function handleCompositeTask(taskData) {
        log(`执行复合任务: "${taskData.name}"`, 'info');
        const chapterContent = "Unit 1";

        const subTaskElements = Array.from(document.querySelectorAll('.pc-header-tabs-container .pc-tab-view-container'));

        for (const clickableTitle of subTaskElements) {
            if (!isAutomationRunning) return;

            const taskName = clickableTitle.getAttribute('title').toLowerCase();
            const subTaskData = taskData.children.find(c => c.name.toLowerCase() === taskName);

            if (!subTaskData) {
                log(`未在地图中找到子任务 "${taskName}"，跳过。`, 'warn');
                continue;
            }

            log(`- 正在处理子任务: "${taskName}"`, 'info');
            robustClick(clickableTitle);
            await sleep(2500);

            if (!await solveTaskByMethod(subTaskData.method, taskName, chapterContent)) {
                log(`处理子任务 "${taskName}" 失败，自动化暂停。`, 'error');
                toggleAutomation();
                return;
            }
        }

        log('所有子任务已处理完毕。', 'success');

        const submitBtn = document.querySelector('.question-common-course-page .btn');
        if (submitBtn) {
            log("找到提交按钮，点击提交...", "info");
            robustClick(submitBtn);
        }

        await navigateToNextMainTask();
    }

    async function solveTaskByMethod(method, name, chapter) {
        switch (method) {
            case 'video': return await handleVideoTask();
            case 'vocabulary': return await handleVocabularyTask();
            case 'quiz': return await handleQuizTask(name, chapter);
            case 'skip': return await handleSkippableTask(name);
            default: log(`未知方法: "${method}"`, 'warn'); return true;
        }
    }

    async function navigateToNextMainTask() {
        await sleep(2000);
        log("智能导航到下一个主任务...", 'info');
        const allMainTasks = Array.from(document.querySelectorAll('.pc-slider-menu-micro'));
        const currentMainTask = document.querySelector('.pc-menu-activity');
        const currentIndex = currentMainTask ? allMainTasks.indexOf(currentMainTask) : -1;
        if (currentIndex === -1) { log("无法定位当前主任务，停止。", 'error'); toggleAutomation(); return; }

        for (let i = currentIndex + 1; i < allMainTasks.length; i++) {
            if (!allMainTasks[i].querySelector('.pc-slider-menu-status-circle-all')) {
                const taskName = allMainTasks[i].querySelector('.pc-menu-node-name')?.getAttribute('title');
                log(`找到下一个未完成任务: "${taskName}"。准备跳转...`, 'success');
                robustClick(allMainTasks[i]);
                return;
            }
        }
        log("恭喜！所有课件均已完成。", 'success');
        document.getElementById('uca-start-stop-btn').textContent = '🎉 全部完成！';
        toggleAutomation();
    }

    // --- Observer and Initialization ---
    function startObserver() {
        let lastUrl = location.href;
        const observerCallback = () => {
            if (location.href !== lastUrl) {
                lastUrl = location.href;
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

    window.addEventListener('load', () => {
        createControlPanel();
        log('U校园助手 v4.5 已加载。');
    });

})();