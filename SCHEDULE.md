# Schedule: finish before September 2026

A forward-looking, dated plan. It complements the other two planning files.
`PLAN.md` is the phase *spine*, what each phase builds; `TIMELINE.md` is the
backward *log* of what already happened. This file is the *calendar*: when each
phase lands, and where the risk sits.

---

## The two assumptions everything rests on

Two levers reshape every date below, and until they're confirmed the calendar
runs on the defaults written in bold.

The first is what *finishing* means. The default is that the core is Phases 1–4
plus 6 (a solid synthesizer, the trust layer, and the writeup), with Phase 5
(beating `-O3`) treated as opportunistic rather than required.

- [ ] Confirm, or change it to: finishing must include a Phase 5 win.

The second is the time budget. The default is roughly 10–15 hours a week across
the summer. At half that, Phase 5 falls away and Phase 4 plus the writeup
becomes the finish line; at double it, the `-O3` comparison turns into a real
deliverable rather than a maybe.

- [ ] Confirm, or set it to ~5/week or ~25/week.

---

## Where things stand (2026-06-05)

The scaffold is in place, but the project is really at the end of Phase 0 and
the start of Phase 1. The IR in `ir.py` is real and clean. `interp.py`,
`encode.py`, `equiv.py`, and `search.py` are still `NotImplementedError` stubs;
`cegis.py`, `fuzz.py`, and `cost.py` don't exist yet; and the only test so far
is `test_ir.py`. Two pieces of Phase 0 are still outstanding: the runnable proof
that `x*2 ≡ x<<1`, and the `DECISION_LOG.md` entry explaining why that UNSAT
result is a proof rather than just evidence.

There's also a piece of housekeeping debt. Locally, `main` (the vault and
config) and `origin/master` (this code) are unrelated histories, so `main`'s
pull errors out until they're reconciled. That needs settling before real code
starts crossing between machines.

---

## What shapes the calendar

Two danger zones can't be compressed without risking confidently-wrong
"optimal" results, and the whole schedule is arranged to protect them. The first
is the Phase 2 encodings: logical versus arithmetic shift, shifting at or past
the width, multiply and negate overflow. The second is the Phase 4 CEGIS
connection constraints: acyclicity, single-definition, the off-by-one zone where
silent bugs hide. Phase 5 is the shock absorber that gives those room; the
encoder cross-check and the fuzzer never are.

---

## The calendar, phase by phase

Roughly twelve and a half weeks, June through the end of August.

**Phase 0 close-out (Jun 5–7).** Three things land: a script you wrote yourself
that proves `x*2 ≡ x<<1` comes back `unsat`, the `DECISION_LOG.md` entry on why
that counts as a proof, and the reconciliation of the two unrelated git
histories. Done when all three are true.

**Phase 1, interpreter and specs (Jun 8–19, two weeks).** Build `execute()`,
watching the ASHR sign-extend trap, and write the three reference specs.
Cross-check the interpreter against hand-coded `Program`s on ten thousand random
inputs. Done when `pytest test_interp.py` is green and every spec matches its
hand-built program.

**Phase 2, encoder and equivalence (Jun 22–Jul 10, three weeks).** The first
danger zone. Encode each opcode in Z3 one at a time, settle `equivalent()`, and
run the encoder-against-interpreter cross-check across a hundred thousand random
program-and-input pairs. Done when those checks pass, `x+x ≡ x<<1` proves
equivalent, and a deliberately wrong pair returns a counterexample that really
does diverge.

**Phase 3, brute-force MVP (Jul 13–24, two weeks).** Enumerate programs by
increasing length with aggressive pruning, rediscover `x & -x` for `isolate_rmb`,
and report it as optimal at length two. This is the de-risk checkpoint: once it
works, the interpreter, encoder, and equivalence stack are proven sound and
CEGIS can be built on top with confidence.

**Phase 4, CEGIS (Jul 27–Aug 21, four weeks).** The intellectual core, and the
long pole. Read Jha 2010 twice, hand-derive the connection constraints, build
the synth-and-verify loop, let constants be free variables rather than
enumerated, scale the bit-vectors to 32-bit, and synthesize one real *Hacker's
Delight* function. Done when that function, constant and all, is synthesized and
verified over every 32-bit input.

**Phase 6, fuzz and writeup (Aug 24–31, one week).** Write the independent
fuzzer, sharing no code with the encoder, and the report in `report/report.md`.
Done when the fuzzer passes on 100% of every program the tool has emitted and
the report has been read back critically.

**Phase 5, the stretch (opportunistic).** It ships after Phase 6, not before,
precisely because it's the first thing cut under pressure. The default form is
beating `-O3` (Option B), the most defensible standalone finding, written up as
a results table with concrete diffs. Phase 5 has three candidate forms: Option A
is a latency cost model, Option B is the `-O3` comparison, Option C is
neural-guided search. The calendar assumes B. Full citations for all three live
in `docs/references.md`.

---

## The reading track, running alongside

The theory reading isn't a phase of its own; it runs in parallel with the build,
on two tracks. The background track spans Phases 1–3. Bradley and Manna's *The
Calculus of Computation* is the main one; its decision-procedure and bit-vector
chapters are the theory directly under the encoder and the equivalence check, so
it pairs naturally with Phase 2. Ben-Ari's *Mathematical Logic for Computer
Science* fills in the logic foundation: soundness, completeness, and why an
UNSAT result is a proof, which is the Phase 0 question exactly. The targeted
track is Jha 2010, read across the Phase 1–3 evenings so Phase 4 doesn't start
cold; the component-based encoding is specific to the synthesizer and appears in
neither textbook. Full citations are in `docs/references.md`.

---

## Critical path and how it degrades

Phase 4 is what eats the buffer. If it slips past August 21, the schedule
degrades in a fixed order, and correctness never pays the price. First, drop
Phase 5 entirely. Then shrink Phase 4's ambition: the De Bruijn trailing-zeros
target falls back to just `isolate_rmb`, and the bit-vectors drop to 8-bit if
32-bit proves slow. Then compress the writeup, framing the narrowed scope
honestly. What never gets cut, under any pressure, is the Phase 2 cross-check or
the Phase 6 fuzzer.

The single best move is to keep the reading track moving through Phases 1–3, so
Phase 4 starts cold on neither the decision-procedure side nor the synthesis
encoding.

---

## Checkpoints

- [ ] **End of July:** the Phase 3 MVP works, and the stack is proven sound.
- [ ] **Aug 21:** Phase 4 lands, or the degradation plan triggers.
- [ ] **Aug 31:** the fuzzer is green, the report is reviewed, and it's done.
