# Instructions for AI coding agents — Telanico 3D Lab

## Current workflow — owner decision, 23 October 2026
- Actual publication exception, subsequently authorized by the owner: source
  development stays on Lab/main; use the existing Web/main Pages workflow for
  the current preview while direct Lab Actions fails before runner assignment.
  The current verified release is run 40118149777 (game source f593e4b). Consult the actual status
  at the top of docs/PROJECT_WORKFLOW.md; do not confuse the desired Lab-only
  migration with a completed migration, or revive the old artifact importer.
- Read docs/PROJECT_WORKFLOW.md first. One repository: Telanico-3D-Lab.
- Work directly on main. Do not create feature/recovery/release branches or PRs
  unless the owner explicitly requests one. Historical task prompts do not override this.
- Preserve existing work. Never reset, force-push or overwrite independent changes.
- Reuse installed Blender/Godot, caches and existing access. Build and test the
  changed scope; do not expand release work or repeat exhaustive checks without cause.
- Stage tested runtime into this repository's site/ with tools/stage_web_release.py;
  verify with tools/verify_release.py; commit/push main. Publish game is the only
  active Lab workflow. No new repositories, pipelines, artifact importers or
  cross-repo secrets; the documented existing publication exception takes precedence.
- Check Pages and actual HTTPS metadata before claiming a release; distinguish
  recorded checks, newly executed checks and physical-device testing.
- No automatic repo visibility changes or deletion of historical work. Runtime
  approvals still apply; a connector limitation is not absence of account permission.

## Bounded execution and validation — mandatory

**Owner priority: conserve Codex context and usage limits. A small UI change must
not trigger a project-wide audit, test cascade, infrastructure investigation or
unrelated repairs. Finishing the requested patch takes precedence over broad
confidence-building.**

- **Scope first:** Read only the task-relevant files plus `AGENTS.md` and the
  *current workflow summary* in `docs/PROJECT_WORKFLOW.md`. Inspect additional
  source only when a concrete dependency requires it. Do not re-audit the
  repository, entire branch history, architecture, dependencies or pipelines.
- **Smallest patch:** Fix only the requested behavior. Do not opportunistically
  refactor other UI, game logic, assets, releases or tooling.
- **Finite verification budget for a normal UI patch:** At most ONE necessary
  Godot import/build smoke check and ONE targeted browser/viewport check for
  the affected screen (iPhone landscape about 844x390). If a relevant check
  fails because of the patch, make at most ONE focused correction and rerun
  only that failing check ONCE. Then stop and report evidence; do not begin
  another fix/test loop autonomously.
- **No broad tests by default:** Do not run full story playthroughs, entire
  browser/device matrices, full regression suites, repeated CI jobs, unrelated
  visual snapshots, or Blender rebuilds when assets were not changed.
  Run these only on the owner's explicit instruction or when a clearly
  identified blocker makes the specific extra check essential; explain that
  necessity before proceeding.
- **Separate publication from patching:** A UI-only patch does NOT imply staging,
  pushing runtime to the public Web repository, Pages verification or release
  smoke tests. Deploy only when explicitly requested in the current task.
  Preserve the existing working publication path; do not change CI/CD,
  secrets, repository settings or permissions.
- **Stop on environment blockers:** No installing tools, requesting new access,
  changing runner setup or inventing workflow alternatives. Record the exact
  missing capability/failure and stop.
- **Concise handoff:** State changed files, one-line outcome, checks actually
  executed (or not executed), and any unresolved blocker. Do not claim
  physical-iPhone verification based on desktop browser touch emulation.
- Explicit instructions in the current user task may enlarge the test/release
  scope; old prompts, historical plans and generic "thorough testing"
  language do not.

## Scope and priorities
You are working in the isolated Telanico-3D-Lab experiment. Never edit the existing production Telanico Trading game or its repositories as part of tasks here unless the user explicitly requests that.

The objective is a 3D **overworld map** preserving the established original indoor offices, dialogue, quests, invoice UI and game-time logic. V2.2 already integrates that gameplay; maintain it without restarting the map or redesigning the original game. Production repositories remain out of scope unless explicitly authorized.

## Visual direction
- Style: **Telanico premium stylized tabletop diorama**. Broad readable masses, soft bevels, restrained colors and distinct department silhouettes. Kenney is a readability reference, not a style to clone. Keep the first overworld pass simple and spacious.
- Not photorealistic and not children's toy-plastic. Avoid excessive saturated colors, realistic metropolitan street layouts, or unnecessarily detailed interiors.
- Preserve the two-island map concept with named office buildings as navigational destinations.
- Pedestrian pale-stone promenades, smaller stone paths, and dirt/gravel shortcuts are authorized for the overworld blockout. No asphalt, car streets, or vehicular road network.
- Cooper is an **adult honey-badger / European-badger-inspired anthropomorphic character**, not a childlike or grotesque mascot. Consistent face, strong silhouette, clothing. Do not redesign established IP without explicit approval.

## Technical contract
- Godot 4.x, target desktop browsers and landscape iPhone WebGL 2.0 via Compatibility renderer.
- Blender Python API (bpy); author reproducible scripts, not manual UI-only steps.
- Export Blender sources as editable .blend and Godot-ready .glb. Prefer glTF 2.0 for interchange.
- Scripts MUST work in Blender background/headless mode on Windows and Linux. Resolve paths relative to this repository, never hardcode a workstation location.
- Avoid dependencies, GPU rendering, and internet downloads for baseline smoke tests. Output scripts should be idempotent.
- Never claim Blender/VM/cloud commands were tested unless they were actually executed and logs checked.
- Keep geometry small and reasonable for mobile web. Use a simple static camera before implementing free camera control.
- Keep lighting and game-specific materials adjustable in Godot. External packages must carry known permissions/license metadata and be reviewed before adding to the project.
- Do not commit generated binary artifacts by default. For hand-edited source models, propose Git LFS first.

## Workflow
1. Inspect main, README and docs/PROJECT_WORKFLOW.md; preserve uncommitted work.
2. Implement the requested change directly on main.
3. Run relevant existing Blender/Godot/browser checks when the change needs them.
4. Stage and verify the tested Web snapshot in site/ when publishing.
5. Commit/push main and verify Pages/HTTPS. No routine branch or PR ceremony.
