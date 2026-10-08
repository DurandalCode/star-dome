# 0031. Stake the foot on rebar, and take any bar in a vee

- **Status:** accepted; replaces the wrap of
  [0027](0027-the-wrap-closes-the-fourth-side.md) and
  [0028](0028-join-the-wrap-ears-and-add-upper-stack-bolts.md), keeps the pad
  of [0025](0025-the-angle-is-met-on-a-pad.md)
- **Date:** 2026-10-08
- **Where it lives:** `connectors/base_hub_v1.py` (`vee_depth`,
  `stake_cradle`, the `stakeRebar*`, `stakeVeeAngle` and `stakeCradle*`
  inputs)

## The decision

`STAKE-BASE` is a **driven steel rebar**, not a steel angle. The base hub's
fifth print is a **cradle**: a block with a 90° vee along the bar, pulled onto
the bar by the same two M8 bolts through the same pad. The pad, the vee's two
flanks and the bar make three lines of contact, and that holds for **every bar
from 8 to 18 mm** across, ribs included. 18 mm covers a 16 mm rebar.

The bottom plate is unchanged. A `BASE3-8` set is already printed, so this
was a requirement and not a nicety. The regenerated `BASE3-8_Bottom` and
`BASE2-8_Bottom` were compared with the ones before the change as solids, and
they differ by 0.0 mm³ in both directions.

| | wrap (0027/0028) | cradle |
|---|---|---|
| holds | one angle, L30, 0.4 mm of fit | any round bar, 8–18 mm |
| contact | the leg's two faces and two edges | three lines along the bar |
| rim to pad, thinnest to thickest | 0.6 mm, one size | 0.6 to 12.7 mm |
| plastic, `BASE3-8` | 56 cm³ | 27 cm³ |
| stake bolts | M8 × 45 | M8 × 40 for the whole range |

## Why

The angle is dropped for rebar after the first printed `BASE3-8`. Rebar is
round, and that changes the answer. 0026 rejected a vee for the angle because
a 90° vee and a 90° corner have parallel faces and meet at one size only. **That is true of a
corner and false of a round.** A round bar touches both flanks of a vee at
any diameter. Its top stands r(1 + 1/sin a) above the apex, so the vee is cut
just shallow enough that on the thinnest bar the rim still stops
`stakeCradleGap` short of the pad. A thicker bar only stands the cradle further
off. The bolts therefore always pull on the steel and never on the plate,
which was the rule the wrap's gap existed for.

The far end of the range is where the thickest bar touches the flanks. With a
9.06 mm vee that is 6.4 mm up, safely below the mouth. `vee_depth` raises if a
range would put the contact on the edge.

## What was rejected

- **Keeping the angle.** It costs a part drawn round one bought section, and
  that section is the one in the schedule still chosen by guess.
- **A closed ring dropped over the bar's top, with a set screw.** It works
  and it is size-indifferent. But the hub would have to go on from above, over
  a bar that is already driven, and the set screw needs a thread or a nut
  pocket in plastic that bears on a rib. The cradle closes the same ring from
  the side, through the pad, with the bolts already there.
- **A new bottom plate drawn for rebar.** The pad already offers everything a
  bar needs: a flat face and two holes. Redrawing it would scrap a printed set
  for nothing.

## What it costs

- **It is still friction.** The 154 N of uplift and 188 N of shear per foot
  at 20 m/s (`make loads`) are taken by clamp, now on three lines rather than
  on faces. The ribs bite into the flanks, which probably helps, and nobody
  has measured it.
- **A bar is far less stiff than the angle.** L30×3 has I ≈ 11 600 mm⁴. A
  12 mm bar has 1 018 mm⁴ and a 16 mm bar has 3 217 mm⁴. The stake takes the
  foot's shear 25 mm off its axis. `STAKE-BASE` was unsized before this and
  still is; the diameter and the driven depth are now that question.
- **The skirt is not ported.** `COLLAR-d` ([0017](0017-the-skirt-post-is-the-stake-made-longer.md))
  is still drawn round an angle post. A skirted dome on rebar stakes needs
  that collar redrawn. This record does not do it.
