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
st.title("Q-Oracle")
st.caption("量子随机数起卦（先本卦，再动爻）")

_load_streamlit_secrets()

if st.button("起卦"):
    result = cast_hexagram()
    st.subheader(f"本卦：{result.base.name}")
    st.code(render_hexagram(result.base.bits, moving_line=result.moving_line), language="text")
    st.subheader(f"之卦：{result.changed.name}")
    st.code(render_hexagram(result.changed.bits), language="text")
