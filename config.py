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


# ═══════════════════════════════════════════════════════════════
# Shared CSS (applied in every theme)
# ═══════════════════════════════════════════════════════════════

_BASE_CSS = """
<style>
    .reportview-container { margin-top: -2em; }
    .stDeployButton { display: none; }
    footer { visibility: hidden; }
    header { background: transparent !important; }
</style>
"""

# ═══════════════════════════════════════════════════════════════
# Theme definitions
# ═══════════════════════════════════════════════════════════════

THEMES = {}

# ── Theme 1: Sci-Fi Neon ──────────────────────────────────────

THEMES["sci-fi"] = {
    "name": "🌌 霓虹科幻",
    "css": """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&display=swap');

    .stApp {
        background: radial-gradient(ellipse at 50% 0%, #0d1a33 0%, #060b14 70%);
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    }

    .main > div:first-child {
        background-image:
            repeating-linear-gradient(
                0deg, transparent, transparent 2px,
                rgba(0, 229, 255, 0.008) 2px, rgba(0, 229, 255, 0.008) 4px
            );
        pointer-events: none;
    }

    h1, h2, h3 {
        font-family: 'Orbitron', 'Segoe UI', sans-serif !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
    }
    h1 { color: #00e5ff !important; font-size: 2rem !important; font-weight: 700 !important;
         text-shadow: 0 0 18px rgba(0,229,255,0.6), 0 0 40px rgba(0,229,255,0.2) !important; }
    h2 { color: #b44aff !important; font-size: 1.3rem !important; font-weight: 600 !important;
         text-shadow: 0 0 10px rgba(180,74,255,0.4) !important; }
    h3 { color: #00e5ff !important; }
    h4, h5, h6 { color: #c8d6e5 !important; }
    p, div, li, span, label, .stMarkdown { color: #b8c9dd !important; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1424 0%, #080f1f 100%);
        border-right: 1px solid rgba(0,229,255,0.1);
        box-shadow: 2px 0 30px rgba(0,229,255,0.06);
    }
    section[data-testid="stSidebar"] h1 { color: #00e5ff !important; font-size: 1.2rem !important;
         text-shadow: 0 0 12px rgba(0,229,255,0.5) !important; }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #b44aff !important; }
    section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSelectbox label { color: #b8c9dd !important; }

    .stTextArea textarea, .stTextInput input {
        background-color: #0a101f !important; color: #00e5ff !important;
        border: 1px solid rgba(0,229,255,0.25) !important; border-radius: 4px !important;
        font-family: 'Consolas', 'Fira Code', monospace !important; caret-color: #00e5ff !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #00e5ff !important;
        box-shadow: 0 0 12px rgba(0,229,255,0.25), inset 0 0 10px rgba(0,229,255,0.04) !important;
    }
    .stTextArea textarea::placeholder, .stTextInput input::placeholder { color: #3a506b !important; }

    .stButton > button {
        background: linear-gradient(135deg, #0d1a33, #111f3a) !important;
        color: #00e5ff !important;
        border: 1px solid rgba(0,229,255,0.4) !important; border-radius: 4px !important;
        font-family: 'Orbitron', 'Segoe UI', sans-serif !important;
        font-size: 0.8rem !important; letter-spacing: 0.05em !important;
        text-transform: uppercase !important; transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #0a2247, #132951) !important;
        border-color: #00e5ff !important; color: #fff !important;
        box-shadow: 0 0 20px rgba(0,229,255,0.35), inset 0 0 14px rgba(0,229,255,0.06) !important;
        transform: translateY(-1px) !important;
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #0d1a33, #111f3a) !important;
        color: #b44aff !important;
        border: 1px solid rgba(180,74,255,0.4) !important; border-radius: 4px !important;
        font-family: 'Orbitron', sans-serif !important; font-size: 0.78rem !important;
        letter-spacing: 0.05em !important;
    }
    .stDownloadButton > button:hover {
        border-color: #b44aff !important; color: #fff !important;
        box-shadow: 0 0 20px rgba(180,74,255,0.35), inset 0 0 14px rgba(180,74,255,0.06) !important;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 4px !important; background: transparent !important; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(15,26,46,0.7) !important;
        border: 1px solid rgba(0,229,255,0.1) !important; border-radius: 6px 6px 0 0 !important;
        color: #4a6380 !important;
        font-family: 'Orbitron', 'Segoe UI', sans-serif !important;
        font-size: 0.75rem !important; letter-spacing: 0.05em !important;
        text-transform: uppercase !important; padding: 0 18px !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #00e5ff !important; border-color: rgba(0,229,255,0.25) !important; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #0f1d35, #0b1526) !important;
        border: 1px solid rgba(0,229,255,0.4) !important; border-bottom: 2px solid #00e5ff !important;
        color: #00e5ff !important; font-weight: 700 !important;
        box-shadow: 0 -2px 16px rgba(0,229,255,0.1) !important;
    }

    .info-card {
        background: linear-gradient(135deg, rgba(15,26,46,0.85), rgba(11,20,36,0.9)) !important;
        padding: 24px !important; border-radius: 6px !important;
        border: 1px solid rgba(0,229,255,0.1) !important; border-left: 3px solid #00e5ff !important;
        box-shadow: 0 0 30px rgba(0,229,255,0.06), inset 0 1px 0 rgba(255,255,255,0.02) !important;
        margin-bottom: 24px !important;
    }

    [data-testid="stChatMessage"] {
        background: rgba(15,26,46,0.6) !important;
        border: 1px solid rgba(0,229,255,0.1) !important; border-radius: 6px !important;
    }
    [data-testid="stChatMessage"][data-testid*="assistant"] { border-left: 3px solid #b44aff !important; }
    [data-testid="stChatMessage"][data-testid*="user"] { border-left: 3px solid #00e5ff !important; }
    [data-testid="stChatInput"] textarea {
        background: #0a101f !important; color: #00e5ff !important;
        border: 1px solid rgba(0,229,255,0.3) !important;
        font-family: 'Consolas', monospace !important;
    }

    .stProgress > div > div { background: linear-gradient(90deg, #00e5ff, #b44aff, #ff2d95) !important; }
    .stProgress { background: rgba(255,255,255,0.04) !important; }
    hr, .stDivider { border-color: rgba(0,229,255,0.12) !important; }
    .stAlert { background: rgba(15,26,46,0.7) !important; border: 1px solid rgba(0,229,255,0.1) !important;
               color: #b8c9dd !important; }
    [data-testid="stInfo"] { border-left: 3px solid #00e5ff !important; }
    [data-testid="stSuccess"] { border-left: 3px solid #00ff88 !important; }
    [data-testid="stWarning"] { border-left: 3px solid #ffaa00 !important; }
    [data-testid="stError"] { border-left: 3px solid #ff2d95 !important; }
    .stSpinner > div { border-top-color: #00e5ff !important; }
</style>
""",
}

# ── Theme 2: Academic Classic ─────────────────────────────────

THEMES["academic"] = {
    "name": "📖 学术经典",
    "css": """
<style>
    .stApp { background: #f8f9fa; font-family: 'Segoe UI', 'Helvetica Neue', serif; }

    h1 { color: #1a3a5c !important; font-size: 2rem !important; font-weight: 700 !important;
         border-bottom: 2px solid #1a5276; padding-bottom: 0.4rem; }
    h2 { color: #1a5276 !important; font-size: 1.3rem !important; font-weight: 600 !important; }
    h3 { color: #2c3e50 !important; }
    h4, h5, h6 { color: #34495e !important; }
    p, div, li, span, label, .stMarkdown { color: #2c3e50 !important; }

    section[data-testid="stSidebar"] {
        background: #ffffff; border-right: 1px solid #e0e0e0;
    }
    section[data-testid="stSidebar"] h1 { color: #1a5276 !important; }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #2c3e50 !important; }
    section[data-testid="stSidebar"] label { color: #333 !important; }

    .stTextArea textarea, .stTextInput input {
        background-color: #fff !important; color: #333 !important;
        border: 1px solid #d1d5db !important; border-radius: 6px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #3498db !important; box-shadow: 0 0 0 3px rgba(52,152,219,0.15) !important;
    }

    .stButton > button {
        background: #3498db !important; color: #fff !important;
        border: none !important; border-radius: 6px !important; transition: all 0.3s !important;
    }
    .stButton > button:hover { background: #2980b9 !important; box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important; }

    .stDownloadButton > button {
        background: #1a5276 !important; color: #fff !important;
        border: none !important; border-radius: 6px !important;
    }
    .stDownloadButton > button:hover { background: #154360 !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px !important; }
    .stTabs [data-baseweb="tab"] {
        background: #e9ecef !important; border-radius: 6px 6px 0 0 !important;
        color: #6c757d !important; padding: 0 18px !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #3498db !important; }
    .stTabs [aria-selected="true"] {
        background: #fff !important; border-bottom: 3px solid #3498db !important;
        color: #1a5276 !important; font-weight: 600 !important;
    }

    .info-card {
        background: #fff !important; padding: 24px !important; border-radius: 10px !important;
        border-left: 5px solid #3498db !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important; margin-bottom: 24px !important;
    }

    [data-testid="stChatMessage"] {
        background: #fff !important; border: 1px solid #e0e0e0 !important; border-radius: 8px !important;
    }
    [data-testid="stChatMessage"][data-testid*="assistant"] { border-left: 4px solid #3498db !important; }
    [data-testid="stChatMessage"][data-testid*="user"] { border-left: 4px solid #2ecc71 !important; }
    [data-testid="stChatInput"] textarea {
        background: #fff !important; color: #333 !important;
        border: 1px solid #d1d5db !important;
    }

    .stProgress > div > div { background: #3498db !important; }
    .stProgress { background: #e9ecef !important; }
    hr, .stDivider { border-color: #e0e0e0 !important; }
    .stAlert { background: #fff !important; border: 1px solid #e0e0e0 !important; color: #333 !important; }
    [data-testid="stInfo"] { border-left: 4px solid #3498db !important; }
    [data-testid="stSuccess"] { border-left: 4px solid #27ae60 !important; }
    [data-testid="stWarning"] { border-left: 4px solid #f39c12 !important; }
    [data-testid="stError"] { border-left: 4px solid #e74c3c !important; }
    .stSpinner > div { border-top-color: #3498db !important; }
</style>
""",
}

# ── Theme 3: Dark Eye-Comfort ─────────────────────────────────

THEMES["eye-care"] = {
    "name": "🌙 暗夜护眼",
    "css": """
<style>
    .stApp {
        background: linear-gradient(180deg, #1a150e 0%, #100c06 100%);
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    }

    h1 { color: #ffb347 !important; font-size: 2rem !important; font-weight: 700 !important; }
    h2 { color: #ffcc80 !important; font-size: 1.3rem !important; font-weight: 600 !important; }
    h3 { color: #e6a817 !important; }
    h4, h5, h6 { color: #d4c5a9 !important; }
    p, div, li, span, label, .stMarkdown { color: #c4b998 !important; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1c1810, #141008);
        border-right: 1px solid rgba(255,179,71,0.1);
    }
    section[data-testid="stSidebar"] h1 { color: #ffb347 !important; }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #ffcc80 !important; }
    section[data-testid="stSidebar"] label { color: #c4b998 !important; }

    .stTextArea textarea, .stTextInput input {
        background-color: #1c1810 !important; color: #e6d5a8 !important;
        border: 1px solid rgba(255,179,71,0.25) !important; border-radius: 4px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #ffb347 !important;
        box-shadow: 0 0 10px rgba(255,179,71,0.2) !important;
    }

    .stButton > button {
        background: rgba(255,179,71,0.1) !important; color: #ffb347 !important;
        border: 1px solid rgba(255,179,71,0.35) !important; border-radius: 4px !important;
        transition: all 0.3s !important;
    }
    .stButton > button:hover {
        background: rgba(255,179,71,0.2) !important; border-color: #ffb347 !important;
        box-shadow: 0 0 16px rgba(255,179,71,0.3) !important; color: #fff !important;
    }

    .stDownloadButton > button {
        background: rgba(255,179,71,0.1) !important; color: #ffcc80 !important;
        border: 1px solid rgba(255,179,71,0.3) !important; border-radius: 4px !important;
    }
    .stDownloadButton > button:hover { border-color: #ffcc80 !important; color: #fff !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 4px !important; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(28,24,16,0.7) !important; border-radius: 6px 6px 0 0 !important;
        color: #8a7555 !important; border: 1px solid rgba(255,179,71,0.08) !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #ffb347 !important; }
    .stTabs [aria-selected="true"] {
        background: #1c1810 !important; border-bottom: 2px solid #ffb347 !important;
        color: #ffb347 !important; font-weight: 600 !important;
    }

    .info-card {
        background: rgba(28,24,16,0.8) !important; padding: 24px !important;
        border-radius: 6px !important; border-left: 3px solid #ffb347 !important;
        border: 1px solid rgba(255,179,71,0.1) !important; margin-bottom: 24px !important;
    }

    [data-testid="stChatMessage"] {
        background: rgba(28,24,16,0.6) !important;
        border: 1px solid rgba(255,179,71,0.1) !important; border-radius: 6px !important;
    }
    [data-testid="stChatMessage"][data-testid*="assistant"] { border-left: 3px solid #ffb347 !important; }
    [data-testid="stChatMessage"][data-testid*="user"] { border-left: 3px solid #e6a817 !important; }
    [data-testid="stChatInput"] textarea {
        background: #1c1810 !important; color: #e6d5a8 !important;
        border: 1px solid rgba(255,179,71,0.3) !important;
    }

    .stProgress > div > div { background: linear-gradient(90deg, #e6a817, #ffb347) !important; }
    .stProgress { background: rgba(255,179,71,0.05) !important; }
    hr, .stDivider { border-color: rgba(255,179,71,0.1) !important; }
    .stAlert { background: rgba(28,24,16,0.7) !important;
               border: 1px solid rgba(255,179,71,0.1) !important; color: #c4b998 !important; }
    [data-testid="stInfo"] { border-left: 3px solid #ffb347 !important; }
    [data-testid="stSuccess"] { border-left: 3px solid #7cb342 !important; }
    [data-testid="stWarning"] { border-left: 3px solid #ffb347 !important; }
    [data-testid="stError"] { border-left: 3px solid #e57373 !important; }
    .stSpinner > div { border-top-color: #ffb347 !important; }
</style>
""",
}

# ── Theme 4: Minimal White ─────────────────────────────────────

THEMES["minimal"] = {
    "name": "⬜ 极简素白",
    "css": """
<style>
    .stApp { background: #ffffff; font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; }

    h1 { color: #111 !important; font-size: 2rem !important; font-weight: 700 !important; }
    h2 { color: #333 !important; font-size: 1.3rem !important; font-weight: 600 !important; }
    h3 { color: #444 !important; }
    h4, h5, h6 { color: #555 !important; }
    p, div, li, span, label, .stMarkdown { color: #444 !important; }

    section[data-testid="stSidebar"] {
        background: #fafafa; border-right: 1px solid #eee;
    }
    section[data-testid="stSidebar"] h1 { color: #111 !important; }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #333 !important; }
    section[data-testid="stSidebar"] label { color: #444 !important; }

    .stTextArea textarea, .stTextInput input {
        background-color: #fff !important; color: #333 !important;
        border: 1px solid #e0e0e0 !important; border-radius: 2px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #999 !important; box-shadow: none !important;
    }

    .stButton > button {
        background: #fff !important; color: #333 !important;
        border: 1px solid #ccc !important; border-radius: 2px !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover { background: #f5f5f5 !important; border-color: #999 !important; }

    .stDownloadButton > button {
        background: #fafafa !important; color: #333 !important;
        border: 1px solid #ddd !important; border-radius: 2px !important;
    }
    .stDownloadButton > button:hover { background: #f0f0f0 !important; border-color: #999 !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 0 !important; border-bottom: 1px solid #e0e0e0 !important; }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; border: none !important; border-radius: 0 !important;
        color: #888 !important; padding: 0 20px !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #333 !important; }
    .stTabs [aria-selected="true"] {
        background: transparent !important; border-bottom: 2px solid #333 !important;
        color: #111 !important; font-weight: 600 !important;
    }

    .info-card {
        background: #fff !important; padding: 24px !important;
        border: 1px solid #eee !important; border-radius: 2px !important;
        margin-bottom: 24px !important;
    }

    [data-testid="stChatMessage"] {
        background: #fff !important; border: 1px solid #eee !important; border-radius: 4px !important;
    }
    [data-testid="stChatMessage"][data-testid*="assistant"] { border-left: 2px solid #888 !important; }
    [data-testid="stChatMessage"][data-testid*="user"] { border-left: 2px solid #ccc !important; }
    [data-testid="stChatInput"] textarea {
        background: #fff !important; color: #333 !important; border: 1px solid #e0e0e0 !important;
    }

    .stProgress > div > div { background: #999 !important; }
    .stProgress { background: #f0f0f0 !important; }
    hr, .stDivider { border-color: #eee !important; }
    .stAlert { background: #fafafa !important; border: 1px solid #eee !important; color: #444 !important; }
    [data-testid="stInfo"] { border-left: 2px solid #888 !important; }
    [data-testid="stSuccess"] { border-left: 2px solid #666 !important; }
    [data-testid="stWarning"] { border-left: 2px solid #999 !important; }
    [data-testid="stError"] { border-left: 2px solid #555 !important; }
    .stSpinner > div { border-top-color: #888 !important; }
</style>
""",
}

# ── Theme 5: Forest Green ──────────────────────────────────────

THEMES["forest"] = {
    "name": "🌿 森林幽绿",
    "css": """
<style>
    .stApp {
        background: linear-gradient(180deg, #0a1612 0%, #060f0c 100%);
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    }

    h1 { color: #00e676 !important; font-size: 2rem !important; font-weight: 700 !important;
         text-shadow: 0 0 12px rgba(0,230,118,0.3) !important; }
    h2 { color: #69f0ae !important; font-size: 1.3rem !important; font-weight: 600 !important; }
    h3 { color: #00e676 !important; }
    h4, h5, h6 { color: #a5d6a7 !important; }
    p, div, li, span, label, .stMarkdown { color: #a5b8a0 !important; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1e16, #08120d);
        border-right: 1px solid rgba(0,230,118,0.08);
    }
    section[data-testid="stSidebar"] h1 { color: #00e676 !important; }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #69f0ae !important; }
    section[data-testid="stSidebar"] label { color: #a5b8a0 !important; }

    .stTextArea textarea, .stTextInput input {
        background-color: #0c1c14 !important; color: #b8e6c0 !important;
        border: 1px solid rgba(0,230,118,0.2) !important; border-radius: 4px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #00e676 !important;
        box-shadow: 0 0 10px rgba(0,230,118,0.2) !important;
    }

    .stButton > button {
        background: rgba(0,230,118,0.08) !important; color: #00e676 !important;
        border: 1px solid rgba(0,230,118,0.3) !important; border-radius: 4px !important;
        transition: all 0.3s !important;
    }
    .stButton > button:hover {
        background: rgba(0,230,118,0.16) !important; border-color: #00e676 !important;
        box-shadow: 0 0 16px rgba(0,230,118,0.25) !important; color: #fff !important;
    }

    .stDownloadButton > button {
        background: rgba(0,230,118,0.08) !important; color: #69f0ae !important;
        border: 1px solid rgba(0,230,118,0.25) !important; border-radius: 4px !important;
    }
    .stDownloadButton > button:hover { border-color: #69f0ae !important; color: #fff !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 4px !important; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(14,30,22,0.7) !important; border-radius: 6px 6px 0 0 !important;
        color: #4a6b55 !important; border: 1px solid rgba(0,230,118,0.06) !important;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #00e676 !important; }
    .stTabs [aria-selected="true"] {
        background: #0e1e16 !important; border-bottom: 2px solid #00e676 !important;
        color: #00e676 !important; font-weight: 600 !important;
    }

    .info-card {
        background: rgba(14,30,22,0.8) !important; padding: 24px !important;
        border-radius: 6px !important; border-left: 3px solid #00e676 !important;
        border: 1px solid rgba(0,230,118,0.08) !important; margin-bottom: 24px !important;
    }

    [data-testid="stChatMessage"] {
        background: rgba(14,30,22,0.6) !important;
        border: 1px solid rgba(0,230,118,0.08) !important; border-radius: 6px !important;
    }
    [data-testid="stChatMessage"][data-testid*="assistant"] { border-left: 3px solid #69f0ae !important; }
    [data-testid="stChatMessage"][data-testid*="user"] { border-left: 3px solid #00e676 !important; }
    [data-testid="stChatInput"] textarea {
        background: #0c1c14 !important; color: #b8e6c0 !important;
        border: 1px solid rgba(0,230,118,0.25) !important;
    }

    .stProgress > div > div { background: linear-gradient(90deg, #00e676, #69f0ae) !important; }
    .stProgress { background: rgba(0,230,118,0.04) !important; }
    hr, .stDivider { border-color: rgba(0,230,118,0.1) !important; }
    .stAlert { background: rgba(14,30,22,0.7) !important;
               border: 1px solid rgba(0,230,118,0.08) !important; color: #a5b8a0 !important; }
    [data-testid="stInfo"] { border-left: 3px solid #00e676 !important; }
    [data-testid="stSuccess"] { border-left: 3px solid #69f0ae !important; }
    [data-testid="stWarning"] { border-left: 3px solid #cddc39 !important; }
    [data-testid="stError"] { border-left: 3px solid #ef5350 !important; }
    .stSpinner > div { border-top-color: #00e676 !important; }
</style>
""",
}

# ═══════════════════════════════════════════════════════════════
# Theme helpers
# ═══════════════════════════════════════════════════════════════

THEME_KEYS = list(THEMES.keys())
THEME_CHOICES = [THEMES[k]["name"] for k in THEME_KEYS]
THEME_KEY_MAP = {THEMES[k]["name"]: k for k in THEME_KEYS}  # display_name → key

# ── Widget-level overrides (selectbox / file-uploader) ────────
# These are applied after the theme CSS so they can use per-theme colors.

_WIDGET_OVERRIDES = {
    "sci-fi": """
<style>
    [data-baseweb="select"] [role="combobox"],
    [data-baseweb="select"] > div {
        background-color: #0a101f !important;
        color: #00e5ff !important;
        border: 1px solid rgba(0,229,255,0.25) !important;
        border-radius: 4px !important;
    }
    [data-baseweb="popover"] { background-color: #0d1a33 !important; border: 1px solid rgba(0,229,255,0.3) !important; }
    [data-baseweb="popover"] li, [data-baseweb="popover"] div { color: #b8c9dd !important; }
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] [aria-selected="true"] {
        background: rgba(0,229,255,0.12) !important; color: #00e5ff !important;
    }
    [data-testid="stFileUploader"] section {
        background: rgba(15,26,46,0.6) !important;
        border: 1px dashed rgba(0,229,255,0.2) !important; border-radius: 6px !important;
    }
    [data-testid="stFileUploader"] section:hover { border-color: rgba(0,229,255,0.4) !important; }
    [data-testid="stFileUploader"] p { color: #6b7d95 !important; }
    [data-testid="stFileUploader"] span { color: #00e5ff !important; }
    [data-testid="stFileUploader"] button {
        background: rgba(0,229,255,0.12) !important; color: #00e5ff !important;
        border: 1px solid rgba(0,229,255,0.3) !important; border-radius: 4px !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background: rgba(0,229,255,0.2) !important; border-color: #00e5ff !important;
    }
</style>
""",
    "academic": """
<style>
    [data-baseweb="select"] [role="combobox"],
    [data-baseweb="select"] > div {
        background-color: #fff !important; color: #333 !important;
        border: 1px solid #d1d5db !important; border-radius: 6px !important;
    }
    [data-baseweb="popover"] { background-color: #fff !important; border: 1px solid #ddd !important; }
    [data-baseweb="popover"] li, [data-baseweb="popover"] div { color: #333 !important; }
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] [aria-selected="true"] {
        background: rgba(52,152,219,0.1) !important; color: #1a5276 !important;
    }
    [data-testid="stFileUploader"] section {
        background: #f8f9fa !important;
        border: 1px dashed #ccc !important; border-radius: 8px !important;
    }
    [data-testid="stFileUploader"] section:hover { border-color: #3498db !important; }
    [data-testid="stFileUploader"] p { color: #888 !important; }
    [data-testid="stFileUploader"] span { color: #3498db !important; }
    [data-testid="stFileUploader"] button {
        background: #fff !important; color: #3498db !important;
        border: 1px solid #3498db !important; border-radius: 6px !important;
    }
    [data-testid="stFileUploader"] button:hover { background: #3498db !important; color: #fff !important; }
</style>
""",
    "eye-care": """
<style>
    [data-baseweb="select"] [role="combobox"],
    [data-baseweb="select"] > div {
        background-color: #1c1810 !important; color: #e6d5a8 !important;
        border: 1px solid rgba(255,179,71,0.25) !important; border-radius: 4px !important;
    }
    [data-baseweb="popover"] { background-color: #1c1810 !important; border: 1px solid rgba(255,179,71,0.3) !important; }
    [data-baseweb="popover"] li, [data-baseweb="popover"] div { color: #c4b998 !important; }
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] [aria-selected="true"] {
        background: rgba(255,179,71,0.12) !important; color: #ffb347 !important;
    }
    [data-testid="stFileUploader"] section {
        background: rgba(28,24,16,0.6) !important;
        border: 1px dashed rgba(255,179,71,0.2) !important; border-radius: 6px !important;
    }
    [data-testid="stFileUploader"] section:hover { border-color: rgba(255,179,71,0.4) !important; }
    [data-testid="stFileUploader"] p { color: #8a7555 !important; }
    [data-testid="stFileUploader"] span { color: #ffb347 !important; }
    [data-testid="stFileUploader"] button {
        background: rgba(255,179,71,0.12) !important; color: #ffb347 !important;
        border: 1px solid rgba(255,179,71,0.3) !important; border-radius: 4px !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background: rgba(255,179,71,0.2) !important; border-color: #ffb347 !important;
    }
</style>
""",
    "minimal": """
<style>
    [data-baseweb="select"] [role="combobox"],
    [data-baseweb="select"] > div {
        background-color: #fff !important; color: #333 !important;
        border: 1px solid #e0e0e0 !important; border-radius: 2px !important;
    }
    [data-baseweb="popover"] { background-color: #fff !important; border: 1px solid #eee !important; }
    [data-baseweb="popover"] li, [data-baseweb="popover"] div { color: #444 !important; }
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] [aria-selected="true"] {
        background: #f5f5f5 !important; color: #111 !important;
    }
    [data-testid="stFileUploader"] section {
        background: #fafafa !important;
        border: 1px dashed #ddd !important; border-radius: 4px !important;
    }
    [data-testid="stFileUploader"] section:hover { border-color: #999 !important; }
    [data-testid="stFileUploader"] p { color: #888 !important; }
    [data-testid="stFileUploader"] span { color: #555 !important; }
    [data-testid="stFileUploader"] button {
        background: #fff !important; color: #555 !important;
        border: 1px solid #ccc !important; border-radius: 2px !important;
    }
    [data-testid="stFileUploader"] button:hover { background: #f5f5f5 !important; border-color: #999 !important; }
</style>
""",
    "forest": """
<style>
    [data-baseweb="select"] [role="combobox"],
    [data-baseweb="select"] > div {
        background-color: #0c1c14 !important; color: #b8e6c0 !important;
        border: 1px solid rgba(0,230,118,0.2) !important; border-radius: 4px !important;
    }
    [data-baseweb="popover"] { background-color: #0e1e16 !important; border: 1px solid rgba(0,230,118,0.3) !important; }
    [data-baseweb="popover"] li, [data-baseweb="popover"] div { color: #a5b8a0 !important; }
    [data-baseweb="popover"] li:hover, [data-baseweb="popover"] [aria-selected="true"] {
        background: rgba(0,230,118,0.12) !important; color: #00e676 !important;
    }
    [data-testid="stFileUploader"] section {
        background: rgba(14,30,22,0.6) !important;
        border: 1px dashed rgba(0,230,118,0.2) !important; border-radius: 6px !important;
    }
    [data-testid="stFileUploader"] section:hover { border-color: rgba(0,230,118,0.4) !important; }
    [data-testid="stFileUploader"] p { color: #4a6b55 !important; }
    [data-testid="stFileUploader"] span { color: #00e676 !important; }
    [data-testid="stFileUploader"] button {
        background: rgba(0,230,118,0.12) !important; color: #00e676 !important;
        border: 1px solid rgba(0,230,118,0.3) !important; border-radius: 4px !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background: rgba(0,230,118,0.2) !important; border-color: #00e676 !important;
    }
</style>
""",
}


def inject_css(theme_name: str = "sci-fi"):
    """Inject CSS for the given theme. Falls back to sci-fi if unknown."""
    if theme_name not in THEMES:
        theme_name = "sci-fi"

    st.markdown(_BASE_CSS, unsafe_allow_html=True)
    st.markdown(THEMES[theme_name]["css"], unsafe_allow_html=True)
    st.markdown(_WIDGET_OVERRIDES.get(theme_name, _WIDGET_OVERRIDES["sci-fi"]), unsafe_allow_html=True)


def build_system_prompt(reader_level: str) -> str:
    """Build the default system instruction for a given reader level."""
    return DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(reader_level=reader_level)
