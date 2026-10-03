# 0030. Let Bambu Studio arrange the plates

- **Status:** accepted
- **Date:** 2026-10-03
- **Where it lives:** `tools/print_plates.py`, `connectors/generate_clamps.py`,
  each generator's `FLIPPED_PIECES`, [`printing.md`](../printing.md)

## The decision

`make prints` writes Bambu Studio projects: one `.3mf` with every printed piece
of a dome at its count, arranged onto plates, and one per part with a single
set. The arranging is done by Bambu Studio's own command line, from turned
STLs and the printer's system preset. Every generator now declares which of its
pieces print upside down, and `make clamps` writes that into a manifest beside
the meshes, so the print export reads it instead of rebuilding anything.

It replaces `connectors/print_sheet.py`, which rebuilt the base hub in FreeCAD,
packed it onto beds with a shelf packer and wrote each bed as one STL.

## Why

The bed STLs were one mesh per bed. A slicer reads a mesh as one object, so the
pieces on it could not be counted, moved or left out without splitting it
first, and a dome's worth was a folder of STLs to drag in one at a time and
multiply by hand. A `.3mf` carries separate named objects and multiple plates,
and opening it is the whole job.

It also covered only the base hub. The fan nodes, clamps, collars and
ferrules — 164 of S's 212 prints — had no print export at all.

## What was rejected

- **Writing the plates ourselves.** A 3MF with objects is easy to write; a
  Bambu project with plates is the vendor's format, and getting it wrong means
  pieces landing between plates. The command line writes the same file the GUI
  saves, so it is right by construction.
- **Keeping the shelf packer and feeding its beds to Bambu.** Bambu's arrange
  packs tighter than a shelf packer and knows the printer's excluded areas.
- **Grouping the dome project by part type, a plate set per part.** Fewer
  plates won: S packs into 12 mixed plates. The per-part projects are there for
  printing a part on its own.

## What it costs

- **`make prints` needs Bambu Studio installed** and reads its system presets
  from the user's profile folder. Without it, `--stl-only` still writes the
  turned STLs. The command line does not resolve a preset's `inherits` chain
  itself — given the P2S preset as it stands it fell back to a 200 × 200
  plate — so the script folds the chain in.
- **Plates are mixed.** A failed plate is several kinds of piece, named in the
  object list rather than obvious from the plate number.
- **`make prints` needs `make clamps` first**, because the manifest is written
  there. It used to rebuild the hub itself and so did not.
- **The crossing clamp's cap is no longer printed upside down.** Its document
  said it should be, from an earlier version of the overhang check; the current
  check prefers it as drawn, 71 mm² steeper than 45° against 414, and both its
  faces are flat. `crossing-clamp-v1.md` is corrected.
