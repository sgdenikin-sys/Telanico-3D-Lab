"""Quick, dependency-free structural sanity check for an exported GLB file."""
import json
from pathlib import Path
import struct
import sys


def validate(path: Path):
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("GLB is too small")
    magic, version, declared_length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or declared_length != len(data):
        raise ValueError("Invalid glTF 2.0 GLB header/size")
    chunk_size, chunk_type = struct.unpack_from("<I4s", data, 12)
    if chunk_type != b"JSON" or 20 + chunk_size > len(data):
        raise ValueError("Missing JSON chunk")
    document = json.loads(data[20 : 20 + chunk_size].decode("utf-8"))
    mesh_count = len(document.get("meshes", []))
    if mesh_count < 1 or len(document.get("scenes", [])) < 1:
        raise ValueError("GLB has no meshes or scenes")
    print(f"GLB OK: {path}, meshes={mesh_count}, bytes={len(data)}")


if __name__ == "__main__":
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1]
        / "godot/assets/generated/smoke_test.glb"
    )
    validate(input_path)
