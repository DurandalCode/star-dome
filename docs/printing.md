# Printing the connectors

Everything in `exports/connectors` is in the frame the part is **designed** in,
next to its STEP, its FreeCAD document and the reference rods — the right set
for CAD and for the Blender scene, and the wrong one for a slicer. `make
prints` turns it into Bambu Studio projects with the plates already laid out:

```bash
make clamps V=S                  # build the parts, and the print manifest
make prints V=S                  # exports/print/d4/
```

```
  d4_dome.3mf            every printed piece the dome needs, at its count,
                         arranged onto as many plates as it takes
  BASE3-8.3mf            one of that part: the fit check, or a spare
  CL2-8-70.5288.3mf      ...one per part
  stl/BASE3-8_Cap.stl    each piece on its print face, for any other slicer
```

Open the `.3mf` and print it plate by plate. For S that is **212 pieces on 12
plates** of a P2S. The arranging is Bambu Studio's own — `tools/print_plates.py`
drives its command line — so the project opens exactly as the GUI would have
packed it, and each piece is a separate object named after its file.

Every piece comes in **already on the face it prints on**. So in the slicer:
**place, do not rotate.** If a piece looks like it wants turning over,
something has changed in the part and the overhang numbers `make clamps`
reports no longer describe what is being printed.

The printer, process and filament are Bambu system presets — P2S, 0.4 mm
nozzle, `0.20mm Standard`, PETG Basic by default — with the three settings
below changed to what this page asks for. Any of the three presets is a flag:

```bash
tools/print_plates.py d4 --filament "Bambu PLA Basic @BBL P2S"   # fit check
tools/print_plates.py d4 --printer "Bambu Lab X1 Carbon 0.4 nozzle" \
    --process "0.20mm Standard @BBL X1C" --filament "Bambu PETG Basic @BBL X1C"
tools/print_plates.py d4 --stl-only          # no Bambu Studio installed
```

A piece wider than the plate is named and left out rather than scaled. Why it
is done this way rather than by laying beds out ourselves is
[decision 0030](decisions/0030-bambu-studio-arranges-the-plates.md).

## Which way up, per part

Each generator says which of its pieces print upside down, in
`FLIPPED_PIECES`, next to the overhang check that judged it; `make clamps`
copies that into the manifest and `make prints` turns those pieces over.

| part | turned over | why |
|---|---|---|
| base hub `BASE*` | Cap | below |
| fan node `FAN4-*` | Cap | its channel faces down in the part's frame |
| crossing clamp `CL2-*`, termination `TERM-*` | nothing | the cap's saddle prints as a bridged arch; turned over its ears overhang — [crossing-clamp-v1](crossing-clamp-v1.md#printability) |
| skirt collar `COLLAR-*` | Collar | brace arm up leaves about a third of the steep area arm down does |
| ferrule `SPLICE-*` | nothing | it lies down either way, and its bore wants support — it is the part best bought as tube, see `rod_splice_v2.py` |

## Which face each base hub piece sits on, and why

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
| `BASE3-8` | 5 | 8 | 40 | 2008 cm³ |
| `BASE2-8` | 4 | 2 | 8 | 364 cm³ |

**48 prints and 2372 cm³ of solid part.** Real filament is roughly half of
that at a normal infill — call it a kilogram — and which half is a slicer's
answer, not this project's. On a P2S's 256 × 256 plate one `BASE3-8` is **one
plate**, wrap included.

## Settings

A starting point, not a specification — **nothing here is a strength
calculation**, and what a printed connector actually carries is milestone 8:

- 0.4 mm nozzle, 0.2 mm layers;
- four perimeters, because every load in these parts is carried by the walls
  round a hole or a channel rather than by the infill;
- 30–40% infill;
- no supports, no brim needed on the flat faces these sit on.

The projects `make prints` writes carry the first three of those as changes to
the process preset: four walls, 35% infill, supports off.

## The ten feet are one geometry

Five of the ten base points are the mirror of the other five, and the hub
serves both by being **turned over** — a rotation, not a reflection. There is
no mirrored print of anything, and the wrap has a relief at both ends for the
same reason. Print the same files ten times.
