# The skirt

A Star Dome hemisphere is only as tall as `0.982 × R`. For the small end of the
family that is not standing height:

| variant | dome height | with skirt |
|---|---|---|
| D3 | 1.47 m | **2.47 m** on a 1.0 m skirt |
| D4 | 1.96 m | — |

D3 is unusable on its own — 1.47 m is a crawl-in shelter. The reference's own
answer to this, and the one this project takes, is to stand the hemisphere on a
vertical skirt rather than distort the Star Dome into a three-quarter sphere.
Distorting it would break everything the geometry rests on: the bows would stop
being great semicircles, `lbow = πR` would stop holding, and the 15 identical
rods would become 15 different ones.

## What is modelled

`skirt_height` in `configs/variants.toml`, per variant. Zero for every dome big
enough to stand up in on its own. When it is non-zero the model gains a `skirt`
block:

- ten vertical posts, one under each base point, each `skirt_height` long;
- a ground ring at the bottom, the same length as the base ring, `2πR`;
- `ground_z` = −`skirt_height`, and `overall_height` = skirt + dome.

### The frame convention, which matters

**The dome keeps its base ring at z = 0 and the skirt hangs below it into
negative z.** The ground is at −`skirt_height`.

That is deliberate. Every crossing, node, tangent and symmetry class in this
project is derived in a frame where the sphere is centred on the origin, and
`weave.py` takes a node's position vector to *be* its radius vector when it
builds the node's tangent plane. Offsetting the dome upward to put the ground
at zero would silently break that. Consumers lift the assembly instead:
`blender/build_scene.py` and `build_site.py` both add `skirt_height` to every z.

`stardome verify` checks the convention — post count, posts under their base
points, post length, `ground_z = −height`, and `overall_height = skirt + dome`
— so a change to it cannot pass unnoticed.

## Bracing

An earlier version of this skirt was ten posts and one ring, and it would have
racked: a ring of pin-ended posts has no resistance to a sideways load at all.
Push the top ring and the whole thing leans until something else stops it. The
dome above is stiff in its own surface but cannot brace the skirt, because it
meets it at exactly the ten points that are free to move together.

The skirt now carries three things that fix it, and the model has all three as
real members:

| | what | why |
|---|---|---|
| **top ring** | 10 chords between the base points | Not only the skirt's. A dome pushes *outward* at its feet, and the ten base points of a bare Star Dome are ten free rod ends with nothing tying them together. Something has to take that thrust in hoop tension whether there is a skirt or not. |
| **bottom ring** | 10 chords at ground level | Closes the far end of every post, so a bay is a quadrilateral and not two free legs. |
| **diagonals** | two per bay, crossed | Triangulates the bay. Declared **tension** members, not rod. |

On S that is 1236 mm across a bay and 1350 mm of post, so a diagonal is
1830 mm at **47.5° above horizontal** — near the middle of the useful range.
Outside roughly 30–60° a brace is either mostly pulling the posts together or
mostly trying to lift them, and `verify` fails if it drifts out.

**Why the diagonals are straps.** The one member in this structure that can
buckle is a 1.8 m diagonal in compression. A strap cannot buckle; it goes
slack instead, which is why they come in crossed pairs — whichever way the
skirt is pushed, one is in tension and the other does nothing. It also keeps
them out of the rod budget, and they are the largest single item in it:

    posts        13.50 m of rod
    top ring     12.36 m
    bottom ring  12.36 m
    ---------------------
    skirt rod    38.22 m   against 94 m for the dome itself
    diagonals    32.95 m of strap

**The door bay is properly open.** Taking the diagonals out is not enough:
both rings still ran straight across it, one along the ground to trip on and
one at the top of the skirt, at head height. Neither is a hole. So that bay
loses its diagonals *and* both ring chords.

That leaves the top ring an open arc, which carries no hoop tension at all, so
the force takes a detour over the opening: post head → the U bow rising from
that base point → **a header between the two U bows** → down the other side.
On S the header spans 701 mm at 2350 mm above ground. Note *2350*, not 1950:
it clears the tallest silhouette the opening actually **admits**, which on S is
a 2.2 m character, rather than the 1800 mm one the door is nominally sized for.
A lintel placed on the nominal figure takes back what the doorway was passing,
and `verify` fails if it does.

That is a portal frame, and it puts bending into the two U bows near their
feet. Nothing here checks that. One open bay is the limit; `verify` says so,
and it also fails if a ring segment is left lying across the doorway.

## The joints

This used to be the largest hole in the parts list. The schedule read the
skirted base point as **eight members** — three bow ends, the post head, two
ring chords and two brace heads — which made the busiest joint in the whole
structure the one place nothing was designed for, and added three more part
types with nothing at all behind them.

None of that had to be true, and the way out was to notice what the base hub
already has.

### The post is the stake, made longer

`base_hub_v1` carries a **pad and a bolt for a driven steel angle**. A skirt
post is that same angle: driven at the bottom, bolted to the hub's pad at the
top, one member doing both jobs. So the post is no more a member of the base
point than a stake is, and

**a skirted dome and a bare one use exactly the same base hub.**

A post *and* a stake at one point would have been two members competing for one
place. Only the length changes — `STAKE-BASE` reports how much of it stands
above the soil, `0 mm` bare and the skirt height under a skirt. How far it is
driven is the ground's answer, not this project's.

### One collar, at both ends of every post

What is left is the skirt's own two members at each end of each post — a ring
chord and a brace — times two sides. They land on a collar clamped to the post,
not on the hub.

The head and the foot are **the same shape**. At both, the chords leave level
and the braces leave at the same angle: downward at the head, upward at the
foot. Turn the collar over about the outward radius and one becomes the other,
so there is one geometry and twenty of them on a ten-post dome. The generator
checks it rather than claiming it: it builds the foot explicitly and asks
whether the flipped head is that part, and gets 1.0.

The two members on each side are **coplanar**, which is why a flat lug is
enough. The chord to the next post leaves at `90 + 180/n` from the outward
radius — 108° on a decagon, derived from the post count — and the brace to that
post's other end leaves on the same plan azimuth, at the brace angle. Both
therefore lie in one vertical plane, so one lug per side carries both, with an
arm out along each member's own ray and a bolt hole at the end of it.

| | before | after |
|---|---|---|
| base hub on a skirted dome | 8 members, nothing designed | the same `BASE3` as a bare dome |
| the skirt's own joints | `FOOT5` + `FOOT3`, hardware | one `COLLAR`, 20 of it |
| part types with nothing at all | 3 (`BASE8`, `BASE5`, `HDR`) | 1 (`HDR`) |

### What the collar deliberately does not decide

**What the ring chord is made of.** A GFRP rod of the dome's own diameter
buckles at well under a hundred newtons over a chord this long, so the ring is a
section somebody has to specify — milestone 8. That is exactly why the lug ends
in a **bolt hole rather than a socket**: a hole takes a rod end fitting, an
angle bolted flat, or a strap, and does not have to be redrawn when the question
is answered.

**Whether a printed collar can carry the ring's force.** It locates the members
and clamps the post, and the load path through it is not checked anywhere.

## Still open

The header over the doorway (`HDR`) is the one skirt part with nothing behind
it: it clamps to a bow part-way up its length, where there is no crossing to
hang it on, and it carries the top ring's hoop force round the opening.

Beyond that: whether the base ring can actually carry the hoop tension the dome
puts into it, how the diagonals are tensioned, and how far the posts are driven.
Those are statics and hardware, not geometry, and the `skirt` block carries the
warning in its own `note` field so anything reading the model sees it.
