# Project architecture

The project deliberately separates three modelling concerns.

## 1. Structural geometry — OpenSCAD

OpenSCAD generates the mathematical Star Dome family and reinforcement experiments.

Expected outputs:
- rod/tube geometry for visual inspection;
- named variants (D4, D6, D8, D12);
- intersection metadata where practical;
- exportable mesh for Blender.

## 2. Manufactured parts — FreeCAD

FreeCAD is used for parts that must be printed or dimensioned precisely:
- crossing clamps;
- base/anchor interfaces;
- belt clips;
- corridor/entrance transition parts.

These parts should be parametric around rod diameter and print clearance.

## 3. Composition and ergonomics — Blender

Blender is the assembly and site-layout environment.

The Blender scene should use actual generated dome geometry, not generic hemispheres, because entrances and corridors must be checked against real rod positions.

Typical checks:
- can a 1.8–2.2 m tall opening fit between structural members;
- does a corridor intersect rods or covers;
- human-scale circulation around dome edges;
- visual and practical composition of several domes.

## Data flow

```text
configs -> OpenSCAD -> generated dome mesh -> Blender
                         |
                         +-> intersection/angle data -> FreeCAD connectors

FreeCAD connector exports ---------------------------> Blender (optional visual integration)
```

## Cost constraint

The baseline stack must not require paid CAD subscriptions or paid cloud rendering/CAD APIs. The intended external paid capability is limited to whatever Claude Code / Codex access the user already has.
