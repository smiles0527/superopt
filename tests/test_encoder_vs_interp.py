from __future__ import annotations

import random
from collections.abc import Sequence

import pytest
from z3 import BitVecVal, simplify, substitute

from superopt.encode import encode
from superopt.interp import execute
from superopt.ir import Const, InputRef, Instruction, Op, Operand, Program, ResultRef

WIDTH = 8
ARITY = 2
MAX_LEN = 6
NUM_PROGRAMS = 1000
NUM_INPUTS = 100
CONST_POOL = (0, 1, 2, 3, 7, 8, 127, 128, 255)
OPS = tuple(Op)
SIGN_BIT = 1 << (WIDTH - 1)

SHIFT_EDGE_CASES = [
    (Op.ASHR, 0x80, 1, 0xC0),
    (Op.ASHR, 0x80, 7, 0xFF),
    (Op.ASHR, 0x80, 8, 0xFF),
    (Op.ASHR, 0x80, 9, 0xFF),
    (Op.ASHR, 0x7F, 1, 0x3F),
    (Op.ASHR, 0x7F, 8, 0x00),
    (Op.LSHR, 0x80, 1, 0x40),
    (Op.LSHR, 0x80, 8, 0x00),
    (Op.SHL, 0x01, 7, 0x80),
    (Op.SHL, 0x01, 8, 0x00),
    (Op.SHL, 0xFF, 4, 0xF0),
]


def _random_operand(rng: random.Random, result_count: int) -> Operand:
    choices = ["input", "const"]
    if result_count > 0:
        choices.append("result")
    kind = rng.choice(choices)
    if kind == "input":
        return InputRef(rng.randrange(ARITY))
    if kind == "const":
        return Const(rng.choice(CONST_POOL))
    return ResultRef(rng.randrange(result_count))


def _random_program(rng: random.Random) -> Program:
    length = rng.randint(1, MAX_LEN)
    instructions: list[Instruction] = []
    for index in range(length):
        op = rng.choice(OPS)
        arity = 1 if op in (Op.NOT, Op.NEG) else 2
        operands = tuple(_random_operand(rng, index) for _ in range(arity))
        instructions.append(Instruction(op, operands))
    output = _random_operand(rng, length)
    return Program(WIDTH, tuple(instructions), output)


def _evaluate(program: Program, inputs: Sequence[int]) -> int:
    input_vars, output_expr = encode(program)
    bindings = [
        (var, BitVecVal(val, WIDTH))
        for var, val in zip(input_vars, inputs, strict=False)
    ]
    return simplify(substitute(output_expr, *bindings)).as_long()


def test_encoder_matches_interpreter() -> None:
    program_rng = random.Random(0xC0FFEE)
    input_rng = random.Random(0x1234)
    checks = 0
    ops_seen: set[Op] = set()
    saw_sign_bit_input = False
    for _ in range(NUM_PROGRAMS):
        program = _random_program(program_rng)
        ops_seen.update(instruction.op for instruction in program.instructions)
        input_pairs = [
            (input_rng.randrange(256), input_rng.randrange(256))
            for _ in range(NUM_INPUTS)
        ]
        for inputs in input_pairs:
            if inputs[0] & SIGN_BIT or inputs[1] & SIGN_BIT:
                saw_sign_bit_input = True
            expected = execute(program, inputs)
            actual = _evaluate(program, inputs)
            assert actual == expected, (program, inputs, expected, actual)
            checks += 1
    assert checks == NUM_PROGRAMS * NUM_INPUTS
    assert ops_seen == set(Op)
    assert max(CONST_POOL) >= WIDTH
    assert saw_sign_bit_input


@pytest.mark.parametrize(("op", "x", "shift", "expected"), SHIFT_EDGE_CASES)
def test_encoder_matches_interpreter_on_shift_edge_cases(
    op: Op, x: int, shift: int, expected: int
) -> None:
    program = Program(
        WIDTH,
        (Instruction(op, (InputRef(0), Const(shift))),),
        ResultRef(0),
    )
    assert execute(program, (x,)) == expected
    assert _evaluate(program, (x,)) == expected
