# 0018. Put the site layout in its own config, and turn a dome rather than re-drill it

- **Status:** accepted
- **Date:** 2026-09-12
- **Where it lives:** `configs/camps.toml`, `stardome/camp.py`, `blender/build_site.py` (`--plan`), `docs/camp.md`

## The decision

A camp — several domes joined by corridors — is described in **`configs/camps.toml`**,
a file of its own. It says which domes stand where, how far each is turned, and which
pairs are joined. Nothing else.

Everything else is derived: the bearing between two domes from their positions, which
door that bearing wants from `variants.toml` plus the turn, the corridor's length from
the gap the two covers leave, and the two mouths from each cover.

**A door comes to face a neighbour because the dome is turned on the ground**, not
because a doorway is cut for the site. `turn` rotates the dome and its doors with it.

## Why

A camp is not a property of a dome, so it does not belong in `variants.toml`. The same
D6 stands in two camps facing two different ways, and the dome does not change.

The alternative was to let a camp override a dome's doors, and that is the arrangement
that rots: the bearing to a neighbour would be written in the camp file and the door
aimed at it written in the variant file, and the first time a dome moved they would stop
agreeing with nobody told. So a link says only *what it joins*. Move a dome and the
bearing, the door check, the corridor's length and both mouths all follow.

Turning rather than re-drilling falls out of the same argument. A dome is a rigid thing
you set down at an angle; a doorway is a cut in the lattice that costs rod and parts.
Aiming a site by turning costs nothing and cannot disagree with the design.

## What was rejected

- **Doors overridden per camp.** Two files describing the same door, and the geometry
  free to differ from the parts list.
- **Deriving the turn automatically.** Tempting, and right for a dome with one
  neighbour. With two it is an optimisation with no obviously correct answer, and it
  would have quietly rotated a dome away from a door the designer aimed on purpose. The
  plan reports the turn each link would want and a person chooses.
- **A corridor length in the config.** It is not a free number. It is what two covers
  leave between them, and writing it down is writing down something already determined.
- **Refusing to draw a plan that will not build.** A corridor that does not fit its
  doorway is reported and drawn. Drawing it before building it is the entire point, and
  a tool that only draws what already works cannot show you what does not.
- **A third scene script.** `build_site.py` grew a `--plan`; the dome-drawing loop it
  already had is what a camp needs, and only the layout and the corridors differ. There
  are already two scene scripts with a copy of `add_skirt` each, and they have drifted.

## What it costs

**A dome in the middle of a camp needs a door per neighbour, and the plan can only say
so.** The shipped `yard` camp is shipped wrong on purpose for that reason: the hall has
two neighbours and one door. Fixing it means giving D8 a second doorway in
`variants.toml`, which costs rod and two part types, and that is a decision about the
dome rather than about the site.

**The corridor joint is drawn, not designed.** Where a tunnel meets a dome there is a
hole in the cover, a hoop that has to land on something, and a load path across the
joint. None of that exists. `stardome camp` reports the shape of the gap and nothing
about what closes it — milestones 5 and 8.

**`make camp` changed meaning.** It used to render a row of one of each size, which was
never a camp; that is now `make lineup`, and `make camp` builds from a plan.
