from __future__ import annotations

from superopt.ir import (
    ARITY,
    Const,
    Hole,
    InputRef,
    Instruction,
    Op,
    Program,
    ResultRef,
)


def test_arity_declared_for_every_op():
    assert set(ARITY) == set(Op)
    assert all(ARITY[op] in (1, 2) for op in Op)


def test_operand_kinds_are_distinct():
    assert InputRef(0) != ResultRef(0)
    assert Const(5).value == 5
    assert InputRef(1).index == 1
    assert ResultRef(2).index == 2


def test_build_isolate_rmb_candidate():
    prog = Program(
        width=8,
        instructions=(
            Instruction(Op.NEG, (InputRef(0),)),
            Instruction(Op.AND, (InputRef(0), ResultRef(0))),
        ),
        output=ResultRef(1),
    )
    assert prog.width == 8
    assert len(prog.instructions) == 2
    assert prog.instructions[1].op is Op.AND
    assert prog.output == ResultRef(1)


def test_program_is_hashable():
    prog = Program(8, (Instruction(Op.NOT, (InputRef(0),)),), ResultRef(0))
    twin = Program(8, (Instruction(Op.NOT, (InputRef(0),)),), ResultRef(0))
    assert hash(prog) == hash(twin)
    assert len({prog, twin}) == 1


def test_hole_is_a_distinct_operand():
    assert Hole(0) != InputRef(0)
    assert Hole(0) != Const(0)
    assert Hole(0) != ResultRef(0)
    assert Hole(2).id == 2
    assert hash(Hole(1)) == hash(Hole(1))
