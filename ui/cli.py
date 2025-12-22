from __future__ import annotations

import argparse

from core.casting import cast_hexagram
from core.qrng import QRNGProvider


def _line_str(bit: int) -> str:
    return "-----" if bit == 1 else "-- --"


def render_hexagram(bits: tuple[int, ...], moving_line: int | None = None) -> str:
    lines = []
    for idx in range(5, -1, -1):
        line = _line_str(bits[idx])
        if moving_line is not None and moving_line - 1 == idx:
            line = f"{line}  *"
        lines.append(line)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Q-Oracle CLI")
    parser.add_argument("--once", action="store_true", help="cast once and exit")
    args = parser.parse_args()

    provider = QRNGProvider()
    result = cast_hexagram(provider)

    print(f"本卦: {result.base.display_name}")
    print(render_hexagram(result.base.bits, moving_line=result.moving_line))
    print("")
    print(f"之卦: {result.changed.display_name}")
    print(render_hexagram(result.changed.bits))
    print("")
    for idx, (source, data) in enumerate(provider.history, start=1):
        print(f"随机源[{idx}] {source}: {data.hex()}")

    if not args.once:
        print("")
        print("提示: 使用 --once 仅生成一次结果")


if __name__ == "__main__":
    main()
