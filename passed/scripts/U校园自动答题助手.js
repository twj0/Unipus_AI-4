// ==UserScript==
// @name         U校园自动答题助手
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

            // 处理模态框和遮罩层
            const modals = document.querySelectorAll('.modal, .popup, .dialog, .overlay, [class*="modal"], [class*="popup"], [class*="dialog"]');
            modals.forEach(modal => {
                if (modal.offsetParent !== null) {
                    const closeBtn = modal.querySelector('.close, .btn-close, [class*="close"], .cancel, .btn-cancel');
                    if (closeBtn) {
                        Utils.forceClick(closeBtn);
                        Utils.log('已关闭模态框', 'info');
                        handled = true;
                    }
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
                // 先处理可能的弹窗
                PopupHandler.handlePopups();

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
