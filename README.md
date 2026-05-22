# 📄 PaperAgent Pro：多模态论文智能助读系统

**开发者**：徐子强
**学号**：2025012085

PaperAgent Pro 是一个基于**大语言模型（LLM）+ PDF 解析**的论文助读系统，旨在帮助研究生与科研人员**快速理解学术论文、提取关键信息并进行深度问答与学术润色**。

本项目作为课程研究与工程实践展示使用。

---

## ✨ 核心功能

### 1. 智能概览（Overview）
- 自动解析论文 PDF 全文
- **Map-Reduce 滑窗策略**：长文本自动分段总结后汇总，突破 LLM 上下文长度限制
- 提取论文标题、核心贡献、方法与结论
- 生成可直接使用的 **BibTeX 引用格式**
- **Mermaid 逻辑结构导图**：AI 自动梳理论文逻辑关系并以流程图可视化

### 2. 深度阅读（Deep Reading）
- **PDF 原文预览**：基于 pdf.js 渲染，支持翻页浏览
- **核心术语提取**：自动生成三列表格（术语 | 通俗比喻 | 学术定义）
- **实验数据挖掘**：提取数据集、Baseline 方法、核心指标提升幅度
- **多轮问答**：基于论文内容与 AI 导师实时对话，支持 4 轮历史上下文
- **智能知识库**：AI 提炼的干货自动沉淀，无需翻找聊天记录

### 3. 学术润色（Academic Polishing）
- **智能翻译**：中→英（SCI 期刊风格）/ 英→中（通俗流畅），自动检测语言方向
- **学术润色**：提升词汇高级感与语法准确性
- **语法纠错**：查找语法错误并给出修改建议
- 支持**PDF 原文对照**或自由粘贴两种输入模式

### 4. 成果导出
- **Markdown**：概览 + 问答记录一键导出
- **PDF**：支持中文字体（SimHei），结构化排版（概览/问答记录）

---

## 🧠 系统架构与技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端框架 | **Streamlit** — 纯 Python Web UI，无需前端代码 |
| PDF 解析 | **pdfplumber** — 文本提取；**pdf.js** — 浏览器端渲染；**fpdf** — 导出 PDF |
| 大语言模型 | **阿里云 DashScope · Qwen-Turbo** |
| 可视化 | **Mermaid.js v10** — 逻辑结构导图 |
| 状态管理 | Streamlit `st.session_state` + `@st.cache_data` 缓存 |
| Prompt 工程 | 结构化多轮 Prompt + System Prompt 约束 + 防幻觉设计 |

### 项目模块结构

```
paperagent/
├── app.py              # 主入口 - Streamlit UI 编排（页面结构、侧边栏、三大功能Tab）
├── config.py           # 页面配置、CSS 样式（学术蓝主题）、System Prompt 模板
├── llm_utils.py        # 通义千问 API 封装（NoProxyContext、call_qwen）
├── pdf_utils.py        # PDF 全流程工具（提取、渲染、导出、文件指纹）
├── text_processing.py  # 文本分块（滑窗）、Mermaid 代码清洗/渲染、导图 Prompt 构造
├── summarization.py    # Map-Reduce 摘要生成、Mermaid 思维导图生成
├── requirements.txt    # Python 依赖
└── .gitignore
```

**模块依赖关系**：
```
config.py          (零依赖)
llm_utils.py       → config.py (默认 Prompt 模板)
pdf_utils.py       (独立模块)
text_processing.py (独立模块)
summarization.py   → llm_utils.py + text_processing.py
app.py             → 所有模块 (UI 编排层)
```

---

## 🧩 工作流程（Workflow）

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  上传 PDF    │ → │ pdfplumber   │ → │  全文文本    │
│  (Streamlit) │    │  提取全文    │    │  (Session)   │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────────────────┼───────────────┐
                    │                          │               │
                    ▼                          ▼               ▼
            ┌─────────────┐          ┌─────────────┐   ┌───────────┐
            │  智能概览    │          │  深度阅读    │   │  学术润色  │
            │             │          │             │   │           │
            │ Map-Reduce │          │ AI 导师问答  │   │ 中⇌英翻译 │
            │ Mermaid导图 │          │ 术语/数据提取│   │ 学术优化   │
            │ BibTeX 引用 │          │ 知识库沉淀   │   │ 语法纠错   │
            └─────────────┘          └─────────────┘   └───────────┘
                    │                          │               │
                    └──────────────────────────┼───────────────┘
                                               ▼
                                      ┌─────────────────┐
                                      │  导出 Markdown  │
                                      │  导出 PDF        │
                                      └─────────────────┘
```

### 关键设计决策

1. **Map-Reduce 摘要**：避免长文本超出 LLM token 限制，5000 字分片 → 分段摘要 → 汇总润色，附带进度条
2. **显式参数传递**：`call_qwen(api_key, reader_level, ...)` — API Key 和用户水平作为显式参数，模块解耦
3. **Proxy 处理**：调用 DashScope 时临时清除 HTTP_PROXY 环境变量，避免企业网络代理干扰
4. **文件指纹**：基于文件名+大小+MD5 哈希校验，确保换文件必定重解析
5. **防幻觉 Prompt**：System Prompt 严格约束"仅基于论文内容，不得编造"，未提及信息明确回答"论文中未给出"

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/xzq123132123/paperagent.git
cd paperagent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

在应用侧边栏直接填入通义千问 API Key，或设置环境变量：

**Windows (PowerShell)**：
```powershell
setx DASHSCOPE_API_KEY "你的通义千问 API Key"
```

**macOS / Linux**：
```bash
export DASHSCOPE_API_KEY="你的通义千问 API Key"
```

### 4. 启动应用

```bash
streamlit run app.py
```

访问：**http://localhost:8501**

### 5. 使用流程

1. 在左侧边栏填入 **API Key**，选择**解释通俗度**（新手/初级/专家）
2. 上传 **PDF 论文**
3. 切换到 **「智能概览」** 生成结构化摘要和逻辑导图
4. 切换到 **「深度阅读」** 边看原文边向 AI 导师提问
5. 切换到 **「学术润色」** 翻译或润色段落
6. 侧边栏导出 **Markdown** 或 **PDF** 笔记

---

## 📋 PDF 导出字体说明

导出 PDF 需要中文字体支持，系统会自动搜索以下路径：

1. 项目目录下的 `SimHei.ttf`
2. `C:\Windows\Fonts\simhei.ttf`（Windows 黑体）
3. `C:\Windows\Fonts\msyh.ttc`（Windows 微软雅黑）

若找不到字体，PDF 将使用英文回退字体（中文部分会出现乱码）。用户可自行下载 SimHei.ttf 放置到项目目录下解决。
