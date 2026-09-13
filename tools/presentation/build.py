"""Build the project presentation: one self-contained HTML page, and a PDF.

Every number on the page comes from `stardome`; nothing is typed by hand. The
page is assembled from `template.html` by substituting two kinds of
placeholder:

    {{svg:name}}   the drawing `draw.py` wrote to <work>/svg/name.svg, inlined
    {{img:name}}   the render <work>/img/name.jpg, as a base64 data URI

Inlining the SVG rather than linking it is what lets the drawings pick up the
page's own theme tokens, so they follow light and dark with everything else.

    python3 tools/presentation/build.py
    python3 tools/presentation/build.py --work exports/presentation --pdf

Renders are pulled from exports/blender and exports/shots and squeezed to
JPEG on the way in -- the full-size PNGs are ~1.5 MB each and the whole page
has to stay comfortably under the 16 MB an artifact may be.
"""

from __future__ import annotations

import argparse
import base64
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# The renders the page uses, by the name the template calls them.
SHOTS = {
    'sizes': 'exports/blender/sizes.png',
    'camp': 'exports/blender/camp.png',
    'site': 'exports/blender/site.png',
    'portal': 'exports/blender/portal.png',
    'star_dome_d4': 'exports/blender/star_dome_d4.png',
    'star_dome_d6': 'exports/blender/star_dome_d6.png',
    'star_dome_d8': 'exports/blender/star_dome_d8.png',
    'star_dome_d10': 'exports/blender/star_dome_d10.png',
    'star_dome_d12': 'exports/blender/star_dome_d12.png',
    'star_dome_d6_plain': 'exports/blender/star_dome_d6_plain.png',
    'd6_doorway': 'exports/shots/d6_doorway.png',
    'd6_inside': 'exports/shots/d6_inside.png',
    'd6_plan': 'exports/shots/d6_plan.png',
    'd8_up': 'exports/shots/d8_up.png',
    'd10_approach': 'exports/shots/d10_approach.png',
}


def shrink(work: Path, quality: int = 62, longest: int = 1100) -> list:
    """Squeeze the renders to JPEG. `sips` ships with macOS; skip if absent."""
    out = work / 'img'
    out.mkdir(parents=True, exist_ok=True)
    missing = []
    for name, rel in SHOTS.items():
        src = ROOT / rel
        dst = out / f'{name}.jpg'
        if not src.exists():
            missing.append(rel)
            continue
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            continue
        subprocess.run(
            ['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(quality),
             '-Z', str(longest), str(src), '--out', str(dst)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    return missing


def assemble(work: Path, template: Path, out: Path) -> tuple:
    html = template.read_text(encoding='utf-8')
    missing = []

    def svg(m):
        p = work / 'svg' / f'{m.group(1)}.svg'
        if not p.exists():
            missing.append('svg:' + m.group(1))
            return ''
        return p.read_text(encoding='utf-8')

    def img(m):
        p = work / 'img' / f'{m.group(1)}.jpg'
        if not p.exists():
            missing.append('img:' + m.group(1))
            return ''
        return 'data:image/jpeg;base64,' + base64.b64encode(p.read_bytes()).decode()

    html = re.sub(r'\{\{svg:([a-z0-9_]+)\}\}', svg, html)
    html = re.sub(r'\{\{img:([a-z0-9_]+)\}\}', img, html)
    out.write_text(html, encoding='utf-8')
    return missing, re.findall(r'\{\{[^}]+\}\}', html), len(html.encode())


CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def to_pdf(page: Path, pdf: Path) -> bool:
    if not Path(CHROME).exists():
        return False
    subprocess.run(
        [CHROME, '--headless', '--disable-gpu', '--no-sandbox',
         f'--print-to-pdf={pdf}', '--no-pdf-header-footer',
         '--virtual-time-budget=15000', page.as_uri()],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--work', default='exports/presentation',
                    help='where the figures, images and page are written')
    ap.add_argument('--template', default=str(HERE / 'template.html'))
    ap.add_argument('--pdf', action='store_true', help='also print a PDF')
    ap.add_argument('--skip-figures', action='store_true',
                    help='reuse the figures already in <work>/svg')
    args = ap.parse_args()

    work = (ROOT / args.work) if not Path(args.work).is_absolute() else Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    if not args.skip_figures:
        subprocess.run([sys.executable, str(HERE / 'extract.py'), '--work', str(work)],
                       check=True, cwd=ROOT)
        subprocess.run([sys.executable, str(HERE / 'draw.py'), '--work', str(work)],
                       check=True, cwd=ROOT)

    absent = shrink(work)
    if absent:
        print('renders not found (run the Blender scenes first):')
        for rel in absent:
            print('  ', rel)

    page = work / 'star-dome.html'
    missing, leftover, size = assemble(work, Path(args.template), page)
    print(f'{page}  ({size/1e6:.2f} MB)')
    if missing:
        print('missing pieces:', ', '.join(sorted(set(missing))))
    if leftover:
        print('unresolved placeholders:', ', '.join(sorted(set(leftover))))

    if args.pdf:
        pdf = work / 'zvyozdny-kupol.pdf'
        if to_pdf(page, pdf):
            print(f'{pdf}')
        else:
            print('no Chrome found; open the HTML and print to PDF instead')
    return 1 if (missing or leftover) else 0


if __name__ == '__main__':
    raise SystemExit(main())
