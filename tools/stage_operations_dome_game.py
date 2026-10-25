"""Stage exact owner-reviewed Operations V3 GLB for Godot without rebuilding."""
from pathlib import Path
from hashlib import sha256
import gzip
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/operations/v3/operations_textured_v3.glb.gz"
TARGET = ROOT / "godot/assets/generated/operations_textured_v3.glb"
ARCHIVE_SHA = "9d471cb3da4510f6eba16c80bab37364ceb82f5f9f5aa52cf471686ac802f220"
GLB_SHA = "25518b2662254dfc2dc0d021f41e58cbbb9c7338ccccb632a7a129bd8c266c9f"

def main():
    compressed = SOURCE.read_bytes()
    assert sha256(compressed).hexdigest() == ARCHIVE_SHA, "Archive SHA mismatch"
    raw = gzip.decompress(compressed)
    assert sha256(raw).hexdigest() == GLB_SHA, "Operations GLB SHA mismatch"
    magic, version, length = struct.unpack_from("<4sII", raw)
    assert (magic, version, length) == (b"glTF", 2, len(raw)), "Invalid GLB"
    count = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20+count])
    assert len(doc.get("materials", [])) == 12, "Changed material count"
    assert len(doc.get("images", [])) == 9, "Missing embedded textures"
    assert {a["name"] for a in doc["animations"]} == {"Doors_Open", "Doors_Close"}
    tris = sum(doc["accessors"][p["indices"]]["count"] // 3
               for m in doc["meshes"] for p in m["primitives"])
    assert tris == 16086, f"Unexpected triangles: {tris}"
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(raw)
    print(f"OPERATIONS_V3_STAGED {tris} triangles, {len(raw)} bytes")

if __name__ == "__main__":
    main()
