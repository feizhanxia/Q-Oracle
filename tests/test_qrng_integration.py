from __future__ import annotations

import os

import pytest

from config.settings import get_settings
from core.qrng import AnuClient, LfdrClient, QRNGError


@pytest.mark.integration
def test_lfdr_live() -> None:
    settings = get_settings()
    client = LfdrClient(settings)
    try:
        data = client.get_bytes(2)
    except QRNGError as exc:
        pytest.skip(f"LFDR unavailable: {exc}")
    assert isinstance(data, bytes)
    assert len(data) == 2


@pytest.mark.integration
def test_anu_live() -> None:
    if not os.getenv("ANU_API_KEY"):
        pytest.skip("ANU_API_KEY not set")
    settings = get_settings()
    client = AnuClient(settings)
    try:
        data = client.get_bytes(2)
    except QRNGError as exc:
        pytest.skip(f"ANU unavailable: {exc}")
    assert isinstance(data, bytes)
    assert len(data) == 2
