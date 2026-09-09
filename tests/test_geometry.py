"""Regression tests for the Star Dome geometry.

Three layers:

1. ``test_invariants`` -- the topology claims from dome/README.md, as
   executable checks. These are what stop a change to the maths from quietly
   breaking the dome.
2. ``test_golden_summary`` -- a small committed snapshot per variant, so a
   change in the numbers shows up as a readable diff in review.
3. ``test_matches_openscad_export`` -- parity with the OpenSCAD producer,
   when its generated files are present. Skipped in a clean clone, because
   exports/ is not in Git.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from stardome import config, export, model, verify

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
OPENSCAD_EXPORT_DIR = ROOT / "exports" / "geometry"

VARIANTS = ["D4", "D6", "D8", "D12"]

# The OpenSCAD exporter labels crossing_types.family_a/family_b from the
# sorted signature while taking t_a/incl_a from the representative crossing's
# own rod order. For the two L/U classes those two orders disagree, so its
# "a" columns mix one rod's family with another rod's angles. This package
# reports every per-rod field in the representative's order instead. Documented
# in docs/architecture.md.
KNOWN_DIVERGENCE = {("crossing_types", "family_a"), ("crossing_types", "family_b")}


@pytest.fixture(scope="module", params=VARIANTS)
def built(request):
    variant = config.load(request.param)
    return model.build(variant)


def test_invariants(built):
    assert verify.check(built) == []


def test_all_bows_are_half_great_circles(built):
    radius = built["meta"]["dome_radius"]
    for rod in built["rods"]:
        assert rod["length_nominal"] == pytest.approx(math.pi * radius, abs=1e-3)


def test_rod_ends_are_on_the_ground(built):
    for node in built["base_nodes"]:
        assert node["z"] == pytest.approx(0.0, abs=1e-9)


def test_five_distinct_crossing_angles(built):
    angles = sorted({t["angle_deg"] for t in built["crossing_types"]})
    assert len(angles) == 5
    assert angles == pytest.approx(
        [37.377368, 41.810315, 63.434949, 70.528779, 79.187683], abs=1e-5
    )


def test_untied_crossings_are_all_the_tetrahedral_angle(built):
    untied = {c["angle_deg"] for c in built["crossings"] if not c["tied"]}
    assert len(untied) == 1
    assert untied.pop() == pytest.approx(math.degrees(math.acos(1 / 3)), abs=1e-5)


def test_crossing_angles_do_not_depend_on_size():
    """Angles are pure topology; only lengths scale with the variant."""
    per_variant = []
    for name in VARIANTS:
        data = model.build(config.load(name))
        per_variant.append(sorted({t["angle_deg"] for t in data["crossing_types"]}))
    for angles in per_variant[1:]:
        assert angles == pytest.approx(per_variant[0], abs=1e-9)


def test_golden_summary(built):
    name = built["meta"]["variant"]
    path = GOLDEN_DIR / f"{name.lower()}.json"
    produced = export.summary(built)
    if not path.exists():  # pragma: no cover - first run only
        pytest.fail(f"missing golden file {path}; run 'make golden' to create it")
    assert produced == path.read_text(encoding="utf-8")


@pytest.mark.parametrize("variant_name", VARIANTS)
def test_matches_openscad_export(variant_name):
    """The Python and OpenSCAD producers must agree field for field."""
    ref_path = OPENSCAD_EXPORT_DIR / f"star_dome_{variant_name.lower()}.json"
    if not ref_path.exists():
        pytest.skip(f"{ref_path} not generated; run the OpenSCAD exporter first")

    reference = json.loads(ref_path.read_text(encoding="utf-8"))
    mine = model.build(
        config.load(variant_name), weave_mode=reference["meta"]["weave_mode"]
    )

    for key, ref_value in reference["meta"].items():
        assert key in mine["meta"], f"meta.{key} missing"
        got = mine["meta"][key]
        if isinstance(ref_value, bool) or isinstance(ref_value, str):
            assert got == ref_value, f"meta.{key}"
        else:
            assert got == pytest.approx(ref_value, abs=1e-5), f"meta.{key}"

    for table in ("rods", "base_nodes", "nodes", "crossings", "crossing_types"):
        assert len(mine[table]) == len(reference[table]), f"{table} length"
        for m, r in zip(mine[table], reference[table]):
            for field, ref_value in r.items():
                if (table, field) in KNOWN_DIVERGENCE:
                    continue
                got = m[field]
                if isinstance(ref_value, list):
                    assert len(got) == len(ref_value), f"{table}.{field}"
                    assert got == pytest.approx(ref_value, abs=1e-5), (
                        f"{table}.{field}"
                    )
                elif isinstance(ref_value, str):
                    # The reference exporter joins list-valued fields with ";"
                    # in JSON as well as CSV; this package keeps them as lists.
                    if isinstance(got, list):
                        got = ";".join(str(x) for x in got)
                    assert got == ref_value, f"{table}.{field}"
                else:
                    assert got == pytest.approx(ref_value, abs=1e-5), (
                        f"{table}.{field}"
                    )
