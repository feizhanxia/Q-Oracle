from __future__ import annotations

import pytest

from core.qrng import QRNGError, QRNGProvider


class FailingClient:
    def get_bytes(self, length: int) -> bytes:
        raise QRNGError("fail")


class StaticClient:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def get_bytes(self, length: int) -> bytes:
        return self._payload[:length]


def test_qrng_fallback_to_anu() -> None:
    provider = QRNGProvider(lfdr=FailingClient(), anu=StaticClient(b"\x01\x02"))
    assert provider.get_bytes(2) == b"\x01\x02"


def test_qrng_all_failed() -> None:
    provider = QRNGProvider(lfdr=FailingClient(), anu=FailingClient())
    with pytest.raises(QRNGError):
        provider.get_bytes(1)
