from __future__ import annotations

import pytest

from superopt.equiv import Counterexample, Equivalent, equivalent
from superopt.interp import execute
from superopt.ir import Const, InputRef, Instruction, Op, Operand, Program, ResultRef


def _single_op_program(width: int, op: Op, operands: tuple[Operand, ...]) -> Program:
    return Program(width, (Instruction(op, operands),), ResultRef(0))


def _add_self(width: int) -> Program:
    return _single_op_program(width, Op.ADD, (InputRef(0), InputRef(0)))


def test_add_self_is_equivalent_to_shift_left_one() -> None:
    add_prog = _add_self(8)
    shl_prog = _single_op_program(8, Op.SHL, (InputRef(0), Const(1)))

    assert isinstance(equivalent(add_prog, shl_prog), Equivalent)


def test_add_self_versus_shift_left_two_yields_real_counterexample() -> None:
    add_prog = _add_self(8)
    shl2_prog = _single_op_program(8, Op.SHL, (InputRef(0), Const(2)))

    result = equivalent(add_prog, shl2_prog)

    assert isinstance(result, Counterexample)
    assert execute(add_prog, result.inputs) != execute(shl2_prog, result.inputs)


def test_program_is_equivalent_to_itself() -> None:
    prog = _add_self(8)

    assert isinstance(equivalent(prog, prog), Equivalent)


def test_width_mismatch_raises_value_error() -> None:
    eight = _add_self(8)
    sixteen = _add_self(16)

    with pytest.raises(ValueError):
        equivalent(eight, sixteen)


def test_commuted_and_is_equivalent() -> None:
    forward = _single_op_program(8, Op.AND, (InputRef(0), InputRef(1)))
    swapped = _single_op_program(8, Op.AND, (InputRef(1), InputRef(0)))

    assert isinstance(equivalent(forward, swapped), Equivalent)


def test_two_input_counterexample_has_full_arity() -> None:
    and_prog = _single_op_program(8, Op.AND, (InputRef(0), InputRef(1)))
    or_prog = _single_op_program(8, Op.OR, (InputRef(0), InputRef(1)))

    result = equivalent(and_prog, or_prog)

    assert isinstance(result, Counterexample)
    assert len(result.inputs) == 2
    assert execute(and_prog, result.inputs) != execute(or_prog, result.inputs)


def test_constant_only_programs_compare_without_inputs() -> None:
    one = Program(8, (), Const(1))
    two = Program(8, (), Const(2))

    same = equivalent(one, Program(8, (), Const(1)))
    different = equivalent(one, two)

    assert isinstance(same, Equivalent)
    assert isinstance(different, Counterexample)
    assert different.inputs == ()
    assert execute(one, different.inputs) != execute(two, different.inputs)
