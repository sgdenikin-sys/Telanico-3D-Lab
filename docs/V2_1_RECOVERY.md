# V2.1 recovery and validation

The interrupted art pass was recovered without resetting either worktree. The
V2 baseline remains `f3949d6` on `codex/telanico-overworld-v2`; checkpoint
`df3b1f2` preserves the V2.1 sources and WebGL comparison captures. Editable
models and ignored output were backed up before regeneration, and remain private
Actions artifacts rather than public source files.

The checkpoint CI exposed a timing error in the native Follow test: twelve
process frames were treated as enough time for the easing camera to converge.
A fast headless runner reached its frustum assertion too early. The test now
waits for actual convergence, bounded by five physics seconds; camera behavior
is unchanged.

The earlier 1920x1080 failure screenshot alone did not establish its cause.
The recovery reproduction reached and passed Finance selection/cancellation.
Browser coordinate synchronization now counts distinct Godot telemetry frames,
rather than repeated polls of one potentially stale UI position. This is test
instrumentation only. Failure state JSON, screenshots, Playwright traces and
console/HTTP errors are retained in the private evidence artifact. `--case 1920`
is available to reproduce that viewport alone.

No approved mobile UI, viewport layout, gesture handler, production game,
office placement, vegetation pack or feature was changed during recovery.
The preserved V2.1 camera/art behavior belongs to the recovered checkpoint.

Release gate: regenerate Blender → validate GLB and 15-landmark layout → import
Godot → native physical journeys → single-thread Web export → desktop/touch
browser suite. The public importer must consume the exact successful run ID,
match its source SHA and build metadata, and pass hosted HTTPS/WebGL checks.
A local build or Draft PR is not release evidence. Final run and deployment
links are recorded on the Draft PR once those gates complete.
