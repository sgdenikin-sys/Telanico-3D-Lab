# Telanico 3D Lab

An isolated experiment replacing the world map of Telanico Trading with a soft, tabletop-style 3D diorama while preserving the original gameplay. V2.2 integrates the original offices, story, invoice, assistant, audio and game rules. The production game repository is separate.

## Current release and working process

V2.2 is live at https://sgdenikin-sys.github.io/Telanico-3D-Web/ .
Start with [project workflow and continuity rules](docs/PROJECT_WORKFLOW.md),
[current publication procedure](docs/PREVIEW_RELEASE.md), and the
[verified release record](docs/v2-2/RELEASE_2026-10-23.md).
The sections below retain earlier setup/blockout history; do not use them to
infer the current release, installed tools or deployment availability.

## Historical overworld blockout

The current preview uses the first two-island overworld: settlements/support in
the west, operations/documents in the east, a central ferry channel, one north
pedestrian bridge, and matching pneumatic towers. See
[layout decisions, rendered views and travel calibration](docs/overworld/README.md).

```bash
blender --background --factory-startup --python-exit-code 1 --python blender/scripts/build_overworld.py
python3 tools/validate_overworld.py
python3 tools/validate_glb.py godot/assets/generated/overworld.glb
```

Open `godot/project.godot` to view it; drag, pinch and Reset remain available, plus
**Landmarks** for names. `bash tools/build_web.sh` now generates this overworld
before exporting the Web preview. In Actions, **Blender overworld blockout**
uploads `telanico-overworld-models`; **Godot Web playable** uploads the Web build,
source models and layout JSON. Select `codex/two-island-overworld` for this pass.
No deployment or branch merge is configured.

The smoke-test instructions below document the earlier single-island prototype.
Its generator remains available for regression/reference; its asset paths are
not the ones used by the current Godot preview.

## Principles

- Visual direction: **Kenney+ / premium tabletop diorama**: soft, restrained colors, readable silhouettes, tasteful bevels, warm light, and an adult-proportioned Cooper honey badger.
- Two islands; buildings are destinations. **No city road network**. Short walking or running transitions may use open paths in the landscape.
- Work in this repository only. Never edit or copy from the production Telanico Trading repository unless expressly requested.
- Blender generates editable source files (.blend) and Godot interchange files (.glb). Code is reproducible on Windows or headless Linux.
- Start without external asset-pack downloads. Import CC0 packs later only after checking license terms and authorship.

## Project layout

- AGENTS.md — permanent instructions for Codex.
- blender/scripts/build_smoke_test.py — procedural Blender diorama generator.
- blender/generated/ — local .blend output (not checked into Git).
- godot/project.godot — isolated Godot 4 test project.
- godot/scenes/main.tscn — simple 3D viewer for the generated model.
- godot/assets/generated/ — .glb output (not checked into Git).
- tools/run_blender.ps1 — Windows one-command Blender generation.
- tools/validate_glb.py — basic output validation using Python stdlib.
- infra/Dockerfile — foundation for a future Linux VM/container.
- .github/workflows/blender-smoke.yml — manually triggered Linux build and downloadable artifacts.

## Start on Windows (recommended)

1. In **GitHub Desktop**, choose File > Clone repository > sgdenikin-sys/Telanico-3D-Lab and clone to a working directory (e.g. Documents/GitHub/Telanico-3D-Lab).
2. Open **PowerShell in the cloned repo root** (the folder containing this README).
3. Run the smoke test:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_blender.ps1
~~~

The script looks for blender.exe on PATH or under Program Files/Blender Foundation. It generates:
- blender/generated/smoke_test.blend
- godot/assets/generated/smoke_test.glb

4. Open the file **blender/generated/smoke_test.blend** in Blender to confirm that geometry is editable.
5. Open **godot/project.godot** via the Godot Project Manager. Press F6 on scenes/main.tscn or F5 for the project to view the exported diorama.
6. Open a terminal in the repository root and start Codex using **codex** (or select the cloned folder in the Codex app). Sign in with ChatGPT when prompted.

Suggested first Codex prompt:
> Read AGENTS.md and README.md. Inspect the Blender generator, Godot viewer, and output validation. Check which tools are installed before running anything. Make one small improvement to the tabletop island smoke test; regenerate and validate it. Work on a feature branch and describe exactly what you tested. Do not change the production Telanico game.

### If the Blender command is not found
Open blender.exe normally to verify installation. You can run it using its full path. The PowerShell helper checks the usual Program Files location; if installed elsewhere, add its folder to PATH or edit the helper's path.

## Codex Cloud / iPhone

Open https://chatgpt.com/codex, connect your GitHub account, enable this repository for Codex if prompted, and create/select an environment using **sgdenikin-sys/Telanico-3D-Lab**. Those account authorizations must be completed interactively by the repository owner.

The local Blender installation is **not** automatically available in a cloud Codex environment. For headless 3D generation, its environment must install Blender, or run builds using the included GitHub Actions workflow / a future VM. Outputs from these environments must be explicitly committed or uploaded as artifacts.

## Headless Blender (Linux/VM)

~~~bash
blender --background --python blender/scripts/build_smoke_test.py
python3 tools/validate_glb.py godot/assets/generated/smoke_test.glb
~~~

A starting Dockerfile is provided under infra/. This makes the generator portable to a Linux VM; it is not an already-provisioned server. Geometry export can run CPU-only. Photorealistic rendering or interactive Blender over remote desktop may later need GPU support.

## Playable Web build (landscape iPhone Safari)

The first interactive Web viewer preserves the two offices and Coffee Area.
Drag one finger to rotate the island; spread/pinch two fingers to zoom. **Reset
view** restores the initial camera. Desktop users can drag with the left mouse
button and zoom with the wheel. Portrait shows a rotate-to-landscape prompt;
Safari may not honor programmatic orientation locks, so rotate the device yourself.
This is an interactive diorama, without character movement or office interiors.

The `Web` preset uses Godot **4.6.3**, the Compatibility/WebGL 2 renderer,
**single-threaded** WASM, no GDExtensions, and no service worker. It does not
require `SharedArrayBuffer` or COOP/COEP headers. iOS Safari 17+ with WebGL 2 is
the intended baseline; a physical iPhone still needs a device check. The browser
smoke test uses Chromium touch emulation, which does not prove iOS compatibility.

### Download the playable artifact on iPhone

1. Sign in to GitHub in Safari. Open this PR's **Checks → Godot Web playable**
   run, or find the run for `codex/playable-web-smoke` in **Actions**.
2. Wait for success, open **Summary → Artifacts → telanico-3d-web**, and download
   the ZIP. Artifacts are retained for **14 days**. Extract it using **Files**.
3. Keep the entire folder together: `index.html`, `index.js`, `index.wasm`,
   `index.pck`, both audio worklet scripts, splash image, and icons. Opening
   `index.html` directly from Files is not a playable preview: WebAssembly and
   resource fetches require an HTTP(S) server. Downloading and playing are separate.
4. For a new build, use **Actions → Godot Web playable → Run workflow** and select
   `codex/playable-web-smoke`. Safari's **Request Desktop Website** may help
   expose these controls.

No deployment is configured. `sgdenikin-sys/Telanico-3D-Web` is only the future
public hosting target; this workflow never pushes to it or enables GitHub Pages.
To test on a physical iPhone before public deployment, an authorized private
HTTPS preview is needed. A GitHub Actions artifact is a download, not a hosted game.

### Reproduce and verify in Linux/cloud

Install Blender (including NumPy), Python 3, ripgrep, Godot 4.6.3 and its matching
`web_nothreads_release.zip` export template in
`$XDG_DATA_HOME/godot/export_templates/4.6.3.stable/` (normally
`~/.local/share/godot/export_templates/4.6.3.stable/`). Then run:

```bash
bash tools/build_web.sh
python3 -m pip install playwright==1.58.0
python3 -m playwright install --with-deps chromium
python3 tools/test_web_browser.py build/web
# Optional local preview (not a public deployment):
python3 -m http.server 8000 --directory build/web --bind 127.0.0.1
```

`build_web.sh` regenerates `.blend` and `.glb` using headless Blender before
Godot import, checks both offices and Coffee Area, tests gestures, exports Web,
and validates runtime files and their declared sizes. The browser test starts
a temporary loopback HTTP server without isolation headers, checks WebGL startup,
touch rotation/pinch/reset, portrait blocking and landscape recovery, and rejects
browser errors or missing HTTP files. CI uploads the playable ZIP only if these
checks pass, plus separate source-model and test-evidence artifacts. Generated
binaries, Web output and browser screenshots are not committed.

## Binary assets and version control

### Download the two-office + Coffee Area models on iPhone

The Coffee Area scene builds on `codex/second-office-smoke` and preserves both
offices. Its small terracotta kiosk has a cream cup sign and a matching bench.

1. Sign in to GitHub in Safari and open the Coffee Area pull request.
2. Open its **Checks** tab and the **Blender smoke test** run. Alternatively,
   open the repository's **Actions** tab and select that run. Confirm the run
   belongs to the latest Coffee Area commit, rather than `main`.
3. After the build succeeds, open the run's **Summary**, scroll to **Artifacts**,
   and tap **telanico-smoke-test-models** to download the ZIP.
4. Open the ZIP in the iPhone **Files** app to extract
   `blender/generated/smoke_test.blend` and
   `godot/assets/generated/smoke_test.glb`.

Artifacts expire after **7 days**. To rebuild, open **Actions → Blender smoke
test → Run workflow**, choose **codex/coffee-area-smoke**, and run it. If Safari
hides the controls, use **Request Desktop Website**. No merge into `main` or
home computer is needed; downloading these files does not require Blender on
the iPhone. This workflow generates and validates the GLB; Godot import is
checked separately in the cloud environment.

The **Python scripts and Godot scenes are versioned**. Generated .blend/.glb files are ignored for the smoke test to keep the repository lightweight and builds reproducible; GitHub Actions uploads them as build artifacts.

When original, hand-edited .blend assets need permanent versioning, enable Git LFS on all development machines and explicitly track approved source files. Avoid committing entire unreviewed asset-pack ZIPs.

## Next milestones

1. Validate the Blender → .blend → .glb → Godot chain locally.
2. Set up Codex Cloud GitHub environment, then test unattended Linux execution.
3. Add curated Kenney / KayKit / Quaternius assets with recorded licenses.
4. Build one polished modular office and a small island without roads.
5. Prototype Cooper's adult-proportioned figurine and short walking animations.
6. Only then explore integration into the presentation game's existing world-map transitions.
