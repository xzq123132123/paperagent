# 📄 PaperAgent Pro：多模态论文智能助读系统
 开发者：徐子强
 学号：2025012085

PaperAgent Pro 是一个基于 **大语言模型（LLM）+ PDF 解析** 的论文助读系统，  
旨在帮助研究生与科研人员 **快速理解学术论文、提取关键信息并进行深度问答与学术润色**。

本项目作为课程研究与工程实践展示使用。

---

## ✨ 核心功能

### 1️⃣ 智能概览（Overview）
- 自动解析论文 PDF
- 提取论文标题、作者、核心贡献与结论
- 生成可直接使用的 **BibTeX 引用格式**

### 2️⃣ 深度阅读（Deep Reading）
- 原文全文预览
- 自动提取核心术语表（通俗解释 + 学术定义）
- 提取实验设置、对比方法与关键结论
- 支持基于论文内容的多轮问答

### 3️⃣ 学术润色（Academic Polishing）
- 中译英（学术风格）
- 英译中（通俗理解）
- 英文论文语言润色与表达优化

---

## 🧠 系统架构与技术栈

- **前端 / 应用框架**：Streamlit
- **PDF 解析**：pdfplumber
- **大语言模型**：阿里云 DashScope · Qwen 系列
- **编排方式**：代码级 Workflow + Session State 状态管理
- **Prompt 工程**：结构化 Prompt + 行为约束 + 防幻觉设计

---

## 🧩 工作流程（Workflow）

1. 用户上传论文 PDF  
2. 系统解析全文并缓存至 Session State  
3. 根据功能模块（概览 / 阅读 / 润色）构造不同 Prompt  
4. 多次调用大语言模型完成分析与生成  
5. 输出结构化结果并支持导出 Markdown 笔记

---

## 🚀 快速开始（本地运行）

### 1️⃣ 克隆项目
```bash
git clone https://github.com/你的用户名/paperagent.git
cd paperagent

2️⃣安装依赖
pip install -r requirements.txt

3️⃣ 配置 API Key

设置环境变量（推荐）：

Windows（PowerShell）

setx DASHSCOPE_API_KEY "你的通义千问 API Key"


macOS / Linux

export DASHSCOPE_API_KEY="你的通义千问 API Key"

4️⃣ 启动应用
streamlit run main.py


访问：

http://localhost:8501
