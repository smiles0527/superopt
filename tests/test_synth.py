from __future__ import annotations

from superopt.ir import Const, Hole, InputRef, Instruction, Op, Program, ResultRef
from superopt.synth import _fill


def _odd_mask(width: int) -> int:
    return sum(1 << i for i in range(1, width, 2))


def _mask_spec(width: int) -> Program:
    return Program(
        width,
        (Instruction(Op.AND, (InputRef(0), Const(_odd_mask(width)))),),
        ResultRef(0),
    )


def _and_sketch(width: int) -> Program:
    return Program(
        width,
        (Instruction(Op.AND, (InputRef(0), Hole(0))),),
        ResultRef(0),
    )


def _or_sketch(width: int) -> Program:
    return Program(
        width,
        (Instruction(Op.OR, (InputRef(0), Hole(0))),),
        ResultRef(0),
    )


def test_fill_replaces_holes_with_constants():
    filled = _fill(_and_sketch(8), {0: 0xAA})
    assert filled == Program(
        8,
        (Instruction(Op.AND, (InputRef(0), Const(0xAA))),),
        ResultRef(0),
    )
