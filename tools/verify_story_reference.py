"""Verify migration provenance against an explicitly supplied read-only source checkout.

Usage: python tools/verify_story_reference.py /path/to/VorGun-Godot-Clean-Test
The source is inspected, never modified or fetched by this tool.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def function(text, name):
    match = re.search(r"^func " + re.escape(name) + r"\(.*?(?=^func |\Z)", text, re.M | re.S)
    if match is None:
        raise ValueError(f"Missing canonical function: {name}")
    return match.group().rstrip() + "\n\n"


def verify(source):
    provenance = json.loads((ROOT / "docs/v2-2/source-provenance.json").read_text())
    head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if head != provenance["commit"]:
        raise ValueError(f"Source revision mismatch: expected {provenance['commit']}, got {head}")
    canonical = (source / "main.gd").read_text()
    if hashlib.sha256(canonical.encode()).hexdigest() != provenance["source_main_sha256"]:
        raise ValueError("Canonical main.gd has local changes")
    migrated = (ROOT / "godot/scripts/story/story_session.gd").read_text()
    for name, expected in provenance["unchanged_methods"].items():
        for label, text in [("source", canonical), ("session", migrated)]:
            if hashlib.sha256(function(text, name).encode()).hexdigest() != expected:
                raise ValueError(f"Canonical method changed: {label}:{name}")
    for asset in provenance["approved_assets"]:
        path = source / asset["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != asset["sha256"]:
            raise ValueError(f"Approved asset missing or changed: {asset['path']}")
    print(f"STORY_REFERENCE_OK {head}: {len(provenance['unchanged_methods'])} methods; "
          f"{len(provenance['approved_assets'])} approved assets available")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    verify(Path(sys.argv[1]).resolve())
