# TASK2_19OCT — Make Telanico World V2 actually LOOK three-dimensional

**Task type:** Autonomous art-direction + camera + environmental rebuild, preserving tested gameplay
**Canonical starting source:** \`codex/telanico-overworld-v2\` at/after commit \`f3949d69190b2fc556b4de972a8cb3ed7c6bfc04\` (PR #6)
**Read this task from:** \`codex/two-island-overworld:tasks/TASK2_19OCT.md\`
**Create working branch / PR:** Develop from latest V2 with mergeable changes; maintain active automatic Web preview publication source.
**Release target:** https://sgdenikin-sys.github.io/Telanico-3D-Web/
**Priority:** Major visual quality correction; NOT more features/menus.

## 0 — Why this task exists: physical iPhone failed visual acceptance

The user has reviewed the real public V2 build on an iPhone. It loads and is functional, but **looks almost strictly TOP-DOWN**, flatter and less impressive than the prior 2D map/concept art.

Screenshot observations:
- Both islands read as flat green slabs, with thin paths and tiny disconnected-looking buildings.
- We can see roofs but almost no façade, stairs, courtyard levels or hill silhouettes.
- The whole world is framed from an overly high angle; there is no satisfying premium 3D diorama depth.
- Mild geometry waves are insufficient when scaled relative to island size.
- Materials feel mostly unlit/pastel/flat; the previous hand-painted 2D map felt richer.
- The temporary courier is invisible at whole-world zoom; little sense of human scale.
- The exported project is technically accomplished but not visually impressive. This is an ART DIRECTION and CAMERA failure, not a CI or feature count problem.

Do NOT tell the user "the angle is 60°, so it is correct". In this project, 60° was interpreted as camera elevation **above the horizontal ground plane**, and THAT IS TOO STEEP visually. 60° above horizontal means only 30° from directly overhead. The user's real-world screenshot, not a unit test, is decisive.

### Verified implementation facts (read current files to confirm)
- \`godot/scripts/world_v2.gd\`: \`camera_elevation := 60.0\`; \`_camera_pose()\` uses position \`sin(e)\` height and \`cos(e)\` ground offset; \`camera.projection = Camera3D.PROJECTION_ORTHOGONAL\`; reset and Explore restore 60°.
- Existing Inspect can vary elevation only 45..75; default and Reset are hard-coded at 60.
- \`blender/scripts/world_v2_layout.py\`: large world approx 170 × 115 units, but \`base_height()\` uses bumps of ~3.6–5.8 vertical units. Big map scale + tiny elevation + steep camera + flat unshadowed materials combine into a flat infographic.
- The real asset manifest includes KayKit Medieval Hexagon and KayKit Adventurers, with 33 pinned fetched files, about 14 distinctive mesh types. So DO NOT redo asset acquisition; improve how these genuine CC0 meshes are assembled, scaled, lit and presented.
- The public build is a working HTML5 release with 15 destinations, click/touch navigation, courier animation, ferry, bridge, tubes. Preserve these achievements.

## 1 — Goal and aesthetic acceptance

Deliver an obvious before/after visual improvement, not a numeric camera tweak and a new text report.

Visual reference / art-direction:
- A charming premium stylized, **oblique 3D miniature archipelago**.
- Two large naturally shaped coast/islands with genuinely differentiated elevation.
- Noticeable building FACADES, entrance stairs/ramps and heights from default overview.
- Lightly sculpted meadows, 2–3 natural hill zones and a few raised terraces with attractive edge geometry.
- Two matching distant outside-edge pneumatic towers, inside channel docks, one northern arched pedestrian bridge, a few scattered small boats.
- More organic winding footpaths, mixed pale stone/gravel/dirt, plenty of open space, no asphalt or car roads.
- Richer but restrained stone/teal/ivory/bronze palette, subtle variation/roughness, sunlight and gentle shadows. Still clearly stylized and performant, not a AAA photoreal scene.
- Buildings remain unique modified CC0 kit assemblies. Avoid boxlike copy/paste silhouettes. The main buildings need enough visual weight to read from world-scale overview.
- Sparse trees, no mountains/forests, no giant excessive decorative road grid.
- Maintain a tabletop / miniature look with carefully limited perspective distortion.

The selected user concept image is a richly composed 3D diorama of two asymmetric rocky landscaped islands divided by inner turquoise channel, connected by stone pedestrian bridge; landmarks are spaced among hills and plazas. Do not claim to inspect this image if not available in the repo. Use this description and original pilot maps, and focus on *similar spatial depth* at much lower geometry/detail.

## 2 — CAMERA: correct semantics and show comparisons

This is the core acceptance criterion.

Camera angle MUST be evaluated ABOVE HORIZONTAL, not from vertical.

Try at least these camera ELEVATIONS above horizontal:
- 30°
- 38°
- 45°
- 55° as reference / fallback

Initially favor ~38–42° above the ground plane (equivalently ~48–52° away from vertical). This is materially more oblique than 60° and will show building walls.

Create 4 screenshots with exactly comparable world target, yaw, lighting, framing and similar coverage at the tested angles. Inspect images with actual rendered world rather than trusting labels or constants. Use 40° as initial default if no better visual choice emerges.

Compare orthographic and **moderate long-lens perspective** at ~38–42° for an attractive tabletop effect. Perspective could improve scale/depth, but NOT at the price of losing navigation and consistent pinch/wheel zoom. If perspective wins, update camera.zoom code correctly (orthographic size vs perspective camera distance/FOV), test input and raycast coordinates, and keep all islands visible at world overview.

Do not merely rotate orthographic camera down and declare victory. Also make the scenery and architecture communicate volume: elevated terrain, building heights, cliffs, soft lighting, composition.

Retain:
- Explore stable north-up orientation with pan/pinch and desktop mouse/scroll.
- Inspect constrained orbit.
- Follow that brings the character into a close game-like camera framing.
- Reset returning to oblique world overview (NOT near-vertical).
- Existing safe-area/mobile viewport behavior and iOS touch controls.
- Desktop use on the SAME PUBLIC URL.

Visually inspect Follow mode at approximately an adult courier's scale. The character should be readable, properly on ground, and not hidden behind building roofs or terrain. Fine-tune Follow focus/zoom and occlusion where needed. World overview need not display every character detail.

## 3 — GEOMETRY + ART PASS: make height differences physically meaningful

Existing \`base_height()\` bumps (~5 units high across 170-wide map) are visually weak. Improve terrain shape and elevation intentionally, not randomly:

- Raise selected building districts onto substantial, smoothly blended terraces/hills and provide natural approach slopes / stairs; increase relative terrain prominence without turning paths too steep.
- Distinguish high and low neighborhoods from the default oblique camera.
- Sculpt shoreline cliffs and stepped banks, especially along exposed outer sides.
- Add gentle rolling hill silhouettes and surface variety, plus small cutouts/beaches in spots; no gigantic mountains.
- Waterfront/channel should have real spatial relief: lower water, dock platforms with visible vertical edges and stairs/ramps from promenades.
- Pedestrian stone bridge needs readable arch/deck/parapet depth at default camera; must remain traversable. No mere thin flat strip between slabs.
- The asset-based halls/buildings should read like actual little buildings, not barely discernible icons. Review building-to-character proportions and prominence. Selectively increase key landmark massing, add kit-based entrance details, doors, roof silhouette and steps/terraces.
- Larger buildings must not overlap paths or navigation targets. Route and collision geometry must adapt automatically.
- Avoid excessive coast foam/props; spend geometry budget on landmarks and variation rather than clutter.
- Curate texture/material detail within low WebGL footprint; reuse same loaded KayKit assets where appropriate.

Prefer modifications of \`blender/scripts/build_world_v2.py\`, \`world_v2_layout.py\`, material/light settings in Godot and camera behavior in \`world_v2.gd\`. Use exact code-grounded changes, not arbitrary image-only enhancements.

## 4 — PRESERVE working game / no UI detour

Do NOT rebuild architecture, route/scene/event framework or start a new app. This is V2.1, visually significant improvement to an already working interactive prototype.

Must preserve:
- All 15 canonical landmarks; West = Settlements, Operations and support; East = Trader, Contracts, VAT, FX, Archive.
- Two matching pneumatic tubes toward diagonally opposite OUTER coasts (NOT in center); 3-minute transfer.
- Two inner-channel docks, visible ferry transfer 5 minutes plus possible approach; slow northern pedestrian bridge.
- Working Animated temporary courier; walking/idle and pathfinding.
- Click or touch building select, action/route preview, Enter/Stay Outside, Labels/Names mode.
- Desktop and landscape iPhone input, zoom/pan/follow/reset.
- Existing original VorGun game and all its production assets untouched.
- Game-time accounting and deadline consistency.
- Existing public release pipeline.

No new complex quest/dialogue/invoice work. No long redesign of UI labels, buttons, safe-area CSS or permissions. Adjust only controls necessary for the camera to be usable.

## 5 — Asset authenticity and quality

Do not falsely claim "we didn't use assets". Verified V2 uses real downloaded KayKit CC0 assets with license manifest. Reuse them, but build better architecture:
- inspect the CURRENT placed model scale and unique building silhouettes;
- identify repeated/dwarfed modules;
- selectively combine available modules for dominant hall, operations, Trader, archive;
- make these structures substantially recognizable from a 40° camera, with subtle bronze/blue/terracotta features;
- keep enough clearance for playability;
- if a small additional freely downloadable CC0 asset greatly improves stairs, arches, rooftops, cliff rocks or piers, add it with pinned checksum and metadata; do not restart a mass download project.

Make art quality and identity measurable by actual side-by-side WebGL screenshots, not by counting CC0 imported meshes.

## 6 — Screenshots, testing, publishing

Run local/cloud Godot+Blender full regeneration and QA, not just syntax tests.

Minimum screenshots:
1. Current V2 as-before reference at 60° (use existing screenshot or generate).
2. Same world from 30/38/45/55° with comparable framing, before terrain changes if helpful.
3. FINAL 40-ish-degree whole-world view in real Godot WebGL on desktop.
4. FINAL 40-ish-degree whole-world on simulated landscape iPhone.
5. Detailed approach to Settlements from Follow showing character, stairs, walls, slope.
6. East Island Trader and Contracts with architecture visibly volumetric.
7. Waterfront ferry and 3D arch bridge + elevation.
8. At least one screenshot showing high-vs-low terraces clearly.

**Acceptance is visual:** when viewed at a glance, the default shot must look like a miniature 3D world, NOT a 2D diagram of two islands viewed from above. Keep the user-favored rich concept direction in mind without trying to match photoreal details.

Automated tests:
- 15 sites, correct island distribution, reachability, path routes, wall/water rejection, bridge crossing, ferry/tube.
- Courier animation and arrival, collision/camera Follow at slopes/entrances.
- Desktop browser at 1920x1080 and 1440x900; simulated iPhone 844×390 CSS landscape, rotate/reflow.
- Explore/Inspect/Follow/Reset, zoom limits for chosen projection, pointer-selection picking.
- Site HTTP(S), Godot assets, WebGL startup, browser console.
- Runtime geometry/bandwidth reasonable for iPhone 12-class device; don't claim actual physical-device performance from emulator.

**MANDATORY DEPLOY:** Use existing public import/publisher from Telanico-3D-Web. Push preview source to the allowlisted \`codex/telanico-overworld-v2\` branch (or update deployment allowlist safely if maintaining a separate head), await verified CI & public deploy. Confirm the LIVE page serves the new commit and changed camera parameters. Merely producing a ZIP/PR is NOT completion. Do not merge into private main or ask user for GitHub buttons/run IDs.

### Completion report

Briefly report:
- Which camera angle/projection was chosen, with the interpretation "degrees ABOVE HORIZONTAL" explicit.
- What changed in terrain/height/buildings and how this is obvious visually.
- Which prior gameplay interactions remain passing.
- Links: PR, before/after comparison/screenshots, successful private Actions, **successful public deployment**, working site.
- Any caveat for physical iPhone test.

**Do not overpromise. If visual change is still small, keep iterating rather than reporting a polished success.**
