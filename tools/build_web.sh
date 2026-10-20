#!/usr/bin/env bash
# Linux/cloud build. Godot and matching Web export templates must be installed.
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
blender_bin=${BLENDER_BIN:-blender}
godot_bin=${GODOT_BIN:-godot}
mkdir -p build/logs
python3 tools/fetch_assets.py
# Remove only this reproducible output so stale runtime files cannot mask failures.
rm -rf build/web
mkdir -p build/web
"$blender_bin" --background --factory-startup --python-exit-code 1 \
  --python blender/scripts/build_world_v2.py 2>&1 | tee build/logs/blender.log
python3 tools/validate_v2.py
python3 tools/validate_glb.py godot/assets/generated/overworld.glb
python3 tools/stamp_build.py --before
"$godot_bin" --headless --path godot --editor --import 2>&1 | tee build/logs/import.log
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
"$godot_bin" --headless --path godot --export-release Web ../build/web/index.html \
  2>&1 | tee build/logs/export.log
python3 tools/stamp_build.py
python3 tools/validate_web.py build/web
