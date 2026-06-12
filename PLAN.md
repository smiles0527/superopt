# Superopt: implementation plan

A provably-optimal superoptimizer for short, loop-free integer and bitwise
routines. It uses Z3 for equivalence checking and CEGIS for synthesis, and the
aim is to rediscover a real *Hacker's Delight* trick by Phase 4 and measure a gap
against `-O3` by Phase 5.

The shape is plain Python. A program is a straight-line sequence of bit-vector
operations, an interpreter gives the reference semantics, an encoder lifts
programs into Z3 formulas, and an equivalence checker uses UNSAT as proof.
Brute-force enumeration is the Phase 3 MVP; the component-based CEGIS encoding
from Jha 2010 is Phase 4; an independent fuzzer is the trust check. The stack is
Python 3.11+, `z3-solver`, `pytest`, `ruff`, and `pyright`, with `hypothesis` as
a maybe in Phase 6.

Two textbooks sit under the early phases: Bradley and Manna's *The Calculus of
Computation* for the decision-procedure and bit-vector theory in Phase 2, and
Ben-Ari's *Mathematical Logic for Computer Science* for the logic behind the
Phase 0 "why UNSAT is a proof" question. Jha 2010 is the targeted read before
Phase 4. Citations are in `docs/references.md`.

One rule sits over all of it, from `CLAUDE.md`. I never commit a line I can't
explain. Claude can write complete code, including the core algorithms, but I
read every line and have to be able to defend it before it lands. This file is the spine;
`TIMELINE.md` logs what's done, and `SCHEDULE.md` puts the phases on a calendar.

---

## File map

The source lives in the `superopt/` package, installable with `pip install -e .`.
Standalone scripts go in `scripts/`, and the tests in `tests/`.

| File | Responsibility | First created in |
|---|---|---|
| `superopt/ir.py` | `Op` enum, `Instruction` and `Program` dataclasses: pure data, no logic | Phase 1 |
| `superopt/interp.py` | `execute(program, inputs) -> int`: reference semantics in Python | Phase 1 |
| `superopt/encode.py` | `encode(program) -> (input_vars, output_expr)`: `Op` to Z3 BitVec | Phase 2 |
| `superopt/equiv.py` | `equivalent(a, b) -> Equivalent \| Counterexample` | Phase 2 |
| `superopt/search.py` | Phase 3 enumeration driver, rewritten or wrapped for CEGIS in Phase 4 | Phase 3 |
| `superopt/cegis.py` | Component-based synth-query and verify-query (Jha 2010) | Phase 4 |
| `superopt/cost.py` | Per-opcode latency/throughput weights (only if I pursue Phase 5A) | Phase 5 |
| `superopt/fuzz.py` | Independent random-input oracle, no shared code with `encode.py` | Phase 6 |
| `superopt/benchmarks/` | Reference specs as Python functions | Phase 1 |
| `scripts/` | Standalone runners, comparisons, experiments | As needed |
| `tests/` | pytest suite: `test_interp.py`, `test_encoder_vs_interp.py`, and so on | Throughout |

The prose deliverables track alongside: `README.md` for whoever lands on the
repo, `DECISION_LOG.md` for me later and any reviewer, the Obsidian vault notes
under `notes/` as I read papers, and `report/report.md` as the final writeup.

---

## Phase 0: setup and the Z3 hello-world

Phase 0 is just a working environment and one proof that the whole idea holds up.
A venv with `z3-solver` and `pytest`, then the proof that matters, that `x*2` and
`x<<1` are the same for every 8-bit input. I write a handful of lines that assert
the *negation*, that the two differ, and expect Z3 to answer `unsat`. That `unsat`
means no input makes them differ, which is the project in miniature, a result
over all inputs instead of a sample of them. The script itself lives in gitignored
`scratch/` and doesn't really matter; what matters is that I can say in my own
words why `unsat` is a proof and not just evidence, written into `DECISION_LOG.md`.

To do:

- [x] venv with `z3-solver` and `pytest`; confirm `python --version` is 3.11+ and `import z3` works
- [ ] Write the hello-world myself: assert the negation of `x*2 == x<<1` on an 8-bit `BitVec`, expect `unsat` (a `sat` means I flipped the assertion)
- [ ] Write the "why is `unsat` a proof" entry in `DECISION_LOG.md`
- [ ] Load the auto-sync hooks with `/hooks`, then commit the log entry

**Done when** the proof prints `unsat`, I can explain why that proves equivalence, the first `DECISION_LOG.md` entry exists, and the hooks are live.

---

## Phase 1: the IR and the interpreter

Phase 1 builds the two things everything else stands on: a data structure for a
program, and a plain Python interpreter that runs it. The IR is already scaffolded
in `ir.py`, an `Op` enum, an `Operand` that's either an input, a constant, or a
reference to an earlier result, and a `Program` that carries its own width (8 bits
to start). The interpreter is a big match on the opcode that masks every
intermediate back down to width. The one real trap is arithmetic shift-right,
where Python's `>>` already does the arithmetic shift on negative ints but I'm
holding masked unsigned values, so I sign-extend, shift, then mask back. That
decision goes in `notes/encodings/shifts.md`.

To trust the interpreter I need something to check it against, so I write three
reference specs the obvious, trick-free way: popcount, absolute value, and
isolate-rightmost-bit. Writing them dumbly is the point, since the synthesizer is
supposed to discover the clever versions like `x & -x` later, on its own. Then I
build a hand-coded `Program` for each, run both the spec and the `Program` on ten
thousand random inputs, and check they agree.

To do:

- [x] Finish `interp.py`'s `execute()`, masking to width and handling the `ASHR` sign-extend trap
- [x] Write the three specs (`popcount`, `absval`, `isolate_rmb`) plainly, no tricks
- [x] Cross-check each spec against a hand-built `Program` on 10k random inputs
- [ ] First `README.md` draft, and log the IR and `ASHR` choices

**Done when** `test_interp.py` is green and all three specs match their hand-built programs on 10k inputs.

---

## Phase 2: the encoder and the equivalence check

This is where the project gets its teeth. I lift a `Program` into a Z3 BitVec
formula and use it to prove two programs equal, and it's the first place a subtle
bug does real damage, so the encoder gets cross-checked against the interpreter
before I trust it for anything.

The encoder goes one opcode at a time, and a few are traps. Logical shift-right
has to be `LShR(x, y)`, not Z3's `>>` (that one's arithmetic), and getting it
wrong quietly corrupts every program that touches it. Multiply wraps on its own
at fixed width, negate is just `-x`, and constants become `BitVecVal(c, width)`
with the width spelled out, never an implicit Python int. Then the cross-check,
the part `CLAUDE.md` calls non-negotiable and I agree with. A thousand random
programs, a hundred random inputs each, interpreter against formula, and every
one of the hundred thousand has to agree. After that `equivalent(a, b)` is short,
assert the inputs equal and the outputs different, ask Z3, and read `unsat` as
"equivalent" and `sat` as a counterexample.

To do:

- [x] Build the random-program generator and run the 100k interpreter-vs-encoder cross-check
- [x] Write `equivalent()`, returning `Equivalent` or a `Counterexample`
- [x] Prove `x + x ≡ x << 1`, and confirm a wrong pair gives a counterexample that actually diverges
- [x] Encode each opcode (shift/overflow settled in code; the `notes/encodings/` writeup is still pending)

**Done when** the cross-checks pass, `x + x ≡ x << 1` is equivalent, and a broken pair returns a real counterexample.

---

## Phase 3: the brute-force MVP

Phase 3 is the first time the thing actually superoptimizes, the slow,
obviously-correct way. I enumerate every program of length 1, then length 2, and
so on, checking each against the spec with the equivalence check from Phase 2.
Because I go shortest-first, the first program that matches is provably the
shortest there is, since everything below it was already ruled out. The
enumeration would explode without pruning, so I skip dead code, skip programs that
read undefined slots, and collapse commutative duplicates (`ADD(a, b)` and
`ADD(b, a)` are one program, not two).

The target is `isolate_rmb`. I expect the search to come back with a
two-instruction program, negate then and, which is exactly `x & -x`, reported as
optimal at length two because every length-one program failed first. This is the
de-risk milestone. If the slow method rediscovers a known trick and proves it
minimal, the interpreter, encoder, and equivalence stack are all sound, and I can
build CEGIS on top without wondering whether the foundation lies to me.

To do:

- [x] Enumerate shortest-first, pruning dead code, undefined slots, and commutative duplicates
- [x] Check each candidate against the spec (exhaustive interpretation at 8-bit, not `equivalent()`)
- [x] Run it on `isolate_rmb` and confirm it returns `x & -x`, reported as optimal at length 2
- [ ] Log the enumeration order, the pruning rules, and what "canonical" means in the IR

**Done when** `search.py` rediscovers `x & -x` for `isolate_rmb` and reports it as provably optimal at length 2. That's the de-risk checkpoint.

---

## Phase 4: CEGIS and component synthesis

Phase 4 is the real one, and the intellectual core. Instead of enumerating whole
programs, I describe a bag of components and let Z3 wire them together. Each
component input gets a location variable saying which earlier slot it reads from,
and a set of well-formedness constraints keeps the wiring honest: no component
reads from a later one, every slot is defined once, the output is the last result.
Those constraints are the off-by-one silent-bug zone, so I derive them on paper
and trace a three-component example by hand before writing any Z3.

The payoff, and the insight worth writing up, is constants. Brute force can only
try constants it thought to enumerate, but here a needed constant is just a free
`BitVec` variable the solver solves for, so it can invent a magic number I'd never
have guessed. The loop itself is guess-and-check. Synthesize a wiring that fits a
handful of example inputs, then verify it against the spec over all inputs; if
verify finds a counterexample, add it to the examples and synthesize again.
`unsat` on the verify query means done, and proven over every 32-bit input. I get
it working at 8 bits on `isolate_rmb` first, scale to 32, then point it at a real
Hacker's Delight function with a non-trivial constant (counting trailing zeros
with a De Bruijn sequence is the likely target) and watch it find the constant on
its own.

Before starting I read Jha, Gulwani, Seshia, and Tiwari (2010) twice, the CEGIS
chapter of Solar-Lezama's thesis, and skim Souper's README for reference, not to
copy.

The work splits in two. The first slice, 4a, is constants on a fixed sketch, and
it's done. A `Hole` operand stands in for an unknown constant, the encoder turns
each hole into a free `BitVec`, and a CEGIS loop solves for it over a few example
inputs, verifies the fit against the spec over all inputs, and refines on any
counterexample. Pointed at `x & C` it recovered `0xAAAAAAAA` over every 32-bit
input, checked by both `equivalent()` and the independent fuzzer, so the
free-constant insight is proven before any wiring exists. The second slice, 4b, is
the wiring itself, where the location variables let Z3 choose the program rather
than just fill a blank in one I handed it. The same loop drives it; what's new is
the component connection encoding and its well-formedness constraints.

To do:

- [x] Read Jha 2010 twice, with notes in `notes/papers/jha-2010.md`
- [x] Add a `Hole` operand and a hole-aware encoder, treating constants as free `BitVec` variables, never enumerated
- [x] Build the CEGIS loop on a fixed sketch and confirm it recovers a 32-bit constant, verified by equiv and the fuzzer
- [ ] Derive the location-variable and well-formedness constraints on paper, then encode them in `cegis.py`
- [ ] Extend the loop to choose the wiring: 8-bit on `isolate_rmb`, scale to 32-bit, then one real Hacker's Delight function with a constant
- [ ] Log the component design, the constraint derivation with the by-hand trace, and the free-constant insight

**Done when** a real Hacker's Delight function, constant and all, is synthesized over every 32-bit input and verified against the spec.

---

## Phase 5: stretch goals

Phase 5 only happens if there's time, and it's the first thing cut under pressure.
There are three directions, and I'd pick at most one or two. The defensible one,
the closest thing to a finding that's mine, is beating `-O3`. Write each spec in C,
compile with `gcc -O3` and `clang -O3`, count the instructions, run my tool on the
same specs, and document the cases where it comes out shorter. The second is a
latency cost model, where "optimal" stops meaning fewest instructions and starts
meaning lowest latency-weighted cost, which can flip the winner (one slow multiply
against three quick shifts). The third is neural-guided enumeration, training a
small model to order the candidates; I'd frame that strictly as applying a known
technique with a measured speedup, not as something new.

To do:

- [ ] Option B, the one I'd prioritize: C versions, `-O3` instruction counts, and a `results/compiler_gap.md` of concrete wins
- [ ] Option A: `cost.py` latency weights and a benchmark where length and latency disagree
- [ ] Option C: a small model to order candidates, measured against uniform enumeration, framed as applying prior work

**Done when** there's a results table for whatever I pursued, with exact benchmarks, numbers, and diffs.

---

## Phase 6: the fuzzer and the writeup

Phase 6 is the trust layer and the story. The fuzzer is deliberately dumb and
deliberately independent. It imports the reference specs and the programs my tool
called optimal, runs both on millions of random inputs, and reports any
divergence. The whole point is that it shares no code with the encoder, so it
catches an encoding bug that the encoder-based equivalence check would be blind
to. Every program the tool has ever emitted has to pass at 100%.

The writeup in `report/report.md` is the paper-style version: background and prior
work, the approach, an implementation walk through the interesting pieces, an
evaluation table, a discussion of what's still open, and an honest framing of
what's standard versus what's mine. The last pass is reading it cold, as if I'd
never seen the project, and cutting anything that overclaims.

To do:

- [ ] Write `fuzz.py` from scratch, sharing no code with `encode.py` or `equiv.py`; run it on every emitted program at 100%
- [ ] Draft `report/report.md`: background, approach, implementation, evaluation, discussion, honest framing, reproducibility
- [ ] Read it cold and cut the overclaims

**Done when** the fuzzer passes 100% on every result and the report is reviewed and something I'm proud of.

---

## Writeup deliverables

The prose that accrues across the phases, tracked in one place.

- [ ] `README.md`: Phase 1 draft, Phase 6 polish
- [ ] `DECISION_LOG.md`: ongoing, at least one entry per phase
- [ ] `notes/papers/jha-2010.md`: stub exists, deepen in Phase 4
- [ ] `notes/encodings/shifts.md`: stub exists, fill in during Phase 2
- [ ] `notes/encodings/overflow.md`: create in Phase 2
- [ ] `notes/encodings/cegis-constraints.md`: create in Phase 4, hand-deriving the connection constraints
- [ ] `results/compiler_gap.md`: create in Phase 5B if I pursue it
- [ ] `report/report.md`: Phase 6
