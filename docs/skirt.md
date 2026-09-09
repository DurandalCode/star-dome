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

**The door bay carries no diagonal**, because a diagonal across a doorway is a
doorway with a diagonal across it. The rings still close around it and the
other nine bays hold it square. One open bay is the limit; `verify` says so.

Still not modelled, and still the important part: how the posts meet the
ground, how the diagonals are anchored and tensioned, and whether the base
ring can actually carry the hoop tension the dome puts into it. Those are
statics and hardware, not geometry.

None of these is drawn, chosen, or calculated. The `skirt` block carries this
warning in its own `note` field so anything reading the model sees it.

The other open questions: what the posts are made of (the same GFRP rod is
weak in vertical compression at 1 m unbraced), how the base nodes fasten to
them, and whether the ground ring wants to be rod, strap or rope.
