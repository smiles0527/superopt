from __future__ import annotations

import inspect
import random
from collections.abc import Callable
from dataclasses import dataclass

from superopt.interp import execute
from superopt.ir import Program


@dataclass(frozen=True)
class Divergence:
    inputs: tuple[int, ...]
    program_output: int
    spec_output: int


def _infer_arity(spec: Callable[..., int]) -> int:
    try:
        params = inspect.signature(spec).parameters
    except (TypeError, ValueError):
        return 1
    count = sum(1 for name in params if name != "width")
    return count if count >= 1 else 1


def fuzz(
    program: Program,
    spec: Callable[..., int],
    *,
    trials: int = 100_000,
    seed: int = 0,
) -> Divergence | None:
    arity = _infer_arity(spec)
    bound = 1 << program.width
    rng = random.Random(seed)
    for _ in range(trials):
        inputs = tuple(rng.randrange(bound) for _ in range(arity))
        program_output = execute(program, inputs)
        spec_output = spec(*inputs, program.width)
        if program_output != spec_output:
            return Divergence(inputs, program_output, spec_output)
    return None


__all__ = ["Divergence", "fuzz"]
