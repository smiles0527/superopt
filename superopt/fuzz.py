from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from superopt.interp import execute
from superopt.ir import InputRef, Program


@dataclass(frozen=True)
class Divergence:
    inputs: tuple[int, ...]
    program_output: int
    spec_output: int


def _arity(program: Program) -> int:
    indices = [
        operand.index
        for instruction in program.instructions
        for operand in instruction.operands
        if isinstance(operand, InputRef)
    ]
    if isinstance(program.output, InputRef):
        indices.append(program.output.index)
    return max(indices) + 1 if indices else 1


def fuzz(
    program: Program,
    spec: Callable[..., int],
    *,
    trials: int = 100_000,
    seed: int = 0,
) -> Divergence | None:
    arity = _arity(program)
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
