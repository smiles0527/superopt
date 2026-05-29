# Superopt — Notes

Vault for the [superoptimizer](../CLAUDE.md) project. Paper notes, encoding
sketches, and reasoning that supports `DECISION_LOG.md` in the repo root.

## Map

- **Theory** — background reference, read in order (see [[theory/index]])
  - [[theory/00-superoptimization]] — what a superoptimizer is, and why "super"
  - [[theory/01-smt-and-bitvectors]] — SMT, QF_BV, exact machine-integer modeling
  - [[theory/02-equivalence-via-unsat]] — proving ∀ via ¬∃, the UNSAT-as-proof argument
  - [[theory/03-synthesis-and-constants]] — synthesis, and why constants break enumeration
  - [[theory/04-cegis]] — the CEGIS loop and component-based encoding
  - [[theory/05-optimality]] — what "provably optimal" precisely means
- **Papers**
  - [[papers/jha-2010]] — Oracle-Guided Component-Based Program Synthesis (the CEGIS paper)
- **Encodings** — the danger zone, write these out carefully
  - [[encodings/shifts]] — logical vs arithmetic shift, shift-amount masking
- **Benchmarks** — _to seed from Hacker's Delight as you go_
- **Decisions** — terse one-liners here; full rationale in `../DECISION_LOG.md`

## Conventions

- Notes are first drafts. Once an idea is settled, the canonical version lives
  in code, `DECISION_LOG.md`, or the writeup — not here.
- Link liberally with `[[wikilinks]]`. A red link is a TODO, not an error.
- One note per concept. If a note grows past ~2 screens, split it.
