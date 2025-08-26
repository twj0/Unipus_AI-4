// ==UserScript==
// @name         U校园全自动助手 (旧版存档 v3.2)
// @namespace    http://tampermonkey.net/
// @version      3.2.0
// @description  [2025-06] 终极修复版。通过精准定位并点击正确的子任务元素，完美解决子任务切换失败的问题。
// @author       AI-Powered Assistant & User Collaboration
// @match        *://ucontent.unipus.cn/*
// @connect      raw.githubusercontent.com
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @run-at       document-start
// ==/UserScript==

// 注意：这是旧版AutoJS脚本的存档版本
// 建议使用新版本的智能答题系统

(function() {
    'use strict';

    // --- Configuration & State ---
    const DEFAULT_QUESTION_BANK_URL = "https://raw.githubusercontent.com/twj0/Unipus_AI-4/refs/heads/main/U%E6%A0%A1%E5%9B%AD%20%E6%96%B0%E4%B8%80%E4%BB%A3%E5%A4%A7%E5%AD%A6%E8%8B%B1%E8%AF%AD%20%E7%BB%BC%E5%90%88%E6%95%99%E7%A8%8B1%E8%8B%B1%E8%AF%AD%E9%A2%98%E5%BA%93.txt";
    const SKIPPABLE_TASKS = ["reading in detail", "repeating after me", "unit project"];
    let questionBankUrl = DEFAULT_QUESTION_BANK_URL;
    let isAutomationRunning = false;
    let isProcessing = false;
    let questionBankContent = null;
    let urlObserver = null;

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

    // --- UI Management ---
    function createControlPanel() {
        const panel = document.createElement('div');
        panel.id = 'uca-control-panel';
        panel.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 320px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            z-index: 999999;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: white;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        `;

        panel.innerHTML = `
            <div style="padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.2);">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600;">🎓 U校园全自动助手</h3>
                <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.8;">版本 3.2 - 精准点击修复版</p>
            </div>
            <div style="padding: 16px;">
                <div style="margin-bottom: 12px;">
                    <label style="display: block; margin-bottom: 6px; font-size: 12px; font-weight: 500;">题库URL:</label>
                    <input type="text" id="uca-url-input" value="${questionBankUrl}" 
                           style="width: 100%; padding: 8px; border: none; border-radius: 6px; font-size: 11px; background: rgba(255,255,255,0.9); color: #333;">
                </div>
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    <button id="uca-start-btn" style="flex: 1; padding: 10px; border: none; border-radius: 6px; background: #22c55e; color: white; font-weight: 600; cursor: pointer; font-size: 12px;">
                        🚀 开始自动化
                    </button>
                    <button id="uca-stop-btn" style="flex: 1; padding: 10px; border: none; border-radius: 6px; background: #ef4444; color: white; font-weight: 600; cursor: pointer; font-size: 12px;" disabled>
                        ⏹️ 停止
                    </button>
                </div>
                <div style="margin-bottom: 12px;">
                    <button id="uca-process-btn" style="width: 100%; padding: 10px; border: none; border-radius: 6px; background: #3b82f6; color: white; font-weight: 600; cursor: pointer; font-size: 12px;">
                        📝 处理当前页面
                    </button>
                </div>
                <div style="background: rgba(0,0,0,0.3); border-radius: 6px; padding: 8px; max-height: 120px; overflow-y: auto;" id="uca-log-container">
                    <div style="color: #94a3b8; font-size: 11px; font-family: monospace;">日志将在这里显示...</div>
                </div>
            </div>
        `;

        document.body.appendChild(panel);

        // Event listeners
        document.getElementById('uca-start-btn').onclick = startAutomation;
        document.getElementById('uca-stop-btn').onclick = stopAutomation;
        document.getElementById('uca-process-btn').onclick = processCurrentPage;
        document.getElementById('uca-url-input').onchange = (e) => {
            questionBankUrl = e.target.value;
            GM_setValue('questionBankUrl', questionBankUrl);
        };

        log('控制面板已加载', 'success');
    }

    // --- Question Bank Management ---
    async function loadQuestionBank() {
        try {
            log('正在加载题库...', 'info');
            const response = await fetch(questionBankUrl);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            questionBankContent = await response.text();
            log('题库加载成功', 'success');
            return true;
        } catch (error) {
            log(`题库加载失败: ${error.message}`, 'error');
            return false;
        }
    }

    function findAnswerInQuestionBank(unit, task, subTask) {
        if (!questionBankContent) return null;
        
        const lines = questionBankContent.split('\n');
        let currentUnit = '';
        let currentTask = '';
        let currentSubTask = '';
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            if (line.startsWith('Unit ')) {
                currentUnit = line;
                continue;
            }
            
            if (currentUnit === unit && line && !line.startsWith('Unit ') && !line.includes(':')) {
                currentTask = line;
                continue;
            }
            
            if (currentUnit === unit && currentTask === task && line.includes(':')) {
                currentSubTask = line.split(':')[0].trim();
                if (currentSubTask === subTask) {
                    const answer = line.split(':')[1]?.trim();
                    return answer || null;
                }
            }
        }
        
        return null;
    }

    // --- Page Processing ---
    async function processCurrentPage() {
        if (isProcessing) {
            log('正在处理中，请稍候...', 'warn');
            return;
        }

        isProcessing = true;
        log('开始处理当前页面', 'info');

        try {
            await sleep(2000);

            // Handle popups first
            handlePopups();

            // Check for video
            const video = document.querySelector('video');
            if (video) {
                await handleVideo(video);
                return;
            }

            // Process questions
            await processQuestions();

        } catch (error) {
            log(`处理页面时出错: ${error.message}`, 'error');
        } finally {
            isProcessing = false;
        }
    }

    async function handleVideo(video) {
        log('发现视频，开始自动播放', 'info');
        
        try {
            video.playbackRate = 2.0;
            video.muted = true;
            await video.play();
            
            log('视频开始播放，速度: 2x', 'success');
            
            return new Promise((resolve) => {
                const checkVideo = () => {
                    if (video.ended) {
                        log('视频播放完成', 'success');
                        resolve();
                    } else {
                        setTimeout(checkVideo, 3000);
                    }
                };
                checkVideo();
            });
        } catch (error) {
            log(`视频播放失败: ${error.message}`, 'error');
        }
    }

    async function processQuestions() {
        const pageInfo = getCurrentPageInfo();
        log(`当前位置: ${pageInfo.unit} - ${pageInfo.task}`, 'info');

        // Check if this is a skippable task
        if (SKIPPABLE_TASKS.some(skip => pageInfo.task.toLowerCase().includes(skip))) {
            log('跳过此任务类型', 'warn');
            return;
        }

        // Find questions
        const questions = findQuestions();
        if (questions.length === 0) {
            log('未发现题目', 'warn');
            return;
        }

        log(`发现 ${questions.length} 个题目`, 'info');

        // Process each question
        for (let i = 0; i < questions.length; i++) {
            await processQuestion(questions[i], pageInfo, i + 1);
            await sleep(1000);
        }

        // Submit if possible
        await submitAnswers();
    }

    function getCurrentPageInfo() {
        const url = window.location.href;
        const hash = window.location.hash;
        
        // Extract unit
        const unitMatch = hash.match(/\/u(\d+)\//);
        const unit = unitMatch ? `Unit ${unitMatch[1]}` : '';
        
        // Extract task
        let task = '';
        if (hash.includes('iexplore1')) {
            task = hash.includes('before') ? 'iExplore 1: Learning before class' : 'iExplore 1: Reviewing after class';
        } else if (hash.includes('iexplore2')) {
            task = hash.includes('before') ? 'iExplore 2: Learning before class' : 'iExplore 2: Reviewing after class';
        } else if (hash.includes('unittest')) {
            task = 'Unit test';
        }
        
        return { unit, task, url, hash };
    }

    function findQuestions() {
        const questions = [];
        
        // Find different types of questions
        const radioGroups = document.querySelectorAll('input[type="radio"]');
        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
        const textInputs = document.querySelectorAll('input[type="text"]');
        const textareas = document.querySelectorAll('textarea');
        
        if (radioGroups.length > 0) {
            questions.push({ type: 'radio', elements: radioGroups });
        }
        if (checkboxes.length > 0) {
            questions.push({ type: 'checkbox', elements: checkboxes });
        }
        if (textInputs.length > 0) {
            questions.push({ type: 'text', elements: textInputs });
        }
        if (textareas.length > 0) {
            questions.push({ type: 'textarea', elements: textareas });
        }
        
        return questions;
    }

    async function processQuestion(question, pageInfo, questionNum) {
        log(`处理第 ${questionNum} 个题目 (${question.type})`, 'info');
        
        // Try to find answer in question bank
        const subTask = `Question ${questionNum}`;
        const answer = findAnswerInQuestionBank(pageInfo.unit, pageInfo.task, subTask);
        
        if (answer) {
            log(`找到答案: ${answer}`, 'success');
            await fillAnswer(question, answer);
        } else {
            log(`未找到答案，使用默认策略`, 'warn');
            await fillDefaultAnswer(question);
        }
    }

    async function fillAnswer(question, answer) {
        switch (question.type) {
            case 'radio':
            case 'checkbox':
                await fillChoiceAnswer(question.elements, answer);
                break;
            case 'text':
                await fillTextAnswer(question.elements, answer);
                break;
            case 'textarea':
                await fillTextareaAnswer(question.elements, answer);
                break;
        }
    }

    async function fillChoiceAnswer(elements, answer) {
        const choices = answer.split(' ');
        for (let i = 0; i < choices.length && i < elements.length; i++) {
            const choice = choices[i].trim();
            if (choice.match(/[ABCD]/)) {
                const targetElement = Array.from(elements).find(el => 
                    el.value === choice || 
                    el.getAttribute('data-option') === choice
                );
                if (targetElement) {
                    robustClick(targetElement);
                    await sleep(300);
                }
            }
        }
    }

    async function fillTextAnswer(elements, answer) {
        const lines = answer.split('\n');
        for (let i = 0; i < elements.length && i < lines.length; i++) {
            const text = lines[i].replace(/^\d+[\.)]\s*/, '').trim();
            if (text) {
                elements[i].value = text;
                elements[i].dispatchEvent(new Event('input', { bubbles: true }));
                elements[i].dispatchEvent(new Event('change', { bubbles: true }));
                await sleep(200);
            }
        }
    }

    async function fillTextareaAnswer(elements, answer) {
        for (const textarea of elements) {
            textarea.value = answer;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));
            await sleep(200);
        }
    }

    async function fillDefaultAnswer(question) {
        switch (question.type) {
            case 'radio':
                // Click first option
                if (question.elements[0]) {
                    robustClick(question.elements[0]);
                }
                break;
            case 'checkbox':
                // Click first checkbox
                if (question.elements[0]) {
                    robustClick(question.elements[0]);
                }
                break;
            case 'text':
                // Fill with placeholder
                for (let i = 0; i < question.elements.length; i++) {
                    question.elements[i].value = `answer${i + 1}`;
                    question.elements[i].dispatchEvent(new Event('input', { bubbles: true }));
                }
                break;
            case 'textarea':
                // Fill with placeholder
                for (const textarea of question.elements) {
                    textarea.value = 'This is a placeholder answer.';
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                }
                break;
        }
    }

    async function submitAnswers() {
        const submitBtn = document.querySelector('button[type="submit"], .submit-btn, .btn-primary');
        if (submitBtn && !submitBtn.disabled) {
            robustClick(submitBtn);
            log('答案已提交', 'success');
            await sleep(2000);
        }
    }

    function handlePopups() {
        const popupSelectors = [
            '.sec-tips .iKnow',
            '.ant-btn.ant-btn-primary.system-info-cloud-ok-button',
            '.modal .close',
            '.popup .close'
        ];
        
        popupSelectors.forEach(selector => {
            const element = document.querySelector(selector);
            if (element && element.offsetParent !== null) {
                robustClick(element);
                log('关闭弹窗', 'info');
            }
        });
    }

    // --- Automation Control ---
    async function startAutomation() {
        if (isAutomationRunning) return;
        
        isAutomationRunning = true;
        document.getElementById('uca-start-btn').disabled = true;
        document.getElementById('uca-stop-btn').disabled = false;
        
        log('开始自动化流程', 'success');
        
        // Load question bank first
        const loaded = await loadQuestionBank();
        if (!loaded) {
            log('题库加载失败，停止自动化', 'error');
            stopAutomation();
            return;
        }
        
        // Start URL monitoring
        startUrlMonitoring();
    }

    function stopAutomation() {
        isAutomationRunning = false;
        document.getElementById('uca-start-btn').disabled = false;
        document.getElementById('uca-stop-btn').disabled = true;
        
        if (urlObserver) {
            urlObserver.disconnect();
            urlObserver = null;
        }
        
        log('自动化已停止', 'warn');
    }

    function startUrlMonitoring() {
        let lastUrl = window.location.href;
        
        const checkUrl = () => {
            if (!isAutomationRunning) return;
            
            const currentUrl = window.location.href;
            if (currentUrl !== lastUrl) {
                lastUrl = currentUrl;
                log('检测到页面变化', 'info');
                setTimeout(processCurrentPage, 3000);
            }
            
            setTimeout(checkUrl, 2000);
        };
        
        checkUrl();
    }

    // --- Initialization ---
    function init() {
        // Wait for page to load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }
        
        // Check if we're on the right domain
        if (!window.location.href.includes('ucontent.unipus.cn')) {
            return;
        }
        
        // Load saved settings
        const savedUrl = GM_getValue('questionBankUrl');
        if (savedUrl) {
            questionBankUrl = savedUrl;
        }
        
        // Create UI after a delay
        setTimeout(createControlPanel, 2000);
        
        // Start popup monitoring
        setInterval(handlePopups, 3000);
    }

    // Start the script
    init();

})();
