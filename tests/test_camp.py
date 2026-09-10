"""Several domes joined by corridors.

The result worth locking in is the constraint: a dome has five bays and no
more, 72 degrees apart, so a camp's angles are not free. Everything else here
follows from that.
"""

from __future__ import annotations

import math

import pytest

from stardome import camp, config, cover, model

LINKS = [("L", "M"), ("L", "S1"), ("L", "S2"), ("M", "S3")]


@pytest.fixture(scope="module")
def domes():
    built = {}
    for label, variant in (("L", "L"), ("M", "M"),
                           ("S1", "S"), ("S2", "S"), ("S3", "S")):
        built[label] = model.build(config.load(variant), weave_mode="layered")
    return built


@pytest.fixture(scope="module")
def plan(domes):
    solved = camp.solve(domes, LINKS)
    return camp.geometry(solved, domes)


# --- the constraint -------------------------------------------------------
def test_a_dome_offers_five_bays_seventy_two_degrees_apart(domes):
    azimuths = camp._bay_azimuths(domes["L"])
    assert len(azimuths) == camp.BAYS
    gaps = [azimuths[i + 1] - azimuths[i] for i in range(len(azimuths) - 1)]
    for gap in gaps:
        assert gap == pytest.approx(72.0, abs=0.5)


def test_every_corridor_lands_in_a_bay_at_both_ends(plan):
    """The whole point of solving rather than drawing."""
    at = {d["label"]: d for d in plan["domes"]}
    for link in plan["corridors"]:
        a, b = at[link["from"]], at[link["to"]]
        out = (link["bay_azimuth_from_deg"] + a["spin_deg"]) % 360.0
        back = (link["bay_azimuth_to_deg"] + b["spin_deg"]) % 360.0
        assert out == pytest.approx(link["world_azimuth_deg"], abs=0.01)
        # The far dome's bay points back down the same line.
        opposed = abs((out - back + 180.0) % 360.0 - 180.0)
        assert opposed == pytest.approx(180.0, abs=0.5)


def test_more_corridors_than_bays_is_refused(domes):
    six = dict(domes)
    for extra in ("S4", "S5"):
        six[extra] = domes["S1"]
    links = [("L", other) for other in six if other != "L"]
    with pytest.raises(ValueError, match="tall bays"):
        camp.solve(six, links)


def test_a_loop_is_refused_rather_than_fudged(domes):
    """A cycle over-constrains a 72 degree grid, so it is not attempted."""
    with pytest.raises(ValueError, match="tree"):
        camp.solve(domes, LINKS + [("S1", "S2")])


def test_a_disconnected_camp_is_refused(domes):
    with pytest.raises(ValueError):
        camp.solve(domes, [("L", "M"), ("L", "S1"), ("S2", "S3")])


# --- where they stand -----------------------------------------------------
def test_the_hub_is_the_dome_with_the_most_corridors(plan):
    hub = max(plan["domes"], key=lambda d: d["corridors"])
    assert hub["label"] == "L"
    assert hub["corridors"] == 3
    assert (hub["x_mm"], hub["y_mm"]) == (0.0, 0.0)


def test_spacing_is_the_two_reaches_plus_the_corridor(plan):
    for link in plan["corridors"]:
        assert link["centre_distance_mm"] == pytest.approx(
            link["reach_from_mm"] + link["length_mm"] + link["reach_to_mm"], abs=0.2
        )


def test_the_domes_stand_where_the_bearings_say(plan):
    at = {d["label"]: d for d in plan["domes"]}
    for link in plan["corridors"]:
        a, b = at[link["from"]], at[link["to"]]
        angle = math.radians(link["world_azimuth_deg"])
        assert b["x_mm"] == pytest.approx(
            a["x_mm"] + math.cos(angle) * link["centre_distance_mm"], abs=1.0
        )
        assert b["y_mm"] == pytest.approx(
            a["y_mm"] + math.sin(angle) * link["centre_distance_mm"], abs=1.0
        )


def test_bays_left_over_are_counted(plan):
    for entry in plan["domes"]:
        assert entry["bays_free"] == camp.BAYS - entry["corridors"]


def test_the_default_camp_does_not_collide(plan, domes):
    assert camp.clashes(plan, domes) == []


def test_a_camp_squeezed_together_is_caught(domes):
    """Shorten the corridors far enough and the neighbours overlap."""
    tight = camp.solve(domes, LINKS, {"length": 10.0})
    assert camp.clashes(tight, domes)


# --- the drawn corridor ---------------------------------------------------
def test_both_ends_are_cut_to_their_own_dome(plan, domes):
    """A corridor between two domes is square at neither end."""
    at = {d["label"]: d for d in plan["domes"]}
    for link in plan["corridors"]:
        skin = link["drawing"]["skin"]
        half = skin["vertex_count"] // 2
        for label, ring in ((link["from"], skin["vertices"][:half]),
                            (link["to"], skin["vertices"][half:])):
            dome = domes[label]
            entry = at[label]
            rc = cover.radius(dome)
            lift = dome["meta"].get("skirt_height", 0.0) or 0.0
            for x, y, z in ring:
                dx, dy, dz = x - entry["x_mm"], y - entry["y_mm"], z - lift
                on = (math.sqrt(dx * dx + dy * dy + dz * dz) if dz >= 0
                      else math.hypot(dx, dy))
                assert on == pytest.approx(rc, abs=1.0)


def test_the_corridor_has_a_clear_run_between_the_domes(plan):
    for link in plan["corridors"]:
        assert link["clear_run_mm"] > 0
        assert link["drawing"]["rib_count"] >= 2


def test_a_portal_camp_draws_frames_instead_of_hoops(domes):
    solved = camp.solve(domes, LINKS, {"kind": "portal", "width": 1500.0,
                                       "height": 2100.0, "pitch": 1200.0})
    camp.geometry(solved, domes)
    for link in solved["corridors"]:
        assert link["drawing"]["frames"]
        assert not link["drawing"]["hoops"]


def test_totals_count_every_run(plan):
    t = plan["totals"]
    assert t["corridor_count"] == len(LINKS)
    assert t["corridor_length_m"] == pytest.approx(
        len(LINKS) * plan["corridor_spec"]["length"] / 1000.0, rel=1e-6
    )
    assert t["rib_material_m"] > 0
