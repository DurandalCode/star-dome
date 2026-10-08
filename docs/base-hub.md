# Base hub versions

The base hub (`BASE3-d`, `BASE2-d`) is the one connector that has been printed
and fitted. Its versions are numbered so a printed piece can be traced to the
geometry that made it. A version is a git tag. A version that has been
superseded is frozen, and is not updated
([0006](decisions/0006-a-superseded-design-is-frozen.md)).

| version | tag | stake | what it is |
|---|---|---|---|
| 1.0 | `base-hub-1.0` | steel angle | a stack of flat plates, one channel per level; a pad on the bottom plate and a printed wrap round the angle ([0025](decisions/0025-the-angle-is-met-on-a-pad.md)–[0029](decisions/0029-put-the-lower-stack-bolts-inside-the-base-plate.md)) |
| 1.1 | `base-hub-1.1` | rebar, 8–18 mm | 1.0 with the wrap replaced by a vee cradle on the same pad; the plates are identical ([0031](decisions/0031-the-stake-is-rebar-and-a-vee-takes-any-bar.md)) |
| 2.0 | — | rebar | in design |

`connectors/base_hub_v1.py` is 1.1, and stays 1.1.

## What the printed set is for

One `BASE3-8` is printed: plates from 1.0, which 1.1 left unchanged. Its rod
channels are drawn for an 8 mm rod with 1.4 mm of clearance, Ø9.4. In the
hand **a 10 mm composite rebar goes in and an 8 mm one rattles**. The printed
set is therefore a hub for 10 mm composite bows, whatever its name says.
Composite rebar is named by an equivalent diameter and measures differently
across its winding. Until that is measured, the channel says nothing about
the rod named on the part.

## What 1.x taught

The fit check found more than the channel:

- **The stack carries material nobody needs.** Each plate is the full outline
  of the hub. A rod occupies one level, but every other level is solid across
  the same footprint. Seen end on, a printed stack is a block with three holes
  in it.
- **The levels are inherited from the node, where they are needed.** At a
  lashed node the rods pass through each other's crossing, so they cannot
  share an axis and must stack. At a base point all three bows *end*, at one
  point, in one plane ([`weave.base_fan`](../stardome/weave.py)). Nothing
  forces them onto different levels.
- **Five prints per hub is too many** for 10 hubs a dome.
- **The cradle is a short grip**: 40 mm along the bar, and a loose piece to
  hold while two bolts are started.

2.0 starts from those four points.
