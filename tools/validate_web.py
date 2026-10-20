"""Validate an intact, single-threaded Godot Web artifact without dependencies."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and ((tag in ('script', 'img') and key == 'src') or
                          (tag == 'link' and key == 'href')):
                self.paths.add(value)


def validate(directory: Path):
    html = (directory / 'index.html').read_text(encoding='utf-8')
    match = re.search(r'const GODOT_CONFIG = (\{.*?\});', html)
    if not match or not re.search(r'const GODOT_THREADS_ENABLED = false;', html):
        raise ValueError('Missing Godot config or export is not single-threaded')
    config = json.loads(match[1])
    if config['executable'] != 'index' or config.get('gdextensionLibs'):
        raise ValueError('Unexpected executable or native extension dependencies')
    if config.get('serviceWorker'):
        raise ValueError('This static artifact must not require a service worker')
    parser = References()
    parser.feed(html)
    required = parser.paths | {
        'index.html', 'index.js', 'index.wasm', 'index.pck',
        'index.audio.worklet.js', 'index.audio.position.worklet.js',
    } | set(config['fileSizes'])
    for name in required:
        url = urlsplit(name)
        path = directory / unquote(url.path)
        if url.scheme or url.netloc or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f'Non-local runtime reference: {name}')
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Missing or empty runtime file: {name}')
    if "audio_bridge.js" in html:
        import hashlib
        music = directory / 'media/music.mp3'
        if not music.is_file() or hashlib.sha256(music.read_bytes()).hexdigest() != 'dc0869cab4b4843c02f3428ab429e826794e4866bed9d1fbcfafffb6a080cef5':
            raise ValueError('Original authored music missing/changed')
        for sample in ['cooper_chponk.wav', 'door_open_office.wav', 'tube_water_flush.wav', 'bird_takeoff_soft_purr.wav', 'door_close_soft.wav', 'select_woosh.wav', 'menu_flip.wav']:
            if not (directory/'media'/sample).is_file():
                raise ValueError('Missing canonical browser audio: '+sample)
    for name, size in config['fileSizes'].items():
        if (directory / name).stat().st_size != size:
            raise ValueError(f'Runtime size mismatch: {name}')
    if (directory / 'index.wasm').read_bytes()[:8] != b'\x00asm\x01\x00\x00\x00':
        raise ValueError('Invalid WebAssembly header')
    if (directory / 'index.pck').read_bytes()[:4] != b'GDPC':
        raise ValueError('Invalid Godot resource pack')
    print(f'WEB_OK: {len(required)} local files; single-threaded; WASM and PCK valid')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    validate(parser.parse_args().directory)
