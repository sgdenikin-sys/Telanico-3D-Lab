"""Stage only a fully checked local Web snapshot in the main repository site/ directory."""
import hashlib
import json
from pathlib import Path
import shutil
import platform
import time

from validate_web import validate

ROOT = Path(__file__).resolve().parents[1]


def main():
    web = ROOT / 'build/web'
    public = ROOT
    validate(web)
    meta = json.loads((web / 'build.json').read_text())
    assert meta['version'] == 'telanico-v2.2' and meta['source_run_id'] == 'local', meta
    log = (ROOT / 'build/story-browser-release.log').read_text(encoding='utf-8')
    assert 'STORY_BROWSER_PASS 1280 opening-office-wrong-answer' in log
    assert 'STORY_BROWSER_PASS 844 full' in log
    for width in (1280, 844):
        result = json.loads((ROOT / f'build/screenshots/story/story-result-{width}.json').read_text())
        assert not result['errors'] and result['audio']['musicStarts'] == 1, result
    allowed = {
        'index.html', 'index.js', 'index.wasm', 'index.pck', 'index.audio.worklet.js',
        'index.audio.position.worklet.js', 'index.icon.png', 'index.apple-touch-icon.png',
        'index.png', 'build.json', 'LICENSES.html', 'audio_bridge.js', 'media/music.mp3',
    }
    allowed.update('media/' + p.name for p in (ROOT / 'godot/assets/audio/sfx').glob('*.wav'))
    actual = {p.relative_to(web).as_posix() for p in web.rglob('*') if p.is_file()}
    assert actual <= allowed, ('Unexpected public files', actual - allowed)
    assert allowed <= actual, ('Missing runtime files', allowed - actual)
    rollback = ROOT / 'build/site-history' / str(time.time_ns())
    if (public / 'site').exists():
        shutil.copytree(public / 'site', rollback)
    for name in sorted(actual):
        target = public / 'site' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(web / name, target)
    (public / 'site/.nojekyll').touch()
    manifest = {
        'version': meta['version'], 'source_commit': meta['commit'],
        'build_environment': platform.platform(),
        'validation': {'native_release_gates': 'passed', 'desktop_browser': 'passed',
                       'phone_full_story': 'passed', 'physical_iphone_safari': 'not tested'},
        'disabled_features': [],
        'files': {name: hashlib.sha256((web / name).read_bytes()).hexdigest() for name in sorted(actual)},
    }
    (public / 'tools/release.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('V22_PUBLIC_SNAPSHOT_STAGED', meta['commit'], len(actual), 'runtime files')


if __name__ == '__main__':
    main()
