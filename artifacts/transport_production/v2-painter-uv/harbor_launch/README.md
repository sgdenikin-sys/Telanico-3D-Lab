# harbor_launch — V2 Painter UV

Geometry, pivots and animation actions are unchanged from V1. This is a separate
painting source, NOT installed in the live game. Old V1 UVs do not match these maps.

Two atlases, both on UV0, selected by material prefix (MAIN__ / TRIM__):
- MAIN: 2048×2048, hull/walls, roof, glass, doors and interior furnishings.
- TRIM: 2048×2048, continuous metal wraps, rails, frames and hardware.
- Shared physical density: 94.18 pixels/m. Unique UVs, no stacked duplicates.

`main_layout.png` / `trim_layout.png`: clean transparent ISLAND BOUNDARIES.
`main_wire.png` / `trim_wire.png`: full native Blender SVG export rasterized to PNG.
`main_guide.png` / `trim_guide.png`: exactly the same coordinates, chart IDs and colors.
`main_key.png` / `trim_key.png`, `surface_mapping.csv`: names and face correspondence.
`main_paint.png` / `trim_paint.png`: blank white painting canvases at correct size.
`main_checker.png` / `trim_checker.png`: temporary chart-ID checker diagnostics.
`mapping_exterior.png` / `mapping_interior.png`: actual mapped Blender renders.
`harbor_launch.blend` / `harbor_launch.glb`: models that MATCH these UVs.

Paint on a separate layer using layout/guide as a locked reference. Hide all guide
and checker layers before saving the painted atlas; never resize or move islands.
In Blender connect the matching PAINT_ATLAS image node Color to Principled Base Color.
The image nodes are deliberately unconnected to preserve the approved PBR appearance.
For opacity keep the original glass Alpha values; for Godot use white albedo tint
when assigning a full-color atlas. Every material records `paint_atlas` in extras.

MAIN and TRIM coordinates may coincide because they are DIFFERENT images/materials.
There is no overlap within either sheet. Keep the original dimensions and padding.
Roof remains separately selectable; Doors_Open and Doors_Close remain separate clips.
`checks.json` records geometry identity and UV checks; no gameplay regression.
