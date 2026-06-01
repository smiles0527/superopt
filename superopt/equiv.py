from __future__ import annotations

from dataclasses import dataclass

from superopt.ir import Program


@dataclass(frozen=True)
class Equivalent:
    pass


@dataclass(frozen=True)
class Counterexample:
    inputs: tuple[int, ...]


Result = Equivalent | Counterexample


def equivalent(a: Program, b: Program) -> Result:
    raise NotImplementedError
