from __future__ import annotations

from dataclasses import dataclass

from core.hexagrams import Hexagram
from core.qrng import QRNGProvider


@dataclass(frozen=True)
class CastingResult:
    base: Hexagram
    changed: Hexagram
    moving_line: int  # 1..6, bottom -> top


def _rand_int(provider: QRNGProvider, max_inclusive: int) -> int:
    if max_inclusive < 0 or max_inclusive > 255:
        raise ValueError("max_inclusive must be between 0 and 255")
    span = max_inclusive + 1
    limit = (256 // span) * span
    while True:
        value = provider.get_bytes(1)[0]
        if value < limit:
            return value % span


def _rand_bits(provider: QRNGProvider, count: int) -> list[int]:
    if count < 1:
        return []
    byte_len = (count + 7) // 8
    raw = provider.get_bytes(byte_len)
    bits: list[int] = []
    for b in raw:
        for i in range(8):
            bits.append((b >> i) & 1)
            if len(bits) == count:
                return bits
    return bits


def cast_hexagram(provider: QRNGProvider | None = None) -> CastingResult:
    provider = provider or QRNGProvider()

    bits = _rand_bits(provider, 6)
    base = Hexagram(bits=tuple(bits))

    moving_line = _rand_int(provider, 5) + 1  # 1..6
    changed_bits = list(base.bits)
    idx = moving_line - 1
    changed_bits[idx] = 1 - changed_bits[idx]
    changed = Hexagram(bits=tuple(changed_bits))

    return CastingResult(base=base, changed=changed, moving_line=moving_line)
