from __future__ import annotations

from collections.abc import Sequence
from typing import assert_never

from superopt.ir import Const, InputRef, Op, Operand, Program, ResultRef


def execute(program: Program, inputs: Sequence[int]) -> int:
    width = program.width
    mask = (1 << width) - 1
    results: list[int] = []

    def value(operand: Operand) -> int:
        match operand:
            case InputRef(index=i):
                return inputs[i] & mask
            case Const(value=v):
                return v & mask
            case ResultRef(index=i):
                return results[i]
        assert_never(operand)

    for instruction in program.instructions:
        args = [value(operand) for operand in instruction.operands]
        results.append(_apply(instruction.op, args, width, mask))

    return value(program.output)


def _apply(op: Op, args: Sequence[int], width: int, mask: int) -> int:
    match op:
        case Op.ADD:
            return (args[0] + args[1]) & mask
        case Op.SUB:
            return (args[0] - args[1]) & mask
        case Op.MUL:
            return (args[0] * args[1]) & mask
        case Op.AND:
            return args[0] & args[1]
        case Op.OR:
            return args[0] | args[1]
        case Op.XOR:
            return args[0] ^ args[1]
        case Op.NOT:
            return ~args[0] & mask
        case Op.NEG:
            return -args[0] & mask
        case Op.SHL:
            return (args[0] << args[1]) & mask if args[1] < width else 0
        case Op.LSHR:
            return args[0] >> args[1] if args[1] < width else 0
        case Op.ASHR:
            signed = args[0] - (1 << width) if args[0] & (1 << (width - 1)) else args[0]
            if args[1] >= width:
                return mask if signed < 0 else 0
            return (signed >> args[1]) & mask
    assert_never(op)
