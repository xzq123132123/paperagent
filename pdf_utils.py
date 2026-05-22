"""PDF text extraction, rendering, export, and file fingerprinting."""

import os
import io
import base64
import hashlib
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
import pdfplumber
from fpdf import FPDF


@st.cache_data
def extract_text_from_pdf(uploaded_file):
    text = ""
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"PDF 读取失败: {e}")
        return None


def get_file_id(uploaded_file) -> str:
    """Generate a stable fingerprint from filename + size + content hash."""
    data = uploaded_file.getvalue()
    h = hashlib.md5(data).hexdigest()
    return f"{uploaded_file.name}_{len(data)}_{h}"


# ── PDF rendering ──────────────────────────────────────────────

def display_pdf(uploaded_file, height=800):
    """Render PDF via pdf.js onto a canvas (no browser PDF plugin needed)."""
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
    """Render PDF via iframe (supports text selection and copy)."""
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


# ── PDF export ─────────────────────────────────────────────────

def generate_pdf_content(summary, chat_history):
    """Generate a Chinese-supporting PDF binary stream."""

    font_path = "SimHei.ttf"
    if not os.path.exists(font_path):
        for p in [r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc"]:
            if os.path.exists(p):
                font_path = p
                break

    class PDF(FPDF):
        def __init__(self):
            super().__init__()
            self.font_registered = False
            try:
                self.add_font("SimHei", "", font_path)
                self.font_registered = True
            except Exception:
                pass

        def header(self):
            try:
                if self.font_registered:
                    self.set_font("SimHei", "", 10)
                else:
                    self.set_font("Arial", "", 10)
            except Exception:
                self.set_font("Arial", "", 10)
            self.cell(0, 10, "PaperAgent Pro - Study Notes", ln=True, align="R")
            self.ln(5)

    pdf = PDF()
    pdf.add_page()

    if pdf.font_registered:
        pdf.set_font("SimHei", "", 12)
    else:
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "Error: Chinese font not found. Please install SimHei.ttf", ln=True)

    # Title
    try:
        if pdf.font_registered:
            pdf.set_font("SimHei", "", 16)
            pdf.cell(0, 10, "论文研读笔记", ln=True, align="C")
        else:
            pdf.set_font("Arial", "", 16)
            pdf.cell(0, 10, "Study Notes", ln=True, align="C")
        pdf.ln(10)
    except Exception:
        pdf.set_font("Arial", "", 16)
        pdf.cell(0, 10, "Study Notes", ln=True, align="C")
        pdf.ln(10)

    # Date
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        if pdf.font_registered:
            pdf.set_font("SimHei", "", 10)
        else:
            pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"Date: {date_str}", ln=True)
        pdf.ln(5)
    except Exception:
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"Date: {date_str}", ln=True)
        pdf.ln(5)

    # Summary
    if summary:
        try:
            if pdf.font_registered:
                pdf.set_font("SimHei", "", 14)
                pdf.cell(0, 10, "一、论文概览", ln=True)
                pdf.set_font("SimHei", "", 11)
            else:
                pdf.set_font("Arial", "", 14)
                pdf.cell(0, 10, "1. Paper Overview", ln=True)
                pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, summary)
            pdf.ln(10)
        except Exception:
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, summary)
            pdf.ln(10)

    # Chat history
    if chat_history:
        try:
            if pdf.font_registered:
                pdf.set_font("SimHei", "", 14)
                pdf.cell(0, 10, "二、重点问答记录", ln=True)
            else:
                pdf.set_font("Arial", "", 14)
                pdf.cell(0, 10, "2. Key Q&A Records", ln=True)
            pdf.ln(5)

            for msg in chat_history:
                role = "【AI 导师】" if msg["role"] == "assistant" else "【我】"
                if not pdf.font_registered:
                    role = "[AI Tutor]" if msg["role"] == "assistant" else "[Me]"
                content = msg["content"]

                try:
                    if pdf.font_registered:
                        pdf.set_font("SimHei", "", 11)
                    else:
                        pdf.set_font("Arial", "", 11)
                    pdf.cell(0, 8, role, ln=True)
                except Exception:
                    pdf.set_font("Arial", "", 11)
                    pdf.cell(0, 8, "[User]" if msg["role"] != "assistant" else "[AI]", ln=True)

                try:
                    pdf.set_x(15)
                    if pdf.font_registered:
                        pdf.set_font("SimHei", "", 10)
                    else:
                        pdf.set_font("Arial", "", 10)
                    pdf.multi_cell(0, 6, content)
                    pdf.ln(3)
                except Exception:
                    pdf.set_x(15)
                    pdf.set_font("Arial", "", 10)
                    pdf.multi_cell(0, 6, content[:500])
                    pdf.ln(3)
        except Exception:
            pass

    return bytes(pdf.output())
