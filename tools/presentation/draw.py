"""Draw the figures the presentation uses, as SVG.

Colours follow docs/colours.md, which is the palette Blender and FreeCAD also
use -- so a G bow is the same blue here as it is in a render. Structural
colours are written literally; everything else (rules, grids, paper) is a CSS
variable, which is how the drawings follow the page into dark mode.

    python3 tools/presentation/draw.py --work exports/presentation
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
_ap.add_argument('--work', default=str(ROOT / 'exports' / 'presentation'))
_args = _ap.parse_args()

WORK = Path(_args.work)
DATA = json.loads((WORK / 'model.json').read_text(encoding='utf-8'))
OUT = str(WORK / 'svg') + '/'
Path(OUT).mkdir(parents=True, exist_ok=True)

# docs/colours.md, converted to hex
C = {
    'G': '#268CF2',      # 0.15,0.55,0.95
    'U': '#F2730E',      # 0.95,0.45,0.10
    'L': '#33BF59',      # 0.20,0.75,0.35
    'lashed': '#F22640',  # 0.95,0.15,0.25
    'unlashed': '#8C8C99',
    'base': '#40404D',
    'door': '#FFC71A',
    'jamb': '#FF6B0D',
}


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def svg(w, h, body, extra=''):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" '
            f'style="max-width:100%;height:auto" {extra}>{body}</svg>')


# ---------------------------------------------------------------------------
# 1. Size comparison: every dome to one scale, with a 1.8 m person
# ---------------------------------------------------------------------------
def sizes_svg():
    sizes = [
        ('D3', 3000, 1473.4, 1000, None),
        ('D4', 4000, 1964.5, 1350, 'S'),
        ('D6', 6000, 2946.7, 0, 'M'),
        ('D8', 8000, 3929.0, 0, 'L'),
        ('D10', 10000, 4911.2, 0, 'XL'),
        ('D12', 12000, 5893.5, 0, None),
    ]
    pad_l, pad_r, pad_t, pad_b = 56, 30, 46, 64
    gap_mm = 900
    total_mm = sum(s[1] for s in sizes) + gap_mm * (len(sizes) - 1)
    max_h_mm = max(s[2] + s[3] for s in sizes)
    W = 1180
    scale = (W - pad_l - pad_r) / total_mm
    H = pad_t + pad_b + max_h_mm * scale

    def X(mm):
        return pad_l + mm * scale

    def Y(mm):
        return H - pad_b - mm * scale

    p = []
    # ground
    p.append(f'<line x1="{pad_l-30:.1f}" y1="{Y(0):.1f}" x2="{W-10:.1f}" y2="{Y(0):.1f}" '
             f'stroke="var(--rule)" stroke-width="1.25"/>')
    # height grid at 1 m steps
    for m in range(1, 7):
        y = Y(m * 1000)
        p.append(f'<line x1="{pad_l-30:.1f}" y1="{y:.1f}" x2="{W-10:.1f}" y2="{y:.1f}" '
                 f'stroke="var(--grid)" stroke-width="0.75" stroke-dasharray="2 5"/>')
        p.append(f'<text x="{pad_l-36:.1f}" y="{y+3.5:.1f}" text-anchor="end" '
                 f'class="dim">{m} м</text>')

    cursor = 0.0
    for name, dia, dome_h, skirt, alias in sizes:
        r = dia / 2.0
        cx = cursor + r
        # skirt
        if skirt:
            p.append(f'<rect x="{X(cursor):.1f}" y="{Y(skirt):.1f}" '
                     f'width="{dia*scale:.1f}" height="{skirt*scale:.1f}" '
                     f'fill="var(--skirt-fill)" stroke="var(--skirt-line)" stroke-width="1"/>')
        # dome profile: a circular arc of radius r, flattened to dome_h
        pts = []
        for i in range(49):
            a = math.pi * i / 48.0
            px = cx - r * math.cos(a)
            pz = skirt + dome_h * math.sin(a)
            pts.append(f'{X(px):.1f},{Y(pz):.1f}')
        p.append(f'<polyline points="{" ".join(pts)}" fill="var(--dome-fill)" '
                 f'stroke="{C["G"]}" stroke-width="2" stroke-linejoin="round"/>')
        # label
        label = f'{alias} · {name}' if alias else name
        p.append(f'<text x="{X(cx):.1f}" y="{Y(0)+24:.1f}" text-anchor="middle" '
                 f'class="lbl-big">{esc(label)}</text>')
        p.append(f'<text x="{X(cx):.1f}" y="{Y(0)+42:.1f}" text-anchor="middle" '
                 f'class="lbl-sm">{dia/1000:g} м · {(dome_h+skirt)/1000:.2f} м</text>')
        cursor += dia + gap_mm

    # 1.8 m person at the far left, inside D12 for reference
    hx = X(cursor - 12000 - gap_mm + 2700)
    hh = 1800 * scale
    p.append(f'<g stroke="var(--ink)" stroke-width="1.6" fill="none" opacity="0.75">')
    head_r = hh * 0.085
    p.append(f'<circle cx="{hx:.1f}" cy="{Y(0)-hh+head_r:.1f}" r="{head_r:.1f}"/>')
    p.append(f'<line x1="{hx:.1f}" y1="{Y(0)-hh+2*head_r:.1f}" x2="{hx:.1f}" y2="{Y(0)-hh*0.42:.1f}"/>')
    p.append(f'<line x1="{hx-hh*0.11:.1f}" y1="{Y(0):.1f}" x2="{hx:.1f}" y2="{Y(0)-hh*0.42:.1f}"/>')
    p.append(f'<line x1="{hx+hh*0.11:.1f}" y1="{Y(0):.1f}" x2="{hx:.1f}" y2="{Y(0)-hh*0.42:.1f}"/>')
    p.append(f'<line x1="{hx-hh*0.14:.1f}" y1="{Y(0)-hh*0.5:.1f}" x2="{hx+hh*0.14:.1f}" y2="{Y(0)-hh*0.58:.1f}"/>')
    p.append('</g>')
    p.append(f'<text x="{hx:.1f}" y="{Y(1800)-10:.1f}" text-anchor="middle" class="dim">1,8 м</text>')

    return svg(int(W), int(H), ''.join(p))


# ---------------------------------------------------------------------------
# 2 & 3. D6 elevation and plan
# ---------------------------------------------------------------------------
def dome_view(mode='elevation', colour_by='family', show_labels=False):
    """mode: elevation (x,z) or plan (x,y). colour_by: family | part"""
    d6 = DATA['d6']
    rods = d6['rods']
    nodes = d6['nodes']
    base = d6['base_nodes']
    R = d6['meta']['dome_radius']

    # node -> part id
    node_part = {}
    for part in DATA['connectors']['D6']['parts']:
        for n in part.get('nodes', []) or []:
            node_part[n] = part['id']

    W = 720
    pad = 62
    if mode == 'elevation':
        span_x = 2 * R * 1.04
        span_y = d6['meta']['dome_height_nominal'] * 1.08
    else:
        span_x = 2 * R * 1.04
        span_y = 2 * R * 1.04
    scale = (W - 2 * pad) / span_x
    H = span_y * scale + 2 * pad + (26 if mode == 'elevation' else 0)

    def proj(pt):
        x, y, z = pt
        if mode == 'elevation':
            return (W / 2 + x * scale, H - pad - 26 - z * scale, y)
        return (W / 2 + x * scale, H / 2 - y * scale, z)

    p = []
    if mode == 'elevation':
        gy = H - pad - 26
        p.append(f'<line x1="{pad*0.5:.1f}" y1="{gy:.1f}" x2="{W-pad*0.5:.1f}" y2="{gy:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1.25"/>')
    else:
        p.append(f'<circle cx="{W/2:.1f}" cy="{H/2:.1f}" r="{R*scale:.1f}" fill="none" '
                 f'stroke="var(--grid)" stroke-width="0.75" stroke-dasharray="3 4"/>')

    # depth-sorted rods so the near ones sit on top
    drawn = []
    for rod in rods:
        pts = [proj(q) for q in rod['points']]
        depth = sum(q[2] for q in pts) / len(pts)
        col = C[rod['family']]
        drawn.append((depth, rod, pts, col))
    drawn.sort(key=lambda t: t[0])

    for depth, rod, pts, col in drawn:
        far = depth < 0
        op = 0.32 if far else 1.0
        wdt = 1.6 if far else 2.6
        poly = ' '.join(f'{q[0]:.1f},{q[1]:.1f}' for q in pts)
        p.append(f'<polyline points="{poly}" fill="none" stroke="{col}" '
                 f'stroke-width="{wdt}" stroke-linecap="round" opacity="{op}"/>')

    # base points
    for b in base:
        q = proj((b['x'], b['y'], b['z']))
        p.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="4.2" fill="{C["base"]}" '
                 f'stroke="var(--paper)" stroke-width="1.2"/>')

    # nodes
    for n in nodes:
        q = proj((n['x'], n['y'], n['z']))
        far = q[2] < 0 if mode == 'elevation' else False
        if colour_by == 'part':
            pid = node_part.get(n['name'], '')
            col = C['lashed'] if pid.startswith('FAN') else C['unlashed']
            r = 5.6 if pid.startswith('FAN') else 4.0
        else:
            col = C['lashed'] if n['rod_count'] >= 4 else C['unlashed']
            r = 5.2 if n['rod_count'] >= 4 else 3.8
        p.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{r:.1f}" fill="{col}" '
                 f'stroke="var(--paper)" stroke-width="1.3" '
                 f'opacity="{0.4 if far else 1}"/>')

    if mode == 'elevation':
        # height dimension
        gy = H - pad - 26
        hz = d6['meta']['dome_height_nominal']
        dx = W - pad * 0.75
        p.append(f'<line x1="{dx:.1f}" y1="{gy:.1f}" x2="{dx:.1f}" y2="{gy-hz*scale:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1"/>')
        for yy in (gy, gy - hz * scale):
            p.append(f'<line x1="{dx-4:.1f}" y1="{yy:.1f}" x2="{dx+4:.1f}" y2="{yy:.1f}" '
                     f'stroke="var(--rule)" stroke-width="1"/>')
        p.append(f'<text x="{dx-8:.1f}" y="{gy-hz*scale/2:.1f}" text-anchor="end" '
                 f'class="dim" transform="rotate(-90 {dx-8:.1f} {gy-hz*scale/2:.1f})">2947 мм</text>')
        # diameter
        by = gy + 18
        p.append(f'<line x1="{W/2-R*scale:.1f}" y1="{by:.1f}" x2="{W/2+R*scale:.1f}" y2="{by:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1"/>')
        p.append(f'<text x="{W/2:.1f}" y="{by+15:.1f}" text-anchor="middle" class="dim">'
                 f'⌀ 6000 мм</text>')
    return svg(int(W), int(H), ''.join(p))


# ---------------------------------------------------------------------------
# 3b. Where every part sits on the dome, called out by name
# ---------------------------------------------------------------------------
SPLICE_COL = '#8E5BD9'


def _bow_point_at(points, frac):
    """Interpolate along a polyline by fraction of its own arc length."""
    seg = []
    total = 0.0
    for a, b in zip(points, points[1:]):
        d = math.dist(a, b)
        seg.append((total, d, a, b))
        total += d
    target = frac * total
    for s0, d, a, b in seg:
        if target <= s0 + d or (s0, d, a, b) == seg[-1]:
            t = (target - s0) / d if d else 0.0
            t = max(0.0, min(1.0, t))
            return [a[i] + (b[i] - a[i]) * t for i in range(3)]
    return points[-1]


def parts_callout():
    d6 = DATA['d6']
    rods, nodes, base = d6['rods'], d6['nodes'], d6['base_nodes']
    R = d6['meta']['dome_radius']
    sections = 4  # D6 divides into 4 x 2356 mm

    # The label columns live in the margins, so the drawing gets the middle band
    # and no callout can ever run into the dome or into its opposite number.
    W = 1000
    MARGIN = 208
    pad_t, pad_b = 26, 46
    span_x = 2 * R * 1.03
    scale = (W - 2 * MARGIN) / span_x
    H = d6['meta']['dome_height_nominal'] * scale + pad_t + pad_b

    def proj(pt):
        x, y, z = pt
        return (W / 2 + x * scale, H - pad_b - z * scale, y)

    p = []
    gy = H - pad_b
    p.append(f'<line x1="{MARGIN-40:.1f}" y1="{gy:.1f}" x2="{W-MARGIN+40:.1f}" y2="{gy:.1f}" '
             f'stroke="var(--rule)" stroke-width="1.25"/>')

    # rods as quiet context
    drawn = []
    for rod in rods:
        pts = [proj(q) for q in rod['points']]
        depth = sum(q[2] for q in pts) / len(pts)
        drawn.append((depth, rod, pts))
    drawn.sort(key=lambda t: t[0])
    for depth, rod, pts in drawn:
        far = depth < 0
        poly = ' '.join(f'{q[0]:.1f},{q[1]:.1f}' for q in pts)
        p.append(f'<polyline points="{poly}" fill="none" stroke="var(--ctx)" '
                 f'stroke-width="{1.2 if far else 2.0}" stroke-linecap="round" '
                 f'opacity="{0.3 if far else 0.72}"/>')

    # splices along every bow
    for rod in rods:
        for k in range(1, sections):
            q = proj(_bow_point_at(rod['points'], k / sections))
            far = q[2] < 0
            p.append(f'<rect x="{q[0]-3.4:.1f}" y="{q[1]-3.4:.1f}" width="6.8" height="6.8" '
                     f'transform="rotate(45 {q[0]:.1f} {q[1]:.1f})" fill="{SPLICE_COL}" '
                     f'stroke="var(--paper)" stroke-width="1" '
                     f'opacity="{0.38 if far else 1}"/>')

    # crossings and fans
    for n in nodes:
        q = proj((n['x'], n['y'], n['z']))
        far = q[2] < 0
        four = n['rod_count'] >= 4
        col = C['lashed'] if four else C['unlashed']
        p.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="{6.0 if four else 4.2:.1f}" '
                 f'fill="{col}" stroke="var(--paper)" stroke-width="1.3" '
                 f'opacity="{0.4 if far else 1}"/>')
    # feet
    for b in base:
        q = proj((b['x'], b['y'], b['z']))
        p.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="5.4" fill="{C["base"]}" '
                 f'stroke="var(--paper)" stroke-width="1.2"/>')
        p.append(f'<path d="M {q[0]:.1f} {q[1]+5:.1f} l 0 12" stroke="{C["base"]}" '
                 f'stroke-width="2.2" stroke-linecap="round"/>')

    # Callouts. Each label sits in a reserved slot in one of the two margins and
    # its leader runs to the frontmost instance on that same side, so no leader
    # crosses the dome and no two labels can ever collide.
    def best_node(pred, side):
        best = None
        for n in nodes:
            if not pred(n):
                continue
            q = proj((n['x'], n['y'], n['z']))
            if q[2] < 0:
                continue                      # back of the dome
            if (q[0] > W / 2) if side < 0 else (q[0] < W / 2):
                continue
            if best is None or q[2] > best[2]:
                best = q
        return best

    def best_splice(side):
        best = None
        for rod in rods:
            for k in range(1, sections):
                q = proj(_bow_point_at(rod['points'], k / sections))
                if q[2] < 0:
                    continue
                if (q[0] > W / 2 - 50) if side < 0 else (q[0] < W / 2 + 50):
                    continue
                if best is None or q[2] > best[2]:
                    best = q
        return best

    def best_foot(side):
        c = [proj((b['x'], b['y'], b['z'])) for b in base]
        c = [q for q in c if (q[0] < W / 2 if side < 0 else q[0] > W / 2)]
        return max(c, key=lambda q: q[2]) if c else None

    callouts = [
        (best_node(lambda n: n['rod_count'] >= 4, -1), -1, 0.16,
         'FAN4-10-37.3774', '10 шт · узел на 4 прутка', C['lashed']),
        (best_splice(-1), -1, 0.56,
         'SPLICE-10', '45 шт · стальная гильза', SPLICE_COL),
        (best_node(lambda n: n['rod_count'] == 2, 1), 1, 0.26,
         'CL2-10-70.5288', '30 шт · хомут на 2 прутка', C['unlashed']),
        (best_foot(1), 1, 0.88,
         'BASE3/BASE2 + STAKE', '8 + 2 + 10 шт · пята и штырь', C['base']),
    ]
    for q, side, fy, name, sub, col in callouts:
        if not q:
            continue
        ex = MARGIN - 24 if side < 0 else W - MARGIN + 24
        ey = pad_t + fy * (gy - pad_t)
        anchor = 'end' if side < 0 else 'start'
        tx = ex + side * 9
        p.append(f'<path d="M {q[0]:.1f} {q[1]:.1f} L {ex:.1f} {ey:.1f}" stroke="{col}" '
                 f'stroke-width="1.1" fill="none" opacity="0.85"/>')
        p.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="2.6" fill="{col}"/>')
        p.append(f'<text x="{tx:.1f}" y="{ey-2:.1f}" text-anchor="{anchor}" '
                 f'class="mono-sm" fill="{col}">{esc(name)}</text>')
        p.append(f'<text x="{tx:.1f}" y="{ey+12:.1f}" text-anchor="{anchor}" '
                 f'class="dim">{esc(sub)}</text>')

    p.append(f'<text x="{W/2:.1f}" y="{H-10:.1f}" text-anchor="middle" class="lbl-sm">'
             f'M · D6 — 107 деталей на купол в 7 типах</text>')
    return svg(int(W), int(H), ''.join(p))


# ---------------------------------------------------------------------------
# 4. Where the parts sit: node height ladder
# ---------------------------------------------------------------------------
def parts_ladder():
    d6 = DATA['d6']
    types = d6['crossing_types']
    node_part = {}
    for part in DATA['connectors']['D6']['parts']:
        for n in part.get('nodes', []) or []:
            node_part[n] = part['id']

    # group crossing types by z
    rings = {}
    for t in types:
        rings.setdefault(round(t['z'], 1), []).append(t)
    zs = sorted(rings, reverse=True)

    W, pad_t, pad_b, pad_l = 720, 34, 34, 150
    H = pad_t + pad_b + 26 * len(zs) + 30
    top_z = d6['meta']['dome_height_nominal']
    p = []
    p.append(f'<text x="{pad_l}" y="18" class="lbl-sm">высота, мм</text>')
    p.append(f'<text x="{pad_l+150}" y="18" class="lbl-sm">классы пересечений на этой высоте</text>')
    for i, z in enumerate(zs):
        y = pad_t + 22 + i * 26
        frac = z / top_z
        p.append(f'<line x1="{pad_l-96:.1f}" y1="{y:.1f}" x2="{W-20:.1f}" y2="{y:.1f}" '
                 f'stroke="var(--grid)" stroke-width="0.75"/>')
        p.append(f'<text x="{pad_l-104:.1f}" y="{y+4:.1f}" text-anchor="end" class="mono-sm">'
                 f'{z:.0f}</text>')
        # bar for relative height
        p.append(f'<rect x="{pad_l-92:.1f}" y="{y-5:.1f}" width="{max(2,frac*72):.1f}" height="10" '
                 f'fill="{C["G"]}" opacity="0.22"/>')
        chips = []
        x = pad_l
        for t in sorted(rings[z], key=lambda t: t['name']):
            nodes4 = t['tied'] == 1
            col = C['lashed'] if nodes4 else C['unlashed']
            w = 116
            chips.append(
                f'<rect x="{x:.1f}" y="{y-9:.1f}" width="{w}" height="18" rx="2" '
                f'fill="{col}" opacity="0.14"/>'
                f'<text x="{x+7:.1f}" y="{y+4:.1f}" class="mono-sm" fill="{col}">'
                f'{t["name"]} ×{t["count"]} · {t["angle_deg"]:.1f}°</text>')
            x += w + 7
        p.append(''.join(chips))
    return svg(W, int(H), ''.join(p))



# ---------------------------------------------------------------------------
# 5. The cover, main's model: one gore, drawn from its real outline
# ---------------------------------------------------------------------------
GORE_COL = '#268CF2'


def gore_svg():
    cv = DATA['cover_d6']
    g = cv['gores']
    outline = [(float(a), float(b)) for a, b in cv['outline']]
    L = g['gore_length_mm']
    Wd = g['gore_width_mm']

    W, pad_l, pad_r, pad_t, pad_b = 620, 96, 96, 44, 54
    scale = (W - pad_l - pad_r) / L
    H = Wd * scale + pad_t + pad_b

    def X(s):
        return pad_l + s * scale

    def Y(h):
        return pad_t + Wd * scale / 2 - h * scale

    top = ' '.join(f'{X(s):.1f},{Y(h):.1f}' for s, h in outline)
    bot = ' '.join(f'{X(s):.1f},{Y(-h):.1f}' for s, h in reversed(outline))
    p = [f'<polygon points="{top} {bot}" fill="{GORE_COL}" fill-opacity="0.16" '
         f'stroke="{GORE_COL}" stroke-width="1.8" stroke-linejoin="round"/>']
    p.append(f'<line x1="{X(0):.1f}" y1="{Y(0):.1f}" x2="{X(L):.1f}" y2="{Y(0):.1f}" '
             f'stroke="{GORE_COL}" stroke-width="0.9" stroke-dasharray="6 4" opacity="0.55"/>')
    dx = X(L) + 22
    p.append(f'<line x1="{dx:.1f}" y1="{Y(Wd/2):.1f}" x2="{dx:.1f}" y2="{Y(-Wd/2):.1f}" '
             f'stroke="var(--rule)" stroke-width="1"/>')
    for yy in (Y(Wd / 2), Y(-Wd / 2)):
        p.append(f'<line x1="{dx-4:.1f}" y1="{yy:.1f}" x2="{dx+4:.1f}" y2="{yy:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1"/>')
    p.append(f'<text x="{dx+9:.1f}" y="{Y(0)+4:.1f}" class="dim">низ · {Wd:.0f} мм</text>')
    by = Y(-Wd / 2) + 24
    p.append(f'<line x1="{X(0):.1f}" y1="{by:.1f}" x2="{X(L):.1f}" y2="{by:.1f}" '
             f'stroke="var(--rule)" stroke-width="1"/>')
    for xx in (X(0), X(L)):
        p.append(f'<line x1="{xx:.1f}" y1="{by-4:.1f}" x2="{xx:.1f}" y2="{by+4:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1"/>')
    p.append(f'<text x="{X(L/2):.1f}" y="{by+15:.1f}" text-anchor="middle" class="dim">'
             f'{L:.0f} мм — от полюса до основания</text>')
    p.append(f'<text x="{X(0)-10:.1f}" y="{Y(0)+4:.1f}" text-anchor="end" class="mono-sm">полюс</text>')
    return svg(int(W), int(H), ''.join(p))


def gore_roll_svg(show=4):
    """Gores laid down the roll, which is how the 61,7 m gets spent."""
    cv = DATA['cover_d6']
    g = cv['gores']
    outline = [(float(a), float(b)) for a, b in cv['outline']]
    L, Wd, roll = g['gore_length_mm'], g['gore_width_mm'], g['roll_width_mm']
    n = g['count']

    W, pad_l, pad_r, pad_t, pad_b = 1180, 74, 30, 42, 58
    run = L * show
    scale = (W - pad_l - pad_r) / run
    H = roll * scale + pad_t + pad_b

    def X(mm):
        return pad_l + mm * scale

    def Y(mm):
        return pad_t + mm * scale

    p = [f'<rect x="{X(0):.1f}" y="{Y(0):.1f}" width="{run*scale:.1f}" '
         f'height="{roll*scale:.1f}" fill="var(--roll-fill)" stroke="var(--rule)" '
         f'stroke-width="1.25"/>']
    mid = roll / 2.0
    for k in range(show):
        s0 = k * L
        top = ' '.join(f'{X(s0+s):.1f},{Y(mid-h):.1f}' for s, h in outline)
        bot = ' '.join(f'{X(s0+s):.1f},{Y(mid+h):.1f}' for s, h in reversed(outline))
        p.append(f'<polygon points="{top} {bot}" fill="{GORE_COL}" '
                 f'fill-opacity="{0.10 + 0.06*(k%2):.2f}" stroke="{GORE_COL}" '
                 f'stroke-width="1.4" stroke-linejoin="round"/>')
        p.append(f'<text x="{X(s0+L/2):.1f}" y="{Y(mid)+4:.1f}" text-anchor="middle" '
                 f'class="mono-sm">клин {k+1}</text>')
        if k:
            p.append(f'<line x1="{X(s0):.1f}" y1="{Y(0):.1f}" x2="{X(s0):.1f}" '
                     f'y2="{Y(roll):.1f}" stroke="var(--grid)" stroke-width="0.8" '
                     f'stroke-dasharray="3 4"/>')
    p.append(f'<text x="{X(run)-10:.1f}" y="{Y(mid)-14:.1f}" text-anchor="end" '
             f'class="dim">… и так {n} раз</text>')
    dx = pad_l - 16
    p.append(f'<line x1="{dx:.1f}" y1="{Y(0):.1f}" x2="{dx:.1f}" y2="{Y(roll):.1f}" '
             f'stroke="var(--rule)" stroke-width="1"/>')
    for yy in (Y(0), Y(roll)):
        p.append(f'<line x1="{dx-4:.1f}" y1="{yy:.1f}" x2="{dx+4:.1f}" y2="{yy:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1"/>')
    p.append(f'<text x="{dx-8:.1f}" y="{Y(roll/2):.1f}" text-anchor="middle" class="dim" '
             f'transform="rotate(-90 {dx-8:.1f} {Y(roll/2):.1f})">рулон {roll:.0f} мм</text>')
    by = Y(roll) + 26
    p.append(f'<text x="{X(run/2):.1f}" y="{by:.1f}" text-anchor="middle" class="dim">'
             f'{n} клиньев × {L/1000:.2f} м = {n*L/1000:.1f} м рулона · '
             f'клин {Wd:.0f} мм в ширину против рулона {roll:.0f} мм</text>')
    return svg(int(W), int(H), ''.join(p))


def faces_svg():
    """The other way to cut it: flat faces, a pentagon and a triangle."""
    pn = DATA['cover_d6']['panels']
    edge = pn['edge_mm']
    sh = pn['shapes']
    W, H = 1180, 400
    p = []

    def poly(cx, cy, sides, r, rot, col, label, sub, minw, strips):
        pts = []
        for i in range(sides):
            a = rot + 2 * math.pi * i / sides
            pts.append(f'{cx + r*math.cos(a):.1f},{cy + r*math.sin(a):.1f}')
        p.append(f'<polygon points="{" ".join(pts)}" fill="{col}" fill-opacity="0.15" '
                 f'stroke="{col}" stroke-width="1.8" stroke-linejoin="round"/>')
        p.append(f'<line x1="{cx-r*1.06:.1f}" y1="{cy:.1f}" x2="{cx+r*1.06:.1f}" '
                 f'y2="{cy:.1f}" stroke="{col}" stroke-width="1.2" '
                 f'stroke-dasharray="5 4" opacity="0.85"/>')
        p.append(f'<text x="{cx:.1f}" y="{cy+r+34:.1f}" text-anchor="middle" '
                 f'class="lbl-big">{esc(label)}</text>')
        p.append(f'<text x="{cx:.1f}" y="{cy+r+51:.1f}" text-anchor="middle" '
                 f'class="dim">{esc(sub)}</text>')
        p.append(f'<text x="{cx:.1f}" y="{cy+r+66:.1f}" text-anchor="middle" '
                 f'class="dim">{minw:.0f} мм поперёк → {strips} полосы</text>')

    poly(400, 150, 5, 104, -math.pi / 2, GORE_COL, 'Пятиугольник ×6',
         f'сторона {edge:.0f} мм', sh['5']['min_width_mm'], sh['5']['strips'])
    poly(790, 150, 3, 104, -math.pi / 2, C['U'], 'Треугольник ×10',
         f'сторона {edge:.0f} мм', sh['3']['min_width_mm'], sh['3']['strips'])
    p.append(f'<text x="{W/2:.1f}" y="{H-10:.1f}" text-anchor="middle" class="lbl-sm">'
             f'16 граней · {pn["pieces"]} деталей · пунктир — деление на полосы под рулон 1500 мм</text>')
    return svg(W, H, ''.join(p))




# ---------------------------------------------------------------------------
# 7. The leaf: the cut that escapes the roll width
# ---------------------------------------------------------------------------
LEAF_COLS = ['#268CF2', '#3E9BF5', '#5BAAF7', '#79B9F9']


def _lanes():
    """Rebuild each lane's top and bottom width from the leaf plan."""
    cv = DATA['cover_d6']
    lf = cv['leaf']
    r = cv['radius_mm']
    leaves, lap, lanes = lf['leaves'], lf['lap_mm'], lf['lanes_per_leaf']
    slant = math.pi * r / 2.0
    step = (slant - lap) / lanes

    def width_at(arc):
        return 2.0 * math.pi * r * math.sin(min(arc / r, math.pi / 2.0)) / leaves

    out = []
    for i in range(lanes):
        s_top = i * step
        s_low = min(slant, (i + 1) * step + lap)
        out.append((i, s_top, s_low, width_at(s_top), width_at(s_low)))
    return lf, slant, out


def leaf_svg():
    """One leaf, assembled: four lanes lapped, narrow at the pole."""
    lf, slant, lanes = _lanes()
    # Full width like the other plates, so it renders at the same scale as
    # them rather than being blown up to fit the container.
    W, pad_t, pad_b = 1180, 40, 54
    widest = lanes[-1][4]
    scale = min((W - 420) / widest, (500 - pad_t - pad_b) / slant)
    H = slant * scale + pad_t + pad_b
    cx = W / 2
    p = []

    def Y(s):
        return pad_t + s * scale

    for i, s_top, s_low, w_top, w_low in lanes:
        col = LEAF_COLS[i % len(LEAF_COLS)]
        pts = (f'{cx-w_top/2*scale:.1f},{Y(s_top):.1f} '
               f'{cx+w_top/2*scale:.1f},{Y(s_top):.1f} '
               f'{cx+w_low/2*scale:.1f},{Y(s_low):.1f} '
               f'{cx-w_low/2*scale:.1f},{Y(s_low):.1f}')
        p.append(f'<polygon points="{pts}" fill="{col}" fill-opacity="0.17" '
                 f'stroke="{col}" stroke-width="1.5"/>')
        p.append(f'<text x="{cx:.1f}" y="{Y((s_top+s_low)/2)+4:.1f}" '
                 f'text-anchor="middle" class="mono-sm">полоса {i+1}</text>')
        p.append(f'<text x="{cx+w_low/2*scale+9:.1f}" y="{Y(s_low)-3:.1f}" '
                 f'class="dim">{w_low:.0f}</text>')
    # the slant
    dx = 46
    p.append(f'<line x1="{dx:.1f}" y1="{Y(0):.1f}" x2="{dx:.1f}" y2="{Y(slant):.1f}" '
             f'stroke="var(--rule)" stroke-width="1"/>')
    for yy in (Y(0), Y(slant)):
        p.append(f'<line x1="{dx-4:.1f}" y1="{yy:.1f}" x2="{dx+4:.1f}" y2="{yy:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1"/>')
    p.append(f'<text x="{dx-7:.1f}" y="{Y(slant/2):.1f}" text-anchor="middle" '
             f'class="dim" transform="rotate(-90 {dx-7:.1f} {Y(slant/2):.1f})">'
             f'дуга {slant:.0f} мм</text>')
    p.append(f'<text x="{cx:.1f}" y="{H-14:.1f}" text-anchor="middle" class="lbl-sm">'
             f'один лепесток из {lf["lanes_per_leaf"]} полос · нахлёст '
             f'{lf["lap_mm"]:.0f} мм · всего {lf["leaves"]} лепестков</text>')
    return svg(int(W), int(H), ''.join(p))


def leaf_roll_svg():
    """Why it is cheap: two lanes share a rectangle, turned end for end."""
    lf, slant, lanes = _lanes()
    roll = lf['roll_width_mm']
    lane_h = lf['lane_height_mm']
    run = sum(w_top + w_low for _, _, _, w_top, w_low in lanes)

    # Two stacked dimensions in the left margin: the roll, and the lane in it.
    W, pad_l, pad_r, pad_t, pad_b = 1180, 112, 28, 40, 58
    scale = (W - pad_l - pad_r) / run
    H = roll * scale + pad_t + pad_b
    p = []

    def X(mm):
        return pad_l + mm * scale

    def Y(mm):
        return pad_t + mm * scale

    p.append(f'<rect x="{X(0):.1f}" y="{Y(0):.1f}" width="{run*scale:.1f}" '
             f'height="{roll*scale:.1f}" fill="var(--roll-fill)" '
             f'stroke="var(--rule)" stroke-width="1.25"/>')
    # the leftover strip down the whole run
    p.append(f'<rect x="{X(0):.1f}" y="{Y(lane_h):.1f}" width="{run*scale:.1f}" '
             f'height="{(roll-lane_h)*scale:.1f}" fill="var(--offcut)"/>')

    cursor = 0.0
    for i, _, _, w_top, w_low in lanes:
        col = LEAF_COLS[i % len(LEAF_COLS)]
        up = (f'{X(cursor):.1f},{Y(0):.1f} {X(cursor+w_top):.1f},{Y(0):.1f} '
              f'{X(cursor+w_low):.1f},{Y(lane_h):.1f} {X(cursor):.1f},{Y(lane_h):.1f}')
        p.append(f'<polygon points="{up}" fill="{col}" fill-opacity="0.20" '
                 f'stroke="{col}" stroke-width="1.4"/>')
        # its partner, turned end for end, filling the rest of the rectangle
        dn = (f'{X(cursor+w_top):.1f},{Y(0):.1f} {X(cursor+w_top+w_low):.1f},{Y(0):.1f} '
              f'{X(cursor+w_top+w_low):.1f},{Y(lane_h):.1f} {X(cursor+w_low):.1f},{Y(lane_h):.1f}')
        p.append(f'<polygon points="{dn}" fill="{col}" fill-opacity="0.36" '
                 f'stroke="{col}" stroke-width="1.4"/>')
        mid = cursor + (w_top + w_low) / 2
        p.append(f'<text x="{X(mid):.1f}" y="{Y(lane_h/2)-2:.1f}" '
                 f'text-anchor="middle" class="mono-sm">полоса {i+1} ×2</text>')
        p.append(f'<text x="{X(mid):.1f}" y="{Y(lane_h/2)+13:.1f}" '
                 f'text-anchor="middle" class="dim">{w_top:.0f} → {w_low:.0f}</text>')
        cursor += w_top + w_low

    dx = pad_l - 16
    p.append(f'<line x1="{dx:.1f}" y1="{Y(0):.1f}" x2="{dx:.1f}" y2="{Y(roll):.1f}" '
             f'stroke="var(--rule)" stroke-width="1"/>')
    for yy in (Y(0), Y(roll)):
        p.append(f'<line x1="{dx-4:.1f}" y1="{yy:.1f}" x2="{dx+4:.1f}" y2="{yy:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1"/>')
    p.append(f'<text x="{dx-8:.1f}" y="{Y(roll/2):.1f}" text-anchor="middle" class="dim" '
             f'transform="rotate(-90 {dx-8:.1f} {Y(roll/2):.1f})">рулон {roll:.0f} мм</text>')
    dh = pad_l - 52
    p.append(f'<line x1="{dh:.1f}" y1="{Y(0):.1f}" x2="{dh:.1f}" y2="{Y(lane_h):.1f}" '
             f'stroke="var(--rule)" stroke-width="1"/>')
    for yy in (Y(0), Y(lane_h)):
        p.append(f'<line x1="{dh-4:.1f}" y1="{yy:.1f}" x2="{dh+4:.1f}" y2="{yy:.1f}" '
                 f'stroke="var(--rule)" stroke-width="1"/>')
    p.append(f'<text x="{dh-8:.1f}" y="{Y(lane_h/2):.1f}" text-anchor="middle" '
             f'class="dim" transform="rotate(-90 {dh-8:.1f} {Y(lane_h/2):.1f})">'
             f'полоса {lane_h:.0f}</text>')
    # the leftover runs the whole length; mark it at the end rather than across it
    p.append(f'<line x1="{X(run):.1f}" y1="{Y(lane_h):.1f}" x2="{X(run)+14:.1f}" '
             f'y2="{Y(lane_h):.1f}" stroke="var(--rule)" stroke-width="0.9"/>')
    p.append(f'<line x1="{X(run)+10:.1f}" y1="{Y(lane_h):.1f}" x2="{X(run)+10:.1f}" '
             f'y2="{Y(roll):.1f}" stroke="var(--rule)" stroke-width="0.9"/>')
    p.append(f'<text x="{X(run/2):.1f}" y="{Y(roll)+26:.1f}" text-anchor="middle" '
             f'class="dim">по одной паре каждой полосы · на весь купол '
             f'{lf["roll_length_mm"]/1000:.1f} м рулона, а не '
             f'{lf["roll_unnested_mm"]/1000:.1f} м, если кроить всё в одну сторону '
             f'· сверху остаётся лента {roll-lane_h:.0f} мм по всей длине</text>')
    return svg(int(W), int(H), ''.join(p))




# ---------------------------------------------------------------------------
# 8. Cutting the bows: one bow unrolled, with what the joints have to dodge
# ---------------------------------------------------------------------------
CUT_ROWS = ['D4', 'D6', 'D8', 'D10']


def cut_svg():
    """Each size's typical bow, laid out straight and to one common scale.

    A bow is bent, so where it gets cut is an arc length -- and arc length is
    a straight line once the bow is unrolled. That is the frame the two rules
    are naturally stated in: no section longer than the transport limit, no
    joint within a sleeve of a crossing.
    """
    rows = [(n, DATA['cuts'][n]) for n in CUT_ROWS]
    longest = max(c['bow_mm'] for _, c in rows)

    # pad_r holds the overall-length label that sits past the end of the bar.
    W, pad_l, pad_r, pad_t = 1180, 184, 82, 40
    row_h, bar_h = 84, 26
    H = pad_t + row_h * len(rows) + 30
    scale = (W - pad_l - pad_r) / longest
    p = []

    for r, (name, cut) in enumerate(rows):
        pat = cut['patterns'][0]
        ex = pat['example']
        y = pad_t + r * row_h
        mid = y + bar_h / 2
        L = ex['length_mm']

        def X(mm):
            return pad_l + mm * scale

        # the bow itself
        p.append(f'<rect x="{X(0):.1f}" y="{y:.1f}" width="{L*scale:.1f}" '
                 f'height="{bar_h}" rx="2" fill="var(--panel-2)" '
                 f'stroke="var(--rule)" stroke-width="1"/>')

        # keep-out: a sleeve either side of every crossing, which is the band
        # a joint may not land in
        for t in ex['crossings_mm']:
            a, b = t - cut['sleeve_mm'], t + cut['sleeve_mm']
            p.append(f'<rect x="{X(max(0,a)):.1f}" y="{y:.1f}" '
                     f'width="{(min(L,b)-max(0,a))*scale:.1f}" height="{bar_h}" '
                     f'fill="{C["lashed"]}" fill-opacity="0.16"/>')
            p.append(f'<line x1="{X(t):.1f}" y1="{y:.1f}" x2="{X(t):.1f}" '
                     f'y2="{y+bar_h:.1f}" stroke="{C["unlashed"]}" '
                     f'stroke-width="1"/>')

        # the cuts
        for i, s in enumerate(ex['joints_mm']):
            nudged = abs(ex['moved_mm'][i]) > 0.5
            p.append(f'<line x1="{X(s):.1f}" y1="{y-7:.1f}" x2="{X(s):.1f}" '
                     f'y2="{y+bar_h+7:.1f}" stroke="{SPLICE_COL}" '
                     f'stroke-width="2"/>')
            p.append(f'<rect x="{X(s)-3.2:.1f}" y="{y-10.2:.1f}" width="6.4" '
                     f'height="6.4" transform="rotate(45 {X(s):.1f} {y-7:.1f})" '
                     f'fill="{SPLICE_COL}"/>')
            if nudged:
                p.append(f'<text x="{X(s):.1f}" y="{y+bar_h+20:.1f}" '
                         f'text-anchor="middle" class="dim" '
                         f'fill="{C['U']}">↔{abs(ex["moved_mm"][i]):.0f}</text>')

        # section lengths, written in the section they belong to
        edges = [0.0] + ex['joints_mm'] + [L]
        for i, length in enumerate(pat['sections_mm']):
            cx = (edges[i] + edges[i + 1]) / 2.0
            if (edges[i + 1] - edges[i]) * scale > 34:
                p.append(f'<text x="{X(cx):.1f}" y="{mid+4:.1f}" '
                         f'text-anchor="middle" class="mono-sm">{length:.0f}</text>')

        # the label
        label = f'{cut["alias"]} · {name}' if cut['alias'] else name
        p.append(f'<text x="{pad_l-14:.1f}" y="{y+11:.1f}" text-anchor="end" '
                 f'class="lbl-big">{esc(label)}</text>')
        p.append(f'<text x="{pad_l-14:.1f}" y="{y+25:.1f}" text-anchor="end" '
                 f'class="dim">{len(pat["sections_mm"])} секции · '
                 f'{pat["bows"]} из 15 дуг</text>')
        p.append(f'<text x="{X(L)+8:.1f}" y="{mid+4:.1f}" class="dim">'
                 f'{L/1000:.2f} м</text>')

    # one legend line, in the figure, because the bands need naming
    ly = pad_t + row_h * len(rows) + 4
    p.append(f'<rect x="{pad_l:.1f}" y="{ly-9:.1f}" width="13" height="13" '
             f'fill="{C["lashed"]}" fill-opacity="0.16"/>')
    p.append(f'<text x="{pad_l+19:.1f}" y="{ly+2:.1f}" class="dim">'
             f'зона пересечения — стык сюда не встаёт</text>')
    p.append(f'<rect x="{pad_l+290:.1f}" y="{ly-11:.1f}" width="2.4" height="17" '
             f'fill="{SPLICE_COL}"/>')
    p.append(f'<text x="{pad_l+301:.1f}" y="{ly+2:.1f}" class="dim">'
             f'рез · длины секций в мм</text>')
    p.append(f'<text x="{pad_l+520:.1f}" y="{ly+2:.1f}" class="dim" '
             f'fill="{C['U']}">↔ — стык сдвинут с ровного деления</text>')
    return svg(int(W), int(H), ''.join(p))




# ---------------------------------------------------------------------------
# 9. The cut list as a picture: how many sticks of each length
# ---------------------------------------------------------------------------
def cut_tally_svg(size='D4'):
    """Every section the dome needs, gathered by length.

    The cut sheet shows where one bow is sawn; this shows what comes off the
    bench at the end of it -- which is the thing you count before starting.
    """
    cut = DATA['cuts'][size]
    tally = {}
    for pat in cut['patterns']:
        for length in pat['sections_mm']:
            tally[length] = tally.get(length, 0) + pat['bows']
    rows = sorted(tally.items(), reverse=True)
    longest = max(tally)
    total = sum(tally.values())

    W, pad_l, pad_r, pad_t = 1180, 150, 210, 38
    row_h, bar_h = 62, 30
    H = pad_t + row_h * len(rows) + 26
    scale = (W - pad_l - pad_r) / longest
    p = []

    for i, (length, count) in enumerate(rows):
        y = pad_t + i * row_h
        col = LEAF_COLS[i % len(LEAF_COLS)]
        p.append(f'<rect x="{pad_l:.1f}" y="{y:.1f}" width="{length*scale:.1f}" '
                 f'height="{bar_h}" rx="3" fill="{col}" fill-opacity="0.20" '
                 f'stroke="{col}" stroke-width="1.5"/>')
        p.append(f'<text x="{pad_l-14:.1f}" y="{y+20:.1f}" text-anchor="end" '
                 f'class="lbl-big">{count} шт</text>')
        # Comma on the number only -- replacing in the whole tag would eat
        # the decimal points in the coordinates too.
        mm = f'{length:.1f}'.replace('.', ',')
        p.append(f'<text x="{pad_l+12:.1f}" y="{y+20:.1f}" class="mono-sm">'
                 f'{mm} мм</text>')
        # a run of ticks, one per piece, so the count reads as a quantity
        tx = pad_l + length * scale + 16
        for k in range(count):
            p.append(f'<line x1="{tx+k*6.5:.1f}" y1="{y+7:.1f}" '
                     f'x2="{tx+k*6.5:.1f}" y2="{y+bar_h-7:.1f}" '
                     f'stroke="{col}" stroke-width="2.4" stroke-linecap="round"/>')
        run = (f'{count} × {length/1000:.3f} м = '
               f'{count*length/1000:.1f} м').replace('.', ',')
        p.append(f'<text x="{pad_l+length*scale+16:.1f}" y="{y+bar_h+15:.1f}" '
                 f'class="dim">{run}</text>')

    label = f'{cut["alias"]} · {size}' if cut['alias'] else size
    in_sections = sum(l * c for l, c in tally.items()) / 1000.0
    summary = (f'{esc(label)} — {total} секций, {in_sections:.1f} м прутка в них; '
               f'дуга целиком {cut["bow_mm"]/1000:.2f} м').replace('.', ',')
    p.append(f'<text x="{pad_l:.1f}" y="{H-8:.1f}" class="lbl-sm">{summary}</text>')
    return svg(int(W), int(H), ''.join(p))


figs = {
    'sizes': sizes_svg(),
    'elevation': dome_view('elevation', 'family'),
    'plan': dome_view('plan', 'family'),
    'parts_callout': parts_callout(),
    'ladder': parts_ladder(),
    'gore': gore_svg(),
    'gore_roll': gore_roll_svg(),
    'faces': faces_svg(),
    'leaf': leaf_svg(),
    'leaf_roll': leaf_roll_svg(),
    'cuts': cut_svg(),
    'cut_tally_s': cut_tally_svg('D4'),
}
for k, v in figs.items():
    open(OUT + k + '.svg', 'w').write(v)
    print(k, len(v))
