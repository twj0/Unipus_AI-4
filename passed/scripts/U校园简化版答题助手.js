// ==UserScript==
// @name         U校园简化版答题助手
// @namespace    http://tampermonkey.net/
// @version      1.0.0
// @description  专门针对U校园的简化版自动答题脚本
// @author       AI Assistant
// @match        *://ucontent.unipus.cn/*
// @connect      raw.githubusercontent.com
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    // 题库数据 (内置部分常用答案)
    const QUESTION_BANK = {
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
    };

    let isProcessing = false;

    // 工具函数
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function log(message, type = 'info') {
        const colors = { info: '#0ea5e9', success: '#22c55e', error: '#ef4444', warn: '#f97316' };
        console.log(`%c[U校园助手] ${message}`, `color: ${colors[type]}`);
    }

    function forceClick(element) {
        if (!element) return false;
        element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        return true;
    }

    // 获取当前页面信息
    function getCurrentPageInfo() {
        const hash = window.location.hash;
        const unitMatch = hash.match(/\/u(\d+)\//);
        const unit = unitMatch ? `Unit ${unitMatch[1]}` : '';
        
        let task = '';
        if (hash.includes('iexplore1')) {
            task = 'iExplore 1: Learning before class';
        } else if (hash.includes('unittest')) {
            task = 'Unit test';
        }
        
        return { unit, task };
    }

    // 处理选择题
    async function handleMultipleChoice(answers) {
        const choices = answers.split(' ');
        log(`处理选择题答案: ${answers}`);
        
        const options = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
        
        for (let i = 0; i < choices.length; i++) {
            const choice = choices[i].trim();
            if (choice.match(/[ABCD]/)) {
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
                        forceClick(option);
                        clicked = true;
                        break;
                    }
                }
                
                if (!clicked && options[i]) {
                    forceClick(options[i]);
                }
                
                await sleep(300);
            }
        }
    }

    // 处理填空题
    async function handleFillBlanks(answers) {
        const lines = answers.split('\n');
        const inputs = document.querySelectorAll('input[type="text"], textarea');
        
        log(`处理填空题，共${inputs.length}个空格`);
        
        for (let i = 0; i < inputs.length && i < lines.length; i++) {
            const answer = lines[i].replace(/^\d+\)\s*/, '').trim();
            if (answer) {
                inputs[i].value = answer;
                inputs[i].dispatchEvent(new Event('input', { bubbles: true }));
                inputs[i].dispatchEvent(new Event('change', { bubbles: true }));
                await sleep(200);
            }
        }
    }

    // 处理视频
    async function handleVideo() {
        const video = document.querySelector('video');
        if (!video) return false;

        log('发现视频，开始自动播放');
        
        video.playbackRate = 2.0;
        
        try {
            await video.play();
            log('视频开始播放，速度: 2x');
            
            return new Promise((resolve) => {
                const checkVideo = () => {
                    if (video.ended) {
                        log('视频播放完成');
                        resolve(true);
                    } else {
                        setTimeout(checkVideo, 2000);
                    }
                };
                checkVideo();
            });
        } catch (e) {
            log('视频播放失败: ' + e.message, 'error');
            return false;
        }
    }

    // 主处理函数
    async function processCurrentPage() {
        if (isProcessing) {
            log('正在处理中，请稍候...', 'warn');
            return;
        }

        isProcessing = true;
        log('开始处理当前页面');

        try {
            await sleep(2000);

            const hasVideo = document.querySelector('video');
            if (hasVideo) {
                await handleVideo();
                isProcessing = false;
                return;
            }

            const pageInfo = getCurrentPageInfo();
            log(`当前位置: ${pageInfo.unit} - ${pageInfo.task}`);

            const hasQuestions = document.querySelector('input[type="radio"], input[type="checkbox"], input[type="text"], textarea');
            if (!hasQuestions) {
                log('未发现题目', 'warn');
                isProcessing = false;
                return;
            }

            let answer = null;
            if (QUESTION_BANK[pageInfo.unit] && QUESTION_BANK[pageInfo.unit][pageInfo.task]) {
                const taskData = QUESTION_BANK[pageInfo.unit][pageInfo.task];
                
                answer = taskData['Reading comprehension'] || 
                        taskData['Dealing with vocabulary'] || 
                        taskData['Part I'] || 
                        taskData['Part II'] || 
                        taskData['Application'];
            }

            if (!answer) {
                log('未找到对应答案', 'warn');
                isProcessing = false;
                return;
            }

            log('找到答案，开始填写');

            if (answer.match(/^[ABCD\s]+$/)) {
                await handleMultipleChoice(answer);
            } else if (answer.includes('\n') && answer.match(/^\d+\)/m)) {
                await handleFillBlanks(answer);
            } else {
                const textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.value = answer;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }

            await sleep(1000);

            const submitBtn = document.querySelector('button[type="submit"], .submit-btn, .btn-primary');
            if (submitBtn && !submitBtn.disabled) {
                forceClick(submitBtn);
                log('已提交答案', 'success');
            }

        } catch (error) {
            log('处理过程中出错: ' + error.message, 'error');
        } finally {
            isProcessing = false;
        }
    }

    // 创建简单的控制按钮
    function createControlButton() {
        const button = document.createElement('button');
        button.innerHTML = '🎓 开始答题';
        button.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 99999;
            padding: 10px 15px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        `;
        
        button.onclick = processCurrentPage;
        document.body.appendChild(button);
        
        log('U校园简化版答题助手已加载', 'success');
    }

    // 初始化
    function init() {
        setTimeout(() => {
            createControlButton();
        }, 3000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
