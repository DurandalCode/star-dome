"""The order the bows go up in, and what that order costs.

Rule 1 of this project is that fast assembly is a requirement of the first
class. Everything measured so far describes the dome once it is standing.
This module is about getting it there.

## The only thing that makes a bow hard to add

A bow is nine metres of flexible rod. Laying it *on top of* what is already
standing is free -- you walk it round and drop it on. Passing it *under*
something already standing is not: the rod has to be sprung, or the standing
rod lifted off its node, and either way it is a two-person move at height.

So the cost of an assembly order is one number: **how many times a bow has to
be threaded under a bow that is already in place.** Call each of those a
threading.

## Why this is a graph problem and not a guess

Two bows are two great semicircles on the same sphere. Two distinct great
circles meet at one antipodal pair, and every bow covers exactly the half of
its circle above the ground plane, so **any two bows cross at most once**. The
count closes exactly: 105 pairs, 15 of which share both base points (the three
bows at a foot run foot-to-foot together and never cross elsewhere), leaving
the 90 rod-to-rod contacts the model already reports.

At each of those 90 crossings one rod is radially inside the other. That is
not a drawing convention here -- ``weave.global_profile`` solves for a radial
route that keeps every crossing clear, and its answer says who is inside.

So the weave is a digraph on 15 vertices with 90 arcs, one per crossing,
pointing **inner -> outer**. An assembly order is a linear ordering of the
vertices. An arc is free if the inner bow goes up first; it costs a threading
if the outer bow is already there. The number of threadings is therefore the
number of arcs pointing backwards along the order, which is the **minimum
feedback arc set** problem -- NP-hard in general and completely trivial at
n = 15, where the Held-Karp subset recursion settles it exactly in 2^15 * 15
steps.

Nothing here is heuristic. ``minimum_threadings`` returns the true optimum
over all 15! = 1.3e12 orders, and the count of how many orders achieve it.

## What comes out

- **The weave is cyclic, so a threading-free assembly does not exist.** There
  is no order at all in which every bow is laid on top of what is already
  standing. That is not a flaw; a weave with no cycles would be a stack of
  hoops with nothing holding it together.
- **The floor is 21 threadings out of 90 crossings**, and it is the same 21
  for every variant, because the digraph is a property of the topology and the
  chosen stacking order, not of the diameter. D3 and D12 are the same build,
  differing in rod length and weight rather than in moves.
- **Twenty of those 21 are forced by the ten lashed nodes alone.** The fan
  order fixes the radial level of all four rods at a node, which orients 60 of
  the 90 arcs before anything is routed. Feed only those 60 to the solver and
  the answer is 20. So the weave routing of the 30 free crossings is very
  nearly free, and almost the whole cost of assembly is bought at the nodes.
- **The obvious order is more than twice as expensive.** Building family by
  family -- the reference's own pentagram-first drawing -- costs 34 threadings
  at best and 54 at worst, against 21.

## What this does not do

- It does not model time, crew size or fatigue. A threading is one hard move;
  how long it takes is milestone 4's stopwatch, not this.
- It does not say the partial structure stands up. A single bow is a free
  arch that falls over, and nothing here knows that. ``standing`` in the
  schedule counts bows not yet passing through a completed node, which is a
  proxy for how many still need a hand on them, not a stability calculation.
- It assumes any single threading is physically possible -- that a 9 m rod
  can be sprung far enough to pass one already-placed rod. On a 3 m dome bent
  to a 1.5 m radius that is worth checking on the prototype before the number
  21 is treated as an assembly plan.
"""

from __future__ import annotations

from . import weave

FAMILIES = ("G", "U", "L")


def weave_digraph(data: dict) -> list:
    """One arc per crossing, pointing from the inner rod to the outer one.

    The radial offsets come from ``weave.global_profile``, which is the only
    place in the project that knows a physically consistent weave rather than
    a drawing convention. The solve is deterministic, so this is too.
    """
    solved = weave.global_profile(data)
    offset = {
        (rod, stop["node"]): stop["offset_mm"]
        for rod, stops in solved["routes"].items()
        for stop in stops
    }

    arcs = []
    for c in data["crossings"]:
        a, b, node = c["rod_a"], c["rod_b"], c["node"]
        da, db = offset[(a, node)], offset[(b, node)]
        inner, outer = (a, b) if da < db else (b, a)
        arcs.append(
            {
                "inner": inner,
                "outer": outer,
                "node": node,
                "tied": bool(c["tied"]),
                "separation_mm": round(abs(da - db), 6),
            }
        )
    arcs.sort(key=lambda x: (x["node"], x["inner"], x["outer"]))
    return arcs


def _masks(rods: list, arcs: list) -> list:
    """``out[i]`` is the bitmask of bows that bow ``i`` is inside of."""
    index = {name: i for i, name in enumerate(rods)}
    out = [0] * len(rods)
    for arc in arcs:
        out[index[arc["inner"]]] |= 1 << index[arc["outer"]]
    return out


def find_cycle(rods: list, arcs: list) -> list:
    """A shortest directed cycle in the weave, or an empty list if acyclic.

    This is the evidence for the claim that no threading-free order exists:
    a cycle of bows each inside the next cannot be linearised, so at least one
    of its arcs must be paid for whatever the order.
    """
    index = {name: i for i, name in enumerate(rods)}
    n = len(rods)
    adjacency = [[] for _ in range(n)]
    for arc in arcs:
        adjacency[index[arc["inner"]]].append(index[arc["outer"]])

    best: list = []
    for start in range(n):
        # Breadth-first from start; the first arc that comes back to start
        # closes the shortest cycle through it.
        previous = {start: start}
        frontier = [start]
        found = None
        while frontier and found is None:
            nxt = []
            for u in frontier:
                for w in adjacency[u]:
                    if w == start:
                        found = u
                        break
                    if w not in previous:
                        previous[w] = u
                        nxt.append(w)
                if found is not None:
                    break
            frontier = nxt
        if found is None:
            continue
        path = [found]
        while path[-1] != start:
            path.append(previous[path[-1]])
        path.reverse()
        if not best or len(path) < len(best):
            best = path
    return [rods[i] for i in best]


def order_cost(order: list, arcs: list) -> int:
    """Threadings this order costs: arcs whose inner bow goes up second."""
    position = {name: i for i, name in enumerate(order)}
    return sum(1 for a in arcs if position[a["inner"]] > position[a["outer"]])


def minimum_threadings(rods: list, arcs: list) -> dict:
    """Exact minimum over every ordering, with one order that achieves it.

    Held-Karp over subsets. ``f[S]`` is the cheapest way to raise the bows in
    ``S`` first, in some order; appending bow ``v`` to that prefix costs one
    threading for every bow already standing that ``v`` has to pass under,
    which is ``popcount(inside_of[v] & S)`` and depends on nothing else. That
    independence is what makes the recursion exact.

    ``optimal_orders`` counts how many of the 15! orderings hit the minimum,
    which says whether the answer is a knife edge or a broad plateau.
    """
    n = len(rods)
    inside_of = _masks(rods, arcs)
    full = (1 << n) - 1
    unreached = len(arcs) + 1

    cost = [unreached] * (1 << n)
    ways = [0] * (1 << n)
    last = [-1] * (1 << n)
    cost[0] = 0
    ways[0] = 1

    for subset in range(1 << n):
        here = cost[subset]
        if here >= unreached:
            continue
        count = ways[subset]
        for v in range(n):
            bit = 1 << v
            if subset & bit:
                continue
            candidate = here + bin(inside_of[v] & subset).count("1")
            target = subset | bit
            if candidate < cost[target]:
                cost[target] = candidate
                ways[target] = count
                last[target] = v
            elif candidate == cost[target]:
                ways[target] += count

    order: list = []
    subset = full
    while subset:
        v = last[subset]
        order.append(rods[v])
        subset ^= 1 << v
    order.reverse()

    return {
        "threadings": cost[full],
        "order": order,
        "optimal_orders": ways[full],
        "crossings": len(arcs),
    }


def family_blocked(rods: list, arcs: list) -> list:
    """Every order that raises one whole family before starting the next.

    This is the order a person can actually be told: "all five G, then all
    five U, then all five L". The reference's own construction diagram draws
    it that way. Worth pricing against the optimum, because an order that has
    to be read off a sheet is not the same thing as a rule.
    """
    out = []
    for a in FAMILIES:
        for b in FAMILIES:
            if b == a:
                continue
            c = next(f for f in FAMILIES if f not in (a, b))
            rank = {f: i for i, f in enumerate((a, b, c))}
            order = sorted(rods, key=lambda r: (rank[r[0]], r))
            out.append(
                {
                    "families": f"{a}-{b}-{c}",
                    "order": order,
                    "threadings": order_cost(order, arcs),
                }
            )
    out.sort(key=lambda o: o["threadings"])
    return out


def schedule(data: dict, order: list, arcs: list) -> list:
    """Step by step: what each bow meets, what it costs, what it completes.

    ``nodes_closed`` is the lashed nodes whose fourth rod arrives at this
    step -- the moment a fan connector can be bolted up, and therefore the
    moment that node stops being held by hand. ``feet_closed`` is the same for
    a base point's three bow ends.
    """
    lashed = {
        n["name"]: set(n["rods"])
        for n in data["nodes"]
        if n["rod_count"] == 4
    }
    feet = {b["name"]: set(b["rods"]) for b in data["base_nodes"]}

    by_pair = {
        frozenset((arc["inner"], arc["outer"])): arc for arc in arcs
    }

    lashed_rods: set = set()
    placed: list = []
    rows = []
    running = 0
    closed_nodes = 0

    for step, bow in enumerate(order, start=1):
        meets = 0
        thread_under = []
        for other in placed:
            arc = by_pair.get(frozenset((bow, other)))
            if arc is None:
                continue
            meets += 1
            if arc["inner"] == bow:
                thread_under.append(other)
        placed.append(bow)
        standing = set(placed)

        nodes_closed = sorted(
            name
            for name, members in lashed.items()
            if bow in members and members <= standing
        )
        feet_closed = sorted(
            name
            for name, members in feet.items()
            if bow in members and members <= standing
        )
        for name in nodes_closed:
            lashed_rods |= lashed[name]

        running += len(thread_under)
        closed_nodes += len(nodes_closed)
        rows.append(
            {
                "step": step,
                "rod": bow,
                "family": bow[0],
                "crossings_made": meets,
                "threadings": len(thread_under),
                "threads_under": sorted(thread_under),
                "cumulative_threadings": running,
                "nodes_closed": nodes_closed,
                "feet_closed": feet_closed,
                "lashed_nodes_total": closed_nodes,
                "standing_unlashed": len(standing - lashed_rods),
            }
        )
    return rows


def analyse(data: dict) -> dict:
    """The whole picture for one variant."""
    rods = [r["name"] for r in data["rods"]]
    arcs = weave_digraph(data)
    tied = [a for a in arcs if a["tied"]]

    best = minimum_threadings(rods, arcs)
    forced = minimum_threadings(rods, tied)
    cycle = find_cycle(rods, arcs)
    blocked = family_blocked(rods, arcs)

    return {
        "variant": data["meta"]["variant"],
        "rods": len(rods),
        "crossings": len(arcs),
        "lashed_arcs": len(tied),
        "free_arcs": len(arcs) - len(tied),
        "acyclic": not cycle,
        "shortest_cycle": cycle,
        "threadings": best["threadings"],
        "optimal_orders": best["optimal_orders"],
        "order": best["order"],
        # Reversing an order flips every arc, so the dearest order costs
        # exactly the crossings less the cheapest. No second solve needed.
        "worst_threadings": len(arcs) - best["threadings"],
        "forced_by_nodes": forced["threadings"],
        "attributable_to_routing": best["threadings"] - forced["threadings"],
        "family_blocked": blocked,
        "schedule": schedule(data, best["order"], arcs),
    }


def format_analysis(data: dict) -> str:
    """Human-readable summary, for the CLI."""
    a = analyse(data)
    lines = [
        f"--- {a['variant']} assembly order  "
        f"({a['rods']} bows, {a['crossings']} crossings)",
    ]
    if a["acyclic"]:
        lines.append("  the weave is acyclic: some order lays every bow on top")
    else:
        lines.append(
            "  the weave is cyclic, so no threading-free order exists: "
            + " inside ".join(a["shortest_cycle"])
            + f" inside {a['shortest_cycle'][0]}"
        )
    lines += [
        f"  minimum threadings {a['threadings']} of {a['crossings']} crossings"
        f"   (worst order {a['worst_threadings']}; "
        f"{a['optimal_orders']} orders reach the minimum)",
        f"  forced by the {a['lashed_arcs'] // 6} lashed nodes alone: "
        f"{a['forced_by_nodes']}"
        f"  -- only {a['attributable_to_routing']} comes from routing the "
        f"{a['free_arcs']} free crossings",
        "  raise in this order: " + " ".join(a["order"]),
        "  one family at a time, for comparison:",
    ]
    for option in a["family_blocked"]:
        lines.append(f"    {option['families']}   {option['threadings']} threadings")
    lines.append(
        f"    (the cheap ones are exactly those raising L before U; the best "
        f"costs {a['family_blocked'][0]['threadings'] - a['threadings']} more "
        f"than the optimum)"
    )
    lines.append("  step  bow  meets  thread  under            closes")
    for row in a["schedule"]:
        closes = ", ".join(row["nodes_closed"] + row["feet_closed"]) or "-"
        under = " ".join(row["threads_under"]) or "-"
        lines.append(
            f"   {row['step']:>3}  {row['rod']:<3}  {row['crossings_made']:>5}  "
            f"{row['threadings']:>6}  {under:<16} {closes}"
        )
    lines.append(
        f"  first lashed node closes at step "
        f"{next((r['step'] for r in a['schedule'] if r['nodes_closed']), 0)}; "
        f"all ten by step "
        f"{next((r['step'] for r in a['schedule'] if r['lashed_nodes_total'] == 10), 0)}"
    )
    return "\n".join(lines)
