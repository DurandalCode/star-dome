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

**M and L are bare by choice**, and that decides their doors. Only S carries a
skirt, because a 4 m dome without one admits nothing at all.

| | dome | skirt | opening | overall | you get in |
|---|---|---|---|---|---|
| **S** | D4 | 1350 mm | 2368 mm | 3.31 m | carrying something |
| **M** | D6 | none | 1528 mm | 2.95 m | **on all fours** |
| **L** | D8 | none | 2038 mm | 3.93 m | **ducking** |
| **XL** | D10 | none | 2548 mm | 4.91 m | carrying something |

That is the price of no skirt, and it is steep in the middle of the range.
A bare D6 is 497 mm wide at 1200 mm and 209 mm at 1400 — not a door anyone
walks through. A bare D8 gives 908 mm at 1400 mm, which is a proper duck, and
384 mm at 1800, which is not a walk. Only at 10 m does the lancet alone clear
a standing person, and then it does it with a third of a metre to spare.

The `door` field in `configs/variants.toml` therefore records **what the dome
admits**, not what would be nice, and `admits` in the model lists every
silhouette that gets through:

| | admits |
|---|---|
| S | crawl, stoop, walk, carry, walk_wide |
| M | crawl |
| L | crawl, stoop |
| XL | crawl, stoop, walk, carry, walk_wide, **tall** |

Where a skirt is present it is not a preference; it is the answer to the door.
To re-solve one:

```bash
python3 -m stardome doorway D6 --skirt 0 --skirt-for carry   # -> 700 mm
python3 -m stardome doorway D8 --skirt 0 --skirt-for carry   # -> 190 mm
```

D3 is not a size here. It cannot take a walk-in door at any skirt height that
keeps it a dome rather than a silo — see [`interior.md`](interior.md).

## Who gets through

`entrance.TEMPLATES` holds person-shaped silhouettes rather than rectangles,
because neither a person nor a lancet is a rectangle and testing one against
the other understates every opening.

| | width × height | who |
|---|---|---|
| `crawl` | 700 × 900 | on all fours |
| `stoop` | 600 × 1400 | ducking |
| `walk` | 600 × 1800 | walking |
| `walk_wide` | 800 × 1900 | walking, in costume |
| `carry` | 900 × 1800 | carrying a chest, a table end, a stretcher |
| `tall` | 700 × 2200 | a character on stilts or in a frame |

The last one is not a person, and it is the one that separates the sizes.
**XL takes it bare — by 31 mm.** Nothing smaller takes it at all: D8 would
need 470 mm of skirt, D6 980 mm, D4 1510 mm.

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
make blender v=d6          # one dome, camera on the door
make sizes                 # S, M, L and XL in a row, every door facing front
```

Each dome is spun about its own axis so its door faces the camera. That changes
nothing about it — the structure is five-fold symmetric — and without it half
the row shows its blank side.

**Two figures stand in every doorway, 1.8 m and 2.2 m.** One is a person; the
other is the question. On M the 2.2 m one is taller than the whole opening,
on L it is head and shoulders above it, and on XL it walks in — which is the
size argument in a single picture.
