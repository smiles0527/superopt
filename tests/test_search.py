from __future__ import annotations

from superopt.benchmarks import isolate_rmb, popcount
from superopt.interp import execute
from superopt.ir import InputRef, Op, Program, ResultRef
from superopt.search import _programs_of_length, enumerate_optimal


def test_isolate_rmb_rediscovers_two_instruction_trick():
    program = enumerate_optimal(isolate_rmb, 8, 4)

    assert program is not None
    assert len(program.instructions) == 2


def test_isolate_rmb_result_matches_spec_on_all_inputs():
    program = enumerate_optimal(isolate_rmb, 8, 4)

    assert program is not None
    assert all(execute(program, (x,)) == isolate_rmb(x, 8) for x in range(256))


def test_isolate_rmb_is_neg_then_and():
    program = enumerate_optimal(isolate_rmb, 8, 4)

    assert program is not None
    neg, conj = program.instructions
    assert neg.op is Op.NEG
    assert neg.operands == (InputRef(0),)
    assert conj.op is Op.AND
    assert set(conj.operands) == {InputRef(0), ResultRef(0)}
    assert program.output == ResultRef(1)


def test_no_single_instruction_program_matches_isolate_rmb():
    for instructions in _programs_of_length(1, 1):
        program = Program(8, instructions, ResultRef(0))
        assert any(execute(program, (x,)) != isolate_rmb(x, 8) for x in range(256))


def test_returns_none_when_max_len_too_small():
    assert enumerate_optimal(popcount, 8, 1) is None


def test_identity_spec_is_optimal_at_zero_instructions():
    program = enumerate_optimal(lambda x, width: x & ((1 << width) - 1), 8, 4)

    assert program is not None
    assert program.instructions == ()
    assert program.output == InputRef(0)


def test_two_input_and_spec_found_at_length_one():
    program = enumerate_optimal(lambda a, b, width: a & b, 4, 2)

    assert program is not None
    assert len(program.instructions) == 1
    assert program.instructions[0].op is Op.AND
    assert all(execute(program, (a, b)) == a & b for a in range(16) for b in range(16))
