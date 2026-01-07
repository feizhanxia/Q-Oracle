from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Tuple
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings
from core.casting import CastingResult, cast_hexagram
from core.llm import LLMError, build_llm_config, stream_chat_completion
from ui.cli import render_hexagram


def _load_streamlit_secrets() -> None:
    try:
        secrets = st.secrets
        anu_key = secrets.get("ANU_API_KEY")
        lfdr_url = secrets.get("LFDR_URL")
        anu_url = secrets.get("ANU_URL")
        llm_key = secrets.get("LLM_API_KEY")
        llm_base = secrets.get("LLM_BASE_URL")
        llm_model = secrets.get("LLM_MODEL")
    except Exception:
        return
    if anu_key:
        os.environ.setdefault("ANU_API_KEY", anu_key)
    if lfdr_url:
        os.environ.setdefault("LFDR_URL", lfdr_url)
    if anu_url:
        os.environ.setdefault("ANU_URL", anu_url)
    if llm_key:
        os.environ.setdefault("LLM_API_KEY", llm_key)
    if llm_base:
        os.environ.setdefault("LLM_BASE_URL", llm_base)
    if llm_model:
        os.environ.setdefault("LLM_MODEL", llm_model)


st.set_page_config(page_title="Q-Oracle", page_icon="☯")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@300;400;600&family=Cinzel:wght@400;600&display=swap');

:root {
  --deep: #0a0f1a;
  --ink: #c9d4e5;
  --mist: #96a7bf;
  --halo: #2f435f;
  --pulse: #7fb2ff;
  color-scheme: dark;
}

html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 20% 10%, #1a2333 0%, #0b0f18 45%, #05070c 100%);
  color: var(--ink);
  min-height: 100vh;
}

[data-testid="stAppViewContainer"] > .main {
  min-height: 100vh;
}

[data-testid="stHeader"] {
  background: transparent;
  height: 0;
}

[data-testid="stToolbar"] {
  visibility: hidden;
  height: 0;
  display: none;
}

button[kind="headerTheme"] {
  display: none !important;
}

footer, div[data-testid="stDecoration"], .viewerBadge_container__2QSgA {
  display: none !important;
}

.block-container {
  padding: 1.2rem 0.6rem 1.8rem 0.6rem;
  max-width: 980px;
}

.q-title {
  font-family: 'Cinzel', serif;
  letter-spacing: 0.08em;
  font-size: 2.05rem;
  color: #e5ecf7;
  margin-bottom: 0.2rem;
}

.q-sub {
  font-family: 'Spectral', serif;
  color: var(--mist);
  font-size: 0.92rem;
  margin-bottom: 1.2rem;
}

div[data-testid="stVerticalBlock"]:has(.q-panel-block) {
  background: rgba(10, 15, 26, 0.65);
  border: 1px solid rgba(127, 178, 255, 0.2);
  border-radius: 18px;
  padding: 14px 14px;
  box-shadow: 0 0 30px rgba(46, 82, 140, 0.2);
}

.q-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(127,178,255,0.35), transparent);
  margin: 22px 0;
}

.q-tag {
  font-family: 'Spectral', serif;
  color: var(--mist);
  font-size: 0.9rem;
}

.q-quote {
  font-family: 'Spectral', serif;
  color: #eef3ff;
  font-size: 0.9rem;
  line-height: 1.6;
}

.q-label {
  font-family: 'Spectral', serif;
  color: var(--mist);
  font-size: 0.9rem;
  margin-bottom: 0.4rem;
}

.q-foot {
  font-family: 'Spectral', serif;
  color: var(--mist);
  font-size: 0.9rem;
}

/* Chat text tone */
section[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  margin-bottom: 8px !important;
}

section[data-testid="stChatMessage"] div[data-testid="stChatMessageContent"] {
  background: #0f1320 !important;
  border: 1px solid rgba(127, 178, 255, 0.18) !important;
  border-radius: 12px !important;
  padding: 8px 12px !important;
}

section[data-testid="stChatMessage"] div[data-testid="stChatMessageContent"] * {
  color: #f8fbff !important;
}

section[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
  background: transparent !important;
  padding: 0 !important;
}

section[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] p,
section[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] span,
section[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] code,
section[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] li,
section[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] strong {
  color: #f8fbff !important;
}

/* Inputs */
div[data-testid="stTextInput"] input {
  background: #1c212d !important;
  color: #e8eef9 !important;
  border: 1px solid rgba(127, 178, 255, 0.35) !important;
}

div[data-testid="stTextInput"] input:focus {
  border-color: rgba(127, 178, 255, 0.8) !important;
  box-shadow: 0 0 0 2px rgba(127, 178, 255, 0.25) !important;
}

div[data-testid="stTextInput"] input::placeholder {
  color: #9aa7bd !important;
}

div[data-testid="stTextInput"] {
  margin-top: 36px;
  margin-bottom: 42px;
}

/* Buttons */
div.stButton > button {
  background: linear-gradient(90deg, #1f2a3a, #243348);
  color: #e5ecf7;
  border: 1px solid rgba(127, 178, 255, 0.35);
  box-shadow: 0 0 12px rgba(127, 178, 255, 0.15);
}

div.stButton > button:hover {
  border-color: rgba(127, 178, 255, 0.6);
  box-shadow: 0 0 14px rgba(127, 178, 255, 0.25);
}

div.stButton > button:disabled {
  opacity: 0.45;
  border-color: rgba(150, 160, 180, 0.4);
  box-shadow: none;
}

/* Code blocks / outputs */
div[data-testid="stCodeBlock"],
div[data-testid="stCodeBlock"] pre,
div[data-testid="stCodeBlock"] code,
pre,
pre code {
  background: #0f1320 !important;
  color: #e8eef9 !important;
}

div[data-testid="stCodeBlock"] {
  border: 1px solid rgba(127, 178, 255, 0.25) !important;
  border-radius: 12px !important;
  padding: 12px !important;
  box-shadow: 0 0 14px rgba(30, 45, 70, 0.35) !important;
}

/* Chat area */
.chat-panel {
  background: rgba(10, 15, 26, 0.7);
  border: 1px solid rgba(127, 178, 255, 0.25);
  border-radius: 14px;
  padding: 12px 14px;
  box-shadow: 0 0 18px rgba(30, 45, 70, 0.35);
}

div[data-testid="stChatInput"] textarea {
  background: #1c212d !important;
  color: #e8eef9 !important;
  border: 1px solid rgba(127, 178, 255, 0.35) !important;
}

div[data-testid="stChatInput"] textarea:focus {
  border-color: rgba(127, 178, 255, 0.8) !important;
  box-shadow: 0 0 0 2px rgba(127, 178, 255, 0.25) !important;
}

section[data-testid="stChatInput"] {
  margin-top: 18px;
}

/* Chat avatars */
section[data-testid="stChatMessage"] img {
  display: none !important;
}

</style>
""",
    unsafe_allow_html=True,
)

if "entered" not in st.session_state:
    st.session_state.entered = False
if "show_llm" not in st.session_state:
    st.session_state.show_llm = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_cast" not in st.session_state:
    st.session_state.last_cast = None
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "is_streaming" not in st.session_state:
    st.session_state.is_streaming = False
if "pending_user_input" not in st.session_state:
    st.session_state.pending_user_input = None

_load_streamlit_secrets()

def _load_prompt_template() -> str:
    prompt_path = ROOT / "prompts" / "llm_prompt.txt"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "我起卦占断，所问：{question}\n本卦：{base_name}\n动爻：第 {moving_line} 爻\n之卦：{changed_name}\n请结合卦象给出解读与建议。"


def _format_prompt(result: CastingResult, question: str) -> str:
    template = _load_prompt_template()
    return template.format(
        question=question.strip(),
        base_name=result.base.display_name,
        moving_line=result.moving_line,
        changed_name=result.changed.display_name,
    )


def _render_chat_area(result: CastingResult, question: str) -> None:
    st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-title">AI 解读</div>', unsafe_allow_html=True)
    st.markdown('<div class="q-sub"></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)

    chat_container = st.container()
    with chat_container:
        for role, content in st.session_state.chat_history:
            if role == "system":
                continue
            avatar = "⚫️" if role == "assistant" else "🌕"
            with st.chat_message(role, avatar=avatar):
                st.markdown(content)

        # 首次自动解读（当还没有 assistant 回复时）
        has_assistant = any(role == "assistant" for role, _ in st.session_state.chat_history)
        if st.session_state.show_llm and not has_assistant:
            with st.chat_message("assistant", avatar="⚫️"):
                with st.spinner(""):
                    try:
                        st.session_state.is_streaming = True
                        settings = get_settings()
                        config = build_llm_config(settings)
                        messages: List[dict[str, str]] = []
                        for role, content in st.session_state.chat_history:
                            messages.append({"role": role, "content": content})
                        chunks: list[str] = []
                        placeholder = st.empty()
                        for chunk in stream_chat_completion(messages, config):
                            chunks.append(chunk)
                            placeholder.markdown("".join(chunks))
                        full = "".join(chunks).strip()
                        st.session_state.chat_history.append(("assistant", full))
                    except LLMError as exc:
                        st.error(f"AI 解读失败：{exc}")
                    finally:
                        st.session_state.is_streaming = False

        if st.session_state.pending_user_input:
            user_input = st.session_state.pending_user_input
            st.session_state.pending_user_input = None
            st.session_state.chat_history.append(("user", user_input))
            with st.chat_message("user", avatar="🌕"):
                st.markdown(user_input)

            placeholder = st.chat_message("assistant", avatar="⚫️")
            with placeholder:
                with st.spinner(""):
                    try:
                        st.session_state.is_streaming = True
                        settings = get_settings()
                        config = build_llm_config(settings)
                        messages: List[dict[str, str]] = []
                        # seed context
                        if not any(role == "system" for role, _ in st.session_state.chat_history):
                            seed = _format_prompt(result, question)
                            messages.append({"role": "user", "content": seed})
                        for role, content in st.session_state.chat_history:
                            messages.append({"role": role, "content": content})
                        chunks: list[str] = []
                        out = st.empty()
                        for chunk in stream_chat_completion(messages, config):
                            chunks.append(chunk)
                            out.markdown("".join(chunks))
                        full = "".join(chunks).strip()
                        st.session_state.chat_history.append(("assistant", full))
                    except LLMError as exc:
                        st.error(f"AI 解读失败：{exc}")
                    finally:
                        st.session_state.is_streaming = False

        if not st.session_state.is_streaming and not st.session_state.pending_user_input:
            user_input = st.chat_input("可继续追问，或让 AI 解释卦意")
            if user_input:
                st.session_state.pending_user_input = user_input
                st.rerun()

if not st.session_state.entered:
    panel = st.container()
    with panel:
        st.markdown('<div class="q-panel-block"></div>', unsafe_allow_html=True)
        st.markdown('<div class="q-title">Q-Oracle</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="q-sub">量子随机驱动的起卦引擎 · 高维信息译码通道</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            """
<div class="q-quote">
宏观尺度下的量子相干会在与环境耦合中快速退相干，量子态的相位相关性被环境纠缠扩散，
最终在可观测层面表现为信息被噪声平均化与稀释。<br><br>
量子随机在更深的层面是高维灵体的信息流，是被测量投影到现实的额外指引。
周易是这份信息的译码表，它把量子随机翻译成我们可以理解与使用的语言。<br><br>
本系统以量子随机为入口，以周易为译码，让理工与玄学在同一套语言中对齐。
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="q-tag">心诚不息 · 神气归一 · 六根澄明 · 持念所问</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<br>', unsafe_allow_html=True)
        if st.button("进入起卦", use_container_width=True):
            st.session_state.entered = True
            st.rerun()
else:
    panel = st.container()
    with panel:
        st.markdown('<div class="q-panel-block"></div>', unsafe_allow_html=True)
        st.markdown('<div class="q-title">起卦</div>', unsafe_allow_html=True)
        # st.markdown('<div class="q-sub">请在心中持念所问</div>', unsafe_allow_html=True)
        st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)
        question = st.text_input(
            "问题",
            placeholder="请定其问，勿复移。",
            label_visibility="collapsed",
        )
        can_cast = bool(question.strip())
        if st.button("所问既明，起卦在此。", disabled=not can_cast, use_container_width=True):
            with st.spinner("起卦接引中……"):
                result = cast_hexagram()
            st.session_state.last_cast = result
            st.session_state.last_question = question.strip()
            st.session_state.show_llm = False
            st.session_state.chat_history = []

        # 展示最新一次起卦结果
        if st.session_state.last_cast:
            result = st.session_state.last_cast
            st.subheader(f"本卦：{result.base.display_name}")
            st.code(
                render_hexagram(result.base.bits, moving_line=result.moving_line),
                language="text",
            )
            st.subheader(f"之卦：{result.changed.display_name}")
            st.code(render_hexagram(result.changed.bits), language="text")

            st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)
            if st.button("AI 解读此卦", use_container_width=True):
                st.session_state.show_llm = True
                # 立即触发首轮解读（作为系统上下文，不显示）
                system_prompt = _format_prompt(st.session_state.last_cast, st.session_state.last_question)
                st.session_state.chat_history = [("system", system_prompt)]
                st.rerun()

        if st.session_state.show_llm and st.session_state.last_cast:
            _render_chat_area(st.session_state.last_cast, st.session_state.last_question)
