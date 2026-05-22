"""Map-Reduce summarization and Mermaid mindmap generation.

These functions depend on llm_utils (for LLM calls) and text_processing
(for chunking / prompt building).
"""

import streamlit as st

from llm_utils import call_qwen
from text_processing import split_text_into_chunks, build_mermaid_prompt


def generate_map_reduce_summary(api_key, reader_level, full_text):
    """Map-Reduce: chunk → per-chunk summary → merged final report."""
    chunks = split_text_into_chunks(full_text, chunk_size=5000)

    if len(chunks) == 1:
        return call_qwen(
            api_key, reader_level,
            f"请阅读全文，生成摘要（贡献、方法、结论）：\n{full_text}",
        )

    # Map phase
    chunk_summaries = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, chunk in enumerate(chunks):
        status_text.text(f"正在研读第 {i + 1}/{len(chunks)} 部分...")
        summary = call_qwen(
            api_key, reader_level,
            f"请简要总结以下论文片段的主要内容（保留关键技术点和实验结论）：\n片段内容：\n{chunk}",
        )
        if summary:
            chunk_summaries.append(summary)
        progress_bar.progress((i + 1) / len(chunks))

    # Reduce phase
    status_text.text("正在整合全篇逻辑...")
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

    final_result = call_qwen(api_key, reader_level, final_prompt)
    progress_bar.empty()
    status_text.empty()
    return final_result


def generate_mindmap_code(api_key, reader_level, text):
    """Ask the LLM to produce a Mermaid mindmap for the paper."""
    prompt = build_mermaid_prompt(text[:8000])
    return call_qwen(api_key, reader_level, prompt)
