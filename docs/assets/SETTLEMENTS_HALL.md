# Settlements Hall — standalone landmark asset

Editable, procedural architecture based on the owner's supplied concept: a
blue ribbed dome above a circular colonnaded hall, matching side wings, ivory
stone, restrained brass, arched glazing, double entrance doors, seven stairs,
blue flags and a simplified paved forecourt. This adds an asset and optional
inspection scenes; it does not replace the overworld building or alter gameplay.

## Generate and inspect

Run from the repository root using the existing Blender installation:

```sh
blender -b --python-exit-code 1 --python blender/scripts/build_settlements_hall.py -- --render
```

Omit `--render` for a fast asset-only build. `--views hero front rear detail`
selects review cameras. Rendering uses CPU Cycles without a denoiser or add-ons.
Default generated files remain ignored by Git, following the existing workflow:

| File | Purpose |
| --- | --- |
| `blender/generated/settlements_hall/settlements_hall.blend` | Editable authoring scene with seven named architectural collections, linked modules, UV0, PBR materials, review cameras and studio lighting |
| `godot/assets/generated/settlements_hall.glb` | Engine asset, material-batched to 11 mesh surfaces; excludes studio, cameras and lights |
| `blender/generated/settlements_hall/{hero,front,rear,detail}.png` | CPU-rendered review images |
| `blender/generated/settlements_hall/asset_stats.json` | Authoring geometry and dimension report |
| `blender/generated/settlements_hall/glb_validation.json` | Actual exported geometry/material check |

Use `--output-dir PATH` to put the blend, GLB, statistics and renders in a single
delivery directory instead of the default paths. The build intentionally resets
the scene: save hand edits under a different filename before regenerating.

To export hand edits **without rebuilding**, retain the numbered architectural
collections and one material per part, then run:

```sh
blender -b path/to/edited.blend --python-exit-code 1 --python blender/scripts/export_settlements_hall.py -- --output path/to/edited.glb
```

That exporter preserves added/deleted parts and material edits, evaluates
modifiers, batches by material, and omits the studio. New parts need a UV0 layer.
UV0 uses metre-based box projection as a practical editable texturing baseline;
it is not a unique baked lightmap atlas. Generate UV2 in Godot if baking lighting.

## Asset contract

| Property | Result |
| --- | --- |
| Blender / tested Godot | 4.3.2 / 4.6.3 stable |
| Exported triangles | 34,473, including flags and optional forecourt |
| Authoring objects / unique meshes | 814 / 469 |
| Runtime meshes / PBR materials | 11 / 11 |
| GLB size | Approximately 1.93 MB, uncompressed, self-contained |
| Dimensions | 23.9 m wide × 15.9 m deep × 16.47 m high |
| Origin / units | Ground plane below the rotunda centre; 1 unit = 1 metre |
| Front axis | Blender −Y; glTF/Godot +Z; Godot Y is up |
| Stair geometry | Seven 170 mm rises, 310 mm treads; plaza top 0.24 m, landing 1.43 m |
| Entrance frame clearance | Approximately 1.99 m wide, 4.155 m to the arch apex; monumental double doors |
| Dome | 64 radial segments, 16 vertical intervals, smooth shading; 12 modeled brass ribs |

The upper end of the permitted triangle budget is used for the curved cornices,
24 classical columns, real arch openings and frames, clerestory, shaped roofs
and readable dome ribs. The fully built rear and side elevations support orbiting
views. Small ornament, landscaping, tile relief and interiors are omitted.
No 3D meshes or textures were downloaded; geometry is original procedural work
derived from the supplied visual reference.

Eleven plain Principled materials export as standard metallic/roughness PBR:
warm ivory limestone, recessed sandstone, deep petrol blue metal, aged brass,
dark bronze frames, alpha-blended blue glass, painted blue doors, rough blue
fabric, pale paving, a restrained paving variant, and interior shadow wells.
Glass alpha is 0.63. Fabric is double-sided. No transmission/refraction,
screen-space effects, procedural shader dependency or external texture is needed.
Godot 4.6.3 imports glass with its alpha depth prepass, preserving partial alpha.

The `.blend` keeps the platform in its own removable collection. If removing it,
place the building on a host surface at 0.24 m or lower the remaining architecture
by 0.24 m. The GLB merges source parts by material for runtime efficiency; edit
the `.blend` when moving individual architectural modules.

## Godot use

Generate the GLB, then open the existing `godot/project.godot`. The main scene and
renderer settings remain unchanged. Optional scenes:

- `res://scenes/assets/settlements_hall.tscn`: an instanceable landmark wrapper
  with five inexpensive building collision primitives. Remove or disable the
  `OptionalBuildingCollision` body if the host scene owns collisions.
- `res://scenes/assets/settlements_hall_preview.tscn`: a separate inspection
  scene, with orbit/zoom controls and ordinary Compatibility lighting and sky
  reflections. Run this scene directly; do not change the game's main scene.

Maintain scale 1 for a 1.8 m character. This is an exterior landmark with closed,
static doors and static modeled flags. It contains no navigable interior, opening
animation, navigation mesh or walkable floor/stair colliders. Those depend on
the host game's interaction and navigation design. The coarse building body
intentionally treats the building as solid. No automatic map placement occurs.

## Verification performed

```sh
python tools/validate_settlements_hall.py --json blender/generated/settlements_hall/glb_validation.json
godot --headless --path godot --editor --import
godot --headless --path godot --script ../tools/check_settlements_hall.gd
```

The actual Godot check used an isolated scratch project with the same 4.6.3
binary, Compatibility settings, GLB, wrapper, preview script and scenes, so it
did not import or rebuild the rest of the game. Results:

- GLB header, triangle budget, UV0, normalized normals, finite coordinates,
  identity transforms, geometry dimensions, all 11 materials and zero-area
  triangle check passed. No degenerate triangles.
- Godot imported and instantiated 11 StandardMaterial3D surfaces and 34,473
  triangles; tinted alpha glass, double-sided fabric and five colliders passed.
- The standalone preview initialized with `renderer=gl_compatibility` in
  headless mode. This validates scene/script startup, not GPU-rendered pixels.
- Reopened the saved `.blend`, exported through the hand-edit exporter and ran
  the same GLB geometry/material validator successfully.
- Reviewed front, rear, entrance detail and three-quarter CPU Blender renders.

No full game/Web export or browser/device pass was run. This environment has no
installed Web export template or local display server; no tools were installed.
The Godot editor's headless import also logged its restricted TCP-listen startup
warning, while scene import and the separate runtime checks completed.
Web/Compatibility suitability here is supported by the core PBR feature set and
Godot import checks; physical iPhone performance has not been measured.
