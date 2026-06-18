# superopt

A superoptimizer for short, loop-free integer and bitwise routines. Hand it a
small function and it searches for the shortest equivalent program, then proves
there's nothing shorter. Not "a bit faster," but provably optimal under a fixed
instruction set. For the from-scratch version that assumes no background, read
[docs/explainer.md](docs/explainer.md).

## The idea

An ordinary compiler at `-O3` applies a big bag of heuristic rewrites. It makes
your code faster but never claims it found the best version. Superoptimization,
going back to Massalin in 1987, asks the harder question: out of *all* programs,
which is the shortest one that computes this function? The classic party trick
is rediscovering something like `x & -x` (isolate the lowest set bit) from
nothing, and certifying that no shorter sequence does the same job.

The catch is the word "equivalent." Two programs are equivalent only if they
agree on *every* input, and you can't check that by running them. A single
32-bit input already means four billion cases, and it gets worse fast with more
arguments. So instead of running anything, superopt encodes each program as a
bit-vector formula and hands it to the Z3 SMT solver, asking the question
backwards:

> Is there *any* input where these two programs disagree?

If Z3 says unsat (unsatisfiable), no such input exists, which means the programs
are equal everywhere. That's the proof. If it says sat, it hands back the exact
input where they differ, which is a gift when you're debugging. This backwards
framing is the whole foundation. Once it clicks for one pair of programs it
scales to all of them.

Finding the optimal program comes in two flavors. The brute-force version
enumerates programs by length (all of length 1, then 2, then 3) and asks Z3
"equivalent?" for each. The first length that matches is optimal by
construction. It's slow but obviously correct, which is exactly why it comes
first: it proves the interpreter, the encoder, and the equivalence check all
agree before anything clever gets layered on. The clever version is CEGIS
(counterexample-guided inductive synthesis, from Jha et al. 2010): synthesize a
program that works on a handful of example inputs, verify it against all inputs
with Z3, and feed any counterexample back as a new example. It converges fast
because every counterexample rules out a huge slice of wrong programs.

One thing that falls out of the SMT approach genuinely surprised me: a constant
isn't something you have to guess. In the formula it's just a free variable the
solver gets to pick, so Z3 can *solve* for the magic number that makes a program
correct, something brute-force enumeration could never stumble onto.

## Status and scope

Phases 1 through 4 and the independent fuzzer are done and verified:

- the reference interpreter,
- the Z3 encoder, cross-checked against the interpreter on 100,000 random cases,
- the equivalence checker, with counterexample extraction,
- brute-force search, which rediscovers `x & -x` for isolate-rightmost-bit and
  proves it optimal at length 2 (the de-risk milestone),
- a random-input fuzzer written without reusing the encoder,
- CEGIS constant synthesis (Phase 4a): the solver treats a program's constants as
  free bit-vector variables and solves for them, which recovered the magic number
  `0xAAAAAAAA` over all 32-bit inputs, something enumeration can never reach,
- component synthesis (Phase 4b): the Jha 2010 location-variable encoding, where
  the solver wires a fixed bag of operations into a program. It rediscovers
  `x & -x`, recovers a mask constant and even a shift amount on its own, and
  verifies the result over all inputs.

The suite runs 68 tests green by default, and every synthesized program clears
both layers, the SMT proof and the independent fuzzer.

One result is worth stating plainly. Full SWAR population count is the measured
ceiling of the component synthesizer. Even at 8-bit, with bit-vector locations,
symmetry breaking, and the shift amounts pinned so only the masks stay free, CEGIS
does not converge: the per-round synthesis cost explodes as counterexamples pile up,
running 0.06s, 0.1s, 3.9s, 11s, 27s over the first five examples and then falling off
a cliff. The two popcount rungs stay in the suite marked `slow`, deselected by
default and runnable with `pytest -m slow`, documenting both the target and the wall.
The seven rungs that pass prove the technique end to end.

Phase 5 is next, the stretch goals. The most defensible is measuring concrete wins
against `-O3`, with a latency cost model or neural-guided search as alternates.

Deliberately out of scope for now: floating point, memory and loads/stores,
loops and branches, and multi-output programs. Each one is its own research
project; the single-output, loop-free, integer case comes first.

## Run it

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -e ".[dev]"
pytest
```

`pytest` should report 68 passed, with 2 popcount rungs deselected as `slow`.

## Notes

The study notes (superoptimization theory, SMT and bit-vectors,
equivalence-via-unsat, CEGIS, the Jha 2010 reading) live in a separate
repository, so the Obsidian auto-sync churn never clutters this one's history:

**→ [github.com/smiles0527/superopt-notes](https://github.com/smiles0527/superopt-notes)**

They're also checked out locally at `notes/` (gitignored here) as an Obsidian
vault. Edit them there; the `obsidian-git` plugin syncs them to the notes repo
on its own. A fresh clone of this project that wants the notes should also
`git clone` the notes repo into `notes/`. A clean, read-only snapshot lives
under [docs/notes/](docs/notes/), browsable on GitHub, alongside the
[plain-English explainer](docs/explainer.md) and the
[references](docs/references.md).

## Honest framing

The synthesis technique here (CEGIS, component-based encoding) isn't novel. It
goes back to Jha et al. 2010 and Solar-Lezama's sketching work, both cited in
the references. What's mine is the IR design, the encoder, the implementation,
and the evaluation.
