# The door

The goal is a room for a live-action event, and a room needs a door. A Star
Dome has none: it has fifteen rods and whatever gaps they leave. So the door is
not designed, it is **chosen** — and then measured.

```bash
python3 -m stardome doorway --all
python3 -m stardome doorway M --template walk
python3 -m stardome doorway D12 --skirt 0 --skirt-for carry
make doorways
```

[`entrance.md`](entrance.md) answers "how big an opening fits anywhere on this
dome". This answers the next question: **which opening, framed by what, and
where is it in space** — which is what a cover panel and a door frame get cut
to.

## Ten gaps, in two sizes

Unrolled, the dome has ten ground-standing openings, alternating tall and low.
The tall ones are the doors. Their shape is a property of the structure, not of
the size:

| | |
|---|---|
| bays | 10 — five tall, five low |
| span | 34.5° of azimuth, at every diameter |
| head height | **0.26287 × D**, exactly |
| clear height | about 0.254 × D |
| open area | about 0.042 × D² |

Two numbers, not one, because they measure different things. The head is a
*node*, and the shape is self-similar, so it scales exactly. The clear height
is the head **less the rod**, and a rod is a fixed thickness taking a shrinking
bite out of a growing dome — 0.2541 of D on D3, 0.2549 on D12. Anything
quoting a single figure is quoting the big end.

## The opening is free

Each tall bay is a **lancet**: two bows of family G spring from adjacent base
points and meet overhead at a lashed four-rod node.

```
              N20  ← lashed 4-rod node (G1, G4, L1, L5)
             /  \
        G1  /    \  G4
           /      \
    b1 ●──┘        └──● b2      ← two base points
```

So the doorway is framed, top and bottom, by joints that already exist: two
base points and one of the ten strongest nodes in the structure. **Nothing is
cut, nothing is added, and there are five of them.** A second door opposite
costs nothing structurally.

This is worth stating plainly because the obvious alternative is much worse.
Every bow is one continuous semicircle carrying load the whole way round.
Shortening one to widen a hole does not trim a member — it deletes one, and it
deletes it at the exact place the structure has just been opened.

## The four sizes

Each aliased size carries the shortest skirt that lets a person **carrying
something** walk in (the `carry` silhouette: 900 mm at the shoulder, 1800 mm
tall), rounded up for about 100 mm of headroom to spare.

| | dome | skirt | opening | overall | spare |
|---|---|---|---|---|---|
| **S** | D4 | 1350 mm | 2368 mm | 3.31 m | 113 mm |
| **M** | D6 | 800 mm | 2328 mm | 3.75 m | 106 mm |
| **L** | D8 | 300 mm | 2338 mm | 4.23 m | 113 mm |
| **XL** | D10 | none | 2548 mm | 4.91 m | 340 mm |

The skirt is not a preference; it is the answer to the door. Change the
silhouette and it has to be recomputed:

```bash
python3 -m stardome doorway D6 --skirt 0 --skirt-for walk_wide
```

L's 300 mm is barely a skirt at all — a sill, which also keeps the cover off
the ground. XL needs none: at 10 m the lancet alone clears a walking person
with a third of a metre to spare.

D3 is not a size here. It cannot take this door at any skirt height that keeps
it a dome rather than a silo — see [`interior.md`](interior.md).

## What this does not settle

- **The cover.** The opening is measured to the rod surface; the fabric has to
  be cut and hemmed around the same gap, and it will eat some of it.
- **The frame.** A door frame has its own stiffness and its own thickness, and
  neither is modelled.
- **The skirt bay.** Taking a bay out of the skirt for a door removes whatever
  bracing that bay would have carried, and the skirt is already the unbraced
  part — see [`skirt.md`](skirt.md).
- **Load paths.** Leaving one bay uncovered changes how the cover shares load
  around the shell. Nothing here says anything about that.

## In Blender

The doorway travels in `model.json` as a closed 3D outline, so the scene
builders draw it rather than rediscovering it:

```bash
make blender v=m           # one dome, camera on the door, figure standing in it
make sizes                 # S, M, L and XL in a row, every door facing front
```

Each dome is spun about its own axis so its door faces the camera. That changes
nothing about it — the structure is five-fold symmetric — and without it half
the row shows its blank side.
