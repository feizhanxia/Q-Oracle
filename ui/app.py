from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.casting import cast_hexagram
from ui.cli import render_hexagram


def _load_streamlit_secrets() -> None:
    try:
        secrets = st.secrets
        anu_key = secrets.get("ANU_API_KEY")
        lfdr_url = secrets.get("LFDR_URL")
        anu_url = secrets.get("ANU_URL")
    except Exception:
        return
    if anu_key:
        os.environ.setdefault("ANU_API_KEY", anu_key)
    if lfdr_url:
        os.environ.setdefault("LFDR_URL", lfdr_url)
    if anu_url:
        os.environ.setdefault("ANU_URL", anu_url)


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
}

html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 20% 10%, #1a2333 0%, #0b0f18 45%, #05070c 100%);
  color: var(--ink);
}

[data-testid="stHeader"] {
  background: transparent;
  height: 0;
}

[data-testid="stToolbar"] {
  visibility: hidden;
  height: 0;
}

.block-container {
  padding: 1.5rem 1.2rem 2rem 1.2rem;
  max-width: 920px;
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
  padding: 18px 18px;
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
  color: #d7e3f7;
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

div[data-testid="stTextInput"] {
  margin-top: 36px;
  margin-bottom: 42px;
}


</style>
""",
    unsafe_allow_html=True,
)

if "entered" not in st.session_state:
    st.session_state.entered = False

_load_streamlit_secrets()

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
            st.subheader(f"本卦：{result.base.display_name}")
            st.code(
                render_hexagram(result.base.bits, moving_line=result.moving_line),
                language="text",
            )
            st.subheader(f"之卦：{result.changed.display_name}")
            st.code(render_hexagram(result.changed.bits), language="text")
