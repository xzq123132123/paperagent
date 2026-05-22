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
    """Single-page fit-to-height PDF reader via pdf.js.

    Scales each page to fully fit the container height without clipping.
    Navigation buttons switch pages; no vertical scrollbar inside the viewer.
    """
    if uploaded_file is None:
        return

    b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

    html = f"""
    <style>
      #pdf-reader-outer {{
        display: flex; flex-direction: column;
        width: 100%; height: {height}px;
        background: #0d1117; border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.08);
        overflow: hidden;
      }}
      #pdf-reader-nav {{
        display: flex; align-items: center; justify-content: center;
        gap: 16px; padding: 10px 16px;
        background: rgba(255,255,255,0.03);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        flex-shrink: 0;
      }}
      #pdf-reader-nav button {{
        background: rgba(255,255,255,0.08); color: #c8d6e5;
        border: 1px solid rgba(255,255,255,0.12); border-radius: 6px;
        padding: 6px 18px; cursor: pointer; font-size: 14px;
        transition: all 0.2s;
      }}
      #pdf-reader-nav button:hover {{
        background: rgba(255,255,255,0.16); color: #fff;
      }}
      #pdf-reader-nav button:disabled {{
        opacity: 0.35; cursor: default;
      }}
      #pdf-reader-nav span {{
        color: #8b949e; font-size: 14px; min-width: 100px; text-align: center;
      }}
      #pdf-reader-stage {{
        flex: 1; display: flex; align-items: center; justify-content: center;
        overflow: hidden; position: relative;
      }}
      #pdf-canvas-wrap {{
        position: relative;
        box-shadow: 0 2px 20px rgba(0,0,0,0.5); border-radius: 2px;
      }}
      #pdf-canvas-wrap canvas {{ display: block; }}
      #pdf-text-layer {{
        position: absolute; top: 0; left: 0; overflow: hidden;
        opacity: 0.2; line-height: 1.0;
        pointer-events: auto; user-select: text; cursor: text;
      }}
      #pdf-text-layer span {{
        color: transparent;
        position: absolute; white-space: pre;
        transform-origin: 0% 0%;
      }}
      #pdf-text-layer span::selection {{
        background: rgba(0,229,255,0.35); color: transparent;
      }}
    </style>

    <div id="pdf-reader-outer">
      <div id="pdf-reader-nav">
        <button id="prev-btn">◀ 上一页</button>
        <span><strong id="page-num">1</strong> / <span id="page-count">?</span></span>
        <button id="next-btn">下一页 ▶</button>
        <button id="copy-btn" style="margin-left:12px;">📋 复制本页文字</button>
      </div>
      <div id="pdf-reader-stage">
        <div id="pdf-canvas-wrap">
          <canvas id="pdf-canvas"></canvas>
          <div id="pdf-text-layer"></div>
        </div>
      </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
    (function() {{
      const b64 = "{b64}";
      const raw = atob(b64);
      const uint8Array = new Uint8Array(raw.length);
      for (let i = 0; i < raw.length; i++) uint8Array[i] = raw.charCodeAt(i);

      const pdfjsLib = window['pdfjs-dist/build/pdf'];
      pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

      let pdfDoc = null, pageNum = 1, pageRendering = false, pageNumPending = null;
      const canvas = document.getElementById('pdf-canvas');
      const ctx = canvas.getContext('2d');
      const stage = document.getElementById('pdf-reader-stage');
      const wrap = document.getElementById('pdf-canvas-wrap');
      const textLayerDiv = document.getElementById('pdf-text-layer');
      const btnPrev = document.getElementById('prev-btn');
      const btnNext = document.getElementById('next-btn');
      const btnCopy = document.getElementById('copy-btn');

      // Copy current page text to clipboard
      let currentPageText = '';
      btnCopy.addEventListener('click', async function() {{
        if (!currentPageText) {{
          btnCopy.textContent = '⚠ 无文字';
          setTimeout(() => {{ btnCopy.textContent = '📋 复制本页文字'; }}, 2000);
          return;
        }}
        try {{
          await navigator.clipboard.writeText(currentPageText);
          btnCopy.textContent = '✅ 已复制!';
          setTimeout(() => {{ btnCopy.textContent = '📋 复制本页文字'; }}, 2000);
        }} catch(e) {{
          btnCopy.textContent = '❌ 复制失败';
          setTimeout(() => {{ btnCopy.textContent = '📋 复制本页文字'; }}, 2000);
        }}
      }});

      function renderPage(num) {{
        pageRendering = true;
        textLayerDiv.innerHTML = '';
        currentPageText = '';

        pdfDoc.getPage(num).then(function(page) {{
          const vp = page.getViewport({{ scale: 1 }});
          const pw = vp.width, ph = vp.height;
          const cw = stage.clientWidth, ch = stage.clientHeight;

          const pixelRatio = window.devicePixelRatio || 2;
          const scale = Math.min(
            (cw - 24) / pw,
            (ch - 16) / ph
          ) * pixelRatio;

          const viewport = page.getViewport({{ scale: scale }});
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          canvas.style.width = Math.round(viewport.width / pixelRatio) + 'px';
          canvas.style.height = Math.round(viewport.height / pixelRatio) + 'px';

          const displayW = Math.round(viewport.width / pixelRatio);
          const displayH = Math.round(viewport.height / pixelRatio);
          wrap.style.width = displayW + 'px';
          wrap.style.height = displayH + 'px';
          textLayerDiv.style.width = displayW + 'px';
          textLayerDiv.style.height = displayH + 'px';

          // Render canvas at high-DPI
          const renderTask = page.render({{ canvasContext: ctx, viewport: viewport }});

          // Text layer at display (1x) scale so positions match CSS layout
          const textViewport = page.getViewport({{ scale: scale / pixelRatio }});

          // Render selectable text layer + store text for copy button
          page.getTextContent().then(function(textContent) {{
            pdfjsLib.renderTextLayer({{
              textContent: textContent,
              container: textLayerDiv,
              viewport: textViewport,
              textDivs: [],
            }});
            // Store plain text for copy button
            currentPageText = textContent.items
              .map(function(it) {{ return it.str; }})
              .join(' ')
              .replace(/\\s+/g, ' ');
          }});

          renderTask.promise.then(function() {{
            pageRendering = false;
            document.getElementById('page-num').textContent = pageNum;
            btnPrev.disabled = (pageNum <= 1);
            btnNext.disabled = (pageNum >= pdfDoc.numPages);
            if (pageNumPending !== null) {{
              renderPage(pageNumPending);
              pageNumPending = null;
            }}
          }});
        }});
      }}

      function queueRenderPage(num) {{
        if (pageRendering) {{ pageNumPending = num; }}
        else {{ renderPage(num); }}
      }}

      btnPrev.addEventListener('click', function() {{
        if (pageNum <= 1) return;
        pageNum--;
        queueRenderPage(pageNum);
      }});
      btnNext.addEventListener('click', function() {{
        if (pageNum >= pdfDoc.numPages) return;
        pageNum++;
        queueRenderPage(pageNum);
      }});

      // Keyboard navigation
      document.addEventListener('keydown', function(e) {{
        if (e.key === 'ArrowLeft') {{ btnPrev.click(); }}
        if (e.key === 'ArrowRight') {{ btnNext.click(); }}
      }});

      // Re-render on resize
      let resizeTimer;
      window.addEventListener('resize', function() {{
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {{ renderPage(pageNum); }}, 200);
      }});

      // Also observe stage size changes (tab switch etc.)
      if (window.ResizeObserver) {{
        new ResizeObserver(function() {{
          clearTimeout(resizeTimer);
          resizeTimer = setTimeout(function() {{ renderPage(pageNum); }}, 150);
        }}).observe(stage);
      }}

      pdfjsLib.getDocument({{ data: uint8Array }}).promise.then(function(doc) {{
        pdfDoc = doc;
        document.getElementById('page-count').textContent = pdfDoc.numPages;
        renderPage(pageNum);
      }});
    }})();
    </script>
    """

    components.html(html, height=height + 52, scrolling=False)


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
