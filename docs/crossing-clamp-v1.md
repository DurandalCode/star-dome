# Crossing clamp V1 — design notes

Source of truth: `connectors/crossing_clamp_v1.py` (generator) →
`connectors/star_dome_crossing_clamp_v1.FCStd` (editable FreeCAD model).

The generator is idempotent: it rebuilds `Parameters`, `BottomClamp` and
`TopClamp` in the document. If a `Parameters` spreadsheet already exists, its
values override the defaults in the script, so variants are produced by editing
the spreadsheet and re-running the generator.

## The governing geometric constraint

The brief asked for two halves, each with two semicircular grooves, split on a
plane between two rod axes separated by 12 mm. That combination cannot exist.

For a rod to be removable from a rigid half, the half must not wrap it by more
than 180°, i.e. the parting surface has to pass at or below the rod's own axis
plane. Two crossing rods at different heights have two different axis planes,
and a single parting surface cannot sit at both heights in the region where the
rods cross. Concretely, with `verticalSeparation = 12` and a 10.4 mm channel:

- parting at z = 0 (mid-way) leaves each rod fully enclosed in its own half —
  the rods would have to be threaded through every node during assembly;
- parting at either rod's axis leaves the other rod enclosed;
- a vertical parting plane encloses both rods away from the crossing.

The only two-piece arrangement that both clamps and releases is therefore:

    parting plane at the UPPER rod's axis height,
    axis separation = rodDiameter (the rods bear on each other at the crossing).

So `verticalSeparation` is **driven**, not free: the generator forces it to
`rodDiameter` and records the requested value in the run report. The rods still
do not share a point in 3D — they touch tangentially at the crossing, which is
what the original lashed Star Dome joint does anyway.

## Architecture

- **BottomClamp** — holds the lower rod in a 180° U-channel that is open
  upward, and carries two raised saddle segments that support the upper rod
  from below. Its top face (the seat) is one `clampGap` below the upper rod's
  axis. The channel above the lower rod is opened all the way to the seat so
  the lower rod can always be lifted out; that opening also interrupts the
  upper rod's saddle across the crossing, which is where the lower rod passes.
- **TopClamp** — a 180° saddle over the upper rod with two bolt ears.

One bolted joint clamps both rods: the cap presses the upper rod down, the
upper rod presses the lower rod into its channel. The load path is
cap → upper rod → lower rod → lower channel.

`clampGap = 1.2 mm` is a deliberate open gap at the parting faces. The faces
never bottom out, so the bolts always develop clamping force even with rods at
the low end of their diameter tolerance. Travel budget for a nominal 10 mm rod:
0.2 mm cap clearance + 0.2 mm lower-channel clearance, leaving 0.8 mm of
reserve for undersized rod stock.

## Fastening

Two M5 through-bolts on the Y axis, i.e. on the bisector of the obtuse sector
between the rods, so each bolt straddles both rod axes. `boltOffset` is derived:

    boltOffset = (channelRadius + fastenerHeadDiameter/2 + headClearance/2
                  + minimumWall) / cos(crossingAngle/2)

Head/washer counterbore in the cap, captive hex pocket for the nut in the
underside of the base. Minimum wall from the head counterbore to a rod channel
is exactly `minimumWall`; from the bolt shank to a rod channel, 6.75 mm.

Hardware per node, 10 mm variant: 2x M5x30 bolt, 2x M5 washer under the head,
2x M5 nut (captive, no washer needed — the pocket floor spreads the load).
Grip length under the counterbore is 21.4 mm.

## Sizes

| rodDiameter | footprint (mm) | height (mm) | volume bottom + top |
|---|---|---|---|
| 8  | 47.6 x 51.4 | 26.4 | 20.3 + 10.3 cm3 |
| 10 | 48.0 x 53.9 | 30.4 | 24.5 + 11.8 cm3 |
| 12 | 48.4 x 56.3 | 34.4 | 28.4 + 13.3 cm3 |

Height is `2*rodDiameter + rodClearance + capThickness + minimumWall`.
The assembled height already contains the parting gap; tightening closes it by
up to about 0.4 mm.

## Printability

Both halves print flat on the bed with no supports; the cap is printed upside
down so its saddle faces up. Verified on the solids: zero flat unsupported
ceiling area in either part, worst overhang ≈ 43° from horizontal (the tapered
transitions under the counterbore and above the nut pocket).

The bed-contact faces are deliberately left unfilleted.

## What V1 covers in the real dome

Added after the connector schedule was derived from the dome model
(`python3 -m stardome connectors D6`):

- **Covers:** all 30 unlashed crossings. They are two-rod contacts at a single
  angle, `acos(1/3)` = 70.5288 deg, so one clamp geometry serves every one of
  them. The generator builds it at that angle rather than the hand-picked 72
  deg default in `INPUTS`.
- **Does not cover:** the 10 lashed nodes, where four rods meet at one point
  with six pairwise angles between them. A two-piece two-rod clamp cannot serve
  them, and the radial stacking order that a four-rod part would need is still
  a drawing convention rather than a build decision.

The reference lashes the second group and leaves the first alone, so V1 as it
stands solves the crossings the original design does not tie. See
`docs/roadmap.md` milestone 3.

Batch generation for a whole dome: `connectors/generate_clamps.py`.

## Known compromises for V1

1. The lower rod is clamped only through the upper rod, and is retained
   laterally by a 180° channel. Away from the crossing it is not gripped.
   Acceptable because the crossing is where the joint has to work.
2. The rods bear directly on each other at the crossing — crossed-cylinder
   contact on fibreglass. Torque must be limited; this is the first thing to
   check on the printed prototype.
3. Wall at the flared channel mouth is 3.0 mm, below `minimumWall`. This is
   the local lip only; it grows immediately away from the mouth.
4. No snap features, no keying, no labelling yet.
5. Fillets are applied by the generator as a geometric post-process, not as
   named features in the FreeCAD tree. Editing the model by hand in the GUI is
   possible, but re-running the generator overwrites `BottomClamp`/`TopClamp`.
