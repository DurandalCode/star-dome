# 0014. Hang the cover on the stakes the dome already stands on

- **Status:** accepted
- **Date:** 2026-09-12
- **Where it lives:** `stardome/attachment.py`, `docs/cover.md`

## The decision

The cover is held by three things and none of them is a new part:

- **a bolt rope in a hem** all round the base edge — a continuous line in a sewn sleeve,
  not a row of eyelets;
- **ten loops**, one per foot, dropped over the driven steel angle already there;
- **five straps over the crown**, laid along the bows of family U, each ending on the two
  angles its bow already stands on.

On M that is 17.2 m of rope, 50.4 m of webbing, 10 anchors and **zero printed parts**.

## Why

Milestone 5 asks for an attachment that does not concentrate load on one printed part.
The way to satisfy that is not a better lug: it is no lug. The driven angle at each foot
is the one thing in the structure whose whole job is resisting uplift, through soil. The
cover's job is the same job. Giving it a separate anchor would be a second system to get
wrong, and it would put a tearing load into plastic that is already carrying the frame.

A rope in a sleeve rather than eyelets for the same reason one size down: **fabric tears
from a point and does not tear from a line.** The hem turns the whole base edge into one
member, and the sag between feet is the fabric's own problem rather than a fastener's.

The straps are where the geometry does the work. A cover held only at its edge lifts in
the middle, which is where a dome's uplift is worst — but every bow runs foot to foot, so
a strap laid along one needs no anchor of its own. It ends on angles that already exist.

And the family is not a preference. All three touch every foot **exactly once**, so any
of them shares the anchors out evenly; U is the one that reaches the dome's own height,
2947 mm on M, where G stops at 2683 and L at 1821. Five straps, ten ends, ten feet, one
each. `tests/test_attachment.py` checks both halves of that, because a family that
doubled up would leave one angle with two straps and another with none.

## What was rejected

- **Webbing loops at the lashed nodes.** The obvious answer, and it is exactly the load
  concentration the milestone names: a fan node is five printed plates holding four rods,
  and hanging a cover off it adds a peeling load to a part chosen for none.
- **Eyelets round the hem.** Every eyelet is a point, and a point in a coated fabric
  under wind is where the tear starts.
- **A separate ring of ground pegs for the cover.** Twice the anchors, twice the driving,
  and the dome's own anchors sit right there unused.
- **Straps over the G or L bows.** Same anchor arithmetic, neither reaches the crown.

## What it costs

**Nothing here is a load calculation.** The module reports lengths, counts and where
things land. Whether webbing of a given strength holds 54.7 m² of cover in a given wind
is milestone 8, and the rope's sag between feet is reported as a shape rather than solved,
because the tension is not known.

The doorway interrupts the hem over 1818 mm on M, so the rope dead-ends at the two feet
the door stands between rather than running through. Those two feet are also the ones the
portal cut already left holding two bow ends instead of three — see
[decision 0013](0013-the-bolt-is-half-the-rod.md) and `BASE2`. They are the busiest feet
on the dome and nothing has checked what that adds up to.
