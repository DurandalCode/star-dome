# 0028. Join the wrap ears and add an upper pair of stack bolts

- **Status:** accepted
- **Date:** 2026-09-27
- **Where it lives:** `connectors/base_hub_v1.py`, the base-hub fastener
  schedule in `stardome/connectors.py`

## The decision

The base hub keeps two M8 bolts on the angle wrap. Both bolt ears are part of
one printed solid: a bridge below the tip of either possible second leg of
the L section joins the ears to the wrap's centre. The rim still stops short
of the pad, and both reliefs remain, so the same wrap fits the mirrored feet.

Two more stack bolts pass through every plate in the upper bow sector. A
three-arm foot puts one in each gap between arms. The two-arm doorway foot
puts them just outside its two arms. The stack now has four bolts, assembled
at home; the angle wrap still has its separate pair, worked in the field.

## Why

The shallow wrap of [0027](0027-the-wrap-closes-the-fourth-side.md) looked
whole in a render, but FreeCAD reports **three solids**: the through reliefs
isolate the two bolt ears from the centre. That cannot be printed as one
working clamp. The new bridge lies below the steel tip, where it can connect
all three regions without colliding with the angle.

The added stack bolts hold the upper portion of the plate assembly on both
sides of the bow fan. Their positions come from the fan angles and the same
channel-clearance calculation as the lower pair. `verify` now rejects any
plate or wrap that is not one valid solid and checks material around all four
stack holes.

## What was rejected

- Leaving the two through reliefs in the shallow wrap: the two ears remain
  separate printable objects, regardless of how continuous they appear in a
  shaded view.
- Bridging a relief through the steel: it would prevent the angle from
  seating. Keeping only one relief would make the wrap handed at the five
  mirrored feet.

## What it costs

For `BASE3-10`, the wrap grows from about **18.4 to 59.1 cm³** and from 11.4
to **33.8 mm** deep. The bridge and the longer M8 angle bolts sit lower near
the soil, so the assembly clearance must be checked on a physical prototype.
There are two more M5 stack bolts per foot: **40 shop bolts** across ten feet
instead of 20. The field bolt count and assembly action are unchanged.

FreeCAD's solid, interference and printability checks pass for `BASE3-10`
and `BASE2-10` at the M rod size. This is a geometric result, not a strength
or creep validation of the printed joint.
