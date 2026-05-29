# Encoding: Shifts

> Danger zone. A wrong encoding produces confidently-wrong "optimal" answers
> that pass casual testing. Derive everything here yourself; cross-check with
> [[../index|the interpreter]] on random programs.

## The three shifts to keep distinct

| Opcode | Semantics | Z3 op |
|--------|-----------|-------|
| `shl`  | logical left shift | `x << y` (a.k.a. `BitVecRef.__lshift__`) |
| `lshr` | logical right shift (zero-fill) | `LShR(x, y)` |
| `ashr` | arithmetic right shift (sign-fill) | `x >> y` (in Z3 this is arithmetic!) |

> Z3 gotcha: `x >> y` on a `BitVec` is **arithmetic** shift. For logical right
> shift you must call `LShR(x, y)` explicitly. Getting this backwards is the
> classic silent bug.

## Shift-amount semantics

Open questions to pin down before writing `encode.py`:

- [ ] What does Z3 do with shift amount ≥ width? (C says UB; LLVM says poison;
      Z3 has a defined behavior — find out which and document it.)
- [ ] Are shift amounts treated as unsigned by Z3, regardless of the signedness
      I'm modeling? Test on a small example before trusting.
- [ ] Should `const` shift amounts be restricted to `[0, width-1]` in the
      synthesizer, or should I let the solver explore the full domain and rely
      on the equivalence check to reject nonsense?

## Cross-check obligation

Every shift case has a paired test in `tests/test_encoder_vs_interp.py` that:
1. Builds a tiny program containing that shift.
2. Runs it through `interp.execute` on random inputs.
3. Asks Z3 to evaluate the encoded formula on the same inputs.
4. Asserts the two outputs are bit-identical.

If this test isn't passing for all three shifts, **nothing downstream is
trustworthy.** Do not move to Phase 3 until this is green.
