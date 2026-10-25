"""Publish only the separate V3 Lite artifact folder after its asset QA passes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'blender/generated/settlements_hall_lite'
TARGET = ROOT/'artifacts/settlements_hall/v3-lite'
FRAMES = ROOT/'work/hall-v3-animation-frames'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    stats = json.loads((OUT/'asset_stats.json').read_text())
    geometry = json.loads((OUT/'glb_validation.json').read_text())
    native = json.loads((OUT/'godot_animation_validation.json').read_text())
    visual = json.loads((OUT/'godot_visual_validation.json').read_text())
    assert stats['quality_preset'] == 'lite'
    assert 15000 <= geometry['triangles'] == stats['source_triangles'] <= 20000
    assert geometry['materials'] == 11 and visual['glass_render_verified']
    assert native['morph_fabric_objects'] == 4 and native['independent_playback_verified']
    assert native['engine'].startswith('4.6.3') and native['cloth_loop_seam_verified']
    demo = json.loads((FRAMES/'round_trip_animation_report.json').read_text())
    assert demo['glb_sha256'] == sha(OUT/'settlements_hall.glb') == visual['glb_sha256']
    for panel in ['doors', 'flag']:
        assert len(list((FRAMES/panel).glob('*.png'))) == 4*demo['fps']
    mp4, gif = OUT/'animation_demo.mp4', OUT/'animation_demo.gif'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-filter_complex_threads', '1',
                    '-framerate', str(demo['fps']), '-i', str(FRAMES/'doors/%04d.png'),
                    '-framerate', str(demo['fps']), '-i', str(FRAMES/'flag/%04d.png'),
                    '-filter_complex', 'hstack=inputs=2', '-c:v', 'libx264', '-threads', '2',
                    '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(mp4)], check=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-filter_complex_threads', '1', '-i', str(mp4),
                    '-filter_complex', '[0:v]split[x][y];[x]palettegen=max_colors=96[p];[y][p]paletteuse=dither=bayer:bayer_scale=3',
                    '-loop', '0', str(gif)], check=True)
    shutil.copyfile(FRAMES/'round_trip_animation_report.json', OUT/'round_trip_animation_report.json')
    evidence = OUT/'evidence'
    evidence.mkdir(exist_ok=True)
    for name in ['final-build', 'godot-import', 'godot-check', 'browser-qa', 'visual-pack', 'edit-export', 'camera-comparison']:
        shutil.copyfile(ROOT/f'work/hall-v3-{name}.log', evidence/(name+'.log'))
    names = ['settlements_hall.blend', 'settlements_hall.glb', 'animation_demo.mp4', 'animation_demo.gif',
             'hero.png', 'front.png', 'rear.png', 'detail.png',
             'godot_lite_844x390.png', 'godot_v2_844x390.png', 'godot_lite_animation_pose.png',
             'godot_glass_hidden.png', 'godot_glass_transparent.png', 'godot_glass_opaque.png',
             'asset_stats.json', 'glb_validation.json', 'godot_animation_validation.json',
             'godot_visual_validation.json', 'hand_edit_export_validation.json',
             'round_trip_animation_report.json', 'lod_comparison.json',
             'render_comparison.json', 'camera_lighting_comparison.json']
    source = ['blender/scripts/build_settlements_hall.py', 'blender/scripts/build_smoke_test.py',
              'blender/scripts/export_settlements_hall.py', 'blender/scripts/render_settlements_hall_demo.py',
              'godot/scripts/settlements_hall_asset.gd', 'godot/scripts/settlements_hall_preview.gd',
              'godot/scenes/assets/settlements_hall.tscn', 'godot/scenes/assets/settlements_hall_preview.tscn',
              'tools/check_settlements_hall.gd', 'tools/validate_glb.py', 'tools/validate_settlements_hall.py',
              'tools/compare_settlements_hall_lod.py', 'tools/compare_hall_lite_renders.py',
              'tools/hall_lite_visual_qa.gd', 'tools/check_hall_lite_visual.py',
              'tools/package_settlements_hall_lite.py', 'docs/assets/SETTLEMENTS_HALL_LITE.md']
    archive_files = [(OUT/name, 'blender/generated/settlements_hall_lite/'+name) for name in names if not name.endswith('.glb')]
    archive_files += [(OUT/'settlements_hall.glb', 'godot/assets/generated/settlements_hall.glb')]
    archive_files += [(ROOT/name, name) for name in source]
    archive_files += [(p, 'evidence/'+p.name) for p in sorted(evidence.glob('*.log'))]
    manifest = {'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                'quality': 'lite', 'glb_sha256': sha(OUT/'settlements_hall.glb'),
                'files': [{'path': name, 'bytes': path.stat().st_size, 'sha256': sha(path)} for path, name in archive_files]}
    (OUT/'deliverable_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    pack = OUT/'settlements_hall_v3_lite.zip'
    with zipfile.ZipFile(pack, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path, name in archive_files:
            z.write(path, 'SettlementsHallLite/'+name)
        z.write(OUT/'deliverable_manifest.json', 'SettlementsHallLite/deliverable_manifest.json')
        z.writestr('SettlementsHallLite/README.md',
            '# Settlements Hall V3 Lite\n\n19,816 triangles, unchanged 11 PBR materials, four animation clips.\n'
            'Blender: blender/generated/settlements_hall_lite/settlements_hall.blend\n'
            'Godot model: godot/assets/generated/settlements_hall.glb\n'
            'Open godot/project.godot with Godot 4.6.3. O opens, C closes, D plays demo.\n'
            'Regenerate with --quality lite. See docs/assets/SETTLEMENTS_HALL_LITE.md.\n'
            'This is an isolated viewer project. Original V2 and the game are untouched.\n')
        z.writestr('SettlementsHallLite/godot/project.godot',
            'config_version=5\n[application]\nconfig/name="Settlements Hall V3 Lite"\n'
            'run/main_scene="res://scenes/assets/settlements_hall_preview.tscn"\n'
            'config/features=PackedStringArray("4.6", "GL Compatibility")\n'
            '[display]\nwindow/size/viewport_width=1280\nwindow/size/viewport_height=900\n'
            '[rendering]\nrenderer/rendering_method="gl_compatibility"\nrenderer/rendering_method.mobile="gl_compatibility"\n')
    with zipfile.ZipFile(pack) as z:
        assert z.testzip() is None
        assert len([p for p in z.namelist() if p.endswith('.glb')]) == 1
    TARGET.mkdir(parents=True, exist_ok=True)
    publish = [pack, OUT/'deliverable_manifest.json', *[OUT/name for name in names],
               *[OUT/('comparison_'+view+'.png') for view in ['hero', 'front', 'rear', 'detail']]]
    for path in publish:
        shutil.copyfile(path, TARGET/path.name)
    (TARGET/'SHA256SUMS.txt').write_text(''.join(sha(path)+'  '+path.name+'\n' for path in publish))
    print('V3_LITE_PACKAGE_READY', str(pack), pack.stat().st_size)


if __name__ == '__main__':
    main()
