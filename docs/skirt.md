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

## What is NOT modelled, and it is the important part

**The skirt as drawn is ten unbraced verticals and a ring. It will rack.**

A ring of pin-ended posts has no resistance to a sideways load at all: push the
top ring sideways and the whole skirt leans until something else stops it. The
dome above is stiff in its own surface but it cannot brace the skirt, because
it meets it at exactly the ten points that are free to move together.

So before any 3 m dome gets built, the skirt needs one of:

- diagonal bracing in each of the ten bays, or in alternate bays;
- a tension belt or guy set taking the shear to ground anchors;
- a fabric skirt cut and tensioned to work as a shear panel;
- posts fixed rigidly at the ground instead of pinned, which turns the racking
  problem into a bending problem at the feet, and puts the whole load into the
  anchors.

None of these is drawn, chosen, or calculated. The `skirt` block carries this
warning in its own `note` field so anything reading the model sees it.

The other open questions: what the posts are made of (the same GFRP rod is
weak in vertical compression at 1 m unbraced), how the base nodes fasten to
them, and whether the ground ring wants to be rod, strap or rope.
