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


def test_the_cover_radius_is_the_weave_and_not_a_drawing_convention():
    """How the model is *drawn* must not change how much fabric gets cut.

    Two conventions were wrong here in turn. Reading a flat model put the
    fabric on the nominal sphere, which is 15 mm under the outermost rod.
    Reading a layered one put it on r = 3075, which is 55 mm over: `layered`
    gives each of the 15 bows its own shell and spreads them across fourteen
    rod diameters, and the dome is built on a weave that spans three.

    The right figure is a closed form. A four-rod stack is three diameters
    tall, so the outermost rod sits 1.5 diameters off the nominal sphere and
    the fabric clears its surface half a diameter further: r + 2d.
    """
    rod = config.load("D6").rod_diameter
    want = 3000.0 + 2.0 * rod

    built = {
        mode: model.build(config.load("D6"), weave_mode=mode)
        for mode in ("flat", "layered", "woven")
    }
    radii = {mode: cover.radius(d) for mode, d in built.items()}
    assert len(set(radii.values())) == 1, radii
    assert radii["flat"] == pytest.approx(want, abs=0.5)

    # And it agrees with the route the weave solver actually finds, which is
    # what `verify` bounds at 1.5 rod diameters.
    band = max(
        abs(v)
        for r in model.build(
            config.load("D6"), weave_mode="woven", include_polylines=True
        )["rods"]
        for _t, v in r.get("radial_profile", [])
    )
    assert band == pytest.approx(1.5 * rod, abs=1e-6)


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
