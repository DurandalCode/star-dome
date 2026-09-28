# AI workflow for FreeCAD connector changes

This guide records the failure modes exposed while revising the base hub. It
supplements `AGENTS.md`; the source of truth and design decisions remain where
that file assigns them.

## Understand the request before changing geometry

1. Identify the exact part ID and variant. `BASE3-10` is the three-arm foot;
   `BASE2-10` is the two-arm doorway foot. A successful check of one does not
   cover the other.
2. Name the physical piece and load path. The angle wrap (`Plate_Wrap`) has
   its own M8 bolt ears. The M5 stack bolts pass through the plate stack. The
   upper and lower pairs solve different placement problems. Refer to
   [0028](decisions/0028-join-the-wrap-ears-and-add-upper-stack-bolts.md) and
   [0029](decisions/0029-put-the-lower-stack-bolts-inside-the-base-plate.md).
3. Treat a correction from the user as a change to the specification. In this
   case the wrap ears were meant, the extra bolts were meant to pass through
   the upper plate stack, and the lower stack holes needed a broad flange
   integrated into every plate. Do not return to an earlier interpretation.
4. Check the top, side and assembly views. One valid solid can still have a
   narrow neck or a collision hidden by overlapping shaded parts. Verify the
   wrap and each manufactured plate as one valid solid, the relevant hole
   clearances, and the print orientation. CAD validity alone is not a strength
   claim.

## Generate and verify the deliverable

1. Change the generator in `connectors/` and the connector schedule in
   `stardome/` when needed. Generated files in `exports/connectors/` are
   deliverables, not the source to edit by hand as the final fix.
2. Rebuild the affected variants and check the generator's solid,
   interference and printability report. Run `make check` before reporting a
   geometric result as true.
3. Open the **exact newly generated `.FCStd`** in graphical FreeCAD. Confirm
   that the document stays open, the expected plates appear in the tree and
   in the 3D view, reference rods and steel have the intended visibility, and
   the app remains responsive after `fitAll` and a view change. For a base-hub
   edit, inspect both `BASE2` and `BASE3` at the affected rod sizes.
4. A ZIP integrity check, `Shape.isValid()`, STEP/STL export, and `make check`
   do not establish that a `.FCStd` opens and displays in FreeCAD. Report
   those checks separately. Say "fixed" only after the graphical check of
   the file the user will open.

## If FreeCAD fails to open a file

1. Preserve the failing file and record its exact path, part ID and FreeCAD
   version. Reproduce with that file in a fresh FreeCAD session. Avoid opening
   copies of the same document together when comparing them; duplicate
   document identities can themselves end the session.
2. Isolate the failure: compare the `.FCStd` archive entries (`Document.xml`,
   `GuiDocument.xml`, BREP shapes and shape maps) against a known opening
   copy. Change one class of data at a time in a temporary copy and open it
   alone. Headless loading tests document data; graphical loading also tests
   the view providers and tessellation.
3. Keep synthetic `GuiDocument.xml` minimal. The headless generator needs
   visibility records so manufactured pieces appear and references stay
   hidden. In this incident, adding hand-written `Transparency` properties
   broke opening `BASE2-10` while the BREP shapes stayed identical. A copy
   with those properties removed opened with all four manufactured pieces
   visible.
4. Fix the generator, regenerate the deliverable, then repeat the graphical
   check. Do not present a temporary archive edit as the durable repair.

When reporting a result, identify the exact file opened, the checks that
passed, and any remaining physical validation. A FreeCAD view establishes
geometry and usability of the CAD file, not the printed joint's strength.
