# The project presentation

One self-contained HTML page covering the range, the parts and where they sit,
the cover patterns, and the tables — plus a PDF of the same thing.

```bash
python3 tools/presentation/build.py --pdf
```

Writes `exports/presentation/star-dome.html` and `zvyozdny-kupol.pdf`. The page
carries its own images and drawings inline, so the one file is the whole
deliverable — mail it, or open it and print.

## How it is put together

| | |
|---|---|
| `extract.py` | snapshots `stardome` into `exports/presentation/model.json` |
| `draw.py` | draws the SVG figures from that snapshot |
| `template.html` | the page, with `{{svg:name}}` and `{{img:name}}` holes in it |
| `build.py` | runs the first two, squeezes the renders, fills the holes |

Nothing on the page is typed by hand — every number comes back through
`model.json`, so a change in `configs/variants.toml` reaches the presentation
by rebuilding it.

The drawings are **inlined**, not linked. That is what lets them read the
page's own CSS variables and follow it into dark mode; a linked `<img>` would
be stuck in one theme. Structural colours (the G/U/L families, node kinds) are
literal hex from [`docs/colours.md`](../../docs/colours.md), so a bow is the
same blue here as in a Blender render.

## What it needs

The Blender renders, already in `exports/blender/` and `exports/shots/` — the
build lists any it cannot find and carries on without them. `sips` (macOS) to
squeeze them, and Chrome for `--pdf`; without Chrome, open the page and print.

The text is in Russian. It is the one place in this repo that is, because it is
the thing shown to people rather than read by the toolchain.
