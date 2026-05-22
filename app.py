import re
import base64
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from config import setup_page, inject_css, build_system_prompt
from pdf_utils import (
    extract_text_from_pdf,
    get_file_id,
    display_pdf,
    display_pdf_selectable,
    generate_pdf_content,
)
from llm_utils import call_qwen
from text_processing import clean_mermaid, render_mermaid
from summarization import generate_map_reduce_summary, generate_mindmap_code

# ── Page setup ──────────────────────────────────────────────────
setup_page()
inject_css()

# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 助手设置")

    default_key = ""
    api_key = st.text_input(
        "通义千问 API Key",
        value=default_key,
        type="password",
        help="阿里云百炼控制台获取",
    )

    st.markdown("---")

    st.subheader("🎯 身份设定")
    reader_level = st.radio(
        "选择解释通俗度：",
        ("完全新手 (生活比喻)", "初级研究员 (学术+直观)", "专家 (深度总结)"),
    )

    st.markdown("---")
    st.info(
        "💡 **功能导航**：\n"
        "1. **概览**：使用滑窗+归纳策略生成深度全文分析，包含详细摘要和BibTeX引用\n"
        "2. **阅读**：左侧嵌入PDF原文（保留排版），右侧AI导师实时问答，智能知识库自动沉淀关键信息\n"
        "3. **润色**：智能翻译（中⇌英）、学术润色、语法纠错，支持PDF原文对照"
    )

    st.markdown("---")
    st.subheader("💾 成果导出")

    has_history = "chat_history" in st.session_state and st.session_state.chat_history
    has_summary = "paper_summary" in st.session_state and st.session_state.paper_summary

    if has_history or has_summary:
        md_content = f"# 论文研读笔记\n日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        if has_summary:
            md_content += f"## 1. 论文概览\n{st.session_state.paper_summary}\n\n"
        if has_history:
            md_content += "## 2. 重点问答记录\n"
            for msg in st.session_state.chat_history:
                role = "AI 导师" if msg["role"] == "assistant" else "我"
                md_content += f"**{role}**: {msg['content']}\n\n"

        col_md, col_pdf = st.columns(2)

        with col_md:
            st.download_button(
                label="⬇️ Markdown",
                data=md_content,
                file_name="study_notes.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_notes_md",
            )

        with col_pdf:
            if st.button("⬇️ PDF", key="btn_gen_pdf", use_container_width=True):
                with st.spinner("正在生成 PDF..."):
                    pdf_data = generate_pdf_content(
                        st.session_state.paper_summary,
                        st.session_state.chat_history,
                    )
                    st.session_state.tmp_pdf_data = pdf_data

            if "tmp_pdf_data" in st.session_state:
                st.download_button(
                    label="点击保存 PDF",
                    data=st.session_state.tmp_pdf_data,
                    file_name="study_notes.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_download_pdf",
                )
    else:
        st.caption("暂无笔记内容可导出")

# ── Session state init ──────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "paper_summary" not in st.session_state:
    st.session_state.paper_summary = None
if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None

# ── Main UI ─────────────────────────────────────────────────────
st.title("📄 PaperAgent Pro: 多模态论文助读")

uploaded_file = st.file_uploader("📂 上传论文 (PDF)", type="pdf")

if uploaded_file:
    new_file_id = get_file_id(uploaded_file)

    if st.session_state.current_file_id != new_file_id:
        st.session_state.current_file_id = new_file_id
        st.session_state.raw_text = ""
        st.session_state.paper_summary = None
        st.session_state.analysis_result = None
        st.session_state.chat_history = []
        st.session_state.polished_result = ""

    if st.session_state.raw_text == "":
        with st.spinner("正在解析 PDF 全文..."):
            st.session_state.raw_text = extract_text_from_pdf(uploaded_file)
            st.success("解析成功！")

if st.session_state.raw_text:
    tab0, tab1, tab2 = st.tabs(["🏠 智能概览", "📖 深度阅读", "✍️ 学术润色"])

    # ═══════════════════════════════════════════════════════════
    # Tab 0: Smart Overview
    # ═══════════════════════════════════════════════════════════
    with tab0:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.subheader("📑 论文核心信息卡")

        c_act1, c_act2 = st.columns([1, 1])

        with c_act1:
            if st.button("🚀 生成深度概览 (Text)", use_container_width=True):
                with st.spinner("AI 正在使用滑窗策略阅读全篇论文..."):
                    summary = generate_map_reduce_summary(
                        api_key, reader_level, st.session_state.raw_text
                    )
                    st.session_state.paper_summary = summary

                    bib_prompt = (
                        f"请根据论文前2000字，直接生成 BibTeX 格式。\n"
                        f"内容：{st.session_state.raw_text[:2000]}"
                    )
                    bib_res = call_qwen(api_key, reader_level, bib_prompt)
                    if bib_res:
                        st.session_state.paper_summary += (
                            f"\n\n## BibTeX\n```bibtex\n{bib_res}\n```"
                        )

        with c_act2:
            if st.button("🗺️ 生成逻辑导图 (Graph)", use_container_width=True):
                with st.spinner("AI 正在梳理逻辑结构..."):
                    if not st.session_state.raw_text:
                        st.warning("请先上传并解析PDF")
                    else:
                        raw_code = generate_mindmap_code(
                            api_key, reader_level, st.session_state.raw_text
                        )
                        clean_code = clean_mermaid(raw_code)
                        st.session_state.mindmap_raw = raw_code
                        st.session_state.mindmap_code = clean_code

        st.divider()

        if "mindmap_code" in st.session_state and st.session_state.mindmap_code:
            st.markdown("### 🧠 逻辑结构导图")
            try:
                render_mermaid(st.session_state.mindmap_code, height=650)
            except Exception as e:
                st.error(f"Mermaid 渲染失败：{e}")
            st.divider()

        if st.session_state.paper_summary:
            st.markdown("### 📝 深度概览")
            st.markdown(st.session_state.paper_summary)
            st.info("💡 提示：你可以直接复制上方的 BibTeX 用于论文写作。")

        st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    # Tab 1: Deep Reading
    # ═══════════════════════════════════════════════════════════
    with tab1:
        col1, col2 = st.columns([5.5, 4.5])

        with col1:
            left_tab1, left_tab2 = st.tabs(["📄 PDF 原文", "🧠 知识库 (术语/数据)"])

            with left_tab1:
                st.download_button(
                    "📥 下载 PDF",
                    data=uploaded_file.getvalue(),
                    file_name=uploaded_file.name,
                    mime="application/pdf",
                    key="download_pdf_tab1",
                )
                display_pdf(uploaded_file)

            with left_tab2:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                has_content = False

                if st.session_state.paper_summary:
                    st.markdown("### 📑 论文概览")
                    st.markdown(st.session_state.paper_summary)
                    st.divider()
                    has_content = True

                if st.session_state.analysis_result:
                    st.markdown("### 📚 核心术语表")
                    st.markdown(st.session_state.analysis_result)
                    st.divider()
                    has_content = True

                if not has_content:
                    st.info(
                        "👈 这里是智能知识库。\n\n"
                        "当你在右侧点击 **'提取核心术语'** 或在概览页生成 **'摘要'** 后，"
                        "AI 提炼的干货会自动沉淀在这里，方便你随时查阅，无需翻找聊天记录。"
                    )

                st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.subheader("💬 AI 导师")

            st.markdown(
                '<div class="info-card" style="padding: 15px; margin-bottom: 15px;">',
                unsafe_allow_html=True,
            )
            st.caption("🛠️ 挖掘工具 (点击后结果将在左侧'知识库'显示)")
            c_btn1, c_btn2 = st.columns(2)

            with c_btn1:
                if st.button("🔍 提取核心术语", key="btn_term", use_container_width=True):
                    prompt = (
                        f"请阅读以下论文片段，提取5-8个关键术语。\n"
                        f"必须输出Markdown表格，包含列：| 术语 | 通俗比喻 | 学术定义 |。\n"
                        f"论文片段（前2000字）：{st.session_state.raw_text[:2000]}"
                    )
                    with st.spinner("正在提取术语..."):
                        res = call_qwen(api_key, reader_level, prompt)
                        if res:
                            st.session_state.analysis_result = res
                            st.success("已提取！请查看左侧【🧠 知识库】面板")
                            st.rerun()

            with c_btn2:
                if st.button("📊 提取实验数据", key="btn_data", use_container_width=True):
                    prompt_data = (
                        f"请阅读全文，专门提取实验部分的关键信息：\n"
                        f"1. 使用了哪些数据集？\n"
                        f"2. 对比了哪些 Baseline 方法？\n"
                        f"3. 核心指标提升了多少？\n"
                        f"请用列表形式简明扼要地回答。\n"
                        f"论文内容：{st.session_state.raw_text}"
                    )
                    with st.spinner("正在挖掘数据..."):
                        res_data = call_qwen(api_key, reader_level, prompt_data)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"📊 **实验数据提取结果**：\n\n{res_data}",
                        })
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

            chat_container = st.container(height=600)
            with chat_container:
                for msg in st.session_state.chat_history:
                    st.chat_message(msg["role"]).write(msg["content"])

            if user_input := st.chat_input("针对论文提问..."):
                with chat_container:
                    st.chat_message("user").write(user_input)
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input,
                })

                context = (
                    f"基于论文内容：\n{st.session_state.raw_text}\n\n"
                    f"用户问题：{user_input}"
                )

                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("思考中..."):
                            response = call_qwen(
                                api_key, reader_level, context,
                                history=st.session_state.chat_history[:-1],
                            )
                            if response:
                                st.write(response)
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": response,
                                })

    # ═══════════════════════════════════════════════════════════
    # Tab 2: Academic Polishing
    # ═══════════════════════════════════════════════════════════
    with tab2:
        if "task_type" not in st.session_state:
            st.session_state.task_type = "🔁 智能翻译 (中⇌英)"
        if "target_input" not in st.session_state:
            st.session_state.target_input = ""
        if "polished_result" not in st.session_state:
            st.session_state.polished_result = ""

        st.markdown(
            '<div class="info-card" style="padding: 10px 20px; margin-bottom: 20px;">',
            unsafe_allow_html=True,
        )
        c_mode, c_src, _ = st.columns([5, 3, 2])

        with c_mode:
            task_type = st.radio(
                "🎯 任务模式",
                ("🔁 智能翻译 (中⇌英)", "✨ 学术润色", "🔴 语法纠错"),
                horizontal=True,
                label_visibility="collapsed",
                key="task_type",
            )

        with c_src:
            source_mode = st.toggle(
                "📖 显示论文 PDF 原件",
                value=True if uploaded_file else False,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 1])

        with col_left:
            if source_mode and uploaded_file:
                st.markdown("**📖 论文原文 (保留排版，请直接划词复制)**")
                st.download_button(
                    "📥 下载 PDF",
                    data=uploaded_file.getvalue(),
                    file_name=uploaded_file.name,
                    mime="application/pdf",
                    key="download_pdf_tab2",
                )
                display_pdf_selectable(uploaded_file, height=700)

                if "page_num" not in st.session_state:
                    st.session_state.page_num = 0

                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    if st.button("Prev Page"):
                        st.session_state.page_num = max(
                            0, st.session_state.page_num - 1
                        )
                with c2:
                    if st.button("Next Page"):
                        st.session_state.page_num = (
                            st.session_state.page_num + 1
                        )
                with c3:
                    st.write(f"当前页: {st.session_state.page_num + 1}")

                if st.button("🔎 OCR 当前页（可复制）"):
                    with st.spinner("正在 OCR..."):
                        placeholder_text = (
                            f"这是第 {st.session_state.page_num + 1} 页的OCR结果示例。\n\n"
                            f"在实际环境中，这里会显示从PDF页面识别出的真实文本。\n\n"
                            f"要启用完整的OCR功能，请安装以下依赖：\n"
                            f"1. pip install pytesseract pdf2image Pillow\n"
                            f"2. 安装Tesseract OCR引擎\n"
                            f"3. 安装Poppler（用于PDF转图像）\n\n"
                            f"安装完成后，请取消注释代码中的OCR相关函数。"
                        )
                        st.session_state.input_clip = placeholder_text
                        st.success('OCR 完成：已自动填入待处理片段，可直接点击「立即执行」翻译。')
            else:
                st.markdown("**📄 自由粘贴区 (无 PDF 时使用)**")
                st.text_area(
                    "Custom Text",
                    height=700,
                    placeholder="在此粘贴大段原文作为参考...",
                    label_visibility="collapsed",
                )

        with col_right:
            st.markdown("**✂️ 待处理片段 (在此粘贴)**")

            if "input_clip" not in st.session_state:
                st.session_state.input_clip = ""
            if "polished_result" not in st.session_state:
                st.session_state.polished_result = ""

            with st.form("translate_form", clear_on_submit=False):
                st.text_area(
                    "Target Clip",
                    key="input_clip",
                    height=200,
                    placeholder=(
                        '💡 操作指南：\n'
                        '1. 从左侧复制一段文字\n'
                        '2. 粘贴到这里\n'
                        '3. 点击上方「🚀 立即执行」'
                    ),
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button("🚀 立即执行")

            st.markdown("**📝 AI 结果**")
            st.text_area(
                "Result",
                value=st.session_state.get("polished_result", ""),
                height=420,
                label_visibility="collapsed",
            )

        if submitted:
            target_input = st.session_state.input_clip.strip()
            if not target_input:
                st.warning("请先粘贴待处理片段")
            else:
                system_role = "你是一位资深的 Nature/Science 期刊审稿人。"

                if "智能翻译" in task_type:
                    contains_chinese = bool(
                        re.search(r"[一-龥]", target_input)
                    )
                    prompt_task = (
                        f"请将以下中文翻译成**地道的学术英文 (SCI风格)**：\n\n{target_input}"
                        if contains_chinese
                        else f"请将以下英文翻译成**通俗流畅的学术中文**：\n\n{target_input}"
                    )
                elif "学术润色" in st.session_state.task_type:
                    prompt_task = (
                        f"请润色以下段落，提升词汇高级感和语法准确性：\n\n{target_input}"
                    )
                else:
                    prompt_task = (
                        f"请找出以下段落的语法错误并给出修改建议：\n\n{target_input}"
                    )

                with st.spinner("AI 正在处理..."):
                    st.session_state.polished_result = call_qwen(
                        api_key, reader_level, prompt_task,
                        system_instruction=system_role,
                    )

else:
    st.info("👋 请在左侧上传 PDF 开始体验 PaperAgent Pro！")
