from __future__ import annotations

import re
import logging
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import SettingsError
from core.casting import CastingResult, cast_hexagram
from core.llm import LLMError, build_llm_configs, stream_chat_completion
from core.qrng import QRNGError, QRNGProvider
from ui.cli import render_hexagram

logger = logging.getLogger(__name__)


def _render_styles() -> None:
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


def _format_prompt(result: CastingResult, question: str) -> str:
    prompt_path = ROOT / "prompts" / "llm_prompt.txt"
    try:
        template = prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        template = (
            "我起卦占断，所问：{question}\n本卦：{base_name}\n动爻：第 {moving_line} 爻\n"
            "之卦：{changed_name}\n请结合卦象给出解读与建议。"
        )
    except (OSError, UnicodeError) as exc:
        raise LLMError("无法读取 AI 解读提示词") from exc

    values = {
        "question": question.strip(),
        "base_name": result.base.display_name,
        "moving_line": str(result.moving_line),
        "changed_name": result.changed.display_name,
    }
    return re.sub(r"\{(question|base_name|moving_line|changed_name)\}", lambda match: values[match[1]], template)


def _write_reply(messages: list[dict[str, str]]) -> str:
    configs = build_llm_configs()
    output = st.empty()
    for config in configs:
        try:
            with output.container(), st.spinner(""):
                reply = st.write_stream(stream_chat_completion(messages, config))
            if isinstance(reply, str) and reply.strip():
                return reply.strip()
            raise LLMError("模型未返回回答正文")
        except LLMError as exc:
            output.empty()
            logger.warning("AI model %s failed: %s", config.model, exc)
    raise LLMError("All configured models failed")


def _render_chat_area(result: CastingResult, question: str) -> None:
    st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-title">AI 解读</div>', unsafe_allow_html=True)
    st.markdown('<div class="q-sub"></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)

    state = st.session_state
    with st.container():
        for message in state.chat_history:
            avatar = "⚫️" if message["role"] == "assistant" else "🌕"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

        if state.reply_status == "failed":
            st.error("AI 暂时无法回复。可以重试这条请求，卦象和已完成的对话仍可查看。")
            if st.button("重试 AI 回复"):
                state.reply_status = "pending"

        if state.reply_status == "pending":
            # Mark the request retryable before streaming in case the run is interrupted.
            state.reply_status = "failed"
            with st.chat_message("assistant", avatar="⚫️"):
                try:
                    if state.cast_prompt is None:
                        state.cast_prompt = _format_prompt(result, question)
                    messages = [{"role": "system", "content": state.cast_prompt}, *state.chat_history]
                    reply = _write_reply(messages)
                except (LLMError, SettingsError) as exc:
                    logger.warning("AI interpretation failed: %s", exc)
                else:
                    state.chat_history.append({"role": "assistant", "content": reply})
                    state.reply_status = "ready"
            st.rerun()

        if state.reply_status == "ready":
            user_input = st.chat_input("可继续追问，或让 AI 解释卦意")
            if user_input and user_input.strip():
                state.chat_history.append({"role": "user", "content": user_input.strip()})
                state.reply_status = "pending"
                st.rerun()


def _render_landing() -> None:
    state = st.session_state
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
            state.entered = True
            st.rerun()


def _cast(question: str) -> None:
    try:
        with st.spinner("起卦接引中……"):
            result = cast_hexagram()
    except QRNGError as exc:
        logger.warning("Casting failed: %s", exc)
        st.error("暂时无法取得起卦所需的随机数，请稍后重新起卦。")
    except SettingsError as exc:
        st.error(f"起卦配置有误：{exc}")
    else:
        state = st.session_state
        state.last_cast = result
        state.last_question = question
        state.cast_prompt = None
        state.chat_history = []
        state.reply_status = None


def _render_casting_page() -> None:
    state = st.session_state
    panel = st.container()
    with panel:
        st.markdown('<div class="q-panel-block"></div>', unsafe_allow_html=True)
        st.markdown('<div class="q-title">起卦</div>', unsafe_allow_html=True)
        st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)
        question = st.text_input(
            "问题",
            placeholder="请定其问，勿复移。",
            label_visibility="collapsed",
        )
        can_cast = bool(question.strip())
        if st.button("所问既明，起卦在此。", disabled=not can_cast, use_container_width=True):
            _cast(question.strip())

        if state.last_cast is None:
            return

        result = state.last_cast
        st.subheader(f"本卦：{result.base.display_name}")
        st.code(
            render_hexagram(result.base.bits, moving_line=result.moving_line),
            language="text",
        )
        st.subheader(f"之卦：{result.changed.display_name}")
        st.code(render_hexagram(result.changed.bits), language="text")

        st.markdown('<div class="q-divider"></div>', unsafe_allow_html=True)
        if st.button("AI 解读此卦", use_container_width=True):
            if state.reply_status in (None, "failed"):
                state.reply_status = "pending"

        if state.reply_status is not None:
            _render_chat_area(result, state.last_question)


def main() -> None:
    st.set_page_config(page_title="Q-Oracle", page_icon="☯")
    _render_styles()
    state = st.session_state
    state.setdefault("entered", False)
    state.setdefault("last_cast", None)
    state.setdefault("last_question", "")
    state.setdefault("cast_prompt", None)
    state.setdefault("chat_history", [])
    state.setdefault("reply_status", None)

    if state.entered:
        _render_casting_page()
    else:
        _render_landing()


if __name__ == "__main__":
    main()
