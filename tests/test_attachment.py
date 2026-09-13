"""What holds the cover on: counts, lengths, and the one structural claim.

The claim worth testing is not a length. It is that the attachment needs no
new part -- every anchor is a driven angle that is already there, doing the
same job for the frame -- and that the straps fall out of the topology rather
than being chosen.
"""

from __future__ import annotations

import math

import pytest

from stardome import attachment, config, cover, model

NAMED = ("S", "M", "L", "XL", "XXL")


@pytest.fixture(params=NAMED)
def built(request):
    return model.build(config.load(request.param))


def test_every_foot_takes_exactly_one_strap_end(built):
    """Five straps, ten ends, ten feet. That is why this family was chosen.

    All three bow families touch every foot exactly once, so any of them would
    share the anchors out evenly; U is picked because it is the one that goes
    over the crown. If a family were ever chosen that doubled up on a foot,
    one angle would take two straps and another none.
    """
    lines = attachment.straps(built)
    assert lines["count"] == 5
    assert lines["one_end_per_foot"]
    assert sorted(lines["ends_per_foot"]) == [
        b["name"] for b in built["base_nodes"]
    ]
    assert set(lines["ends_per_foot"].values()) == {1}


def test_the_strap_family_is_the_one_that_crosses_the_crown(built):
    """A cover held only at its edge lifts in the middle. The strap family has
    to reach the top, and only one of the three does."""
    tops = {}
    with_points = model.build(
        config.load(built["meta"]["variant"]), include_polylines=True
    )
    for rod in with_points["rods"]:
        top = max(p[2] for p in rod["points"])
        tops[rod["family"]] = max(tops.get(rod["family"], 0.0), top)

    height = built["meta"]["dome_height_measured"]
    assert tops[attachment.STRAP_FAMILY] == pytest.approx(height, rel=1e-6)
    for family, top in tops.items():
        if family != attachment.STRAP_FAMILY:
            assert top < height


def test_the_attachment_adds_no_printed_part(built):
    """Milestone 5 asks for an attachment that does not concentrate load on
    one printed part. The way this satisfies it is by having no part at all:
    the anchor is the driven angle the foot already stands on."""
    a = attachment.analyse(built)
    assert a["anchors"]["new_printed_parts"] == 0
    assert a["anchors"]["count"] == len(built["base_nodes"])


def test_the_hem_follows_the_cover_and_not_the_frame(built):
    """The rope is in the fabric, so it goes round the cover's circle, which
    is outside the dome's -- the same 2d the cover radius carries."""
    edge = attachment.hem(built)
    r = cover.radius(built)
    assert edge["cover_radius_mm"] == pytest.approx(r, abs=0.05)
    assert edge["circumference_mm"] == pytest.approx(2.0 * math.pi * r, abs=0.5)
    assert r > built["meta"]["dome_radius"]


def test_the_doorway_interrupts_the_rope(built):
    """A hem rope run straight across the door would close it."""
    edge = attachment.hem(built)
    door = built.get("doorway")
    if not door:
        assert edge["doorway_gap_mm"] == 0.0
        return
    assert edge["doorway_gap_mm"] > 0.0
    assert edge["rope_length_mm"] < edge["circumference_mm"]
    share = door["bay"]["span_deg"] / 360.0
    assert edge["doorway_gap_mm"] == pytest.approx(
        edge["circumference_mm"] * share, abs=0.5
    )
