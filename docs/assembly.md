# Putting it up

Rule 1 of this project is that fast assembly is a requirement of the first
class. Everything measured so far — the doorway, the interior, the cover, the
connector schedule — describes the dome once it is standing. This is the first
thing in the repository about getting it there.

```bash
python3 -m stardome assembly D6
python3 -m stardome assembly --all
python3 -m stardome assembly D6 --json -o exports/model
make assembly
```

## The one move that is expensive

A bow is nine metres of flexible rod. Laying it **on top of** what is already
standing is free: you walk it round the dome and drop it on. Passing it
**under** something already standing is not — the rod has to be sprung, or the
standing rod lifted off its node, and either way it is a two-person move at
head height or above.

So an assembly order costs exactly one thing: **how many times a bow has to be
threaded under a bow that is already up.** Call each one a *threading*. Nothing
else here is being counted.

## Why this is a graph and not a guess

Two bows are two great semicircles on the same sphere. Two distinct great
circles meet at one antipodal pair of points, and every bow covers exactly the
half of its circle above the ground plane, so **any two bows cross at most
once.** The arithmetic closes exactly:

| | |
|---|---|
| pairs of bows | 105 |
| pairs sharing both feet, which never cross | 15 |
| **rod-to-rod crossings** | **90** |

The 15 are the co-footed pairs: three bows leave every base point and all three
run to the base point diametrically opposite, so each such pair shares both
ends and meets nowhere in between. Ten feet, three pairs each, every pair
counted at both of its ends — 15. That is the same 90 contacts the model has
been reporting since milestone 1, arrived at from the other direction.

At each of those 90 crossings one rod is radially inside the other, and that is
not a drawing convention: `weave.global_profile` solves for a radial route that
keeps every crossing clear, and its answer says who is inside. See
[`tied-node.md`](tied-node.md).

So the weave is a **digraph on 15 vertices with 90 arcs**, each pointing from
the inner bow to the outer one. An assembly order is a linear ordering of the
vertices; an arc is free if the inner bow goes up first and costs a threading
if the outer one is already there. The number of threadings is the number of
arcs pointing backwards along the order — the **minimum feedback arc set**
problem. It is NP-hard in general and completely trivial at *n* = 15, where the
Held-Karp subset recursion settles it exactly in 2¹⁵ × 15 steps, well under a
second.

Nothing below is a heuristic or a good order somebody found. It is the true
optimum over all 15! ≈ 1.3 × 10¹² orderings, and the test suite checks the
recursion against every permutation at *n* = 7, where they can all be
enumerated.

## Four results

### 1. There is no free assembly

The weave is cyclic. On every variant the shortest cycle is three bows long:

> **G1 is inside G5, which is inside U1, which is inside G1.**

Three bows each inside the next cannot be put in any order, so at least one of
those three arcs has to be paid for whichever bow goes up first. A weave with
no cycles would be a stack of hoops with nothing holding it together; the cycle
is the structure, and the threading is what it costs to build it.

### 2. The floor is 21 threadings, and it is the same at every size

| | |
|---|---|
| crossings | 90 |
| **minimum threadings** | **21** |
| worst possible order | 69 |
| orders achieving the minimum | 16 |

The worst order is the crossings less the best, because reversing an order
flips every arc — so there is no separate solve for it.

The number is identical for D3, D4, D6, D8, D10 and D12. The digraph comes from
the topology and the chosen stacking order, and neither scales, so **a 3 m dome
and a 12 m dome are the same build**. What changes with size is the length and
weight of what you are springing, not the number of times you have to spring
it. That is worth knowing before anyone concludes that the small variants are
the easy ones to put up.

### 3. Twenty of the 21 are bought at the ten lashed nodes

The fan stacking order fixes the radial level of all four rods at a node, which
orients 60 of the 90 arcs before any weave routing happens at all. Feed the
solver only those 60 and the answer is **20**.

So the routing of the 30 free crossings — the part `global_profile` solves for,
and the part that could in principle be chosen differently — is worth at most
one threading out of 21. **Almost the entire cost of assembly is decided by the
stacking order at the nodes, not by the weave.** If a cheaper build is ever
wanted, that is where to look, and `weave.stacking_options` already enumerates
the alternatives with what each does to the connector.

Twenty is a hard floor under any routing whatsoever. Whether some other
feasible routing reaches it — that is, whether the last threading can be
removed — is open, and would need the weave solver to optimise rather than just
find a feasible answer.

### 4. Family by family costs half as much again

The obvious order, and the one the reference's own construction diagram draws,
is one whole family at a time: all five of the pentagram, then the next five,
then the last five. It is also the only kind of order a person can be *told*
rather than handed on a sheet.

| order | threadings |
|---|---|
| G–L–U | 34 |
| L–G–U | 34 |
| L–U–G | 34 |
| G–U–L | 54 |
| U–G–L | 54 |
| U–L–G | 54 |

The split is exactly one rule: **put family L up before family U.** Where G
goes makes no difference at all. Obey it and a family order costs 34; break it
and it costs 54.

So the price of an order simple enough to say out loud is 34 against the
optimum's 21 — thirteen extra threadings. Whether thirteen hard moves are worth
more than a memorised fifteen-item permutation is a field question, not a
geometry one, and milestone 4's stopwatch is what should answer it.

## The schedule

The optimal order on M, with what each step meets and what it closes. `closes`
is a lashed node whose fourth rod has just arrived — the moment its fan
connector can be bolted up — or a base point whose third bow end has landed.

| step | bow | crossings made | threadings | threads under | closes |
|---|---|---|---|---|---|
| 1 | L2 | 0 | 0 | — | — |
| 2 | G2 | 1 | 0 | — | — |
| 3 | G5 | 2 | 0 | — | — |
| 4 | L1 | 3 | 0 | — | N21 |
| 5 | L4 | 4 | 1 | G2 | — |
| 6 | G4 | 4 | 1 | G2 | — |
| 7 | L3 | 5 | 1 | L2 | N23 |
| 8 | L5 | 6 | 2 | G5, L4 | — |
| 9 | U3 | 6 | 0 | — | b4, b9 |
| 10 | G3 | 8 | 3 | G2, L2, L4 | N24 |
| 11 | U1 | 8 | 1 | G4 | b0, b5 |
| 12 | G1 | 10 | 4 | G4, G5, L2, L5 | N07, N20, N22 |
| 13 | U4 | 10 | 2 | G2, G4 | N05, b1, b6 |
| 14 | U2 | 11 | 3 | G2, G5, U3 | N08, b2, b7 |
| 15 | U5 | 12 | 3 | G3, G5, U3 | N06, N09, b3, b8 |

Three things in it matter on site.

**The first four bows are free.** A quarter of the frame goes up with no hard
move at all, and the first lashed node closes at step 4 — so there is something
rigid to work against early rather than a pile of loose arches.

**The work is back-loaded.** The last five steps carry 13 of the 21 threadings,
and the worst single step is four. The crew is not needed evenly: the last
third of the build is where the hands go.

**At most three bows are ever standing loose.** Counting bows that are up but
do not yet pass through any completed node, the running total goes
1, 2, 3, 0, 1, 2, 0, 1, 2, 1, 2, 0, 0, 0, 0 — it never exceeds three, and it
returns to zero five times. That is a proxy for how many bows still need a hand
on them, not a stability calculation, but the shape of it is encouraging: the
frame keeps locking itself down rather than accumulating loose members.

## What this does not tell you

- **Nothing about time.** A threading is one hard move. How long it takes, and
  how much longer the tenth one takes than the first, is milestone 4's
  stopwatch.
- **Nothing about whether the partial frame stands.** A single bow is a free
  arch that falls over, and nothing here knows that. The `standing` count above
  is a proxy, not a mechanics result.
- **Nothing about whether a threading is possible at all.** The whole model
  assumes a 9 m rod can be sprung far enough to pass one already-placed rod.
  On D3, bent to a 1.5 m radius already, that assumption is worth checking on
  the prototype before 21 is treated as a build plan. It is the same question
  as minimum bend radius, from the other end.
- **Nothing about the cover, the skirt or the doorway.** Those go on after the
  frame closes and have their own sequence, which nobody has written down.
