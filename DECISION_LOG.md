# Decision log

Why each non-obvious choice was made. Newest entry first.

## Phase 0 — project scaffold

- **`Op` is a `StrEnum`.** Programs print and serialise as readable text
  (`add`, `lshr`), which keeps enumerator output and test failures legible.
- **`Operand` is a tagged union of three frozen dataclasses** — `InputRef`,
  `Const`, `ResultRef` — instead of one dataclass with a `kind` string. The
  type checker then forces the interpreter and encoder to handle all three
  operand kinds explicitly, rather than guessing.
- **Constants are operands, not an opcode.** A `Const` holds a concrete value
  now and becomes a free variable the solver fills during synthesis (Phase 4).
  That is why `CONST` is dropped from the `Op` enum that the file map listed.
- **`Program.output` is an `Operand`, not an instruction index.** This lets a
  program's output be a result, a pass-through input, or a constant, so the
  zero-instruction identity program is representable.
- **`interp.execute(program, inputs)` drops the separate `width` argument** the
  plan sketched, in favour of `program.width`, to keep width single-sourced.

## Phase 0 — Z3 hello-world

- _TODO (write this one yourself): why does an UNSAT result prove equivalence
  for every input, rather than just being evidence for the inputs tried?_
