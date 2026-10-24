"""Render a four-second, two-camera animation proof from the EXPORTED GLB.

blender -b --python-exit-code 1 --python blender/scripts/render_settlements_hall_demo.py

Frame sequences are intermediate files under work/hall_animation_frames. Output
MP4/GIF are assembled with the existing ffmpeg binary by the package workflow.
CPU Cycles, no display/GPU, add-ons or simulation caches required.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_settlements_hall import ROOT, configure_studio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--glb', type=Path, default=ROOT/'godot/assets/generated/settlements_hall.glb')
    parser.add_argument('--frames', type=Path, default=ROOT/'work/hall_animation_frames')
    parser.add_argument('--size', type=int, default=384)
    parser.add_argument('--samples', type=int, default=8)
    parser.add_argument('--fps', type=int, default=10)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
    owners = []
    for obj in list(scene.objects):
        owners.append(obj)
        if obj.type == 'MESH' and obj.data.shape_keys:
            owners.append(obj.data.shape_keys)
    active = 0
    for owner in owners:
        if not owner.animation_data:
            continue
        owner.animation_data.action = None
        for track in owner.animation_data.nla_tracks:
            track.mute = track.name != 'Hall_Demo-loop'
            if not track.mute:
                active += 1
    assert active == 6, f'Expected two hinges plus four fabrics after GLB reimport; got {active}'
    samples = []
    for frame in (1, 16, 31, 91, 121):
        scene.frame_set(frame)
        samples.append({'frame': frame,
                        'hinges': {o.name: list(o.rotation_quaternion) for o in scene.objects if o.name.startswith('Door_Hinge_')},
                        'fabric': {o.name: [k.value for k in o.data.shape_keys.key_blocks][1:]
                                   for o in scene.objects if o.type == 'MESH' and o.data.shape_keys}})
    args.frames.mkdir(parents=True, exist_ok=True)
    report = {'glb_sha256': hashlib.sha256(args.glb.read_bytes()).hexdigest(),
              'renderer': 'Blender CPU Cycles after GLB reimport', 'seconds': 4,
              'fps': args.fps, 'animated_owners': active, 'pose_samples': samples}
    (args.frames/'round_trip_animation_report.json').write_text(json.dumps(report, indent=2)+'\n')
    scene.frame_set(1)
    configure_studio()
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = False
    scene.render.use_persistent_data = True
    scene.render.resolution_x = scene.render.resolution_y = args.size
    scene.render.resolution_percentage = 100
    for name, pos, target, scale in [
            ('doors', (4, -20, 8), (0, -5.4, 3.1), 7.4),
            ('flag', (-11, -9, 14), (-9.5, 1.4, 10.9), 4.1)]:
        folder = args.frames/name
        folder.mkdir(exist_ok=True)
        bpy.ops.object.camera_add(location=pos)
        camera = bpy.context.object
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.type, camera.data.ortho_scale = 'ORTHO', scale
        scene.camera = camera
        for i in range(4*args.fps):
            scene.frame_set(1+round(i*30/args.fps))
            scene.render.filepath = str(folder/f'{i:04}.png')
            bpy.ops.render.render(write_still=True)
            print(f'GLB_DEMO_FRAME {name} {i+1}/{4*args.fps}', flush=True)
    print('GLB_ANIMATION_DEMO_OK '+str(args.frames), flush=True)


if __name__ == '__main__':
    main()
