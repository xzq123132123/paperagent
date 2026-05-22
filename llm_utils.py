"""Qwen API call and proxy utilities."""

import os
from http import HTTPStatus

import streamlit as st
import dashscope
from dashscope import Generation

from config import DEFAULT_SYSTEM_PROMPT_TEMPLATE, MODEL_NAME


class NoProxyContext:
    """Temporarily remove proxy env vars for DashScope calls."""

    def __enter__(self):
        self.backup = {}
        for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
            if k in os.environ:
                self.backup[k] = os.environ[k]
                del os.environ[k]

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k, v in self.backup.items():
            os.environ[k] = v


def call_qwen(api_key, reader_level, prompt, history=None, system_instruction=None):
    """Call the Qwen model via DashScope.

    Args:
        api_key: DashScope API key string.
        reader_level: One of the reader-level labels used in the system prompt.
        prompt: The user prompt / question.
        history: Optional list of prior messages (last 4 are used).
        system_instruction: Override the default system prompt. If None, the
            template from config is used.
    """
    if not api_key:
        st.error("请先填入 API Key")
        return None

    dashscope.api_key = api_key

    if system_instruction is None:
        system_instruction = DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(
            reader_level=reader_level
        )

    messages = [{"role": "system", "content": system_instruction}]
    if history:
        messages.extend(history[-4:])
    messages.append({"role": "user", "content": prompt})

    try:
        with NoProxyContext():
            response = Generation.call(
                model=MODEL_NAME,
                messages=messages,
                result_format="message",
            )

        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0]["message"]["content"]
        else:
            st.error(f"API Error: {response.message}")
            return None
    except Exception as e:
        st.error(f"Network Error: {e}")
        return None
