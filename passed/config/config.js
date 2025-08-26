// U校园自动答题助手 - 配置文件
// 用户可以根据需要修改这些配置

const UCAMPUS_CONFIG = {
    // 基础设置
    BASIC: {
        // 脚本版本
        VERSION: '1.0.0',
        
        // 是否启用调试模式
        DEBUG_MODE: false,
        
        // 是否自动开始处理
        AUTO_START: false,
        
        // 默认语言 ('zh' | 'en')
        LANGUAGE: 'zh'
    },

    // 延迟设置 (毫秒)
    DELAYS: {
        // 页面加载等待时间
        PAGE_LOAD: 2000,
        
        // 填写答案的延迟
        ANSWER_FILL: 1000,
        
        // 点击操作延迟
        CLICK_DELAY: 500,
        
        // 视频检查间隔
        VIDEO_CHECK: 3000,
        
        // 自动循环检查间隔
        AUTO_LOOP_INTERVAL: 10000,
        
        // 错误重试延迟
        RETRY_DELAY: 2000
    },

    // 视频设置
    VIDEO: {
        // 默认播放速度
        DEFAULT_SPEED: 2.0,
        
        // 可选播放速度
        SPEED_OPTIONS: [1, 1.25, 1.5, 2, 2.5, 3, 4],
        
        // 是否自动播放
        AUTO_PLAY: true,
        
        // 是否静音播放
        MUTED: true,
        
        // 视频播放完成后的等待时间
        COMPLETION_WAIT: 1000
    },

    // 答题设置
    ANSWERING: {
        // 是否自动提交答案
        AUTO_SUBMIT: true,
        
        // 是否显示答案预览
        SHOW_PREVIEW: true,
        
        // 填写答案前的确认延迟
        CONFIRM_DELAY: 500,
        
        // 最大重试次数
        MAX_RETRIES: 3,
        
        // 是否跳过已完成的题目
        SKIP_COMPLETED: true
    },

    // UI界面设置
    UI: {
        // 控制面板位置
        PANEL_POSITION: {
            top: '20px',
            left: '20px'
        },
        
        // 控制面板大小
        PANEL_SIZE: {
            width: '320px',
            minHeight: '200px'
        },
        
        // 是否可拖拽
        DRAGGABLE: true,
        
        // 主题颜色
        THEME: {
            primary: '#4CAF50',
            secondary: '#2196F3',
            warning: '#FF9800',
            error: '#f44336',
            success: '#22c55e'
        },
        
        // 日志设置
        LOG: {
            // 最大日志条数
            MAX_ENTRIES: 100,
            
            // 是否显示时间戳
            SHOW_TIMESTAMP: true,
            
            // 日志级别 ('debug' | 'info' | 'warn' | 'error')
            LEVEL: 'info'
        }
    },

    // 题库设置
    QUESTION_BANK: {
        // 默认题库URL
        DEFAULT_URL: "https://raw.githubusercontent.com/twj0/Unipus_AI-4/refs/heads/main/U%E6%A0%A1%E5%9B%AD%20%E6%96%B0%E4%B8%80%E4%BB%A3%E5%A4%A7%E5%AD%A6%E8%8B%B1%E8%AF%AD%20%E7%BB%BC%E5%90%88%E6%95%99%E7%A8%8B1%E8%8B%B1%E8%AF%AD%E9%A2%98%E5%BA%93.json",
        
        // 备用题库URL列表
        BACKUP_URLS: [
            "https://example.com/backup1.json",
            "https://example.com/backup2.json"
        ],
        
        // 本地题库缓存时间 (毫秒)
        CACHE_DURATION: 24 * 60 * 60 * 1000, // 24小时
        
        // 是否启用本地题库
        ENABLE_LOCAL: true
    },

    // 选择器配置
    SELECTORS: {
        // 视频选择器
        VIDEO: [
            'video',
            '.video-player video',
            '#video-container video'
        ],
        
        // 选择题选择器
        MULTIPLE_CHOICE: [
            'input[type="radio"]',
            'input[type="checkbox"]',
            '.option input',
            '.choice input'
        ],
        
        // 文本输入选择器
        TEXT_INPUT: [
            'input[type="text"]',
            'textarea',
            '.text-input',
            '.answer-input'
        ],
        
        // 提交按钮选择器
        SUBMIT_BUTTON: [
            'button[type="submit"]',
            '.submit-btn',
            '.btn-submit',
            '.btn-primary',
            'button:contains("提交")',
            'button:contains("Submit")'
        ],
        
        // 继续按钮选择器
        CONTINUE_BUTTON: [
            '.continue-btn',
            '.next-btn',
            '.btn-continue',
            'button:contains("继续")',
            'button:contains("下一步")',
            'button:contains("Next")'
        ],
        
        // 单词卡片选择器
        WORD_CARD: [
            '.word-card',
            '.vocabulary-card',
            '.vocab-item',
            '[data-type="vocabulary"]'
        ]
    },

    // 错误处理设置
    ERROR_HANDLING: {
        // 是否启用自动重试
        AUTO_RETRY: true,
        
        // 最大重试次数
        MAX_RETRIES: 3,
        
        // 重试间隔倍数
        RETRY_MULTIPLIER: 2,
        
        // 是否记录错误日志
        LOG_ERRORS: true,
        
        // 是否显示错误通知
        SHOW_NOTIFICATIONS: true
    },

    // 高级设置
    ADVANCED: {
        // 是否启用页面监听
        ENABLE_PAGE_OBSERVER: true,
        
        // 是否启用URL变化监听
        ENABLE_URL_OBSERVER: true,
        
        // 是否启用键盘快捷键
        ENABLE_HOTKEYS: true,
        
        // 快捷键配置
        HOTKEYS: {
            START: 'Ctrl+Enter',
            STOP: 'Ctrl+Shift+Enter',
            TOGGLE_AUTO: 'Ctrl+Alt+A'
        },
        
        // 是否启用统计功能
        ENABLE_STATISTICS: true,
        
        // 数据保存设置
        DATA_PERSISTENCE: {
            // 是否保存用户设置
            SAVE_SETTINGS: true,
            
            // 是否保存操作历史
            SAVE_HISTORY: false,
            
            // 数据保存键前缀
            STORAGE_PREFIX: 'ucampus_'
        }
    },

    // 兼容性设置
    COMPATIBILITY: {
        // 支持的浏览器
        SUPPORTED_BROWSERS: ['chrome', 'firefox', 'edge', 'safari'],
        
        // 最低浏览器版本要求
        MIN_BROWSER_VERSION: {
            chrome: 80,
            firefox: 75,
            edge: 80,
            safari: 13
        },
        
        // 是否启用兼容模式
        COMPATIBILITY_MODE: false,
        
        // 兼容性检查
        CHECK_COMPATIBILITY: true
    }
};

// 语言配置
const UCAMPUS_LANG = {
    zh: {
        PANEL_TITLE: 'U校园自动答题助手',
        START_BUTTON: '▶️ 开始处理',
        STOP_BUTTON: '⏹️ 停止处理',
        AUTO_BUTTON: '🔄 自动循环',
        PROCESSING: '处理中...',
        VIDEO_SPEED: '视频播放速度:',
        AUTO_SUBMIT: '自动提交答案',
        LOG_TITLE: '操作日志:',
        DESCRIPTION: '支持视频自动播放、题目自动填答、单元测试等',
        
        // 日志消息
        SCRIPT_LOADED: '脚本已加载',
        PROCESSING_START: '开始处理当前页面',
        VIDEO_FOUND: '发现视频，开始自动播放',
        VIDEO_COMPLETED: '视频播放完成',
        ANSWER_FOUND: '找到答案，开始填写',
        ANSWER_SUBMITTED: '答案已提交',
        NO_CONTENT: '未发现可处理的内容',
        ERROR_OCCURRED: '处理过程中出错'
    },
    
    en: {
        PANEL_TITLE: 'U Campus Auto Helper',
        START_BUTTON: '▶️ Start Processing',
        STOP_BUTTON: '⏹️ Stop Processing',
        AUTO_BUTTON: '🔄 Auto Loop',
        PROCESSING: 'Processing...',
        VIDEO_SPEED: 'Video Speed:',
        AUTO_SUBMIT: 'Auto Submit Answers',
        LOG_TITLE: 'Operation Log:',
        DESCRIPTION: 'Support auto video play, auto answer filling, unit tests, etc.',
        
        // Log messages
        SCRIPT_LOADED: 'Script loaded',
        PROCESSING_START: 'Start processing current page',
        VIDEO_FOUND: 'Video found, start auto play',
        VIDEO_COMPLETED: 'Video playback completed',
        ANSWER_FOUND: 'Answer found, start filling',
        ANSWER_SUBMITTED: 'Answer submitted',
        NO_CONTENT: 'No processable content found',
        ERROR_OCCURRED: 'Error occurred during processing'
    }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UCAMPUS_CONFIG, UCAMPUS_LANG };
} else if (typeof window !== 'undefined') {
    window.UCAMPUS_CONFIG = UCAMPUS_CONFIG;
    window.UCAMPUS_LANG = UCAMPUS_LANG;
}
