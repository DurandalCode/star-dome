# The camp

```bash
python3 -m stardome camp
make camp CAMP_KIND=portal
```

Several domes joined by corridors. The layout is **solved**, not drawn, and
the reason is one number.

## Five bays, and only five

A dome has five tall bays, 72° apart, and a corridor has to land in one. Turn
the dome and all five turn with it. So:

- **Five neighbours maximum**, each on its own bay.
- **Every corridor runs along a bay azimuth at both ends.** Two domes cannot
  be joined at whatever angle the site suggests — the pair has to agree, and
  agreeing means turning at least one of them.
- **A tree always solves.** A dome's rotation is free until its first corridor
  lands; that one fixes the other four. So hang the camp off a hub and every
  branch can be made to work.
- **A loop usually does not.** Closing a cycle needs the last corridor to
  emerge at a bay already pointing the right way, and a 72° grid rarely
  obliges. `camp.solve` refuses rather than fudging the angle.

## How far apart

Not a guess. The corridor's mouth stands a known distance from each dome's
centre — the cover is a sphere, so it is the same in every direction — and
the gap between the two mouths is the corridor itself:

    centre distance = reach(A) + length + reach(B)

## The default camp

`L M S S S`, linked `L:M L:S1 L:S2 M:S3` — a hall with three ways out of it,
one of which leads on to a fourth dome.

| dome | stands at | turned | corridors | bays left |
|---|---|---|---|---|
| L | 0.0, 0.0 m | 0.0° | 3 | 2 |
| M | +5.9, +8.2 m | 252.0° | 2 | 3 |
| S1 | −5.3, +7.3 m | 324.1° | 1 | 4 |
| S2 | −8.6, −2.8 m | 36.1° | 1 | 4 |
| S3 | +10.7, +1.7 m | 144.0° | 1 | 4 |

Bearings 54.0°, 126.1°, 198.1° off L — consecutive bays — and 306.0° off M.
Footprint 19.3 × 11.0 m between centres; 12 m of corridor in four runs,
20 hoops, 88 m of rod.

**L still has two bays free and M three.** The camp can grow to nine domes
before the hub runs out of places to put a door.

## Both ends are cut

A corridor between two domes is square at neither end. Each end follows its
own dome's cover — sphere above the base ring, cylinder through the skirt —
and the two domes rarely share a skirt height, so the corridor is solved on
the shared ground rather than in either dome's frame.

That is why `camp.geometry` emits **world** coordinates: a corridor belongs to
two domes at once and has no frame of its own.

## What is checked

- every corridor lands in a bay at both ends;
- the graph is a tree, connected, and no dome is over-subscribed;
- both mouths lie on their own dome's cover;
- `camp.clashes` catches neighbours whose covers overlap — a layout that
  solves can still collide, and shortening the corridors far enough proves it.

## What this does not do

No structure, no ground modelling, no drainage, no fire separation, no
guy-line clashes between neighbours, no wind on a group of domes rather than
one. It answers where the domes stand so their doors line up, and what the
corridors cost. See [`corridor.md`](corridor.md) for the two kinds.
