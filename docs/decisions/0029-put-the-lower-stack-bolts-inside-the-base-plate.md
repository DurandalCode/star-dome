# 0029. Put the lower stack bolts inside the base plate

- **Status:** accepted
- **Date:** 2026-09-27
- **Where it lives:** `connectors/base_hub_v1.py`

## The decision

The lower two stack-bolt holes sit inside one broad flange shared by every
plate of the base hub. The flange grows from the hub disc and encloses both
holes and their surrounding material. The upper bolt positions and the angle
wrap remain as in [0028](0028-join-the-wrap-ears-and-add-upper-stack-bolts.md).

## Why

The lower pair introduced as two round bosses joined to the hub by narrow
radial webs. The top view exposed those necks as the weak-looking part of the
plate. A continuous flange carries the holes within the plate outline, like
the upper pair, without a local transition from a web to a circular ear.

## What was rejected

- Keeping the narrow radial webs under the lower bosses. Although FreeCAD
  reported one solid, the material between each boss and the hub was locally
  narrow and did not match the intended integrated plate outline.

## What it costs

The flange uses more plastic. On M, `BASE3-10` grows from about 303 to
324 cm³ and `BASE2-10` from about 218 to 228 cm³. Across ten base hubs this
adds about 184 cm³ of solid part. The four M5 stack bolts and assembly actions
are unchanged.

FreeCAD's solid, interference and printability checks pass for both base-hub
families at the S and M rod sizes. This is a geometric result, not a strength
validation of the printed joint.
