from __future__ import annotations

import logging
import re
import sys
from html import escape
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import SettingsError
from core.casting import CastingResult, cast_hexagram
from core.hexagrams import Hexagram
from core.llm import LLMError, build_llm_config, stream_chat_completion
from core.qrng import QRNGError

logger = logging.getLogger(__name__)


def _render_styles() -> None:
    styles = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)


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
    config = build_llm_config()
    output = st.empty()
    try:
        with output.container(), st.spinner(""):
            reply = st.write_stream(stream_chat_completion(messages, config))
        if isinstance(reply, str) and reply.strip():
            return reply.strip()
        raise LLMError("模型未返回回答正文")
    except LLMError:
        output.empty()
        raise


def _render_chat_area(result: CastingResult, question: str) -> None:
    st.markdown('<h2 class="q-title q-chat-title">AI 解读</h2>', unsafe_allow_html=True)

    state = st.session_state
    with st.container():
        for message in state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if state.reply_status == "failed":
            st.error("AI 暂时无法回复。可以重试这条请求，卦象和已完成的对话仍可查看。")
            if st.button("重试 AI 回复"):
                state.reply_status = "pending"

        if state.reply_status == "pending":
            # Mark the request retryable before streaming in case the run is interrupted.
            state.reply_status = "failed"
            with st.chat_message("assistant"):
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
    st.markdown(
        """
<header class="q-masthead">
<h1 class="q-title q-wordmark">Q-Oracle</h1>
<p class="q-sub">量子随机驱动的起卦引擎 · 高维信息译码通道</p>
</header>
<div class="q-quote">
<p>宏观尺度下的量子相干会在与环境耦合中快速退相干，量子态的相位相关性被环境纠缠扩散，最终在可观测层面表现为信息被噪声平均化与稀释。</p>
<p>量子随机在更深的层面是高维灵体的信息流，是被测量投影到现实的额外指引。周易是这份信息的译码表，它把量子随机翻译成我们可以理解与使用的语言。</p>
<p>本系统以量子随机为入口，以周易为译码，让理工与玄学在同一套语言中对齐。</p>
</div>
<p class="q-tag">心诚不息 · 神气归一 · 六根澄明 · 持念所问</p>
""",
        unsafe_allow_html=True,
    )
    if st.button("进入起卦", type="primary"):
        state.entered = True
        st.rerun()


def _cast(question: str) -> bool:
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
        return True
    return False


def _hexagram_figure(kind: str, hexagram: Hexagram, moving_line: int | None = None) -> str:
    stroke = '<span class="q-stroke"></span>'
    rows = []
    for index, bit in reversed(tuple(enumerate(hexagram.bits, start=1))):
        row_class = "q-yao q-yao--moving" if index == moving_line else "q-yao"
        rows.append(f'<div class="{row_class}">{stroke if bit else stroke * 2}</div>')

    line_summary = "、".join("阳" if bit else "阴" for bit in hexagram.bits)
    trigrams = f"上{hexagram.upper_name}下{hexagram.lower_name}"
    moving_label = (
        f'<span class="q-moving-label">动爻 · 第 {moving_line} 爻</span>' if moving_line is not None else ""
    )
    return (
        '<figure class="q-hexagram">'
        f'<div class="q-lines" role="img" aria-label="爻线自下而上为{line_summary}">{"".join(rows)}</div>'
        '<figcaption>'
        f'<span class="q-hexagram-kind">{escape(kind)}</span>'
        f'<strong class="q-hexagram-name">{escape(hexagram.name)}</strong>'
        f'<span class="q-trigrams">{escape(trigrams)}</span>'
        f'{moving_label}</figcaption></figure>'
    )


def _render_reading(result: CastingResult, fresh_cast: bool) -> None:
    reading_class = "q-reading q-reading--new" if fresh_cast else "q-reading"
    base = _hexagram_figure("本卦", result.base, result.moving_line)
    changed = _hexagram_figure("之卦", result.changed)
    st.markdown(
        f'<section class="{reading_class}" aria-label="卦象">{base}{changed}</section>',
        unsafe_allow_html=True,
    )


def _render_casting_page() -> None:
    state = st.session_state
    st.markdown('<h1 class="q-title q-masthead">起卦</h1>', unsafe_allow_html=True)
    question = st.text_input(
        "问题",
        placeholder="请定其问，勿复移。",
        label_visibility="collapsed",
    ).strip()
    fresh_cast = False
    if st.button("所问既明，起卦在此。", disabled=not question, type="primary"):
        fresh_cast = _cast(question)

    if state.last_cast is None:
        return

    result = state.last_cast
    _render_reading(result, fresh_cast)
    if st.button("AI 解读此卦") and state.reply_status in (None, "failed"):
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
