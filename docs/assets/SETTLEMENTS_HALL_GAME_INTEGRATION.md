# Settlements Hall V3 Lite — overworld integration

## Implementation status
**Built and staged for owner-requested deployment; live status recorded below.** Only the Settlements
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
+ `Vector3(0, 0.04, 3.25)` (Godot +Z points toward the entrance).
The 0.55 scale fits the 14m reserved site. Visual review found a forecourt gap;
the Hall alone was moved +0.75m in Z. Its platform front now reaches +8.475m,
2.5cm short of the unchanged +8.5m canonical entrance.

The flag wind clip plays automatically from the existing asset script.
Doors open on arriving at the Settlements Hall and on choosing Enter; doors
close when walking away. The original interior/story remains unchanged.
No main-screen widgets or quest/office logic were modified.

## Original build/deploy checklist

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

## Verification and owner-requested publication — 25 October 2026

Built game source: `ee678d9f80c6455da3048d087f7a171a6efbfd5f`. Godot 4.6.3
stable, Compatibility, single-thread Web. The pinned V3 Lite GLB is unchanged.

Completed: native Hall import/placement, transparent glass, two outward hinged
doors (100°), all four looping morph fabrics and independent wind/door playback.
All 15 canonical sites and navigation remain intact. Initial release gates
passed, including the native story victory at 13:54. After the placement-only
fix, the Hall and actual world/navigation checks passed again and Web export
completed without errors.

Browser: the initial source `01e17b6` passed desktop opening/office/wrong-answer
checks and rendered the Hall on desktop and 844x390 touch. The full touch story
progressed through FX with correct travel charges. The final build completed
the desktop walk away and rendered the corrected Hall. The owner then said
“хватит тестировать прохождение, деплой”; both remaining browser runs were
stopped immediately. Return/Enter in the final browser run and full touch
completion are **not claimed as passed**. No physical iPhone Safari test.

The release manifest records `phone_full_story: stopped_by_owner`. Existing
release validators accept this owner exception only for the exact built source
SHA above; no workflows, branches, PRs or infrastructure were added.

Evidence: [native Hall report](hall-game-integration/native-hall.json),
[verification record](hall-game-integration/verification.json),
[final desktop placement](hall-game-integration/hall-closed-1280.png),
[initial touch view](hall-game-integration/hall-game-844.png).

Live publication: pending existing Pages workflow and HTTPS verification.
