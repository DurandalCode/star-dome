# How much room you actually get

The goal is a room for a live-action event. So the number that decides a
variant is not its diameter and not its peak height — it is **how many square
metres a person can stand up in**. A dome is bad at that: the ceiling falls
away from you everywhere except the middle.

```bash
python3 -m stardome interior --all
python3 -m stardome interior D3 --skirt 1600
make interiors
```

The interior surface is taken as the sphere the bows lie on. The rods stop
short of the zenith and a cover pulled over them sits a little inside, so these
areas are the optimistic case by a few percent.

## Bare domes

Standing height taken as 1800 mm.

| variant | floor | you can stand in | of floor | volume | m² per m of rod |
|---|---|---|---|---|---|
| D3 | 7.07 m² | 0.00 m² | 0% | 5.3 m³ | 0.000 |
| D4 | 12.57 m² | 2.39 m² | 19% | 16.8 m³ | 0.025 |
| D6 | 28.27 m² | 18.10 m² | 64% | 56.5 m³ | 0.128 |
| D8 | 50.27 m² | 40.09 m² | 80% | 134.0 m³ | 0.213 |
| D10 | 78.54 m² | 68.36 m² | 87% | 261.8 m³ | 0.290 |
| D12 | 113.10 m² | 102.92 m² | 91% | 452.4 m³ | 0.364 |

A bare D4 has twelve and a half square metres of floor and **two and a half you
can stand in**. That is the shape of the problem at the small end.

## What the skirt is actually worth

D3, standing height 1800 mm:

| skirt | you can stand in | of floor | overall height | tip index | rod | m²/m |
|---|---|---|---|---|---|---|
| 0 | 0.00 m² | 0% | 1473 mm | 0.424 | 71 m | 0.000 |
| 500 | 1.76 m² | 25% | 1973 mm | 0.582 | 85 m | 0.021 |
| 800 | 3.93 m² | 56% | 2273 mm | 0.678 | 88 m | 0.045 |
| **1000** | **5.06 m²** | **72%** | 2473 mm | 0.743 | 90 m | 0.056 |
| 1300 | 6.28 m² | 89% | 2773 mm | 0.841 | 93 m | 0.067 |
| 1600 | 6.94 m² | 98% | 3073 mm | 0.939 | 96 m | 0.072 |
| 2000 | 7.07 m² | 100% | 3473 mm | 1.071 | 100 m | 0.071 |

**A 3 m dome on a 1 m skirt has more than twice the standing room of a bare 4 m
dome**, on a smaller footprint, at better than twice the rod efficiency. It no
longer uses *less* rod: bracing the skirt properly ([`skirt.md`](skirt.md))
adds a second ring, and D3 + 1 m now spends 99 m against a bare D4's 94, plus
27 m of strap. The "silo" is still not the compromise it looks like, but it is
no longer the cheap option.

And D6, with the 760 mm of skirt a walk-in door needs anyway
([`entrance.md`](entrance.md)):

| | standing room | of floor | overall | tip index | m²/m |
|---|---|---|---|---|---|
| D6 bare | 18.10 m² | 64% | 2947 mm | 0.424 | 0.128 |
| D6 + 760 | **24.88 m²** | **88%** | 3707 mm | 0.543 | 0.148 |

38% more standing room, 16% better rod efficiency, and the door — for 760 mm of
height on a 6 m dome. **This is probably what the reference prototype should
be.**

## The one thing it costs

Everything above improves. The price is paid in exactly one place: **wind.**

`tip_index` is the ratio of the overturning arm to the righting arm, per unit
of sail area — the silhouette's centroid height over the base radius,
dimensionless and comparable between variants. A bare dome sits at **0.424 at
every size**, because the shape is self-similar. A skirt raises it, and the
silhouette area grows at the same time, so the anchoring demand rises on both
counts.

It is a shape comparison. There is no pressure coefficient in it and it proves
nothing about safety.

Two things follow:

- **Standing room saturates; tipping does not.** D3's floor is fully usable at
  about 1.6 m of skirt. Going to 2.0 m adds 2% of area and another 0.13 to the
  tip index. Past saturation a taller skirt is pure cost.
- **The skirt is the part that has to be braced.** `docs/skirt.md`: ten pin-ended
  verticals and a ring rack under any sideways load, and the taller they are
  the worse it is. The wind penalty and the bracing problem are the same
  problem.

## D4 on a skirt, and why it retires D3

Standing height 1800 mm. `slenderness` is overall height over diameter — at 1.0
the thing is taller than it is wide, which is when it stops reading as a dome.

| skirt | you can stand in | of floor | overall | tip index | slenderness | rod | m²/m |
|---|---|---|---|---|---|---|---|
| 0 | 2.39 m² | 19% | 1964 mm | 0.424 | 0.50 | 94 m | 0.025 |
| 500 | 7.26 m² | 58% | 2464 mm | 0.542 | 0.62 | 112 m | 0.065 |
| 800 | 9.42 m² | 75% | 2764 mm | 0.614 | 0.70 | 115 m | 0.082 |
| **1320** | **11.84 m²** | **94%** | 3284 mm | 0.740 | 0.83 | 120 m | 0.099 |
| 1800 | 12.57 m² | 100% | 3764 mm | 0.857 | 0.95 | 125 m | 0.101 |

1320 mm is the skirt a walk-in 1800×700 door needs on D4
([`entrance.md`](entrance.md)), and it lands almost exactly on saturation: the
last 480 mm of skirt buys 6% more area for another 0.12 of tip index.

Set that against D3 carrying the same door:

| | standing room | of floor | overall | tip index | slenderness | rod | m²/m |
|---|---|---|---|---|---|---|---|
| D3 + 1600 | 6.94 m² | 98% | 3073 mm | 0.939 | **1.03** | 96 m | 0.072 |
| D4 + 1320 | **11.84 m²** | 94% | 3284 mm | **0.740** | 0.83 | 120 m | **0.099** |

**D4 + 1320 beats D3 + 1600 on every axis that matters** — 70% more standing
room, a materially lower tip index, 37% better rod efficiency — and it is still
wider than it is tall where D3 is not. D3 pays for its smaller footprint twice:
once in area and once in stability. Two things stay in D3's favour: the 3 m
footprint itself, and 96 m of rod against 120 m.

So **D3 + skirt is dominated**, and the earlier "D3 on a skirt beats a bare D4"
result is true but the wrong comparison — the honest one is skirt against
skirt. Choose D3 only when the site is too small for 4 m.

The same sweep across the family, each with the skirt its walk-in door needs:

| | skirt | standing room | of floor | tip index | slenderness | m²/m |
|---|---|---|---|---|---|---|
| D3 | 1600 | 6.94 m² | 98% | 0.939 | 1.03 | 0.072 |
| D4 | 1320 | 11.84 m² | 94% | 0.740 | 0.83 | 0.099 |
| D6 | 760 | 24.88 m² | 88% | 0.543 | 0.63 | 0.148 |
| D8 | 250 | 42.72 m² | 85% | 0.453 | 0.53 | 0.198 |
| D10 | 0 | 68.36 m² | 87% | 0.424 | 0.50 | 0.290 |
| D12 | 0 | 102.92 m² | 91% | 0.424 | 0.50 | 0.364 |

Every column improves monotonically with size. **Bigger is simultaneously more
efficient and more stable**, because the skirt a door needs shrinks faster than
the dome grows. The expected trade — big domes buy room at the cost of
exposure — does not exist once the door requirement is held constant.

## What this suggests

- **D6 + 760 mm skirt** as the reference: a walk-in door, 88% of the floor
  usable, a modest tip penalty.
- **D3 + 1300–1600 mm skirt** as a small sleeping pod, accepting a tip index
  near 0.9 and the anchoring that implies. Not a public space.
- **D10 and above** need no skirt for either headroom or a door.
- **D4 wants a skirt more than any other size, and repays it best.** Bare it is
  the worst of the family — 19% of its floor usable, the lowest rod efficiency
  of any dome that works at all. On a skirt it is the best thing at the small
  end; see below.

None of this is a structural calculation. It is geometry and a shape
comparison, which is enough to choose a size and not enough to build one.
