# Operations Textured V3 — visual-only integration

The exact owner-reviewed GLB is preserved in compressed form as
`artifacts/operations/v3/operations_textured_v3.glb.gz`.
`tools/stage_operations_dome_game.py` checks SHA-256, 16,086 triangles,
12 materials, 9 embedded images and both door animation clips, then
decompresses the original to `godot/assets/generated/operations_textured_v3.glb`.

`world_v2.gd` replaces the placeholder appearance only; it does not change
original navigation/collision, site selection, office content, character scale,
15-site registry or quest logic. Initial placement scale 0.75, front offset
+0.65m (+Z) and height +0.06m are first-fit values matching the existing entrance
waypoint. Door open/close actions are wired to existing site-arrival events.
The supplied trimesh GLB is Z-up. The `Architecture` instance rotates -90°
around X to become Godot Y-up; source geometry and animation tracks are intact.
The standalone GLB has static flags — do not claim a flag-wind animation.

The follow-up applies six owner-supplied ground albedos at 512×512 with mipmaps
and world-space triplanar projection. Existing grass zones, terrain, routes and
collisions are reused. Main sunlight and the matching sky now come from north-west
(Godot -X/-Z); shadows fall south-east. Hall and courier sizes remain unchanged.

Source integration is not the same as a completed Godot Web build or live
publication. The private Lab Actions previously failed before a runner was
assigned. Keep the existing live game unchanged unless a verified Web runtime
is built and deployed by the established publication process.


## Ground / NW sun release
Source: `8573f5afb5ef2efa4211ab0e87fa6effe818f67f`. One quick smoke and
one Operations office entry passed. A visible Z-up orientation error required
one instance-rotation correction and an affected visual/door recheck.
Three final Web screenshots are stored with the published site evidence.
Full story and physical iPhone checks were not run, per the owner's bounded scope.
See `operations-ground-result.json`; release publication is recorded below.
