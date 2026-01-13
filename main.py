import streamlit as st
import re  # <--- 新增这个，用于自动检测语言
import pdfplumber
import dashscope
import base64  # <--- 新增这个
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

# --- 🎨 视觉优化版 CSS ---
st.markdown("""
<style>
    /* 1. 全局背景与字体设置 */
    .stApp {
        background-color: #f8f9fa; /* 浅灰色背景，护眼且专业 */
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    }
    
    /* 2. 侧边栏样式：纯白背景，与主界面区分 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0; /* 极淡的分割线 */
    }

    /* 3. 字体颜色优化：提升对比度 */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important; /* 深青色标题，稳重 */
        font-weight: 600;
    }
    
    p, div, li, span, label, .stMarkdown {
        color: #333333 !important; /* 深灰色正文，高可读性 */
    }
    
    /* 4. 组件样式改进 */
    /* 隐藏无关元素 */
    .reportview-container { margin-top: -2em; }
    .stDeployButton {display:none;}
    footer {visibility: hidden;}

    /* 输入框与文本域：白底深字 */
    .stTextArea textarea, .stTextInput input {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #d1d5db; /* 浅灰色边框 */
        border-radius: 6px;
    }
    
    /* 按钮：学术蓝系列，提供视觉引导 */
    .stButton > button {
        background-color: #3498db; 
        color: white !important;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #2980b9; /* 悬停加深 */
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* 5. Tab 选项卡样式优化 */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 20px; 
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #e9ecef; /* 未选中态：浅灰 */
        border-radius: 6px 6px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #6c757d;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 3px solid #3498db; /* 选中态：蓝色下划线 */
        color: #2c3e50;
        font-weight: bold;
    }

    /* 6. 自定义信息卡片：白底+阴影 */
    .info-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 10px;
        border-left: 5px solid #3498db; /* 蓝色左边框呼应主题 */
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); /* 柔和阴影，增加层次感 */
        margin-bottom: 24px;
    }
    
    /* 侧边栏标题微调 */
    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# --- 侧边栏：配置区 ---
with st.sidebar:
    st.title("⚙️ 助手设置")

    default_key = ""  # 替换为你的真实 Key 或留空
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

def display_pdf(uploaded_file):
    """将 PDF 文件嵌入到 Streamlit 页面中"""
    # 读取文件二进制内容
    bytes_data = uploaded_file.getvalue()
    # 转为 base64 编码
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    # 嵌入 PDF 查看器
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


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


# --- 新增：长文本处理工具 ---

def split_text_into_chunks(text, chunk_size=4000, overlap=500):
    """
    朴素的滑窗切分函数
    chunk_size: 每个分片的字符数
    overlap: 重叠部分，防止上下文在切分处断裂
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        # 尽量在换行符处截断，避免切断句子
        if end < len(text):
            next_newline = text.find('\n', end)
            if next_newline != -1 and next_newline - end < 200:
                end = next_newline
        
        chunks.append(text[start:end])
        start = end - overlap # 滑窗推进，保留重叠
    return chunks

def generate_map_reduce_summary(full_text):
    """
    Map-Reduce 策略：分段总结 -> 汇总总结
    """
    # 1. 切分文本
    chunks = split_text_into_chunks(full_text, chunk_size=5000)
    
    # 如果文本很短，直接用原来的方法
    if len(chunks) == 1:
        return call_qwen(f"请阅读全文，生成摘要（贡献、方法、结论）：\n{full_text}")

    # 2. Map 阶段：分段摘要
    chunk_summaries = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, chunk in enumerate(chunks):
        status_text.text(f"正在研读第 {i+1}/{len(chunks)} 部分..." )
        prompt = f"""请简要总结以下论文片段的主要内容（保留关键技术点和实验结论）：
        片段内容：
        {chunk}
        """
        summary = call_qwen(prompt)
        if summary:
            chunk_summaries.append(summary)
        progress_bar.progress((i + 1) / len(chunks))
    
    # 3. Reduce 阶段：汇总
    status_text.text("正在整合全篇逻辑..." )
    combined_text = "\n\n".join(chunk_summaries)
    
    final_prompt = f"""你已经阅读了论文的各个部分，以下是各部分的摘要汇总：
    {combined_text}
    
    请根据上述汇总信息，重新生成一份结构清晰的**全文研读报告**。
    请严格按照以下 Markdown 格式输出：
    
    ## 1. 基本信息
    - **标题**：(尝试从内容推断)
    - **核心贡献**：(用一句话概括)

    ## 2. 详细摘要
    - **研究背景 (Problem)**：
    - **核心方法 (Method)**：
    - **实验结果 (Result)**：
    - **结论 (Conclusion)**：

    ## 3. 潜在局限与未来方向 (根据内容推断)
    """
    
    final_result = call_qwen(final_prompt)
    progress_bar.empty()
    status_text.empty()
    return final_result


# --- 主界面逻辑 ---
st.title("📄 PaperAgent Pro: 多模态论文助读")

# 全局状态管理
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "raw_text" not in st.session_state: st.session_state.raw_text = ""
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "paper_summary" not in st.session_state: st.session_state.paper_summary = None 

# 文件上传
uploaded_file = st.file_uploader("📂 上传论文 (PDF)", type="pdf")

if uploaded_file:
    # 仅当文件变化时重新读取
    if st.session_state.raw_text == "":
        with st.spinner("正在解析 PDF 全文..."):
            st.session_state.raw_text = extract_text_from_pdf(uploaded_file)
            st.success("解析成功！")

if st.session_state.raw_text:
    
    # 将 .info-card 应用于核心信息卡（原代码此处没有使用 class，现在加上以适配新样式）
    tab0, tab1, tab2 = st.tabs(["🏠 智能概览", "📖 深度阅读", "✍️ 学术润色"])

    # === 功能 0: 智能概览 (Map-Reduce 升级版) ===
    with tab0:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.subheader("📑 论文核心信息卡")

        if st.session_state.paper_summary is None:
            if st.button("🚀 生成深度概览 (全篇分析)"):
                with st.spinner("AI 正在使用滑窗策略阅读全篇论文，这可能需要 30-60 秒..."):
                    # 使用新的 Map-Reduce 函数
                    summary = generate_map_reduce_summary(st.session_state.raw_text)
                    st.session_state.paper_summary = summary
                    
                    # 额外单独生成 BibTeX (因为 summary prompt 变复杂了，分开生成更稳定)
                    bib_prompt = f"请根据论文前2000字，直接生成 BibTeX 格式。无需其他废话。\n内容：{st.session_state.raw_text[:2000]}"
                    bib_res = call_qwen(bib_prompt)
                    if bib_res:
                        st.session_state.paper_summary += f"\n\n## BibTeX\n```bibtex\n{bib_res}\n```"

        if st.session_state.paper_summary:
            st.markdown(st.session_state.paper_summary)
            st.info("💡 提示：你可以直接复制上方的 BibTeX 用于论文写作。")
        
        st.markdown('</div>', unsafe_allow_html=True) # 闭合卡片 div

    # === 功能 1: 深度阅读 (左侧多功能面板版) ===
    with tab1:
        # 调整布局比例：左侧信息区 (55%)，右侧交互区 (45%)
        col1, col2 = st.columns([5.5, 4.5])
        
        # --- 左侧：多功能信息面板 ---
        with col1:
            # 定义三个子面板：原文、知识库、纯文本
            left_tab1, left_tab2, left_tab3 = st.tabs(["📄 PDF 原文", "🧠 知识库 (术语/数据)", "📝 解析文本"])
            
            #Panel A: PDF 原文
            with left_tab1:
                display_pdf(uploaded_file)
            
            # Panel B: 知识库 (自动汇集提取出的信息)
            with left_tab2:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                has_content = False
                
                # 1. 展示概览 (如果有)
                if st.session_state.paper_summary:
                    st.markdown("### 📑 论文概览")
                    st.markdown(st.session_state.paper_summary)
                    st.divider()
                    has_content = True
                
                # 2. 展示术语表 (如果有)
                if st.session_state.analysis_result:
                    st.markdown("### 📚 核心术语表")
                    st.markdown(st.session_state.analysis_result)
                    st.divider()
                    has_content = True
                
                # 3. 提示信息
                if not has_content:
                    st.info("👈这里是空白的。请在右侧点击 **'提取核心术语'** 或在概览页生成 **'摘要'**，结果将自动显示在这里。")
                
                st.markdown('</div>', unsafe_allow_html=True)

            # Panel C: 纯文本备份
            with left_tab3:
                st.caption("如果 PDF 无法加载，可查看解析后的纯文本：")
                st.text_area("Raw Text", st.session_state.raw_text, height=800, label_visibility="collapsed")

        # --- 右侧：AI 导师交互区 ---
        with col2:
            st.subheader("💬 AI 导师")
            
            # --- 工具栏 (Action Bar) ---
            # 使用卡片包裹，视觉更整洁
            st.markdown('<div class="info-card" style="padding: 15px; margin-bottom: 15px;">', unsafe_allow_html=True)
            st.caption("🛠️ 挖掘工具 (点击后结果将在左侧'知识库'显示)")
            c_btn1, c_btn2 = st.columns(2)
            
            with c_btn1:
                if st.button("🔍 提取核心术语", key="btn_term", use_container_width=True):
                    prompt = f"""请阅读以下论文片段，提取5-8个关键术语。
                    必须输出Markdown表格，包含列：| 术语 | 通俗比喻 | 学术定义 |。
                    论文片段（前2000字）：{st.session_state.raw_text[:2000]}"""
                    with st.spinner("正在提取术语..."):
                        res = call_qwen(prompt)
                        if res:
                            st.session_state.analysis_result = res
                            st.success("已提取！请查看左侧【🧠 知识库】面板")
                            st.rerun() # 强制刷新以更新左侧

            with c_btn2:
                if st.button("📊 提取实验数据", key="btn_data", use_container_width=True):
                    prompt_data = f"""请阅读全文，专门提取实验部分的关键信息：
                    1. 使用了哪些数据集？
                    2. 对比了哪些 Baseline 方法？
                    3. 核心指标提升了多少？
                    请用列表形式简明扼要地回答。
                    论文内容：{st.session_state.raw_text}"""
                    with st.spinner("正在挖掘数据..."):
                        res_data = call_qwen(prompt_data)
                        # 数据提取的结果通常适合直接对话显示，也可以存入 session_state 显示在左侧
                        # 这里为了交互流畅，我们选择直接追加到聊天记录
                        st.session_state.chat_history.append({'role': 'assistant', 'content': f"� **实验数据提取结果**：\n\n{res_data}"})
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            # --- 聊天区域 ---
            # 固定高度容器，防止页面过长
            chat_container = st.container(height=600)
            with chat_container:
                for msg in st.session_state.chat_history:
                    st.chat_message(msg['role']).write(msg['content'])

            # 输入框
            if user_input := st.chat_input("针对论文提问..."):
                # 1. 显示用户输入
                with chat_container:
                    st.chat_message("user").write(user_input)
                st.session_state.chat_history.append({'role': 'user', 'content': user_input})

                # 2. 构建 Prompt (使用全文)
                context = f"基于论文内容：\n{st.session_state.raw_text}\n\n用户问题：{user_input}"
                
                # 3. AI 回答
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("思考中..."):
                            response = call_qwen(context, history=st.session_state.chat_history[:-1])
                            if response:
                                st.write(response)
                                st.session_state.chat_history.append({'role': 'assistant', 'content': response})

    # === 功能 2: 沉浸式翻译工作台 (参考 PDF 阅读器布局) ===
    with tab2:
        # 顶部：功能控制条 (扁平化设计)
        st.markdown('<div class="info-card" style="padding: 10px 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
        c_mode, c_src, c_act = st.columns([5, 3, 2])
        
        with c_mode:
            task_type = st.radio(
                "🎯 任务模式",
                ("🔁 智能翻译 (中⇌英)", "✨ 学术润色", "🔴 语法纠错"),
                horizontal=True,
                label_visibility="collapsed"
            )
        
        with c_src:
            # 开关：决定左侧显示 PDF 还是 空白输入框
            # 默认为 True (显示 PDF)
            source_mode = st.toggle("📖 显示论文 PDF 原件", value=True if uploaded_file else False)
        
        with c_act:
            run_btn = st.button("🚀 立即执行", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 主工作区：左右分栏
        col_left, col_right = st.columns([1, 1])

        # --- 左侧：原文参考区 (Reference) ---
        with col_left:
            if source_mode and st.session_state.raw_text:
                st.markdown("**� 论文原文库 (仅供复制参考)**")
                # 显示全文，方便用户复制
                st.text_area(
                    "Ref Text",
                    value=st.session_state.raw_text,
                    height=700,
                    label_visibility="collapsed",
                    disabled=False, # 允许选中复制
                    help="请从中复制您想翻译的段落，粘贴到右侧输入框中。"
                )
            else:
                st.markdown("**📄 原文暂存区 (自由粘贴)**")
                # 空白画布，让用户自己粘贴大段文字
                custom_text = st.text_area(
                    "Custom Text",
                    height=700,
                    placeholder="在此粘贴大段原文作为参考...",
                    label_visibility="collapsed"
                )

        # --- 右侧：翻译工作区 (Workbench) ---
        with col_right:
            # 1. 待处理片段输入框
            st.markdown("**✂️ 待处理片段 (在此粘贴)**")
            
            # 如果session中没有content，初始化为空
            if "target_clip" not in st.session_state: st.session_state.target_clip = ""
            
            target_input = st.text_area(
                "Target Clip",
                key="input_clip",
                height=200, # 较矮的高度，用于放选中的段落
                placeholder="💡 操作指南：\n1. 从左侧复制一段文字\n2. 粘贴到这里\n3. 点击上方\"🚀 立即执行\"",
                label_visibility="collapsed"
            )

            # 2. 结果输出框
            st.markdown("**📝 AI 结果**")
            output_text = st.session_state.get("polished_result", "")
            
            st.text_area(
                "Result",
                value=output_text,
                height=420, # 占据剩余空间
                label_visibility="collapsed"
            )

        # --- 逻辑处理 (点击执行后) ---
        if run_btn and target_input:
            prompt_task = ""
            system_role = "你是一位资深的 Nature/Science 期刊审稿人。"
            
            # 逻辑 A: 智能翻译
            if "智能翻译" in task_type:
                contains_chinese = bool(re.search(r'[\u4e00-\u9fa5]', target_input))
                if contains_chinese:
                    prompt_task = f"请将以下中文翻译成**地道的学术英文 (SCI风格)**：\n\n{target_input}"
                else:
                    prompt_task = f"请将以下英文翻译成**通俗流畅的学术中文**：\n\n{target_input}"
            
            # 逻辑 B: 润色
            elif "学术润色" in task_type:
                prompt_task = f"请润色以下段落，提升词汇高级感和语法准确性：\n\n{target_input}"
            
            # 逻辑 C: 纠错
            elif "语法纠错" in task_type:
                prompt_task = f"请找出以下段落的语法错误并给出修改建议：\n\n{target_input}"

            with st.spinner("AI 正在处理..."):
                # 调用 AI
                res = call_qwen(prompt_task, system_instruction=system_role)
                st.session_state.polished_result = res
                st.rerun() # 刷新以显示结果

else:
    st.info("👋 请在左侧上传 PDF 开始体验 PaperAgent Pro！")
