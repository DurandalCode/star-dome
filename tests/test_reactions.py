"""Check equilibrium independently of the rigid-base implementation."""
import math
import pytest
from stardome import reactions


def test_arbitrary_translated_supports_recover_all_six_resultants():
    anchors = [dict(name=str(i), x=x+1300, y=y-900)
               for i, (x, y) in enumerate([(-1000,-700), (900,-600), (1200,800), (-600,1100)])]
    force = [130., -260., 900.]
    moment = [250000., -430000., 170000.]
    r = reactions.distribute(anchors, force, moment)
    total = [sum(a["force_n"][j] for a in r["anchors"]) for j in range(3)]
    recovered = [sum(a["y_mm"]*a["force_n"][2] for a in r["anchors"]),
                 -sum(a["x_mm"]*a["force_n"][2] for a in r["anchors"]),
                 sum(a["x_mm"]*a["force_n"][1]-a["y_mm"]*a["force_n"][0] for a in r["anchors"])]
    assert total == pytest.approx(force, abs=1e-9)
    assert recovered == pytest.approx(moment, abs=1e-6)


def test_regular_ring_maximum_matches_closed_form():
    n, radius, lift, my = 10, 2000., 1500., 1800000.
    anchors = [dict(name=str(i), x=radius*math.cos(2*math.pi*i/n), y=radius*math.sin(2*math.pi*i/n)) for i in range(n)]
    r = reactions.distribute(anchors, [0, 0, lift], [0, my, 0])
    assert r["max_uplift_n"] == pytest.approx(lift/n+2*my/(n*radius))
    assert r["max_bearing_n"] == pytest.approx(2*my/(n*radius)-lift/n)
    assert r["max_shear_n"] == 0


@pytest.mark.parametrize("xy", [[(0,0)]*3, [(0,0),(1,1),(2,2)], [(0,0),(1,0)]])
def test_degenerate_support_layout_is_rejected(xy):
    with pytest.raises(ValueError):
        reactions.distribute([dict(name=str(i), x=x, y=y) for i,(x,y) in enumerate(xy)], [0,0,1], [0,0,0])
