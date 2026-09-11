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

### 2. The floor is 20 threadings, and it is the same at every size

| | |
|---|---|
| crossings | 90 |
| **minimum threadings** | **20** |
| worst possible order | 70 |
| orders achieving the minimum | 3 |

The worst order is the crossings less the best, because reversing an order
flips every arc — so there is no separate solve for it.

The number is identical for D3, D4, D6, D8, D10 and D12. The digraph comes from
the topology and the chosen stacking order, and neither scales, so **a 3 m dome
and a 12 m dome are the same build**. What changes with size is the length and
weight of what you are springing, not the number of times you have to spring
it. That is worth knowing before anyone concludes that the small variants are
the easy ones to put up.

### 3. Eighteen of the 20 are bought at the ten lashed nodes

The fan stacking order fixes the radial level of all four rods at a node, which
orients 60 of the 90 arcs before any weave routing happens at all. Feed the
solver only those 60 and the answer is **18**.

So the routing of the 30 free crossings — the part `global_profile` solves for,
and the part that could in principle be chosen differently — is worth at most
two threadings out of 20. **Almost the entire cost of assembly is decided by the
stacking order at the nodes, not by the weave.** If a cheaper build is ever
wanted, that is where to look, and `weave.stacking_options` already enumerates
the alternatives with what each does to the connector.

Eighteen is a hard floor under any routing whatsoever. Whether some other
feasible routing reaches it — that is, whether the last two threadings can be
removed — is open, and would need the weave solver to optimise rather than just
find a feasible answer.

### 4. Family by family costs half as much again

The obvious order, and the one the reference's own construction diagram draws,
is one whole family at a time: all five of the pentagram, then the next five,
then the last five. It is also the only kind of order a person can be *told*
rather than handed on a sheet.

| order | threadings |
|---|---|
| G–L–U | 30 |
| L–G–U | 30 |
| L–U–G | 30 |
| G–U–L | 50 |
| U–G–L | 50 |
| U–L–G | 50 |

The split is exactly one rule: **put family L up before family U.** Where G
goes makes no difference at all. Obey it and a family order costs 30; break it
and it costs 50.

So the price of an order simple enough to say out loud is 30 against the
optimum's 20 — ten extra threadings. Whether ten hard moves are worth more than
a memorised fifteen-item permutation is a field question, not a geometry one,
and milestone 4's stopwatch is what should answer it.

## The schedule

The optimal order on M, with what each step meets and what it closes. `closes`
is a lashed node whose fourth rod has just arrived — the moment its fan
connector can be bolted up — or a base point whose third bow end has landed.

| step | bow | crossings made | threadings | threads under | closes |
|---|---|---|---|---|---|
| 1 | G5 | 0 | 0 | — | — |
| 2 | L1 | 1 | 0 | — | — |
| 3 | L2 | 2 | 0 | — | — |
| 4 | G2 | 3 | 0 | — | N21 |
| 5 | L3 | 3 | 0 | — | — |
| 6 | L4 | 5 | 1 | G5 | — |
| 7 | G4 | 5 | 1 | L1 | N23 |
| 8 | L5 | 6 | 2 | G5, L1 | — |
| 9 | U3 | 6 | 0 | — | b4, b9 |
| 10 | U1 | 8 | 1 | G4 | — |
| 11 | G1 | 9 | 3 | G5, L2, L3 | N07, N20 |
| 12 | G3 | 9 | 4 | G2, G5, L4, L5 | N22, N24, b0, b5 |
| 13 | U4 | 10 | 2 | G2, G4 | N05, b1, b6 |
| 14 | U2 | 11 | 3 | G2, G5, U3 | N08, b2, b7 |
| 15 | U5 | 12 | 3 | G3, G5, U3 | N06, N09, b3, b8 |

Three things in it matter on site.

**The first 5 bows are free.** A third of the frame goes up with no hard
move at all, and the first lashed node closes at step 4 — so there is
something rigid to work against early rather than a pile of loose arches.

**The work is back-loaded.** The last five steps carry 15 of the 20
threadings, and the worst single step is four. The crew is not needed evenly: the last
third of the build is where the hands go.

**At most three bows are ever standing loose.** Counting bows that are up but
do not yet pass through any completed node, the running total goes
1, 2, 3, 0, 1, 2, 0, 1, 2, 3, 0, 0, 0, 0, 0 — it never exceeds three, and it
returns to zero 7 times. That is a proxy for how many bows still need a hand
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
  the prototype before 20 is treated as a build plan. It is the same question
  as minimum bend radius, from the other end.
- **Nothing about the cover, the skirt or the doorway.** Those go on after the
  frame closes and have their own sequence, which nobody has written down.
