from __future__ import annotations

from dataclasses import dataclass


TRIGRAMS_BY_LINES = {
    (1, 1, 1): "乾",
    (1, 1, 0): "兑",
    (1, 0, 1): "离",
    (1, 0, 0): "震",
    (0, 1, 1): "巽",
    (0, 1, 0): "坎",
    (0, 0, 1): "艮",
    (0, 0, 0): "坤",
}

HEXAGRAM_NAMES = {
    ("坤", "坤"): "坤",
    ("艮", "坤"): "剥",
    ("坎", "坤"): "比",
    ("巽", "坤"): "观",
    ("震", "坤"): "豫",
    ("离", "坤"): "晋",
    ("兑", "坤"): "萃",
    ("乾", "坤"): "否",
    ("坤", "艮"): "谦",
    ("艮", "艮"): "艮",
    ("坎", "艮"): "蹇",
    ("巽", "艮"): "渐",
    ("震", "艮"): "小过",
    ("离", "艮"): "旅",
    ("兑", "艮"): "咸",
    ("乾", "艮"): "遁",
    ("坤", "坎"): "师",
    ("艮", "坎"): "蒙",
    ("坎", "坎"): "坎",
    ("巽", "坎"): "涣",
    ("震", "坎"): "解",
    ("离", "坎"): "未济",
    ("兑", "坎"): "困",
    ("乾", "坎"): "讼",
    ("坤", "巽"): "升",
    ("艮", "巽"): "蛊",
    ("坎", "巽"): "井",
    ("巽", "巽"): "巽",
    ("震", "巽"): "恒",
    ("离", "巽"): "鼎",
    ("兑", "巽"): "大过",
    ("乾", "巽"): "姤",
    ("坤", "震"): "复",
    ("艮", "震"): "颐",
    ("坎", "震"): "屯",
    ("巽", "震"): "益",
    ("震", "震"): "震",
    ("离", "震"): "噬嗑",
    ("兑", "震"): "随",
    ("乾", "震"): "无妄",
    ("坤", "离"): "明夷",
    ("艮", "离"): "贲",
    ("坎", "离"): "既济",
    ("巽", "离"): "家人",
    ("震", "离"): "丰",
    ("离", "离"): "离",
    ("兑", "离"): "革",
    ("乾", "离"): "同人",
    ("坤", "兑"): "临",
    ("艮", "兑"): "损",
    ("坎", "兑"): "节",
    ("巽", "兑"): "中孚",
    ("震", "兑"): "归妹",
    ("离", "兑"): "睽",
    ("兑", "兑"): "兑",
    ("乾", "兑"): "履",
    ("坤", "乾"): "泰",
    ("艮", "乾"): "大畜",
    ("坎", "乾"): "需",
    ("巽", "乾"): "小畜",
    ("震", "乾"): "大壮",
    ("离", "乾"): "大有",
    ("兑", "乾"): "夬",
    ("乾", "乾"): "乾",
}


@dataclass(frozen=True)
class Hexagram:
    bits: tuple[int, int, int, int, int, int]  # bottom -> top

    @property
    def lower_trigram(self) -> int:
        return (self.bits[0], self.bits[1], self.bits[2])

    @property
    def upper_trigram(self) -> int:
        return (self.bits[3], self.bits[4], self.bits[5])

    @property
    def upper_name(self) -> str:
        return TRIGRAMS_BY_LINES[self.upper_trigram]

    @property
    def lower_name(self) -> str:
        return TRIGRAMS_BY_LINES[self.lower_trigram]

    @property
    def hexagram_name(self) -> str:
        key = (self.upper_name, self.lower_name)
        if key in HEXAGRAM_NAMES:
            return HEXAGRAM_NAMES[key]
        return f"上{self.upper_name}下{self.lower_name}"

    @property
    def display_name(self) -> str:
        return f"上{self.upper_name}下{self.lower_name}（{self.hexagram_name}）"

    @property
    def name(self) -> str:
        return self.hexagram_name

    def to_int(self) -> int:
        value = 0
        for idx, bit in enumerate(self.bits):
            value |= (bit & 1) << idx
        return value

    @staticmethod
    def from_int(value: int) -> "Hexagram":
        bits = tuple((value >> i) & 1 for i in range(6))
        return Hexagram(bits=bits)
