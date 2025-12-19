import streamlit as st
import pdfplumber
import dashscope
from dashscope import Generation
from http import HTTPStatus
import os
import time
from datetime import datetime

# --- 页面基础配置 ---
st.set_page_config(
    page_title="AI 论文助读 Agent Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 自定义 CSS ---
st.markdown("""
<style>
    .reportview-container { margin-top: -2em; }
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .stTextArea textarea { font-size: 14px; color: #333; }
    /* 优化 Tab 样式 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 2px solid #ff4b4b; }
    /* 卡片样式 */
    .info-card { background-color: #f9f9f9; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏：配置区 ---
with st.sidebar:
    st.title("⚙️ 助手设置")

    default_key = "XXXX"  # 替换为你的真实 Key 或留空
    api_key = st.text_input(
        "通义千问 API Key",
        value=default_key,
        type="password",
        help="阿里云百炼控制台获取"
    )

    st.markdown("---")

    st.subheader("🎯 身份设定")
    reader_level = st.radio(
        "选择解释通俗度：",
        ("完全新手 (生活比喻)", "初级研究员 (学术+直观)", "专家 (深度总结)")
    )

    st.markdown("---")
    st.info("💡 **功能导航**：\n1. **概览**：摘要与引用生成\n2. **阅读**：全文对照与问答\n3. **润色**：中英互译与优化")

    # --- 新增：导出功能 ---
    st.markdown("---")
    st.subheader("💾 成果导出")
    if st.button("生成研读笔记 (Markdown)"):
        if "chat_history" in st.session_state and st.session_state.chat_history:
            # 构建笔记内容
            note_content = f"# 论文研读笔记\n日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            if "paper_summary" in st.session_state and st.session_state.paper_summary:
                note_content += f"## 1. 论文概览\n{st.session_state.paper_summary}\n\n"
            note_content += "## 2. 重点问答记录\n"
            for msg in st.session_state.chat_history:
                role = "AI 导师" if msg['role'] == 'assistant' else "我"
                note_content += f"**{role}**: {msg['content']}\n\n"

            st.download_button(
                label="📥 点击下载笔记",
                data=note_content,
                file_name="paper_study_note.md",
                mime="text/markdown"
            )
        else:
            st.warning("暂无对话记录可导出")


# --- 核心工具函数 ---

@st.cache_data
def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            # 移除页数限制，读取所有页面
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text: text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"PDF 读取失败: {e}")
        return None


# 上下文管理器：临时禁用代理 (给 DashScope 用)
class NoProxyContext:
    def __enter__(self):
        self.backup = {}
        for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
            if k in os.environ:
                self.backup[k] = os.environ[k]
                del os.environ[k]

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k, v in self.backup.items():
            os.environ[k] = v


def call_qwen(prompt, history=None, system_instruction=None):
    if not api_key:
        st.error("请先填入 API Key")
        return None
    dashscope.api_key = api_key

    # 默认 System Prompt
    if not system_instruction:
        system_instruction = f"""
你是一位专业、严谨的学术导师（Academic Research Mentor）。
用户的理解水平是：{reader_level}，请使用适合该水平的语言解释专业术语。

【身份与防伪声明】
如果用户询问：
- 你是谁开发的
- 你是谁开发的？
- 这个系统是谁做的
- 开发者是谁

请只回答下面这一句话，不要添加任何多余内容：
“本服务由【徐子强，2025012085】开发，仅用于课程研究展示。”

【回答约束】
- 仅基于用户上传的论文内容进行分析，不得引入外部知识。
- 若论文中未提及相关信息，请明确回答“论文中未给出相关信息”。
- 禁止编造作者、实验结果、数值或结论。
"""

    messages = [{'role': 'system', 'content': system_instruction}]
    if history:
        messages.extend(history[-4:])
    messages.append({'role': 'user', 'content': prompt})

    try:
        # 关键：调用 DashScope 时，使用上下文管理器临时清除代理环境变量
        with NoProxyContext():
            response = Generation.call(
                model="qwen-turbo",
                messages=messages,
                result_format='message'
            )

        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0]['message']['content']
        else:
            st.error(f"API Error: {response.message}")
            return None
    except Exception as e:
        st.error(f"Network Error: {e}")
        return None


# --- 主界面逻辑 ---
st.title("📄 PaperAgent Pro: 多模态论文助读")

# 全局状态管理
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "raw_text" not in st.session_state: st.session_state.raw_text = ""
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "paper_summary" not in st.session_state: st.session_state.paper_summary = None  # 新增：论文摘要缓存

# 文件上传
uploaded_file = st.file_uploader("📂 上传论文 (PDF)", type="pdf")

if uploaded_file:
    # 仅当文件变化时重新读取
    if st.session_state.raw_text == "":
        with st.spinner("正在解析 PDF 全文..."):
            st.session_state.raw_text = extract_text_from_pdf(uploaded_file)
            st.success("解析成功！")

if st.session_state.raw_text:
    # 新增 Tab 0: 概览 (移除了逻辑导图 Tab)
    tab0, tab1, tab2 = st.tabs(["🏠 智能概览", "📖 深度阅读", "✍️ 学术润色"])

    # === 功能 0: 智能概览与引用 (新增) ===
    with tab0:
        st.subheader("📑 论文核心信息卡")

        if st.session_state.paper_summary is None:
            if st.button("🚀 生成概览与引用"):
                prompt_summary = f"""请阅读论文前3000字，完成以下任务：
                1. 提取论文标题、作者（如无法提取则写Unknown）。
                2. 用中文总结论文的核心贡献（Objective）、方法（Method）和结论（Conclusion）。
                3. 生成该论文的 BibTeX 引用格式（年份和会议如果找不到，请根据内容推测或留空）。

                请严格按照 Markdown 格式输出，结构如下：
                ## 基本信息
                ...
                ## 核心摘要
                ...
                ## BibTeX
                ```bibtex
                ...
                ```

                论文内容：{st.session_state.raw_text[:3000]}
                """
                with st.spinner("AI 正在提炼核心信息..."):
                    summary = call_qwen(prompt_summary)
                    st.session_state.paper_summary = summary

        if st.session_state.paper_summary:
            st.markdown(st.session_state.paper_summary)
            st.info("💡 提示：你可以直接复制上方的 BibTeX 用于论文写作。")

    # === 功能 1: 基础阅读与问答 ===
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("📑 原文全文预览")
            # 显示全部文本
            st.text_area("Content", st.session_state.raw_text, height=700, label_visibility="collapsed")

        with col2:
            st.subheader("💬 AI 导师")
            # 术语分析按钮
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("🔍 提取核心术语表", key="btn_term"):
                    prompt = f"""请阅读以下论文片段，提取5-8个关键术语。
                    必须输出Markdown表格，包含列：| 术语 | 通俗比喻 | 学术定义 |。
                    论文片段（前2000字）：{st.session_state.raw_text[:2000]}"""
                    with st.spinner("分析中..."):
                        res = call_qwen(prompt)
                        if res: st.session_state.analysis_result = res

            with c_btn2:
                # 新增：一键提取实验数据
                if st.button("📊 提取实验结论", key="btn_data"):
                    prompt_data = f"""请阅读全文，专门提取实验部分的关键信息：
                    1. 使用了哪些数据集？
                    2. 对比了哪些 Baseline 方法？
                    3. 核心指标提升了多少？
                    请用列表形式简明扼要地回答。
                    论文内容：{st.session_state.raw_text[:4000]}"""
                    with st.spinner("挖掘数据中..."):
                        res_data = call_qwen(prompt_data)
                        st.session_state.chat_history.append({'role': 'assistant', 'content': res_data})

            if st.session_state.analysis_result:
                with st.expander("📚 核心术语表 (点击展开/收起)", expanded=True):
                    st.markdown(st.session_state.analysis_result)
                st.divider()

            # 聊天区域
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.chat_history:
                    st.chat_message(msg['role']).write(msg['content'])

            if user_input := st.chat_input("针对论文提问..."):
                st.chat_message("user").write(user_input)
                st.session_state.chat_history.append({'role': 'user', 'content': user_input})

                # 截取前3000字作为上下文，避免 token 溢出 (即使全文很长，发给AI时仍需截断)
                context = f"基于论文内容：\n{st.session_state.raw_text[:3000]}\n\n用户问题：{user_input}"
                with st.spinner("思考中..."):
                    response = call_qwen(context, history=st.session_state.chat_history[:-1])
                    if response:
                        st.chat_message("assistant").write(response)
                        st.session_state.chat_history.append({'role': 'assistant', 'content': response})

    # === 功能 2: 学术润色 ===
    with tab2:
        st.subheader("✍️ 学术翻译与润色助手")
        c1, c2 = st.columns(2)
        with c1:
            text_input = st.text_area("输入中文或英文段落", height=300, placeholder="粘贴你需要润色或翻译的论文段落...")
            mode = st.selectbox("选择模式", ["中译英 (学术风格)", "英译中 (通俗理解)", "英文润色 (语法+词汇提升)"])

        with c2:
            st.info("结果展示区")
            if st.button("开始处理") and text_input:
                prompt_polish = ""
                if mode == "中译英 (学术风格)":
                    prompt_polish = f"请将以下中文翻译成地道的学术英文（计算机/理工科风格）：\n{text_input}"
                elif mode == "英译中 (通俗理解)":
                    prompt_polish = f"请将以下英文翻译成中文，要求通俗易懂，适合初学者理解：\n{text_input}"
                else:
                    prompt_polish = f"请优化以下英文段落，纠正语法错误，并提升词汇的高级感和学术性：\n{text_input}"

                with st.spinner("AI 正在打磨文字..."):
                    res = call_qwen(prompt_polish, system_instruction="你是一位资深的SCI论文编辑。")
                    st.markdown(res)

else:
    st.info("👋 请在左侧上传 PDF 开始体验 PaperAgent Pro！")