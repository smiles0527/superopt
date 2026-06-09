from __future__ import annotations

from dataclasses import dataclass

from z3 import Solver, sat, unsat

from superopt.encode import encode
from superopt.ir import Program


@dataclass(frozen=True)
class Equivalent:
    pass


@dataclass(frozen=True)
class Counterexample:
    inputs: tuple[int, ...]


Result = Equivalent | Counterexample


def equivalent(a: Program, b: Program) -> Result:
    if a.width != b.width:
        raise ValueError(f"width mismatch: {a.width} != {b.width}")

    vars_a, out_a = encode(a)
    vars_b, out_b = encode(b)
    shared_vars = vars_a if len(vars_a) >= len(vars_b) else vars_b

    solver = Solver()
    solver.add(out_a != out_b)
    outcome = solver.check()

    if outcome == unsat:
        return Equivalent()

    if outcome == sat:
        model = solver.model()
        values = tuple(
            model.eval(var, model_completion=True).as_long() for var in shared_vars
        )
        return Counterexample(inputs=values)

    raise RuntimeError(f"solver returned {outcome}")
