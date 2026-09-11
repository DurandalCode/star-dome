# 0010. Stack the four rods at a lashed node in fan order, 1-2-3-4

- **Status:** accepted
- **Date:** 2026-09-09
- **Where it lives:** `stardome/weave.py` (`STACK_ORDER`, `node_fan_in_part_order`), `docs/tied-node.md`

## The decision

At each lashed node the four rods stack radially in the order they fan out. Every
alternative is enumerated by `weave.stacking_options` with the rod-on-rod contacts it
creates; this is the one chosen.

## Why

It puts the three shallowest angles the fan offers into contact — 37.38, 41.81, 37.38 —
needs only two distinct saddle angles rather than three, is palindromic so the stack reads
the same from either side, and states in the field as one sentence: *stack them in the
order they fan out.*

The four rods at a lashed node are coplanar, because a great circle's tangent lies in the
sphere's tangent plane. So the node is a flat four-armed fan rather than a
three-dimensional tangle, all ten nodes are the same fan, and only rods adjacent in the
stack touch — which is what makes choosing the order a choice about which three of the
fan's angles become contacts.

## What was rejected

Every other permutation, on the two counts above. One of them creates fewer weave
collisions on the naive route; that turned out not to matter, because
`weave.global_profile` finds a consistent route for *any* order and the route stays inside
the radial band the stack already occupies.

## What it costs

Family G and L rods change level between nodes, so they migrate radially. Checked and
negligible: three levels is three rod diameters, spread over the arc between two tie
marks, a slope near 1.5% on a rod already bent to the dome radius.

A consequence for the part: a rod arrives at a node with a radial tilt of up to ~1.2°,
generally different on each side, so a channel drilled exactly on the tangent will
pre-stress it. `tiltAllowance` in the generators exists for this.

This decision is also where almost all of the assembly cost comes from. It orients 60 of
the 90 weave arcs before any routing happens, and those 60 alone force 18 of the 20
threadings the build needs — see `docs/assembly.md`. If a cheaper build is ever wanted,
this is the decision to reopen.

**Where the fan is cut matters as much as the order.** "Fan order" needs a first arm, and
a fan closes on itself, so one of its four gaps is never a contact. The part spends that
on the widest, 63.4349°, which is what leaves the three contacts above. Starting instead
at the arm with the smallest angle -- which is what sorting by angle does -- puts the
widest gap in the middle of the stack at the five LOWER nodes and asks for contacts
37.3774, 63.4349, 37.3774 there: a second part, at ten nodes this decision describes as
one. `weave.node_fan_in_part_order` cuts at the widest gap, and
`tests/test_weave.py` checks that all ten nodes come out with the same three contacts.
