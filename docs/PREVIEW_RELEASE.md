# Current preview publication procedure

Read [PROJECT_WORKFLOW.md](PROJECT_WORKFLOW.md) first. Last verified release:
V2.2, product source `2c94a3f687e7174340360885e069336b73cf599e`, public runtime
commit `b096474845e9c0eeca4245086c97c592b43df304`.

Live: https://sgdenikin-sys.github.io/Telanico-3D-Web/
Successful Pages run: https://github.com/sgdenikin-sys/Telanico-3D-Web/actions/runs/39908236241
Evidence: [release record](v2-2/RELEASE_2026-10-23.md) and
[machine-readable results](v2-2/evidence/live-release-20261023.json).

## Existing chain

1. Select and record the exact candidate from private Telanico-3D-Lab.
2. Reuse a verified matching runtime or build with the existing local/cloud tools.
   Run relevant native and browser checks against that exact output.
3. Publish only the allowlisted runtime snapshot to existing Telanico-3D-Web.
   Preserve source metadata, runtime hashes and V2.1 rollback history.
4. Existing `.github/workflows/pages.yml` verifies the runtime and deploys site/.
5. Check actual HTTPS build.json and real desktop/touch gameplay. CI success
   alone is not live verification. Physical iPhone Safari is a separate check.

For V2.2 the private Actions jobs were refused before runner assignment with a
payment/spending annotation. The Windows workstation built and tested the runtime;
public metadata honestly says source_run_id=local. The public Pages Action ran
successfully. No account billing or security settings were changed.

The pinned Godot 4.6.3 editor/template, Playwright packages and browser are already
cached locally under ignored build/. Do not download them again as normal release
preparation. Bootstrap is recovery/setup support only. See the workflow inventory.

## Private artifact importer and rollback

The original design was private successful Actions artifact → public importer →
Pages. The public importer is currently **manual-only**, not scheduled every ten
minutes. Its retained V2.1 pin is a rollback source. Dispatching it now restores
V2.1; it is not the current V2.2 publication path.

When private Actions is usable again, inspect the actual workflow/allowlist/pin
before using that importer for another version. Never report a failed private run
as successful, invent an artifact run ID, or publish private source to move builds
onto public runners. Model/source artifacts and test logs stay private.
