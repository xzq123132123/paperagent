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
        page_title="PaperAgent Pro · 论文助读",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_css():
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&display=swap');

    /* ═══════════════════════════════════════════════════
       SCI-FI THEME — PaperAgent Pro
       ═══════════════════════════════════════════════════ */

    :root {
        --bg-deep: #060b14;
        --bg-panel: #0b1424;
        --bg-card: #0f1a2e;
        --accent-cyan: #00e5ff;
        --accent-purple: #b44aff;
        --accent-pink: #ff2d95;
        --text-primary: #e0e8f0;
        --text-dim: #6b7d95;
        --border-glow: rgba(0, 229, 255, 0.25);
        --border-subtle: rgba(0, 229, 255, 0.10);
    }

    /* ── Global ───────────────────────────────────── */

    .stApp {
        background: radial-gradient(ellipse at 50% 0%, #0d1a33 0%, #060b14 70%);
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    }

    .main > div:first-child {
        /* subtle scanline overlay */
        background-image:
            repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0, 229, 255, 0.008) 2px,
                rgba(0, 229, 255, 0.008) 4px
            );
        pointer-events: none;
    }

    /* ── Typography ───────────────────────────────── */

    h1, h2, h3 {
        font-family: 'Orbitron', 'Segoe UI', sans-serif !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }

    h1 {
        color: #00e5ff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 0 18px rgba(0, 229, 255, 0.6), 0 0 40px rgba(0, 229, 255, 0.2) !important;
        margin-bottom: 0.5rem !important;
    }

    h2 {
        color: #b44aff !important;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        text-shadow: 0 0 10px rgba(180, 74, 255, 0.4) !important;
    }

    h3 {
        color: #00e5ff !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }

    h4, h5, h6 {
        color: #c8d6e5 !important;
    }

    p, div, li, span, label, .stMarkdown {
        color: #b8c9dd !important;
    }

    /* ── Hide cruft ───────────────────────────────── */

    .reportview-container { margin-top: -2em; }
    .stDeployButton { display: none; }
    footer { visibility: hidden; }
    header { background: transparent !important; }

    /* ── Sidebar ──────────────────────────────────── */

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1424 0%, #080f1f 100%);
        border-right: 1px solid var(--border-subtle);
        box-shadow: 2px 0 30px rgba(0, 229, 255, 0.06);
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 1.2rem !important;
        color: #00e5ff !important;
        text-shadow: 0 0 12px rgba(0, 229, 255, 0.5) !important;
    }

    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #b44aff !important;
        font-family: 'Orbitron', sans-serif !important;
    }

    section[data-testid="stSidebar"] .stRadio label {
        color: #b8c9dd !important;
    }

    section[data-testid="stSidebar"] .stRadio [data-checked="true"] {
        /* selected radio pill */
        background: rgba(0, 229, 255, 0.12) !important;
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
        border-radius: 4px !important;
    }

    /* ── Inputs & Textareas ───────────────────────── */

    .stTextArea textarea, .stTextInput input {
        background-color: #0a101f !important;
        color: #00e5ff !important;
        border: 1px solid var(--border-glow) !important;
        border-radius: 4px !important;
        font-family: 'Consolas', 'Fira Code', monospace !important;
        caret-color: #00e5ff !important;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #00e5ff !important;
        box-shadow: 0 0 12px rgba(0, 229, 255, 0.25), inset 0 0 10px rgba(0, 229, 255, 0.04) !important;
        outline: none !important;
    }

    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: #3a506b !important;
    }

    /* ── Buttons ──────────────────────────────────── */

    .stButton > button {
        background: linear-gradient(135deg, #0d1a33 0%, #111f3a 100%) !important;
        color: #00e5ff !important;
        border: 1px solid rgba(0, 229, 255, 0.4) !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        font-family: 'Orbitron', 'Segoe UI', sans-serif !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #0a2247 0%, #132951 100%) !important;
        border-color: #00e5ff !important;
        box-shadow: 0 0 20px rgba(0, 229, 255, 0.35), inset 0 0 14px rgba(0, 229, 255, 0.06) !important;
        color: #fff !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 0 8px rgba(0, 229, 255, 0.2) !important;
    }

    /* ── Download buttons ─────────────────────────── */

    .stDownloadButton > button {
        background: linear-gradient(135deg, #0d1a33 0%, #111f3a 100%) !important;
        color: #b44aff !important;
        border: 1px solid rgba(180, 74, 255, 0.4) !important;
        border-radius: 4px !important;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.05em !important;
    }

    .stDownloadButton > button:hover {
        border-color: #b44aff !important;
        box-shadow: 0 0 20px rgba(180, 74, 255, 0.35), inset 0 0 14px rgba(180, 74, 255, 0.06) !important;
        color: #fff !important;
    }

    /* ── Tabs ─────────────────────────────────────── */

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px !important;
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px !important;
        background: rgba(15, 26, 46, 0.7) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 6px 6px 0px 0px !important;
        color: #4a6380 !important;
        font-family: 'Orbitron', 'Segoe UI', sans-serif !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        padding: 0 18px !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #00e5ff !important;
        border-color: rgba(0, 229, 255, 0.25) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #0f1d35 0%, #0b1526 100%) !important;
        border: 1px solid rgba(0, 229, 255, 0.4) !important;
        border-bottom: 2px solid #00e5ff !important;
        color: #00e5ff !important;
        font-weight: 700 !important;
        box-shadow: 0 -2px 16px rgba(0, 229, 255, 0.10) !important;
    }

    /* ── Info Card ────────────────────────────────── */

    .info-card {
        background: linear-gradient(135deg, rgba(15, 26, 46, 0.85) 0%, rgba(11, 20, 36, 0.9) 100%) !important;
        padding: 24px !important;
        border-radius: 6px !important;
        border: 1px solid var(--border-subtle) !important;
        border-left: 3px solid #00e5ff !important;
        box-shadow: 0 0 30px rgba(0, 229, 255, 0.06), inset 0 1px 0 rgba(255,255,255,0.02) !important;
        margin-bottom: 24px !important;
        backdrop-filter: blur(8px) !important;
    }

    /* ── Chat messages ────────────────────────────── */

    [data-testid="stChatMessage"] {
        background: rgba(15, 26, 46, 0.6) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 6px !important;
        padding: 12px 16px !important;
    }

    [data-testid="stChatMessage"][data-testid*="assistant"] {
        border-left: 3px solid #b44aff !important;
    }

    [data-testid="stChatMessage"][data-testid*="user"] {
        border-left: 3px solid #00e5ff !important;
    }

    /* ── Chat input ───────────────────────────────── */

    [data-testid="stChatInput"] textarea {
        background: #0a101f !important;
        color: #00e5ff !important;
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
        font-family: 'Consolas', monospace !important;
    }

    /* ── Progress bar ─────────────────────────────── */

    .stProgress > div > div {
        background: linear-gradient(90deg, #00e5ff, #b44aff, #ff2d95) !important;
        border-radius: 2px !important;
    }

    .stProgress {
        background: rgba(255,255,255,0.04) !important;
    }

    /* ── Expander ─────────────────────────────────── */

    .streamlit-expanderHeader {
        background: rgba(15, 26, 46, 0.5) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 4px !important;
        color: #00e5ff !important;
        font-family: 'Orbitron', sans-serif !important;
    }

    /* ── Horizontal rule ──────────────────────────── */

    hr, .stDivider {
        border-color: rgba(0, 229, 255, 0.12) !important;
    }

    /* ── Radio & Checkbox ─────────────────────────── */

    .stRadio [role="radiogroup"] label,
    .stCheckbox label {
        color: #b8c9dd !important;
    }

    /* ── Info / Warning / Success boxes ───────────── */

    .stAlert {
        background: rgba(15, 26, 46, 0.7) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 4px !important;
        color: #b8c9dd !important;
    }

    [data-testid="stInfo"] {
        border-left: 3px solid #00e5ff !important;
    }

    [data-testid="stSuccess"] {
        border-left: 3px solid #00ff88 !important;
    }

    [data-testid="stWarning"] {
        border-left: 3px solid #ffaa00 !important;
    }

    [data-testid="stError"] {
        border-left: 3px solid #ff2d95 !important;
    }

    /* ── Form submit button ───────────────────────── */

    [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #00e5ff20 0%, #b44aff20 100%) !important;
        border: 1px solid rgba(0, 229, 255, 0.5) !important;
        color: #00e5ff !important;
    }

    [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #00e5ff30 0%, #b44aff30 100%) !important;
        box-shadow: 0 0 24px rgba(0, 229, 255, 0.4) !important;
        color: #fff !important;
    }

    /* ── Toggle ───────────────────────────────────── */
    .stToggle [role="switch"] {
        /* No direct selector for inner, handle via checked state */
    }

    /* ── Spinner ──────────────────────────────────── */
    .stSpinner > div {
        border-top-color: #00e5ff !important;
    }

</style>
""",
        unsafe_allow_html=True,
    )


def build_system_prompt(reader_level: str) -> str:
    """Build the default system instruction for a given reader level."""
    return DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(reader_level=reader_level)
