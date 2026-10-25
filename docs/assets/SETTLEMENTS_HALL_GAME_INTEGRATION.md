# Settlements Hall V3 Lite — overworld integration

## Implementation status
**Committed to `main`; not yet game-built or deployed.** Only the Settlements
Hall visual was replaced in the Godot overworld controller. Route graph,
site-selection areas, canonical story/office rules, time limits, transport,
camera, UI, and the remaining 14 locations are unchanged.

Model: `artifacts/settlements_hall/v3-lite/settlements_hall.glb` at 19,816
triangles (11 PBR materials, alpha glass, opening doors and four wind fabrics).
`tools/stage_settlements_hall_game.py` checks SHA-256, triangle count,
materials, clips, and glTF header, then copies to
`godot/assets/generated/settlements_hall.glb` for Godot import.

`godot/scripts/world_v2.gd` now instantiates
`res://scenes/assets/settlements_hall.tscn` and hides only the old
`Site_settlements` **visual** hierarchy after original terrain and WalkSurface
colliders have been set up. The canonical site target/collision and entrance
waypoint remain authoritative, so the replacement does not change navigation.
The freestanding preview model's `OptionalBuildingCollision` is disabled to
avoid extra collision walls.

Runtime placement: scale = **0.55**, position = canonical site centre
+ `Vector3(0, 0.04, 2.5)` (Godot +Z points toward the entrance).
This is a first-fit for the 14m-wide reserved site, not a fully
reviewed camera/collision alignment.

The flag wind clip plays automatically from the existing asset script.
Doors open on arriving at the Settlements Hall and on choosing Enter; doors
close when walking away. The original interior/story remains unchanged.
No main-screen widgets or quest/office logic were modified.

## Verification still required — Codex build/deploy handoff

From the existing Codex/Blender/Godot development workspace, use the existing
installed binaries and project workflow:

1. `python tools/stage_settlements_hall_game.py`; validate pinned V3 SHA.
2. Build with the existing `bash tools/build_web.sh` (or supported Windows
   build). The build now runs `tools/check_hall_overworld.gd` as a focused gate.
3. Visually inspect the integrated Hall from the existing game camera. Check
   sizing, orientation, feet/base contact with terrain, front entrance alignment,
   roof clipping, access to the entrance and no double geometry.
4. Verify alpha-glass, material response, independently animated doors,
   continuous flags, no floating decoration or z-fighting. Use the targeted
   smoke check and only the already documented necessary story/viewport gates.
5. Verify both desktop and iPhone-landscape touch browser at 844x390. Do not
   call browser emulation a physical iPhone Safari test.
6. If alignment/collision needs correction, make one focused placement/collider
   fix, run the affected test once, then stop and report.
7. Stage/verify and publish the TESTED game Web snapshot using the established
   `Telanico-3D-Lab` source → `Telanico-3D-Web` publication exception.
   Keep the previously working site available until live HTTPS/WebGL verification
   succeeds. Do not invent any CI workflow, credentials, branch or PR.

Source changes in this integration are not proof of a successful Web export.
**Do not state that the Hall is playable until a real built/deployed Web snapshot
has been verified by its commit.**

## Rollback
Remove the `_install_settlements_hall()` call (and optional event hooks) from
`godot/scripts/world_v2.gd` and rebuild the game. This makes the already
existing `Site_settlements` visual visible again. The original source
overworld generator is unchanged and V2/V3 model packages remain available.
