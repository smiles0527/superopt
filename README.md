# superopt

A superoptimizer for short, loop-free integer and bitwise routines. Hand it a
small function and it searches for the shortest equivalent program, then proves
there's nothing shorter. Not "a bit faster," but provably optimal under a fixed
instruction set.

## The idea

An ordinary compiler at `-O3` applies a big bag of heuristic rewrites. It makes
your code faster but never claims it found the best version. Superoptimization,
going back to Massalin in 1987, asks the harder question: out of *all* programs,
which is the shortest one that computes this function? The classic party trick
is rediscovering something like `x & (x - 1)` (clear the lowest set bit) from
nothing, and certifying that no shorter sequence does the same job.

The catch is the word "equivalent." Two programs are equivalent only if they
agree on *every* input, and you can't check that by running them. A single
32-bit input already means four billion cases, and it gets worse fast with more
arguments. So instead of running anything, superopt encodes each program as a
bit-vector formula and hands it to the Z3 SMT solver, asking the question
backwards:

> Is there *any* input where these two programs disagree?

If Z3 says unsat (unsatisfiable), no such input exists, which means the programs
are equal everywhere. That's the proof. If it says sat, it hands back the exact
input where they differ, which is a gift when you're debugging. This backwards
framing is the whole foundation. Once it clicks for one pair of programs it
scales to all of them.

Finding the optimal program comes in two flavors. The brute-force version
enumerates programs by length (all of length 1, then 2, then 3) and asks Z3
"equivalent?" for each. The first length that matches is optimal by
construction. It's slow but obviously correct, which is exactly why it comes
first: it proves the interpreter, the encoder, and the equivalence check all
agree before anything clever gets layered on. The clever version is CEGIS
(counterexample-guided inductive synthesis, from Jha et al. 2010): synthesize a
program that works on a handful of example inputs, verify it against all inputs
with Z3, and feed any counterexample back as a new example. It converges fast
because every counterexample rules out a huge slice of wrong programs.

One thing that falls out of the SMT approach genuinely surprised me: a constant
isn't something you have to guess. In the formula it's just a free variable the
solver gets to pick, so Z3 can *solve* for the magic number that makes a program
correct, something brute-force enumeration could never stumble onto.

## Status and scope

Early days. The repo is set up and the theory is written up; the optimizer
itself is still ahead of me. The build goes in phases: Z3 hello-world, then the
IR and interpreter, the encoder and equivalence check, brute-force search, then
CEGIS, with a stretch goal of a latency-based cost model or measured wins
against `-O3`.

Deliberately out of scope for now: floating point, memory and loads/stores,
loops and branches, and multi-output programs. Each one is its own research
project; the single-output, loop-free, integer case comes first.

## Notes

The study notes (superoptimization theory, SMT and bit-vectors,
equivalence-via-unsat, CEGIS, the Jha 2010 reading) live in a separate
repository, so the Obsidian auto-sync churn never clutters this one's history:

**→ [github.com/smiles0527/superopt-notes](https://github.com/smiles0527/superopt-notes)**

They're also checked out locally at `notes/` (gitignored here) as an Obsidian
vault. Edit them there; the `obsidian-git` plugin syncs them to the notes repo
on its own. A fresh clone of this project that wants the notes should also
`git clone` the notes repo into `notes/`. A clean, read-only snapshot of the
notes lives under `docs/notes/` so they're browsable here on GitHub too.
