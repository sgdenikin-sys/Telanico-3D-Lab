# Settlements Hall — animated standalone asset

A procedural landmark based on the supplied concept: ribbed blue dome, circular
colonnade, symmetrical wings, ivory limestone, brass, arched glass, entrance
stairs and blue banners. The architecture and 11 materials are preserved from
the original delivery. The corrected version adds hinged double doors and four
lightweight animated fabric pieces. It does not alter or redeploy the game.

## Persistent downloads and previews

The Release REST API and CLI returned `Forbidden`; the connected GitHub tools
have no Release-upload operation. The owner explicitly authorized a repository
fallback, so the actual binaries and images are published here:

- [Animated package, four-image gallery, demonstration and reports](../../artifacts/settlements_hall/v2-animated/README.md)
- [Original static archive and four original images](../../artifacts/settlements_hall/v1-static/README.md)

Use the ZIP link on the gallery page to download the editable `.blend`, `.glb`,
four PNGs, MP4/GIF demonstration, reports, source and a self-contained Godot
inspection project. The repository is private: sign in with repository access.
SHA-256 checksums accompany each published delivery. These paths are outside
`site/` and the game publication workflow's path filters.

## Generate, edit and export

From the repository root, with the existing Blender installation:

```sh
blender -b --python-exit-code 1 --python blender/scripts/build_settlements_hall.py -- --render
```

Omit `--render` for an asset-only build. `--views hero front rear detail` chooses
review cameras. CPU Cycles needs no GPU, denoiser, add-ons or external textures.
`--output-dir PATH` puts all generated files together. Default output paths:

| Path | Contents |
| --- | --- |
| `blender/generated/settlements_hall/settlements_hall.blend` | Seven named architectural collections; linked modules; separate door hinges and leaves; four deforming cloth objects; editable NLA actions, UV0, PBR materials, cameras and studio |
| `godot/assets/generated/settlements_hall.glb` | Static material batches plus separate animated components and all four clips |
| `blender/generated/settlements_hall/{hero,front,rear,detail}.png` | Closed-pose review renders |
| `blender/generated/settlements_hall/*validation.json` | Actual GLB and Godot verification results |

Regeneration resets the scene. Save hand edits under a separate filename and
export them without rebuilding:

```sh
blender -b path/to/edited.blend --python-exit-code 1 --python blender/scripts/export_settlements_hall.py -- --output path/to/edited.glb
```

Retain the numbered collections, hinge parenting, `motion_group` properties and
NLA track names. Rigid authoring parts use one material each; the four cloth
objects intentionally have two materials and shape keys. The exporter batches
rigid moving parts only within their own leaf/hinge. It preserves cloth morphs
and animation tracks and excludes the studio. New parts need UV0. UV0 uses
metre-based projection; it is not a unique baked lightmap atlas. Generate UV2
in Godot if the host scene uses baked lighting.

## Geometry, scale and materials

| Property | Corrected asset |
| --- | --- |
| Tested Blender / Godot | 4.3.2 / 4.6.3 stable |
| Triangles | **34,643**, including cloth and platform; only 170 more than the original |
| Authoring objects / unique meshes | 798 / 453 |
| Runtime meshes / material surfaces | 18 / 22 |
| Shared PBR materials | 11, unchanged |
| GLB | Approximately 2.09 MB, self-contained |
| Dimensions | 23.9 m wide × 15.9 m deep × 16.47 m high |
| Origin / units | Rotunda centre at ground level; 1 unit = 1 metre |
| Facing | Blender −Y; Godot +Z; Godot Y is up |
| Stairs | Seven 170 mm rises and 310 mm treads; landing 1.43 m, plaza 0.24 m |
| Door leaves | Approximately 0.95 m wide each and 2.645 m high, under a fixed arched fanlight |
| Dome | 64 radial segments, 16 vertical intervals, 12 modeled brass ribs |

The upper triangle allowance supports the circular cornices, 24 columns, real
arch openings, clerestory, shaped roofs and dome ribs. No added cloth subdivision
modifiers, armature, simulation cache or heavy texture payload is required. Only
the small hanging pennants received a restrained 4×4 cloth grid. No third-party
meshes or textures were downloaded.

Materials remain plain metallic/roughness PBR: warm ivory limestone, sandstone,
petrol blue roofing metal, aged brass, dark bronze, tinted alpha glass, blue
painted doors, blue fabric, two pale paving variants and interior shadow wells.
Glass alpha remains 0.63; fabric is double-sided. No transmission, refraction,
procedural-only shader or screen-space effect is required.

The platform can be removed separately in Blender. Then place the remaining
building on a surface at 0.24 m, or lower it by 0.24 m. Preserve scale 1 for a
1.8 m character; placement in the existing overworld is deliberately separate.

## Animation contract

| GLB clip | Godot imported name | Duration | Tracks / behavior |
| --- | --- | --- | --- |
| `Doors_Open` | `Doors_Open` | 1 s | Two independent hinge rotations, outward from 0° to 100° |
| `Doors_Close` | `Doors_Close` | 1 s | Two hinge rotations returning to 0° |
| `Flags_Wind-loop` | `Flags_Wind` | 4 s, looping | Morph weights on four separate fabric meshes |
| `Hall_Demo-loop` | `Hall_Demo` | 4 s, looping | Open, pause, close, pause; wind throughout |

The double doors have separate vertical pivots at their outer edges. Their blue
panels, brass insets, handles and meeting stiles move together. The fixed fanlight
and architectural frame remain fixed. These are exterior doors opening onto a
shadowed reveal, with no modeled or navigable interior.

Each roof flag and entrance pennant has three small relative morph targets.
The cloth, hems and insignia deform together. Roof flags stay pinned to their
pole-side edge; entrance pennants stay pinned at the top. The 4-second clip
contains two travelling-wave cycles with matching endpoint weights. This is
portable glTF morph animation, not a Godot-only shader or runtime cloth solver.
Godot recognizes the `-loop` suffix and imports both looping clips as linear loops.

In Blender, play frames 1–121 at 30 fps. `Hall_Demo-loop` NLA tracks are active;
the separate open, close and wind tracks are stashed/muted for export. All named
NLA tracks are preserved by the GLB exporter.

## Godot integration and verification

Generate or unpack the asset, then run the optional inspection scene directly:

- `res://scenes/assets/settlements_hall.tscn`: instanceable wrapper with five
  optional coarse building colliders and independent door/wind controls.
- `res://scenes/assets/settlements_hall_preview.tscn`: orbit/zoom inspection and
  automatic combined demo. **O** opens, **C** closes, **D** plays the combined
  demo; **F/R** select front/rear views.
- Wrapper methods: `open_doors()`, `close_doors()`, `play_demo()`.

Godot adds constant door-rest tracks to the imported wind clip. The wrapper
copies just its blend-shape tracks into a separate wind AnimationPlayer, so wind
cannot reset an opening door. This independent playback is explicitly tested.
The imported GLB itself retains all named clips and the two hinge nodes. There
are no floor/stair navigation colliders or walkable interior; those depend on
the host scene. The optional building body still treats the landmark as solid.

Executed checks use an isolated scratch project with the same Godot 4.6.3 binary
and Compatibility settings, without importing/building the game:

```sh
python tools/validate_settlements_hall.py --json blender/generated/settlements_hall/glb_validation.json
godot --headless --path godot --editor --import
godot --headless --path godot --script ../tools/check_settlements_hall.gd -- path/to/godot_animation_validation.json
```

The GLB validator checks the triangle budget, finite geometry, UV0, normalized
normals, zero-area triangles, all materials, hinge hierarchy, morph targets,
clip/channel membership, 100° quaternion motion, durations and matching loop
endpoints. Godot reimport and actual AnimationPlayer playback verify:

- Both leaves rotate **99.99999°** and close to their original pose.
- All four fabric meshes retain three blend shapes and changing weights.
- Loop endpoints match, and both suffix-marked clips import with looping enabled.
- Door and wind players advance concurrently without overriding each other.
- 18 meshes, 22 surfaces, 34,643 triangles, alpha glass and five colliders survive.

The standalone preview starts with `renderer=gl_compatibility`. Headless checks
validate animation state, not GPU pixels. No full game build, deployment, Web
export or physical-device performance test was performed. The editor import can
log its environment's restricted TCP-listen startup warning; runtime checks pass.

## Short demonstration and delivery package

```sh
blender -b --python-exit-code 1 --python blender/scripts/render_settlements_hall_demo.py
python tools/package_settlements_hall.py --publish-dir artifacts/settlements_hall/v2-animated
```

The renderer reimports the **exported GLB** into a fresh Blender scene and plays
its combined clip, rather than rendering source-only animation. It records the
GLB SHA-256 and sampled hinge/morph states. Existing FFmpeg assembles two close-up
panels into a four-second MP4 and looping GIF: entrance on the left, roof flag on
the right. The four architectural PNGs, editable source, GLB, videos, validation
reports, checksums, source and an independent Godot viewer project are included
in the ZIP. The published PNGs and GIF can also be viewed directly on GitHub.
