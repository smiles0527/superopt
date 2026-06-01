# Timeline

A running log of project milestones. Newest last.

## 2026-05

- **May 29** — Repo set up: working agreement, implementation plan, `.gitignore`,
  and tooling. The Obsidian notes vault was split into its own repository and
  synced separately, so vault churn never lands in the code history.
- **May 30** — Wrote the theory notes, a references/reading map, and a
  plain-English explainer. Stood up a MkDocs site that renders the notes locally.
- **May 31** — Reworked theory notes 00–05. Landed the project code scaffold:
  `ir.py` (the program data model), stubs for `interp`, `encode`, `equiv`, and
  `search`, the three benchmark specs, `pyproject.toml` with pytest config, and a
  green test for the IR. Started `DECISION_LOG.md`.
