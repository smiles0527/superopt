from __future__ import annotations

from typing import assert_never

from z3 import BitVec, BitVecRef, BitVecVal, LShR

from superopt.ir import Const, Hole, InputRef, Op, Operand, Program, ResultRef


def _input_arity(program: Program) -> int:
    arity = 0
    for instruction in program.instructions:
        for operand in instruction.operands:
            if isinstance(operand, InputRef):
                arity = max(arity, operand.index + 1)
    if isinstance(program.output, InputRef):
        arity = max(arity, program.output.index + 1)
    return arity


def apply(op: Op, args: list[BitVecRef]) -> BitVecRef:
    match op:
        case Op.ADD:
            return args[0] + args[1]
        case Op.SUB:
            return args[0] - args[1]
        case Op.MUL:
            return args[0] * args[1]
        case Op.AND:
            return args[0] & args[1]
        case Op.OR:
            return args[0] | args[1]
        case Op.XOR:
            return args[0] ^ args[1]
        case Op.NOT:
            return ~args[0]
        case Op.NEG:
            return -args[0]
        case Op.SHL:
            return args[0] << args[1]
        case Op.LSHR:
            return LShR(args[0], args[1])
        case Op.ASHR:
            return args[0] >> args[1]
    assert_never(op)


def _hole_ids(program: Program) -> list[int]:
    ids: set[int] = set()
    for instruction in program.instructions:
        for operand in instruction.operands:
            if isinstance(operand, Hole):
                ids.add(operand.id)
    if isinstance(program.output, Hole):
        ids.add(program.output.id)
    return sorted(ids)


def encode_sketch(
    program: Program,
) -> tuple[list[BitVecRef], dict[int, BitVecRef], BitVecRef]:
    width = program.width
    input_vars = [BitVec(f"in{i}", width) for i in range(_input_arity(program))]
    hole_vars = {h: BitVec(f"hole{h}", width) for h in _hole_ids(program)}
    results: list[BitVecRef] = []

    def value(operand: Operand) -> BitVecRef:
        match operand:
            case InputRef(index=i):
                return input_vars[i]
            case Const(value=v):
                return BitVecVal(v, width)
            case ResultRef(index=i):
                return results[i]
            case Hole(id=h):
                return hole_vars[h]
        assert_never(operand)

    for instruction in program.instructions:
        args = [value(operand) for operand in instruction.operands]
        results.append(apply(instruction.op, args))

    return input_vars, hole_vars, value(program.output)


def encode(program: Program) -> tuple[list[BitVecRef], BitVecRef]:
    input_vars, _, output = encode_sketch(program)
    return input_vars, output
