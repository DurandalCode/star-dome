# 0033. The second mirror set of feet takes the base hub's mirror image, not the hub turned over

- **Status:** accepted; reverses the "one part turned over" reading of the two
  mirror sets that [0025](0025-the-angle-is-met-on-a-pad.md) to
  [0032](0032-the-base-hub-is-one-print.md) all lived with
- **Date:** 2026-10-28
- **Where it lives:** `connectors/base_hub_v2.py` (`mirror`),
  `stardome/connectors.py` (`_base_placement`, `_split_base_hubs_by_hand`),
  [`base-hub.md`](../base-hub.md)

## The decision

The ten base points are two mirror sets of five. Until now the schedule put
one hub on all ten, turned over about its vertical axis at five of them.
Turning a flat part over is a rotation, so it fits the rods. It also swaps the
two faces of the stack.

Now nothing is turned over. The five feet the hub does not fit as drawn take
its **mirror image**: every arm at 180° minus its azimuth, the same rod on the
same level, the sleeve and its tunnel where they were (they are symmetric
across the mirror plane). It is a part of its own, with `m` on the end of the
id: `BASE3-8` and `BASE3-8m`, `BASE2-8` and `BASE2-8m`. The placement of each
foot reports a `hand`, `as-drawn` or `mirrored`, like the two-rod clamp's, and
none reports `turned_over`.

On D4 that is 4 + 4 `BASE3-8` and 1 + 1 `BASE2-8`; on M the same at size 10.

## Why

The sleeve for the rebar sits on one face of the stack, under the lowest
level. Turned over, it is on the dome side at five feet and on the outside at
the other five, so five bars stand inboard of the bow bundle and five
outboard. Hub 1.x had the same property with its pad, and nobody had noticed
([0025](0025-the-angle-is-met-on-a-pad.md)). With the mirror image all ten
bars are on the same side, every foot is assembled the same way up, and
nothing is turned over in the field.

## What was rejected

- **Keep one part and turn it over.** Fewer parts, and it fits the rods. The
  bar then stands on opposite sides of the bundle at the two sets. Nothing was
  measured that says that matters; this is a preference for ten identical
  assembly actions, which [`AGENTS.md`](../../AGENTS.md) ranks first.
- **A mirror flag on the placement, not a part.** The print export, the BOM,
  the scene builder and the file names all key on the part id. A hand that is
  not a part would have needed each of them taught about it.

## What it costs

- **Two prints to keep apart.** `BASE3-8` and `BASE3-8m` have the same volume,
  the same height and nearly the same outline. Nothing on the part says which
  is which. Label the pieces when they come off the bed.
- **Two more part ids** in the schedule (`distinct_part_types` rises by 2),
  two more `.FCStd` files per size, and four prints of each instead of eight of
  one. The total of prints does not change.
- **Part counts are split.** Anything that asked for the count of `BASE3-d`
  now has to add the `m`.
- **Hub 1.x is not changed.** It stays frozen
  ([0006](0006-a-superseded-design-is-frozen.md)) and is still turned over.
