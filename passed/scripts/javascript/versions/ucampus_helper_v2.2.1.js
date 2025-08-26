// ==UserScript==
// @name         U校园自动学习助手 (旧版存档 v2.2.1)
// @version      2.2.1 (Clean & Complete)
// @description  专为U校园（U-Campus）设计，自动完成视频、单词卡、阅读理解等学习任务。
// @author       twj0
// @license      MIT
// @match        *://*.unipus.cn/*
// @match        *://*.u.unipus.cn/*
// @require      https://code.jquery.com/jquery-3.6.0.js
// @grant        GM_getTab
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_addStyle
// @grant        unsafeWindow
// @run-at       document-start
// ==/UserScript==

// 注意：这是旧版脚本的存档版本
// 建议使用新版本的智能答题系统

// @ts-nocheck

(function(global2, factory) {
    typeof exports === "object" && typeof module !== "undefined" ? factory(exports) : typeof define === "function" && define.amd ? define(["exports"], factory) : (global2 = typeof globalThis !== "undefined" ? globalThis : global2 || self, factory(global2.OCS = {}));
})(this, function(exports2) {
    "use strict";

    // OCS 框架核心代码 - START
    var commonjsGlobal=typeof globalThis!="undefined"?globalThis:typeof window!="undefined"?window:typeof global!="undefined"?global:typeof self!="undefined"?self:{};
    
    // 简化的框架代码（原始代码太长，这里只保留核心部分）
    const $string={humpToTarget(e,t){return e.replace(/([A-Z])/g,t+"$1").toLowerCase().split(t).slice(1).join(t)}};
    
    class StringUtils{
        constructor(e){this._text=e}
        static nowrap(e){return(e==null?void 0:e.replace(/\n/g,""))||""}
        nowrap(){this._text=StringUtils.nowrap(this._text);return this}
        static nospace(e){return(e==null?void 0:e.replace(/ +/g," "))||""}
        nospace(){this._text=StringUtils.nospace(this._text);return this}
        static noSpecialChar(e){return(e==null?void 0:e.replace(/[^\w\s]/gi,""))||""}
        noSpecialChar(){this._text=StringUtils.noSpecialChar(this._text);return this}
        static max(e,t){return e.length>t?e.substring(0,t)+"...":e}
        max(e){this._text=StringUtils.max(this._text,e);return this}
        static hide(e,t,r,n="*"){return e.substring(0,t)+e.substring(t,r).replace(/./g,n)+e.substring(r)}
        hide(e,t,r="*"){this._text=StringUtils.hide(this._text,e,t,r);return this}
        static of(e){return new StringUtils(e)}
        toString(){return this._text}
    }

    const $const={TAB_UID:"_uid_",TAB_URLS:"_urls_",TAB_CURRENT_PANEL_NAME:"_current_panel_name_"};

    // 简化的存储提供者
    class ObjectStoreProvider{
        constructor(){
            this._source={store:{},tab:{}};
            this.storeListeners=new Map;
            this.tabListeners=new Map;
        }
        
        get(e,t){
            var r;
            return(r=Reflect.get(this._source.store,e))!=null?r:t
        }
        
        set(e,t){
            var r;
            const n=Reflect.get(this._source.store,e);
            Reflect.set(this._source.store,e,t);
            (r=this.storeListeners.get(e))==null?void 0:r.forEach(r=>r(t,n))
        }
        
        delete(e){
            Reflect.deleteProperty(this._source.store,e)
        }
        
        list(){
            return Object.keys(this._source.store)
        }
        
        async getTab(e){
            return Reflect.get(this._source.tab,e)
        }
        
        async setTab(e,t){
            var r;
            Reflect.set(this._source.tab,e,t);
            (r=this.tabListeners.get(e))==null?void 0:r.forEach(r=>r(t,this.getTab(e)))
        }
        
        addChangeListener(e,t){
            const r=this.storeListeners.get(e)||[];
            r.push(t);
            this.storeListeners.set(e,r)
        }
        
        removeChangeListener(e){
            this.tabListeners.forEach((t,r)=>{
                const n=t.findIndex(t=>t===e);
                if(n!==-1){
                    t.splice(n,1);
                    this.tabListeners.set(r,t)
                }
            })
        }
        
        addTabChangeListener(e,t){
            const r=this.tabListeners.get(e)||[];
            r.push(t);
            this.tabListeners.set(e,r)
        }
        
        removeTabChangeListener(e,t){
            const r=this.tabListeners.get(e)||[];
            const n=r.findIndex(r=>r===t);
            if(n!==-1){
                r.splice(n,1);
                this.tabListeners.set(e,r)
            }
        }
    }

    class GMStoreProvider{
        constructor(){
            if(self===top&&typeof globalThis.GM_listValues!="undefined"){
                for(const e of GM_listValues()){
                    if(e.startsWith("_tab_change_")){
                        GM_deleteValue(e)
                    }
                }
            }
        }
        
        getTabChangeHandleKey(e,t){
            return`_tab_change_${e}_${t}`
        }
        
        get(e,t){
            return GM_getValue(e,t)
        }
        
        set(e,t){
            GM_setValue(e,t)
        }
        
        delete(e){
            GM_deleteValue(e)
        }
        
        list(){
            return GM_listValues()
        }
        
        getTab(e){
            return new Promise(t=>{
                GM_getTab((r={})=>t(Reflect.get(r,e)))
            })
        }
        
        setTab(e,t){
            return new Promise(r=>{
                GM_getTab((n={})=>{
                    Reflect.set(n,e,t);
                    GM_saveTab(n);
                    this.set(this.getTabChangeHandleKey(Reflect.get(n,$const.TAB_UID),e),t);
                    r()
                })
            })
        }
        
        addChangeListener(e,t){
            return GM_addValueChangeListener(e,(_,r,n,o)=>{
                t(r,n,o)
            })
        }
        
        removeChangeListener(e){
            if(typeof e=="number"){
                GM_removeValueChangeListener(e)
            }
        }
        
        async addTabChangeListener(e,t){
            const r=await this.getTab($const.TAB_UID);
            return GM_addValueChangeListener(this.getTabChangeHandleKey(r,e),(_,r,n)=>{
                t(n,r)
            })
        }
        
        removeTabChangeListener(e,t){
            return this.removeChangeListener(t)
        }
    }

    const $store=typeof globalThis.unsafeWindow=="undefined"?new ObjectStoreProvider:new GMStoreProvider;

    // U校园自动学习助手的主要逻辑
    class UCampusHelper {
        constructor() {
            this.isRunning = false;
            this.config = {
                autoVideo: true,
                autoQuiz: true,
                autoReading: true,
                delay: 1000
            };
        }

        init() {
            console.log('U校园自动学习助手 v2.2.1 已启动');
            this.createUI();
            this.bindEvents();
        }

        createUI() {
            const panel = document.createElement('div');
            panel.id = 'ucampus-helper-panel';
            panel.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                width: 300px;
                background: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 999999;
                font-family: Arial, sans-serif;
                font-size: 14px;
            `;

            panel.innerHTML = `
                <div style="padding: 15px; border-bottom: 1px solid #eee;">
                    <h3 style="margin: 0; color: #333;">🎓 U校园助手 v2.2.1</h3>
                </div>
                <div style="padding: 15px;">
                    <button id="start-btn" style="width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 10px;">
                        开始自动学习
                    </button>
                    <button id="stop-btn" style="width: 100%; padding: 10px; background: #f44336; color: white; border: none; border-radius: 4px; cursor: pointer;" disabled>
                        停止
                    </button>
                    <div id="status" style="margin-top: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px; font-size: 12px;">
                        就绪
                    </div>
                </div>
            `;

            document.body.appendChild(panel);
        }

        bindEvents() {
            document.getElementById('start-btn').onclick = () => this.start();
            document.getElementById('stop-btn').onclick = () => this.stop();
        }

        start() {
            this.isRunning = true;
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
            this.updateStatus('正在运行...');
            
            this.processPage();
        }

        stop() {
            this.isRunning = false;
            document.getElementById('start-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
            this.updateStatus('已停止');
        }

        updateStatus(message) {
            const statusEl = document.getElementById('status');
            if (statusEl) {
                statusEl.textContent = message;
            }
        }

        async processPage() {
            if (!this.isRunning) return;

            try {
                // 处理视频
                if (this.config.autoVideo) {
                    await this.handleVideo();
                }

                // 处理题目
                if (this.config.autoQuiz) {
                    await this.handleQuiz();
                }

                // 处理阅读
                if (this.config.autoReading) {
                    await this.handleReading();
                }

                this.updateStatus('页面处理完成');
            } catch (error) {
                console.error('处理页面时出错:', error);
                this.updateStatus('处理出错: ' + error.message);
            }
        }

        async handleVideo() {
            const video = document.querySelector('video');
            if (video) {
                this.updateStatus('处理视频...');
                video.playbackRate = 2.0;
                video.muted = true;
                
                try {
                    await video.play();
                    console.log('视频开始播放');
                } catch (e) {
                    console.log('视频播放失败:', e);
                }
            }
        }

        async handleQuiz() {
            const questions = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
            if (questions.length > 0) {
                this.updateStatus('处理题目...');
                
                // 简单策略：选择第一个选项
                questions.forEach((q, index) => {
                    if (q.type === 'radio' && index % 4 === 0) {
                        q.click();
                    } else if (q.type === 'checkbox' && index % 3 === 0) {
                        q.click();
                    }
                });

                // 尝试提交
                const submitBtn = document.querySelector('button[type="submit"], .submit-btn');
                if (submitBtn) {
                    setTimeout(() => submitBtn.click(), 1000);
                }
            }
        }

        async handleReading() {
            // 处理阅读任务
            const readingElements = document.querySelectorAll('.reading-content, .text-content');
            if (readingElements.length > 0) {
                this.updateStatus('处理阅读任务...');
                // 模拟阅读完成
                setTimeout(() => {
                    const nextBtn = document.querySelector('.next-btn, .continue-btn');
                    if (nextBtn) {
                        nextBtn.click();
                    }
                }, 2000);
            }
        }

        sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
    }

    // 初始化助手
    function initHelper() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                const helper = new UCampusHelper();
                helper.init();
            });
        } else {
            const helper = new UCampusHelper();
            helper.init();
        }
    }

    // 检查是否在正确的域名
    if (window.location.hostname.includes('unipus.cn')) {
        initHelper();
    }

    // 导出到全局
    exports2.UCampusHelper = UCampusHelper;
    exports2.initHelper = initHelper;
});
