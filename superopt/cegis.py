from __future__ import annotations

from dataclasses import dataclass

from superopt.ir import (
    ARITY,
    Const,
    InputRef,
    Instruction,
    Op,
    Program,
    ResultRef,
)


@dataclass(frozen=True)
class Library:
    ops: tuple[Op, ...]
    n_constants: int = 0


@dataclass(frozen=True)
class _Assignment:
    lo: dict[int, int]
    li: dict[tuple[int, int], int]
    consts: dict[int, int]


def _decode(
    assignment: _Assignment, library: Library, n_inputs: int, width: int
) -> Program:
    ops = library.ops
    n_consts = library.n_constants
    n_lines = n_inputs + n_consts + len(ops)
    order = sorted(range(len(ops)), key=lambda k: assignment.lo[k])
    line_to_result = {assignment.lo[k]: pos for pos, k in enumerate(order)}

    def operand(line: int) -> Const | InputRef | ResultRef:
        if line < n_inputs:
            return InputRef(line)
        if line < n_inputs + n_consts:
            return Const(assignment.consts[line - n_inputs])
        return ResultRef(line_to_result[line])

    instructions = tuple(
        Instruction(
            ops[k],
            tuple(operand(assignment.li[(k, j)]) for j in range(ARITY[ops[k]])),
        )
        for k in order
    )
    return Program(width, instructions, ResultRef(line_to_result[n_lines - 1]))
