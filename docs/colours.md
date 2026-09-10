# Colours and transparency

A rod should be the same colour whichever tool it is looked at in. Blender and
FreeCAD do not share code — the scene builders are consumers of `model.json`,
the connector scripts run inside FreeCAD — so the palette is repeated in both,
and this file is where it is agreed rather than inferred.

## The palette

| | RGB | where |
|---|---|---|
| **G family** | `0.15, 0.55, 0.95` blue | the icosidodecahedral skeleton |
| **U family** | `0.95, 0.45, 0.10` orange | upper thirds-marked family |
| **L family** | `0.20, 0.75, 0.35` green | lower thirds-marked family |
| lashed node | `0.95, 0.15, 0.25` red | the ten four-rod nodes |
| unlashed crossing | `0.55, 0.55, 0.60` grey | the thirty two-rod crossings |
| base point | `0.25, 0.25, 0.30` dark grey | the ten feet |
| skirt | `0.72, 0.72, 0.70` light grey | posts and both rings |
| skirt diagonal | `0.35, 0.62, 0.78` pale blue | **tension**, not rod — see below |
| doorway | `1.00, 0.78, 0.10` amber | the opening and its outline |
| doorway jamb | `1.00, 0.42, 0.05` deep orange | the rods that frame a lancet |
| cut away | `0.90, 0.10, 0.10` red | a piece removed, drawn as a ghost |

The three family colours are the load-bearing ones. Everything else is a label.

## Transparency

Transparency says *what you are meant to see past*, and it is used for exactly
three things.

**A connector's plates are translucent, its rods are not.** The question a
connector drawing answers is where each rod sits in the stack, so the rods are
solid and the part is 55% see-through. Plates carry a light-to-dark ramp from
bottom to cap, so the stacking order reads without selecting anything.

**A removed piece is a red ghost at 50%.** A doorway whose price is invisible
looks free. Use `--hide-cuts` for a picture of the thing as built rather than
of the decision — `make camp` does.

**The doorway panel is 16% amber.** It marks a hole; anything more opaque reads
as a surface, which is the opposite of what it is.

## Family colour or per-rod colour

Both are right, in different places.

Use the **family** colours wherever what matters is which family a rod belongs
to: every Blender scene, and the base hub, whose three arms are one L, one U
and one G.

Use **distinct per-rod** colours where what matters is telling four rods apart
in a stack: the four-rod node is G-U-U-G, so family colours would give it two
identical pairs and lose exactly the thing the drawing is for.

## Getting colours into a saved FreeCAD document

`ViewObject` is `None` when `FreeCAD.GuiUp` is 0, which is what `freecadcmd`
runs as. `FreeCADGui` still *imports* there, so guarding on the import passes
and the colouring then silently does nothing — that is why the parts came out
grey for a while.

So a document generated headlessly carries geometry and no appearance. Colour
it with the GUI up, which is what the FreeCAD MCP bridge gives:

```python
# through the MCP bridge, against the open document
for obj in doc.Objects:
    view = getattr(obj, "ViewObject", None)
    if view is None:
        continue
    ...
doc.save()
```

`apply_view` in each connector script does the same and is a no-op headless.

When the bridge is down, the GUI will run a script given on its command line,
which is the same thing without the bridge:

```
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD colour_it.py
```

Two things to know. That path is a wrapper which execs
`Resources/bin/freecad`, so `pgrep -f MacOS/FreeCAD` finds nothing and the run
looks like it died — match on `bin/freecad` instead. And `Console.PrintMessage`
goes to the report view, not to stdout, so a script that reports its results
has to write them to a file if you want to read them back.

Colours are checked by reading them back off the objects, not out of the saved
file: FreeCAD 1.x keeps `ShapeColor` in a `ShapeAppearance` material list,
written as separate binary members of the `.FCStd` zip. `Transparency` is
still plain XML, so it greps and the colour does not — an easy way to conclude
the colouring silently failed when it did not.

## Where these are defined

`blender/build_scene.py` and `blender/build_site.py` at the top;
`connectors/fan_node_v2.py`, `connectors/base_hub_v1.py` and
`connectors/splice_v1.py` above their `apply_view`. Five copies,
deliberately: the two Blender scripts run inside Blender's interpreter and the
three connector scripts inside FreeCAD's, and neither can import from
`stardome/`. Change one, change this table, change the rest.

Two greys are easy to swap and mean opposite things: `0.55, 0.55, 0.58` is
**bought steel** — bolts, and nothing else — while a part *you make* is a blue
at 55%. The splice had them the wrong way round for a commit.

## One hue, two values

Where several members are the same kind and the drawing is about how they sit
relative to each other, ramp one hue rather than reaching for a second: the
base hub's four plates go light to dark bottom to cap, and the splice's two
rod sections take a light and a dark of the G blue. Both are one bow and one
family — a second hue would say they were not.
