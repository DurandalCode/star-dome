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

from stardome import bom, config, connectors, cover, model  # noqa: E402

# The dome every drawing uses. M is the reference prototype, and it is the one
# size whose parts are all generated, so it is what the part drawings show.
REFERENCE = 'D6'
SIZES = ['D3', 'D4', 'D6', 'D8', 'D10', 'D12']


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
        'gores': gores,
        'outline': cover.gore_outline(flat, gores['count']),
        'panels': cover.panels(flat),
        'analyse': cover.analyse(flat),
    }

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
