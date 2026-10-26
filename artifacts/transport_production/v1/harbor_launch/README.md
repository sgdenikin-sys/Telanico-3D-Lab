# harbor_launch

Standalone editable original VorGun derivative, meters/Z-up Blender, Y-up glTF.

- `harbor_launch.blend`: separate named components, real interior and removable `ROOF_removable` collection.
- `harbor_launch.glb`: standalone PBR, independent hinged doors; `Doors_Open` / `Doors_Close`, 1 second at 30 fps.
- `uv_layout.svg`: native Blender UV0 export.
- `uv_layout.png`: exact native SVG rasterized at 2048², transparent background (no GPU needed).
- `uv_guide.png`: color/ID annotation on exactly the same island coordinates.
- `model_to_uv.png`: actual atlas applied temporarily to model, for painting correspondence.
- `surface_mapping.json`: exact object IDs, semantic regions, polygon indices and UV coordinates.
- `isometric.png`, `interior_doors_open.png`: actual Blender renders.
- `checks.json`: measured geometry, UV and exported animation checks.

Atlas regions are labeled by function. Every face has its own intentionally separated
planar island, allowing all interior/exterior surfaces to be painted without overlap.
Uniform physical texel density; minimum 4 px separation at 2048². Small bevel islands
can share their region's base color when painted. No final texture painting.

The saved Blend opens with NLA tracks muted to show closed doors. Unmute ONLY the
chosen `Doors_Open` OR `Doors_Close` track on each hinge when previewing. Both tracks
are exported as separate synchronized glTF clips. The roof is removable, not animated.
The inspection ground/lights/camera are excluded from GLB export.

Reference: `docs/assets/VORGUN_VISUAL_REFERENCES_FOR_3D_BATCH.md`;
original `courier_mini_launch.png`.
Rebuild with `blender -b -t 8 --python-exit-code 1 --python blender/scripts/build_transport_production.py -- --asset harbor_launch`.
No game integration, asset overwrite or deployment.
