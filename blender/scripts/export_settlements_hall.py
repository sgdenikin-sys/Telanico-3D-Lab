"""Export hand edits without rebuilding the procedural source.

blender -b path/to/edited.blend --python-exit-code 1 --python
blender/scripts/export_settlements_hall.py -- --output path/to/edited.glb

Only numbered architectural collections 01–07 are exported. Studio, cameras,
lights and unrelated objects are excluded. Deleted parts stay deleted.
"""
import argparse
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_settlements_hall as hall

parser = argparse.ArgumentParser(description=__doc__)
is_lite = '--quality lite' in bpy.context.scene.get('regenerate', '')
parser.add_argument('--output', type=Path,
                    default=hall.ROOT/('blender/generated/settlements_hall_lite/settlements_hall.glb'
                                       if is_lite else 'godot/assets/generated/settlements_hall.glb'))
args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
hall.ASSET[:] = sorted({obj for col in bpy.context.scene.collection.children
                     if col.name[:2] in {'01', '02', '03', '04', '05', '06', '07'}
                     for obj in col.all_objects if obj.type == 'MESH'}, key=lambda obj: obj.name)
if not hall.ASSET:
    raise RuntimeError('Open the editable Settlements Hall blend before exporting')
for obj in hall.ASSET:
    if not obj.data.shape_keys and len(obj.data.materials) != 1:
        raise RuntimeError('Keep one material per authoring part: '+obj.name)
    if not obj.data.uv_layers:
        raise RuntimeError('Add UV0 to the edited part: '+obj.name)
hall.M.update({mat.name: mat for obj in hall.ASSET for mat in obj.data.materials})
bpy.context.view_layer.update()
args.output.parent.mkdir(parents=True, exist_ok=True)
stats = hall.export_runtime(args.output.resolve())
if stats['source_triangles'] > 35000:
    print('NOTE: hand edits exceed the 35,000-triangle target')
print('SETTLEMENTS_EDIT_EXPORT_OK', args.output, stats)
