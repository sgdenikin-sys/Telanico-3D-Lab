"""Run the established release gates on Windows with the pinned portable editor."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / 'build' / 'logs'


def run(name, command, marker=None, timeout=240):
    print('RUN', name, flush=True)
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout,
                            encoding='utf-8', errors='replace')
    (LOGS / f'{name}.log').write_text(result.stdout, encoding='utf-8')
    bad = [line for line in result.stdout.splitlines()
           if any(token in line for token in ('SCRIPT ERROR:', 'Assertion failed', 'ERROR:'))]
    if result.returncode or bad or (marker and marker not in result.stdout):
        print(result.stdout[-12000:], flush=True)
        raise RuntimeError(f'{name} failed: exit={result.returncode}, errors={bad[:5]}')
    print('PASS', name, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', required=True)
    parser.add_argument('--skip-generation', action='store_true', help='Validate already generated models')
    args = parser.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    editor = ROOT / 'build/toolchain/Godot_v4.6.3-stable_win64_console.exe'
    if not editor.is_file():
        raise RuntimeError('Run tools/bootstrap_release.py first')
    os.environ['PYTHONUTF8'] = '1'
    python = sys.executable
    if not args.skip_generation:
        run('blender', [args.blender, '--background', '--factory-startup', '--python-exit-code', '1',
                        '--python', 'blender/scripts/build_world_v2.py'], 'V2_WORLD_OK', 600)
    run('layout', [python, 'tools/validate_v2.py'], 'V2_VALIDATION_OK')
    run('glb', [python, 'tools/validate_glb.py', 'godot/assets/generated/overworld.glb'], 'GLB OK')
    run('stamp-before', [python, 'tools/stamp_build.py', '--before'])
    base = [str(editor), '--headless', '--path', 'godot']
    run('import', base + ['--editor', '--import'], timeout=600)
    tests = {
        'test_story_session': 'TELANICO_STORY_SESSION_PASS',
        'test_source_parity': 'TELANICO_SOURCE_PARITY_PASS',
        'test_world_integration': 'TELANICO_WORLD_STORY_PASS',
        'test_playthrough': 'TELANICO_PLAYTHROUGH_PASS',
        'test_optional_offices': 'TELANICO_OPTIONAL_OFFICES_PASS',
        'test_story_ui': 'TELANICO_STORY_UI_PASS',
    }
    for test, marker in tests.items():
        run(test, base + ['--script', f'res://tests/story/{test}.gd'], marker)
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js is required for the existing audio lifecycle regression')
    run('audio', [node, 'tools/audio_lifecycle_regression.js'])
    run('viewer', base + ['--script', 'res://tests/test_v2.gd'], 'TELANICO_TEST_OK')
    web = ROOT / 'build/web'
    # Never merge a new export with an old runtime snapshot.
    if web.exists():
        raise RuntimeError('build/web already exists; preserve it separately before rebuilding')
    web.mkdir()
    run('export', base + ['--export-release', 'Web', '../build/web/index.html'], timeout=600)
    shutil.copy2(ROOT / 'godot/web/audio_bridge.js', web / 'audio_bridge.js')
    media = web / 'media'
    media.mkdir()
    shutil.copy2(ROOT / 'godot/assets/audio/music/original_theme.mp3', media / 'music.mp3')
    for sample in (ROOT / 'godot/assets/audio/sfx').glob('*.wav'):
        shutil.copy2(sample, media / sample.name)
    run('stamp-after', [python, 'tools/stamp_build.py'])
    run('web-validation', [python, 'tools/validate_web.py', str(web)], 'WEB_OK')
    print('WINDOWS_RELEASE_BUILD_PASS', flush=True)


if __name__ == '__main__':
    main()
