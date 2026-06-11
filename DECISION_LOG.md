# Decision log

Why each non-obvious choice was made. Newest entry first.

## Phase 3: brute-force search

- **Candidates are matched by exhaustive interpretation, not the SMT checker.** At 8-bit the input space is 256 values, so running a candidate through the interpreter on every input is a complete, exact check. SMT-against-a-spec over all 32-bit inputs is the Phase 4 job.
- **Enumeration searches no constants.** Operands come only from inputs and earlier results. A constant operand would multiply the space by 2^width per constant, which is intractable, and it's exactly the limitation CEGIS removes in Phase 4 by solving for constants. The `x & -x` target needs none.
- **Shortest-first makes the first match provably optimal.** Every shorter length is fully enumerated first, so the first match has minimum instruction count. Dead-code and commutative-duplicate pruning are non-lossy: a program with an unused instruction has a shorter equivalent found earlier, and `f(a,b)` equals `f(b,a)` for commutative ops.
- **Length-0 programs handle identity.** A pass-through output (a bare input) is tried before length 1, so an identity spec resolves to the zero-instruction program instead of a one-instruction equivalent.

## Phase 2: encoder and equivalence

- **Each opcode maps to the matching Z3 bit-vector op.** Fixed-width `BitVec` arithmetic already wraps mod 2^width, so that wrap is the masking and the encoder adds no explicit mask. Constants are `BitVecVal(c, width)`, width spelled out, never an implicit Python int.
- **LSHR must use `LShR`, not `>>`.** On a Z3 `BitVecRef` the `>>` operator is arithmetic (sign-propagating), so logical shift right needs the explicit `LShR()`. This is the one line where a wrong choice produces confidently-wrong "optimal" results that pass casual testing.
- **Equivalence is proved by an UNSAT check.** `equivalent` asserts the two outputs differ and asks Z3; `unsat` means no input can make them differ, so they agree on every input. A proof over the whole symbolic domain, not a sample.
- **The proof relies on shared input variables.** Both programs are encoded with inputs named `in0, in1, ...`, and Z3 interns by name, so the two output expressions share the same variables. If the encoder ever namespaced inputs per program, the check would compare independent variables and report false counterexamples. There's no runtime guard for this, so the `x+x` vs `x<<1` test is the regression canary.

## Phase 1: interpreter

- **Bit width is enforced by masking every intermediate with `(1 << width) - 1`.** The interpreter models a fixed-width register, so arithmetic wraps like hardware rather than growing into an unbounded Python int.
- **ASHR sign-extends, LSHR does not.** ASHR reinterprets a sign-bit-set value as a negative int and then shifts; LSHR works on the masked non-negative value. Getting these backwards is a silent bug that only shows on sign-bit-set inputs.
- **An over-width shift (amount at or past the width) returns a fixed result.** SHL and LSHR return 0; ASHR returns all-ones or 0 depending on the sign bit. This matches Z3's native bvshl/bvlshr/bvashr, so the encoder and interpreter agree without special-casing, and it avoids constructing a multi-gigabit Python int once the width scales to 32.

## Phase 0: project scaffold

- **`Op` is a `StrEnum`.** Programs print and serialise as readable text
  (`add`, `lshr`), which keeps enumerator output and test failures legible.
- **`Operand` is a tagged union of three frozen dataclasses** (`InputRef`,
  `Const`, `ResultRef`) instead of one dataclass with a `kind` string. The
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

## Phase 0: Z3 hello-world

- **Why UNSAT proves equivalence.** Asserting the two expressions differ and getting `unsat` means no assignment of the input bits makes them differ. The solver reasons over the symbolic bit-vector instead of trying values, so `unsat` is a statement about all 2^width inputs at once, equal everywhere. A `sat` result instead returns a concrete differing input. So the check is a proof, not evidence from sampling.
