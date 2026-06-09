from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator
from itertools import combinations_with_replacement, product

from superopt.interp import execute
from superopt.ir import (
    ARITY,
    InputRef,
    Instruction,
    Op,
    Operand,
    Program,
    ResultRef,
)

COMMUTATIVE: frozenset[Op] = frozenset({Op.ADD, Op.MUL, Op.AND, Op.OR, Op.XOR})


def _infer_arity(spec: Callable[..., int]) -> int:
    try:
        params = inspect.signature(spec).parameters
    except (TypeError, ValueError):
        return 1
    count = sum(1 for name in params if name != "width")
    return count if count >= 1 else 1


def _operand_key(operand: Operand) -> tuple[int, int]:
    if isinstance(operand, InputRef):
        return (0, operand.index)
    if isinstance(operand, ResultRef):
        return (1, operand.index)
    raise TypeError(operand)


def _operand_pool(arity: int, slot: int) -> list[Operand]:
    pool: list[Operand] = [InputRef(i) for i in range(arity)]
    pool.extend(ResultRef(i) for i in range(slot))
    return pool


def _instruction_choices(arity: int, slot: int) -> Iterator[Instruction]:
    pool = _operand_pool(arity, slot)
    for op in Op:
        operand_arity = ARITY[op]
        if operand_arity == 1:
            for operand in pool:
                yield Instruction(op, (operand,))
        elif op in COMMUTATIVE:
            for left, right in combinations_with_replacement(pool, 2):
                yield Instruction(op, (left, right))
        else:
            for left, right in product(pool, repeat=2):
                yield Instruction(op, (left, right))


def _programs_of_length(arity: int, length: int) -> Iterator[tuple[Instruction, ...]]:
    if length == 0:
        yield ()
        return
    for prefix in _programs_of_length(arity, length - 1):
        for instruction in _instruction_choices(arity, length - 1):
            yield (*prefix, instruction)


def _is_fully_used(instructions: tuple[Instruction, ...]) -> bool:
    length = len(instructions)
    reachable = {length - 1}
    for slot in range(length - 1, -1, -1):
        if slot not in reachable:
            return False
        for operand in instructions[slot].operands:
            if isinstance(operand, ResultRef):
                reachable.add(operand.index)
    return True


def _matches(
    program: Program, spec: Callable[..., int], width: int, arity: int
) -> bool:
    space = range(1 << width)
    for inputs in product(space, repeat=arity):
        if execute(program, inputs) != spec(*inputs, width=width):
            return False
    return True


def enumerate_optimal(
    spec: Callable[..., int], width: int, max_len: int
) -> Program | None:
    arity = _infer_arity(spec)
    for index in range(arity):
        program = Program(width, (), InputRef(index))
        if _matches(program, spec, width, arity):
            return program
    for length in range(1, max_len + 1):
        output = ResultRef(length - 1)
        for instructions in _programs_of_length(arity, length):
            if not _is_fully_used(instructions):
                continue
            program = Program(width, instructions, output)
            if _matches(program, spec, width, arity):
                return program
    return None
