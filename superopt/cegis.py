from __future__ import annotations

import random
from dataclasses import dataclass

from z3 import (
    And,
    ArithRef,
    BitVec,
    BitVecRef,
    BitVecVal,
    BoolRef,
    Distinct,
    Implies,
    Int,
    Solver,
    sat,
)

from superopt.encode import apply, encode_sketch
from superopt.equiv import Equivalent, equivalent
from superopt.interp import execute
from superopt.ir import (
    ARITY,
    Const,
    InputRef,
    Instruction,
    Op,
    Program,
    ResultRef,
)


@dataclass(frozen=True)
class Library:
    ops: tuple[Op, ...]
    n_constants: int = 0


@dataclass(frozen=True)
class _Assignment:
    lo: dict[int, int]
    li: dict[tuple[int, int], int]
    consts: dict[int, int]


def _decode(
    assignment: _Assignment, library: Library, n_inputs: int, width: int
) -> Program:
    ops = library.ops
    n_consts = library.n_constants
    n_lines = n_inputs + n_consts + len(ops)
    order = sorted(range(len(ops)), key=lambda k: assignment.lo[k])
    line_to_result = {assignment.lo[k]: pos for pos, k in enumerate(order)}

    def operand(line: int) -> Const | InputRef | ResultRef:
        if line < n_inputs:
            return InputRef(line)
        if line < n_inputs + n_consts:
            return Const(assignment.consts[line - n_inputs])
        return ResultRef(line_to_result[line])

    instructions = tuple(
        Instruction(
            ops[k],
            tuple(operand(assignment.li[(k, j)]) for j in range(ARITY[ops[k]])),
        )
        for k in order
    )
    return Program(width, instructions, ResultRef(line_to_result[n_lines - 1]))


def _wellformed(
    lo: dict[int, ArithRef],
    li: dict[tuple[int, int], ArithRef],
    n_inputs: int,
    n_consts: int,
    n_lines: int,
) -> BoolRef:
    first_op_line = n_inputs + n_consts
    clauses = []
    for var in lo.values():
        clauses.append(var >= first_op_line)
        clauses.append(var < n_lines)
    for var in li.values():
        clauses.append(var >= 0)
        clauses.append(var < n_lines)
    op_lines = list(lo.values())
    if len(op_lines) >= 2:
        clauses.append(Distinct(*op_lines))
    for (k, _j), var in li.items():
        clauses.append(var < lo[k])
    return And(*clauses)


def _example(
    ops: tuple[Op, ...],
    lo: dict[int, ArithRef],
    li: dict[tuple[int, int], ArithRef],
    consts: dict[int, BitVecRef],
    inputs: tuple[int, ...],
    expected: int,
    n_inputs: int,
    n_consts: int,
    n_lines: int,
    width: int,
    e: int,
) -> BoolRef:
    out = {k: BitVec(f"o_{e}_{k}", width) for k in range(len(ops))}
    iv = {
        (k, j): BitVec(f"iv_{e}_{k}_{j}", width)
        for k, op in enumerate(ops)
        for j in range(ARITY[op])
    }
    clauses = []
    for k, op in enumerate(ops):
        args = [iv[(k, j)] for j in range(ARITY[op])]
        clauses.append(out[k] == apply(op, args))
    for (k, j), port in iv.items():
        for m in range(len(ops)):
            clauses.append(Implies(li[(k, j)] == lo[m], port == out[m]))
        for s in range(n_inputs):
            clauses.append(
                Implies(li[(k, j)] == s, port == BitVecVal(inputs[s], width))
            )
        for s in range(n_consts):
            clauses.append(
                Implies(li[(k, j)] == n_inputs + s, port == consts[s])
            )
    for m in range(len(ops)):
        clauses.append(
            Implies(lo[m] == n_lines - 1, out[m] == BitVecVal(expected, width))
        )
    return And(*clauses)


def _finite_synthesis(
    spec: Program,
    library: Library,
    examples: list[tuple[int, ...]],
    n_inputs: int,
    width: int,
) -> _Assignment | None:
    ops = library.ops
    n_consts = library.n_constants
    n_lines = n_inputs + n_consts + len(ops)
    lo = {k: Int(f"lo_{k}") for k in range(len(ops))}
    li = {
        (k, j): Int(f"li_{k}_{j}")
        for k, op in enumerate(ops)
        for j in range(ARITY[op])
    }
    consts = {s: BitVec(f"c_{s}", width) for s in range(n_consts)}
    solver = Solver()
    solver.add(_wellformed(lo, li, n_inputs, n_consts, n_lines))
    for e, inp in enumerate(examples):
        expected = execute(spec, inp)
        solver.add(
            _example(
                ops, lo, li, consts, inp, expected,
                n_inputs, n_consts, n_lines, width, e,
            )
        )
    if solver.check() != sat:
        return None
    model = solver.model()
    return _Assignment(
        lo={k: model.eval(lo[k], model_completion=True).as_long() for k in lo},
        li={kj: model.eval(li[kj], model_completion=True).as_long() for kj in li},
        consts={
            s: model.eval(consts[s], model_completion=True).as_long()
            for s in consts
        },
    )


def synthesize(
    spec: Program,
    library: Library,
    *,
    seed: int = 0,
    max_iters: int = 64,
) -> Program | None:
    width = spec.width
    n_inputs = len(encode_sketch(spec)[0])
    bound = 1 << width
    rng = random.Random(seed)
    examples: list[tuple[int, ...]] = [
        tuple(rng.randrange(bound) for _ in range(n_inputs))
    ]
    for _ in range(max_iters):
        assignment = _finite_synthesis(spec, library, examples, n_inputs, width)
        if assignment is None:
            return None
        program = _decode(assignment, library, n_inputs, width)
        result = equivalent(program, spec)
        if isinstance(result, Equivalent):
            return program
        examples.append(result.inputs)
    raise RuntimeError("CEGIS did not converge within max_iters")
