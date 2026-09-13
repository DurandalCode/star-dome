# What one dome is made of

Every other document here answers one question and counts what it needs to
answer it: [`cover.md`](cover.md) counts fabric, [`placement.md`](placement.md)
counts connectors, [`skirt.md`](skirt.md) counts posts. Nobody had ever added
them up. The dome was thoroughly measured as a **shape** and had never once
been measured as a **quantity**.

```bash
make clamps V=M          # build the parts, if you want the plastic column
make bom                 # or: python3 -m stardome bom M
```

## Where each number comes from

Nothing is computed twice. The parts come from `connectors.schedule`, the rod
from the model's own `meta`, the fabric from `cover`, the webbing and rope from
`attachment`, the posts and rings from the `skirt` block. This module joins
them and derives no geometry of its own — so a wrong number here is a number
that is already wrong somewhere else, and one place to fix it.

One number it takes care over: **how many sections a bow is cut into.** Dividing
the bow by the transport length gives the wrong answer, because a doorway cut
shortens two bows and each then wants one splice fewer. The count comes from the
splice schedule instead — a bow is cut into one more section than it has joints.
On XL that is 103 sections, not the 105 the division gives.

## The plastic is measured, not remembered

A connector's volume is a property of the drawn solid, and the drawn solid lives
in FreeCAD. Keeping a copy of that number in the source would guarantee it drifts
the first time a generator changes, so it is read off the exported meshes in
`exports/connectors` — the signed tetrahedra of each closed triangle mesh, summed.
Exact for a closed mesh, and it needs nothing installed.

So the column is **present when the parts have been built and honestly absent
when they have not**, rather than being an estimate either way:

```
  BASE3-10                   8      32     430.5     3444.1   50.0%
  STAKE-BASE                10                            hardware
  HDR-8                      2                         nothing yet
```

**Volumes are of the solid part.** Real filament at a normal infill is roughly
half of it, and which half is a slicer's answer, not this project's. Nothing
here multiplies by a density.

## What it showed the first time it ran

**The base hubs are half the plastic in the dome.** On M, `BASE3` and `BASE2`
together are 4040 cm³ of 6882 — 59% — and one `BASE3-10` is 430 cm³, of which
258 is a single bottom plate. It is four and a half times the four-rod fan that
holds twice as many rods.

That is not news, exactly: [decision 0013](decisions/0013-the-bolt-is-half-the-rod.md)
already recorded that the base hub does not scale, because its size is set by the
30 mm stake slot and the bolt spread around it rather than by the rod. What the
list adds is the price of it. `STAKE-BASE` is the one position in the schedule
with no answer at all, and until it has one the biggest single item in the dome
is sized by a guess.

## The fasteners are counted, and split

It used to say here that how many bolts a part takes is a property of the
generator that draws it and the schedule did not carry it. It carries it now —
and the number that matters is not the total but **where the work happens**:

```
  fastener          M5     half the rod, snapped (decision 0013)
    in the field    84     bolts, each with a nut and a tool at both ends; and 28 cross pins
    in the shop     20     bolts, done up once and never touched again
    hinged          52     field bolts instead, 32 fewer, if the clamps are built with the hinged closure
```

Each generator already stated its own field sequence and they do not agree: a
base hub's stack is bolted up at home and only pinned at the dome, a fan node's
is opened and closed at head height. Adding the two together hid the only
number rule 1 cares about. See [`quick-release.md`](quick-release.md) for what
the 84 costs and [decision 0020](decisions/0020-the-hinge-is-worth-more-than-the-lever.md)
for the closure that removes a third of it.

The other thing worth seeing: **107 parts is 197 prints.** A part is not a print
— the fan is five plates, the base hub four, a clamp two — and the print farm
works in prints.

## What it does not count

**Money, and mass.** Both want a supplier and a material, and this project has
neither yet. The quantities are here for when it does.
