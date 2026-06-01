from __future__ import annotations

from collections.abc import Sequence

from superopt.ir import Program


def execute(program: Program, inputs: Sequence[int]) -> int:
    raise NotImplementedError
