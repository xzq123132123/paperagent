"""Text chunking, Mermaid cleaning/rendering, and prompt builders."""

import re

import streamlit.components.v1 as components


# ── Text chunking ───────────────────────────────────────────────

def split_text_into_chunks(text, chunk_size=4000, overlap=500):
    """Sliding-window text chunker. Tries to break at newlines near chunk edges."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            next_newline = text.find("\n", end)
            if next_newline != -1 and next_newline - end < 200:
                end = next_newline
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


# ── Text wrapping ───────────────────────────────────────────────

def wrap_text(text, max_len=12):
    """Auto-insert <br/> for long node labels."""
    if not text:
        return text
    lines = []
    current_line = ""
    for char in text:
        current_line += char
        if len(current_line) >= max_len:
            lines.append(current_line)
            current_line = ""
    if current_line:
        lines.append(current_line)
    return "<br/>".join(lines)


# ── Mermaid helpers ─────────────────────────────────────────────

def clean_mermaid(text: str) -> str:
    """Strip markdown fences and chatter, keep only the Mermaid diagram body."""
    if not text:
        return ""

    text = text.strip()

    # Remove ```mermaid ... ``` fences
    m = re.search(r"```(?:mermaid)?\s*(.*?)```", text, flags=re.S)
    if m:
        text = m.group(1).strip()

    # Start from the first Mermaid diagram keyword
    m2 = re.search(
        r"(?s)\b(flowchart|graph|sequenceDiagram|stateDiagram|classDiagram|"
        r"erDiagram|journey|gantt)\b.*",
        text,
    )
    if m2:
        text = m2.group(0).strip()

    # Remove zero-width characters / BOM
    text = text.replace("​", "").replace("﻿", "")

    # Auto-wrap long node labels
    def replace_node(match):
        id_part = match.group(1)
        text_part = match.group(2)
        if "<br/>" not in text_part:
            wrapped_text = wrap_text(text_part)
            return f'{id_part}["{wrapped_text}"]'
        return match.group(0)

    text = re.sub(r'(\w+)\["([^"]+)"\]', replace_node, text)
    return text


def build_mermaid_prompt(full_text: str) -> str:
    """Prompt that instructs the LLM to output a clean Mermaid flowchart."""
    return f"""
请基于全文生成 Mermaid 逻辑结构导图，严格遵循学术规范。

【必须遵守】
1) 输出必须以 flowchart TD 开头，只输出 Mermaid 代码本体。
2) 每个节点必须写成：ID["显示文字"]（显示文字允许空格和中文）。
   - ID 只能用 A1,A2,B1... 这种简短ID，禁止用驼峰词当ID。
3) 逻辑关系表示：
   - "-->"：主逻辑关系（论文真正给出的内容）
   - "-.->"：说明/注释/非主逻辑（文献未明确给出的内容）
4) 内容处理原则：
   - 论文真正给出的结论 → 画在主逻辑链
   - 文献未明确给出的结论 → 不作为主结论节点
   - 如需说明信息缺失，用虚线说明节点，而不是"结论 → 未给出信息"
5) 节点文本换行要求：
   - 所有较长节点文本，必须在合适位置插入 <br/> 强制换行
   - 不改语义，只做视觉换行
   - 每行建议 10～14 个中文字符
6) 必须提取论文中的具体内容填充到节点中：
   - 背景：写出具体要解决什么难题？
   - 方法：写出具体的算法名称、模块名称（如 "HGSTA算法", "混合策略"）。
   - 实验：写出具体的提升数值（如 "锌耗降低 46kg"）。
7) 示例结构（供参考）：
   flowchart TD
   A["背景"]
   A --> B["区间数据相比点数据<br/>包含更多信息"]
   A --> C["传统方法难以同时刻画<br/>区间范围和水平特征"]

   D["方法"]
   D --> D1["提出区间自回归<br/>(ACI) 模型"]
   D --> D2["采用最小距离估计<br/>进行参数估计"]

   E["实验结果"]
   E --> F["结论"]

   F -.-> N["部分结论在文献中<br/>未明确报告"]

【论文内容】
{full_text}
""".strip()


def render_mermaid(mermaid_code: str, height: int = 620):
    """Render Mermaid diagram via injected HTML + mermaid@10 CDN."""
    mermaid_code = clean_mermaid(mermaid_code)

    html = f"""
    <div class="mermaid">
    {mermaid_code}
    </div>

    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose' }});
    </script>
    """

    components.html(html, height=height, scrolling=True)
