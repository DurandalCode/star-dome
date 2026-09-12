# 0017. Make the skirt post the stake, and put the skirt's own members on a collar

- **Status:** accepted
- **Date:** 2026-09-12
- **Where it lives:** `stardome/connectors.py` (base points, `COLLAR`, `STAKE-BASE`), `connectors/skirt_collar_v1.py`, `docs/skirt.md`

## The decision

The skirted base point is **three members, not eight**, and it takes the same
`BASE3` hub a bare dome takes.

`base_hub_v1` already carries a through slot for a driven steel angle and two bolts
across it. A skirt post is that same angle, longer: driven at the bottom, standing in
the hub's slot at the top. So the post is no more a member of that joint than a stake
is, and the skirt's own members — two ring chords and two brace ends — land on a
**collar clamped to the post** at each of its two ends.

One collar geometry serves both ends. At the head and at the foot alike the chords
leave level and the braces leave at the same angle, downward at one and upward at the
other, so turning the part over about the outward radius turns a head collar into a foot
collar. Twenty of one part on a ten-post dome.

| | before | after |
|---|---|---|
| base hub, skirted | 8 members, undesigned | the same `BASE3` as bare |
| the skirt's own joints | `FOOT5` + `FOOT3`, hardware | one `COLLAR`, 20 of it |
| part types with nothing at all | `BASE8`, `BASE5`, `HDR` | `HDR` |

## Why

The eight-member reading was an assumption, not a measurement: it put every member that
*arrives near* the base point *onto* the base point. Three of them did not have to go
there, and the one that looked most unavoidable — the post — was the same piece of steel
the joint was already designed around.

Two facts made the collar fall out rather than have to be invented:

**The two members on each side are coplanar.** The chord to the next post leaves at
`90 + 180/n` from the outward radius — 108° on a decagon, derived from the post count —
and the brace to that post's other end leaves on the *same* plan azimuth at the brace
angle. One flat lug per side therefore carries both.

**The head and the foot are mirror images through the horizontal.** Measured, not
assumed: both ends report chords at ±108° and rise 0, and braces at ±108° and rise
∓47.5226°. The generator checks the consequence rather than asserting it — it builds the
foot collar explicitly and asks whether the flipped head collar is that solid, and gets
1.0.

## What was rejected

- **Designing the eight-member hub.** It is the joint with the most members in the
  structure and it sits 1.35 m in the air, and it only exists if you put the skirt's
  members on it.
- **A post and a stake as separate members.** Two things driven into one point, one of
  them through the other's fixing. The slot holds one angle.
- **A socket for the ring chord.** What the ring is made of is not decided — a GFRP rod
  of the dome's own diameter buckles at well under a hundred newtons over a chord this
  long — so a socket would have had to be redrawn when milestone 8 answers it. A bolt
  hole takes a rod end fitting, an angle bolted flat, or a strap, and does not care.
- **Two pinch bolts on the same diagonal.** It would have grouped as well and cost the
  same, and it would have broken the flip symmetry — making the foot a second part for
  no gain. They go on opposite diagonals at opposite heights instead.
- **A rectangular lug spanning both rays.** Mostly material holding nothing. One arm per
  member, each out along its own ray, is a third less plastic.

## What it costs

**The collar is in the hoop load path and nothing checks it.** It locates the ring chord
that takes the dome's outward thrust, and whether printed plastic carries that is
milestone 8. The base hub makes the same kind of claim and carries the same kind of
warning; this one is worth repeating because the collar is smaller.

**The post now has to be drilled or gripped.** The collar clamps with two bolts across
the bore and relies on that grip to stay at its height. Whether friction on a smooth
steel angle is enough, or whether the post wants a hole through it, is a field question
the geometry does not answer.

**`HDR` is still nothing.** The header over the doorway clamps to a bow part-way up its
length, where there is no crossing to hang it on, and carries the top ring's hoop force
round the opening. It is now the only part in any variant's schedule with nothing behind
it at all.
