from __future__ import annotations

from superopt.cegis import Library, _Assignment, _decode
from superopt.ir import Const, InputRef, Instruction, Op, Program, ResultRef


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
