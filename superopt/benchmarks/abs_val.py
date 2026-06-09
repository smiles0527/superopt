from __future__ import annotations


def absval(x: int, width: int) -> int:
    mask = (1 << width) - 1
    x &= mask
    if x & (1 << (width - 1)):
        return -x & mask
    return x
