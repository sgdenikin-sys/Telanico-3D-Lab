# HISTORICAL — superseded by main → Pages

Do not apply these cross-repository importer preparations. See docs/PROJECT_WORKFLOW.md.

# Unapplied public importer preparation — recovery refresh 2026-10-22

These files are private review material, not active workflows or a deployment.
Updated against public origin/main bf963ab and recovery/v22-release-20261022.
No successful V2.2 Actions artifact or release pin exists yet. Do not apply until
all private release gates pass for the exact source commit/run.

Retains the existing artifact importer and its manual-only workflow dispatch.
Adds only the exact recovery branch, required authored audio runtime files and
hosted original-story opening verification. V2.1 remains trusted for rollback;
the abandoned PR #8 branch is not trusted. No schedule, push import, public source
build, provisional acceptance or alternative publishing pipeline is introduced.
Only required runtime files may be public. The nested .github directory here is
documentation storage, not an active private workflow.

After private success: apply the reviewed importer/tests/workflow to the latest
public main without overwriting independent changes, pin exact successful private
run/SHA, invoke Import tested 3D Web build with source_run_id, and verify the live
V2.2 intro -> Cooper -> original invoice -> assistant -> overworld at both sizes.
Keep V2.1 run 39494743117 / commit 8319d91 available for rollback. The public
repository's existing release pin and deployed runtime have not been changed.
