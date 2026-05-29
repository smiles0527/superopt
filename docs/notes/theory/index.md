# Theory — background for the superoptimizer

Reference notes on the theory the project rests on: superoptimization, SMT and
bit-vector reasoning, equivalence checking, program synthesis, CEGIS, and what
"optimal" actually means.

## What these notes are, and what they aren't

These are study notes. I wrote them (with Claude's help) to get the background
straight, and every outside claim is cited so I can check it against the real
source instead of taking my own word for it. They're logged as AI-assisted in
`AI_USAGE.md`.

They are not portfolio writing. The report in `report/report.md` and any
follow-ups are mine, in my own words — that's where I actually show I understand
this. Think of these as the textbook I read, not the essay I hand in.

## Reading order

The notes build on each other, so on a first pass read them in order.

| # | Note | Question it answers |
|---|------|---------------------|
| 0 | [[00-superoptimization]] | What's a superoptimizer, and why "super"? |
| 1 | [[01-smt-and-bitvectors]] | What's SMT, and how does it model machine integers exactly? |
| 2 | [[02-equivalence-via-unsat]] | Why does an UNSAT result prove two programs equal for every input? |
| 3 | [[03-synthesis-and-constants]] | What's program synthesis, and why do constants wreck enumeration? |
| 4 | [[04-cegis]] | How does CEGIS prove correctness over all inputs without checking them all? |
| 5 | [[05-optimality]] | What does "provably optimal" actually mean? |

## Related vault notes

- [[papers/jha-2010]] — the component-based synthesis paper, the deep read for Phase 4
- [[encodings/shifts]] — the bit-vector shift danger zone, for Phase 2

## The four things to keep my own hands on

From the project `CLAUDE.md`. These are the spots where wrong-but-plausible work
produces confidently-wrong results, so I write them myself:

1. SMT encodings of the nasty instructions — see [[01-smt-and-bitvectors]] and [[encodings/shifts]]
2. CEGIS correctness — see [[04-cegis]]
3. Constants as free variables — see [[03-synthesis-and-constants]]
4. The definition of "optimal" — see [[05-optimality]]
