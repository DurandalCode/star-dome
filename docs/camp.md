# A camp

[`corridor.md`](corridor.md) opens with the sentence this finishes — *a corridor
is how two domes become a camp rather than two tents* — and then does the half
that fits inside one dome: it puts a tunnel on a doorway and measures whether it
fits the hole it is attached to. A corridor between two domes has **two** ends,
and its length is not a parameter at all.

```bash
make camp                 # CAMP=yard by default
make camp CAMP=pair
python3 -m stardome camp yard
```

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

## A dome is turned, not re-drilled

A door faces a neighbour because the dome was **turned on the ground**, not
because a new doorway was cut for this site. `turn` rotates the dome and its
doors with it, and a plan reports the turn each link would want:

```
    west        door at 18.0 deg, 162.0 off the bearing  -- turn to 162 deg
```

What a turn cannot do is make one door face two neighbours. A dome in the middle
of a camp needs a door per neighbour, and that is a change to
`configs/variants.toml` — [decision 0016](decisions/0016-a-domes-doors-are-written-in-its-config.md)
put doors there precisely so it could be made. The plan says which dome is short
of one rather than quietly drawing a door that is not in the design:

```
  will not build as drawn:
    - hall's nearest door is 80 deg off the bearing to its neighbour -- turn hall to 275 deg
```

That is the shipped `yard` camp, and it is shipped *wrong on purpose*: the hall
has two neighbours and one door. `pair` is the other example — two M domes on
one corridor, with nothing wrong with it at all.

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

## What it will not do

**It will not fix a plan.** A corridor that does not fit the doorway it lands on
is reported and drawn anyway — whether it fits is `corridor`'s question and it
answers it, and a plan is allowed to be wrong on paper. That is what drawing it
before building it is for.

Nothing here is structural. Where a corridor meets a dome, what carries the load
across that joint, and what holds a tunnel down in wind are milestones 5 and 8.
