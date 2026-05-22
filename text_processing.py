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

    # Append default sci-fi node styling (mermaid v10 flowchart)
    if text.lstrip().startswith(("flowchart", "graph")):
        text += (
            "\nclassDef default fill:#0d1a33,stroke:#00e5ff,"
            "color:#e0e8f0,stroke-width:1.5px,rx:8,ry:8;\n"
        )

    return text


def build_mermaid_prompt(full_text: str) -> str:
    """Prompt that instructs the LLM to output a clean Mermaid flowchart."""
    return f"""
请基于全文生成 Mermaid 逻辑结构导图，严格遵循学术规范。

【必须遵守】
1) 输出必须以 flowchart LR 开头（从左到右横向布局），只输出 Mermaid 代码本体。
2) 每个节点必须写成：ID["显示文字"]（显示文字允许空格和中文）。
   - ID 只能用 A1,A2,B1... 这种简短ID。
   - 每个节点的显示文字必须包含分类标签+内容，如 "背景：..."、"方法：..."、"实验：..."、"结论：..."。
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
   flowchart LR
   A["背景：传统方法无法<br/>同时刻画区间范围"]
   A --> B["提出区间自回归<br/>(ACI) 模型"]
   B --> C["采用最小距离估计<br/>进行参数估计"]
   C --> D["实验：锌耗降低<br/>46kg / 精度提升 12%"]
   D --> E["结论：区间建模<br/>优于传统点估计"]
   B -.-> S1["说明：历史数据<br/>包含区间信息"]
   D -.-> S2["未明确：模型<br/>鲁棒性验证缺失"]

【论文内容】
{full_text}
""".strip()


def render_mermaid(mermaid_code: str, height: int = 700):
    """Render Mermaid diagram via injected HTML + mermaid@10 CDN."""
    mermaid_code = clean_mermaid(mermaid_code)

    html = f"""
    <style>
      .mermaid-container {{
        background: linear-gradient(135deg, rgba(6,11,20,0.92), rgba(13,26,51,0.85));
        border: 1px solid rgba(0,229,255,0.15);
        border-radius: 10px;
        padding: 24px 16px;
        box-shadow: 0 0 40px rgba(0,229,255,0.06), inset 0 0 80px rgba(0,0,0,0.3);
        overflow: auto;
      }}
      .mermaid-container svg {{
        max-width: 100%;
        filter: drop-shadow(0 0 6px rgba(0,229,255,0.2));
      }}
      .mermaid-container .edgePath .path {{
        stroke-width: 1.8px;
      }}
      .mermaid-container .node rect,
      .mermaid-container .node circle,
      .mermaid-container .node polygon {{
        stroke-width: 1.4px;
      }}
    </style>
    <div class="mermaid-container">
      <div class="mermaid">
      {mermaid_code}
      </div>
    </div>

    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{
        startOnLoad: true,
        securityLevel: 'loose',
        theme: 'base',
        themeVariables: {{
          primaryColor: '#0d1a33',
          primaryTextColor: '#e0e8f0',
          primaryBorderColor: '#00e5ff',
          lineColor: '#b44aff',
          secondaryColor: '#0f1d35',
          secondaryTextColor: '#b8c9dd',
          secondaryBorderColor: '#b44aff',
          tertiaryColor: '#080f1f',
          tertiaryTextColor: '#8899aa',
          tertiaryBorderColor: '#5a6a80',
          fontFamily: 'Segoe UI, Helvetica Neue, sans-serif',
          fontSize: '15px',
          edgeLabelBackground: 'transparent',
        }},
        flowchart: {{
          htmlLabels: true,
          curve: 'basis',
          padding: 20,
          nodeSpacing: 60,
          rankSpacing: 70,
        }},
      }});
    </script>
    """

    components.html(html, height=height, scrolling=True)
