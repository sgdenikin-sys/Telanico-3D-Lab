# Settlements Hall Lite — separate mobile optimization experiment

## Baseline and scope
Current approved V2: **34,643 triangles**, 11 core glTF PBR materials, 2 independently
hinged doors with 100-degree opens, 4 morph-animated pieces of fabric, 4 clips.
Authoring source: `blender/scripts/build_settlements_hall.py`. The published V2
remains unchanged at `artifacts/settlements_hall/v2-animated/`.

The new generator option **`--quality lite`** alters only mesh construction
for a newly generated model and **does not overwrite** existing V2 assets by
default. It simplifies arch tessellation, drum/window repetition, dome rings and
ornament, roof seams, secondary facades, columns, small bevels, flag tessellation,
and optional paving microdetail. Never strip glass, doors, armatures/shape keys,
or the recognizable dome. Eleven materials and the exact four animation clips
remain mandatory. Retain the building's ivory/deep-teal/aged-brass style.

## How to build in a Blender-enabled Codex workspace
From repository root, preserving any existing changes:

```sh
blender -b --python-exit-code 1 --python blender/scripts/build_settlements_hall.py -- --quality lite --render
python tools/compare_settlements_hall_lod.py
python tools/validate_settlements_hall.py blender/generated/settlements_hall_lite/settlements_hall.glb
```

The first command writes a **separate** editable file, GLB, stats and rendered
previews to `blender/generated/settlements_hall_lite/`. It never writes
`godot/assets/generated/settlements_hall.glb` when using the default Lite
output directory. For all custom output directories specify `--quality lite`.

## Acceptance criteria and further work
1. **Target 15–20k triangles**, soft fallback ceiling **22k**. This is a target,
   **not a claimed measured result**; inspect numbers from the actual export.
2. Match landmark dimensions/recognizable silhouette within 12cm of V2. Keep
   front entrance, stairs, ribbed dome, wings, and transparent blue glass.
3. Preserve PBR distinctions between ivory stone, bronze/brass, blue roof metal,
   tinted glass, blue doors and fabric. Ensure transparent glass renders correctly
   in Godot Compatibility.
4. Independently opening/closing 100-degree doors and four looping flag fabric
   animations must survive *GLB reimport* in Godot 4.6.3.
5. Compare the V2 and Lite Hero/Front/Rear/Detail camera renders at equal scale.
   The mobile variant should read less busy, not collapse into toy-like blocks.
6. Verify Web/iPhone landscape visual read, loading, FPS and memory *before*
   calling the version mobile-ready. Browser emulation is not actual Safari.
7. If triangle budget or visual fidelity fails, make one targeted adjustment
   to the Lite preset and rerun only this model's checks (not whole-game tests).

## Delivery and publishing
Publish corrected `.blend`, `.glb`, four renders, animation demo and reports
under a new `artifacts/settlements_hall/v3-lite/` directory **only after**
successful build/validation. Do not rewrite V2 assets. The existing independent
Web viewer can load a ZIP or GLB; optionally stage the validated Lite GLB in
the dedicated public `Telanico-3D-Web/site/hall/` asset path, but **never modify
the root game release or main scene**. Do not rely on downloading private files
from public Actions, which previously failed 403. Do not add new infrastructure.
