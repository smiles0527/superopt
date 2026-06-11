from __future__ import annotations

from superopt.benchmarks import isolate_rmb
from superopt.fuzz import Divergence, fuzz
from superopt.interp import execute
from superopt.ir import Const, InputRef, Instruction, Op, Program, ResultRef

WIDTH = 8


def _isolate_rmb_program() -> Program:
    return Program(
        width=WIDTH,
        instructions=(
            Instruction(Op.NEG, (InputRef(0),)),
            Instruction(Op.AND, (InputRef(0), ResultRef(0))),
        ),
        output=ResultRef(1),
    )


def _wrong_program() -> Program:
    return Program(
        width=WIDTH,
        instructions=(Instruction(Op.OR, (InputRef(0), Const(1))),),
        output=ResultRef(0),
    )


def test_correct_program_has_no_divergence() -> None:
    result = fuzz(_isolate_rmb_program(), isolate_rmb, trials=10_000, seed=1)
    assert result is None


def test_wrong_program_reports_reproducible_divergence() -> None:
    program = _wrong_program()
    result = fuzz(program, isolate_rmb, trials=10_000, seed=1)

    assert isinstance(result, Divergence)
    assert execute(program, result.inputs) == result.program_output
    assert isolate_rmb(*result.inputs, WIDTH) == result.spec_output
    assert result.program_output != result.spec_output


def test_same_seed_is_deterministic() -> None:
    program = _wrong_program()
    first = fuzz(program, isolate_rmb, trials=10_000, seed=7)
    second = fuzz(program, isolate_rmb, trials=10_000, seed=7)
    assert first == second


def test_different_seeds_share_no_state() -> None:
    program = _isolate_rmb_program()
    assert fuzz(program, isolate_rmb, trials=10_000, seed=1) is None
    assert fuzz(program, isolate_rmb, trials=10_000, seed=2) is None


def test_arity_follows_spec_not_program() -> None:
    def first_of_two(a: int, b: int, width: int) -> int:
        return a & ((1 << width) - 1)

    program = Program(
        width=WIDTH,
        instructions=(Instruction(Op.NOT, (InputRef(0),)),),
        output=ResultRef(0),
    )
    result = fuzz(program, first_of_two, trials=200, seed=3)
    assert isinstance(result, Divergence)
    assert len(result.inputs) == 2
