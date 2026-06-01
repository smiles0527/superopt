from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Op(StrEnum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    AND = "and"
    OR = "or"
    XOR = "xor"
    NOT = "not"
    NEG = "neg"
    SHL = "shl"
    LSHR = "lshr"
    ASHR = "ashr"


ARITY: dict[Op, int] = {
    Op.ADD: 2,
    Op.SUB: 2,
    Op.MUL: 2,
    Op.AND: 2,
    Op.OR: 2,
    Op.XOR: 2,
    Op.SHL: 2,
    Op.LSHR: 2,
    Op.ASHR: 2,
    Op.NOT: 1,
    Op.NEG: 1,
}


@dataclass(frozen=True)
class InputRef:
    index: int


@dataclass(frozen=True)
class Const:
    value: int


@dataclass(frozen=True)
class ResultRef:
    index: int


Operand = InputRef | Const | ResultRef


@dataclass(frozen=True)
class Instruction:
    op: Op
    operands: tuple[Operand, ...]


@dataclass(frozen=True)
class Program:
    width: int
    instructions: tuple[Instruction, ...]
    output: Operand
