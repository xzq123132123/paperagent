import streamlit as st
import re  # <--- 新增这个，用于自动检测语言
import pdfplumber
import dashscope
import base64  # <--- 新增这个
from dashscope import Generation
from http import HTTPStatus
import os
import time
import io  # <--- 新增
import hashlib  # <--- 新增
from fpdf import FPDF  # <--- 新增
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

def generate_pdf_content(summary, chat_history):
    """生成支持中文的 PDF 二进制流"""
    # --- 关键：先注册中文字体 ---
    # 必须下载 SimHei.ttf 放在同级目录，或者使用系统路径
    import os
    font_path = "SimHei.ttf" # 优先找项目目录下的字体
    
    # 如果项目里没有，尝试找 Windows 系统字体
    if not os.path.exists(font_path):
        possible_paths = [
            r"C:\Windows\Fonts\simhei.ttf",
            r"C:\Windows\Fonts\msyh.ttc"
        ]
        for p in possible_paths:
            if os.path.exists(p):
                font_path = p
                break
    
    # 定义 PDF 类，在初始化时注册字体
    class PDF(FPDF):
        def __init__(self):
            super().__init__()
            self.font_registered = False
            # 尝试注册中文字体
            try:
                # 注册字体，这步是显示中文的关键
                self.add_font('SimHei', '', font_path)
                self.font_registered = True
            except Exception as e:
                # 如果找不到字体，回退到默认（中文会乱码，但不会报错崩溃）
                print(f"字体加载失败: {e}")
        
        def header(self):
            # 简单的页眉
            try:
                if self.font_registered:
                    self.set_font('SimHei', '', 10)
                else:
                    self.set_font('Arial', '', 10)
            except:
                self.set_font('Arial', '', 10)
            # 确保使用英文标题避免中文编码问题
            self.cell(0, 10, 'PaperAgent Pro - Study Notes', ln=True, align='R')
            self.ln(5)
    
    # 创建 PDF 实例
    pdf = PDF()
    
    # 添加页面
    pdf.add_page()
    
    # 设置默认字体
    if pdf.font_registered:
        pdf.set_font('SimHei', '', 12)
    else:
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, "Error: Chinese font not found. Please install SimHei.ttf", ln=True)

    # 1. 写入标题
    try:
        if pdf.font_registered:
            pdf.set_font('SimHei', '', 16)
            pdf.cell(0, 10, '论文研读笔记', ln=True, align='C')
        else:
            pdf.set_font('Arial', '', 16)
            pdf.cell(0, 10, 'Study Notes', ln=True, align='C')
        pdf.ln(10)
    except Exception as e:
        print(f"标题写入失败: {e}")
        pdf.set_font('Arial', '', 16)
        pdf.cell(0, 10, 'Study Notes', ln=True, align='C')
        pdf.ln(10)

    # 2. 写入时间
    try:
        if pdf.font_registered:
            pdf.set_font('SimHei', '', 10)
            pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        else:
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(5)
    except Exception as e:
        print(f"时间写入失败: {e}")
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(5)

    # 3. 写入概览
    if summary:
        try:
            if pdf.font_registered:
                pdf.set_font('SimHei', '', 14)
                pdf.cell(0, 10, '一、论文概览', ln=True)
                pdf.set_font('SimHei', '', 11)
            else:
                pdf.set_font('Arial', '', 14)
                pdf.cell(0, 10, '1. Paper Overview', ln=True)
                pdf.set_font('Arial', '', 11)
            # multi_cell 用于自动换行
            pdf.multi_cell(0, 8, summary)
            pdf.ln(10)
        except Exception as e:
            print(f"概览写入失败: {e}")
            pdf.set_font('Arial', '', 11)
            pdf.multi_cell(0, 8, summary)
            pdf.ln(10)

    # 4. 写入问答记录
    if chat_history:
        try:
            if pdf.font_registered:
                pdf.set_font('SimHei', '', 14)
                pdf.cell(0, 10, '二、重点问答记录', ln=True)
            else:
                pdf.set_font('Arial', '', 14)
                pdf.cell(0, 10, '2. Key Q&A Records', ln=True)
            pdf.ln(5)
            
            for msg in chat_history:
                role = "【AI 导师】" if msg['role'] == 'assistant' else "【我】"
                if not pdf.font_registered:
                    role = "[AI Tutor]" if msg['role'] == 'assistant' else "[Me]"
                content = msg['content']
                
                # 角色名
                try:
                    if pdf.font_registered:
                        pdf.set_font('SimHei', '', 11)
                    else:
                        pdf.set_font('Arial', '', 11)
                    pdf.cell(0, 8, role, ln=True)
                except Exception as e:
                    print(f"角色名写入失败: {e}")
                    pdf.set_font('Arial', '', 11)
                    pdf.cell(0, 8, "[User]" if msg['role'] != 'assistant' else "[AI]", ln=True)
                
                # 内容 (缩进一点)
                try:
                    pdf.set_x(15)
                    if pdf.font_registered:
                        pdf.set_font('SimHei', '', 10)
                    else:
                        pdf.set_font('Arial', '', 10)
                    pdf.multi_cell(0, 6, content)
                    pdf.ln(3)
                except Exception as e:
                    print(f"内容写入失败: {e}")
                    pdf.set_x(15)
                    pdf.set_font('Arial', '', 10)
                    pdf.multi_cell(0, 6, content[:500])  # 只写入部分内容避免崩溃
                    pdf.ln(3)
        except Exception as e:
            print(f"问答记录写入失败: {e}")

    # 返回二进制数据
    return bytes(pdf.output())

def get_file_id(uploaded_file) -> str:
    """
    用文件名 + 文件大小 + 内容hash 生成稳定指纹，确保换文件必定触发重解析
    """
    data = uploaded_file.getvalue()
    h = hashlib.md5(data).hexdigest()
    return f"{uploaded_file.name}_{len(data)}_{h}"

import base64
import streamlit.components.v1 as components
from PIL import Image
import pytesseract
import pdf2image

def display_pdf(uploaded_file, height=800):
    """
    ✅ 终极方案：pdf.js 渲染到 canvas（不依赖浏览器 PDF 插件，Edge 不会拦）
    """
    if uploaded_file is None:
        return

    b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

    html = f"""
    <div style="display:flex; gap:10px; align-items:center; margin-bottom:8px;">
      <button id="prev">⬅️ Prev</button>
      <span>Page: <span id="page_num"></span> / <span id="page_count"></span></span>
      <button id="next">Next ➡️</button>
    </div>
    <canvas id="the-canvas" style="width:100%; border:1px solid #ddd; border-radius:10px;"></canvas>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
      const b64 = "{b64}";
      const raw = atob(b64);
      const uint8Array = new Uint8Array(raw.length);
      for (let i = 0; i < raw.length; i++) uint8Array[i] = raw.charCodeAt(i);

      const pdfjsLib = window['pdfjs-dist/build/pdf'];
      pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

      let pdfDoc = null, pageNum = 1, pageRendering = false, pageNumPending = null;
      const canvas = document.getElementById('the-canvas');
      const ctx = canvas.getContext('2d');

      function renderPage(num) {{
        pageRendering = true;
        pdfDoc.getPage(num).then(function(page) {{
          const viewport = page.getViewport({{ scale: 1.5 }});
          canvas.height = viewport.height;
          canvas.width = viewport.width;

          const renderContext = {{ canvasContext: ctx, viewport: viewport }};
          const renderTask = page.render(renderContext);

          renderTask.promise.then(function() {{
            pageRendering = false;
            document.getElementById('page_num').textContent = pageNum;

            if (pageNumPending !== null) {{
              renderPage(pageNumPending);
              pageNumPending = null;
            }}
          }});
        }});
      }}

      function queueRenderPage(num) {{
        if (pageRendering) {{
          pageNumPending = num;
        }} else {{
          renderPage(num);
        }}
      }}

      document.getElementById('prev').addEventListener('click', function() {{
        if (pageNum <= 1) return;
        pageNum--;
        queueRenderPage(pageNum);
      }});

      document.getElementById('next').addEventListener('click', function() {{
        if (pageNum >= pdfDoc.numPages) return;
        pageNum++;
        queueRenderPage(pageNum);
      }});

      pdfjsLib.getDocument({{ data: uint8Array }}).promise.then(function(pdfDoc_) {{
        pdfDoc = pdfDoc_;
        document.getElementById('page_count').textContent = pdfDoc.numPages;
        document.getElementById('page_num').textContent = pageNum;
        renderPage(pageNum);
      }});
    </script>
    """

    components.html(html, height=height, scrolling=True)

def display_pdf_selectable(uploaded_file, height=700):
    """
    ✅ 可复制版本：使用 iframe 显示 PDF（支持文本选择和复制）
    """
    if uploaded_file is None:
        return

    base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

    pdf_iframe = f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}#toolbar=1&navpanes=0"
        width="100%"
        height="{height}"
        style="border:1px solid #ddd; border-radius:10px;"
    ></iframe>
    """
    st.markdown(pdf_iframe, unsafe_allow_html=True)

def render_pdf_page_to_image(uploaded_file, page_num, scale=2.0):
    """
    将PDF指定页面渲染为图像
    """
    try:
        # 将上传的文件保存为临时文件
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # 使用pdf2image转换PDF页面为图像
        images = pdf2image.convert_from_path(
            "temp.pdf",
            first_page=page_num + 1,  # pdf2image使用1-based索引
            last_page=page_num + 1,
            dpi=int(150 * scale),  # 根据scale调整DPI
            fmt="PNG"
        )
        
        if images:
            return images[0]
        return None
    except Exception as e:
        st.error(f"PDF渲染失败: {e}")
        return None

def ocr_image(image):
    """
    对图像进行OCR识别，提取文本
    """
    try:
        # 使用pytesseract进行OCR
        text = pytesseract.image_to_string(image, lang="eng+chi_sim")
        return text
    except Exception as e:
        st.error(f"OCR失败: {e}")
        return ""


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

# -------- 1) 清洗 Mermaid：去围栏、去杂话、只保留主图 --------
def wrap_text(text, max_len=12):
    """自动为长文本添加换行符"""
    if not text:
        return text
    # 按最大长度分割文本
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

def clean_mermaid(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

    # A. 把 ```mermaid ... ``` 围栏剥掉（LLM最常见“夹带”）
    import re
    m = re.search(r"```(?:mermaid)?\s*(.*?)```", text, flags=re.S)
    if m:
        text = m.group(1).strip()

    # B. 从第一个 Mermaid 图类型关键字开始截断，去掉前后说明
    m2 = re.search(
        r"(?s)\b(flowchart|graph|sequenceDiagram|stateDiagram|classDiagram|erDiagram|journey|gantt)\b.*",
        text
    )
    if m2:
        text = m2.group(0).strip()

    # C. 常见隐藏字符清理（有时会导致语法问题）
    text = text.replace("\u200b", "").replace("\ufeff", "")  # 零宽字符/BOM

    # D. 处理长文本节点，添加换行符
    # 查找所有节点定义：ID["文本"]
    def replace_node(match):
        id_part = match.group(1)
        text_part = match.group(2)
        # 检查是否已经包含换行符
        if "<br/>" not in text_part:
            # 如果没有换行符，自动添加
            wrapped_text = wrap_text(text_part)
            return f'{id_part}["{wrapped_text}"]'
        return match.group(0)
    
    # 匹配节点定义：ID["文本"]
    text = re.sub(r'(\w+)\["([^"]+)"\]', replace_node, text)

    return text


# -------- 2) Mermaid 渲染（纯HTML注入，兼容 mermaid@10）--------
def render_mermaid(mermaid_code: str, height: int = 620):
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

    import streamlit.components.v1 as components
    components.html(html, height=height, scrolling=True)


# -------- 3) 让 LLM “只输出纯 Mermaid”，避免语法炸点 --------
def build_mermaid_prompt(full_text: str) -> str:
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

def generate_mindmap_code(text):
    """让 AI 生成 Mermaid 思维导图代码 (稳定版)"""
    prompt = build_mermaid_prompt(text[:8000])  # 建议截断，避免太长
    return call_qwen(prompt)

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
    st.info("💡 **功能导航**：\n1. **概览**：使用滑窗+归纳策略生成深度全文分析，包含详细摘要和BibTeX引用\n2. **阅读**：左侧嵌入PDF原文（保留排版），右侧AI导师实时问答，智能知识库自动沉淀关键信息\n3. **润色**：智能翻译（中⇌英）、学术润色、语法纠错，支持PDF原文对照")

    # --- 新增：导出功能 (支持 Markdown 和 PDF) ---
    st.markdown("---")
    st.subheader("💾 成果导出")
    
    # 检查是否有内容可导出
    has_history = "chat_history" in st.session_state and st.session_state.chat_history
    has_summary = "paper_summary" in st.session_state and st.session_state.paper_summary
    
    if has_history or has_summary:
        # 1. Markdown 导出 (保留原有功能)
        md_content = f"# 论文研读笔记\n日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        if has_summary:
            md_content += f"## 1. 论文概览\n{st.session_state.paper_summary}\n\n"
        if has_history:
            md_content += "## 2. 重点问答记录\n"
            for msg in st.session_state.chat_history:
                role = "AI 导师" if msg['role'] == 'assistant' else "我"
                md_content += f"**{role}**: {msg['content']}\n\n"
        
        col_md, col_pdf = st.columns(2)
        
        with col_md:
            st.download_button(
                label="⬇️ Markdown",
                data=md_content,
                file_name="study_notes.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_notes_md"
            )

        # 2. PDF 导出 (新增功能)
        with col_pdf:
            # 只有点击时才生成PDF，节省资源
            if st.button("⬇️ PDF", key="btn_gen_pdf", use_container_width=True):
                with st.spinner("正在生成 PDF..."):
                    pdf_data = generate_pdf_content(
                        st.session_state.paper_summary,
                        st.session_state.chat_history
                    )
                    # 由于 st.button 点击后会刷新，这里需要利用 session_state 或者直接立即显示下载链接
                    # 但为了简化交互，我们直接在这里显示一个下载按钮（嵌套逻辑在Streamlit中虽然不推荐但可用，或者使用回调）
                    # 最好的方式是把 PDF 生成逻辑封装，直接用 download_button 调用函数(但fpdf生成较慢，会卡顿)
                    # 这里采用“生成后显示下载链接”的方式：
                    st.session_state.tmp_pdf_data = pdf_data

            # 如果已经生成了 PDF 数据，显示下载按钮
            if "tmp_pdf_data" in st.session_state:
                st.download_button(
                    label="点击保存 PDF",
                    data=st.session_state.tmp_pdf_data,
                    file_name="study_notes.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_download_pdf" # 唯一的 key
                )
    else:
        st.caption("暂无笔记内容可导出")


# --- 主界面逻辑 ---
st.title("📄 PaperAgent Pro: 多模态论文助读")

# 全局状态管理
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "raw_text" not in st.session_state: st.session_state.raw_text = ""
if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
if "paper_summary" not in st.session_state: st.session_state.paper_summary = None 
if "current_file_id" not in st.session_state: st.session_state.current_file_id = None

# 文件上传
uploaded_file = st.file_uploader("📂 上传论文 (PDF)", type="pdf")

if uploaded_file:
    new_file_id = get_file_id(uploaded_file)

    # ✅ 文件变了：清空旧状态，强制重解析
    if st.session_state.current_file_id != new_file_id:
        st.session_state.current_file_id = new_file_id

        # 清空与论文相关的所有缓存/结果
        st.session_state.raw_text = ""
        st.session_state.paper_summary = None
        st.session_state.analysis_result = None
        st.session_state.chat_history = []
        st.session_state.polished_result = ""  # 可选：清空润色结果

    # ✅ 需要解析时再解析
    if st.session_state.raw_text == "":
        with st.spinner("正在解析 PDF 全文..."):
            st.session_state.raw_text = extract_text_from_pdf(uploaded_file)
            st.success("解析成功！")

if st.session_state.raw_text:
    
    # 将 .info-card 应用于核心信息卡（原代码此处没有使用 class，现在加上以适配新样式）
    tab0, tab1, tab2 = st.tabs(["🏠 智能概览", "📖 深度阅读", "✍️ 学术润色"])

    # === 功能 0: 智能概览 (含思维导图) ===
    with tab0:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.subheader("📑 论文核心信息卡")

        # 使用列布局放置两个大按钮
        c_act1, c_act2 = st.columns([1, 1])
        
        with c_act1:
            if st.button("🚀 生成深度概览 (Text)", use_container_width=True):
                with st.spinner("AI 正在使用滑窗策略阅读全篇论文..."):
                    summary = generate_map_reduce_summary(st.session_state.raw_text)
                    st.session_state.paper_summary = summary
                    
                    # 额外生成 BibTeX
                    bib_prompt = f"请根据论文前2000字，直接生成 BibTeX 格式。\n内容：{st.session_state.raw_text[:2000]}"
                    bib_res = call_qwen(bib_prompt)
                    if bib_res:
                        st.session_state.paper_summary += f"\n\n## BibTeX\n```bibtex\n{bib_res}\n```"

        with c_act2:
            if st.button("🗺️ 生成逻辑导图 (Graph)", use_container_width=True):
                with st.spinner("AI 正在梳理逻辑结构..."):
                    if not st.session_state.raw_text:
                        st.warning("请先上传并解析PDF")
                    else:
                        raw_code = generate_mindmap_code(st.session_state.raw_text)
                        clean_code = clean_mermaid(raw_code)
                        
                        # 保存结果到会话状态
                        st.session_state.mindmap_raw = raw_code
                        st.session_state.mindmap_code = clean_code

        st.divider()

        # 展示区
        # 1. 展示导图
        if "mindmap_code" in st.session_state and st.session_state.mindmap_code:
            st.markdown("### 🧠 逻辑结构导图")
            
            # ✅ 渲染
            try:
                render_mermaid(st.session_state.mindmap_code, height=650)
            except Exception as e:
                st.error(f"Mermaid 渲染失败：{e}")
            st.divider()

        # 2. 展示文字概览 (如果已生成)
        if st.session_state.paper_summary:
            st.markdown("### 📝 深度概览")
            st.markdown(st.session_state.paper_summary)
            st.info("💡 提示：你可以直接复制上方的 BibTeX 用于论文写作。")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # === 功能 1: 深度阅读 (精简版) ===
    with tab1:
        # 布局比例：左侧信息区 (55%)，右侧交互区 (45%)
        col1, col2 = st.columns([5.5, 4.5])
        
        # --- 左侧：多功能信息面板 ---
        with col1:
            # 修改点：只保留两个 Tab，删除了“解析文本”
            left_tab1, left_tab2 = st.tabs(["📄 PDF 原文", "🧠 知识库 (术语/数据)"])
            
            # Panel A: PDF 原文
            with left_tab1:
                # 添加下载按钮作为兜底
                st.download_button(
                    "📥 下载 PDF",
                    data=uploaded_file.getvalue(),
                    file_name=uploaded_file.name,
                    mime="application/pdf",
                    key="download_pdf_tab1"
                )
                display_pdf(uploaded_file)
            
            # Panel B: 知识库 (自动汇集提取出的信息)
            with left_tab2:
                st.markdown('<div class="info-card">', unsafe_allow_html=True)
                has_content = False
                
                # 1. 展示概览
                if st.session_state.paper_summary:
                    st.markdown("### 📑 论文概览")
                    st.markdown(st.session_state.paper_summary)
                    st.divider()
                    has_content = True
                
                # 2. 展示术语表
                if st.session_state.analysis_result:
                    st.markdown("### 📚 核心术语表")
                    st.markdown(st.session_state.analysis_result)
                    st.divider()
                    has_content = True
                
                # 3. 提示信息
                if not has_content:
                    st.info("👈 这里是智能知识库。\n\n当你在右侧点击 **'提取核心术语'** 或在概览页生成 **'摘要'** 后，AI 提炼的干货会自动沉淀在这里，方便你随时查阅，无需翻找聊天记录。")
                
                st.markdown('</div>', unsafe_allow_html=True)

        # --- 右侧：AI 导师交互区 ---
        with col2:
            st.subheader("💬 AI 导师")
            
            # --- 工具栏 ---
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
                            st.rerun()

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
                        st.session_state.chat_history.append({'role': 'assistant', 'content': f"📊 **实验数据提取结果**：\n\n{res_data}"})
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

            # --- 聊天区域 ---
            chat_container = st.container(height=600)
            with chat_container:
                for msg in st.session_state.chat_history:
                    st.chat_message(msg['role']).write(msg['content'])

            # 输入框
            if user_input := st.chat_input("针对论文提问..."):
                with chat_container:
                    st.chat_message("user").write(user_input)
                st.session_state.chat_history.append({'role': 'user', 'content': user_input})

                context = f"基于论文内容：\n{st.session_state.raw_text}\n\n用户问题：{user_input}"
                
                with chat_container:
                    with st.chat_message("assistant"):
                        with st.spinner("思考中..."):
                            response = call_qwen(context, history=st.session_state.chat_history[:-1])
                            if response:
                                st.write(response)
                                st.session_state.chat_history.append({'role': 'assistant', 'content': response})

    # === 功能 2: 沉浸式翻译工作台 (PDF 原文对照版) ===
    with tab2:
        # 初始化状态
        if "task_type" not in st.session_state:
            st.session_state.task_type = "🔁 智能翻译 (中⇌英)"
        if "target_input" not in st.session_state:
            st.session_state.target_input = ""
        if "polished_result" not in st.session_state:
            st.session_state.polished_result = ""
        
        # 1. 顶部：功能控制条
        st.markdown('<div class="info-card" style="padding: 10px 20px; margin-bottom: 20px;">', unsafe_allow_html=True)
        c_mode, c_src, c_act = st.columns([5, 3, 2])
        
        with c_mode:
            task_type = st.radio(
                "🎯 任务模式",
                ("🔁 智能翻译 (中⇌英)", "✨ 学术润色", "🔴 语法纠错"),
                horizontal=True,
                label_visibility="collapsed",
                key="task_type"
            )
        
        with c_src:
            # 开关：决定左侧显示 PDF 还是 空白输入框
            # 默认为 True (显示 PDF)
            source_mode = st.toggle("📖 显示论文 PDF 原件", value=True if uploaded_file else False)
        
        
        st.markdown('</div>', unsafe_allow_html=True)

        # 2. 主工作区：左右分栏
        col_left, col_right = st.columns([1, 1])

        # --- 左侧：原文参考区 (Reference) ---
        with col_left:
            # 如果开关开启 且 文件存在，则显示 PDF
            if source_mode and uploaded_file:
                st.markdown("**📖 论文原文 (保留排版，请直接划词复制)**")
                # 添加下载按钮作为兜底
                st.download_button(
                    "📥 下载 PDF",
                    data=uploaded_file.getvalue(),
                    file_name=uploaded_file.name,
                    mime="application/pdf",
                    key="download_pdf_tab2"
                )
                # 使用可复制版本的PDF显示
                display_pdf_selectable(uploaded_file, height=700)
                
                # 添加翻页控制
                if "page_num" not in st.session_state:
                    st.session_state.page_num = 0  # 0-based
                
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    if st.button("Prev Page"):
                        st.session_state.page_num = max(0, st.session_state.page_num - 1)
                with c2:
                    if st.button("Next Page"):
                        st.session_state.page_num = st.session_state.page_num + 1
                
                with c3:
                    st.write(f"当前页: {st.session_state.page_num + 1}")
                
                # 添加OCR功能
                if st.button("🔎 OCR 当前页（可复制）"):
                    with st.spinner("正在 OCR..."):
                        img = render_pdf_page_to_image(uploaded_file, st.session_state.page_num, scale=2.0)
                        if img:
                            text = ocr_image(img)
                            st.session_state.input_clip = text  # ✅ 自动填入“待处理片段”
                            st.success("OCR 完成：已自动填入待处理片段，可直接点击“立即执行”翻译。")
                        else:
                            st.error("OCR 失败：无法渲染PDF页面。")
                
            else:
                # 否则显示自由粘贴区
                st.markdown("**📄 自由粘贴区 (无 PDF 时使用)**")
                custom_text = st.text_area(
                    "Custom Text",
                    height=700,
                    placeholder="在此粘贴大段原文作为参考...",
                    label_visibility="collapsed"
                )

        # --- 右侧：翻译工作区 (Workbench) ---
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
                    placeholder="💡 操作指南：\n1. 从左侧复制一段文字\n2. 粘贴到这里\n3. 点击上方“🚀 立即执行”",
                    label_visibility="collapsed"
                )
                submitted = st.form_submit_button("🚀 立即执行")

            st.markdown("**📝 AI 结果**")
            st.text_area(
                "Result",
                value=st.session_state.get("polished_result", ""),
                height=420,
                label_visibility="collapsed"
            )

        # --- 逻辑处理（点一次就走） ---
        if submitted:
            target_input = st.session_state.input_clip.strip()
            if not target_input:
                st.warning("请先粘贴待处理片段")
            else:
                prompt_task = ""
                system_role = "你是一位资深的 Nature/Science 期刊审稿人。"

                if "智能翻译" in task_type:
                    contains_chinese = bool(re.search(r'[\u4e00-\u9fa5]', target_input))
                    prompt_task = (
                        f"请将以下中文翻译成**地道的学术英文 (SCI风格)**：\n\n{target_input}"
                        if contains_chinese else
                        f"请将以下英文翻译成**通俗流畅的学术中文**：\n\n{target_input}"
                    )
                elif "学术润色" in task_type:
                    prompt_task = f"请润色以下段落，提升词汇高级感和语法准确性：\n\n{target_input}"
                else:
                    prompt_task = f"请找出以下段落的语法错误并给出修改建议：\n\n{target_input}"

                with st.spinner("AI 正在处理..."):
                    st.session_state.polished_result = call_qwen(prompt_task, system_instruction=system_role)

else:
    st.info("👋 请在左侧上传 PDF 开始体验 PaperAgent Pro！")
