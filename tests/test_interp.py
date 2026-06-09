from __future__ import annotations

import pytest

from superopt.benchmarks import absval, isolate_rmb, popcount
from superopt.interp import execute
from superopt.ir import Const, InputRef, Instruction, Op, Operand, Program, ResultRef


def _single_op_program(width: int, op: Op, operands: tuple[Operand, ...]) -> Program:
    return Program(width, (Instruction(op, operands),), ResultRef(0))


def _sample_inputs(width: int) -> list[int]:
    mask = (1 << width) - 1
    fixed = [0, 1, 2, 3, 7, 42, 100, 255]
    boundaries = [0, 1, mask, mask >> 1, 1 << (width - 1)]
    return sorted({v & mask for v in fixed + boundaries})


def test_isolate_rmb_trick_matches_spec_over_all_inputs():
    prog = Program(
        8,
        (
            Instruction(Op.NEG, (InputRef(0),)),
            Instruction(Op.AND, (InputRef(0), ResultRef(0))),
        ),
        ResultRef(1),
    )

    results = [execute(prog, (x,)) for x in range(256)]

    assert results == [isolate_rmb(x, 8) for x in range(256)]


def test_add_self_equals_shift_left_one_over_all_8bit_inputs():
    add_prog = _single_op_program(8, Op.ADD, (InputRef(0), InputRef(0)))
    shl_prog = _single_op_program(8, Op.SHL, (InputRef(0), Const(1)))

    add_results = [execute(add_prog, (x,)) for x in range(256)]
    shl_results = [execute(shl_prog, (x,)) for x in range(256)]

    assert add_results == shl_results


@pytest.mark.parametrize("width", [8, 16, 32])
def test_add_self_equals_shift_left_one_across_widths(width: int):
    add_prog = _single_op_program(width, Op.ADD, (InputRef(0), InputRef(0)))
    shl_prog = _single_op_program(width, Op.SHL, (InputRef(0), Const(1)))

    for x in _sample_inputs(width):
        assert execute(add_prog, (x,)) == execute(shl_prog, (x,))


def test_ashr_sign_extends_while_lshr_zero_fills():
    ashr_prog = _single_op_program(8, Op.ASHR, (InputRef(0), Const(1)))
    lshr_prog = _single_op_program(8, Op.LSHR, (InputRef(0), Const(1)))

    ashr_result = execute(ashr_prog, (0x80,))
    lshr_result = execute(lshr_prog, (0x80,))

    assert ashr_result == 0xC0
    assert lshr_result == 0x40


def test_shl_by_full_width_is_zero():
    prog = _single_op_program(8, Op.SHL, (InputRef(0), Const(8)))

    result = execute(prog, (0xFF,))

    assert result == 0


def test_ashr_by_full_width_saturates_to_sign_bit():
    prog = _single_op_program(8, Op.ASHR, (InputRef(0), Const(8)))

    negative = execute(prog, (0x80,))
    positive = execute(prog, (0x7F,))

    assert negative == 0xFF
    assert positive == 0


def test_and_or_xor_basics():
    and_prog = _single_op_program(8, Op.AND, (InputRef(0), InputRef(1)))
    or_prog = _single_op_program(8, Op.OR, (InputRef(0), InputRef(1)))
    xor_prog = _single_op_program(8, Op.XOR, (InputRef(0), InputRef(1)))

    assert execute(and_prog, (0b1100, 0b1010)) == 0b1000
    assert execute(or_prog, (0b1100, 0b1010)) == 0b1110
    assert execute(xor_prog, (0b1100, 0b1010)) == 0b0110


def test_not_and_neg_basics():
    not_prog = _single_op_program(8, Op.NOT, (InputRef(0),))
    neg_prog = _single_op_program(8, Op.NEG, (InputRef(0),))

    assert execute(not_prog, (0x0F,)) == 0xF0
    assert execute(neg_prog, (1,)) == 0xFF
    assert execute(neg_prog, (0,)) == 0


def test_sub_and_mul_wrap_around():
    sub_prog = _single_op_program(8, Op.SUB, (InputRef(0), InputRef(1)))
    mul_prog = _single_op_program(8, Op.MUL, (InputRef(0), InputRef(1)))

    assert execute(sub_prog, (0, 1)) == 0xFF
    assert execute(mul_prog, (16, 16)) == 0
    assert execute(mul_prog, (3, 5)) == 15


def test_output_referencing_missing_result_raises():
    prog = Program(8, (), ResultRef(0))

    with pytest.raises(IndexError):
        execute(prog, (0,))


def test_instruction_referencing_own_slot_raises():
    prog = Program(
        8,
        (Instruction(Op.NOT, (ResultRef(0),)),),
        ResultRef(0),
    )

    with pytest.raises(IndexError):
        execute(prog, (0,))


def test_input_referencing_missing_slot_raises():
    prog = _single_op_program(8, Op.ADD, (InputRef(0), InputRef(1)))

    with pytest.raises(IndexError):
        execute(prog, (5,))


def test_spec_functions_return_known_values():
    assert popcount(0b1011, 8) == 3
    assert popcount(0xFF, 8) == 8
    assert absval(0x80, 8) == 0x80
    assert absval(0xFF, 8) == 1
    assert isolate_rmb(0b1100, 8) == 0b0100
    assert isolate_rmb(0, 8) == 0
