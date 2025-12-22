from __future__ import annotations

from dataclasses import dataclass


TRIGRAMS = {
    0b111: "乾",
    0b110: "兑",
    0b101: "离",
    0b100: "震",
    0b011: "巽",
    0b010: "坎",
    0b001: "艮",
    0b000: "坤",
}


@dataclass(frozen=True)
class Hexagram:
    bits: tuple[int, int, int, int, int, int]  # bottom -> top

    @property
    def lower_trigram(self) -> int:
        return (self.bits[2] << 2) | (self.bits[1] << 1) | self.bits[0]

    @property
    def upper_trigram(self) -> int:
        return (self.bits[5] << 2) | (self.bits[4] << 1) | self.bits[3]

    @property
    def name(self) -> str:
        upper = TRIGRAMS[self.upper_trigram]
        lower = TRIGRAMS[self.lower_trigram]
        return f"上{upper}下{lower}"

    def to_int(self) -> int:
        value = 0
        for idx, bit in enumerate(self.bits):
            value |= (bit & 1) << idx
        return value

    @staticmethod
    def from_int(value: int) -> "Hexagram":
        bits = tuple((value >> i) & 1 for i in range(6))
        return Hexagram(bits=bits)
