# V2.2 playable integration — release candidate

Continues checkpoint `33371dc` and Draft PR #8. Source remains pinned to
VorGun `fc5e861`; see MIGRATION.md for the unchanged canonical inventory.

## Milestones

- `a32ee83`: world/session adapter, physical journey and explicit office entry/return.
  Actual-world integration test passes 29 assertions: walking, slow bridge,
  scheduled ferry wait, tube, modal locks, exact entrance return and single charge.
- Original approved HUD/invoice/office/character artwork copied byte-for-byte.
  Source office composition helpers and invoice renderer reused; presentation is
  separate from story rules. Shared state persists across invoice/assistant/offices.
- Intro -> locked character selection -> Cooper's draft -> assistant -> world.
  NPC dialogue lines, live options, source financial rules, lunch and outcomes remain
  in the pinned session. No Coffee/Archive quest content invented.
- Actual-geography playthrough passes 104 assertions, finishes **13:54**:
  Operations -> Contracts -> Trader -> VAT -> FX -> LC Desk -> Settlements, using
  the matching tubes when faster. The historical itinerary fails here; no walking
  speed, geography, deadline, financial prerequisite or lunch window was changed.
- Native landscape UI/invoice, deadline, Game Over and actual scene restart pass.
- Original browser audio singleton and lifecycle mock suite reused. Original MP3
  reconstructed losslessly from source chunks, SHA-256
  `dc0869cab4b4843c02f3428ab429e826794e4866bed9d1fbcfafffb6a080cef5`.
  Native playback is stopped/released on teardown; Web restart preserves one owner.

## Testing and release gate

`tools/build_web.sh` now retains all V2.1 generator/GLB/navigation/export checks
and gates on session (61), source parity (1116), world integration, real story
playthrough and UI/restart tests. Browser audio mock checks run before export.
`tools/test_story_browser.py` uses real canvas mouse/touch actions, original art,
incorrect/correct answers, invoice review, assistant, a complete phone victory
route and restart. Screenshots/traces/failure state persist under
`build/screenshots/story`. Existing four-case V2.1 browser suite uses `?test=1`
as a standalone navigation fixture; story QA adds `&story_test=1`. Ordinary
players always see the original story opening. QA probes expose state/coordinates;
they do not grant facts, skip travel, mutate the quest or change route costs.

UI placement changes only replace the old debug HUD and place the existing camera
buttons below the new clock. The Safari viewport/safe-area implementation and
world gesture algorithms are retained. Invoice supports scroll, +/- zoom and
pinch; navigation is blocked during every story modal and office.

**Release is pending complete browser/CI validation.** Do not import an unfinished
or failed candidate over public V2.1. Publish only the exact successful private
`telanico-3d-web` artifact; never private Blender sources or development files.
