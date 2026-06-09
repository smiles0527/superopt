from __future__ import annotations


def popcount(x: int, width: int) -> int:
    x &= (1 << width) - 1
    count = 0
    for i in range(width):
        count += (x >> i) & 1
    return count
