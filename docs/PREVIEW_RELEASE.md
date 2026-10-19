# Automatic preview release

The private feature branch `codex/telanico-overworld-v2` is the sole allowlisted source for V2. No private main merge is required. Open PR updates run **Godot Web playable**: pinned asset fetch → headless Blender → geometry/provenance validation → Godot import → real physics gameplay tests → single-thread Compatibility Web export → desktop/touch browser tests. Only after all gates pass is `telanico-3d-web` uploaded. Source models and evidence remain separate private artifacts (14-day retention).

The public repository `sgdenikin-sys/Telanico-3D-Web` runs **Import tested 3D Web build** on importer changes and every ten minutes. It uses the already configured `TELANICO_LAB_ARTIFACT_TOKEN` with private Actions read access. No new secret, copied run number, manual ZIP or owner workflow restart is needed. Scheduling can be delayed by GitHub.

The importer chooses the newest run of the exact named workflow/branch. Pending, failed, missing, expired or older-than-14-day candidates fail visibly and preserve the previous live snapshot. It verifies source head SHA, branch and run ID against `build.json`, single-threaded config, WASM/PCK signatures and an exact public runtime filename allowlist before replacing anything. An identical commit is an idempotent no-op. Source Python, Blender files, vendor archives, credentials and test logs are never copied to the public repository. The PCK intentionally contains the playable compiled project and licensed runtime assets.

A changed verified snapshot is committed to public main and deployed using the existing GitHub Pages environment. The publishing job then checks the **actual HTTPS** `build.json` and starts the hosted WebGL game at desktop and phone-landscape dimensions, requiring the expected commit and all 15 destinations. A green artifact import without hosted runtime verification is not considered release proof. The public HUD displays the short source SHA; `build.json` exposes the full identifier.

Live URL: https://sgdenikin-sys.github.io/Telanico-3D-Web/

To download editable models on iPhone: open the private PR → Checks → successful Godot Web playable run → Artifacts → `telanico-web-source-models`. Save its ZIP to Files. `telanico-3d-web` is the downloadable browser bundle; the live URL is the convenient way to play without locally serving WASM. Artifacts require a signed-in GitHub account with private repository access.
