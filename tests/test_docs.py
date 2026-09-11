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

from stardome import config, model, tolerance

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
