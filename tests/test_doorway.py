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
        assert door["spare_mm"] >= 0.0, f"{variant.alias} has no headroom at all"
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


def test_a_bare_uncut_six_metre_dome_is_a_crawl_in():
    """The price of leaving M and L bare, before anything is cut.

    Untouched, D6's opening is 497 mm wide at 1200 mm and 209 mm at 1400 --
    not a door anyone walks through. D8 manages a duck and no more. This is
    the baseline the cut is measured against.
    """
    m = model.build(config.load("M", door_cut=False))
    assert m["meta"]["skirt_height"] == 0.0
    assert m["doorway"]["admits"] == ["crawl"]

    lg = model.build(config.load("L", door_cut=False))
    assert lg["meta"]["skirt_height"] == 0.0
    assert lg["doorway"]["admits"] == ["crawl", "stoop"]


def test_m_and_l_ship_with_a_portal_door():
    """Both are bare, and both get their door from a low bay rather than a
    tall one.

    The portal is the better trade by a distance: it has a lintel instead of a
    pointed head, it stands higher for it, and it costs the same 2.8% of rod
    while severing nothing and stranding nothing. M goes from crawling to
    walking in with something in your hands.
    """
    for name, uncut_best in (("M", "crawl"), ("L", "stoop")):
        data = model.build(config.load(name))
        door = data["doorway"]
        assert door["cut"] is not None, f"{name} should ship cut"
        assert door["cut"]["level"] == "portal"
        assert door["cut"]["cost"]["severs_nothing"]
        assert not door["cut"]["cost"]["nodes_with_nothing_through"]
        assert door["frame"] is None
        assert "carry" in door["admits"]

        uncut = model.build(config.load(name, door_cut="none"))
        assert uncut["doorway"]["admits"][-1] == uncut_best
        assert "carry" not in uncut["doorway"]["admits"]


def test_a_portal_stands_higher_than_a_lancet_for_the_same_rod(bare):
    """Why the portal wins.

    Both cuts cost about 2.8% of the rod and neither severs anything. The
    lancet's head is a node at 0.2629 of D; the portal's lintel clears about
    0.3009. Same price, a tenth more height, and a level top to hang a door
    from rather than a point.
    """
    lancet = doorway.place(bare, cut="jambs")
    portal = doorway.place(bare, cut="portal")

    assert portal["in_bay"]["clear_height_mm"] > lancet["in_bay"]["clear_height_mm"]
    assert portal["cut"]["cost"]["severs_nothing"]
    assert (
        abs(
            portal["cut"]["cost"]["rod_removed_fraction"]
            - lancet["cut"]["cost"]["rod_removed_fraction"]
        )
        < 0.005
    )


def test_the_portal_head_is_a_fixed_fraction_of_the_diameter(bare):
    """0.3009 of D, the same at every size -- the shape is self-similar."""
    portal = doorway.place(bare, cut="portal")
    fraction = (
        portal["in_bay"]["clear_height_mm"] / bare["meta"]["dome_diameter"]
    )
    assert fraction == pytest.approx(0.3027, abs=0.002)


def test_a_bare_six_metre_dome_only_just_takes_a_loaded_person():
    """M's portal clears 1816 mm and `carry` wants 1800.

    Sixteen millimetres is not a margin, it is an accident, and it is the kind
    of number that quietly stops being true once a cover is hemmed round the
    opening. Worth a test so it cannot be forgotten.
    """
    m = model.build(config.load("M"))
    assert m["doorway"]["in_bay"]["clear_height_mm"] == pytest.approx(1816, abs=5)
    assert m["doorway"]["door"]["fits"]
    assert m["doorway"]["door"]["spare_mm"] < 50.0


def test_the_head_cut_strands_the_head_node_and_says_so():
    """The cost that is not measured in metres of rod.

    At the head level all four bows terminate at the head node, so nothing
    runs through it and no continuous member holds it. That wants a lintel,
    and the model has to say so rather than leave it to be noticed. This is
    why neither shipped size uses that level.
    """
    for name in ("M", "L"):
        data = model.build(config.load(name, door_cut="head"))
        cost = data["doorway"]["cut"]["cost"]
        assert not cost["severs_nothing"]
        assert cost["severed_bows"] == ["L1", "L5"]
        assert cost["nodes_with_nothing_through"] == ["N20"]


def test_each_cut_level_opens_more_than_the_one_below(bare):
    """none < jambs < head, measured in the door's own bay and nowhere else."""
    heights = []
    for level in ("none", "jambs", "head"):
        placed = doorway.place(bare, cut=level)
        heights.append(placed["in_bay"]["clear_height_mm"])
    assert heights[0] <= heights[1] <= heights[2]
    assert heights[2] > heights[0]


def test_the_jamb_level_leaves_the_head_node_carrying_something(bare):
    """The line between the two levels, in one assertion."""
    jambs = doorway.place(bare, cut="jambs")["cut"]["cost"]
    head = doorway.place(bare, cut="head")["cut"]["cost"]
    assert jambs["nodes_with_nothing_through"] == []
    assert head["nodes_with_nothing_through"] != []


def test_the_cut_reaches_the_rods_that_draw_it():
    """A consumer must be able to draw the cut without re-deriving it."""
    data = model.build(config.load("M"))
    spans = data["doorway"]["cut"]["spans"]
    carried = {
        rod["name"]: rod["cut_spans_deg"]
        for rod in data["rods"]
        if "cut_spans_deg" in rod
    }
    assert carried == spans

    untouched = model.build(config.load("XL", door_cut="none"))
    assert untouched["doorway"]["cut"] is None
    assert not any("cut_spans_deg" in rod for rod in untouched["rods"])


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
        config.load("XXXL")
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
    """Uncut, the five tall bays are the five places a door goes.

    Cutting one open adds a sixth, which is the point of cutting -- so this
    has to ask an untouched dome.
    """
    data = model.build(config.load("XL", door_cut="none"))
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


def test_the_skirt_bay_under_a_door_is_actually_open():
    """Taking the diagonals out of a bay does not make a doorway.

    Both rings still ran straight across it -- one along the ground to trip
    on, one at the top of the skirt at head height. Neither is a hole, and the
    drawing looked fine either way, which is how it survived a review.
    """
    data = model.build(config.load("S"))
    skirt = data["skirt"]
    bay = skirt["open_bays"][0]

    assert not [b for b in skirt["braces"] if b["bay"] == bay]
    assert not [seg for seg in skirt["top_ring"] if seg["bay"] == bay]
    assert not [seg for seg in skirt["bottom_ring"] if seg["bay"] == bay]
    assert len(skirt["top_ring"]) == skirt["bay_count"] - 1
    assert len(skirt["bottom_ring"]) == skirt["bay_count"] - 1


def test_a_header_carries_the_hoop_force_over_the_doorway():
    """An open bay leaves the top ring an open arc, which carries no hoop
    tension at all. The header takes it round: post head, up the U bow,
    across, and down the other side."""
    data = model.build(config.load("S"))
    skirt = data["skirt"]
    header = skirt["header"]

    assert header["bay"] == skirt["open_bays"][0]
    assert len(set(header["rods"])) == 2
    assert all(rod.startswith("U") for rod in header["rods"])
    # Level, and clear of everything the opening admits -- not merely of the
    # silhouette it is nominally sized for. S is sized for someone carrying
    # something at 1800 mm and passes a 2.2 m character, and a header on the
    # nominal figure would have taken that back.
    assert header["a"][2] == pytest.approx(header["b"][2], abs=1.0)
    assert header["height_above_ground"] > 2200.0
    assert header["clears_mm"] == 2200.0
    # But not above the dome's own opening, where it would carry nothing.
    assert (
        header["height_above_ground"]
        <= data["doorway"]["in_bay"]["clear_height_mm"] + skirt["height"] + 1.0
    )


def test_a_dome_with_no_door_keeps_its_rings_closed():
    """D3 has no doorway worked out, so nothing is taken out of its skirt."""
    d3 = model.build(config.load("D3"))
    skirt = d3["skirt"]
    assert skirt["open_bays"] == []
    assert len(skirt["top_ring"]) == skirt["bay_count"]
    assert len(skirt["braces"]) == 2 * skirt["bay_count"]
    assert "header" not in skirt


# --- more than one door -----------------------------------------------------
#
# A dome in a camp wants doors facing particular ways, and a different number
# of them per dome. What has to hold: the doors are aimed and land in real
# bays, they are measured on the dome all of them leave rather than each on
# its own, and every consumer that used to read "the doorway" now reads all of
# them. The single-door path must come out byte-identical, which is what lets
# every existing variant and every golden file stay put.


from stardome import attachment, connectors, cover  # noqa: E402
from stardome.config import Door  # noqa: E402


def _multi(name="D10", doors=()):
    return model.build(config.load(name, doors=doors))


def test_one_unaimed_door_is_exactly_what_place_gave_before():
    """The compatibility guarantee the whole refactor rests on."""
    data = model.build(config.load("D6"))
    one = doorway.place(data, "carry", cut="portal")
    both = doorway.place_all(
        data, (Door(cut="portal", facing=None, template="carry"),)
    )[0]
    for key in ("bay", "frame", "cut", "in_bay", "opening_height_mm", "admits"):
        assert one[key] == both[key], key


def test_the_model_still_calls_the_first_one_the_doorway():
    data = _multi(doors=(Door("portal", 18.0, "carry"), Door("none", 198.0, "carry")))
    assert data["doorway"] is data["doorways"][0]
    assert len(data["doorways"]) == 2


def test_a_door_lands_in_the_bay_nearest_the_way_it_faces():
    data = _multi(
        doors=(
            Door("none", 198.0, "carry"),
            Door("none", 270.0, "carry"),
            Door("none", 54.0, "carry"),
        )
    )
    landed = [round(d["bay"]["centre_azimuth_deg"]) for d in data["doorways"]]
    assert landed == [198, 270, 54]
    for door in data["doorways"]:
        gap = abs(door["landed_deg"] - door["facing_deg"])
        assert gap < 2.0, door


def test_a_portal_takes_a_low_bay_and_a_lancet_a_tall_one():
    """The cuts are different cuts; each only makes sense in its own bay."""
    plain = model.build(config.load("D10", door="", door_cut="none"))
    low = {round(b["centre_azimuth_deg"]) for b in doorway.low_bays(plain)}
    tall = {round(b["centre_azimuth_deg"]) for b in doorway.tall_bays(plain)}
    assert low.isdisjoint(tall)

    # Aim both at the same azimuth and they still go to different bays.
    data = _multi(doors=(Door("portal", 54.0, "carry"),))
    assert round(data["doorways"][0]["bay"]["centre_azimuth_deg"]) in low

    data = _multi(doors=(Door("none", 54.0, "carry"),))
    assert round(data["doorways"][0]["bay"]["centre_azimuth_deg"]) in tall


def test_two_doors_in_one_bay_is_an_error_not_a_wider_door():
    with pytest.raises(ValueError, match="both land in the bay"):
        _multi(doors=(Door("none", 198.0, "carry"), Door("none", 200.0, "carry")))


def test_every_cut_lands_on_the_rods_not_just_the_first_doors():
    data = _multi(doors=(Door("portal", 18.0, "carry"), Door("portal", 162.0, "carry")))
    spans = doorway.removed_spans(data)
    # Two portals cut three bows between them, and one of them at both ends.
    assert len(spans) == 3
    assert sum(len(v) for v in spans.values()) == 4


def test_two_portals_leave_a_bow_standing_on_nothing():
    """One door cannot do this; two can, and it must not pass unremarked."""
    one = _multi(doors=(Door("portal", 18.0, "carry"),))
    two = _multi(doors=(Door("portal", 18.0, "carry"), Door("portal", 162.0, "carry")))
    assert doorway.landless_bows(one) == []
    assert doorway.landless_bows(two) == ["L1"]
    assert "no longer standing on the ground" in doorway.format_doors(two)


def test_the_schedule_counts_every_doorway_not_the_first():
    """Four released feet want four two-armed hubs, and four rod ends want
    four terminations. A schedule that saw one door would ask for two of
    each -- parts that do not fit where it matters most."""
    data = model.build(
        config.load(
            "D10", doors=(Door("portal", 18.0, "carry"), Door("portal", 162.0, "carry"))
        ),
        weave_mode="woven",
    )
    counts = {p["id"]: p["count"] for p in connectors.schedule(data)["parts"]}
    assert counts["BASE2-12"] == 4
    assert counts["BASE3-12"] == 6
    assert counts["TERM-12-70.5288"] == 4
    assert counts["BASE2-12"] + counts["BASE3-12"] == len(data["base_nodes"])


def test_the_cover_loses_every_opening():
    one = _multi(doors=(Door("portal", 18.0, "carry"),))
    three = _multi(
        doors=(
            Door("portal", 18.0, "carry"),
            Door("none", 198.0, "carry"),
            Door("none", 270.0, "carry"),
        )
    )
    a, b = cover.analyse(one), cover.analyse(three)
    assert a["opening"]["count"] == 1
    assert b["opening"]["count"] == 3
    assert b["opening"]["area_m2"] > a["opening"]["area_m2"]
    assert b["areas"]["total_m2"] < a["areas"]["total_m2"]
    # The seam still falls on the first door, which is the one azimuth anybody
    # can find on a built dome.
    assert three["cover"]["seam_phase_deg"] == pytest.approx(
        three["doorways"][0]["bay"]["centre_azimuth_deg"]
    )


def test_the_hem_is_broken_once_per_door():
    three = _multi(
        doors=(
            Door("portal", 18.0, "carry"),
            Door("none", 198.0, "carry"),
            Door("none", 270.0, "carry"),
        )
    )
    hem = attachment.analyse(three)["hem"]
    assert hem["doorway_count"] == 3
    assert len(hem["doorway_gaps_mm"]) == 3
    assert hem["rope_length_mm"] == pytest.approx(
        hem["circumference_mm"] - sum(hem["doorway_gaps_mm"]), abs=0.2
    )


def test_a_skirt_opens_a_bay_for_every_door():
    data = model.build(
        config.load(
            "D4", doors=(Door("portal", 18.0, "carry"), Door("portal", 162.0, "carry"))
        )
    )
    assert len(data["skirt"]["open_bays"]) == 2
    open_bays = set(data["skirt"]["open_bays"])
    assert not [b for b in data["skirt"]["braces"] if b["bay"] in open_bays]


# --- what the config accepts ------------------------------------------------


def _write(tmp_path, body: str):
    path = tmp_path / "variants.toml"
    path.write_text(
        "[defaults]\nrod_segments = 48\n\n"
        "[variants.D6]\ndiameter = 6000\nrod_diameter = 10\n" + body,
        encoding="utf-8",
    )
    return path


def test_the_config_reads_an_array_of_doors(tmp_path):
    path = _write(
        tmp_path,
        'door = "carry"\n'
        "[[variants.D6.doors]]\ncut = \"portal\"\nfacing = 18\n"
        "[[variants.D6.doors]]\ncut = \"none\"\nfacing = 198\ntemplate = \"tall\"\n",
    )
    doors = config.load("D6", path).doorways
    assert [d.cut for d in doors] == ["portal", "none"]
    assert [d.facing for d in doors] == [18.0, 198.0]
    # A door with no template of its own falls back to the variant's.
    assert [d.template for d in doors] == ["carry", "tall"]


def test_a_facing_is_taken_modulo_a_full_turn(tmp_path):
    path = _write(
        tmp_path,
        'door = "carry"\n[[variants.D6.doors]]\ncut = "none"\nfacing = 378\n',
    )
    assert config.load("D6", path).doorways[0].facing == pytest.approx(18.0)


def test_the_config_refuses_a_door_it_cannot_read(tmp_path):
    with pytest.raises(ValueError, match="unknown keys"):
        config.load(
            "D6",
            _write(tmp_path, 'door = "carry"\n[[variants.D6.doors]]\nwidth = 900\n'),
        )
    with pytest.raises(ValueError, match="no template"):
        config.load(
            "D6", _write(tmp_path, '[[variants.D6.doors]]\ncut = "none"\n')
        )
    with pytest.raises(ValueError, match="must be one of"):
        config.load(
            "D6",
            _write(tmp_path, 'door = "carry"\n[[variants.D6.doors]]\ncut = "sawn"\n'),
        )


def test_the_single_door_pair_still_describes_one_door():
    variant = config.load("D6")
    assert not variant.doors
    assert [d.cut for d in variant.doorways] == ["portal"]
    assert config.load("D3").doorways == ()
