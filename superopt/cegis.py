from __future__ import annotations

import random
from dataclasses import dataclass

from z3 import (
    UGE,
    ULE,
    ULT,
    And,
    BitVec,
    BitVecRef,
    BitVecVal,
    BoolRef,
    Distinct,
    Implies,
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

COMMUTATIVE: frozenset[Op] = frozenset(
    {Op.ADD, Op.MUL, Op.AND, Op.OR, Op.XOR}
)


@dataclass(frozen=True)
class Library:
    ops: tuple[Op, ...]
    n_constants: int = 0
    fixed_constants: tuple[int, ...] = ()


@dataclass(frozen=True)
class _Assignment:
    lo: dict[int, int]
    li: dict[tuple[int, int], int]
    consts: dict[int, int]


def _decode(
    assignment: _Assignment, library: Library, n_inputs: int, width: int
) -> Program:
    ops = library.ops
    n_consts = library.n_constants + len(library.fixed_constants)
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
    ops: tuple[Op, ...],
    lo: dict[int, BitVecRef],
    li: dict[tuple[int, int], BitVecRef],
    n_inputs: int,
    n_consts: int,
    n_lines: int,
) -> BoolRef:
    first_op_line = n_inputs + n_consts
    clauses = []
    for var in lo.values():
        clauses.append(UGE(var, first_op_line))
        clauses.append(ULT(var, n_lines))
    for var in li.values():
        clauses.append(ULT(var, n_lines))
    op_lines = list(lo.values())
    if len(op_lines) >= 2:
        clauses.append(Distinct(*op_lines))
    for (k, _j), var in li.items():
        clauses.append(ULT(var, lo[k]))
    same_op: dict[Op, list[int]] = {}
    for k, op in enumerate(ops):
        same_op.setdefault(op, []).append(k)
    for indices in same_op.values():
        for a, b in zip(indices, indices[1:], strict=False):
            clauses.append(ULT(lo[a], lo[b]))
    for k, op in enumerate(ops):
        if op in COMMUTATIVE and ARITY[op] == 2:
            clauses.append(ULE(li[(k, 0)], li[(k, 1)]))
    return And(*clauses)


def _example(
    ops: tuple[Op, ...],
    lo: dict[int, BitVecRef],
    li: dict[tuple[int, int], BitVecRef],
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
    n_free = library.n_constants
    fixed = library.fixed_constants
    n_consts = n_free + len(fixed)
    n_lines = n_inputs + n_consts + len(ops)
    loc_width = max(1, (n_lines - 1).bit_length())
    lo = {k: BitVec(f"lo_{k}", loc_width) for k in range(len(ops))}
    li = {
        (k, j): BitVec(f"li_{k}_{j}", loc_width)
        for k, op in enumerate(ops)
        for j in range(ARITY[op])
    }
    free_consts = {s: BitVec(f"c_{s}", width) for s in range(n_free)}
    consts: dict[int, BitVecRef] = dict(free_consts)
    for s, value in enumerate(fixed):
        consts[n_free + s] = BitVecVal(value, width)
    solver = Solver()
    solver.add(_wellformed(ops, lo, li, n_inputs, n_consts, n_lines))
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
    const_values = {
        s: model.eval(free_consts[s], model_completion=True).as_long()
        for s in free_consts
    }
    for s, value in enumerate(fixed):
        const_values[n_free + s] = value
    return _Assignment(
        lo={k: model.eval(lo[k], model_completion=True).as_long() for k in lo},
        li={kj: model.eval(li[kj], model_completion=True).as_long() for kj in li},
        consts=const_values,
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
