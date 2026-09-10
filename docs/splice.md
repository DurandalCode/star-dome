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

**One part, used twice, with a bought stud between.** Each half is a steel
socket: bored for the rod at the outer end, tapped at the inner, and the two
pulled together by a stud. A male half and a female half would be two parts to
make, two to stock and two to pick up in a field with cold hands, for no gain
— **the stud is the male.**

    rod → [ bore, 6d ][ shoulder ][ thread ] | [ thread ][ shoulder ][ bore ] ← rod
                                            stud

M, on 10 mm rod:

| | |
|---|---|
| ferrule | 77 mm long, 40 g, 5.13 cm³ |
| the pair | 154 mm, against 379 mm of free span |
| bore | 10.4 mm, a slide fit |
| engagement | 60 mm, six rod diameters |
| joint end | 14.4 mm across, 4.65 mm of wall round the thread |
| mouth end | 12.0 mm across |
| over the rod | 4.4 mm at its widest |
| stud | M6 × 28 |
| pin | 4 mm at 22 from the mouth |
| **per dome** | 43 joints, **86 identical ferrules** |

**The outside tapers, and that is the whole design.** Steel needs 2 mm of wall
at the joint to hold a thread, which is 15.6× the rod's bending stiffness —
the joint does not share the curve and the bow takes the extra bend just
outside it. Thinning to 0.8 mm by the mouth spreads that step over the
engagement instead of standing it at one section, and takes the ratio there
down to **4.5×**. The taper is a parameter; turn it off and `verify` reports
both ends so the cost is visible rather than assumed.

The mouth is flared 0.35 mm over 2.5 mm, because a square bore edge is a
stress raiser on fibreglass — the same rule the crossing clamp follows.

Everything scales with `rodDiameter`: 8 mm for D3/D4, 10 for D6/D8, 12 for
D10/D12, with the stud and pin following it. One script, three sizes.

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
