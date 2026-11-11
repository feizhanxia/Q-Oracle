from __future__ import annotations

import json
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
SOURCE_NAMES = {"LFDR": "LFDR（量子）", "ANU": "ANU（量子）", "CLASSIC": "系统随机（回退）"}


def _interpretation_messages(
    result: CastingResult,
    question: str,
    history: list[dict[str, str]],
) -> list[dict[str, str]]:
    prompt_path = ROOT / "prompts" / "llm_prompt.txt"
    try:
        instructions = prompt_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        instructions = "请以《周易》为背景，根据给定的本卦、动爻和之卦提供简明的文化解读。"
    except (OSError, UnicodeError) as exc:
        raise LLMError("无法读取 AI 解读提示词") from exc

    cast_context = {
        "占问": question,
        "本卦": result.base.display_name,
        "动爻": result.moving_line,
        "之卦": result.changed.display_name,
    }
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": json.dumps(cast_context, ensure_ascii=False)},
        *history,
    ]


def _write_reply(messages: list[dict[str, str]]) -> str:
    configs = build_llm_configs()
    output = st.empty()
    for config in configs:
        try:
            with output.container(), st.spinner("正在解读……"):
                reply = st.write_stream(stream_chat_completion(messages, config))
            if isinstance(reply, str) and reply.strip():
                return reply.strip()
            raise LLMError("模型未返回回答正文")
        except LLMError as exc:
            output.empty()
            logger.warning("AI model %s failed: %s", config.model, exc)
    raise LLMError("All configured models failed")


def _render_chat_area(result: CastingResult, question: str) -> None:
    st.subheader("AI 解读")
    state = st.session_state
    for message in state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.text(message["content"])
            else:
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
                messages = _interpretation_messages(result, question, state.chat_history)
                reply = _write_reply(messages)
            except (LLMError, SettingsError) as exc:
                logger.warning("AI interpretation failed: %s", exc)
            else:
                state.chat_history.append({"role": "assistant", "content": reply})
                state.reply_status = "ready"
        st.rerun()

    if state.reply_status == "ready":
        question_followup = st.chat_input("追问这次卦象")
        if question_followup and question_followup.strip():
            state.chat_history.append({"role": "user", "content": question_followup.strip()})
            state.reply_status = "pending"
            st.rerun()


def _render_cast(result: CastingResult, question: str, sources: tuple[str, ...]) -> None:
    st.subheader("本次卦象")
    st.caption("起卦时的占问")
    st.text(question)
    source_names = "、".join(SOURCE_NAMES[source] for source in sources)
    st.caption(f"动爻：第 {result.moving_line} 爻（自下而上） · 随机源：{source_names}")
    base, changed = st.columns(2)
    with base:
        st.markdown(f"**本卦 · {result.base.display_name}**")
        st.code(render_hexagram(result.base.bits, moving_line=result.moving_line), language="text")
    with changed:
        st.markdown(f"**之卦 · {result.changed.display_name}**")
        st.code(render_hexagram(result.changed.bits), language="text")


def main() -> None:
    st.set_page_config(page_title="Q-Oracle", page_icon="☯")
    st.markdown(
        """
<style>
[data-testid="stAppViewContainer"] {
  background: radial-gradient(ellipse at 20% 0%, #1a2333 0%, #0b0f18 52%, #080b12 100%);
}
.block-container {
  max-width: 840px;
  padding-top: 3rem;
  padding-bottom: 3rem;
}
</style>
""",
        unsafe_allow_html=True,
    )
    state = st.session_state
    state.setdefault("entered", False)
    state.setdefault("last_cast", None)
    state.setdefault("last_question", "")
    state.setdefault("last_sources", ())
    state.setdefault("chat_history", [])
    state.setdefault("reply_status", None)

    st.title("Q-Oracle")
    if not state.entered:
        st.markdown("以量子随机起卦，以《周易》读卦。")
        st.caption("心诚不息 · 神气归一 · 六根澄明 · 持念所问")
        if st.button("进入起卦", type="primary"):
            state.entered = True
            st.rerun()
        return

    with st.form("cast"):
        question = st.text_input("占问", placeholder="写下你想占问的事")
        submitted = st.form_submit_button("起卦", type="primary")
    if submitted:
        question = question.strip()
        if not question:
            st.warning("请输入占问后再起卦。")
        else:
            try:
                with st.spinner("起卦接引中……"):
                    provider = QRNGProvider()
                    result = cast_hexagram(provider)
            except QRNGError as exc:
                logger.warning("Casting failed: %s", exc)
                st.error("暂时无法取得起卦所需的随机数，请稍后重新起卦。")
            except SettingsError as exc:
                st.error(f"起卦配置有误：{exc}")
            else:
                state.last_cast = result
                state.last_question = question
                state.last_sources = tuple(dict.fromkeys(source for source, _ in provider.history))
                state.chat_history = []
                state.reply_status = None

    if state.last_cast is None:
        return

    _render_cast(state.last_cast, state.last_question, state.last_sources)
    if state.reply_status is None:
        st.caption("AI 解读会将占问、卦象和追问发送给首选模型服务，必要时尝试已配置的备用服务。")
        if st.button("AI 解读此卦"):
            state.reply_status = "pending"

    if state.reply_status is not None:
        _render_chat_area(state.last_cast, state.last_question)


if __name__ == "__main__":
    main()
