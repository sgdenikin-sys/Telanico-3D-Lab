"""Verify the exact tested site/ snapshot before publishing from this repository."""
import hashlib
import json
from pathlib import Path

from validate_web import validate

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = {
    'index.html', 'index.js', 'index.wasm', 'index.pck',
    'index.audio.worklet.js', 'index.audio.position.worklet.js',
    'index.icon.png', 'index.apple-touch-icon.png', 'index.png',
    'build.json', 'LICENSES.html', 'audio_bridge.js', 'media/music.mp3',
}
RUNTIME.update('media/' + name + '.wav' for name in (
    'bird_takeoff_soft_purr', 'cooper_chponk', 'door_close_soft',
    'door_open_office', 'door_open_playful', 'menu_flip', 'select_woosh',
    'swallow_takeoff', 'tube_water_flush',
))


def verify(root=ROOT):
    site = root / 'site'
    manifest = json.loads((root / 'tools/release.json').read_text())
    meta = json.loads((site / 'build.json').read_text())
    actual = {p.relative_to(site).as_posix() for p in site.rglob('*') if p.is_file()}
    assert actual == RUNTIME | {'.nojekyll'}, ('Unexpected/missing files', actual ^ (RUNTIME | {'.nojekyll'}))
    assert set(manifest['files']) == RUNTIME, 'Unexpected release manifest entries'
    assert meta['version'] == manifest['version'] == 'telanico-v2.2', meta
    assert meta['commit'] == manifest['source_commit'], meta
    assert meta['camera_projection'] == 'orthographic' and meta['camera_elevation_above_horizontal'] == 40
    for name, expected in manifest['files'].items():
        path = site / name
        assert not path.is_symlink(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    for key in ('native_release_gates', 'desktop_browser', 'phone_full_story'):
        assert manifest['validation'][key] == 'passed', key
    assert meta['commit'] in (site / 'index.html').read_text(encoding='utf-8')
    validate(site)
    print('RELEASE_SNAPSHOT_VERIFIED', meta['version'], meta['commit'], len(RUNTIME), 'files')


if __name__ == '__main__':
    verify()
