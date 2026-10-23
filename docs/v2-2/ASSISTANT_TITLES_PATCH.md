# Assistant, button and time-loss presentation patch — 23 October 2026

Implementation commits: 6d695bd and 94f261e, directly on main.

- Assistant is anchored eight CSS pixels beneath the Assistant HUD button. The
  original `hud_assistant_video_frame.png`, clipped portrait, dark matte, ivory
  speech bubble and brass shell reproduce the pinned VorGun presentation. The
  unchanged original GIF-to-PNG bridge uses the inner portrait rectangle.
- HUD artwork, ordinary choices, menu controls, invoice controls and camera/travel
  buttons have larger hit areas. Office Invoice/Assistant occupy a separate wide
  footer row; the leave and scroll row remains reachable on short landscape screens.
- The original #85DEFF/105-pixel-per-second perimeter runner marks active HUD,
  office and camera toggles, and hovered/focused/pressed enabled buttons. The
  decoration ignores input, preserves artwork and does not alter touch gestures.
- The session emits actual charged minute deltas, without changing costs or rules.
  A separate input-transparent overlay displays number, MINUTES, then LOST! in
  three central beats. Rapid events queue; zero-cost actions emit nothing. At the
  deadline, feedback reports only the remaining minutes actually charged.

Validation before publication: complete Blender/GLB/layout, 61 session assertions,
1,116 source comparisons, 29 world-integration assertions, 104 full-geography
playthrough assertions (victory 13:54), 36 optional-office assertions, native UI and
V2.1 navigation/audio gates passed on 6d695bd. The final office-footer/active-state
adjustment in 94f261e passed native UI again at 667x375, 844x390 and 1920x1080,
including footer reachability, Assistant anchor/artwork, moving perimeter,
time-loss beat order/queue, zero cost and clipped deadline delta, and GUI restart.
Web export and runtime validation passed on 94f261e. Full final browser checks and
publication results are recorded in the companion evidence receipt when complete.

The initial browser candidate passed desktop gameplay; visual review identified
small office artwork buttons. That candidate was stopped before phone testing,
its log preserved, and the office footer was enlarged before final export/testing.
A transient environment transport interruption preserved files and the running
final browser process. Source commits were pushed for recovery.

Cloud evidence: build/logs/ui-titles-build.log,
ui-titles-native-final.log, ui-titles-export-final.log and
build/story-browser-release.log. Physical iPhone Safari is not tested.

The first final-runtime phone pass stopped on a new test assertion mixing CSS HUD
coordinates with Godot's 1558x720 render coordinates (844x390 CSS). Screenshot
confirmed the panel was correctly anchored. The test now converts coordinates
using viewport/CSS width; gameplay and viewport code were unchanged. Original
failure log: build/logs/ui-titles-browser-coordinate-failure.log. The final
release log combines the passed unchanged desktop case and rerun phone case.
