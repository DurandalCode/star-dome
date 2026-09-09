"""How much floor you can stand on.

The project's goal is a room for an event, so this is the metric that decides
whether a variant is worth building. These tests lock in the two results that
change decisions: a bare dome wastes most of its floor, and a skirt is the
cheapest way to get it back.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, interior, model

VARIANTS = sorted(config.load_all())


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param))


def skirted(name: str, skirt_mm: float):
    return model.build(config.load(name, skirt_height=skirt_mm))


def test_a_bare_dome_wastes_most_of_its_floor_when_small():
    """D4 has 12.6 m2 of floor and 2.4 m2 you can stand in."""
    d4 = model.build(config.load("D4"))
    result = interior.usable_area(d4, 1800.0)
    assert result["floor_m2"] == pytest.approx(12.57, abs=0.05)
    assert result["usable_m2"] == pytest.approx(2.39, abs=0.05)
    assert result["fraction"] < 0.2


def test_a_small_dome_on_a_skirt_beats_a_bigger_one_without():
    """D3 + 1 m of skirt gives more standing room than D4 bare, on less rod.

    This is the result that decides the small end of the family, so it is
    worth a test rather than a note.
    """
    d3 = skirted("D3", 1000.0)
    d4 = model.build(config.load("D4"))
    a3 = interior.usable_area(d3, 1800.0)
    a4 = interior.usable_area(d4, 1800.0)
    assert a3["usable_m2"] > 2 * a4["usable_m2"]

    e3 = interior.rod_efficiency(d3)
    e4 = interior.rod_efficiency(d4)
    assert e3["m2_per_rod_m"] > e4["m2_per_rod_m"]
    assert e3["total_rod_m"] < e4["total_rod_m"]


def test_a_bare_dome_has_the_same_tip_index_at_every_size():
    """The bare shape is self-similar, so wind exposure is a constant."""
    for name in VARIANTS:
        data = model.build(config.load(name, skirt_height=0.0))
        assert interior.exposure(data)["tip_index"] == pytest.approx(0.424, abs=0.005)


def test_the_skirt_is_paid_for_in_tipping():
    """Standing room goes up, and so does the overturning arm. Both, always."""
    previous_area = -1.0
    previous_tip = -1.0
    for skirt in (0.0, 500.0, 1000.0, 1600.0, 2000.0):
        data = skirted("D3", skirt)
        area = interior.usable_area(data, 1800.0)["usable_m2"]
        tip = interior.exposure(data)["tip_index"]
        assert area >= previous_area
        assert tip > previous_tip
        previous_area, previous_tip = area, tip


def test_standing_room_saturates_but_tipping_does_not():
    """Past the point where the whole floor is usable, more skirt buys nothing.

    D3's floor is fully usable at about 1.6 m of skirt; going to 2.0 m adds
    2% of area and another 0.13 to the tip index. That asymmetry is the whole
    argument against simply making the skirt taller.
    """
    mid = skirted("D3", 1600.0)
    tall = skirted("D3", 2000.0)
    area_mid = interior.usable_area(mid, 1800.0)["usable_m2"]
    area_tall = interior.usable_area(tall, 1800.0)["usable_m2"]
    tip_mid = interior.exposure(mid)["tip_index"]
    tip_tall = interior.exposure(tall)["tip_index"]

    assert area_tall - area_mid < 0.2       # m2
    assert tip_tall - tip_mid > 0.1


def test_usable_area_never_exceeds_the_floor(built):
    floor = math.pi * built["meta"]["dome_radius"] ** 2 / 1e6
    for height in interior.STANDING_HEIGHTS_MM:
        result = interior.usable_area(built, height)
        assert 0.0 <= result["usable_m2"] <= floor + 0.01
        assert result["floor_m2"] == pytest.approx(floor, abs=0.01)


def test_taller_standing_height_never_gains_area(built):
    areas = [
        interior.usable_area(built, h)["usable_m2"]
        for h in interior.STANDING_HEIGHTS_MM
    ]
    assert areas == sorted(areas, reverse=True)


def test_a_skirted_d4_dominates_a_skirted_d3():
    """Skirt against skirt, D4 wins on area, tipping and rod efficiency.

    The older comparison in this file pits D3 + skirt against a *bare* D4,
    which flatters D3. Carrying the same walk-in door, D3 is dominated, and
    that is what decides the small end of the family.
    """
    d3 = skirted("D3", 1600.0)
    d4 = skirted("D4", 1320.0)

    assert (
        interior.usable_area(d4, 1800.0)["usable_m2"]
        > interior.usable_area(d3, 1800.0)["usable_m2"]
    )
    assert (
        interior.exposure(d4)["tip_index"] < interior.exposure(d3)["tip_index"]
    )
    assert (
        interior.rod_efficiency(d4)["m2_per_rod_m"]
        > interior.rod_efficiency(d3)["m2_per_rod_m"]
    )


def test_slenderness_flags_the_variants_that_stop_being_domes():
    """Overall height over diameter: a bare dome is 0.5, D3 + 1600 exceeds 1."""
    for name in VARIANTS:
        bare = model.build(config.load(name, skirt_height=0.0))
        assert interior.exposure(bare)["slenderness"] == pytest.approx(0.5, abs=0.01)

    assert interior.exposure(skirted("D3", 1600.0))["slenderness"] > 1.0
    assert interior.exposure(skirted("D4", 1320.0))["slenderness"] < 1.0


def test_the_door_requirement_makes_bigger_domes_strictly_better():
    """With each variant carrying its walk-in door, every column improves.

    This is the counterintuitive one: the skirt a door needs shrinks faster
    than the dome grows, so there is no size at which extra room is bought
    with extra exposure.
    """
    from stardome import entrance

    tips = []
    efficiencies = []
    for name in sorted(VARIANTS, key=lambda k: config.load(k).diameter):
        bare = model.build(config.load(name, skirt_height=0.0))
        needed = entrance.skirt_for_door(bare, 1800.0, 700.0)["skirt_needed_mm"]
        data = skirted(name, float(needed))
        tips.append(interior.exposure(data)["tip_index"])
        efficiencies.append(interior.rod_efficiency(data)["m2_per_rod_m"])

    assert tips == sorted(tips, reverse=True)
    assert efficiencies == sorted(efficiencies)


def test_rod_efficiency_improves_with_size_for_bare_domes():
    """The big domes are better value per metre of rod, which is why D12 exists."""
    efficiencies = []
    for name in sorted(VARIANTS, key=lambda k: config.load(k).diameter):
        data = model.build(config.load(name, skirt_height=0.0))
        efficiencies.append(interior.rod_efficiency(data)["m2_per_rod_m"])
    # D3 bare has no standing room at all, so start from D4.
    assert efficiencies[1:] == sorted(efficiencies[1:])
