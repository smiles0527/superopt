# Superopt — Implementation Plan

> Authored under the **authorship rule** (see `CLAUDE.md`): never commit a line
> you can't explain. Claude may write complete code, including the core
> algorithms; the project owner reads every line and must be able to explain it
> before it's committed. Tasks use `- [ ]` for tracking. This plan is the spine;
> phase-specific subplans (e.g. a separate CEGIS plan) will be drafted when their
> phase arrives.

**Goal:** A provably-optimal superoptimizer for short, loop-free integer /
bitwise routines, using Z3 SMT for equivalence checking and CEGIS for
synthesis. Rediscover a real *Hacker's Delight* result by Phase 4, document
a measured gap against `gcc -O3` / `clang -O3` by Phase 5.

**Architecture:** Pure-Python. Programs = straight-line sequences of
bit-vector ops. An *interpreter* gives reference semantics; an *encoder*
lifts programs to Z3 BitVec formulas; an *equivalence checker* uses
UNSAT-as-proof. Brute-force enumeration is the Phase 3 MVP; CEGIS with
component-based encoding (Jha 2010) is Phase 4. An independent *fuzz
harness* is the trust check.

**Tech Stack:** Python 3.11+, `z3-solver`, `pytest`, `ruff`, `pyright`
(via the `pyright-lsp` Claude Code plugin), optional `hypothesis` in Phase 6.

---

## File map

### Code

| File | Responsibility | First created in |
|---|---|---|
| `ir.py` | `Op` enum, `Instruction` dataclass, `Program` dataclass — pure data, no logic | Phase 1 |
| `interp.py` | `execute(program, inputs, width) -> int` — reference semantics in Python | Phase 1 |
| `encode.py` | `encode(program, width) -> (input_vars, output_expr)` — `Op` → Z3 BitVec | Phase 2 |
| `equiv.py` | `equivalent(a, b, width) -> Equivalent \| Counterexample` | Phase 2 |
| `search.py` | Phase 3 enumeration driver; rewritten / wrapped for CEGIS in Phase 4 | Phase 3 |
| `cegis.py` | Component-based synth-query and verify-query (Jha 2010) | Phase 4 |
| `cost.py` | Per-opcode latency/throughput weights (only if Phase 5A pursued) | Phase 5 |
| `fuzz.py` | Independent random-input oracle, no shared code with `encode.py` | Phase 6 |
| `benchmarks/__init__.py` + spec files | Reference specs as Python functions | Phase 1 |
| `tests/` | pytest suite — `test_interp.py`, `test_encoder_vs_interp.py`, etc. | Throughout |

### Writeups

| File | Audience | When |
|---|---|---|
| `README.md` | Portfolio visitor, prof, recruiter | Drafted in Phase 1, refined in Phase 6 |
| `DECISION_LOG.md` | Future-you + reviewer | Entries added throughout, starting Phase 0 |
| `report/report.md` | The paper-style final writeup | Phase 6 |
| `notes/papers/*.md` | You (Obsidian vault) | As you read papers |
| `notes/encodings/*.md` | You (Obsidian vault) | Phase 2 onwards |

---

## Phase 0 — Setup + Z3 hello-world

**Goal:** Working venv, Z3 import, one UNSAT proof, first DECISION_LOG entry.

### Task 0.1 — Python env

**Files:** none committed (creates `venv/`, gitignored)

- [ ] Confirm `python --version` ≥ 3.11
- [ ] `python -m venv venv`
- [ ] Activate: `venv\Scripts\activate` (Windows) — prompt shows `(venv)`
- [ ] `pip install z3-solver pytest`
- [ ] Verify: `python -c "import z3; print(z3.get_version())"` prints a tuple

### Task 0.2 — Z3 hello-world (authorship-rule zone)

**Files:** `scratch/hello_z3.py` (`scratch/` is gitignored — the deliverable is your *understanding*, not the file)

- [ ] Write 5–8 lines: import `BitVec`, `Solver`, `unsat` from `z3`; make an 8-bit `BitVec`; add the *negation* of `x * 2 == x << 1` to a `Solver`; call `check()`. **Write it yourself, no copy-paste.**
- [ ] Run it; expect `unsat`
- [ ] If you got `sat`, you flipped the assertion direction — fix and retry
- [ ] In `DECISION_LOG.md`, write 2–4 sentences answering: *Why does UNSAT here constitute a proof of equivalence, not just evidence?* (Hint: the solver reasons over the symbolic value, not by enumerating concrete inputs.)

### Task 0.3 — Activate the auto-sync hooks

- [ ] Type `/hooks` in Claude Code (or restart) so it loads `.claude/settings.json`
- [ ] Commit `DECISION_LOG.md`:
  ```bash
  git add DECISION_LOG.md
  git commit -m "Phase 0: UNSAT proof of x*2 == x<<1, log first entry"
  git push
  ```
- [ ] Next time you end the Claude Code session, the SessionEnd hook should run and report "nothing to push" (you just pushed)

**Phase 0 done when:** Z3 hello-world prints `unsat`, you can explain *why* UNSAT proves equivalence, `DECISION_LOG.md` has its first entry, hooks are live.

---

## Phase 1 — IR + interpreter

**Goal:** Pure-Python representation of a program + reference interpreter,
cross-checked on 10,000 random inputs against hand-written spec functions.

### Files to create

- `ir.py` — `Op` enum (`ADD, SUB, MUL, AND, OR, XOR, NOT, NEG, SHL, LSHR, ASHR, CONST`); `Operand` (Input | Const | Result-of-instruction-N); `Instruction`; `Program` (ordered list + output index). Width parameter on `Program` (start at 8).
- `interp.py` — `execute(program, inputs, width) -> int`. Mask every intermediate value to width. Use Python's int arithmetic; for `ASHR`, sign-extend before shifting.
- `benchmarks/__init__.py` — empty
- `benchmarks/popcount.py` — `popcount(x: int, width: int) -> int`
- `benchmarks/abs_val.py` — `absval(x: int, width: int) -> int` (use the standard "branchless abs" trick later — but for the *spec*, write the obvious version)
- `benchmarks/isolate_rmb.py` — `isolate_rmb(x: int, width: int) -> int` (the spec: return x with all bits except its lowest set bit cleared; the trick `x & -x` comes later as a *candidate*, not the spec)
- `tests/__init__.py` — empty
- `tests/test_interp.py`

### Task 1.1 — IR (authorship-rule zone, but mostly mechanical)

- [ ] Define `Op` as a `StrEnum` or `IntEnum` — your call, document in `DECISION_LOG.md`
- [ ] Define `Operand` as a tagged union or three separate dataclasses; consistent serialization
- [ ] `Instruction(op, operands)`; `Program(width, instructions, output_index)`
- [ ] Hand-write 2 small example programs as `Program` literals in a docstring or scratch file — you'll need them for testing

### Task 1.2 — Interpreter

- [ ] Implement `execute(program, inputs, width)`. Big match on `op`. Mask every result with `(1 << width) - 1`. **`ASHR` is the danger spot** — Python's `>>` on negative ints does arithmetic shift, but you're working with masked unsigned ints. You'll need to sign-extend to signed Python int, shift, then mask back.
- [ ] Document the `ASHR` semantics choice in `notes/encodings/shifts.md` (the file already exists with the danger-zone warning — fill in your decision)

### Task 1.3 — Reference specs (authorship-rule zone)

- [ ] Write `popcount(x, width)` — obvious bit-counting loop, no tricks
- [ ] Write `absval(x, width)` — obvious branchful version
- [ ] Write `isolate_rmb(x, width)` — obvious loop, no tricks. The whole *point* is for the synthesizer to discover `x & -x` later.

### Task 1.4 — Tests (test code OK to draft together)

- [ ] `test_interp_spec_match` — for each spec function, build a hand-coded `Program` that *should* implement it, run both on 10,000 random `width`-bit inputs, assert they match
- [ ] `test_interp_undefined_behavior` — programs that reference undefined operand slots should raise, not silently produce garbage. (Decide what "undefined" means in your IR — document.)
- [ ] Run: `pytest tests/test_interp.py -v` — expect green

### Task 1.5 — Commit + writeup

- [ ] `README.md` first draft: 2 paragraphs explaining what the project is, current phase, how to run tests
- [ ] `DECISION_LOG.md` entries for: IR shape (tagged union vs single dataclass), `Op` enum representation, `ASHR` semantics
- [ ] Commit + push

**Phase 1 done when:** `pytest` green on `test_interp.py`, three benchmarks have spec functions matched by hand-coded `Program`s on 10k random inputs, `README.md` exists.

---

## Phase 2 — SMT encoder + equivalence

**Goal:** Lift programs to Z3 BitVec formulas. Cross-check the encoder
against the interpreter on random programs. Implement `equivalent()` and
verify it returns counterexamples on deliberately-mismatched program pairs.

### Files to create

- `encode.py` — `encode(program, width) -> (input_vars: list[BitVec], output_expr: BitVecRef)`
- `equiv.py` — `equivalent(a: Program, b: Program, width) -> Result` where `Result = Equivalent | Counterexample(inputs: list[int])`
- `tests/test_encode.py`
- `tests/test_encoder_vs_interp.py` — **the most important test in this project**

### Task 2.1 — Encoder (authorship-rule zone, danger zone)

- [ ] One Op at a time. For each Op, decide its Z3 expression. The danger spots:
  - `SHL` → `x << y` (logical) — but: what does Z3 do if `y` ≥ width? Find out, document.
  - `LSHR` → `LShR(x, y)` — *not* `>>` (which is arithmetic in Z3). Critical.
  - `ASHR` → `x >> y` (arithmetic in Z3)
  - `MUL` → standard, but wraparound is automatic for fixed-width BitVec
  - `NEG` → `-x`, equivalent to `~x + 1` on BitVec
- [ ] `CONST` operands become `BitVecVal(c, width)` — explicit width, never implicit int promotion
- [ ] Fill in `notes/encodings/shifts.md` with the answers you found
- [ ] Add a `notes/encodings/overflow.md` covering MUL wraparound, NEG of `INT_MIN`-equivalent (the negation-overflow case)

### Task 2.2 — Encoder-vs-interpreter cross-check

This test is non-negotiable per CLAUDE.md. Test design:

- [ ] Random program generator: small (length ≤ 6), random Ops, random valid operand wirings. Make it deterministic per-seed for reproducibility.
- [ ] For each generated program + each of 100 random concrete inputs:
  - Compute `interp_result = interp.execute(program, inputs, width=8)`
  - Compute `smt_result = solver.model().eval(encode(program).output_expr, substituting inputs)`
  - Assert equal
- [ ] Run 1000 random programs × 100 random inputs = 100k cross-checks
- [ ] If a mismatch fires, you have a wrong encoding — debug before going further

### Task 2.3 — Equivalence checker

- [ ] `equivalent(a, b, width)` builds both encodings, asserts inputs are equal and outputs are *not equal*, calls `check()`:
  - `unsat` → return `Equivalent`
  - `sat` → extract `model()`, read the input bit-vectors as concrete ints, return `Counterexample(inputs=[...])`
- [ ] Tests:
  - Positive: `x + x ≡ x << 1` returns `Equivalent`
  - Negative: a deliberately-wrong pair returns `Counterexample`; verify the returned input actually triggers the divergence by running both through the interpreter

### Task 2.4 — Commit + writeup

- [ ] DECISION_LOG entries: Z3 BitVec library choice, how you encode each Op, the cross-check methodology and its result
- [ ] Commit + push

**Phase 2 done when:** 100k random cross-checks pass, `equivalent` returns `Equivalent` on the `x+x ≡ x<<1` test, returns a verified `Counterexample` on a wrong pair.

---

## Phase 3 — Brute-force search MVP

**Goal:** A working superoptimizer that rediscovers a known optimal trick by
exhaustive enumeration up to the optimal length, and reports the optimality
proof.

### Files to create

- `search.py` — `enumerate_optimal(spec, width, max_len) -> Program | None`
- `tests/test_search.py`

### Task 3.1 — Enumeration

- [ ] For each length `n` from 1 upwards: enumerate all syntactic programs of length `n`. Each instruction picks an `Op` + valid operand sources (inputs or earlier results)
- [ ] Prune aggressively:
  - Skip dead code (a program's output must depend on every instruction transitively)
  - Skip non-canonical duplicates from commutativity (`ADD(a, b)` and `ADD(b, a)` are the same — enumerate only one)
  - Skip programs where an operand references an undefined slot
- [ ] For each surviving candidate, call `equivalent(candidate, spec_program, width)` (or build a spec-fn-based equivalence query — your call, document)
- [ ] First `n` at which a candidate succeeds → that program is *provably optimal*, because all shorter lengths were exhausted

### Task 3.2 — Rediscover a known trick

- [ ] Pick `isolate_rmb` as the target. Spec: the obvious branchful loop you wrote in Phase 1.
- [ ] Run `enumerate_optimal(isolate_rmb_spec, width=8, max_len=4)`
- [ ] Expect: a program of length 2 — `t0 = NEG(input_0); out = AND(input_0, t0)` — i.e. `x & -x`
- [ ] Report: "optimal at length 2 (all length-1 programs exhausted)"

### Task 3.3 — Tests + writeup

- [ ] `tests/test_search.py`:
  - `test_finds_xor_for_swap` or similar small known-optimal benchmark
  - `test_optimality_proof` — length-`N-1` enumeration exhausted before length-`N` succeeded
- [ ] DECISION_LOG: enumeration order, pruning rules, what "canonical form" means in your IR
- [ ] Commit + push

**Phase 3 done when:** `search.py` rediscovers `x & -x` for `isolate_rmb`, reports it as provably optimal at length 2.

**This is your de-risking milestone.** If this works, the SMT/interpreter/equivalence stack is sound, and you can build CEGIS on top with confidence.

---

## Phase 4 — CEGIS / component synthesis

**Goal:** Synthesize a real *Hacker's Delight* function over **all 32-bit
inputs**, including any required constants, via component-based CEGIS.

### Required reading before starting

- Jha, Gulwani, Seshia, Tiwari (2010) — read **twice**. Take notes in
  `notes/papers/jha-2010.md`.
- Solar-Lezama PhD thesis (2008), chapter on CEGIS
- Skim Souper's README for implementation reference (not for copying)

### Files to create

- `cegis.py` — synth-query and verify-query encodings (separate from `equiv.py`)
- `search.py` — updated to drive the CEGIS loop, sitting alongside (or replacing) the Phase 3 enumeration entry point
- `tests/test_cegis.py`

### Task 4.1 — Component-based encoding (authorship-rule zone, the intellectual core)

Sketch only — you derive and write this:

- [ ] Pick a component multiset for the target benchmark. Start small (e.g., for `isolate_rmb`: just `NEG, AND`)
- [ ] Encode the wiring: for each component input, a *location variable* names the slot it reads from
- [ ] Encode well-formedness constraints:
  - Acyclicity (no component reads from a later component)
  - Each slot defined at most once
  - Output is the last component's result
  - **This is the off-by-one silent-bug zone.** Derive it on paper *before* writing Z3 code. Trace through a 3-component example by hand.
- [ ] Treat any required constant as a free `BitVec` variable — *do not* enumerate constants. This is the single biggest reason CEGIS beats brute force. Write up the insight in DECISION_LOG.

### Task 4.2 — The CEGIS loop

- [ ] Start with a tiny example set: e.g., 5 random concrete inputs and their spec outputs
- [ ] **Synth query:** given the example set, find a wiring (and constant values) that satisfies all examples. If UNSAT, no program with this component multiset matches — try a larger one
- [ ] **Verify query:** given the synthesized wiring, ask Z3 for an input where it differs from the spec
- [ ] If verify returns UNSAT, you're done and proven correct over all 32-bit inputs
- [ ] If verify returns SAT, extract the counterexample, add it to the example set, re-synth

### Task 4.3 — Scale to 32-bit

- [ ] All BitVec widths bumped to 32 (parametrize so you can flip back to 8 for debugging)
- [ ] Run on `isolate_rmb` — should still find `x & -x`, now with the optimality argument quantifying over all `2^32` inputs

### Task 4.4 — Target a real Hacker's Delight function

- [ ] Pick one with a non-trivial constant — e.g., counting trailing zeros via De Bruijn sequence, or one of the bit-reversal tricks. Document the target choice in DECISION_LOG.
- [ ] Spec function in `benchmarks/`
- [ ] Run CEGIS; expect the synthesizer to discover any needed constants on its own
- [ ] If it doesn't terminate in reasonable time, the issue is *component multiset choice*, not the loop — iterate

### Task 4.5 — Tests + writeup

- [ ] `tests/test_cegis.py` — synth a known target end-to-end, asserting both correctness and the specific shape of the result
- [ ] DECISION_LOG entries: component multiset design, well-formedness constraint derivation (with the by-hand trace), free-constant insight, scaling notes
- [ ] Commit + push

**Phase 4 done when:** A real Hacker's Delight function (with constants) is synthesized over 32-bit inputs, verified equivalent to the spec.

---

## Phase 5 — Stretch goals (pick 1–2)

### Option A: Latency cost model

- [ ] `cost.py` — opcode → (latency, throughput) numbers, sourced from a public table (Agner Fog or Intel manuals)
- [ ] Search modified to optimize for latency-weighted total cost rather than instruction count
- [ ] Show a benchmark where length-vs-latency picks different winners (e.g., a 2-instruction sequence with one slow multiply vs a 3-instruction sequence of shifts/adds)
- [ ] DECISION_LOG: definition of "optimal" widened; what choice changes for which benchmarks

### Option B: Beat `-O3`

- [ ] Write each spec in C inside `benchmarks/c_versions/`
- [ ] Build a tiny script that compiles each with `gcc -O3` and `clang -O3`, extracts the asm, counts instructions
- [ ] Run your tool over the same specs, compare
- [ ] Cases your tool finds shorter/fewer instructions → write up in `results/compiler_gap.md` with concrete diffs
- [ ] **This is the defensible "new" finding** — invest writeup energy here

### Option C: Neural-guided enumeration

- [ ] Train a small model to predict which candidate programs to enumerate first
- [ ] Measure search-time speedup vs uniform enumeration on a held-out set
- [ ] Frame strictly as *application of a known technique* (neural-guided search), not as a new method. Cite the relevant prior work.
- [ ] Requires the `claude-api` plugin if using Claude as the model, OR a small local transformer (PyTorch)

**Phase 5 done when:** Documented results table for whichever options you pursued. Be specific — exact benchmarks, exact numbers, exact diffs.

---

## Phase 6 — Independent fuzz harness + final writeup

### Task 6.1 — Fuzz harness

- [ ] `fuzz.py` — a Python script that:
  - Imports the reference spec functions from `benchmarks/`
  - Imports the tool's "this is the optimal program" output
  - Runs both on millions of random inputs
  - Reports any divergence
- [ ] **Write `fuzz.py` without reusing any code from `encode.py` or `equiv.py`.** This is the independence point — it catches encoding bugs that would be invisible if the fuzzer used the same encoder
- [ ] Optionally: integrate `hypothesis` for property-based input generation
- [ ] Run over every "optimal" program the tool has ever emitted. Pass rate must be 100%.

### Task 6.2 — Final writeup

- [ ] `report/report.md` structured roughly as:
  1. **Background** — what superoptimization is, prior work (Massalin 1987, Souper, Jha 2010, Solar-Lezama). 1–2 pages.
  2. **Approach** — IR, encoder, equivalence-via-UNSAT, CEGIS with component encoding, free constants. Diagrams from Excalidraw if installed.
  3. **Implementation** — file walk, with code excerpts for the *interesting* pieces (encoder cases, CEGIS connection constraints). Not a tutorial.
  4. **Evaluation** — table of benchmarks rediscovered, length found, time-to-prove, comparison to compiler if Phase 5B
  5. **Discussion** — what surprised you, what's still open (loops, memory, floats, multi-output)
  6. **Honest framing** — what's standard (CEGIS, component encoding), what's yours (IR design, encoder, evaluation, any gap-against-`-O3` results). Cite Jha 2010 prominently.
  7. **Reproducibility** — venv setup, run commands, commit hash for the final result
- [ ] Source citations from `notes/papers/`
- [ ] Self-review: read it as if you'd never seen the project. Would a prof understand it? Does it overclaim? Edit.

**Phase 6 done when:** Fuzzer passes 100% on every result, `report/report.md` is reviewed and you're proud of it.

---

## Writeup deliverables — index

Tracking all the prose-output across phases in one place:

- [ ] `README.md` — Phase 1 draft, Phase 6 polish
- [ ] `DECISION_LOG.md` — ongoing, target ≥1 entry per phase
- [ ] `notes/papers/jha-2010.md` — initial stub exists, deepen in Phase 4
- [ ] `notes/encodings/shifts.md` — initial stub exists, fill in Phase 2
- [ ] `notes/encodings/overflow.md` — create in Phase 2
- [ ] `notes/encodings/cegis-constraints.md` — create in Phase 4, hand-derive the connection constraints
- [ ] `results/compiler_gap.md` — create in Phase 5B (if pursued)
- [ ] `report/report.md` — Phase 6

---

## Execution model

This plan is for **you** to own. Claude's role:

- **Explanation.** Z3 API, SMT theory, bitvec semantics, the CEGIS paper.
- **Implementation.** Claude can write complete code, including the encodings and CEGIS, for you to read, question, and be able to explain before it lands.
- **Test writing.** Test code describes behavior, not implementation. Claude can draft tests for your review.
- **Code review.** After each commit, ask for a `code-review` skill pass; before merging anything tricky, `requesting-code-review`.
- **Debugging.** When something fails, `systematic-debugging` skill applies.
- **Verification.** Before claiming a phase done, `verification-before-completion` skill applies — run the tests, confirm output, evidence before assertion.
- **Prose drafting.** Claude can draft DECISION_LOG entries, README sections, report paragraphs — for you to edit.

The one hard rule: don't commit a line you can't explain. Claude can write the
code; you read it, understand it, and own the result. Avoid handing the whole
plan to subagents to run unattended — the point is that you understand what
lands, not that you typed it.

When you're ready for the next phase to be more granular than what's above
(once Phase 0–1 are done), say "write the Phase 2 plan" and I'll produce a
detailed subplan in `docs/plans/`.
