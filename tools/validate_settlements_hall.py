"""Validate the shipped GLB geometry/material contract without Blender or packages."""
import argparse
import json
import math
from pathlib import Path
import struct

from validate_glb import validate

ROOT = Path(__file__).resolve().parents[1]


def inspect(path):
    validate(path)
    raw = path.read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+length])
    start = 20+length
    binary_length, binary_type = struct.unpack_from('<I4s', raw, start)
    assert binary_type == b'BIN\x00'
    binary = raw[start+8:start+8+binary_length]
    def accessor(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        fmt = {5121: 'B', 5123: 'H', 5125: 'I', 5126: 'f'}[a['componentType']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        size = struct.calcsize('<'+fmt)*width
        stride = view.get('byteStride', size)
        offset = view.get('byteOffset', 0)+a.get('byteOffset', 0)
        return [struct.unpack_from('<'+fmt*width, binary, offset+i*stride)
                for i in range(a['count'])]
    tris, vertices, degenerate = 0, 0, 0
    minimum, maximum = [math.inf]*3, [-math.inf]*3
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            assert primitive.get('mode', 4) == 4, 'Only indexed triangle meshes expected'
            assert 'NORMAL' in primitive['attributes'] and 'TEXCOORD_0' in primitive['attributes']
            assert 'material' in primitive
            positions = accessor(primitive['attributes']['POSITION'])
            normals = accessor(primitive['attributes']['NORMAL'])
            indices = [v[0] for v in accessor(primitive['indices'])]
            assert len(indices)%3 == 0
            tris += len(indices)//3
            vertices += len(positions)
            for p in positions:
                assert all(math.isfinite(c) for c in p)
                for j in range(3):
                    minimum[j], maximum[j] = min(minimum[j], p[j]), max(maximum[j], p[j])
            for normal in normals:
                assert .98 < sum(n*n for n in normal) < 1.02, 'Invalid vertex normal'
            for i in range(0, len(indices), 3):
                a, b, c = [positions[indices[i+j]] for j in range(3)]
                u, v = [b[j]-a[j] for j in range(3)], [c[j]-a[j] for j in range(3)]
                cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
                if sum(n*n for n in cross) < 1e-16:
                    degenerate += 1
    assert 12000 <= tris <= 35000, f'Triangle budget exceeded: {tris}'
    assert degenerate == 0, f'{degenerate} zero-area triangles'
    assert len(doc['meshes']) <= 20, 'Runtime material batching missing'
    assert not doc.get('cameras') and not doc.get('skins')
    assert not doc.get('extensionsRequired'), 'Core glTF materials required'
    mats = {m['name']: m for m in doc['materials']}
    assert len(mats) == 11
    for m in mats.values():
        pbr = m['pbrMetallicRoughness']
        assert len(pbr.get('baseColorFactor', [])) == 4
    glass = mats['Semi transparent blue tinted glass']
    assert glass.get('alphaMode') == 'BLEND'
    assert 0 < glass['pbrMetallicRoughness']['baseColorFactor'][3] < 1
    assert glass.get('doubleSided')
    assert mats['Restrained aged brass']['pbrMetallicRoughness']['metallicFactor'] > .7
    assert mats['Warm ivory limestone']['pbrMetallicRoughness'].get('metallicFactor', 1) == 0
    assert mats['Woven blue banner fabric'].get('doubleSided')
    assert not doc.get('images'), 'Unexpected external image dependence'
    dims = [round(maximum[j]-minimum[j], 3) for j in range(3)]
    assert 15 < dims[1] < 18 and 22 < dims[0] < 26
    # Only hinged components have local transforms; architecture remains at metre scale.
    for node in doc['nodes']:
        assert 'scale' not in node or node['scale'] == [1, 1, 1]
    nodes = doc['nodes']
    by_name = {n['name']: i for i, n in enumerate(nodes)}
    hinge_ids = {by_name['Door_Hinge_L'], by_name['Door_Hinge_R']}
    for side in ('L', 'R'):
        hinge = nodes[by_name['Door_Hinge_'+side]]
        expected = [-.96 if side == 'L' else .96, 1.51, 5.17]
        assert max(abs(a-b) for a, b in zip(hinge['translation'], expected)) < .001
        assert len(hinge.get('children', [])) == 2, 'Each hinged leaf must retain blue and brass batches'
    flag_ids = {by_name[name] for name in ['Flag_Roof_L', 'Flag_Roof_R', 'Flag_Entry_L', 'Flag_Entry_R']}
    for i in flag_ids:
        flag_mesh = doc['meshes'][nodes[i]['mesh']]
        for primitive in flag_mesh['primitives']:
            assert len(primitive.get('targets', [])) == 3, 'Fabric must retain three morph targets'
    clips = {a['name']: a for a in doc['animations']}
    assert set(clips) == {'Doors_Open', 'Doors_Close', 'Flags_Wind-loop', 'Hall_Demo-loop'}
    clip_report = {}
    for name, clip in clips.items():
        targets = {c['target']['node'] for c in clip['channels']}
        expected = hinge_ids if name.startswith('Doors_') else flag_ids if name.startswith('Flags_') else hinge_ids | flag_ids
        assert targets == expected, (name, targets, expected)
        duration = 0
        for channel in clip['channels']:
            sampler = clip['samplers'][channel['sampler']]
            times = accessor(sampler['input'])
            values = accessor(sampler['output'])
            duration = max(duration, times[-1][0])
            assert abs(times[0][0]) < .001
            if channel['target']['path'] == 'weights':
                values = [v[0] for v in values]
                assert max(values)-min(values) > .9, 'Static cloth weights'
                assert max(abs(a-b) for a, b in zip(values[:3], values[-3:])) < .0001, 'Wind seam must close'
            else:
                assert channel['target']['path'] == 'rotation'
                if name.startswith('Doors_'):
                    dot = abs(sum(a*b for a, b in zip(values[0], values[-1])))
                    assert .60 < dot < .68, 'Door must rotate about 100 degrees'
        assert abs(duration-(1 if name.startswith('Doors_') else 4)) < .001
        clip_report[name] = {'seconds': round(duration, 3), 'channels': len(clip['channels'])}
    result = {'triangles': tris, 'export_vertices': vertices, 'meshes': len(doc['meshes']),
              'materials': len(mats), 'degenerate_triangles': degenerate,
              'dimensions_xyz_metres_gltf': dims, 'bytes': len(raw),
              'core_gltf_materials': True, 'glass_alpha_blend': True,
              'animations': clip_report, 'hinged_leaves': 2, 'morph_animated_fabric_pieces': 4}
    print('SETTLEMENTS_GLB_OK '+json.dumps(result))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', type=Path,
                        default=ROOT/'godot/assets/generated/settlements_hall.glb')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    result = inspect(args.path)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2)+'\n')
