"""A camp: domes joined by corridors, laid out from a plan.

`corridor.py` opens with the sentence this module finishes -- a corridor is how
two domes become a camp rather than two tents -- and does the half that fits in
one dome. What is guarded here is the other half: that a link is described by
what it joins and nothing else, that everything about it follows from the two
positions, and that a plan which will not build says so rather than being
quietly adjusted until it does.
"""

from __future__ import annotations

import math

import pytest

from stardome import camp, config, cover, model

CAMPS = camp.load_all()


@pytest.fixture(scope="module")
def models():
    needed = {
        config.resolve(dome["variant"])
        for plan in CAMPS.values()
        for dome in plan["domes"]
    }
    return {name: model.build(config.load(name)) for name in sorted(needed)}


# --- the plan is read, and read strictly ------------------------------------


def test_the_shipped_camps_load(models):
    assert set(CAMPS) >= {"yard", "pair"}
    for name, plan in CAMPS.items():
        a = camp.analyse(plan, models)
        assert len(a["domes"]) == len(plan["domes"])
        assert len(a["links"]) == len(plan.get("links") or [])


def _write(tmp_path, body):
    path = tmp_path / "camps.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_a_camp_can_hold_two_of_one_variant_but_not_two_of_one_name(tmp_path):
    both = (
        '[camps.c]\n'
        '[[camps.c.domes]]\nname = "a"\nvariant = "M"\nat = [0, 0]\n'
        '[[camps.c.domes]]\nname = "b"\nvariant = "M"\nat = [9000, 0]\n'
    )
    assert camp.load_all(_write(tmp_path, both))["c"]

    clash = both.replace('name = "b"', 'name = "a"')
    with pytest.raises(ValueError, match="two domes called"):
        camp.load_all(_write(tmp_path, clash))


def test_a_link_has_to_join_two_domes_that_are_here(tmp_path):
    base = (
        '[camps.c]\n'
        '[[camps.c.domes]]\nname = "a"\nvariant = "M"\nat = [0, 0]\n'
    )
    with pytest.raises(ValueError, match="not in this camp"):
        camp.load_all(_write(
            tmp_path, base + '[[camps.c.links]]\nbetween = ["a", "ghost"]\n'
        ))
    with pytest.raises(ValueError, match="linked to itself"):
        camp.load_all(_write(
            tmp_path, base + '[[camps.c.links]]\nbetween = ["a", "a"]\n'
        ))
    with pytest.raises(ValueError, match="exactly two"):
        camp.load_all(_write(
            tmp_path, base + '[[camps.c.links]]\nbetween = ["a"]\n'
        ))


def test_a_camp_with_no_domes_is_not_a_camp(tmp_path):
    with pytest.raises(ValueError, match="no domes"):
        camp.load_all(_write(tmp_path, "[camps.c]\n"))


# --- everything about a link follows from the two positions -----------------


def test_the_bearing_is_read_off_the_positions(models):
    a = {"name": "a", "at": [0.0, 0.0], "turn": 0.0, "data": models["D6"]}
    b = {"name": "b", "at": [10000.0, 0.0], "turn": 0.0, "data": models["D6"]}
    assert camp.link(a, b, 900.0, 1950.0)["bearing_deg"] == pytest.approx(0.0)

    b["at"] = [0.0, 10000.0]
    assert camp.link(a, b, 900.0, 1950.0)["bearing_deg"] == pytest.approx(90.0)


def test_the_length_is_what_is_left_between_the_two_covers(models):
    """Not a parameter. The free run is the gap the fabrics leave."""
    a = {"name": "a", "at": [0.0, 0.0], "turn": 0.0, "data": models["D6"]}
    b = {"name": "b", "at": [10000.0, 0.0], "turn": 0.0, "data": models["D6"]}
    one = camp.link(a, b, 900.0, 1950.0)
    assert one["length_mm"] == pytest.approx(
        one["centres_mm"] - sum(one["reach_mm"]), abs=0.2
    )
    # Move them apart and the corridor grows by exactly as much.
    b["at"] = [12000.0, 0.0]
    assert camp.link(a, b, 900.0, 1950.0)["length_mm"] == pytest.approx(
        one["length_mm"] + 2000.0, abs=0.2
    )


def test_covers_that_touch_are_reported_as_the_overlap_they_are(models):
    a = {"name": "a", "at": [0.0, 0.0], "turn": 0.0, "data": models["D6"]}
    close = cover.radius(models["D6"]) * 1.5
    b = {"name": "b", "at": [close, 0.0], "turn": 0.0, "data": models["D6"]}
    one = camp.link(a, b, 900.0, 1950.0)
    assert one["covers_overlap"] is True
    assert one["covers_clear_mm"] < 0


# --- a dome is turned, not re-drilled ---------------------------------------


def test_turning_a_dome_turns_its_doors_with_it(models):
    data = models["D6"]
    at_rest = camp.door_azimuths(data, 0.0)
    turned = camp.door_azimuths(data, 90.0)
    assert len(at_rest) == len(turned)
    for before, after in zip(at_rest, turned):
        assert after == pytest.approx((before + 90.0) % 360.0)


def test_a_door_that_does_not_face_its_neighbour_says_what_turn_would(models):
    data = models["D6"]
    door = camp.door_facing(data, 0.0, turn_deg=0.0)
    assert door["has_door"]
    # Apply the turn it asks for and the door comes round to the bearing.
    fixed = camp.door_facing(data, 0.0, turn_deg=door["turn_for_it_deg"])
    assert fixed["off_by_deg"] == pytest.approx(0.0, abs=1e-6)
    assert fixed["facing_it"] is True


def test_the_shipped_pair_is_a_camp_that_works():
    """`pair` is the example of a plan with nothing wrong with it."""
    ready = camp.prepare(CAMPS["pair"])
    a = camp.analyse(ready["plan"], ready["models"])
    assert a["problems"] == []
    assert len(a["links"]) == 1
    for door in a["links"][0]["doors"]:
        assert door["facing_it"] is True
        assert door["off_by_deg"] == pytest.approx(0.0, abs=0.01)


def test_a_dome_gets_one_door_per_neighbour():
    """The hall has two neighbours, so it has two doors -- and nobody wrote
    either of them anywhere."""
    ready = camp.prepare(CAMPS["yard"])
    a = camp.analyse(ready["plan"], ready["models"])
    hall = next(d for d in a["domes"] if d["name"] == "hall")
    assert len(hall["doors"]) == 2
    assert len(next(d for d in a["domes"] if d["name"] == "kitchen")["doors"]) == 1


def test_the_shipped_tree_is_a_camp_of_seven_that_works():
    """An XL hub, two L, two M and two S, six corridors, nothing wrong."""
    ready = camp.prepare(CAMPS["tree"])
    a = camp.analyse(ready["plan"], ready["models"])
    assert len(a["domes"]) == 7
    assert len(a["links"]) == 6
    assert a["problems"] == []
    # Every dome faces every neighbour it has.
    for one in a["links"]:
        for door in one["doors"]:
            assert door["facing_it"], one["between"]


# --- what gets drawn --------------------------------------------------------


def test_the_drawing_is_in_camp_coordinates(models):  # noqa: ARG001
    """Blender consumes it and computes nothing, so the mouths have to arrive
    where the domes actually stand."""
    plan = CAMPS["pair"]
    a = camp.analyse(plan, models)
    drawing = a["links"][0]["drawing"]
    first, second = drawing["mouths"]

    assert len(first) == len(second)
    assert len(drawing["rings"]) == a["links"][0]["hoops"]

    east = next(d for d in a["domes"] if d["name"] == "east")
    west = next(d for d in a["domes"] if d["name"] == "west")
    # Each mouth sits between its own dome and the other one.
    assert all(east["at"][0] < p[0] < west["at"][0] for p in first)
    assert all(east["at"][0] < p[0] < west["at"][0] for p in second)
    # And the gap between them is the length the link reports.
    gap = min(p[0] for p in second) - max(p[0] for p in first)
    assert gap == pytest.approx(a["links"][0]["length_mm"], abs=1.0)


def test_a_ring_is_the_two_mouths_interpolated(models):
    a = camp.analyse(CAMPS["pair"], models)
    drawing = a["links"][0]["drawing"]
    first, second = drawing["mouths"]
    rings = drawing["rings"]
    n = len(rings)
    for k, ring in enumerate(rings, start=1):
        f = k / (n + 1.0)
        for p, pa, pb in zip(ring, first, second):
            for i in range(3):
                assert p[i] == pytest.approx(pa[i] + (pb[i] - pa[i]) * f, abs=0.01)


def test_a_skirted_dome_is_lifted_so_the_camp_shares_one_ground(models):
    """A dome keeps its base ring at zero and hangs the skirt below, so a camp
    that ignored the lift would bury the small one."""
    plan = {
        "domes": [
            {"name": "flat", "variant": "M", "at": [0, 0]},
            {"name": "raised", "variant": "S", "at": [9000, 0]},
        ],
        "links": [{"between": ["flat", "raised"]}],
    }
    a = camp.analyse(plan, models)
    ground = min(
        p[2] for loop in a["links"][0]["drawing"]["mouths"] for p in loop
    )
    assert ground == pytest.approx(0.0, abs=1e-6)
