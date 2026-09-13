# A camp

[`corridor.md`](corridor.md) opens with the sentence this finishes — *a corridor
is how two domes become a camp rather than two tents* — and then does the half
that fits inside one dome: it puts a tunnel on a doorway and measures whether it
fits the hole it is attached to. A corridor between two domes has **two** ends,
and its length is not a parameter at all.

```bash
make camp                 # CAMP=yard by default
make camp CAMP=tree       # an XL hub and six domes hanging off it
python3 -m stardome camp tree
```

Four camps ship: `pair`, two M domes on one corridor; `yard`, three round a
yard; `tree`, an XL hub with two L halls, two M off one hall and two S off one
of those — seven domes and six corridors; and `court`, which closes the far
end of that tree back on itself, so six of its eight domes stand round an open
yard and every one of them is reachable two ways.

## What is written down, and what is derived

`configs/camps.toml` says which domes stand where, how far each is turned, and
which pairs are joined. **That is all it says.** Everything else follows:

| derived | from |
|---|---|
| the bearing between two domes | their two positions |
| which door that bearing wants | the doors in `variants.toml`, plus the turn |
| the corridor's length | the gap the two covers leave along that bearing |
| the two mouths | each cover, at that bearing |

A bearing typed into both files is a bearing that stops agreeing with itself, so
it is typed into neither. Move a dome and everything moves with it.

## One door per neighbour, and the one door nobody can derive

A dome in the middle of a camp has every door it owns taken by a corridor, so
there is nothing left to walk in through: `court`'s hub had two neighbours,
two doors and no entrance. That one is a decision rather than a consequence,
so a dome may write extra bearings of its own:

```toml
[[camps.court.domes]]
name = "hub"
doors = [252]
```

They are added to the ones the links ask for. **It cannot be any bearing.** A
door sits in a bay and there are five of them 72° apart, so an extra door has
to be a multiple of 72° from the ones the corridors already want — or the
derived turn moves to accommodate it and the corridors stop landing square.
Asking the hub for 216° swung it 18° and put both its corridor doors 18° out.
252° is 144° from one and 216° from the other, and it faces away from the camp.

## One door per neighbour, and nobody writes them

A dome joined to three others has three doors, pointing at the three. Neither
the count nor the directions appear anywhere in either config: the links
already determine both, and writing them down would be writing down something
already determined.

`configs/variants.toml` keeps describing a dome **standing on its own**, which
is what it is for. A camp builds its own domes.

## Five places for a door, 72° apart

This is the constraint that decides how a camp is laid out, and it is not
obvious until the first plan fails.

A door goes in a *bay*, and a dome has five of each kind, **72° apart**. So a
dome cannot put a door on an arbitrary bearing: the best it can do is the
nearest bay, up to 36° away. Which way the dome is set down therefore matters,
and `turn` is derived — the turn that makes the worst of its doors the least
bad, found by scanning, because the objective is a maximum of absolute
differences and has corners everywhere.

The sharp consequence:

> **Two domes that face each other want their lattices half a bay apart.**
> A bearing and its reverse differ by 180°, and 180 is not a multiple of 72, so
> two domes turned the same way can never *both* have a door on the line
> between them. Turn one by 36° and both can.

A camp whose links form a tree can always be coloured that way, and the
derived turns come out alternating 0° and 36° along every corridor — which is
what the shipped `tree` does without anyone arranging it.

The other half of the same constraint is on the positions: neighbours want to
sit at bearings 72° apart from a common dome. The `tree` camp is laid out that
way, and every one of its six corridors lands square on a door at both ends.
Lay one out by eye instead and the plan says how far off each door is.

## The length is what is left between two covers

A dome's cover reaches further out at the crown of a tunnel's section than at
its floor, so the joint is not a plane cut — `corridor.mouth` already reports how
far from flat it is, 680 mm on M. What a corridor has to span is therefore
measured from the furthest point of each mouth:

    length = distance between centres − reach of A − reach of B

Two M domes 10 m apart leave **4027 mm** of free run. Move them 2 m further
apart and the corridor grows by exactly 2 m; there is no number anybody chose in
it. When two domes are close enough that their covers would touch it comes out
negative, and that is reported as the overlap it is rather than as a corridor of
negative length.

## A ring, and why the chain in it has three domes

`court` is `tree` with its far end closed: `hall_west` carries two M, and the
two M are joined back to each other by a chain of S. That makes a **cycle**,
and a cycle is what the 72° rule above cannot always serve.

The derived turns alternate 0° and 36° along every corridor, which is a
two-colouring of the link graph — and a graph is two-colourable only if every
cycle in it is even. A chain of two S closes the ring with five corridors and
one door lands 36° out. Three closes it with six, and every door lands square.

The positions are not laid out by eye either. Round the ring, the angle at
each dome between its two neighbours must be a multiple of 72°, and the six of
them must sum to 720° — which leaves 72° at the two M and 144° everywhere
else, and that in turn forces the three edge lengths to satisfy

    L–M  =  S–S  +  0.618 × M–S

Pick the two short ones at two metres of free run and the long one follows.
`hall_west` also carries the hub, so the bearing to the hub has to be a
multiple of 72° from the bearings to both M: 216° is and 180° is not, which is
why the plan is not symmetric about an axis.

## Two kinds of corridor, and a junction is not a bearing

```bash
make camp CAMP=court CAMP_KIND=portal
python3 -m stardome camp court --kind portal --pitch 3000
```

A link is joined by a bent-rod **hoop** (900 × 1950 by default) or by a timber
**portal** — two posts, a header and a knee brace in each top corner, 1800 ×
2100 out of 45 × 145 board. See [`corridor.md`](corridor.md) for the section
each one leaves. `--kind` sets the camp's default and a link in
`configs/camps.toml` can override it with its own `kind`, so one camp can hold
both.

The kind is not a finish. The mouth is cut to the section, so a wider corridor
reaches less far up the sphere and leaves a **longer** free run between the
same two covers: on `pair`, 4027 mm on hoops against 4234 mm on portals.

And the plan now answers two questions rather than one. The layout solves
**bearings**; whether the section also passes **through** the bay it lands on
is separate, and reported separately — saying only the first would be true and
misleading in the same breath. A portal is wider than every bay in the family,
so its posts come down on the bows; the 900 mm hoop passes at S, which stands
on a skirt, and fails at bare M and bare L.

Neither is the corridor being wrong. A person walks through every one of those
doors. It means the junction needs the entrance/corridor interface from
milestone 5, or a narrower corridor.

## Walking through it

```bash
make camp CAMP=court CAMP_KIND=portal CAMP_FLAGS="--cover --figures one --walk"
```

`--walk` on `blender/build_site.py` changes several things at once, and it is
useless without all of them:

- **the covers go opaque.** At 0.14 alpha a camp is a diagram; from the
  inside it is not a room at all.
- **a lamp goes inside every dome and every corridor.** An opaque dome under
  sunlight is a black hole from within. Power follows the floor each lamp has
  to cover, so the 12 m dome is not lit to the same few watts as the 4 m one.
  The corridor lamps cast no shadow — sixteen shadow-casting lights asked
  EEVEE for 2400 of the 2048 shadow maps it has, and a tunnel lamp is fill.
- **the scene camera becomes an eye 1.7 m off the ground**, standing clear of
  the camp and looking back at it, with a 24 mm lens and a 50 mm near clip so
  putting your face through a doorway does not clip the world away.
- **the translucent panel across each doorway is left out.** It says "this is
  the hole" in a picture and it is a wall to walk into.

And one thing that is not a walk-through setting at all, because it is simply
true: **the cover is cut open where something goes through it.** The cover is
a shell of revolution with no doorway and no hole where a corridor lands, so a
camp that looks joined was a row of sealed domes with tubes leaning on them
and a door painted on. Every opening is now taken out of it — 16 corridor
mouths and 17 doorways on `court`. The check is a ray, not an eye: out of the
hub along a corridor it now reaches the far dome's wall 15.7 m away, and in a
direction with no opening it stops on the cover at 4.7 m.

The cover gets 30 mm of thickness first, and that is not decoration. The exact
boolean solver decides what is inside a target by winding number, and an open
sheet has none: asked to take a plug out of one it welds the plug's own end
cap in instead. The hole came out as a bump, and a ray stopped dead on it a
metre short of where the cover actually is.

Blender does the walking: `Numpad 0`, then `Shift+\`` for Walk Navigation.
Gravity is a preference and not a scene setting, so it cannot be shipped in
the file — Preferences > Navigation > Walk > Gravity.

The still preview is still taken from the overview camera. A render from the
eye is a picture of the inside of whatever it happens to be facing, which is
no use as a thumbnail.

## What it will not do

**It will not fix a plan.** A corridor that does not fit the doorway it lands on
is reported and drawn anyway — whether it fits is `corridor`'s question and it
answers it, and a plan is allowed to be wrong on paper. That is what drawing it
before building it is for.

Nothing here is structural. Where a corridor meets a dome, what carries the load
across that joint, and what holds a tunnel down in wind are milestones 5 and 8.
