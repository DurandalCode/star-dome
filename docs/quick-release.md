# Closing a joint without a spanner

Rule 1 of this project is that fast assembly is a requirement of the first
class. [`assembly.md`](assembly.md) counts the one expensive *move* — threading
a bow under a bow already standing — and settles it exactly. This counts the
expensive *minutes*, which is a different thing and had never been counted at
all.

```bash
python3 -m stardome bom M            # the fastener block at the bottom
make clamps V=M                      # the bolted clamp, unchanged
STAR_DOME_CLOSURE=hinge make clamps V=M   # the same clamp, hinged
```

## What it costs today

Until now the schedule knew how many parts a dome needs and not how many
fasteners, and [`bom.md`](bom.md) said so in as many words: *"how many bolts a
part takes is a property of the generator that draws it, and the schedule does
not carry it yet."* It carries it now, and the number splits in a way that
matters more than the total:

| M, L, XL | bolts | pins |
|---|---|---|
| **worked in the field** | **84** | 28 |
| worked in the shop | 20 | — |

The split is not tidiness. Every generator already states its own field
sequence, and they do not agree about the bolt:

- **`base_hub_v1`** — *"the stack is assembled once, on the ground or at home,
  and the bow ends go in afterwards."* Its twenty bolts are done up before the
  dome leaves the workshop and never touched again. What happens at the dome is
  a pin per arm.
- **`fan_node_v2`** — *"open the stack → lay rod 1 → … → tighten two bolts."*
  Its twenty are undone and done up at head height.
- **`crossing_clamp_v1`** and **`term_clamp_v1`** — the cap comes off to admit
  the rods, so sixty-four bolts, sixty-four nuts and thirty-two caps are loose
  objects in somebody's hand, up a ladder, in whatever weather the event has.

So the honest target is not "104 bolts". It is **84**, and within those the
worst are the clamps, because a clamp is not one fastener to turn — it is
**three loose pieces to not drop**.

S is worse and for an unrelated reason: its skirt puts twenty collars on the
list at six bolts each, so it asks for **204** field bolts. The skirt is not
what this document changes, but it is where the next hundred are.

## What already exists

### Cam lever on a tension member — the bicycle quick release

An eccentric on a lever, bearing on a washer, pulling a rod: closing the lever
rotates the cam against a thrust face and pulls the rod about
[0.8–1.2 mm](https://www.firgelliauto.com/blogs/mechanisms/quick-release-skewer).
Force follows `F = F_hand × L / e × η` with η ≈ 0.6–0.8, so a 45 mm arm on a
2 mm eccentric is around 1.5 kN at a hand's 100 N — the same order as a
hand-tight M5, from a motion that takes a second. It self-locks when the cam's
rise angle is no steeper than the friction angle `atan(μ)`, and past the
maximum-lift point the load turns it further closed rather than open.

**Applies, as hardware, and not as a printed part.** The mechanism needs a
member in tension and gives about a millimetre of travel, so it can replace the
*tightening* of a bolt and nothing else — it cannot open a joint. The cam's
working face is a line contact under full preload, which is why the trade
specifies [45 HRC minimum](https://www.firgelliauto.com/blogs/mechanisms/cam-lever-grip)
there; a printed PETG cam at 1.5 kN flattens. An M5 quick-release lever for a
bicycle seat collar is an orderable item that already solves it in steel, and
that is where this belongs: **as an option on the bolt this design keeps**,
listed the way the driven steel angle is listed — a thing to specify, not a
shape to draw.

### Over-centre toggle latch, and the one-piece cam latch

A case latch, a ski-boot buckle, a [drum-lid latch](https://www.jwwinco.com/en-us/products/2.4-Tensioning-with-clamping-mechanisms):
a lever, a link, and a catch, with the link pin carried past the line between
the other two so the load locks it. Mechanically ideal for this joint — high
advantage near the dead point, positive lock, no reliance on friction.

**Measured against this part, and it does not fit.** Both variants were drawn
and thrown away, and the reason is the same number in each:

- The clamp's two fastener stations sit **17.9 mm** either side of the crossing
  and the part is **30.4 mm** tall, so the distance from a pivot low in the
  bottom half to a bearing surface on top of the cap is **≈ 24 mm**. A
  *one-piece* cam latch has to span that with its own material, so its cam
  radius is 24 mm against an eccentricity of 2 — a thin arc on a 24 mm radius,
  which sweeps straight across the cap the moment the lever moves. The swing
  check catches it at ten degrees.
- A *linked* toggle fixes the reach but needs a clevis on the link, and the
  clevis has to contain a bolt head: **≥ 11 mm** across, inside a fork gap of
  **6.6**. Nesting it the other way — the link straddling the lever straddling
  the tab — works geometrically and costs three printed pieces and three pins
  per clamp, which is 150 prints a dome against 60.

The mechanism is right and the envelope is wrong. A latch wants a shallow joint
and a short reach; this is a deep one.

### Wedge

Scaffolding's answer: a tapered key driven through a slot, self-locking on
friction, indifferent to tolerance. Fast, cheap, printable, and it needs a
mallet — which a camp that drives ten steel angles into the ground already
has. **Not pursued here**, and not dismissed: it is the obvious candidate if
the hinged joint turns out to want more preload than a hand can give it.

### Strap — the reference's own answer

A [cam-buckle or rubber gear strap](https://reyrgear.com/products/voile-rod-straps)
over a printed saddle: one part, no metal, nothing loose, a second per joint,
and *"a firm, stable hold rather than maximum clamping force."* This is the
closest thing on the list to what the Takekawa dome actually does at its nodes,
which is lash them.

**Deliberately left open.** The strap gives grip and no location, and the dome's
shape depends on the rods crossing at the right point at the right angle — but
milestone 3 already asks whether the thirty untied crossings need a clamp at
all, and if the answer is no, a strap is what replaces them. That question is
about load, so it belongs to a test rig and not to this document.

### Quick-release pin, R-clip, ball-detent pin

A pin in double shear, pulled out by hand.
[Ideal](https://www.runsom.com/blog/guide-to-quick-release-pins/) where a joint
*locates* rather than clamps, and useless where preload is the point.

**Already in use, and the right place for it is not the clamp.** `base_hub_v1`
gives every arm a slide-fit channel and a cross pin precisely because it does
not clamp; those 28 pins are the dome's existing tool-free fasteners. Turning
them into hairpin clips is a small, obvious, separate change.

### Quarter-turn fasteners and printed snap fits

A quarter-turn fastener draws about 2 mm and holds a panel, not a preload. A
printed cantilever snap holds a lid and creeps under sustained load —
[PETG takes a set when stored deflected](https://www.goodprints3d.com/blogs/3d/best-filament-for-3d-printed-springs-petg-nylon-pla-pro-or-tpu),
and the standing advice for anything that must hold force over time is a metal
spring and a printed housing round it. **Neither applies.**

## The thing the survey nearly missed

Every mechanism above answers *"how do I tighten this without a tool?"* — and
that is not the expensive part of putting up a clamp. This is:

> place the bottom half on the standing rod · lay the upper rod · hold the cap ·
> start two bolts from above into two nuts that can fall out of their traps ·
> ten turns each, two tools, at head height

The bolts are half a minute of it. **The other half is that a two-piece clamp
becomes three separate objects the moment it is opened**, at the exact moment
both hands are busy. Sixty bolts, sixty nuts and thirty caps, thirty times over,
each one droppable into long grass.

So the change worth making is not a faster fastener. It is **a joint that never
comes apart at all.**

## What was built

`fastenerStyle = 1` on the crossing clamp (`connectors/closure.py`) — one generator, two closures, and the
bolted output is byte-identical to what it was:

    the cap is HINGED to the bottom half on one side, on a steel pin, so the
    connector is one object from the moment it is printed;

    on the other side it keeps ONE bolt, standing in a slot that is open to the
    outside rather than in a drilled hole.

Field sequence, against the four-line one above:

> place the clamp on the standing rod, open · lay the upper rod · swing the cap
> shut · four turns

Slacken those four turns, lift the cap the 2.2 mm its hinge slot allows, and
swing it: the ear comes out from under the washer sideways, and the bolt never
leaves the nut it is threaded into. Nothing in the joint is a separate piece at
any point, **including while it is open**. Fit a bicycle seat-collar lever in
place of the bolt head and the four turns go too.

### The hinge axis is not a choice

The cap wraps the upper rod through 180°, so its channel is a half cylinder
whose diameter lies in the parting plane. A half cylinder turned about *any*
line in that plane clears the rod immediately — the near lip moves away, not in
— and turned about a line anywhere else it digs in. So the pin sits **in the
parting plane, at the upper rod's axis height, parallel to the upper rod**, and
that is the only family of positions that works at all. The verify step opens
the joint through eight positions and measures it:

| swung | clear of upper rod | fouls the other half |
|---|---|---|
| 2° | 0.22 mm | — |
| 10° | 0.58 mm | — |
| 40° | 4.49 mm | — |
| 80° | clear | — |

It did not work first time, and both failures are worth naming because neither
is visible in a closed view:

- **A square cheek cannot hinge.** The fork started as a rectangular lug with a
  pin bore in it. Its corners stand 10 mm from the pin, in the middle of the arc
  the cap's own edge sweeps, and the joint bound at ten degrees while looking
  perfectly sound shut. Above the pin, a fork can only be a circle.
- **Nothing wide may sit above the pin.** The cap's tongue was drawn wide at the
  top to meet the cap's body, because at the fork's own width it stops 0.3 mm
  short of it and comes out as a *second solid*. But anything wider than the
  fork gap and higher than the pin swings outward and downward as the cap opens
  — a point directly over the pin lands at pin height at ninety degrees — onto
  the cheeks. The tongue is one blade the whole way up, and it reaches inboard
  exactly as far as the slot does, which turns out to be far enough.

### What it costs and what it saves

| per clamp | bolted | hinged |
|---|---|---|
| bolts, nuts, washers | 2 / 2 / 2 | 1 / 1 / 1 |
| steel pins | — | 1 × ⌀3 × 14.6 |
| pieces in the hand when open | 3 | **1** |
| plastic | 36.3 cm³ | 34.4 cm³ |
| unsupported overhang, cap | 414 mm² | 84 mm² |
| unsupported overhang, bottom | 0 mm² | 27 mm² |

| per dome (M) | bolted | hinged |
|---|---|---|
| **bolts worked in the field** | **84** | **52** |
| pins worked in the field | 28 | 28 |
| fasteners fitted in the shop | 20 | 52 |
| plastic | 6882 cm³ | 6824 cm³ |

Thirty-two field bolts become thirty-two pins pushed in at home, the clamp gets
5% lighter, and its cap loses four fifths of its unsupported overhang along with
the counterbores. The bottom half picks some up — 27 mm², the roof of the pin
bore where it crosses the fork gap, which is a 6.6 mm bridge and not a ceiling
— so the trade is a fifth of the cap's overhang against a small bridge, and
both halves still print flat with no support. The remaining 52 are the fan nodes' twenty — five plates on
two bolts, a harder problem and the obvious next one — and the thirty-two the
clamps keep.

### What is not answered

**How hard it grips.** Nothing in this project computes force, so nothing here
can say whether one bolt at this station holds what two did. It is the same
bolt at the same offset with the same washer; the second station now takes its
load in shear through a 3 mm steel pin instead of in tension through a bolt, and
whether that is equivalent is a question for a test rig, not for a CAD file.
Milestone 3 already lists *"print it and check repeated assembly and
disassembly"* and *"record the failure modes"*, and this is now the first thing
to put on that rig.

**Whether the hinge survives the cycles.** A printed knuckle on a steel pin,
opened and closed at every build and teardown, is a wear part. It is 2.85 mm of
material around the bore and nobody has cycled one.

Both parts stay. `fastenerStyle = 0` is the default and the bolted clamp is
unchanged to the byte, because a joint whose load path has never been measured
is not a joint to make compulsory.
