# Instructions for AI coding agents — Telanico 3D Lab

## Continuity and releases — read first
- Read [PROJECT_WORKFLOW.md](docs/PROJECT_WORKFLOW.md) before reporting status or preparing a release. Check the remote candidate and live metadata; one local checkout is not the whole project.
- Reuse the existing local machine, cloud workspace, installed tools, cached exporters, credentials and publication repository. Inventory them before proposing downloads, setup, new access or infrastructure. A missing PATH command is not evidence that a tool is absent.
- For an authorized interim release, freeze new features, fix the concrete blocker, and defer only confirmed broken components when the user permits it. Do not expand the release into a redesign or a new exhaustive test matrix.
- Diagnose the actual failed layer. If Actions executes zero steps, inspect check annotations using existing access before retrying or changing game code. A connector limitation is not proof that the account lacks access.
- Reuse build → runtime snapshot → existing GitHub Pages → live verification. Prefer an already usable build environment; do not rebuild the toolchain by default. Preserve honest provenance and rollback.
- Release authorization includes its routine necessary steps; do not ask conversational permission again. Obey mandatory runtime approvals, reuse applicable approved command rules, and distinguish sandbox prompts from missing credentials. Never bypass a denial or weaken security controls.
- Keep workflow/release records current. Completion requires the expected version at the public HTTPS URL plus desktop/phone-layout checks. State physical-device testing limits.

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
1. Inspect README, scripts and project state.
2. Create a feature branch for changes beyond the initial scaffold.
3. Prefer small changes that produce testable .blend + .glb outputs.
4. Run Blender in background if available, validate .glb, check the Godot scene if Godot is installed.
5. If a tool is unavailable, say precisely what was not tested and provide an exact command for a compatible environment.
6. Open a PR with summary, testing evidence and visual samples where practical.
