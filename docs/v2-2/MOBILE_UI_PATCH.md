# Mobile UI correction — 24 October 2026

Development remains on Lab/main. iPhone and desktop load the same single-thread
Compatibility Web runtime; there is no independent iPhone publication branch.
Before this patch the deployed carrier was Web/main e5906f7, game source 4909d8f,
verified by public Pages run 40064787666. That release remains in history for rollback.

## Evidence and targeted corrections

- HUD textures used KEEP_ASPECT_CENTERED inside unrelated fixed button bounds.
  Original PNG separators/padding were also included. The original VorGun
  `_set_hud_button_art` crop was consulted; this patch clips detached separators
  and the remaining transparent gap down to the opaque frame (Menu y=15,
  Assistant y=14), and trims Invoice to its illustrated frame. The final artwork
  fills its actual Button rectangle, so input, artwork and runner share bounds.
- Only the normal state was styled/cleared. Hover/pressed/focus could fall back
  to Godot's unrelated default surfaces. All button states now explicitly use
  their approved asset or matching brass/navy surface. Camera/travel controls
  have a legible plate and retain **no animated perimeter**.
- Short-screen HUD sizes were clamped by the old 52px custom minimum while
  positions assumed a shorter button. Set the minimum and layout together;
  short landscape buttons are 44 CSS px, with no overlapping rows.
- Assistant was inside a vertically shrinking outer ScrollContainer with a
  full-width footer. With Safari toolbars the footer clipped the portrait and
  speech. The portrait is now outside that scroll; the speech and fixed 44px
  Continue button share the right column. Only advice text scrolls. The actual
  canonical `hud_assistant_video_frame.png`, original GIF/PNG bridge and timing
  are retained. Construct footer in its final container instead of reparenting
  a previously laid-out footer. The fixed footer leaves readable text height.
- Restore VorGun's `#102331EF` brass-bordered clock plate; keep analog art and
  authoritative game time visible in the world and offices.
- Position the office Menu inside the same safe insets as the world HUD.
- Clamp modal windows inside safe areas. Keep Select Cooper in the persistent
  footer rather than below clipped character cards.

Geography, lighting, vegetation, routes, gestures, story facts, travel costs,
invoice and original read-only VorGun source are unchanged.

## Validation scope

Native build gates include Blender/GLB, 61 session assertions, 1,116 source parity
comparisons, 29 movement/session assertions, 104 winning-route assertions
(victory 13:54), 36 optional-office assertions, original V2.1 navigation,
audio lifecycle, atmosphere and native UI/Restart. Native UI now also covers
844×306 and 667×280.

`tools/test_mobile_ui.py` exercises Retina DPR 3 (render buffer capped at 2),
47px left/right and 21px bottom safe insets, 844×306 → 667×280 → 844×390
without resetting the session, original frame, text/footer separation, clock
plate, matching artwork/input rectangles, and actual edge taps. This is cloud
Chromium with iPhone UA and touch, not a physical iPhone Safari certification.
The focused UI suite uses DPR 3; the full story keeps standard DPR 1 to avoid
repeating high-resolution software rasterization for every dialogue action.
CSS-space touch geometry is checked in both suites; no product renderer or
viewport setting is changed.

The first Web export was blocked by an absent ephemeral template cache after
workspace restart. Restored the official matching 4.6.3 single-thread release
template using the existing range-download helper; no version or workflow
change. Initial visual runs were intentionally stopped for fixes and are not
reported as a completed final pass. The native moving-runner assertion now
waits 0.4s instead of 0.15s, because a 22px segment can remain at its corner clamp
for the shorter interval even while its path distance advances normally.

Final browser/deployment results are recorded alongside the release evidence.

On cloud Chromium 154/SwiftShader, repeated full-page captures and trace DOM
snapshots made the functional suite spend minutes in WebGL readbacks. An
independent CDP observation confirmed the game had reached `world/invoice` and
its frame counter continued (67 → 83); the desktop invoice screenshot also
completed. This was slow evidence capture, not a stopped quest/session. Added
an explicit `--no-screenshots` option for the full functional run; all gameplay,
touch, UI, audio and result assertions are unchanged. Separate Retina visual
suite retains its screenshots and JSON geometry, and the public verifier still
captures the delivered website. No product rendering setting was reduced.

The first full Retina route stopped at a test telemetry assertion after Contracts
→ Trader. The captured failure contains world `current=trader`, `IDLE`, last
walk cost 9 and session time 48 (39 + 9), with errors=[]; `_arrive()` charges
Session immediately, while world/story browser probes are published separately.
The test waited only for world arrival, then immediately read the older story
probe. It now waits for the time probe too and asserts the **exact** charged
delta against last_trip.minutes. The game rules were not modified. The failed
run is preserved separately; the unchanged successful desktop case is retained
and the full phone case is rerun on the same exported product.

Final local validation: desktop and complete phone route passed on game source
`f593e4b`, victory 13:54 and clean Restart, no runtime/resource errors and one
music owner. Retina visual suite passed on `620fad1`; subsequent product change
only adjusts office Menu safe insets, covered by final native/UI and story run.
See [results](evidence/mobile-ui-results.json) and the matching evidence logs.

## Verified public release

[Pages and actual live browser validation, run 40118149777](https://github.com/sgdenikin-sys/Telanico-3D-Web/actions/runs/40118149777)
completed successfully on public main `7f1d283`. All 24 HTTPS runtime hashes and
the embedded in-game source `f593e4b` matched the tested snapshot at desktop
1280×720 and Retina touch 844×306 with safe insets, followed by resize to 390.
Clock plate, original Assistant frame, aligned artwork and control scaling
passed on the real public site. Evidence artifact: `live-validation` 12570103059.

[Play this release](https://sgdenikin-sys.github.io/Telanico-3D-Web/?release=f593e4b).
Physical iPhone Safari remains untested. The previous runtime is recoverable
by reverting public publication commit `7f1d283` (previous main `e5906f7`).

Private auto-run 40118100126 again failed before runner assignment (runner 0,
zero steps); it did not test or publish anything. The successful existing public
publisher is the release evidence. No new workflow, importer, branch or PR.
