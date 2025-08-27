# U校园智能答题系统 🎓

一个基于Playwright的U校园自动化答题工具，支持多种题型的智能识别和自动答题。

## ✨ 功能特点

- 🔐 **自动登录**: 自动处理登录流程和用户协议
- 🍪 **Cookie管理**: 自动保存和重用登录状态
- 🎬 **视频处理**: 自动快进视频内容
- 🪟 **弹窗管理**: 智能处理各种系统弹窗
- 🤖 **智能答题**: 支持翻译题、选择题、填空题等多种题型
- 📊 **进度跟踪**: 实时显示答题进度和统计信息

## 🚀 快速开始

### 1. 环境要求

- Python 3.7+
- Windows/macOS/Linux

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd U校园

# 安装Python依赖
pip install -r requirements_simple.txt

# 安装Playwright浏览器
playwright install chromium
```

### 3. 配置账号

编辑 `main_simple.py` 文件，修改以下配置：

```python
self.config = {
    "username": "你的用户名",      # 替换为你的U校园用户名
    "password": "你的密码",       # 替换为你的U校园密码
    "course_name": "新一代大学英语（提高篇）综合教程2",
    "max_questions": 30,
    "headless": False  # 设为True可隐藏浏览器窗口
}
```

### 4. 运行程序

```bash
python main_simple.py
```

## 📋 支持的题型

| 题型 | 状态 | 说明 |
|------|------|------|
| 翻译题 | ✅ | 中英互译，基于预设翻译库 |
| 选择题 | ✅ | 自动选择第一个选项 |
| 填空题 | ✅ | 自动填写通用答案 |
| 视频题 | ✅ | 自动快进到最后一秒 |
| 录音题 | ⚠️ | 自动跳过或模拟录音 |
| 连线题 | ⚠️ | 随机连接选项 |

## 🛠️ 高级配置

### 修改答题策略

在 `_generate_translation()` 方法中添加更多预设翻译：

```python
def _generate_translation(self, source_text: str) -> str:
    # 添加你的预设翻译
    if '你的中文文本' in source_text:
        return "Your English translation"
    elif 'Your English text' in source_text:
        return "你的中文翻译"
    
    # 其他逻辑...
```

### 调整运行参数

```python
self.config = {
    "max_questions": 50,    # 最大答题数量
    "headless": True,       # 无头模式（隐藏浏览器）
    "course_name": "你的课程名称"
}
```

## 📊 运行示例

```
🚀 启动U校园智能答题系统
🎓 U校园智能答题系统启动
🌐 启动浏览器...
✅ 浏览器启动成功
🔐 开始登录...
✅ 登录成功
📚 导航到课程: 新一代大学英语（提高篇）综合教程2
✅ 成功进入学习界面
🤖 开始智能答题，最大题目数: 30

📝 处理第 1 题...
📝 翻译题
✅ 第 1 题处理成功

📝 处理第 2 题...
☑️ 选择题
✅ 第 2 题处理成功

==================================================
📊 答题统计
==================================================
📝 处理题目: 25
✅ 成功答题: 23
❌ 失败答题: 2
📈 成功率: 92.0%
==================================================
```

## ⚠️ 注意事项

1. **仅供学习交流使用**，请勿用于违规用途
2. **建议在测试环境中先运行**，确认功能正常
3. **定期更新预设翻译库**，提高答题准确率
4. **网络不稳定时可能影响运行**，建议在稳定网络环境下使用

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [Playwright](https://playwright.dev/) - 现代化的浏览器自动化工具
- U校园平台 - 提供学习环境

---

**免责声明**: 本工具仅供学习和研究使用，使用者需自行承担使用风险。
