# The span between supports

[`tolerance.md`](tolerance.md) asks how accurately a bow has to be cut and
marked. This asks the question underneath it: **a bow is held at some points
and free between them — how far apart are those points, and what happens to
that distance when the dome gets bigger?**

It is the first thing in this project that is not about shape. The topology
scales to any diameter: every angle in it is the same at D3 and at D12, which
is what makes the family a family. What does not scale is the rod.

```bash
make spans                              # every variant, both numbers
python3 -m stardome span M --clamps
python3 -m stardome span D12 --holds contact
```

## What holds a bow is a decision, not a fact

A bow touches other rods at every crossing, but touching is not holding. Ten of
the forty crossing points are lashed junctions with a printed connector; the
other thirty are rod-on-rod contacts that may never get a part at all —
[milestone 5](roadmap.md) has not decided. So there are two readings, and the
gap between them *is* the decision:

- **`lashed`** — a bow is held at its two feet and its tie marks, and nowhere
  else. This is the position [decision 0012](decisions/0012-mismatch-is-measured-against-bending.md)
  and `tolerance.held_spans` already take, and it is the conservative one.
- **`contact`** — every crossing holds, because every crossing got a clamp.

Family G is marked in fifths and families U and L in thirds, so the two
readings disagree about which family is weak — and they swap:

| held at | G | U and L | the dome's worst |
|---|---|---|---|
| lashed nodes only | 36° | **60°** | 60°, on U and L |
| every crossing | **36°** | 22.24° | 36°, on G |

Clamping the free crossings does nothing at all for family G — all four of its
crossings are already lashed nodes — and cuts U and L from 60° to 22.24°.

On D6 that is **3142 mm against 1885 mm**. The ratio is exactly 5/3 at every
size, and because the rod that holds a span goes as the square of it, the
thirty clamps are worth **2.78× in rod diameter**. That is the first number
anybody has put on them.

## The span is a fraction of the radius, and that is the whole scaling story

The worst span is `1.0472 R` under the conservative reading — 60° of arc — at
every variant, because the dome is similar to itself at every size:

| variant | worst span, lashed | with every crossing clamped |
|---|---|---|
| D3 | 1571 mm | 942 mm |
| D4 | 2094 mm | 1257 mm |
| D6 | 3142 mm | 1885 mm |
| D8 | 4189 mm | 2513 mm |
| D10 | 5236 mm | 3142 mm |
| D12 | 6283 mm | 3770 mm |

## What that does to the rod

Two domes here are geometrically similar, so one bow between two supports can
be compared with another directly:

    sag  ~  w a⁴ / (E I),    I ~ d⁴

The constant in front — end fixity, arch action, the part of the load a bent
rod carries in compression rather than bending — is not known here and does not
need to be: **it is the same constant for both domes, because they are the same
shape.** The ratio survives even though neither sag is computed.

Two load types scale differently, and both are reported because which one
governs is [milestone 8](roadmap.md)'s to say:

- **self-weight** — `w ~ d²`, so the sag ratio is `(a/a₀)⁴ (d₀/d)²`;
- **pressure on the cover** — the lattice carries wind or snow over a strip as
  wide as the spacing between neighbouring rods, which scales with R, so
  `w ~ pR` and the ratio is `(R/R₀) (a/a₀)⁴ (d₀/d)⁴`.

Measured against D6, the reference prototype:

| variant | rod configured | similarity asks | sags, self-weight | rod for equal sag |
|---|---|---|---|---|
| D8 | 10 mm | 13.3 mm | 3.2× | 17.8 mm |
| D10 | 12 mm | 16.7 mm | 5.4× | 27.8 mm |
| D12 | 12 mm | 20.0 mm | 11.1× | 40.0 mm |

`configs/variants.toml` says in as many words that its rod diameters are
provisional assumptions rather than results. This is the first check of them,
and it says they do not scale: past the reference, **every variant carries a
rod thinner than plain similarity asks for**, and D12 is 11× slacker between
supports than the dome it is derived from.

## Two constraints, pulling opposite ways

To keep the reference's sag the rod must be **at least** `d₀(a/a₀)²`. To be bent
to the dome radius at all, its outer fibre must survive `d / 2R`, so for an
allowable strain `e` it may be **at most** `2Re`. One grows as `R²`, the other
as `R`. They cross exactly once, and that crossing is the largest dome of this
family that can be built at all:

    R_max  =  ( 2 e R₀ᵖ / (d₀ kᑫ) ) ^ 1/(p−1)

| allowable strain | 0.2% | 0.4% | 0.6% | 0.8% |
|---|---|---|---|---|
| largest dome, self-weight parity | **7.2 m** | 14.4 m | 21.6 m | 28.8 m |
| largest dome, pressure parity | 12.4 m | >100 m | >100 m | >100 m |

The pressure row never binds — it grows as the fourth power of the allowance.
The self-weight row does, and it lands inside the range this project is
actually arguing about: **at 0.2% allowable strain the ceiling is below D8; at
0.4% it is past D12.**

So the practical ceiling for this family is not set by the topology, and not by
anything in this repository. It is set by one material number nobody has
measured yet — [milestone 3](roadmap.md)'s one open item that depends on nothing
else. The dome already proposed for building works its rod at 0.167%.

`k` is the span factor: the worst span as a fraction of the bare topology's.
Because it enters squared, **halving the worst span multiplies the ceiling by
four.** That is why every reinforcement candidate in milestone 7 is measured
against the span and not against the others.

## What this is not

There is no modulus, no strength and no load anywhere in it. These are ratios
between two domes of the same shape, and the reference's own adequacy is
assumed rather than shown — nobody has yet built a D6 and watched it stand.
`2s/a²` and `d/2R` are geometry; everything that turns them into a verdict is
milestones 3 and 8.
