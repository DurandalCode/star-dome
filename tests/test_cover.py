"""The fabric cover: what it rests on, how much of it there is, how it cuts.

The result worth locking in is the first one: the fabric does not lie on the
nominal sphere. It rides on the outermost rod of the weave, and reading the
nominal figure instead understates every cover in the family.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, cover, model

VARIANTS = sorted(config.load_all())


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    return model.build(config.load(request.param))


def test_the_fabric_rests_outside_the_nominal_sphere(built):
    """Rods weave off their great circles, and the cover goes over the lot."""
    r = cover.radius(built)
    assert r > built["meta"]["dome_radius"]


def test_the_cover_radius_ignores_the_drawing_convention():
    """flat vs layered is how the model is *drawn*; the dome is woven either way.

    This is the bug the ``max_diameter_woven`` field exists to prevent: a
    model built flat used to report a cover 70 mm smaller, which is 5% of D6's
    fabric and 5% of its sail area.
    """
    flat = model.build(config.load("D6"), weave_mode="flat")
    layered = model.build(config.load("D6"), weave_mode="layered")
    assert cover.radius(flat) == cover.radius(layered)
    assert cover.radius(flat) == pytest.approx(3075.0, abs=0.5)


def test_the_dome_fabric_is_a_hemisphere(built):
    """2*pi*R^2, and a factor of two here would be metres of fabric."""
    r = cover.radius(built)
    assert built["cover"]["areas"]["dome_m2"] == pytest.approx(
        2.0 * math.pi * r * r / 1e6, abs=0.02
    )


def test_cutting_the_doorway_out_only_ever_removes_fabric(built):
    areas = built["cover"]["areas"]
    assert areas["total_m2"] <= areas["gross_m2"]
    if built.get("doorway"):
        assert areas["doorway_m2"] > 0


def test_a_skirt_adds_a_cylinder_of_fabric():
    bare = model.build(config.load("D6", skirt_height=0.0))
    tall = model.build(config.load("D6", skirt_height=1000.0))
    r = cover.radius(tall)
    added = tall["cover"]["areas"]["skirt_m2"] - bare["cover"]["areas"]["skirt_m2"]
    assert added == pytest.approx(2.0 * math.pi * r * 1000.0 / 1e6, abs=0.02)


def test_the_gore_always_fits_the_roll_it_is_cut_from(built):
    for roll in (900.0, 1200.0, 1500.0, 2000.0):
        g = cover.gores(built, roll)
        assert g["gore_width_mm"] <= roll
        assert g["count"] >= 3


def test_a_narrower_roll_needs_at_least_as_many_gores(built):
    wide = cover.gores(built, 2000.0)["count"]
    narrow = cover.gores(built, 900.0)["count"]
    assert narrow >= wide


def test_the_gore_is_a_lens_that_closes_at_the_pole(built):
    g = cover.gores(built, 1500.0)
    outline = cover.gore_outline(built, g["count"])
    assert outline[0] == (0.0, 0.0) or outline[0][1] == pytest.approx(0.0, abs=0.5)
    # Widest at the equator, which is the last sample.
    assert outline[-1][1] == pytest.approx(g["gore_width_mm"] / 2.0, abs=1.0)
    assert outline[-1][0] == pytest.approx(g["gore_length_mm"], abs=1.0)


def test_the_mesh_is_closed_and_sits_on_the_cover_radius(built):
    m = cover.mesh(built, meridians=12, parallels=6)
    r = cover.radius(built)
    ground = built["meta"].get("ground_z", 0.0) or 0.0
    assert m["vertex_count"] == len(m["vertices"])
    assert m["face_count"] == len(m["faces"])
    for x, y, z in m["vertices"]:
        assert z >= ground - 1e-6
        if z >= 0.0:
            assert math.sqrt(x * x + y * y + z * z) == pytest.approx(r, abs=0.5)
        else:
            assert math.hypot(x, y) == pytest.approx(r, abs=0.5)


def test_every_mesh_vertex_is_used_by_a_face(built):
    m = cover.mesh(built, meridians=12, parallels=6)
    used = {i for face in m["faces"] for i in face}
    assert used == set(range(m["vertex_count"]))


def test_bigger_domes_need_more_fabric_and_more_seams():
    areas = []
    seams = []
    for name in ("D4", "D6", "D8", "D10"):
        d = model.build(config.load(name))
        areas.append(d["cover"]["areas"]["dome_m2"])
        seams.append(d["cover"]["gores"]["count"])
    assert areas == sorted(areas)
    assert seams == sorted(seams)
