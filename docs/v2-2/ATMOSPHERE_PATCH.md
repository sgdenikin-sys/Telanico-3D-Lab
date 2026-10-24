# Late-afternoon atmosphere and control correction — 24 October 2026

Scope: environmental dressing only. Preserve terrain, landmarks/entrances, all
story/session/travel rules, illustrated offices, approved gestures and viewport.

- Northeast key: world +X/-Z, about 19.5 degrees above horizontal, warm light.
  Single shadow caster, two shadow splits; lower shadow opacity and blue sky fill.
- Static blue/cloud sky: cached 128px radiance cubemap; background samples cached
  radiance rather than recalculating cloud noise per pixel/frame. Same sky lights
  and reflects in the water. The approved downward orthographic camera is kept.
- Godot 4.6 Compatibility's simplified SSAO supplies subtle contact darkening.
  Small radius/intensity; no Forward+ feature or volumetric fog dependency.
- Gentle height/depth haze and one low water-only transparent plane. Islands
  occlude the plane naturally by depth testing. Two samples from a shared 128px
  noise image; no raymarching, screen/depth copies or texture-worker jobs.
- Existing verified KayKit CC0 A/B trees: 24 -> 38, same two mesh resources.
  36 original rounded, root-darkened bush clusters, one additional shared GLB
  mesh. Runtime crowns batch in one MultiMesh with per-instance phases. Only
  upper vertices sway; bases remain fixed. Bushes have no collision or real-time
  shadow pass. Paths, courts and shore clearance are checked deterministically.
- No perimeter runners on the translucent world camera/travel controls. Their
  size/font scales by exactly 0.8 only for coarse-pointer touch devices; desktop
  size stays unchanged. Asset HUD/office and dialogue controls keep click/active
  perimeter feedback; hover alone no longer activates the runner.

Available assets were verified on disk; no Quaternius or new external pack used.
Blender source remains reproducible and private; .blend/.glb generation retained.

References: supplied YouTube 0792U-wuwjA and godotlab.org tutorial both returned
network-policy 403 in this environment; no claim of reading their transcript.
Official Godot 4.6 documentation consulted via godotengine/godot-docs on GitHub:
`environment_and_post_processing.rst` (Compatibility SSAO since 4.6; non-volumetric
fog), and `shader_reference/sky_shader.rst` (AT_CUBEMAP_PASS / cached RADIANCE).

Initial native test issue: a renderer-only fixture started native music/door
playback and exited before mixer references drained. Verbose logs identified
AudioStreamMP3/WAV, not sky/foliage resources. The fixture now isolates audio;
existing opening/restart/audio regressions still exercise real playback. Three
isolated repeats passed cleanly. Product audio code was not changed.

Validation: complete Blender/GLB, all native story/source-parity/transport/UI/audio
and atmosphere gates passed. Native held-press feedback and UI checks passed after
the final button-down refinement. Exact final source 4909d8f passed desktop and
full 844x390 trusted-touch story (both tubes, all canonical offices, victory 13:54,
clean Restart). No runtime/resource errors, one music start. Actual world controls
measured factor 0.8 on touch, 1.0 on desktop, no world perimeter nodes. Shader
compilation and final visual review passed; 38 trees/36 bushes stay clear of routes.
Evidence: evidence/atmosphere-*. Publication status: atmosphere-results.json.
Physical iPhone Safari is untested.
