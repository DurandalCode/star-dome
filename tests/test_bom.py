"""What one dome is made of, counted once.

The dome was thoroughly measured as a shape long before anybody added it up as
a quantity. This guards the adding up: that the list counts every part the
schedule asks for, that the plastic is read off the built meshes rather than
kept in the source where it would drift, and that a dome nobody has built the
parts for says so instead of reporting zero as though it meant none.
"""

from __future__ import annotations

import struct

import pytest

from stardome import bom, config, connectors, model

VARIANTS = ["D4", "D6", "D10"]


@pytest.fixture(scope="module")
def built():
    return {
        name: model.build(config.load(name), weave_mode="woven")
        for name in VARIANTS
    }


def _stl(path, triangles):
    """A little binary STL, written the way FreeCAD writes them."""
    with open(path, "wb") as handle:
        handle.write(b"x" * 80)
        handle.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            handle.write(struct.pack("<3f", 0.0, 0.0, 0.0))
            for point in tri:
                handle.write(struct.pack("<3f", *point))
            handle.write(struct.pack("<H", 0))


def _unit_cube(path):
    """A closed 1 mm cube: twelve triangles, volume 1 mm3."""
    v = [
        (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
        (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
    ]
    faces = [
        (0, 2, 1), (0, 3, 2),  # bottom
        (4, 5, 6), (4, 6, 7),  # top
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]
    _stl(path, [(v[a], v[b], v[c]) for a, b, c in faces])


# --- the mesh arithmetic ----------------------------------------------------


def test_a_closed_mesh_gives_its_own_volume(tmp_path):
    """Summed signed tetrahedra, which is exact for a closed surface."""
    path = tmp_path / "CUBE-1_Body.stl"
    _unit_cube(path)
    assert bom.stl_volume_mm3(str(path)) == pytest.approx(1.0, abs=1e-6)


def test_reference_geometry_is_not_a_part(tmp_path):
    """A generator exports the rods it drew a part around. They are drawings,
    and counting them would roughly double the plastic."""
    _unit_cube(tmp_path / "PART-1_Body.stl")
    _unit_cube(tmp_path / "PART-1_ref-Rod1.stl")
    _unit_cube(tmp_path / "PART-1_ref-Assembly.stl")
    found = bom.measured(str(tmp_path))
    assert list(found) == ["PART-1"]
    assert list(found["PART-1"]) == ["Body"]


def test_a_directory_with_nothing_in_it_is_an_answer(tmp_path):
    assert bom.measured(str(tmp_path)) == {}
    assert bom.measured(str(tmp_path / "not-here")) == {}


# --- the list ---------------------------------------------------------------


def test_every_part_the_schedule_asks_for_is_on_the_list(built):
    for name, data in built.items():
        sched = connectors.schedule(data)
        listed = bom.printed(sched, {})
        assert listed["part_types"] == len(sched["parts"]), name
        assert listed["parts"] == sched["totals"]["parts_per_dome"], name


def test_an_unbuilt_dome_says_so_rather_than_reporting_none(built):
    listed = bom.printed(connectors.schedule(built["D6"]), {})
    assert listed["cm3"] == 0.0
    assert listed["prints"] == 0
    assert listed["all_measured"] is False
    assert all(row["measured"] is False for row in listed["rows"])


def test_the_plastic_adds_up_and_the_shares_close(built):
    """Made-up volumes, so the arithmetic is checked and not the parts."""
    sched = connectors.schedule(built["D6"])
    volumes = {
        part["id"]: {"A": 10.0, "B": 5.0}
        for part in sched["parts"]
        if part.get("generator")
    }
    listed = bom.printed(sched, volumes)
    generated = [r for r in listed["rows"] if r["measured"]]

    assert listed["cm3"] == pytest.approx(
        sum(15.0 * r["count"] for r in generated)
    )
    assert listed["prints"] == sum(2 * r["count"] for r in generated)
    assert sum(r["share"] for r in listed["rows"]) == pytest.approx(1.0, abs=1e-3)
    # Biggest first: a list nobody can sort is a list nobody reads.
    assert [r["cm3_total"] for r in listed["rows"]] == sorted(
        (r["cm3_total"] for r in listed["rows"]), reverse=True
    )


def test_hardware_carries_no_plastic_and_is_still_counted(built):
    sched = connectors.schedule(built["D6"])
    listed = bom.printed(sched, {})
    stake = next(r for r in listed["rows"] if r["id"] == "STAKE-BASE")
    assert stake["state"] == "hardware"
    assert stake["cm3_total"] == 0.0
    assert stake["count"] == 10
    assert stake["count"] in [r["count"] for r in listed["rows"]]


# --- the materials ----------------------------------------------------------


def test_the_materials_come_from_the_modules_that_own_them(built):
    """Nothing here is recomputed; a wrong number would be wrong twice."""
    for name, data in built.items():
        m = bom.materials(data, connectors.schedule(data))
        assert m["rod_m"] == pytest.approx(
            data["meta"]["total_rod_length"] / 1000.0, abs=0.01
        ), name
        assert m["fabric_m2"] == data["cover"]["areas"]["total_m2"], name
        assert m["webbing_m"] == data["attachment"]["webbing_total_m"], name
        assert m["anchors"] == len(data["base_nodes"]), name


def test_a_bow_is_cut_into_as_many_sections_as_it_has_splices_plus_one(built):
    for name, data in built.items():
        sched = connectors.schedule(data)
        m = bom.materials(data, sched)
        splices = next(
            (p for p in sched["parts"] if p["kind"] == "rod_splice"), None
        )
        if splices is None:
            continue
        joints_per_bow = splices["count"] / data["meta"]["rod_count"]
        assert m["sections"] / m["bows"] == pytest.approx(joints_per_bow + 1), name


def test_only_a_skirted_dome_lists_a_skirt(built):
    assert "skirt" in bom.materials(built["D4"], connectors.schedule(built["D4"]))
    assert "skirt" not in bom.materials(built["D6"], connectors.schedule(built["D6"]))
    skirt = bom.materials(built["D4"], connectors.schedule(built["D4"]))["skirt"]
    assert skirt["posts_m"] == pytest.approx(
        built["D4"]["skirt"]["post_total_length"] / 1000.0, abs=0.01
    )


def test_the_bolt_follows_the_rod(built):
    """Decision 0013's rule, restated here because kit.py only imports inside
    FreeCAD and this has to answer without it."""
    assert bom._fastener_for(8.0) == "M4"
    assert bom._fastener_for(10.0) == "M5"
    assert bom._fastener_for(12.0) == "M6"
    for name, data in built.items():
        m = bom.materials(data, connectors.schedule(data))
        assert m["fastener"] == bom._fastener_for(data["meta"]["rod_diameter"])


def test_it_formats_without_the_parts_being_built(built, tmp_path):
    text = bom.format_analysis(
        built["D6"], connectors.schedule(built["D6"]), str(tmp_path)
    )
    assert "bill of materials" in text
    assert "not built" in text
    assert "run `make clamps`" in text
