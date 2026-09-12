"""Numbers stated in prose must still be the numbers the model computes.

Every other test in this suite checks the maths. This one checks the writing,
because that is where this project has actually drifted.

Three documents spent two days telling readers that D6 wanted 760 mm of skirt
and could only be crawled into. Both had been true, and both stopped being true
the moment the door moved to a portal in a low bay. Nothing failed: the maths
was right, the tests were green, and the only thing wrong was every sentence a
person would actually read.

So the load-bearing numbers get a registry. If one changes, the test names the
document that has to change with it. If a sentence holding one is deleted or
reworded past recognition, the test fails too -- which is correct, because the
registry is the list of claims someone promised to keep true.

Adding a number here is a commitment. Do not register every figure in the
docs; register the ones a reader would make a decision on.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from stardome import bom, config, connectors, model, span, tolerance

ROOT = pathlib.Path(__file__).resolve().parent.parent

NAMED = ["D4", "D6", "D8", "D10"]


@pytest.fixture(scope="module")
def built():
    return {name: model.build(config.load(name)) for name in NAMED}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def clear_opening(data: dict) -> float:
    return data["doorway"]["bay"]["clear_height_mm"]


# --- the size table, parsed rather than eyeballed ---------------------------


def _readme_size_rows() -> list:
    """The rows of README's `## Sizes` table, as dicts."""
    text = read("README.md")
    section = text.split("## Sizes", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0].startswith("**"):
            continue
        rows.append(
            {
                "alias": cells[0].strip("*"),
                "variant": cells[1],
                "skirt": cells[2],
                "overall": cells[3],
                "clear": cells[4],
            }
        )
    return rows


def test_readme_lists_every_named_size():
    rows = _readme_size_rows()
    assert [r["alias"] for r in rows] == ["S", "M", "L", "XL"]
    assert [r["variant"] for r in rows] == NAMED


def test_readme_aliases_match_the_config():
    for row in _readme_size_rows():
        variant = config.load(row["variant"])
        assert variant.alias == row["alias"]


def test_readme_skirts_match_the_config():
    """The drift that started this file: a document offering a skirt to a
    variant that does not have one."""
    for row in _readme_size_rows():
        variant = config.load(row["variant"])
        stated = row["skirt"]
        if variant.skirt_height == 0:
            assert stated == "none", (
                f"README gives {row['variant']} a skirt of {stated!r}, "
                f"but configs/variants.toml has none"
            )
        else:
            assert f"{variant.skirt_height:.0f} mm" in stated


def test_readme_clear_openings_match_the_model(built):
    for row in _readme_size_rows():
        wanted = f"{clear_opening(built[row['variant']]):.0f} mm"
        assert wanted in row["clear"], (
            f"README says the {row['alias']} opening is {row['clear']!r}; "
            f"the model says {wanted}"
        )


def test_readme_overall_heights_match_the_config():
    for row in _readme_size_rows():
        variant = config.load(row["variant"])
        wanted = f"{variant.overall_height / 1000.0:.2f} m"
        assert wanted in row["overall"]


# --- what each size admits --------------------------------------------------


def test_only_one_built_size_turns_anything_away(built):
    """README and the roadmap both say M is the only one that refuses a
    silhouette. If a change makes that false -- or makes a second size refuse
    one -- both documents are wrong and say so here first."""
    everything = set()
    for data in built.values():
        everything |= set(data["doorway"]["admits"])

    partial = [
        name
        for name, data in built.items()
        if set(data["doorway"]["admits"]) != everything
    ]
    assert partial == ["D6"], (
        f"sizes that refuse a silhouette: {partial}. README and "
        f"docs/roadmap.md both state that only M does."
    )


def test_m_still_refuses_the_wide_and_the_tall_silhouette(built):
    admits = set(built["D6"]["doorway"]["admits"])
    assert "carry" in admits
    assert "walk_wide" not in admits
    assert "tall" not in admits


def test_every_named_size_walks_in(built):
    """The portal's whole point. README states it in one sentence."""
    for name, data in built.items():
        assert "walk" in data["doorway"]["admits"], f"{name} does not walk in"
    assert "Every one of them walks in" in read("README.md")


# --- the registry -----------------------------------------------------------


def _claims(built) -> list:
    """``(document, what it must contain, why)``.

    The expected text is built from the model, so the assertion is that the
    document still quotes what the model now says.
    """
    return [
        (
            "README.md",
            f"{clear_opening(built['D6']):.0f} mm",
            "M's clear opening",
        ),
        (
            "docs/roadmap.md",
            f"{clear_opening(built['D6']):.0f} мм",
            "M's clear opening, in the roadmap's size table",
        ),
        (
            "docs/roadmap.md",
            f"{clear_opening(built['D8']):.0f} мм",
            "L's clear opening",
        ),
        (
            "docs/tolerance.md",
            f"{tolerance.held_spans(built['D6'])['G']:.0f} mm on M",
            "the span the tolerance is derived from -- family G's fifths",
        ),
        (
            "docs/tolerance.md",
            f"{tolerance.spread_for_curvature(tolerance.DEFAULT_CURVATURE_BUDGET, tolerance.held_spans(built['D6'])['G'], built['D6']['meta']['dome_radius']):.0f} mm of spread",
            "what a 10% curvature budget allows on M",
        ),
    ]


def test_registered_claims_still_hold(built):
    for document, wanted, why in _claims(built):
        text = read(document)
        assert wanted in text, (
            f"{document} no longer contains {wanted!r} ({why}). Either the "
            f"document drifted from the model, or the sentence holding this "
            f"number was rewritten -- update the document, then this registry."
        )


# --- documents do not contradict each other ---------------------------------


def test_readme_and_roadmap_agree_on_the_openings(built):
    """Two size tables in two languages, and they have disagreed before."""
    roadmap = read("docs/roadmap.md")
    for name in NAMED:
        wanted = f"{clear_opening(built[name]):.0f}"
        assert wanted in roadmap, (
            f"docs/roadmap.md does not quote {name}'s opening of {wanted} mm"
        )


def test_superseded_documents_say_so():
    """entrance.md and interior.md answer the rectangle question, which is not
    the door the project built. Both carry a pointer to doorway.md; without it
    a reader takes their conclusions as current, which is exactly what
    happened."""
    for name in ("docs/entrance.md", "docs/interior.md"):
        text = read(name)
        assert "doorway.md" in text, f"{name} does not point at the real door"


def test_no_document_calls_a_bare_variant_the_reference_prototype():
    """The specific sentence that was wrong for two days, in both languages."""
    for name in ("docs/interior.md", "docs/entrance.md", "docs/roadmap.md"):
        text = read(name).lower()
        for phrase in (
            "is probably what the reference prototype should be",
            "и есть то, чем должен быть эталонный прототип",
        ):
            assert phrase not in text, f"{name} still recommends a skirt for M"


# --- links ------------------------------------------------------------------


def test_every_relative_link_resolves():
    pattern = re.compile(r"\[[^\]]*\]\((?!https?:)([^)#][^)]*)\)")
    broken = []
    documents = list((ROOT / "docs").rglob("*.md")) + [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
    ]
    for path in documents:
        for match in pattern.finditer(path.read_text(encoding="utf-8")):
            target = match.group(1).split("#")[0]
            if target and not (path.parent / target).exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    assert not broken, "broken relative links: " + ", ".join(broken)


# --- the span, and the scaling law on it ------------------------------------
#
# docs/span.md is the one document here that states a number nobody can check
# by looking at the dome: a ratio between two variants. Registering these is
# what stops the prose keeping a figure the maths has moved on from.


ALL_VARIANTS = ["D3", "D4", "D6", "D8", "D10", "D12"]


@pytest.fixture(scope="module")
def every_variant():
    return {name: model.build(config.load(name)) for name in ALL_VARIANTS}


def _span_table_rows(heading: str) -> list:
    """The rows of a pipe table in docs/span.md, by the heading above it."""
    text = read("docs/span.md").split(heading, 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def test_span_doc_lists_every_variant_with_both_readings(every_variant):
    """The table of worst spans, both readings, one row per variant."""
    rows = [
        r for r in _span_table_rows("## The span is a fraction of the radius")
        if r[0] in ALL_VARIANTS
    ]
    assert [r[0] for r in rows] == ALL_VARIANTS, "docs/span.md size table"

    for name, lashed, contact in rows:
        data = every_variant[name]
        assert lashed == f"{span.spans(data, 'lashed')['worst']['length_mm']:.0f} mm", name
        assert contact == f"{span.spans(data, 'contact')['worst']['length_mm']:.0f} mm", name


def test_span_doc_states_the_fraction_the_model_computes(every_variant):
    stated = "1.0472 R"
    got = span.spans(every_variant["D6"], "lashed")["fraction_of_radius"]
    assert stated == f"{got:.4f} R"
    assert stated in read("docs/span.md")


def test_span_doc_prices_the_thirty_clamps(every_variant):
    """5/3 in span and 2.78x in rod diameter: the only number on the open
    question of whether the free crossings get a part."""
    value = span.clamp_value(every_variant["D6"])
    text = read("docs/span.md")
    assert f"{value['rod_diameter_ratio']:.2f}\u00d7 in rod diameter" in text
    assert f"**{value['lashed']['length_mm']:.0f} mm against " \
           f"{value['contact']['length_mm']:.0f} mm**" in text


def test_span_doc_scaling_table_matches_the_model(every_variant):
    ref = span.reference(every_variant[span.REFERENCE_VARIANT], "lashed")
    rows = [
        r for r in _span_table_rows("## What that does to the rod")
        if r[0] in ("D8", "D10", "D12")
    ]
    assert [r[0] for r in rows] == ["D8", "D10", "D12"]

    for name, configured, similar, sag, parity in rows:
        a = span.analyse(every_variant[name], ref)
        assert configured == f"{a['rod']['configured_mm']:.0f} mm", name
        assert similar == f"{a['rod']['similar_mm']:.1f} mm", name
        case = a["cases"]["self_weight"]
        assert sag == f"{case['sag_ratio']:.1f}\u00d7", name
        assert parity == f"{case['parity_rod_mm']:.1f} mm", name


def test_span_doc_ceiling_table_matches_the_model(every_variant):
    """The row that decides milestone 7: where the family runs out."""
    ref = span.reference(every_variant[span.REFERENCE_VARIANT], "lashed")
    rows = _span_table_rows("## Two constraints, pulling opposite ways")
    header = next(r for r in rows if r[0] == "allowable strain")
    assert header[1:] == [f"{e * 100:.1f}%" for e in span.STRAIN_SAMPLES]

    self_weight = next(r for r in rows if "self-weight" in r[0])
    for cell, strain in zip(self_weight[1:], span.STRAIN_SAMPLES):
        top = span.ceiling("self_weight", strain, ref)
        assert f"{top['diameter_mm'] / 1000.0:.1f} m" in cell, strain


def test_span_doc_quotes_the_reference_working_strain(every_variant):
    ref = span.reference(every_variant["D6"], "lashed")
    assert f"works its rod at {ref['bend_strain'] * 100:.3f}%" in read("docs/span.md")


# --- the door a big dome already has ----------------------------------------
#
# docs/doorway.md states the diameter at which the uncut tall bay starts
# admitting each silhouette. Those are the numbers that say a cut is optional
# at the XL end, so they get pinned from both sides: admitted at the stated
# diameter, and not admitted just under it.


THRESHOLDS = {
    "walk": 8063,
    "walk_wide": 8626,
    "carry": 8656,
    "tall": 9848,
}


def _admits_uncut(diameter: float) -> set:
    variant = config.load("D10", diameter=float(diameter), door_cut="none")
    return set(model.build(variant)["doorway"]["admits"])


def test_doorway_doc_thresholds_are_where_it_says(built):
    text = read("docs/doorway.md")
    for template, diameter in THRESHOLDS.items():
        assert f"| `{template}`" in text or f"| `{template}` " in text, template
        assert f"D {diameter} mm" in text, f"{template} {diameter}"
        assert template in _admits_uncut(diameter), template
        assert template not in _admits_uncut(diameter - 50), (
            f"{template} still gets in 50 mm under the stated {diameter}"
        )


def test_doorway_doc_compares_the_xl_bay_against_its_portal():
    """The table that says what the cut is still worth on D10."""
    text = read("docs/doorway.md")
    rows = {}
    for level in ("none", "portal"):
        data = model.build(config.load("D10", door_cut=level))
        bay = data["doorway"]["bay"]
        rows[level] = {
            "clear": f"{bay['clear_height_mm']:.0f} mm",
            "area": f"{bay['open_area_m2']:.2f} m\u00b2",
            "width": f"{data['doorway']['in_bay']['widths_mm']['1800']:.0f} mm"
            if "1800" in data["doorway"]["in_bay"]["widths_mm"]
            else None,
        }
    for level in ("none", "portal"):
        assert rows[level]["clear"] in text, (level, rows[level]["clear"])
        assert rows[level]["area"] in text, (level, rows[level]["area"])


# --- what one dome is made of -----------------------------------------------
#
# docs/bom.md states two kinds of number. The counts come from the schedule and
# are checkable anywhere; the plastic is read off built meshes, so those
# assertions skip themselves when the parts have not been generated -- the same
# bargain the OpenSCAD parity test makes.


@pytest.fixture(scope="module")
def woven_m():
    return model.build(config.load("M"), weave_mode="woven")


def test_bom_doc_counts_parts_and_prints(woven_m):
    text = read("docs/bom.md")
    sched = connectors.schedule(woven_m)
    assert f"{sched['totals']['parts_per_dome']} parts is " in text

    volumes = bom.measured(bom.DEFAULT_PARTS_DIR)
    if not volumes:
        pytest.skip("connectors not built; run `make clamps` for the plastic")
    listed = bom.printed(sched, volumes)
    assert f"{listed['parts']} parts is {listed['prints']} prints" in text


def test_bom_doc_sections_are_the_splices_plus_the_bows():
    """The number that says dividing a bow by the transport length is wrong."""
    data = model.build(config.load("XL"), weave_mode="woven")
    m = bom.materials(data, connectors.schedule(data))
    text = read("docs/bom.md")
    assert f"that is {m['sections']} sections" in text
    # And the wrong answer it is contrasted with.
    import math

    naive = m["bows"] * math.ceil(m["bow_length_mm"] / m["section_length_mm"])
    assert f"not the {naive} the division gives" in text
    assert naive != m["sections"]


def test_bom_doc_base_hub_share(woven_m):
    volumes = bom.measured(bom.DEFAULT_PARTS_DIR)
    if not volumes:
        pytest.skip("connectors not built; run `make clamps` for the plastic")
    listed = bom.printed(connectors.schedule(woven_m), volumes)
    hubs = [r for r in listed["rows"] if r["id"].startswith("BASE")]
    if not all(r["measured"] for r in hubs):
        pytest.skip("base hubs not built for this rod size")

    share = sum(r["cm3_total"] for r in hubs)
    text = read("docs/bom.md")
    assert f"{share:.0f} cm\u00b3 of {listed['cm3']:.0f}" in text
    assert f"{share / listed['cm3'] * 100:.0f}%" in text
