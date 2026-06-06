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
  two-track reading plan into the schedule: the textbooks alongside Phases 1–3,
  Jha 2010 before Phase 4.
