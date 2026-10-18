# Instructions for AI coding agents — Telanico 3D Lab

## Scope and priorities
You are working in the isolated Telanico-3D-Lab experiment. Never edit the existing production Telanico Trading game or its repositories as part of tasks here unless the user explicitly requests that.

The objective is to prototype a 3D **overworld map only**. Indoor offices, 2D character dialogue, story quests, invoice UI, and game-time logic are preserved for eventual integration.

## Visual direction
- Style: **Kenney+ / soft premium tabletop board-game diorama**. Compact miniature environments, soft beveled edges, restrained material colors, intentional composition, pleasant lighting.
- Not photorealistic and not children's toy-plastic. Avoid excessive saturated colors, realistic metropolitan street layouts, or unnecessarily detailed interiors.
- Preserve the two-island map concept with named office buildings as navigational destinations.
- NO road network unless the user subsequently authorizes it; movement can use bare ground/pathfinding.
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
