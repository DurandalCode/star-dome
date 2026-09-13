# Printing the connectors

Everything in `exports/connectors` is in the frame the part is **designed** in,
which is the wrong frame for a bed. `make prints` writes a second set that is
in the right one:

```bash
make prints V=S BED=220x220      # exports/print/d4/
```

Each piece comes out **turned onto the face it prints on and dropped so that
face is z = 0**, and the same pieces come out again packed onto beds:

```
  BASE3-8_Bottom.stl   one piece, ready to place
  BASE3-8_bed1.stl     a bedful, already arranged
```

So in the slicer: **place, do not rotate.** If a piece looks like it wants
turning over, something has changed in the part and the overhang numbers
`make clamps` reports no longer describe what is being printed.

## Which face each piece sits on, and why

| piece | on the bed | why |
|---|---|---|
| Bottom | its outer face — the one the angle lies against | that face is flat, and everything the pad offers the angle is on it |
| Mid1, Mid2 | lower face | channel up, so each groove is an open half-pipe |
| Cap | its outer face, **upside down** | the cap's channel faces down in the part's frame; flipped, it faces the nozzle |
| Wrap | its base | every pocket in it then opens upwards |

That table is the whole reason the joint looks the way it does. The angle lies
against the face the bottom plate is printed on, so nothing printed with the
plate can reach round the far side of it — which is why the pad is flat and
why the wrap is a separate piece
([decisions 0025 and 0027](decisions/0027-the-wrap-closes-the-fourth-side.md)).

## No supports

Not "supports off if you like": **the part is drawn so that it does not need
them**, and `make clamps` prints the evidence per piece — worst overhang, and
how much area is steeper than 45°. On the base hub that area is zero on every
piece. Rod channels are horizontal holes and print as bridges, the same as any
horizontal hole in any printed part.

If a slicer proposes supports, it is proposing them for a geometry this
project has not checked. Find out what changed before printing it.

## The first print is a fit check, not a part

PLA is fine for it and is not fine in a field: the joint at the foot holds by
**clamp**, and PLA creeps under a preload faster than anything else on the
shelf. It also does not like sun. The field material is PETG or ASA; the
numbers quoted in the decision records assume PETG.

What the first hub is printed to answer:

- **the rod channels.** 1.4 mm diametral clearance on a nominal rod, meant as
  a slide fit — push the real rod in and see. Composite rebar measures over its
  winding, which is what `rodNominalDiameter` is for;
- **the nut pockets.** An M5 nut has to drop into the bottom plate and stay
  put; the two M8s have to drop into the pad;
- **the wrap on a real angle.** It is drawn round L30 with 0.4 mm of fit, and
  the angle that gets bought will not be exactly L30;
- **the bolt lengths** in the parameter sheet: `stackBolt` and `stakeBolt`;
- **the cross pins**, one per arm.

None of that needs eight hubs. Print one `BASE3-8`, fit it to a rod and an
angle, and change the numbers in the sheet before printing the rest.

## What one dome's feet cost to print

For S, with the rod at 8 mm:

| | pieces each | hubs | prints | solid plastic |
|---|---|---|---|---|
| `BASE3-8` | 5 | 8 | 40 | 1594 cm³ |
| `BASE2-8` | 4 | 2 | 8 | 264 cm³ |

**48 prints and 1858 cm³ of solid part.** Real filament is roughly half of
that at a normal infill — call it a kilogram — and which half is a slicer's
answer, not this project's. On a 220 × 220 bed one `BASE3-8` takes **two
beds**: the four plates together, and the wrap on its own.

`make prints` reports the packing and refuses to scale anything: a piece that
does not fit the bed is named rather than shrunk.

## Settings

A starting point, not a specification — **nothing here is a strength
calculation**, and what a printed connector actually carries is milestone 8:

- 0.4 mm nozzle, 0.2 mm layers;
- four perimeters, because every load in these parts is carried by the walls
  round a hole or a channel rather than by the infill;
- 30–40% infill;
- no supports, no brim needed on the flat faces these sit on.

## The ten feet are one geometry

Five of the ten base points are the mirror of the other five, and the hub
serves both by being **turned over** — a rotation, not a reflection. There is
no mirrored print of anything, and the wrap has a relief at both ends for the
same reason. Print the same files ten times.
