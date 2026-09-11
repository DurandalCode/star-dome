"""The assembly order: the weave digraph, and the exact threading minimum.

Two tests carry the weight here.

``test_subset_solver_matches_brute_force`` is the one that makes the headline
number trustworthy. The claim is not "a good order was found" but "no better
order exists", and the only honest way to check a Held-Karp recursion is
against every permutation on a problem small enough to enumerate.

``test_every_pair_of_bows_crosses_at_most_once`` is the one that makes the
model of the problem legitimate. The whole thing is a digraph on 15 vertices
only because two bows never cross twice; if that ever stopped holding, an
"order" would no longer determine the cost.
"""

from __future__ import annotations

import itertools
import random

import pytest

from stardome import assembly, config, model, weave

VARIANTS = sorted(config.load_all())


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param))


@pytest.fixture(scope="module")
def analysed(built):
    """``analyse`` runs the weave solve and two subset recursions, so it is
    worth computing once per variant rather than once per test."""
    return assembly.analyse(built)


@pytest.fixture(scope="module")
def d6():
    return model.build(config.load("D6"))


# --- the digraph -----------------------------------------------------------


def test_one_arc_per_crossing(built):
    arcs = assembly.weave_digraph(built)
    assert len(arcs) == len(built["crossings"]) == 90


def test_every_pair_of_bows_crosses_at_most_once(built):
    """Two great semicircles above the ground plane meet at most once.

    This is what lets an assembly order be a permutation of bows rather than
    of crossings: the cost of adding a bow depends on which bows are already
    up, not on where along them the contact falls.
    """
    arcs = assembly.weave_digraph(built)
    pairs = [frozenset((a["inner"], a["outer"])) for a in arcs]
    assert len(set(pairs)) == len(pairs)


def test_the_pairs_that_never_cross_are_the_ones_sharing_a_foot(built):
    """15 of the 105 pairs never cross, and they are exactly the co-footed.

    Three bows leave every base point and all three run to the antipodal
    base point, so each such pair shares both ends and meets nowhere else.
    Ten feet times three pairs, each counted at both ends, is 15.
    """
    names = [r["name"] for r in built["rods"]]
    crossing = {
        frozenset((a["inner"], a["outer"])) for a in assembly.weave_digraph(built)
    }
    never = {frozenset(p) for p in itertools.combinations(names, 2)} - crossing

    co_footed = set()
    for base in built["base_nodes"]:
        for pair in itertools.combinations(base["rods"], 2):
            co_footed.add(frozenset(pair))

    assert len(never) == 15
    assert never == co_footed


def test_arcs_point_from_the_inner_rod_outward(built):
    """The arc direction has to agree with the solved radial route."""
    solved = weave.global_profile(built)
    offset = {
        (rod, stop["node"]): stop["offset_mm"]
        for rod, stops in solved["routes"].items()
        for stop in stops
    }
    for arc in assembly.weave_digraph(built):
        assert offset[(arc["inner"], arc["node"])] < offset[(arc["outer"], arc["node"])]


def test_no_crossing_is_tighter_than_a_rod(built):
    rod = built["meta"]["rod_diameter"]
    for arc in assembly.weave_digraph(built):
        assert arc["separation_mm"] >= rod - 1e-6


def test_the_digraph_is_deterministic(d6):
    first = assembly.weave_digraph(d6)
    second = assembly.weave_digraph(model.build(config.load("D6")))
    assert first == second


# --- the cycle, and why a free assembly does not exist ----------------------


def test_the_weave_is_cyclic(built):
    rods = [r["name"] for r in built["rods"]]
    cycle = assembly.find_cycle(rods, assembly.weave_digraph(built))
    assert cycle, "an acyclic weave would allow a threading-free assembly"


def test_the_reported_cycle_is_really_a_cycle(built):
    arcs = assembly.weave_digraph(built)
    rods = [r["name"] for r in built["rods"]]
    cycle = assembly.find_cycle(rods, arcs)
    directed = {(a["inner"], a["outer"]) for a in arcs}
    for i, name in enumerate(cycle):
        assert (name, cycle[(i + 1) % len(cycle)]) in directed


def test_a_cycle_forces_at_least_one_threading(analysed):
    """The cycle is the proof, so the minimum must be consistent with it."""
    analysis = analysed
    assert not analysis["acyclic"]
    assert analysis["threadings"] >= 1


# --- the solver ------------------------------------------------------------


def _random_digraph(n, seed):
    """A tournament on n vertices: the shape the weave has, at a size we can
    enumerate."""
    rng = random.Random(seed)
    rods = [f"R{i}" for i in range(n)]
    arcs = []
    for a, b in itertools.combinations(rods, 2):
        inner, outer = (a, b) if rng.random() < 0.5 else (b, a)
        arcs.append({"inner": inner, "outer": outer, "node": "x", "tied": True})
    return rods, arcs


@pytest.mark.parametrize("seed", range(8))
def test_subset_solver_matches_brute_force(seed):
    """Held-Karp against all 7! orderings.

    The headline claim is a minimum over 15! orders, which cannot be checked
    directly. It can be checked at n = 7, where the same code path runs
    against every permutation there is.
    """
    rods, arcs = _random_digraph(7, seed)
    best = assembly.minimum_threadings(rods, arcs)

    costs = [
        assembly.order_cost(list(order), arcs)
        for order in itertools.permutations(rods)
    ]
    assert best["threadings"] == min(costs)
    assert best["optimal_orders"] == sum(1 for c in costs if c == min(costs))
    assert assembly.order_cost(best["order"], arcs) == best["threadings"]


def test_an_acyclic_weave_would_cost_nothing():
    """The solver has to return zero when a free order exists, or the claim
    that none exists here means nothing."""
    rods = [f"R{i}" for i in range(6)]
    arcs = [
        {"inner": a, "outer": b, "node": "x", "tied": True}
        for a, b in itertools.combinations(rods, 2)
    ]
    best = assembly.minimum_threadings(rods, arcs)
    assert best["threadings"] == 0
    assert best["order"] == rods


def test_reported_order_costs_what_is_claimed(built, analysed):
    arcs = assembly.weave_digraph(built)
    analysis = analysed
    assert assembly.order_cost(analysis["order"], arcs) == analysis["threadings"]


def test_no_sampled_order_beats_the_optimum(built, analysed):
    arcs = assembly.weave_digraph(built)
    names = [r["name"] for r in built["rods"]]
    best = analysed["threadings"]
    rng = random.Random(20260911)
    for _ in range(300):
        shuffled = names[:]
        rng.shuffle(shuffled)
        assert assembly.order_cost(shuffled, arcs) >= best


def test_reversing_an_order_costs_the_complement(built, analysed):
    """Every arc flips, so the dearest order is the crossings less the
    cheapest. ``worst_threadings`` is reported from this rather than solved
    again, so it is worth checking."""
    arcs = assembly.weave_digraph(built)
    analysis = analysed
    reversed_cost = assembly.order_cost(analysis["order"][::-1], arcs)
    assert reversed_cost == len(arcs) - analysis["threadings"]
    assert analysis["worst_threadings"] == reversed_cost


# --- the results this module exists to state -------------------------------


def test_assembly_cost_is_the_same_at_every_size(analysed):
    """The digraph comes from the topology and the stacking order, neither of
    which scales. A 3 m dome and a 12 m dome are the same build."""
    analysis = analysed
    assert analysis["threadings"] == 21
    assert analysis["forced_by_nodes"] == 20
    assert analysis["worst_threadings"] == 69


def test_most_of_the_cost_is_forced_by_the_lashed_nodes(analysed):
    """The stack order orients 60 of the 90 arcs before any routing happens,
    and those 60 alone already cost 20 of the 21."""
    analysis = analysed
    assert analysis["lashed_arcs"] == 60
    assert analysis["free_arcs"] == 30
    assert analysis["forced_by_nodes"] <= analysis["threadings"]
    assert analysis["attributable_to_routing"] == 1


def test_family_by_family_is_worse_than_the_optimum(analysed):
    """The order a person can be told, priced against the order a solver
    finds. If this ever inverts, the recommendation in docs/assembly.md is
    wrong."""
    analysis = analysed
    blocked = analysis["family_blocked"]
    assert len(blocked) == 6
    assert min(o["threadings"] for o in blocked) == 34
    assert max(o["threadings"] for o in blocked) == 54
    assert blocked[0]["threadings"] > analysis["threadings"]


# --- the schedule ----------------------------------------------------------


def test_schedule_covers_every_bow_once(built, analysed):
    rows = analysed["schedule"]
    assert len(rows) == 15
    assert sorted(r["rod"] for r in rows) == sorted(r["name"] for r in built["rods"])


def test_schedule_accounts_for_every_crossing(analysed):
    """Each crossing is made exactly once, by whichever of its two bows is
    raised second."""
    rows = analysed["schedule"]
    assert sum(r["crossings_made"] for r in rows) == 90


def test_schedule_threadings_sum_to_the_total(analysed):
    analysis = analysed
    rows = analysis["schedule"]
    assert sum(r["threadings"] for r in rows) == analysis["threadings"]
    assert rows[-1]["cumulative_threadings"] == analysis["threadings"]


def test_every_node_and_foot_closes_by_the_end(built, analysed):
    rows = analysed["schedule"]
    closed_nodes = [n for r in rows for n in r["nodes_closed"]]
    closed_feet = [f for r in rows for f in r["feet_closed"]]
    assert sorted(closed_nodes) == sorted(
        n["name"] for n in built["nodes"] if n["rod_count"] == 4
    )
    assert sorted(closed_feet) == sorted(b["name"] for b in built["base_nodes"])
    assert rows[-1]["lashed_nodes_total"] == 10


def test_a_bow_only_threads_under_bows_already_standing(analysed):
    rows = analysed["schedule"]
    standing: set = set()
    for row in rows:
        assert set(row["threads_under"]) <= standing
        assert len(row["threads_under"]) == row["threadings"]
        standing.add(row["rod"])


def test_the_first_bow_is_free_and_meets_nothing(analysed):
    first = analysed["schedule"][0]
    assert first["crossings_made"] == 0
    assert first["threadings"] == 0
