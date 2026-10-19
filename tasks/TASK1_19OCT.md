# TASK1_19OCT — Telanico 3D World V2: asset-first, playable overworld, public Web deploy

**Status:** Ready for autonomous implementation
**Task owner:** Telanico 3D Lab
**Priority:** Major full-stack 3D development sprint, not another small smoke test
**Source branch:** codex/two-island-overworld (PR #5)
**Create development branch:** codex/telanico-overworld-v2
**Date:** 2026-10-19

## READ THIS FIRST — non-negotiable deliverable

Build a dramatically better **interactive 3D overworld** that is playable in browsers on both iPhone and desktop. Use ready-made properly licensed 3D assets as the primary visual foundation, customize them in Blender, add a walking/idle-animated character, real building selection and navigation, boat/bridge/tube routes, comfortable terrain scale, and reliable browser tests.

**Build, test, and deploy the result to the already configured PUBLIC preview website.** A PR or ZIP alone is NOT completion.

- Private development repository: https://github.com/sgdenikin-sys/Telanico-3D-Lab
- Existing playable original pilot, READ-ONLY source of truth: https://github.com/sgdenikin-sys/VorGun-Godot-Clean-Test
- Public deployment repository: https://github.com/sgdenikin-sys/Telanico-3D-Web
- Live website: https://sgdenikin-sys.github.io/Telanico-3D-Web/
- Current PR #5, which established the overworld blockout: https://github.com/sgdenikin-sys/Telanico-3D-Lab/pull/5
- Mobile presentation fixes: PR #3 and PR #4 in Telanico-3D-Lab.
- Existing publisher in the public repository: .github/workflows/import-private-web.yml

The user does NOT want to copy files, download ZIPs, start GitHub Actions manually, type workflow run IDs, configure additional secrets, or merge PRs for each preview release. Automate release of validated Web-preview builds. The home PC may be switched off; use cloud Codex/GitHub Actions.

**You have authorization to deploy validated changes to the public prototype website. You do NOT have authorization to merge into the private main branch, to modify the production VorGun game, to expose private source files, or to publish private credentials.**

If a specific operation is blocked by permissions, do all accessible work, record the exact blocker, and propose the least invasive solution. Never claim publication succeeded unless the public site is actually verified.

## 0. Operating contract and iteration strategy

Act as senior Godot engineer, Blender technical artist, environment artist, gameplay programmer, QA lead and release engineer.

This is a long-running integrated sprint. Implement in logical phases with working checkpoints. Do not stop after a simple blockout, a model-count report or the first passing GLB validator. Run automated build/validation repeatedly, fix failures, and produce useful previews.

Order of priorities if time/compute becomes constrained:
1. Correct geography, much larger scale and visually appealing terrain.
2. Real imported CC0 assets and distinctive architectural silhouettes.
3. One authentic imported, rigged, animated character and navigable movement.
4. Touch/click selection, route preview and transport representations.
5. Desktop + iPhone Web export and automated public preview deployment.
6. Polish and additional environmental detail.

Do not overinvest in menus or solve previously accepted mobile UI issues again. Existing mobile UI works adequately; focus on the WORLD. Avoid huge cascades of decorative props.

Preserve original quest/interior/dialogue/invoice content for later integration. This project replaces **overworld map only**; no rewriting office scenes or financial story mechanics.

## 1. Audit and correct original-pilot geography and timing BEFORE modeling

Inspect the ACTUAL original VorGun repository, especially:
- main.gd, including original destinations in _build_travel_system, transfer code, navigation/path lengths and route preview.
- docs/SCENARIO.md, docs/DECISIONS.md, tests/navigation_regression.gd.
- assets/maps/VorGun_island_test_transparent.png and existing original building/tube/boat assets for visual placement reference.
- Current Telanico-3D-Lab overworld_layout.py, build_overworld.py and Godot preview; AGENTS.md; GitHub Actions and public deployment workflow.

Correct previous geography mistake: **Operations belongs to WEST / Island A**, not East. **Trader (Eagle) belongs to EAST / Island B** and is missing from current 3D blockout. Do not repeat previous erroneous office assignment.

Canonical functional grouping from pilot:

**WEST / ISLAND A (left, settlements and support):**
- Settlements Hall — starting point for Cooper
- Operations
- Trade Finance / Finance
- LC Desk (separate landmark in new 3D world)
- Compliance Annex
- Coffee Area (additional)
- West Pneumatic Tube Station
- West Harbor Launch

**EAST / ISLAND B (right, commercial/documentation):**
- Trader (Eagle)
- Contracts
- VAT / Tax
- FX Desk
- Archive Rotunda (additional)
- East Pneumatic Tube Station
- East Harbor Launch

This makes 15 named landmarks when separate LC Desk, Trade Finance, Coffee Area and Archive Rotunda are included; also add pedestrian bridge as traversable infrastructure.

**Critical tube positioning:** the original pilot places its two pneumatic stations at far-apart, roughly diagonal OUTER sides of their respective islands, NOT a mirrored pair beside the central ferry docks. The current blockout coordinates (-10,-8) and (+10,-8) are wrong for the desired visual and gameplay geography. Move West tube toward the far west outer edge and East tube toward far east outer edge (opposite corners / diagonally separated), while keeping both physically reachable.

**Travel-time truth from original pilot code:**
- walking_world_units_per_game_minute = 1.5 in original world scale
- typical walking trip ~6 story minutes (real route costs may vary)
- tube transfer = 3 story minutes
- boat transfer = 5 story minutes plus optional waiting/approach
- quest begins at 12:00 and deadline is 14:00
- original green path roughly 90 in-game minutes, yellow roughly 110, red >120

The larger new overworld must be calibrated using real physical walking paths, character speed, and the scaled story clock, NOT by simply inventing a multiplier that makes small geometry appear to cost 17 minutes. Separately report in-game travel time versus real-time animation duration. The player must not literally wait 6 real minutes to watch a 6-story-minute walk.

New pedestrian bridge is an explicit change from original pilot: make it the **slowest overall inter-island route** in representative central-dock-to-central-dock and hub-to-hub examples. Ferry is relatively fast, tube is the fastest transfer mechanism, but approach distances matter. Explain routes and numerical examples in a machine-readable layout JSON and readable report. Do not claim to exactly recreate original full-run timing without running a scenario simulation.

## 2. ART FIRST: mandatory reuse of genuine third-party free 3D assets

The current 206-mesh scene is almost entirely procedurally generated Blender primitives. Do not make the next version another rectangle-based toy mockup.

**Mandatory asset-first workflow:**
1. Inspect available candidate asset packs and their **actual** license terms and accessible free downloads.
2. Download selected assets from publishers/authorized sources. No gated, paid, pirated or license-unclear downloads.
3. Import real FBX/GLB/OBJ/Blend asset geometry into Blender/Godot. The finished GLB must demonstrably contain third-party meshes; superficial decorative references to Kenney do not count.
4. Curate a focused subset of reusable meshes, not complete giant asset packs; normalize scale, origin/pivots, orientation and collisions.
5. Customize materials and modular architecture into a **distinctive Telanico style**, rather than presenting an unmodified asset-pack scene.
6. Store precise source URL, author, asset version if known, license text/link and list of used models in docs/ASSET_MANIFEST.md.
7. Respect repository constraints for binaries and file size. Preserve reproducible cloud builds, including downloading pinned verified archives with checksums when appropriate. Do not commit gigabytes of binary packs. Ensure automated builds do not depend on an interactive website login.

Asset candidates to CHECK; choose only suitable FREE models:
- Quaternius Medieval Village MegaKit: https://quaternius.com/packs/medievalvillagemegakit.html
- Kenney Fantasy Town Kit: https://kenney.nl/assets/fantasy-town-kit
- Kenney Castle Kit: https://kenney.nl/assets/castle-kit
- Kenney Nature Kit: https://kenney.nl/assets/nature-kit
- Quaternius stylized nature packs: https://quaternius.itch.io/stylized-nature-megakit
- KayKit Adventurers: https://kaylousberg.itch.io/kaykit-adventurers
- KayKit Character Animations: https://kaylousberg.itch.io/kaykit-character-animations

These are **candidates, not a claim that specific versions, licenses, file formats or downloads are available**. Validate everything before import. Free editions only. Prefer CC0, but document and comply with any other clear license; if not suitable, find another confirmed free equivalent.

At least:
- actual ready-made architectural components in several department buildings;
- actual ready-made nature/rock/landscape props (limited quantity);
- a real existing animated character model/rig or compatible imported animation source.

Procedural Blender remains very appropriate for coastline, terrain, paths, docks, bridges, bespoke tube machinery and unique departmental decoration. It must NOT be the only source of geometry.

## 3. Visual brief — the concept art is aspirational, not a request for photorealism

Target a **premium soft stylized tabletop diorama**, a distinctive Telanico fantasy-industrial campus, with mature styling:
- clean architectural silhouettes, slightly rounded bevels
- muted ivory limestone, blue/gray/deep teal roofs, aged bronze/brass, restrained warm terracotta
- soft green meadows, gentle hills and modest rocky ledges
- pleasant turquoise/deep teal water
- warm believable lighting and soft readable shadows
- subtle pneumatic/industrial character, not overt generic medieval-fantasy decoration
- buildings clearly differentiated by function
- some natural imperfections instead of rigid symmetry

Concept composition:
Two large, spacious islands with a central river-like strait. Organic coastlines, a **northern stone pedestrian bridge**, paired inner-side docks and a moving ferry in central channel, plus tube stations far out toward opposite outer island edges. Some raised building terraces with stairs or ramps; modest natural topography. Trees and boulders used sparingly. Several small boats scattered across different shoreline regions, not clustered. Path hierarchy: pale stone main pedestrian promenades, smaller stone footpaths and short dirt/gravel shortcuts. **No roads for cars, no asphalt, no vehicle grid.**

User selected a picturesque two-island isometric concept with broad grassed open spaces, grander building identities, hills/terraces and natural coasts. The reference image may NOT be available in this cloud workspace: use actual original-pilot asset maps and the detailed text brief as grounded sources. Do not claim you inspected an inaccessible picture.

Keep polycount, textures and lighting practical for iPhone 12-class WebGL2. Optimized modular kits, instancing and moderate material count; no expensive ocean simulation or unnecessary postprocessing.

## 4. Large world and walkable terrain

The current effective world is ~68 × 46 Blender world units and still looks cramped. The prior generator uses a rectangular water tray and beveled flat island polygons with decorative surface cylinders/boxes pretending to be hills.

That is NOT sufficient.

- Initial design experiment: ~2.5x increase in **linear effective island dimension** over the current blockout, then tune against character height, building footprints, walking paths and camera framing. The goal is genuine SPACE, not giant geometry with all buildings still packed together.
- Do not solve travel time by inflating a story-time conversion factor while leaving geometry tiny.
- Create real 3D terrain with continuously varying height, slopes and organic shorelines, walkable terraces, ramps, mild rock outcrops and a few stairs.
- At least 2–3 meaningfully different elevation zones visible from a 60° camera.
- 2–3 appealing low hill clusters overall, sparse trees, no mountains or forest carpet.
- Buildings have natural breathing room around them; characters visibly travel through landscape.
- Preserve named landmark location manifests, explicit entrances, collision volumes, walkable surfaces and route graph/navmesh.
- Never place default nav targets inside building footprints.
- Allow paths to curve naturally rather than connecting every building with equally wide geometric spokes.

### Unique architecture / department treatment
- Settlements Hall: prominent civic hub, starting point, entrance steps or portico.
- Operations: major identifiable dispatch hall on LEFT island.
- Trader (Eagle): recognizable commercial office on RIGHT island, distinct from Contracts.
- Contracts: study/records motifs.
- Trade Finance and LC Desk: related visual family, but two destinations.
- Compliance Annex: restrained formal/guarded entrance.
- VAT / Tax: ledgers/official office language.
- FX Desk: distinctive smaller pavilion/tower, a bit isolated.
- Archive Rotunda: round dome, archive language.
- Coffee Area: warm kiosk, benches, few tables.
- Two matching bespoke pneumatic tube stations on opposite OUTER sides.

Rebuild using existing modular assets and local Blender adjustments, not entirely new primitive blockhouses.

## 5. First animated Cooper / character-proof scale test

Introduce at least ONE visible, real, rigged 3D model with idle and walking animations.

Preferred: an adult-proportioned anthropomorphic honey-badger-inspired Cooper, with coherent dark/white markings and muted hoodie/jacket; not infantile, grotesque, plastic or gaunt. Approved final Cooper likeness is NOT provided in this repo; never misrepresent a placeholder as approved final character art.

For speed: reuse a ready-made authorized CC0/compatible rig and animations. Adapt meshes/materials in Blender to test a Cooper-like silhouette. If an animal head rig genuinely blocks delivery, ship a clearly labeled TEMPORARY animated humanoid with correct walk/idle and explain remaining work; do not sink the entire sprint into bespoke face sculpting.

Character gameplay:
- spawn outside Settlements Hall;
- select a reachable location on the map by mouse click or finger tap;
- preview path and estimated story minutes;
- user confirms Walk / Cancel;
- walk with real animated movement, correct slope adjustment and facing;
- stop at the building entrance, never penetrate geometry;
- collision excludes water and steep cliffs;
- bridge is a walkable inter-island connection;
- use NavigationAgent3D and suitable baked/generated navigation mesh or carefully proven equivalent;
- a placeholder interaction “Enter / Stay Outside” may open a tiny department panel and Return to Map; leave original interiors untouched.

## 6. Travel interaction: WALK / BOAT / TUBE

Implement a useful minimum vertical slice with one playable character and all three transfers:

**Walk:** paths/bridge with navigation and story cost from shortest valid walkable route; no teleport through obstacles.

**Ferry/fast motorboat:** two inner-channel docks closer to the middle of both islands. Boat visibly rides between them, has a simple boarding/disembark sequence and consumes 5 in-game minutes + appropriate wait and walking approach. Physical crossing occurs in a much shorter real viewing time (for example a handful of seconds) so the preview is usable. Boat should be an adapted imported 3D model where feasible; decorative boats should be distinct.

**Pneumatic tube:** 2 identical stylized outer island stations. Select station, approach it, clearly signal travel, quick visual transition to the far station, deduct 3 in-game minutes. The stations should not be near the ferry.

Use pilot route/timing data to validate at least 3 representative origin-destination pairs. Bridge walking (with approaches) should be longer/slower than an appropriate ferry or tube route. If travel cost is not fully implemented, expose an honest prototype estimate and do not claim complete scenario timing integration.

## 7. Building selection, labels and UI

All 15 destinations must have stable IDs, island assignments, entrances, labels, clickable mesh/collision targets and route metadata.

Replace giant always-visible floating labels that collide with buildings with context-sensitive landmark UX:
- desktop mouse hover can show names; left click selects;
- on iPhone first tap selects and shows name/action, no hover dependency;
- selected building highlights softly;
- contextual panel: Department, approximate walking time, Walk / Boat / Tube where appropriate, Cancel;
- optional toggle to reveal all landmarks; labels readable and should not overlap wildly;
- character arrival prompts Enter / Stay Outside; Enter displays a minimal placeholder department panel, not a new quest interior;
- close/dismiss interactions working on both mouse and touch.

Avoid UI overhaul. Preserve working page/mobile safe areas and Reset view. The UI must not eat the entire landscape.

## 8. Camera — showcase 3D without confusing navigation

Current camera is too nearly top-down to appreciate buildings/hills. Compare camera elevation **55°, 60°, 70° above the horizontal ground plane**, with 60° favored.

Implement two clear modes:
- EXPLORE default: stable north-up navigation orientation, camera can follow character, drag pans, pinch/scroll zoom; camera angle about 60°; do not freely orbit world with every navigation gesture.
- INSPECT: constrained orbit/tilt/pan/zoom to appreciate architecture. Reset returns canonical whole-map view.

Desktop: mouse click to select, drag to pan, wheel zoom, optional right-drag orbit in Inspect, keyboard shortcuts where useful. Mobile: tap select, drag pan, pinch zoom, optional constrained orbit only in Inspect. Avoid unintentional click/drag confusion. Zoom bounds must permit whole-map overview and useful character/entrance close-up.

Take comparison screenshots at 55/60/70 from identical target/framing. Maintain landscape iPhone and desktop browser layouts.

## 9. One Web build for desktop and mobile

Do NOT create a separate web domain or project for desktop. The EXISTING public Godot HTML5 site should run on:
- Desktop Chrome, Edge and preferably Firefox at ~1920×1080, 1440×900 and 1366×768.
- iPhone Safari and iOS Chrome in landscape with safe areas / toolbar adjustments.
- Android Chromium where practical.

Use Godot Compatibility/WebGL2 and single-thread Web export; existing working Godot 4.6.3 pipeline is the baseline. Respect device memory budgets and WebGL limitations. Preserve physical iPhone proof of previously working drag/pinch/reset, but test again with the new UI. Browser emulation cannot prove real-device performance.

Improve visuals without sacrificing mobile startup and reliability.

## 10. Deployment is REQUIRED, automated and user-free

There is an existing and already working public deployment workflow, including repository secret TELANICO_LAB_ARTIFACT_TOKEN in the PUBLIC repository. It reads successful private “Godot Web playable” artifacts from Telanico-3D-Lab and publishes only the Web runtime to Telanico-3D-Web/GitHub Pages.

Prior history: a manual source_run_id was necessary until a previous update to .github/workflows/import-private-web.yml triggered one release via push. We need **future validated development preview builds to update automatically**, without the user pressing Run Workflow each time.

Implementation contract:
1. Produce and push branch codex/telanico-overworld-v2 in private repo and create PR for review.
2. On each successful authorized preview build for this designated branch, automatically publish the exact successful matching Godot Web artifact to the public site.
3. Prefer GitHub Actions/native triggers with minimum necessary permissions; if cross-repository workflow dispatch isn't possible without new credentials, use an idempotent **scheduled/triggered importer in the public repo** that discovers the newest successful “Godot Web playable” run for an exact allowlisted development branch/commit, verifies run conclusion, artifact existence and age, and imports only when new. Do not blindly publish another branch or a failed run.
4. Do not disclose secrets, private source scripts, Blender files or full asset archives publicly.
5. Confirm real site deployment SUCCESS via the GitHub Pages job and verify HTML and runtime assets are reachable by HTTPS. Verify deployed build version/build identifier, not just old cached page.
6. Failure safety: retain last working public version if the candidate fails tests; surface the blocking error rather than silently reporting green.
7. Do not merge into private main for preview release.
8. Do not require any owner to manually copy an Actions run number, download a ZIP or restart workflows.

If managing the public repository requires additional GitHub connector permissions, complete everything safely possible, report the exact missing action, and do not claim release success until verified. A reviewable PR is required, but the public preview can release from a validated feature branch without merging it into private main.

IMPORTANT: after accomplishing this sprint, document a stable repeatable no-manual-deploy release process in docs/PREVIEW_RELEASE.md. This is a product requirement, not a future idea.

## 11. Automated quality gates and acceptance

Test more than geometric validity.

**Static/build gates:**
- Blender CLI reproducible generation, saved editable .blend and generated .glb.
- Imported CC0 asset manifests with source/license traceability.
- Geometry materials/pivots, GLB structure, reasonable mesh/vertex/texture budgets.
- Scene startup/import in headless Godot.
- Validate unique IDs and correct island assignment, 2 distant matching tube stations, separate inner docks, bridge connection, 15 destinations, valid entrances, walkable paths and collisions.

**Browser gameplay gates (desktop AND simulated landscape touch):**
- 3D world loads, no 404/missing .wasm/.pck assets.
- At least one animated character visibly present.
- Mouse click and mobile tap building selection.
- Walk route preview and character arrival.
- No walking into water/building wall.
- Bridge crossing works.
- Ferry and tube actions route to correct target and charge proper design times.
- Camera Explore/Inspect mode behavior and Reset.
- Zoom and pan gestures, UI tap targets, labels and safe areas.
- Same URL loads on desktop and mobile-sized browsers.

**Visual review (attach screenshots to PR or committed docs):**
- full-world 60° overview (our most important acceptance shot);
- 55° and 70° framing comparison;
- west island buildings;
- east island buildings incl. Trader;
- both outer tube landmarks;
- central ferry & bridge;
- Cooper close-up at Settlements;
- Cooper actually walking near buildings;
- desktop browser screenshot;
- phone landscape browser screenshot.

**Visual fail conditions:**
- two tiny packed flat slabs with all offices next to each other;
- all architecture still built from identical cubes;
- tube pair placed near central docks;
- missing Trader or Operations on wrong island;
- no imported authorized ready-made 3D assets;
- no character locomotion;
- only ZIP/PR with no public deploy;
- photorealistic heavy shaders that break mobile.

First-run acceptance should look like a considerable step toward a real playable premium tabletop world, even though interior quests are still out of scope.

## 12. Deliverables / reporting

Complete independently as much as technically feasible; use progress checkpoints internally, do not block on small questions already covered in this file. If a dependency is genuinely impossible, keep shipping the parts that work.

Provide:
1. PR link in private Telanico-3D-Lab.
2. Successful Blender/Godot/Web test Actions links.
3. Live site URL and verified public deployment run/link + exact build commit/version.
4. Downloadable editable .blend, Godot .glb, route/layout JSON as private Actions artifacts.
5. docs/ASSET_MANIFEST.md with actual imported ready-made third-party meshes and license checks.
6. docs/OVERWORLD_DESIGN_V2.md with layout decisions and old VorGun correspondence.
7. docs/PREVIEW_RELEASE.md with automatic publication contract.
8. Short test results, screenshots, important unimplemented gameplay, any permissions block.

**Success = noticeably better 3D world + playable character + browser controls + verified PUBLIC DEPLOY, not just a finished PR.**

### Explicit exclusions
- No production VorGun changes.
- No rewriting dialogue/story/invoice mechanics or office interiors.
- No adding expensive paid packs, asset piracy, or publishing any private tokens.
- No final mascot likeness claim for an experimental badger head.
- No large UI redesign unrelated to world navigation.
- No blocking on non-essential cosmetic tweaks before shipping the playable world.

BEGIN NOW: Audit the two repos, set up the branch, import usable free assets, upgrade the world, develop gameplay, run full cloud validation, and deploy the new public preview without manual owner action.
