from __future__ import annotations

import pytest

from core.casting import cast_hexagram
from core.hexagrams import Hexagram


class FakeProvider:
    def __init__(self, data: bytes) -> None:
        self._data = bytearray(data)

    def get_bytes(self, length: int) -> bytes:
        if length > len(self._data):
            raise RuntimeError("Insufficient data")
        out = self._data[:length]
        del self._data[:length]
        return bytes(out)


def test_cast_hexagram_bits_and_moving_line() -> None:
    # 0x2d -> bits (lsb first): 1,0,1,1,0,1
    # next byte 0x05 -> moving line index = 6
    provider = FakeProvider(bytes([0x2D, 0x05]))
    result = cast_hexagram(provider)

    assert result.base.bits == (1, 0, 1, 1, 0, 1)
    assert result.moving_line == 6
    assert result.changed.bits == (1, 0, 1, 1, 0, 0)
    assert isinstance(result.base, Hexagram)
