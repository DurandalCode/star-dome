# 0025. Meet the driven angle on a pad, not in a slot through the hub

- **Status:** accepted
- **Date:** 2026-09-13
- **Where it lives:** `connectors/base_hub_v1.py`, `connectors/kit.py`
  (`fastener_for_clearance`, `_outward_normal`), `docs/bom.md`

## The decision

The base hub meets its driven steel angle on a **flat pad with one bolt through
it**, hanging straight down from the hub in the empty sector. The L-section slot
that used to run right across the base plate is gone, and so is the tail that
carried it on the three plates that never needed it.

| one BASE3-10 | slot | pad |
|---|---|---|
| bottom plate | 257.7 cm³ | **73.4 cm³** |
| whole hub | 430.5 cm³ | **231.3 cm³** |
| bottom plate thickness | 46.8 mm, everywhere | 11.6 mm, 15.5 at the pad |
| stack height | 79.3 mm | **44.1 mm** |
| worst overhang, bottom plate | **0.0° over 2643 mm²** | 50.1°, nothing under 45° |
| what holds it to the angle | one M8 across a slot | one M8 through a pad |

Ten hubs a dome: **4.3 litres of plastic down to 2.3**, and no plate in the part
needs support to print.

Nothing about the angle changed. It is the same L30×30×3, driven plumb, offset
inboard of the bow bundle by the same 37 mm, standing proud above the foot for
the cover's loops (decision [0014](0014-the-cover-hangs-on-the-stakes.md)). A
skirt post is still that same angle made longer, so
decision [0017](0017-the-skirt-post-is-the-stake-made-longer.md) stands: it is
bolted to the pad instead of standing in the slot, and it is still not a member
of the joint.

## Why

The slot did three jobs and charged for four. What it was for: hold the hub down
on the angle; let the hub find its own height whatever depth the ground gave;
not care how the angle twisted going in. What it cost:

- **the plate.** A plate is one thickness. Putting a 31 mm band and a floor
  under it into the base plate put them into *all* of the base plate, over its
  whole 104 × 113 mm. `bom.md` had already noticed the result from the other
  end — the base hubs were 59% of the dome's plastic, and one bottom plate was
  258 cm³ of a 431 cm³ hub — and decision 0013 had already recorded the cause:
  the hub is sized by the stake, not by the rod.
- **the print.** 2643 mm² of flat slot roof at 0° of overhang, the worst face in
  the kit and item 4 of the roadmap's near-term list.
- **the fit.** 100 mm of slot that a driven angle has to be straight and
  untwisted along before the hub will go on at all.

A flat pad does all three jobs on a 38 × 45 mm lug. Down is the bolt, in
bearing. Height is a row of holes drilled down the angle's leg at 20 mm pitch —
bolt through whichever one lands, and the foot sits within 10 mm of nominal,
which is the ground tolerance [`tolerance.md`](../tolerance.md) already budgets
for. Twist is two flat faces bolted together: an angle a degree or two out beds
onto a pad, and jams in a slot.

**The load says the joint was never the hard part.** `make loads` puts 154 N of
uplift and 188 N of shear on each of the ten anchors at 20 m/s. The bolt bears
on 8.5 mm of pad, which is 4 MPa. The slot's own cross bolt bore on about twice
that and was carrying the same 154 N.

**The seating face has to be the face the plate is printed on, and that settles
the whole design.** Material on the far side of the angle's leg would hang below
that face, and below that face is the bed. So everything this part can offer the
angle is a flat face and a hole — every flank, roof and closed section the slot
had was bought with support material or with a 0° ceiling.

While the bolts were being looked at, the two that hold the stack together got
the pockets that had been in the parameter table all along and were never cut:
a captive nut in the bottom plate and a counterbore for head and washer in the
cap, each with a cone off it so neither leaves a flat ceiling. That is one tool
at one end of a joint assembled blind inside a stack, instead of two spanners.

## What was rejected

- **A blind socket the angle bottoms out in.** It is the shortest, stiffest
  interface available and it gives up the one property that makes the part
  usable: the hub can no longer find its own height. Controlling driven depth to
  the millimetre, ten times, in a field, is not a field sequence.
- **Putting the pad above the foot, where the bolt is above ground and easy to
  reach.** Measured and lost, and this is the measurement: vertical out of a hub
  is azimuth 90, the U arm sits at 79.19, and an arm is 28.8 mm wide — so the
  vertical line is *inside that arm* for its first 67 mm, and the U channel's
  wall rules out a bolt nearer than that. A pad reaching past it would stand
  135 mm above the foot. Above a foot there is nothing but bows; the empty
  sector is the only place an anchor can be met, and it points at the ground.
- **Two bolts down the pad.** It is the textbook answer and it buys nothing
  here: with a second bolt 40 mm further down, the pad reaches 85 mm below the
  foot instead of 45, all of it into soil that has to be dug for it. What two
  bolts add is resistance to the hub rotating about the anchor — and the hub's
  orientation is fixed by three bow ends, not by its anchor.
- **A fork or a rail that captures the angle's second leg.** Rotation for free,
  out of the section, which is exactly the argument the slot was built on. It
  also inherits the slot's fault: a 3.6 mm groove 45 mm long accepts about 0.8°
  of twist in a member that was driven into the ground with a hammer.
- **Leaving the stake bolt count alone.** It is still one bolt per hub, so the
  schedule does not move. It is also still *uncounted* — see below.

## What it costs

**The bolt is 34 mm below the foot, which is in the ground.** You scrape a
hollow for the pad before the hub goes on. The slot's cross bolt was 19 mm below
the foot and its tail 46 mm, so this is not new, and nothing in this project has
ever said where the soil surface is relative to a base point. It should.

**The angle has to be drilled.** Ten of them, a row of Ø8.5 at 20 mm pitch over
about 120 mm, done at home with a drill press or bought as perforated angle.
`STAKE-BASE` is still the schedule's one position chosen by guess
([`strength.md`](../strength.md) makes it the item the limiting wind speed hangs
on), and this adds a requirement to it rather than settling it.

**The foot lands within ±10 mm of its nominal height.** A hole row is a ladder,
not a slide. That is inside the ground tolerance already assumed, and it is a
real loss against a slot, which was continuous.

**The schedule still does not count this bolt.** `connectors._FASTENERS` gives
the base hub two shop bolts and a pin per bow end, and the one that holds it to
the ground has never been in the tally — the slot's cross bolt was not either.
It is ten field bolts a dome missing from a number
[`quick-release.md`](../quick-release.md) is built on, and it should be added
with its nut, its washer and the holes drilled in the angle, in a change that is
about the tally rather than about the part.

**Five angles stand inboard of the bundle and five outboard.** The pad is on the
outer face of the bottom plate, and five of the ten feet take the hub turned
over — that is what the two mirror sets have always meant. It was equally true
of the slot, which sat on the same side of the same plate, and
`stardome/connectors.py` claimed in a docstring that the offset was always
towards the dome centre. The docstring is corrected; the geometry is not,
because correcting it means a second, mirrored print of a part this project has
always built one of.
