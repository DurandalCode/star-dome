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
