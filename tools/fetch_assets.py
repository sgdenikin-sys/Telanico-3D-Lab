"""Fetch only reviewed CC0 source models; verify pinned per-file SHA-256 hashes."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]

def fetch():
    entries=json.loads((ROOT/'tools/assets.lock.json').read_text())
    for entry in entries:
        path=ROOT/entry['path']
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']:
            continue
        data=urllib.request.urlopen(entry['url'],timeout=90).read()
        if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:
            raise ValueError('Asset checksum mismatch: '+entry['path'])
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print('ASSETS_OK:',len(entries),'pinned, licensed files verified')

if __name__=='__main__':fetch()
