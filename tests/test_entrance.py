"""Where a doorway fits.

These lock in the conclusion that matters for the whole family: a Star Dome
cannot take a walk-in entrance until it is very large, and the small ones
cannot take one at all without a skirt.
"""

from __future__ import annotations

import pytest

from stardome import config, entrance, model

VARIANTS = sorted(config.load_all())

# The default resolution, deliberately. The envelope is resolution-dependent:
# a rod blocks a whole bin plus a margin, so coarse bins under-report the free
# height -- 360 bins puts the D/4 ratio at 0.229 instead of 0.255. Testing at a
# resolution nobody uses would lock in the wrong number.
BINS = entrance.DEFAULT_BINS


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param))


@pytest.fixture(scope="module")
def d6():
    return model.build(config.load("D6"))


def test_free_height_is_a_quarter_of_the_diameter(built):
    """The topology is fixed, so the tallest gap scales with the dome exactly.

    Every variant is the same shape at a different size, so the tallest
    unobstructed spot at the base ring is the same fraction of the diameter --
    which makes it a rule of thumb rather than a lookup: about D/4.
    """
    env = entrance.door_envelope(built, bins=BINS)
    ratio = max(env["envelope_mm"]) / built["meta"]["dome_diameter"]
    assert ratio == pytest.approx(0.2549, abs=0.002)


def test_the_small_domes_have_no_standing_door(built):
    """D3 and D4 cannot take even a 1200 mm opening in the structure."""
    diameter = built["meta"]["dome_diameter"]
    env = entrance.door_envelope(built, bins=BINS)
    widest = entrance.widest_at_height(built, 1200.0, env)["widest_mm"]
    if diameter <= 4000.0:
        assert widest == 0.0
    else:
        assert widest > 0.0


def test_a_walk_in_door_needs_a_ten_metre_dome(built):
    """1800 mm of clear height, at any width, arrives at D10."""
    diameter = built["meta"]["dome_diameter"]
    env = entrance.door_envelope(built, bins=BINS)
    widest = entrance.widest_at_height(built, 1800.0, env)["widest_mm"]
    if diameter >= 10000.0:
        assert widest > 700.0
    if diameter <= 6000.0:
        assert widest == 0.0


def test_the_largest_opening_is_bounded_by_the_envelope(built):
    env = entrance.door_envelope(built, bins=BINS)
    best = entrance.largest_doorway(built, env)
    assert best["height_mm"] <= max(env["envelope_mm"]) + 1e-6
    assert best["width_mm"] <= 2.0 * 3.14159 * built["meta"]["dome_radius"] + 1.0
    assert best["area_mm2"] > 0.0


def test_openings_repeat_with_the_five_fold_symmetry(d6):
    """The dome has D5 symmetry, so openings come in fives or tens."""
    env = entrance.door_envelope(d6, bins=BINS)
    result = entrance.widest_at_height(d6, 1200.0, env)
    assert result["opening_count"] in (5, 10)


def test_wider_doors_reach_less_high(d6):
    """The gap narrows as it rises, so width and height trade off."""
    env = entrance.door_envelope(d6, bins=BINS)
    reaches = [
        entrance.skirt_for_door(d6, 1800.0, w, env, step_mm=20.0)["dome_reach_mm"]
        for w in (200.0, 400.0, 700.0)
    ]
    assert reaches[0] >= reaches[1] >= reaches[2]


def test_clearance_only_ever_shrinks_the_opening(d6):
    tight = entrance.door_envelope(d6, bins=BINS, clearance_mm=0.0)
    loose = entrance.door_envelope(d6, bins=BINS, clearance_mm=25.0)
    assert all(
        b <= a + 1e-9 for a, b in zip(tight["envelope_mm"], loose["envelope_mm"])
    )


def test_the_skirt_bay_is_a_plain_rectangle():
    """Unlike the dome, a skirt bay has no ceiling curving in."""
    d3 = model.build(config.load("D3"))
    bay = entrance.skirt_bay(d3)
    assert bay is not None
    meta = d3["meta"]
    assert bay["height_mm"] == pytest.approx(meta["skirt_height"], abs=0.1)
    assert bay["width_mm"] == pytest.approx(
        meta["base_edge_chord"] - meta["rod_diameter"], abs=0.1
    )
    assert bay["bay_count"] == 10


def test_a_dome_without_a_skirt_reports_no_bay():
    """Asked explicitly for a bare dome -- the sizes in variants.toml now
    carry the skirt their doorway needs, so 'no skirt' has to be said."""
    bare = model.build(config.load("D6", skirt_height=0.0))
    assert entrance.skirt_bay(bare) is None


def test_the_skirt_a_standing_door_needs_shrinks_as_the_dome_grows():
    needed = []
    for name in sorted(VARIANTS, key=lambda k: config.load(k).diameter):
        data = model.build(config.load(name))
        env = entrance.door_envelope(data, bins=BINS)
        needed.append(entrance.skirt_for_door(data, 1800.0, 700.0, env)["skirt_needed_mm"])
    assert needed == sorted(needed, reverse=True)
    assert needed[0] > 1000.0   # D3 needs more skirt than it has
    assert needed[-1] == 0.0    # D12 needs none
