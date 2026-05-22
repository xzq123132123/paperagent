"""Page config, CSS styles, constants, and system prompt template."""

import streamlit as st

MODEL_NAME = "qwen-turbo"

DEFAULT_SYSTEM_PROMPT_TEMPLATE = """\
你是一位专业、严谨的学术导师（Academic Research Mentor）。
用户的理解水平是：{reader_level}，请使用适合该水平的语言解释专业术语。

【身份与防伪声明】
如果用户询问：
- 你是谁开发的
- 你是谁开发的？
- 这个系统是谁做的
- 开发者是谁

请只回答下面这一句话，不要添加任何多余内容：
"本服务由【徐子强，2025012085】开发，仅用于课程研究展示。"

【回答约束】
- 仅基于用户上传的论文内容进行分析，不得引入外部知识。
- 若论文中未提及相关信息，请明确回答"论文中未给出相关信息"。
- 禁止编造作者、实验结果、数值或结论。
"""


def setup_page():
    st.set_page_config(
        page_title="AI 论文助读 Agent Pro",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_css():
    st.markdown(
        """
<style>
    .stApp {{
        background-color: #f8f9fa;
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: #2c3e50 !important;
        font-weight: 600;
    }}

    p, div, li, span, label, .stMarkdown {{
        color: #333333 !important;
    }}

    .reportview-container {{ margin-top: -2em; }}
    .stDeployButton {{display:none;}}
    footer {{visibility: hidden;}}

    .stTextArea textarea, .stTextInput input {{
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #d1d5db;
        border-radius: 6px;
    }}

    .stButton > button {{
        background-color: #3498db;
        color: white !important;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }}
    .stButton > button:hover {{
        background-color: #2980b9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 20px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: #e9ecef;
        border-radius: 6px 6px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #6c757d;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #ffffff;
        border-bottom: 3px solid #3498db;
        color: #2c3e50;
        font-weight: bold;
    }}

    .info-card {{
        background-color: #ffffff;
        padding: 24px;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 24px;
    }}

    [data-testid="stSidebar"] h1 {{
        font-size: 1.5rem;
        color: #2c3e50;
    }}
</style>
""",
        unsafe_allow_html=True,
    )


def build_system_prompt(reader_level: str) -> str:
    """Build the default system instruction for a given reader level."""
    return DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(reader_level=reader_level)
