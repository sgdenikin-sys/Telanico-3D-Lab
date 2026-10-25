"""Stage the reviewed Settlements Hall V3 Lite GLB into the Godot project.

Keeps private authoring renders and Blender sources out of published game assets.
The game uses the unchanged generated path expected by the existing Hall scene.
"""
from hashlib import sha256
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/settlements_hall/v3-lite/settlements_hall.glb"
TARGET = ROOT / "godot/assets/generated/settlements_hall.glb"
EXPECTED = "c4bf665a9639db60a2d3371b2bbbeae496a1295b8886990a2419cff246f0297b"


def main():
    raw = SOURCE.read_bytes()
    digest = sha256(raw).hexdigest()
    assert digest == EXPECTED, "Unexpected Hall V3 Lite asset: " + digest
    magic, version, length = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"glTF" and version == 2 and length == len(raw)
    json_size = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20+json_size])
    assert len(doc.get("materials", [])) == 11
    assert len(doc.get("animations", [])) == 4
    triangles = sum(doc["accessors"][piece["indices"]]["count"] // 3
                    for mesh in doc["meshes"]
                    for piece in mesh["primitives"])
    assert triangles == 19816, f"Not the approved V3 Lite geometry: {triangles}"
    assert any(m.get("alphaMode") == "BLEND" for m in doc["materials"]), "Glass was made opaque"
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(raw)
    assert sha256(TARGET.read_bytes()).hexdigest() == EXPECTED
    print(f"SETTLEMENTS_HALL_V3_STAGED {triangles} triangles {len(raw)} bytes SHA256={digest}")


if __name__ == "__main__":
    main()
