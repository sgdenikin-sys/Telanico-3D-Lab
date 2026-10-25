#!/usr/bin/env bash
# Linux/cloud build. Godot and matching Web export templates must be installed.
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
blender_bin=${BLENDER_BIN:-blender}
godot_bin=${GODOT_BIN:-godot}
mkdir -p build/logs
python3 tools/fetch_assets.py
python3 tools/stage_settlements_hall_game.py
# Remove only this reproducible output so stale runtime files cannot mask failures.
rm -rf build/web
mkdir -p build/web
"$blender_bin" --background --factory-startup --python-exit-code 1 \
  --python blender/scripts/build_world_v2.py 2>&1 | tee build/logs/blender.log
python3 tools/validate_v2.py
python3 tools/validate_glb.py godot/assets/generated/overworld.glb
python3 tools/stamp_build.py --before
"$godot_bin" --headless --path godot --editor --import 2>&1 | tee build/logs/import.log
# Targeted safeguard for the replaced landmark; preserve existing full-story gates.
timeout 120 "$godot_bin" --headless --path godot --script ../tools/check_hall_overworld.gd \
  2>&1 | tee build/logs/hall-overworld.log
rg -q 'TELANICO_HALL_GAME_PASS' build/logs/hall-overworld.log
# Validate the shared rules and actual playable integration before exporting.
for story_test in test_story_session test_source_parity test_world_integration test_playthrough test_optional_offices test_story_ui; do
  timeout 240 "$godot_bin" --headless --path godot \
    --script "res://tests/story/${story_test}.gd" \
    2>&1 | tee "build/logs/${story_test}.log"
done
rg -q 'TELANICO_STORY_SESSION_PASS' build/logs/test_story_session.log
rg -q 'TELANICO_SOURCE_PARITY_PASS' build/logs/test_source_parity.log
rg -q 'TELANICO_WORLD_STORY_PASS' build/logs/test_world_integration.log
rg -q 'TELANICO_PLAYTHROUGH_PASS' build/logs/test_playthrough.log
rg -q 'TELANICO_OPTIONAL_OFFICES_PASS' build/logs/test_optional_offices.log
rg -q 'TELANICO_STORY_UI_PASS' build/logs/test_story_ui.log
node tools/audio_lifecycle_regression.js
if rg -n 'SCRIPT ERROR:|Assertion failed|ERROR:' build/logs/test_story_*.log build/logs/test_source_parity.log build/logs/test_world_integration.log build/logs/test_playthrough.log build/logs/test_optional_offices.log; then
  echo 'Story session/parity regression failed' >&2
  exit 1
fi
# Godot can log script errors without returning nonzero: require the test marker.
timeout 120 "$godot_bin" --headless --path godot --script res://tests/test_v2.gd \
  2>&1 | tee build/logs/viewer.log
# An assertion in an awaited helper can abort that helper while its caller
# continues. Reject every script error, even if a later test marker is printed.
if rg -n 'SCRIPT ERROR:|Assertion failed' build/logs/import.log build/logs/viewer.log; then
  echo 'Godot script/import assertion failed' >&2
  exit 1
fi
rg -q 'TELANICO_TEST_OK' build/logs/viewer.log
timeout 120 "$godot_bin" --headless --path godot --script res://tests/test_atmosphere.gd \
  2>&1 | tee build/logs/atmosphere-native.log
if rg -n 'SCRIPT ERROR:|Assertion failed|ERROR:' build/logs/atmosphere-native.log; then
  echo 'Atmosphere/UI regression failed' >&2
  exit 1
fi
rg -q 'TELANICO_ATMOSPHERE_PASS' build/logs/atmosphere-native.log
"$godot_bin" --headless --path godot --export-release Web ../build/web/index.html \
  2>&1 | tee build/logs/export.log
mkdir -p build/web/media
cp godot/web/audio_bridge.js build/web/audio_bridge.js
cp godot/web/rabbit_animation_bridge.js build/web/rabbit_animation_bridge.js
cp godot/web/rabbit.gif build/web/media/rabbit.gif
cp godot/assets/audio/music/original_theme.mp3 build/web/media/music.mp3
cp godot/assets/audio/sfx/*.wav build/web/media/
python3 tools/stamp_build.py
python3 tools/validate_web.py build/web
