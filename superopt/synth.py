from __future__ import annotations

from superopt.ir import Const, Hole, Instruction, Operand, Program


def _fill(sketch: Program, holes: dict[int, int]) -> Program:
    def resolve(operand: Operand) -> Operand:
        if isinstance(operand, Hole):
            return Const(holes[operand.id])
        return operand

    instructions = tuple(
        Instruction(instruction.op, tuple(resolve(o) for o in instruction.operands))
        for instruction in sketch.instructions
    )
    return Program(sketch.width, instructions, resolve(sketch.output))
