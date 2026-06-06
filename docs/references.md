# References and reading map

The papers and tools behind this project, grouped by what each one is for. It's also a rough reading order: the first group is the core, the rest is context you can pull in when you need it.

Every entry has a link that always resolves (a DOI), plus a free PDF where one exists. If you're new to the whole idea, start with the [plain-English explainer](explainer.md) instead.

## The core: CEGIS and component-based synthesis

This is the foundation of Phase 4. If you read one thing, read the Jha paper, and read it twice.

*Oracle-Guided Component-Based Program Synthesis* (Jha, Gulwani, Seshia, Tiwari; ICSE 2010) is the exact encoding Phase 4 is built on: a bag of components, location variables for the wiring, and the well-formedness constraints that keep it honest. https://doi.org/10.1145/1806799.1806833

*Combinatorial Sketching for Finite Programs* (Solar-Lezama, Tancau, Bodík, Seshia, Saraswat; ASPLOS 2006) is the paper that introduced CEGIS, through the SKETCH system. https://doi.org/10.1145/1168857.1168907

*Program Synthesis by Sketching* (Solar-Lezama; PhD thesis, UC Berkeley, 2008) is the long version. The CEGIS chapter is the part that matters here. Free PDF: https://people.csail.mit.edu/asolar/papers/thesis.pdf (Berkeley mirror: https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-177.pdf)

*Synthesis of Loop-Free Programs* (Gulwani, Jha, Tiwari, Venkatesan; PLDI 2011) is the follow-up to Jha 2010, and the closest match to what you're building: loop-free and component-based. https://doi.org/10.1145/1993316.1993506

## Where superoptimization came from

The origin of the idea, plus the search strategies other people picked.

*Superoptimizer: A Look at the Smallest Program* (Massalin; ASPLOS 1987) is the paper that started all of this. Open PDF from the ACM: https://dl.acm.org/doi/10.1145/36206.36194

*Automatic Generation of Peephole Superoptimizers* (Bansal, Aiken; ASPLOS 2006) scales superoptimization up by learning a big database of peephole rewrites. https://doi.org/10.1145/1168857.1168906

*Stochastic Superoptimization* (Schkufza, Sharma, Aiken; ASPLOS 2013) is the STOKE system, which searches with a random walk instead of an SMT solver. Good to read as a contrast when you reach the Phase 5 stretch goals. https://doi.org/10.1145/2451116.2451150

## The one to read for implementation

*Souper: A Synthesizing Superoptimizer* (Sasnauskas, Chen, Collingbourne, Ketema, Lup, Taneja, Regehr; 2017) is what `CLAUDE.md` calls the reference codebase. Study how it's put together, don't copy it. Paper: https://arxiv.org/abs/1711.04422. Code: https://github.com/google/souper

## The solver and its rules

*Z3: An Efficient SMT Solver* (de Moura, Bjørner; TACAS 2008) is the solver everything here runs on. https://doi.org/10.1007/978-3-540-78800-3_24

Z3 itself, with its Python API, lives at https://github.com/Z3Prover/z3. The official guide has a Python and bit-vector tutorial: https://microsoft.github.io/z3guide/

SMT-LIB's theory of fixed-size bit-vectors pins down the exact meaning of `bvadd`, `bvashr`, `bvudiv`, and the rest. It's the source to trust when you encode each opcode in Phase 2. https://smt-lib.org/theories-FixedSizeBitVectors.shtml

## The theory underneath

Two textbooks for the background the papers above take for granted. Read them alongside the early phases; this is the slow foundational reading, not the night-before-Phase-4 kind.

*The Calculus of Computation: Decision Procedures with Applications to Verification* (Aaron Bradley, Zohar Manna; Springer, 2007; ISBN 978-3-540-74112-1) is the closest thing to a textbook for the front half of this project. Its decision-procedure chapters cover first-order logic, the theory of fixed-size bit-vectors, and theory combination, which is what Z3 is doing under the hood when it settles `x+x ≡ x<<1`. It backs the encoder and the equivalence check in Phase 2, and because CEGIS verifies each candidate with a decision-procedure query over all inputs, it covers half of Phase 4 as well. https://doi.org/10.1007/978-3-540-74113-8

*Mathematical Logic for Computer Science*, 3rd edition (Mordechai Ben-Ari; Springer, 2012; ISBN 978-1-4471-4128-0) is the logic underneath the proof: propositional and first-order logic, soundness and completeness, resolution, SAT. It's where the Phase 0 question really lives. Why does an UNSAT result prove equivalence for every input and not just the ones you happened to try? https://doi.org/10.1007/978-1-4471-4129-7

Neither book covers synthesis. They give you the verifier; the component-based encoding that does the actual synthesizing is still the Jha paper at the top of this list.

## Benchmarks

*Hacker's Delight*, 2nd edition (Henry S. Warren Jr.; Addison-Wesley, 2012; ISBN 978-0321842688) is the source of the bit tricks the tool should rediscover on its own: `x & -x`, popcount, magic-number division, de Bruijn sequences. It's a book, so there's no DOI. The book is the reference.

## If the neural-guided stretch goal happens (Phase 5, Option C)

*Learning to Superoptimize Programs* (Bunel, Desmaison, Kumar, Torr, Kohli; ICLR 2017) is the paper to cite if you try learning which candidates to enumerate first. Frame it as applying a known technique, not inventing one. Free PDF: https://arxiv.org/abs/1611.01787
