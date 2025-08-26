// ==UserScript==
// @name         U校园自动答题助手 (旧版存档)
// @namespace    http://tampermonkey.net/
// @version      1.0.0
// @description  U校园自动答题脚本，支持视频播放、题目自动填答、单元测试等功能
// @author       AI Assistant
// @match        *://ucontent.unipus.cn/*
// @match        *://sso.unipus.cn/*
// @connect      raw.githubusercontent.com
// @connect      *
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_addStyle
// @grant        unsafeWindow
// @run-at       document-start
// ==/UserScript==

// 注意：这是旧版脚本的存档版本
// 建议使用新版本的智能答题系统：tampermonkey/ucampus_helper.js

(function() {
    'use strict';

    // 配置参数
    const CONFIG = {
        // 默认题库URL
        DEFAULT_QUESTION_BANK_URL: "https://raw.githubusercontent.com/twj0/Unipus_AI-4/refs/heads/main/U%E6%A0%A1%E5%9B%AD%20%E6%96%B0%E4%B8%80%E4%BB%A3%E5%A4%A7%E5%AD%A6%E8%8B%B1%E8%AF%AD%20%E7%BB%BC%E5%90%88%E6%95%99%E7%A8%8B1%E8%8B%B1%E8%AF%AD%E9%A2%98%E5%BA%93.json",
        // 延迟设置
        DELAYS: {
            PAGE_LOAD: 2000,        // 页面加载等待时间
            ANSWER_FILL: 1000,      // 填答案延迟
            CLICK_DELAY: 500,       // 点击延迟
            VIDEO_CHECK: 3000       // 视频检查间隔
        },
        // 自动播放视频速度
        VIDEO_SPEED: 2.0
    };

    // 全局状态
    let isRunning = false;
    let questionBank = null;
    let currentUnit = '';
    let currentTask = '';

    // 弹窗处理器
    const PopupHandler = {
        // 处理所有可能的弹窗
        handlePopups: () => {
            let handled = false;

            // 处理鼠标取词弹窗
            const mousePopup = document.querySelector('.sec-tips');
            if (mousePopup && mousePopup.offsetParent !== null) {
                const knowBtn = mousePopup.querySelector('.iKnow');
                if (knowBtn) {
                    Utils.forceClick(knowBtn);
                    Utils.log('已关闭鼠标取词弹窗', 'info');
                    handled = true;
                }
            }

            // 处理系统信息弹窗
            const systemPopup = document.querySelector('.ant-btn.ant-btn-primary.system-info-cloud-ok-button');
            if (systemPopup && systemPopup.offsetParent !== null) {
                Utils.forceClick(systemPopup);
                Utils.log('已关闭系统信息弹窗', 'info');
                handled = true;
            }

            // 处理通用"我知道了"按钮
            const knowButtons = document.querySelectorAll('.iKnow, [class*="know"], button[class*="ok"], .know-box span');
            knowButtons.forEach(btn => {
                if (btn.offsetParent !== null && (btn.textContent.includes('我知道了') || btn.textContent.includes('知道了'))) {
                    Utils.forceClick(btn);
                    Utils.log('已关闭提示弹窗', 'info');
                    handled = true;
                }
            });

            return handled;
        },

        // 定期检查弹窗
        startPopupWatcher: () => {
            setInterval(() => {
                PopupHandler.handlePopups();
            }, 2000); // 每2秒检查一次
        }
    };

    // 工具函数
    const Utils = {
        // 延迟函数
        sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

        // 日志函数
        log: (message, type = 'info') => {
            const colors = {
                info: '#0ea5e9',
                success: '#22c55e',
                error: '#ef4444',
                warn: '#f97316'
            };
            console.log(`%c[U校园助手] ${message}`, `color: ${colors[type]}`);

            // 更新UI日志
            const logContainer = document.getElementById('ucampus-log');
            if (logContainer) {
                const entry = document.createElement('div');
                entry.innerHTML = `<span style="color: #666;">[${new Date().toLocaleTimeString()}]</span> ${message}`;
                entry.style.color = colors[type];
                entry.style.marginBottom = '3px';
                entry.style.fontSize = '12px';
                logContainer.appendChild(entry);
                logContainer.scrollTop = logContainer.scrollHeight;

                // 限制日志条数
                if (logContainer.children.length > 50) {
                    logContainer.removeChild(logContainer.firstChild);
                }
            }
        },

        // 强制点击
        forceClick: (element) => {
            if (!element) return false;
            try {
                element.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                element.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                return true;
            } catch (e) {
                return false;
            }
        },

        // 获取当前页面信息
        getCurrentPageInfo: () => {
            const url = window.location.href;
            const hash = window.location.hash;

            // 解析单元信息
            const unitMatch = hash.match(/\/u(\d+)\//);
            const unit = unitMatch ? `Unit ${unitMatch[1]}` : '';

            // 解析任务信息
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
    };

    // 题库管理器
    const QuestionBankManager = {
        // 内置题库数据
        builtinData: {
            "Unit 1": {
                "iExplore 1: Learning before class": {
                    "Reading comprehension": "A B A B A",
                    "Dealing with vocabulary": "A B A A A B"
                },
                "iExplore 1: Reviewing after class": {
                    "Application": "1. To say is easier than to do.\n2. Mary wanted to make a lot of money, buy stock, and retire early.\n3. She stayed up late either studying her English or going to parties."
                },
                "Unit test": {
                    "Part I": "1) prevails\n2) a variety of\n3) interact\n4) hanging out\n5) scale\n6) In contrast\n7) crucial\n8) engage\n9) in person\n10) directly",
                    "Part II": "B A C B A A"
                }
            }
        },

        // 加载题库
        loadQuestionBank: async () => {
            try {
                Utils.log('正在加载题库...', 'info');
                
                // 尝试从远程加载
                const response = await fetch(CONFIG.DEFAULT_QUESTION_BANK_URL);
                if (response.ok) {
                    const data = await response.json();
                    questionBank = { ...QuestionBankManager.builtinData, ...data };
                    Utils.log('远程题库加载成功', 'success');
                } else {
                    throw new Error('远程题库加载失败');
                }
            } catch (error) {
                Utils.log('使用内置题库', 'warn');
                questionBank = QuestionBankManager.builtinData;
            }
        },

        // 获取答案
        getAnswer: (unit, task, subTask = null) => {
            if (!questionBank || !questionBank[unit] || !questionBank[unit][task]) {
                return null;
            }

            const taskData = questionBank[unit][task];
            
            if (subTask && taskData[subTask]) {
                return taskData[subTask];
            }

            // 尝试常见的子任务名称
            const commonSubTasks = [
                'Reading comprehension',
                'Dealing with vocabulary',
                'Application',
                'Part I',
                'Part II',
                'Part III'
            ];

            for (const subTaskName of commonSubTasks) {
                if (taskData[subTaskName]) {
                    return taskData[subTaskName];
                }
            }

            // 如果taskData是字符串，直接返回
            if (typeof taskData === 'string') {
                return taskData;
            }

            return null;
        }
    };

    // 视频处理器
    const VideoHandler = {
        // 处理视频
        handleVideo: async () => {
            const video = document.querySelector('video');
            if (!video) return false;

            Utils.log('发现视频，开始自动播放', 'info');

            try {
                // 设置播放速度
                video.playbackRate = CONFIG.VIDEO_SPEED;
                
                // 静音播放
                video.muted = true;

                // 开始播放
                await video.play();
                Utils.log(`视频开始播放，速度: ${CONFIG.VIDEO_SPEED}x`, 'success');

                // 监控播放完成
                return new Promise((resolve) => {
                    const checkVideo = () => {
                        if (video.ended) {
                            Utils.log('视频播放完成', 'success');
                            resolve(true);
                        } else {
                            setTimeout(checkVideo, CONFIG.DELAYS.VIDEO_CHECK);
                        }
                    };
                    checkVideo();
                });

            } catch (error) {
                Utils.log(`视频播放失败: ${error.message}`, 'error');
                return false;
            }
        }
    };

    // 答题处理器
    const AnswerHandler = {
        // 处理选择题
        handleMultipleChoice: async (answers) => {
            const choices = answers.split(' ');
            Utils.log(`处理选择题: ${answers}`, 'info');

            for (let i = 0; i < choices.length; i++) {
                const choice = choices[i].trim();
                if (choice.match(/[ABCD]/)) {
                    // 尝试多种选择器
                    const selectors = [
                        `input[value="${choice}"]`,
                        `input[data-option="${choice}"]`,
                        `.option-${choice.toLowerCase()} input`,
                        `label:contains("${choice}") input`
                    ];

                    let clicked = false;
                    for (const selector of selectors) {
                        const option = document.querySelector(selector);
                        if (option) {
                            Utils.forceClick(option);
                            clicked = true;
                            break;
                        }
                    }

                    if (!clicked) {
                        // 按索引点击
                        const options = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                        if (options[i]) {
                            Utils.forceClick(options[i]);
                        }
                    }

                    await Utils.sleep(CONFIG.DELAYS.CLICK_DELAY);
                }
            }
        },

        // 处理填空题
        handleFillBlanks: async (answers) => {
            const lines = answers.split('\n');
            const inputs = document.querySelectorAll('input[type="text"], textarea');

            Utils.log(`处理填空题，共${inputs.length}个空格`, 'info');

            for (let i = 0; i < inputs.length && i < lines.length; i++) {
                const answer = lines[i].replace(/^\d+[\.)]\s*/, '').trim();
                if (answer) {
                    inputs[i].value = answer;
                    inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                    inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
                    await Utils.sleep(200);
                }
            }
        },

        // 处理文本答案
        handleTextAnswer: async (answer) => {
            const textarea = document.querySelector('textarea');
            if (textarea) {
                textarea.value = answer;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.dispatchEvent(new Event('change', { bubbles: true }));
                Utils.log('文本答案已填写', 'success');
            }
        }
    };

    // 主处理器
    const MainProcessor = {
        // 处理当前页面
        processCurrentPage: async () => {
            if (isRunning) {
                Utils.log('正在处理中，请稍候...', 'warn');
                return false;
            }

            isRunning = true;
            Utils.log('开始处理当前页面', 'info');

            try {
                // 处理弹窗
                PopupHandler.handlePopups();

                // 等待页面加载
                await Utils.sleep(CONFIG.DELAYS.PAGE_LOAD);

                // 检查是否有视频
                const hasVideo = document.querySelector('video');
                if (hasVideo) {
                    const result = await VideoHandler.handleVideo();
                    isRunning = false;
                    return result;
                }

                // 检查是否有题目
                const hasQuestions = document.querySelector('input[type="radio"], input[type="checkbox"], input[type="text"], textarea');
                if (!hasQuestions) {
                    Utils.log('未发现题目', 'warn');
                    isRunning = false;
                    return false;
                }

                // 获取页面信息
                const pageInfo = Utils.getCurrentPageInfo();
                Utils.log(`当前位置: ${pageInfo.unit} - ${pageInfo.task}`, 'info');

                // 获取答案
                const answer = QuestionBankManager.getAnswer(pageInfo.unit, pageInfo.task);
                if (!answer) {
                    Utils.log('未找到对应答案', 'warn');
                    isRunning = false;
                    return false;
                }

                Utils.log('找到答案，开始填写', 'success');

                // 根据答案类型处理
                if (answer.match(/^[ABCD\s]+$/)) {
                    await AnswerHandler.handleMultipleChoice(answer);
                } else if (answer.includes('\n') && answer.match(/^\d+[\.)]/m)) {
                    await AnswerHandler.handleFillBlanks(answer);
                } else {
                    await AnswerHandler.handleTextAnswer(answer);
                }

                // 等待一下再提交
                await Utils.sleep(CONFIG.DELAYS.ANSWER_FILL);

                // 自动提交
                const submitBtn = document.querySelector('button[type="submit"], .submit-btn, .btn-primary');
                if (submitBtn && !submitBtn.disabled) {
                    Utils.forceClick(submitBtn);
                    Utils.log('答案已提交', 'success');
                }

                isRunning = false;
                return true;

            } catch (error) {
                Utils.log(`处理过程中出错: ${error.message}`, 'error');
                isRunning = false;
                return false;
            }
        }
    };

    // 初始化
    const init = async () => {
        // 等待页面加载
        if (document.readyState === 'loading') {
            await new Promise(resolve => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        }

        // 再等待一下确保页面完全加载
        await Utils.sleep(3000);

        // 检查是否在U校园页面
        if (!window.location.href.includes('ucontent.unipus.cn')) {
            return;
        }

        Utils.log('U校园自动答题助手已启动', 'success');

        // 加载题库
        await QuestionBankManager.loadQuestionBank();

        // 启动弹窗监听
        PopupHandler.startPopupWatcher();
    };

    // 启动脚本
    init();

})();
