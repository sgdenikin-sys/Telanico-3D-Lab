# V2.2 paused checkpoint — 2026-10-21

Paused explicitly by the owner. **Do not resume implementation, merge or deploy
until the owner asks.** All implementation is committed and pushed on
`codex/telanico-v2-2-story-integration`; existing Draft PR:
https://github.com/sgdenikin-sys/Telanico-3D-Lab/pull/8

Last implementation commit:
`1a5d4e7b716aee653b56ec5d64e76aa782b9157c`.
The subsequent handoff commit only preserves documentation and previously prepared,
unapplied public-import files. Its `[skip ci]` message avoids starting another build.

## Implemented milestones

- Shared canonical session connected to actual V2.1 walking/bridge, three-minute
  tube, scheduled ferry wait plus five-minute sailing. Single travel charge.
- Arrival remains outside; explicit Enter opens the original illustrated office;
  Leave restores the exact entrance, preserving state. Modal navigation locks.
- Original intro, Cooper-only selection, illustrated offices/portraits, approved
  HUD artwork and invoice renderer, assistant feedback/reviews, analog/game clock,
  menu/audio controls, victory/loss and restart are connected.
- Original music reconstructed losslessly from pinned source chunks, browser
  singleton retained; native audio teardown corrected.
- All nine canonical offices covered by native physical-journey tests. Coffee and
  Archive remain non-quest landmarks. Geography, models and gesture algorithms
  are preserved. No original VorGun source files were changed.
- Mobile story controls now use CSS-sized coordinates inside the unchanged
  viewport; GUI controls are retired after callbacks instead of removed mid-click.

Authority remains read-only VorGun commit
`fc5e861f0c899ae5925625ff2191a41d7043d957`. Do not rebuild session rules or repeat
inventory. Read MIGRATION.md and IMPLEMENTATION.md for provenance/design decisions.

## Verification: passed versus blocked

Latest implementation CI:
https://github.com/sgdenikin-sys/Telanico-3D-Lab/actions/runs/39514919611
Job `118944837348` **failed**, specifically the story/iPhone browser step.

Passed in that run:
- Blender generation, layout/GLB validation, Godot import and single-thread Web export.
- Existing session assertions (61) and source parity comparisons (1,116).
- World/session integration (29 assertions).
- Actual-geography winning playthrough (104 assertions), invoice sent at **13:54**:
  Operations -> Contracts -> Trader -> VAT -> FX -> LC Desk -> Settlements,
  using the matching tubes for cross-island journeys.
- Optional offices/repeat visit/Compliance integration (36 assertions).
- Landscape UI/invoice, menu/audio, deadline/Game Over and real scene restart.
- Canonical audio lifecycle mocks, iPhone and desktop cases.
- Existing V2.1 browser suite: 1920, 1440, 844 and 667 cases.
- Desktop story browser: opening, wrong/correct answer, invoice/assistant,
  office return, menu and independent SFX control.

Unresolved release blockers (do not assume causes):
1. CI phone story test times out waiting for `state === 'TUBE'` in
   `tools/test_story_browser.py:transfer`, after reaching `tube_w` and pressing Tube.
   Determine from saved probe/trace whether the transient state was missed or the
   interaction failed. Do not weaken assertions without evidence.
2. Local phone run reaches Contracts then fails with
   `Missing or unstable story control contract_terms`. Failure JSON still lists
   `contract_terms` as a canonical choice, at minute 36. Investigate scroll/hitbox/
   telemetry stability versus actual UI before changing canonical rules.
3. No complete phone-browser victory/restart has passed. Real Safari hardware
   is untested; cloud phone coverage uses Chromium touch plus iPhone user agent.
4. No successful final private Web artifact is approved for publication.

CI evidence (logs, screenshots, Playwright traces, failure probes):
https://github.com/sgdenikin-sys/Telanico-3D-Lab/actions/runs/39514919611/artifacts/12311765573
Retention is 14 days; download before it expires. Local evidence remains in
`build/screenshots/story/` and `/workspace/scratch/v22-*.log` (ignored, not Git assets).

## Deployment status and preserved preparation

**No V2.2 deployment and no merges.** Public repository remains unchanged and
pinned to V2.1 `8319d91c56be7bfbd25535a5a802e5e7de44662c`, private run `39494743117`.
The public `Telanico-3D-Web` worktree was clean at pause.

`deferred-public-prep/` preserves files previously prepared in
`/tmp/telanico-v22-public-prepare/`, not applied to the public repository:
- importer allowlists for V2.2 runtime audio/branch while retaining V2.1 support;
- 13 importer safety tests, previously passed in isolation;
- hosted intro -> Cooper -> draft -> assistant -> map verification workflow.

These are **draft preparation**, not deployed or validated against a successful
V2.2 artifact. No new release pin is included. Do not apply them merely because
those isolated unit tests passed. Only after owner-authorized resumption and a
fully green private run should the exact artifact/run/SHA be pinned and imported.

## Safe resumption

1. Confirm branch/head and clean worktree; preserve independent improvements.
2. Read failed CI evidence first. Reproduce targeted phone failure with
   `python tools/test_story_browser.py build/web --case 844`; use current export.
3. Resolve phone interaction/telemetry blockers, preserving all canonical tests.
4. Rerun complete private workflow before any future deployment.

Cloud commands require writable XDG paths:
`XDG_DATA_HOME=/tmp/telanico-overworld-data`
`XDG_CONFIG_HOME=/tmp/telanico-overworld-config`
`XDG_CACHE_HOME=/tmp/telanico-overworld-cache`.
Local HTTP/Playwright execution also needs the managed tool's network permission.
Source checkout: `/workspace/VorGun-source-readonly` (read only).
No local browser test processes remained at the pause checkpoint.
