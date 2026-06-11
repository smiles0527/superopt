from __future__ import annotations

from z3 import BitVecVal, simplify, substitute

from superopt.encode import encode_sketch
from superopt.ir import Hole, InputRef, Instruction, Op, Program, ResultRef


def _and_hole_sketch(width: int) -> Program:
    return Program(
        width,
        (Instruction(Op.AND, (InputRef(0), Hole(0))),),
        ResultRef(0),
    )


def test_encode_sketch_exposes_one_input_and_one_hole():
    input_vars, hole_vars, _ = encode_sketch(_and_hole_sketch(8))
    assert len(input_vars) == 1
    assert set(hole_vars) == {0}


def test_encode_sketch_output_is_input_and_hole():
    input_vars, hole_vars, out = encode_sketch(_and_hole_sketch(8))
    for x, c, expected in [(0xFF, 0xAA, 0xAA), (0x0F, 0xAA, 0x0A), (0x00, 0xAA, 0x00)]:
        bound = substitute(
            out,
            (input_vars[0], BitVecVal(x, 8)),
            (hole_vars[0], BitVecVal(c, 8)),
        )
        assert simplify(bound).as_long() == expected
