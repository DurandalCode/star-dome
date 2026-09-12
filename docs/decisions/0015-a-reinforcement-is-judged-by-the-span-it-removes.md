# 0015. Judge a reinforcement by the span it removes

- **Status:** accepted
- **Date:** 2026-09-12
- **Where it lives:** `stardome/span.py`, `docs/span.md`, milestone 7 in `docs/roadmap.md`

## The decision

Milestone 7 lists eight candidate reinforcements and nine criteria to compare them on.
They are not weighed against each other. Every candidate is measured against **one**
number first — the longest unsupported span it leaves — and the other eight criteria are
what that span costs.

The reason is a pair of exponents. To hold the reference dome's sag, the rod must be at
least `d₀(a/a₀)²`; to be bent to the dome radius at all it may be at most `2Re`. The
first grows with the square of the span, the second only with the radius. So the
diameter that a design needs and the diameter it is allowed cross at exactly one size,
and that crossing is the family's ceiling:

| allowable strain | 0.2% | 0.4% | 0.6% | 0.8% |
|---|---|---|---|---|
| largest dome, self-weight parity | **7.2 m** | 14.4 m | 21.6 m | 28.8 m |

The span enters squared, so **halving the worst span multiplies the ceiling by four**.
Nothing else on the list of candidates moves it at all.

## Why

The worst span is `1.0472 R` — 60° of arc — at every variant, because the family is
similar to itself at every size. It is therefore not a fact about D12; it is a fact
about the topology, and the only thing a reinforcement can do to it is add a support.

That reframes the whole milestone. A perimeter tension ring, a cover harness and a tube
instead of solid rod are all real answers to real failure modes, but none of them puts a
support in the middle of a bow, so none of them changes the size this family tops out
at. A hoop belt and a denser lattice do. Ranking the eight candidates on part count
before knowing which of them are even in the running would have compared a ring that
cannot lift the ceiling with a belt that can.

It also prices the question milestone 5 has been carrying: whether the thirty unlashed
crossings need clamps at all. They are worth **5/3 in span**, which is **2.78× in rod
diameter**. That is not an opinion about whether a rod-on-rod contact holds; it is what
the dome costs if it does not.

## What was rejected

- **Comparing candidates on the nine criteria directly.** Parts, unique types, threading
  actions and transport length are all computable today and all beside the point until a
  candidate is known to move the ceiling. They become the tie-break, not the test.
- **Waiting for milestone 8.** A ratio between two domes of the same shape needs no
  modulus, no strength and no load: the unknown constant in front of `w a⁴/EI` is the
  same for both, because they are the same shape. Waiting would have meant guessing.
- **Picking one allowable strain and quoting one ceiling.** Nobody has measured the
  stock. The answer is a curve against `e`, and the useful finding is that the curve
  crosses the range this project argues about: at 0.2% the ceiling is below D8, at 0.4%
  it is past D12.
- **Taking the optimistic reading of "held".** Counting every crossing as a support
  makes the span 36° instead of 60° and the ceiling nearly three times further out. It
  is also an assumption about a joint that may never get a part, so the conservative
  reading is the default and the optimistic one is a flag.

## What it costs

**The reference's own adequacy is assumed.** Every number here is a ratio to D6, and
nobody has built a D6 and watched it stand. If the reference is itself marginal, the
whole family moves with it and the ceilings above are the wrong size — though the
*ordering* of the candidates survives, because it depends only on the span.

**Self-weight is taken as the governing case.** It is the harsher of the two on the
ceiling, but only because the pressure case's fourth-power allowance pushes it past
anything buildable; which one actually governs a real dome in real wind is milestone 8,
and if it is pressure, the ceilings above are far too pessimistic.

**A support is counted as a support in both directions.** An unclamped crossing is a
one-way contact: it bears inward and separates outward. The `contact` reading therefore
flatters any load case that lifts the cover, which is exactly the case a temporary
structure cares about.
