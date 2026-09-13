"""Pull everything the presentation draws from into one JSON file.

`draw.py` reads this rather than calling `stardome` itself, so the drawings
and the page are built from one snapshot of the model instead of several.

    python3 tools/presentation/extract.py --work exports/presentation
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import collections  # noqa: E402
import math  # noqa: E402

from stardome import bom, config, connectors, cover, model  # noqa: E402

# The dome every drawing uses. M is the reference prototype, and it is the one
# size whose parts are all generated, so it is what the part drawings show.
REFERENCE = 'D6'
SIZES = ['D3', 'D4', 'D6', 'D8', 'D10', 'D12']


def cut_list(name: str) -> dict:
    """Where every bow is cut, grouped by the pattern the bows share.

    Most bows of a size cut alike, so the page shows a pattern and says how
    many bows take it rather than listing fifteen near-identical rows. The
    representative bow carries its own crossings, which is what the drawing
    needs to show why a joint sits where it does.
    """
    d = model.build(config.load(name), weave_mode='layered')
    meta = d['meta']
    sleeve = connectors.SPLICE_SLEEVE_DIAMETERS * meta['rod_diameter']
    joints = connectors.splice_joints(d, meta['section_length'], sleeve)

    by_rod = collections.defaultdict(list)
    for j in joints:
        by_rod[j['rod']].append(j)

    mm_per_deg = math.pi * meta['dome_radius'] / 180.0
    crossings = collections.defaultdict(list)
    for c in d['crossings']:
        for side in ('a', 'b'):
            crossings[c[f'rod_{side}']].append(c[f't_{side}_deg'] * mm_per_deg)

    patterns = collections.defaultdict(list)
    detail = {}
    for rod in (r['name'] for r in d['rods']):
        placed = sorted(by_rod.get(rod, []), key=lambda j: j['s_mm'])
        if not placed:
            continue
        edges = [0.0] + [j['s_mm'] for j in placed]
        sections = [round(edges[i + 1] - edges[i], 1)
                    for i in range(len(edges) - 1)]
        sections.append(placed[-1]['sections_mm'][1])
        patterns[tuple(sections)].append(rod)
        detail[rod] = {
            'joints_mm': [round(j['s_mm'], 1) for j in placed],
            'moved_mm': [round(j['moved_mm'], 1) for j in placed],
            'clear_mm': [round(j['clear_of_crossing_mm'], 1) for j in placed],
            'crossings_mm': sorted(round(t, 1) for t in crossings.get(rod, [])),
            'length_mm': round(sum(sections), 1),
        }

    grouped = []
    for sections, rods in sorted(patterns.items(), key=lambda kv: -len(kv[1])):
        grouped.append({
            'sections_mm': list(sections),
            'bows': len(rods),
            'rods': rods,
            'even': len(set(sections)) == 1,
            'example': detail[rods[0]],
            'example_rod': rods[0],
        })

    return {
        'alias': meta.get('alias'),
        'bow_mm': round(meta['rod_length_nominal'], 1),
        'section_limit_mm': meta['section_length'],
        'sleeve_mm': round(sleeve, 1),
        'joints': len(joints),
        'sections': sum(len(g['sections_mm']) * g['bows'] for g in grouped),
        'longest_mm': round(max(max(g['sections_mm']) for g in grouped), 1),
        'tightest_clear_mm': round(
            min(j['clear_of_crossing_mm'] for j in joints), 1),
        'moved_max_mm': round(max(abs(j['moved_mm']) for j in joints), 1),
        'patterns': grouped,
    }


def collect() -> dict:
    out = {}

    # Layered weave is a drawing convention -- it pulls the shells apart so a
    # crossing reads as two rods rather than one. See docs/colours.md.
    drawn = model.build(config.load(REFERENCE), weave_mode='layered',
                        include_polylines=True)
    out['d6'] = {
        'meta': drawn['meta'],
        # Every other point: 48 segments per bow is more than a 700 px wide
        # drawing can show, and halving it keeps the page a megabyte smaller.
        'rods': [{'name': r['name'], 'family': r['family'],
                  'points': [[round(c, 1) for c in p] for p in r['points'][::2]]}
                 for r in drawn['rods']],
        'nodes': [{'name': n['name'], 'x': n['x'], 'y': n['y'], 'z': n['z'],
                   'rod_count': n['rod_count'], 'rods': n['rods']}
                  for n in drawn['nodes']],
        'base_nodes': drawn['base_nodes'],
        'crossing_types': drawn['crossing_types'],
    }

    # Flat weave for anything measured: the cover rests on the real sphere,
    # not on the drawing convention.
    flat = model.build(config.load(REFERENCE))
    gores = cover.gores(flat)
    out['cover_d6'] = {
        'radius_mm': cover.radius(flat),
        'gores': gores,
        'outline': cover.gore_outline(flat, gores['count']),
        'leaf': cover.leaf(flat),
        'panels': cover.panels(flat),
        'layouts': cover.layouts(flat),
        'analyse': cover.analyse(flat),
    }

    # The leaf/gore trade reverses across the family, so the page shows it as a
    # row per size rather than asserting one direction.
    out['cover_sizes'] = {}
    for name in SIZES:
        d = model.build(config.load(name))
        cuts = cover.layouts(d)
        out['cover_sizes'][name] = {
            'alias': d['meta'].get('alias'),
            'areas': cover.areas(d),
            'gores': cuts['gores'],
            'leaf': cuts['leaf'],
            'faces': cuts['faces'],
        }

    out['cuts'] = {name: cut_list(name) for name in SIZES}

    out['connectors'] = {}
    out['bom'] = {}
    for name in SIZES:
        d = model.build(config.load(name), weave_mode='layered')
        schedule = connectors.schedule(d)
        out['connectors'][name] = schedule
        out['bom'][name] = bom.analyse(d, schedule)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--work', default=str(ROOT / 'exports' / 'presentation'))
    args = ap.parse_args()

    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    path = work / 'model.json'
    path.write_text(json.dumps(collect(), default=str), encoding='utf-8')
    print(f'{path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
