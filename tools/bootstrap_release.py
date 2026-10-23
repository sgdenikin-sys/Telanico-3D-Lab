"""Fetch the pinned official Windows editor and only its Web release template.

Keeps downloads in ignored build/toolchain; no global installation is required.
The template archive is read with HTTP ranges to avoid downloading other targets.
"""
from pathlib import Path
import io
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build' / 'toolchain'
VERSION = '4.6.3'
BASE = f'https://github.com/godotengine/godot-builds/releases/download/{VERSION}-stable/'


class RemoteZip(io.RawIOBase):
    def __init__(self, url):
        with urllib.request.urlopen(urllib.request.Request(url, headers={'Range': 'bytes=0-0'}), timeout=90) as response:
            if response.status != 206:
                raise RuntimeError('Official archive server did not support HTTP ranges')
            self.url = response.url
            self.size = int(response.headers['Content-Range'].split('/')[-1])
        self.position = 0

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else (self.position if whence == 1 else self.size) + offset
        return self.position

    def tell(self):
        return self.position

    def read(self, size=-1):
        size = min(self.size - self.position, size if size >= 0 else self.size)
        if size <= 0:
            return b''
        start = self.position
        request = urllib.request.Request(self.url, headers={'Range': f'bytes={start}-{start + size - 1}'})
        with urllib.request.urlopen(request, timeout=180) as response:
            if response.status != 206:
                raise RuntimeError('Archive range request was not honored')
            data = response.read()
        if len(data) != size:
            raise RuntimeError('Truncated archive response')
        self.position += len(data)
        return data


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    editor = OUT / f'Godot_v{VERSION}-stable_win64_console.exe'
    if not editor.exists():
        archive = OUT / 'editor.zip'
        print('Downloading official Godot editor', flush=True)
        urllib.request.urlretrieve(BASE + f'Godot_v{VERSION}-stable_win64.exe.zip', archive)
        with zipfile.ZipFile(archive) as source:
            for name in source.namelist():
                if name.endswith('.exe') and '/' not in name:
                    pending = OUT / (name + '.tmp')
                    with source.open(name) as entry, pending.open('wb') as target:
                        shutil.copyfileobj(entry, target)
                    pending.replace(OUT / name)
    template = OUT / 'web_nothreads_release.zip'
    if not template.exists():
        print('Fetching official single-thread Web template', flush=True)
        with zipfile.ZipFile(RemoteZip(BASE + f'Godot_v{VERSION}-stable_export_templates.tpz')) as source:
            pending = template.with_suffix('.tmp')
            with source.open('templates/web_nothreads_release.zip') as entry, pending.open('wb') as target:
                shutil.copyfileobj(entry, target)
        with zipfile.ZipFile(pending) as source:
            if source.testzip():
                raise RuntimeError('Corrupt Web template')
        pending.replace(template)
    print('TOOLCHAIN_OK', editor, template, flush=True)


if __name__ == '__main__':
    main()
