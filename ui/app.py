from __future__ import annotations

import os

import streamlit as st

from core.casting import cast_hexagram
from ui.cli import render_hexagram


def _load_streamlit_secrets() -> None:
    if "ANU_API_KEY" in st.secrets:
        os.environ.setdefault("ANU_API_KEY", st.secrets["ANU_API_KEY"])
    if "LFDR_URL" in st.secrets:
        os.environ.setdefault("LFDR_URL", st.secrets["LFDR_URL"])
    if "ANU_URL" in st.secrets:
        os.environ.setdefault("ANU_URL", st.secrets["ANU_URL"])


st.set_page_config(page_title="Q-Oracle", page_icon="☯")
st.title("Q-Oracle")
st.caption("量子随机数起卦（先本卦，再动爻）")

_load_streamlit_secrets()

if st.button("起卦"):
    result = cast_hexagram()
    st.subheader(f"本卦：{result.base.name}")
    st.code(render_hexagram(result.base.bits, moving_line=result.moving_line), language="text")
    st.subheader(f"之卦：{result.changed.name}")
    st.code(render_hexagram(result.changed.bits), language="text")
