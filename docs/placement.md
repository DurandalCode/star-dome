# Putting the connectors on the dome

```bash
make fitted V=M            # the dome with all 107 connectors on it
make clamps V=M            # just the parts, into exports/connectors/
python3 -m stardome connectors M
```

[`assembly.md`](assembly.md) answers what order the bows go up in. This
answers a different question that had never been asked at all.

Every connector in this project was designed against an angle out of the
model. None had ever been *placed* — stood on the rods it holds, the right way
up, in the dome's own coordinates. Doing that is what this page is about, and
it found three errors and one prerequisite. That is the argument for doing it:
a part checked only against its own parameters is a part checked against the
half of the problem you already understood.

## The prerequisite: a weave you can stand a part on

The model has always had two weave modes and neither will do.

| mode | what it is | radial gap at a crossing, M |
|---|---|---|
| `flat` | every centreline on the nominal sphere | 0 mm — the two rods are in the same place |
| `layered` | each bow on its own shell, 15 shells | up to 140 mm |
| `woven` | the route `weave.global_profile` solves | 10 mm at every unlashed crossing |

`layered` reads well and says so in its own docstring: a drawing convention.
A connector stack is one rod diameter tall, and `layered` spreads the same
crossing over fourteen, so a part drawn on it floats.

The route that a real dome takes was already being solved — `global_profile`
relaxes the free offsets until no two rods share space — but it was only ever
printed, never exported. `weave_mode=woven` writes it: the rod polylines carry
it, every crossing reports its true radial gap, and `verify` checks that none
is closer than one rod diameter and that the whole weave stays inside the
±1.5 rod diameters a four-rod stack has room for. It does, on every variant.

**`flat` is still the basis for exported coordinates.** `woven` is for
building and drawing on, not for measuring.

## What the placement is

`stardome/connectors.py` emits one `placements` entry per connector: where it
sits and a basis mapping the part's own axes onto the dome. The frames are
read off the generators rather than guessed:

| part | local frame |
|---|---|
| `fan_node_v2` | plates stack along +Z, arms in XY, first arm at azimuth 0 |
| `crossing_clamp_v1` | upper rod at `+angle/2`, `z = +v/2`; lower at `-angle/2`, `z = -v/2` |
| `base_hub_v1` | arm azimuths ARE their rises above horizontal; +X along the base ring, −Y straight down |

Every one of these parts is flat, so an orientation is two choices: which way
local +X points in the tangent plane, and whether the part is the right way up
or turned over. Turning a flat part over is a **rotation**, not a reflection,
so the basis stays right-handed and says so by flipping +Y and +Z together.

Two things are checked for every instance, and the second is the one that
matters. The arms have to land on the rod **lines** — necessary, and weak,
because a line has no direction and a part turned over lands on the same
lines. The stack levels have to match how far out each rod actually runs.
That is what pins the part the right way up, and it is what turned up the
three errors below. `tests/test_connectors.py` runs both checks over all 107.

## Three things that only showed up here

### The doorway takes a bow off two feet

The portal cut frees `L1` at `b0` and `L4` at `b1` — the two feet the door
stands between. Those gather **two** bow ends, not three, and the schedule was
still asking for ten identical three-arm hubs: a part that does not fit at the
one place anybody stands.

It costs one more print and no new geometry. Both jambs keep the same pair of
arms — the U bow and the G bow — at the same 37.3774° the node fan already
uses, and the two are mirror images, so one part turned over serves both.
`BASE2` is `base_hub_v1` with one arm fewer.

### The fan was being cut at the wrong arm

A fan closes on itself, so one of its four gaps is never a contact between two
stacked rods: the one from the last arm back to the first. The printed part
spends that on the widest gap, 63.4349°, which is what leaves its three
channel spacings at 37.3774, 41.8103 and 37.3774.

The arms were being ordered by angle and started at the smallest. At the five
upper nodes that lands on the widest gap by luck. At the five **lower** nodes
it puts the widest gap in the middle of the stack, which asks for channels
37.3774, 63.4349, 37.3774 apart — a second part, at ten nodes the project has
always described as one.

Cutting the fan at its widest gap makes the claim true. The solved weave
stays feasible on it, and all ten nodes now stack with the same three
spacings. It also means the fan never has to be turned over, which matters
because its five plates are five different shapes and `Cap` belongs outside.

The cost, and it is real: the naive straight-line route between lashed nodes
now violates 25 of the 30 unlashed crossings instead of 15. The solver was
always required; it is required harder.

### The two-rod clamp is handed

`crossing_clamp_v1` puts the cap outside, over the rod that runs outside. That
fixes the stack, and with the stack fixed a crossing either matches the part
as drawn or matches its mirror image.

Both occur: **17 as drawn, 13 mirrored**, on every variant. Turning the clamp
over to make the angles agree would put the cap on the inside, under the rod
it is meant to hold down, so the mirror is a second print and not a second
orientation. The schedule reports the split; the scene reflects the mesh.

The 17/13 is not a symmetry of the dome — D5 would give 15/15 — so it comes
from the over/under assignment, which is not mirror-symmetric. Whether a
different assignment could make all 30 the same hand, and print one clamp
instead of two, is open and worth an hour.

## What the picture shows

```
[connectors] 97 placed from STL, 10 as proxies, 252 pieces in the scene
```

97 of M's 107 connectors are real geometry imported from the STL their
generator wrote. The ten proxies are `STAKE-BASE`, which is hardware to
specify rather than a shape to design. Each printed piece is imported once and
instanced after that, sharing one mesh, or a 252-piece scene would not open.

`make fitted V=M` also renders three close-ups — `node`, `crossing`
and `foot` — because a whole-dome view can show that connectors are there and
cannot show whether they are *on* the rods. At 6 m across, a rod diameter out
looks identical to right.

## What this does not settle

- **Nothing is printed.** Every part here is geometry that passes its own
  checks and has never been in plastic.
- **Two joints have no answer at all from geometry.** `TERM` puts load along
  a rod into a 5 mm printed wall, and `SPLICE` has to carry bending across a
  butt joint. Both are test-rig questions.
- **The stake.** Ten per dome, still a size to choose.
- **`max_diameter_woven`** — and so the cover area — is still taken from the
  `layered` offsets, which now overstate the real weave by a factor of five.
  It is a straightforward fix and it moves published cover numbers, so it is
  left for a decision rather than taken quietly.
