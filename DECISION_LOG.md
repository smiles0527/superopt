# Decision log

Why each non-obvious choice was made. Newest entry first.

## Phase 4b: component synthesis

- **The wiring is encoded with Jha 2010 location variables.** Each operation gets an integer output line and one input line per operand. Well-formedness keeps the output lines a permutation (one component per line) and forces every input to read a strictly-earlier line (acyclicity), and a connection constraint ties each input to the value on the line it points at. The solver picks the wiring and the constants together, and a decoder reads the model back into a `Program`. The technique is Jha et al. 2010, not novel here; the implementation and evaluation are.
- **Location variables are bit-vectors, not integers.** Integer locations force Z3 to mix linear-integer and bit-vector reasoning, which is slow. Small fixed-width `BitVec` locations make the whole query one bit-vector problem it can bit-blast, with unsigned comparisons (`ULT`, `UGE`) since the indices are non-negative. The fast rungs are the canary: a signed/unsigned slip breaks acyclicity and `x & -x` stops synthesizing.
- **Symmetry is broken on interchangeable parts.** Identical opcodes are ordered by line, and commutative operations have their two input locations ordered. Both are non-lossy (any valid program has exactly one labeling that obeys them), and they stop the solver re-deriving the same wiring under every relabeling.
- **A `Library` can pin constants via `fixed_constants`.** Structural constants like shift amounts are provided rather than searched, while the genuinely magic constants stay free. This keeps the headline, the solver discovering the masks, and shrinks the search (popcount from six unknown bytes to three).
- **The headline target moved from CTZ to popcount.** Count-trailing-zeros via a De Bruijn sequence indexes a 32-entry table, which is a memory load and out of scope, so SWAR population count replaced it: pure arithmetic and bitwise work with real magic masks and no table.
- **Full SWAR popcount is recorded as the measured frontier, not forced.** Even with every lever, CEGIS does not converge on it. The per-round synthesis cost explodes as counterexamples accumulate (0.06s, 0.1s, 3.9s, 11s, 27s over five examples, then a cliff), because each round must find one wiring correct on all accumulated inputs at once. The two popcount rungs are marked `slow` and deselected by default; the seven rungs that pass prove the technique end to end.

## Phase 4a: constant synthesis

- **A constant is a free variable the solver picks, not a value to enumerate.** A `Hole` in a sketch encodes to a free `BitVec`, so the solver solves for the constant that makes the program correct. This recovered `0xAAAAAAAA` over all 32-bit inputs, which brute-force enumeration could never reach. It is the real insight the project exists to show.
- **CEGIS splits the doubly-quantified synthesis query.** "There exists a program such that for all inputs it matches the spec" is too hard to ask Z3 directly, so the loop alternates: finite-synthesis finds constants fitting a few example inputs (an easy existential), `equivalent` verifies over all inputs (the Phase 2 proof), and any counterexample is folded back as a new example. It converges in a few rounds.
- **Finite-synthesis `unsat` means no program exists at all, not just none for these examples.** If no constants fit even the current handful of examples, none fit every input, so the loop returns `None` rather than spinning.
- **Sketch and spec arity and width are checked up front.** A mismatch is a programming error, not a synthesis failure, so it raises rather than producing a misleading `None`.

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
