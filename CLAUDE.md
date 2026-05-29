# Superoptimizer — Working Agreement

A provably-optimal superoptimizer for short, loop-free integer/bitwise routines,
built on Z3 SMT. This file is the contract between the author and any AI
assistant (Claude / Claude Code) that touches this repo.

---

## 1. The Authorship Rule

**Never commit a line you can't explain.**

This is the only rule that matters. Everything else in this document supports it.
Concretely:

- If Claude proposes code, the author must read it, understand it, and be able
  to defend every line in a code review before it lands in a commit.
- If a piece of code is too dense to explain on the spot, it gets simplified or
  rewritten by the author until it can be.
- When in doubt, ask Claude to *explain* rather than to *write*.

---

## 2. What the Author Owns (Do Not Delegate)

These four areas are the intellectual core of the project. Claude may explain,
suggest references, or review.

1. **SMT encodings of tricky instructions.** Arithmetic vs logical shift,
   signed vs unsigned comparisons, division by zero, overflow semantics. A
   wrong encoding produces confidently-wrong "optimal" results that pass
   casual testing.
2. **CEGIS correctness.** The verification query must truly quantify over
   *all* inputs. The component-connection constraints (location variables,
   acyclicity, single-definition) are the classic silent-bug zone.
3. **Constants as free variables.** Why SMT can synthesize constants that
   brute-force enumeration cannot — this is a real insight, write it up.
4. **The definition of "optimal".** Instruction count vs latency vs
   throughput. Pin it down precisely; the choice changes the winner.

If Claude is asked to produce code in these areas, it should respond with an
explanation and a sketch, and only when asked, a finished implementation.

---

## 3. What Claude Is Welcome to Do

- Z3 API lookups, boilerplate scaffolding, test harness plumbing.
- Translating a hand-derived encoding into Python once the author has worked
  the math on paper.
- Code review: spotting off-by-ones, signedness mistakes, missing edge cases.
- Debugging help: explaining Z3 error messages, model output, counterexamples.
- Suggesting *Hacker's Delight* tricks to use as benchmarks.
- Drafting documentation, decision-log entries, and report prose — to be
  edited by the author.


---

## 4. Project Layout

```
superopt/
  ir.py            # instruction + program representation
  interp.py        # reference interpreter (Python, bit-masked)
  encode.py        # program -> Z3 bit-vector formula
  equiv.py         # equivalence checking + counterexample extraction
  search.py        # enumeration / CEGIS driver
  fuzz.py          # independent random-input oracle
  benchmarks/      # reference specs (start from Hacker's Delight)
  tests/           # pytest suite
  DECISION_LOG.md  # why each non-obvious choice was made
  AI_USAGE.md      # what Claude helped with, and where
  CLAUDE.md        # this file
```

Bit width starts at **8-bit** for fast iteration; CEGIS phase scales to **32-bit**.

---

## 5. Phase Plan (Reference)

| Phase | Deliverable | Done-when |
|-------|-------------|-----------|
| 0 | Setup + Z3 hello-world | UNSAT proof that `x*2 == x<<1` |
| 1 | IR + interpreter | Interpreter matches reference spec on 10k random inputs |
| 2 | SMT encoder + `equivalent()` | Proves `x+x ≡ x<<1`; returns counterexample on a wrong pair |
| 3 | Brute-force search (MVP) | Rediscovers a known optimal trick + reports "optimal at length N" |
| 4 | CEGIS / component synthesis | Synthesizes a real Hacker's Delight function over all 32-bit inputs, constants included |
| 5 | Stretch: latency cost model OR beat `-O3` OR neural-guided search | Documented results table of concrete wins |
| 6 | Independent fuzz harness + writeup | Fuzzer passes on 100% of emitted programs |

Phase 3 is the de-risking milestone — a working MVP that proves the
SMT/interpreter/equivalence stack is sound before CEGIS is layered on.

Phase 4 is the intellectual core. Required reading before starting:
Jha, Gulwani, Seshia, Tiwari — *Oracle-Guided Component-Based Program
Synthesis* (2010). Reference codebase: Souper.

---

## 6. Conventions

### Code

- Python 3.11+, no type-stub avoidance — annotate public functions.
- `ruff` for lint, `pytest` for tests. Run both before every commit.
- Prefer explicit `BitVecVal(c, width)` over implicit int promotion in Z3 code;
  the implicit path silently widens and hides bugs.
- Every `encode.py` opcode has a matching `interp.py` opcode, cross-checked
  in `tests/test_encoder_vs_interp.py` on random programs and random inputs.
  **This cross-check is non-negotiable** — it is the only thing that catches a
  wrong encoding before it poisons the optimality results.

### Verification

- Two independent layers:
  1. SMT equivalence (`equiv.py`) — the proof.
  2. Random-input fuzz (`fuzz.py`) — the sanity check, written without
     reusing any code from the encoder.
- A result is only reported as "optimal" if both layers agree.

### Commits

- Conventional-commit style (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`).
- One logical change per commit. No mixed refactor + feature.
- Commit message answers *why*, not *what* — the diff shows the what.
- `DECISION_LOG.md` gets an entry for any choice that wasn't obvious from
  the code (encoding choices, search-order changes, cost-model design).

---

## 7. Definition of "Optimal" (provisional)

For Phases 3–4, **optimal = minimum instruction count** under the chosen
instruction set, where each listed opcode counts as 1 and `const` is free.

Phase 5 may introduce a latency-based cost model; if so, the change is logged
in `DECISION_LOG.md` and the report compares both definitions side-by-side
on the same benchmarks.

---

## 8. Honest Framing for the Writeup

- The synthesis technique (CEGIS, component-based encoding) is **not novel**.
  It is correctly attributed to Jha et al. 2010 and Solar-Lezama's sketching
  work.
- What is the author's: the IR design, the encoder, the implementation,
  the evaluation, and any documented gap-against-`-O3` results.
- If the neural-guided-search stretch goal happens, it is framed as
  "applying a known technique to my synthesizer," with a measured speedup,
  not as a new method.

---

## 9. Out of Scope (For Now)

- Floating point.
- Memory operations / loads / stores.
- Loops, branches, function calls.
- Multi-output programs (single output keeps the equivalence query simple).

Each of these is a research project in its own right; revisit only after the
single-output, loop-free, integer/bitwise case is solid.

---

## 10. First-Time Machine Setup

Read this on any machine that hasn't run this project yet — fresh clone, new
laptop, returning after a long break. Do the steps in order; skip ones
already done.

### Step 1 — Clone (skip if already done)

```bash
git clone https://github.com/smiles0527/superopt.git
cd superopt
```

### Step 2 — Python environment

Inside `superopt/`:

```bash
python --version          # need 3.11+
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate   # macOS / Linux
pip install z3-solver pytest
```

The `venv/` directory is gitignored — it stays per-machine.

### Step 3 — Verify Z3 works (Phase 0 deliverable)

Per the Phase Plan above: write a short Python script that uses Z3 to prove
`x * 2 == x << 1` for 8-bit `x`. Assert the **negation** (that they differ)
and expect `unsat` from the solver.

You'll need `BitVec`, `Solver`, and `unsat` from the `z3` module.

UNSAT means "no 8-bit input makes the two expressions differ" — i.e. they're
provably equivalent for *all* inputs. **Do not move past Step 3 until you
can explain in your own words why UNSAT is the desirable answer here.**

Authorship rule applies: write this yourself, even though it's small. If you
can't reproduce it from memory tomorrow, you haven't internalized it yet.

### Step 4 — Reload Claude Code config

If this is the first time Claude Code has run in this folder, type `/hooks`
(or restart Claude Code) so the harness picks up `.claude/settings.json`.
The `SessionStart` / `SessionEnd` auto-sync hooks won't fire until they've
been loaded once **and** the repo has at least one commit (deliberate guard
— the hook bails on empty repos so it never makes the first commit for you).

### Step 5 (optional) — Sync your personal Claude Code config

This step lives outside the project. If you want your *global* Claude Code
config (enabled plugins, theme, personal `CLAUDE.md`) to match across
machines, bootstrap from the companion repo `smiles0527/claude-config`:

```bash
cd %USERPROFILE%\.claude        # Windows; ~/.claude elsewhere
git init -b main
git remote add origin https://github.com/smiles0527/claude-config.git
git fetch origin
git checkout origin/main -- .gitignore settings.json CLAUDE.md
git branch --set-upstream-to=origin/main main
```

The `git checkout origin/main -- <files>` form pulls only the tracked config
files — your local `.credentials.json` and per-machine session state stay
untouched. After this, `git pull` / `git push` in `~/.claude/` keeps both
machines in lockstep.
