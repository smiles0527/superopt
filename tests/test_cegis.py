from __future__ import annotations

from superopt.benchmarks.isolate_rmb import isolate_rmb
from superopt.cegis import Library, _Assignment, _decode, synthesize
from superopt.equiv import Equivalent, equivalent
from superopt.fuzz import fuzz
from superopt.interp import execute
from superopt.ir import Const, InputRef, Instruction, Op, Program, ResultRef


def _isolate_rmb_spec(width: int) -> Program:
    return Program(
        width,
        (
            Instruction(Op.NEG, (InputRef(0),)),
            Instruction(Op.AND, (InputRef(0), ResultRef(0))),
        ),
        ResultRef(1),
    )


def test_decode_recovers_isolate_rmb_wiring():
    assignment = _Assignment(
        lo={0: 1, 1: 2},
        li={(0, 0): 0, (1, 0): 0, (1, 1): 1},
        consts={},
    )
    library = Library(ops=(Op.NEG, Op.AND))
    program = _decode(assignment, library, n_inputs=1, width=8)
    assert program == Program(
        8,
        (
            Instruction(Op.NEG, (InputRef(0),)),
            Instruction(Op.AND, (InputRef(0), ResultRef(0))),
        ),
        ResultRef(1),
    )


def test_decode_inlines_a_constant_slot():
    assignment = _Assignment(
        lo={0: 2},
        li={(0, 0): 0, (0, 1): 1},
        consts={0: 0x55},
    )
    library = Library(ops=(Op.AND,), n_constants=1)
    program = _decode(assignment, library, n_inputs=1, width=8)
    assert program == Program(
        8,
        (Instruction(Op.AND, (InputRef(0), Const(0x55))),),
        ResultRef(0),
    )


def test_synthesizes_isolate_rmb_at_8_bit():
    spec = _isolate_rmb_spec(8)
    library = Library(ops=(Op.NEG, Op.AND))
    result = synthesize(spec, library, seed=0)
    assert result is not None
    assert isinstance(equivalent(result, spec), Equivalent)
    for x in range(256):
        assert execute(result, (x,)) == execute(spec, (x,))
    assert fuzz(result, isolate_rmb, trials=20_000, seed=1) is None


def test_synthesizes_isolate_rmb_at_32_bit():
    spec = _isolate_rmb_spec(32)
    library = Library(ops=(Op.NEG, Op.AND))
    result = synthesize(spec, library, seed=0)
    assert result is not None
    assert isinstance(equivalent(result, spec), Equivalent)
    assert fuzz(result, isolate_rmb, trials=20_000, seed=1) is None


def test_returns_none_when_library_cannot_match():
    spec = _isolate_rmb_spec(8)
    library = Library(ops=(Op.AND,))
    assert synthesize(spec, library, seed=0) is None
