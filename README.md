# U校园智能答题系统

一个基于Python的现代化U校园智能答题系统，通过创新的试答-提取-缓存机制实现无依赖的动态答题功能。

## ✨ 特性

### 🎯 核心功能
- **🧠 智能答案提取** - 通过试答和响应分析自动获取正确答案
- **💾 答案缓存机制** - 建立本地缓存数据库，提高后续答题效率
- **🎯 多策略回退** - 缓存查找 → 智能提取 → 回退策略的三层保障
- **✅ 自动验证** - 答案正确性验证和置信度管理
- **🎬 视频自动播放** - 支持自动播放、调速、静音等功能
- **🌐 浏览器自动化** - 基于Playwright的现代浏览器控制

### 🖥️ 用户界面
- **🎨 图形界面(GUI)** - 基于Tkinter的友好图形界面
- **⌨️ 命令行界面(CLI)** - 功能完整的命令行操作界面
- **🤖 自动模式** - 完全无人值守的自动化执行

### ⚙️ 高级特性
- **📊 实时监控** - 任务进度、系统状态实时显示
- **🔧 灵活配置** - YAML配置文件，支持热重载
- **📈 统计分析** - 详细的执行统计和成功率分析
- **🛡️ 错误处理** - 完善的异常处理和自动重试机制

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows 10/11, macOS, Linux

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ucampus-automation
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装浏览器**
```bash
playwright install chromium
```

4. **配置环境变量**（可选）
```bash
# 创建 .env 文件
echo "UCAMPUS_USERNAME=your_username" > .env
echo "UCAMPUS_PASSWORD=your_password" >> .env
```

### 运行程序

```bash
# 启动GUI界面（默认）
python main.py

# 启动命令行界面
python main.py cli

# 智能答题模式
python main.py smart                    # 单题智能答题
python main.py smart "https://..."      # 指定URL智能答题
python main.py batch 1 5               # 批量智能答题（Unit 1-5）

# 启动自动模式
python main.py auto

# 运行测试
python main.py test
```

## 🧠 智能答题系统

### 核心优势

1. **无依赖性** - 不依赖外部题库，动态获取最新答案
2. **高效缓存** - 智能缓存机制，提高后续答题效率
3. **多重保障** - 三层策略确保高成功率
4. **自动验证** - 答案正确性验证和置信度管理

### 工作原理

#### 第一阶段：缓存查找
1. 提取题目信息（单元、任务、题目类型、文本）
2. 生成题目唯一标识符（MD5哈希）
3. 在本地缓存中查找对应答案
4. 如果找到，直接填写并提交

#### 第二阶段：智能提取
1. 设置网络监控，捕获API响应
2. 执行试答（随机选择或占位符）
3. 提交试答并分析响应数据
4. 从响应中提取正确答案
5. 存储到缓存并重新答题

#### 第三阶段：回退策略
1. 选择题：按A、B、C、D顺序尝试
2. 填空题：使用通用占位符
3. 翻译题：使用标准占位符翻译

### 使用示例

```bash
# 单题智能答题
python main.py smart

# 批量处理Unit 1-3
python main.py batch 1 3

# 使用GUI界面
python main.py gui
# 然后点击"🧠 智能答题"或"🚀 批量智能答题"按钮
```

详细使用指南请参考：[智能答题系统指南](docs/INTELLIGENT_ANSWERING.md)

## 📁 项目结构

```
U校园智能答题系统/
├── src/                          # 源代码目录
│   ├── intelligence/            # 智能答题模块 🧠
│   │   ├── answer_extractor.py  # 答案提取器
│   │   ├── answer_cache.py      # 答案缓存系统
│   │   └── smart_answering.py   # 智能答题策略
│   ├── automation/              # 自动化模块
│   ├── ui/                      # 用户界面
│   ├── core/                    # 核心模块
│   └── utils/                   # 工具模块
├── config/                      # 配置文件
├── docs/                        # 文档目录
├── examples/                    # 使用示例
├── tests/                       # 测试目录
├── passed/                      # 历史版本存档
├── tampermonkey/                # 浏览器脚本
└── main.py                      # 主程序入口
```

## 🔧 配置选项

主要配置文件：`config/config.yaml`

```yaml
intelligent_answering:
  max_extraction_retries: 3     # 最大提取重试次数
  confidence_threshold: 0.7     # 答案置信度阈值
  enable_fuzzy_matching: true   # 启用模糊匹配
  auto_verify_answers: true     # 自动验证答案
  cache_ttl_days: 30           # 缓存有效期
```

## 📊 性能特性

- **缓存命中率**: 通常可达80%以上
- **提取成功率**: 针对常见题型可达90%以上
- **响应时间**: 缓存命中<1秒，智能提取<30秒
- **存储效率**: SQLite数据库 + 内存缓存双重优化

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request



## ⚠️ 免责声明

本工具仅供学习和研究使用，请遵守相关法律法规和学校规定。使用者需自行承担使用风险。
