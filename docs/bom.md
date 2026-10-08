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
  BASE3-10                   8       8     121.4      971.1   24.3%
  STAKE-BASE                10                            hardware
  HDR-8                      2                         nothing yet
```

**Volumes are of the solid part.** Real filament at a normal infill is roughly
half of it, and which half is a slicer's answer, not this project's. Nothing
here multiplies by a density.

## What it showed the first time it ran

**The base hubs were half the plastic in the dome.** On M, `BASE3` and `BASE2`
together came to 4040 cm³ of 6882 — 59% — and one `BASE3-10` was 430 cm³, of
which 258 was a single bottom plate. It was four and a half times the four-rod
fan that holds twice as many rods.

That was not news, exactly: [decision 0013](decisions/0013-the-bolt-is-half-the-rod.md)
had already recorded that the base hub does not scale, because its size was set
by the 30 mm stake slot and the bolt spread around it rather than by the rod.
What the list added was the price of it — and the price is what got the slot
looked at again.

**It is 3044 cm³ of 5886 now — 52%.** The slot is gone: the angle is met on a
pad on the outside of the bottom plate and closed in by a wrap, so the 31 mm
band the slot needed is no longer added to the whole plate. The lower stack
bolt pair is now enclosed by a broad flange shared by all plates. One
`BASE3-10` is 324 cm³, against 430 before the slot was removed. See
[decision 0025](decisions/0025-the-angle-is-met-on-a-pad.md)
for the pad, [0026](decisions/0026-the-loop-is-bought-not-printed.md) for the
bought loop that is now the alternative, and
[0027](decisions/0027-the-wrap-closes-the-fourth-side.md) for the wrap, and
[0028](decisions/0028-join-the-wrap-ears-and-add-upper-stack-bolts.md) for its
solid bridge and four stack bolts, and
[0029](decisions/0029-put-the-lower-stack-bolts-inside-the-base-plate.md) for
the lower flange.

**And 2753 cm³ of 5595 — 49% — since the stake became rebar.** The pad did not
change; the wrap went, and a vee cradle of about 30 cm³ took its place on the
same two bolts. One `BASE3-10` is 295 cm³. See
[0031](decisions/0031-the-stake-is-rebar-and-a-vee-takes-any-bar.md).

**And 1160 cm³ of 4001 — 29% — since base hub 2.0.** The plate stack is gone:
a hub is one print, a tube per bow on a rib, and a sleeve for the rebar. One
`BASE3-10` is 121 cm³. See
[0032](decisions/0032-the-base-hub-is-one-print.md).

`STAKE-BASE` is still the one position in the schedule with no answer at all,
and nothing about it is drilled. It is a rebar now, and no printed piece has
to follow its size: the cradle takes any bar from 8 to 18 mm. Until it is
chosen, the item the limiting wind speed hangs on is still sized by a guess.

## The fasteners are counted, and split

It used to say here that how many bolts a part takes is a property of the
generator that draws it and the schedule did not carry it. It carries it now —
and the number that matters is not the total but **where the work happens**:

```
  fastener          M5     half the rod, snapped (decision 0013)
    in the field    84     bolts, each with a nut and a tool at both ends; and 28 cross pins
    in the shop      0     bolts, done up once and never touched again
    hinged          52     field bolts instead, 32 fewer, if the clamps are built with the hinged closure
```

Each generator already stated its own field sequence and they do not agree: a
base hub has no stack and is only pinned at the dome, a fan node's
is opened and closed at head height. Adding the two together hid the only
number rule 1 cares about. See [`quick-release.md`](quick-release.md) for what
the 84 costs and [decision 0020](decisions/0020-the-hinge-is-worth-more-than-the-lever.md)
for the closure that removes a third of it.

The fastener line counts the M5 connector schedule. The two M8 set bolts in
each foot's rebar sleeve are specified on the FreeCAD parameter sheet and are
additional field hardware: twenty for the ten feet of M.

The other thing worth seeing: **107 parts is 169 prints.** A part is not a print
— the fan is five plates, a clamp two, the base hub one — and the
print farm
works in prints.

## What it does not count

**Money, and mass.** Both want a supplier and a material, and this project has
neither yet. The quantities are here for when it does.
