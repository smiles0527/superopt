from __future__ import annotations

from collections.abc import Callable

from superopt.ir import Program


def enumerate_optimal(
    spec: Callable[..., int], width: int, max_len: int
) -> Program | None:
    raise NotImplementedError
