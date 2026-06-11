from __future__ import annotations

from z3 import BitVecVal, Solver, sat, substitute

from superopt.encode import encode_sketch
from superopt.interp import execute
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


def _finite_synthesis(
    sketch: Program, spec: Program, examples: list[tuple[int, ...]]
) -> dict[int, int] | None:
    input_vars, hole_vars, out = encode_sketch(sketch)
    width = sketch.width
    solver = Solver()
    for example in examples:
        bindings = [
            (var, BitVecVal(value, width))
            for var, value in zip(input_vars, example, strict=True)
        ]
        bound_out = substitute(out, *bindings) if bindings else out
        solver.add(bound_out == BitVecVal(execute(spec, example), width))
    if solver.check() != sat:
        return None
    model = solver.model()
    return {
        h: model.eval(var, model_completion=True).as_long()
        for h, var in hole_vars.items()
    }
