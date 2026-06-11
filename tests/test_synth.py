from __future__ import annotations

from superopt.equiv import Equivalent, equivalent
from superopt.interp import execute
from superopt.ir import Const, Hole, InputRef, Instruction, Op, Program, ResultRef
from superopt.synth import _fill, _finite_synthesis, synthesize_constants


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


def test_finite_synthesis_pins_the_constant():
    holes = _finite_synthesis(_and_sketch(8), _mask_spec(8), [(0xFF,)])
    assert holes == {0: 0xAA}


def test_finite_synthesis_returns_none_when_unsatisfiable():
    holes = _finite_synthesis(_or_sketch(8), _mask_spec(8), [(0xFF,)])
    assert holes is None


def test_synthesizes_wide_mask_at_8_bit():
    spec = _mask_spec(8)
    result = synthesize_constants(_and_sketch(8), spec, seed=0)
    assert result is not None
    assert isinstance(equivalent(result, spec), Equivalent)
    for x in range(256):
        assert execute(result, (x,)) == execute(spec, (x,))


def test_synthesizes_wide_mask_at_32_bit():
    spec = _mask_spec(32)
    result = synthesize_constants(_and_sketch(32), spec, seed=0)
    assert result is not None
    assert isinstance(equivalent(result, spec), Equivalent)
    const = result.instructions[0].operands[1]
    assert isinstance(const, Const)
    assert const.value == 0xAAAAAAAA


def test_returns_none_when_no_constant_works():
    result = synthesize_constants(_or_sketch(8), _mask_spec(8), seed=0)
    assert result is None
