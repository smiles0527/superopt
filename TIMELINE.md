# Timeline

A running log of project milestones. Newest last.

## 2026-05

- **May 29.** Repo set up: working agreement, implementation plan, `.gitignore`,
  and tooling. The Obsidian notes vault was split into its own repository and
  synced separately, so vault churn never lands in the code history.
- **May 30.** Wrote the theory notes, a references/reading map, and a
  plain-English explainer. Stood up a MkDocs site that renders the notes locally.
- **May 31.** Reworked theory notes 00–05. Landed the project code scaffold:
  `ir.py` (the program data model), stubs for `interp`, `encode`, `equiv`, and
  `search`, the three benchmark specs, `pyproject.toml` with pytest config, and a
  green test for the IR. Started `DECISION_LOG.md`.

## 2026-06

- **June 6.** Drafted `SCHEDULE.md`, a dated calendar that runs the remaining
  phases from June through the end of August. It pins each phase to a window,
  marks the two danger zones (the Phase 2 encodings and the Phase 4 CEGIS
  constraints), and sets a degradation order that protects the encoder
  cross-check and the fuzzer if Phase 4 runs long. Added two background
  textbooks, Bradley and Manna's *The Calculus of Computation* and Ben-Ari's
  *Mathematical Logic for Computer Science*, to the references, and folded a
  two-track reading plan into the schedule, the textbooks alongside Phases 1–3 and
  Jha 2010 before Phase 4.
- **June 9.** Implemented the Phase 1 through 3 core and verified it end to end.
  `interp.py` runs the reference semantics; `encode.py` lifts programs to Z3,
  cross-checked against the interpreter on 100,000 random cases plus deterministic
  shift edge cases; `equiv.py` proves `x+x ≡ x<<1` and returns real
  counterexamples; and `search.py` rediscovers `x & -x` for `isolate_rmb` and
  reports it optimal at length 2, hitting the Phase 3 de-risk milestone. Also
  landed `fuzz.py`, the independent oracle, ahead of its Phase 6 slot. The suite
  is 49 tests, green and ruff-clean.
- **June 10.** Tightened the earlier phases and built the first slice of Phase 4.
  The polish came first: `fuzz.py` now takes its input arity from the spec rather
  than the candidate program, so a program that ignores an argument can no longer
  shrink the fuzz domain and hide a divergence; a Program-hashing test went in; and
  the synthesis quantifier in the theory notes got corrected. Then Phase 4a,
  constant synthesis on a fixed sketch. A new `Hole` operand stands in for an
  unknown constant, `encode.py` lifts each hole to a free `BitVec`, and a CEGIS
  loop in `synth.py` solves for it over a handful of example inputs, verifies the
  fit against the spec over all inputs, and feeds any counterexample back in.
  Pointed at `x & C` it recovered `0xAAAAAAAA` across every 32-bit input, confirmed
  independently by `equivalent()` and the fuzzer. That is the free-constant insight
  working end to end, a magic number the solver found on its own instead of one I
  enumerated. The suite is 61 tests, green and ruff-clean.
- **June 17.** Built Phase 4b, component synthesis, the intellectual core. `cegis.py`
  encodes a program as Jha 2010 location variables: each operation gets an output
  line and input lines, well-formedness keeps the wiring an acyclic
  single-definition DAG, and a connection constraint ties each input to the line it
  reads. The 4a CEGIS loop drives it, now solving for the wiring and the constants
  at once, and a decoder reads the solver's model back into a `Program`. It
  rediscovers `x & -x` from a bag of NEG and AND at 8 and 32 bits, recovers a mask
  constant inside a wiring, and even invents a shift amount, each checked by both the
  proof and the fuzzer. Three levers went in to make the search finish: bit-vector
  locations, symmetry breaking on interchangeable parts, and pinning structural
  constants. The honest result is a measured frontier. Full SWAR popcount does not
  converge even with every lever, because the per-round synthesis cost explodes as
  counterexamples accumulate, running 0.06s up to 27s over five examples and then
  falling off a cliff. The two popcount rungs stay marked `slow` and deselected,
  documenting the wall; the seven that pass prove the technique. The suite runs 68
  green by default, ruff-clean.
