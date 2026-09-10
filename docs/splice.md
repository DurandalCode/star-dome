# The section ferrule

```bash
python3 -m stardome splice M
```

> **Screening, not a structural check.** No live load, no creep, no code, no
> factors. Nothing here says any of these is safe — that is milestone 8.

A bow is nine metres, travels in 2400 mm sections, and is **bent everywhere**.
So the sleeve joining two sections is not a tension coupler: it carries
bending, continuously, along a member with no straight part in it.

That changes which material wins, and it inverts the intuition.

## Strength is the easy half

    M = E_rod · I_rod / R          σ_rod = E_rod · d / 2R

M's 10 mm rod at R = 3000 carries **6.5 N·m and 67 MPa just from being the
shape it is** — comfortable for GFRP, and every material below survives it at
a wall you could actually make. Strength does not decide this.

## Stiffness does, and the metals lose

A sleeve much stiffer than the rod does not share the curve. The bow goes
straight through the joint and takes the extra bend just outside it — a stress
riser exactly where the section changes. Matching `E·I` is what keeps the
curvature continuous.

M, sorted by how well each matches:

| material | wall mm | OD | stiff × | stress | use | g each | kg/dome | governed by |
|---|---|---|---|---|---|---|---|---|
| printed PLA | 4.22 | 18.8 | **1.0** | 11.0 | 0.55 | 28.8 | 1.30 | stiffness |
| printed PETG | 5.40 | 21.2 | **1.0** | 7.4 | 0.41 | 40.9 | 1.84 | stiffness |
| printed nylon-CF | 3.17 | 16.7 | **1.0** | 16.7 | 0.42 | 19.4 | 0.87 | stiffness |
| aluminium 6061 | 0.80 | 12.0 | 1.6 | 88.5 | 0.59 | 9.1 | 0.41 | what can be made |
| stainless 304 | 0.80 | 12.0 | 4.4 | 88.5 | 0.74 | 27.0 | 1.22 | what can be made |
| steel, mild | 0.80 | 12.0 | 4.5 | 88.5 | 0.63 | 26.5 | 1.19 | what can be made |
| cast aluminium | 3.00 | 16.4 | 10.6 | 18.0 | 0.30 | 40.6 | 1.83 | what can be made |
| cast bronze | 3.00 | 16.4 | 15.2 | 18.0 | 0.20 | 133.4 | 6.00 | what can be made |

**To match a GFRP rod's bending stiffness, steel would need a 0.2 mm wall.**
The thinnest tube anyone sells is four times that, so any makeable steel sleeve
is 4–5× too stiff. Casting is worse: a 3 mm minimum wall puts it at 10–15×.

**Printed plastic matches by construction**, because its modulus is *low*. PLA
wants 4.2 mm of wall, which is an easy print, and lands on 1.0.

**Aluminium is the only metal that comes close** — 0.55 mm would match, and
the thinnest drawn tube is 1.6×. It is also the lightest option by a good
margin, 0.41 kg per dome against PLA's 1.30.

So the honest reading is a two-horse race: printed plastic for the curve,
drawn aluminium for the weight and the durability — and **creep is what
decides it**, which is a test, not a formula.

## And it has to miss the crossings

The project has required that from the start. It turns out the obvious section
count often violates it.

Sections divide the bow evenly, so joints land at fixed fractions of its 180°.
Three sections puts them at 60° and 120° — and the star has crossings at
exactly 60° and 120°.

**Not bad luck: the same construction twice.** The U and L bows are *marked in
thirds* — that is the reference's own rod-marking scheme, `MARKS_THIRDS` in
`geometry.py` — and a third of 180° is 60 and 120. The crossings sit on those
marks because sitting on the marks is what the marks are for. Dividing a bow
into three puts a joint at the third points too, so the two constructions are
the same construction and collide by definition.

Which means it is not one near miss but **twenty exact hits**: ten U and L
bows, two joints each, dead centre. And it is not only three — any section
count that is a multiple of three does it, which is why six fails as well.

The G bows are marked in fifths (36, 72, 108, 144), so they collide with
counts that are multiples of five. Which makes the rule exact:

> **A section count divisible by 3 or by 5 lands joints dead on crossings.
> Any other count clears.**

3, 6, 9, 12 hit the thirds; 5 and 10 hit the fifths; 2, 4, 7, 8, 11, 13 are
clean. Clearing at all is not the same as clearing by more than half a
sleeve, though, which is why D12 has to get past 8 (0.26°, 27 mm) and 11
(0.42°, 44 mm) before 13 gives it 88 mm and enough room.

| | transport allows | joints clear? | use | cost |
|---|---|---|---|---|
| D3 | 2 | yes, 203 mm | 2 | — |
| S D4 | 3 | **no — dead on** | 4 | +15 splices |
| M D6 | 4 | yes, 379 mm | 4 | — |
| L D8 | 6 | **no — dead on** | 7 | +15 splices |
| XL D10 | 7 | yes, 303 mm | 7 | — |
| D12 | 8 | **no — 27 mm** | 13 | +75 splices |

Half the family lands a splice on a crossing if you just take the transport
minimum. `splice.choose_sections` searches upward for the first count that
clears, and reports what it cost.

**D12 pays worst**: 8 sections becomes 13, five extra per bow, seventy-five
extra splices over the dome. One more way the top of the range is the awkward
end.

## The part

`connectors/splice_v1.py`, built by `make clamps` like the others.

**A length of tube. One per joint, and nothing else to make.** The rods enter
from both ends and butt in the middle; one cross fastener each side holds them
in. No thread, no shoulder, no stud.

    rod ────→[══════════════════╪══════════════════]←──── rod
             o                                      o
            bolt             they butt             bolt

M, on 10 mm rod:

| | |
|---|---|
| sleeve | 120 mm long, 26 g, 3.31 cm³ |
| stock | **12 × 0.8 tube, cut to length** |
| against | 379 mm of free span |
| bore | 10.4 mm, a slide fit |
| engagement | 60 mm each end, six rod diameters |
| over the rod | 2.0 mm, all the way along |
| fastener | 4 mm at 22 from each end, the two at right angles |
| **per dome** | 43 joints, **43 sleeves** |

### Why it stopped being two halves and a stud

The first draft was a male–female pair pulled together by a threaded stud.
Two things were wrong with it, and both are worth keeping written down.

**The stud carried a load the joint does not have.** A bow is an arch: along
its length it is in compression, and compression crosses a butted joint end to
end through the fibreglass itself, which is the strongest thing GFRP does.
Tension and torsion are what actually need holding, and a cross fastener holds
both.

**And the thread was the only reason the wall was thick.** Tapping needs 2 mm
of meat round the hole, and 2 mm of steel is 15.6× the rod's bending
stiffness. That was the whole problem with the part, and it was self-inflicted:

| wall | 0.8 | 1.0 | 1.2 | 1.5 | 2.0 |
|---|---|---|---|---|---|
| EI / rod EI | **4.5** | 6.0 | 7.6 | 10.3 | 15.6 |

The old design reached 4.5× only at the very mouth, by tapering the outside
away from a 15.6× middle. A plain tube is 4.5× along its whole length — so the
taper had nothing left to soften and went too, along with a part number and
two thirds of the weight per joint.

### Why 0.8 is not an arbitrary minimum

At 0.8 the outside diameter lands on a size tube is actually drawn in, with
the bore coming out exactly right:

| rod | bore | tube | over the rod | EI / rod EI |
|---|---|---|---|---|
| 8 | 8.4 | **10 × 0.8** | 2.0 | 6.1 |
| 10 | 10.4 | **12 × 0.8** | 2.0 | 4.5 |
| 12 | 12.4 | **14 × 0.8** | 2.0 | 3.6 |

No other wall does that. At 1.0 a 10 mm rod wants a 12.4 OD, which is not a
size; the nearest stock is 14 × 1.0, whose bore is 12 — 2 mm of slop on a
10 mm rod. The stiffness optimum and the buyable part are the same part, and
`materials.SLEEVE` already said so: `steel_mild` is recorded as *drawn tube,
cut to length*, `min_wall` 0.8.

The wall stays 0.8 at every size while the rod grows, so **the joint gets
softer as the dome gets bigger** — 6.1× on D3, 3.6× on D12. The end of the
range that needs it most is the end that gets it.

The mouth is flared 0.35 mm over 2.5 mm at both ends, because a square bore
edge is a stress raiser on fibreglass — the same rule the crossing clamp
follows, and here it is also where the rod leaves and starts bending again.

**The fastener is a field choice, not a part change.** The sleeve is a tube
with two cross holes; what goes through them does not change it. A bolt and
nut is captive and comes apart with a spanner; a spring pin drops into the
same hole and needs no nut, at the cost of a hammer. Either, or one of each.
The two holes are drilled at right angles so neither rod loses width in the
same direction as its neighbour.

The rod is drilled through the sleeve's own hole at assembly, so the sleeve is
its own drilling jig and a rod cannot sit short of the butt. That matches the
two rods to that joint; they get marked as a pair.

Everything scales with `rodDiameter`: 8 mm for D3/D4, 10 for D6/D8, 12 for
D10/D12, with the fastener following it. The wall does not scale — it is the
least steel is drawn in at every size. One script, three sizes.

## What this does not settle

- **Only the moment from being bent to shape.** Wind, snow and handling add to
  it. Milestone 8.
- **Creep**, which is the strongest argument against the printed answer and
  the one this calculation cannot see. A PLA sleeve under constant bending for
  a season is a different question from one under a test load for a minute.
- **Temperature and UV** on a plastic part in the sun.
- **The grip itself** — bonded, pinned, swaged, taper. The bearing figure here
  is a first approximation, not a joint design.
- Material properties are nominal. Confirm against data sheets.
