"""The door.

The results worth locking in are that the opening is *free* -- it cuts no rod
and invents no joint -- and that its proportions are a property of the shape
rather than of the size, so a door drawn on one variant is the same door on
every other.
"""

from __future__ import annotations

import math

import pytest

from stardome import config, doorway, entrance, model

VARIANTS = sorted(config.load_all())
ALIASED = sorted(n for n, v in config.load_all().items() if v.alias)


@pytest.fixture(scope="module", params=VARIANTS)
def bare(request):
    return model.build(config.load(request.param, skirt_height=0.0))


def test_the_star_leaves_ten_openings_in_two_sizes(bare):
    """Five tall bays and five low ones, alternating -- D5 all the way down."""
    found = doorway.bays(bare)
    assert len(found) == 10
    assert sum(1 for b in found if b["kind"] == "tall") == 5
    assert sum(1 for b in found if b["kind"] == "low") == 5


def test_the_door_bay_is_the_same_shape_at_every_size(bare):
    """Span and head height are fixed fractions of the diameter.

    This is what makes one door drawing serve the whole family: the head sits
    at 0.26287 * D on every variant, exactly, because the shape is
    self-similar and the head is a node.
    """
    diameter = bare["meta"]["dome_diameter"]
    bay = doorway.tall_bays(bare)[0]
    frame = doorway.frame(bare, bay["apex_azimuth_deg"])

    assert frame["apex_point"][2] / diameter == pytest.approx(0.26287, abs=1e-5)
    assert bay["span_deg"] == pytest.approx(34.5, abs=0.5)
    assert bay["open_area_m2"] * 1e6 / diameter ** 2 == pytest.approx(0.042, abs=1e-3)


def test_the_clear_height_is_not_quite_self_similar():
    """Because the rod is not.

    The head node scales exactly; the *free* height under it is that less the
    rod, and a rod is a fixed thickness eating a shrinking share of a growing
    dome. So the clear fraction creeps up with size -- 0.2541 of D on D3 to
    0.2549 on D12 -- and anything claiming one number for all of them is
    quoting the big end.
    """
    fractions = []
    for name in sorted(VARIANTS, key=lambda k: config.load(k).diameter):
        data = model.build(config.load(name, skirt_height=0.0))
        bay = doorway.tall_bays(data)[0]
        fractions.append(bay["clear_height_mm"] / data["meta"]["dome_diameter"])

    assert 0.2540 < min(fractions) < max(fractions) < 0.2550
    # Not monotone in diameter alone -- rod diameter steps too -- but the
    # smallest dome with the thickest relative rod is always the worst.
    assert fractions[0] == min(fractions)


def test_the_door_is_framed_by_joints_that_already_exist(bare):
    """Head on a lashed four-rod node, feet on two base points, no rod cut.

    The alternative -- shortening a bow to widen the hole -- would remove a
    whole structural member, since every bow runs unbroken from base to base.
    """
    bay = doorway.tall_bays(bare)[0]
    frame = doorway.frame(bare, bay["apex_azimuth_deg"])

    apex = next(n for n in bare["nodes"] if n["name"] == frame["apex_node"])
    assert apex["rod_count"] == 4

    base_names = {b["name"] for b in bare["base_nodes"]}
    assert set(frame["feet"]) <= base_names
    assert len(set(frame["jamb_rods"])) == 2
    for rod in frame["jamb_rods"]:
        assert rod in frame["apex_rods"]


def test_the_two_jambs_come_from_the_same_rod_family(bare):
    """Both jambs are G bows, which is why the opening is a symmetric lancet."""
    bay = doorway.tall_bays(bare)[0]
    frame = doorway.frame(bare, bay["apex_azimuth_deg"])
    families = {rod[0] for rod in frame["jamb_rods"]}
    assert families == {"G"}


def test_the_outline_never_dips_below_the_ground(bare):
    """Regression: Bow.t_of wraps to [0, 360), so a base point can read as
    359.999 instead of 0. Sweeping smallest-to-largest then took the long way
    round -- under the ground and over the top -- and did it on some variants
    and not others, purely on rounding."""
    bay = doorway.tall_bays(bare)[0]
    outline = doorway.outline(bare, bay["apex_azimuth_deg"])
    ground = bare["meta"].get("ground_z", 0.0)
    for x, y, z in outline["points"]:
        assert z >= ground - 1e-6


def test_the_outline_runs_ground_to_apex_to_ground(bare):
    bay = doorway.tall_bays(bare)[0]
    frame = doorway.frame(bare, bay["apex_azimuth_deg"])
    outline = doorway.outline(bare, bay["apex_azimuth_deg"], frame_info=frame)
    points = outline["points"]
    ground = bare["meta"].get("ground_z", 0.0)

    assert points[0][2] == pytest.approx(ground, abs=1e-3)
    assert points[-1][2] == pytest.approx(ground, abs=1e-3)
    assert max(p[2] for p in points) == pytest.approx(
        frame["apex_point"][2], abs=1e-3
    )


def test_every_outline_point_sits_on_the_sphere_or_under_it(bare):
    """The arch is rod centreline, so it lies on the sphere; the two skirt
    drops hang straight below the base ring."""
    radius = bare["meta"]["dome_radius"]
    bay = doorway.tall_bays(bare)[0]
    for x, y, z in doorway.outline(bare, bay["apex_azimuth_deg"])["points"]:
        if z < 0.0:
            continue
        assert math.sqrt(x * x + y * y + z * z) == pytest.approx(radius, abs=1e-3)


def test_the_skirt_a_door_needs_shrinks_as_the_dome_grows():
    needed = [
        doorway.skirt_for_template(
            model.build(config.load(name, skirt_height=0.0)), "carry"
        )
        for name in sorted(VARIANTS, key=lambda k: config.load(k).diameter)
    ]
    assert needed == sorted(needed, reverse=True)
    assert needed[-1] == 0.0  # the biggest needs none


def test_a_wider_silhouette_never_needs_less_skirt(bare):
    """walk < walk_wide < carry in width, so the skirt can only go up."""
    needed = [
        doorway.skirt_for_template(bare, name)
        for name in ("walk", "walk_wide", "carry")
    ]
    assert needed == sorted(needed)


def test_each_named_size_admits_the_silhouette_it_claims():
    """S, M, L and XL are builds, not wishes.

    `door` in variants.toml records what the dome actually admits -- with a
    skirt where there is one, and on all fours where there is not. It has to
    be true, with room over the head.
    """
    for name in ALIASED:
        variant = config.load(name)
        data = model.build(variant)
        door = data["doorway"]["door"]
        assert door["fits"], f"{name} ({variant.alias}) door does not fit"
        assert door["template"] == variant.door
        assert door["spare_mm"] >= 50.0, f"{variant.alias} has no headroom to spare"
        assert variant.door in data["doorway"]["admits"]


def test_what_a_door_admits_only_grows_with_the_dome():
    """Bare and unhelped, every larger dome takes everything a smaller one
    takes, and generally more. Nothing about the shape changes with size, so
    a size that lost a silhouette would mean the maths had."""
    previous = set()
    for name in sorted(VARIANTS, key=lambda k: config.load(k).diameter):
        data = model.build(config.load(name, skirt_height=0.0, door=""))
        got = set(doorway.admits(data))
        assert previous <= got, f"{name} lost {previous - got}"
        previous = got


def test_a_bare_six_metre_dome_is_a_crawl_in():
    """The price of leaving M and L bare, stated so it cannot be forgotten.

    D6's opening is 497 mm wide at 1200 mm and 209 mm at 1400. That is not a
    door anyone walks through; it is a door you go through on all fours.
    """
    m = model.build(config.load("M"))
    assert m["meta"]["skirt_height"] == 0.0
    assert m["doorway"]["admits"] == ["crawl"]

    lg = model.build(config.load("L"))
    assert lg["meta"]["skirt_height"] == 0.0
    assert lg["doorway"]["admits"] == ["crawl", "stoop"]


def test_only_the_biggest_domes_take_a_two_and_a_bit_metre_character():
    """An event has people on stilts and in frames; 1.8 m is not the test.

    XL takes the 2.2 m silhouette bare, but only just -- tens of millimetres,
    not hundreds -- so it is worth a test rather than a note.
    """
    xl = model.build(config.load("XL"))
    fitted = doorway.fit(xl, "tall")
    assert fitted["fits"]
    assert 0.0 < fitted["spare_mm"] < 150.0

    for name in ("D3", "D4", "D6", "D8"):
        bare = model.build(config.load(name, skirt_height=0.0, door=""))
        assert not doorway.fit(bare, "tall", skirt_mm=0.0)["fits"]
        assert doorway.skirt_for_template(bare, "tall") > 0.0


def test_admits_agrees_with_fitting_each_silhouette_one_by_one(bare):
    listed = set(doorway.admits(bare))
    checked = {
        name
        for name in entrance.TEMPLATES
        if doorway.fit(bare, name, skirt_mm=0.0)["fits"]
    }
    assert listed == checked


def test_the_short_names_and_the_d_names_are_the_same_dome():
    for name in ALIASED:
        variant = config.load(name)
        assert config.load(variant.alias) == variant
        assert config.resolve(variant.alias) == name


def test_an_unknown_name_names_the_aliases_it_knows():
    with pytest.raises(KeyError) as caught:
        config.load("XXL")
    assert "XL" in str(caught.value)


def test_the_doorway_is_only_serialised_when_the_variant_asks_for_one():
    with_door = model.build(config.load("M"))
    without = model.build(config.load("M", door=""))
    assert "doorway" in with_door
    assert "doorway" not in without


def test_the_clearance_allowance_only_ever_shrinks_the_opening(bare):
    plain = doorway.tall_bays(bare)[0]
    padded = doorway.tall_bays(bare, clearance_mm=25.0)[0]
    assert padded["clear_height_mm"] < plain["clear_height_mm"]
    assert padded["open_area_m2"] < plain["open_area_m2"]


def test_the_envelope_and_the_head_node_disagree_by_one_rod(bare):
    """The envelope measures to the rod surface, the node is a centreline.

    Worth pinning because the two numbers look like a contradiction in the
    output and are not: 0.2549 * D of free height under a head at 0.2629 * D.
    """
    bay = doorway.tall_bays(bare)[0]
    frame = doorway.frame(bare, bay["apex_azimuth_deg"])
    gap = frame["apex_point"][2] - bay["clear_height_mm"]
    assert gap > bare["meta"]["rod_diameter"] / 2.0
    assert gap == pytest.approx(0.008 * bare["meta"]["dome_diameter"], rel=0.25)


def test_five_doors_fit_and_they_are_the_five_tall_bays():
    data = model.build(config.load("XL"))
    door = data["doorway"]["door"]
    assert door["place_count"] == 5

    tall = {round(b["apex_azimuth_deg"]) for b in doorway.tall_bays(data)}
    placed = {round(p["centre_azimuth_deg"]) for p in door["places"]}
    for azimuth in placed:
        assert min(abs(azimuth - t) for t in tall) <= 5


def test_entrance_and_doorway_agree_on_the_free_height(bare):
    """Two modules, one number: doorway must not re-derive the envelope."""
    env = entrance.analyse(bare)
    bay = doorway.tall_bays(bare)[0]
    assert bay["clear_height_mm"] == pytest.approx(
        env["free_height_max_mm"], abs=0.1
    )


def test_the_jambs_are_end_pieces_so_cutting_them_severs_nothing(bare):
    """The reason cutting the door open is worth considering at all.

    Every bow is divided by its crossings into pieces that each end at a
    lashed node. The doorway's own jambs are the pieces at the ends of their
    bows, so removing them shortens two bows -- each then starts at the head
    node instead of at a base point -- rather than breaking any bow in two.
    """
    cuts = doorway.jamb_cut(bare)
    cost = doorway.cut_pieces(bare, cuts)

    assert set(cuts) == set(doorway.tall_bays(bare) and
                            doorway.frame(bare, doorway.tall_bays(bare)[0]
                                          ["apex_azimuth_deg"])["jamb_rods"])
    assert cost["severs_nothing"]
    assert cost["severed_bows"] == []
    assert len(cost["end_pieces"]) == 2


def test_cutting_the_jambs_costs_the_same_fraction_at_every_size(bare):
    """Two fifths of a bow out of fifteen bows: 2.67% of the rod, always.

    Each G bow is exactly five equal pieces, because its crossings fall on
    fifths -- so this is a property of the topology, not of the diameter.
    """
    cost = doorway.cut_pieces(bare, doorway.jamb_cut(bare))
    assert cost["rod_removed_fraction"] == pytest.approx(2.0 / 75.0, abs=1e-3)


def test_cutting_the_jambs_never_makes_the_opening_smaller(bare):
    plain = doorway.tall_bays(bare)[0]["clear_height_mm"]
    opened = doorway.with_cut(bare, doorway.jamb_cut(bare))

    assert opened["clear_height_mm"] >= plain
    assert set(doorway.admits(bare)) <= set(opened["admits"])


def test_cutting_the_jambs_turns_L_from_a_duck_into_a_walk_in():
    """The result that makes the cut worth doing.

    Bare L admits a stoop and nothing more. With the two jamb pieces out it
    takes someone carrying something, through an opening 1.68 m wide at
    shoulder height -- and no bow has been severed to get it.
    """
    lg = model.build(config.load("L"))
    assert doorway.admits(lg) == ["crawl", "stoop"]

    opened = doorway.with_cut(lg, doorway.jamb_cut(lg))
    assert "carry" in opened["admits"]
    assert opened["widths_mm"]["1800"] > 1500.0
    assert opened["cost"]["severs_nothing"]


def test_a_middle_piece_is_reported_as_severing_its_bow():
    """The distinction the cost model exists to make.

    Going further than the jambs means taking pieces out of the middle of a
    bow, and a bow with its middle gone is two bows.
    """
    m = model.build(config.load("M"))
    cost = doorway.cut_pieces(m, {"L1": [(37.8, 60.0)]})
    assert not cost["severs_nothing"]
    assert cost["severed_bows"] == ["L1"]
    assert cost["end_pieces"] == []


def test_an_envelope_with_a_piece_removed_is_never_lower_than_without(bare):
    """Removing rod can only open the dome up, never close it."""
    plain = entrance.door_envelope(bare)["envelope_mm"]
    cut = entrance.door_envelope(bare, removed=doorway.jamb_cut(bare))["envelope_mm"]
    assert all(c >= p - 1e-6 for p, c in zip(plain, cut))
