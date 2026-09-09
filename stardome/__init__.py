"""Star Dome parametric geometry.

This package is the geometric source of truth for the Star Dome family. It
computes rod centrelines, crossings, node topology and derived dimensions
from the named variants in ``configs/variants.toml``, and serialises them to
a versioned ``model.json`` that every downstream consumer reads:

    OpenSCAD  -- viewer for the generated geometry
    FreeCAD   -- connector generation, driven by the real crossing angles
    Blender   -- 1:1 site composition and clearance checks

Downstream consumers must never recompute geometry themselves.

All dimensions are in millimetres, all angles in degrees.
"""

__version__ = "0.1.0"

SCHEMA_VERSION = 1
