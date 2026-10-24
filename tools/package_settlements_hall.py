"""Package the standalone asset and optionally copy it to its GitHub directory.

Requires the existing Blender outputs, demo frame sequences and ffmpeg. This
script does not change the game project, upload files or trigger deployment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'blender/generated/settlements_hall'
GLB = ROOT/'godot/assets/generated/settlements_hall.glb'
FRAMES = ROOT/'work/hall_animation_frames'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args):
    subprocess.run(args, check=True, cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish-dir', type=Path)
    parser.add_argument('--demo-only', action='store_true')
    args = parser.parse_args()
    demo_report = json.loads((FRAMES/'round_trip_animation_report.json').read_text())
    assert demo_report['glb_sha256'] == sha(GLB), 'Render the demonstration from the final GLB'
    fps = demo_report['fps']
    for panel in ('doors', 'flag'):
        assert len(list((FRAMES/panel).glob('*.png'))) == fps*4, 'Incomplete demonstration frames'
    mp4, gif = OUT/'animation_demo.mp4', OUT/'animation_demo.gif'
    run('ffmpeg', '-y', '-loglevel', 'error', '-filter_complex_threads', '1', '-framerate', str(fps),
        '-i', str(FRAMES/'doors/%04d.png'), '-framerate', str(fps),
        '-i', str(FRAMES/'flag/%04d.png'), '-filter_complex', 'hstack=inputs=2',
        '-c:v', 'libx264', '-threads', '2', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart', str(mp4))
    run('ffmpeg', '-y', '-loglevel', 'error', '-filter_complex_threads', '1', '-i', str(mp4), '-filter_complex',
        '[0:v]split[x][y];[x]palettegen=max_colors=96[p];[y][p]paletteuse=dither=bayer:bayer_scale=3',
        '-loop', '0', str(gif))
    shutil.copyfile(FRAMES/'round_trip_animation_report.json', OUT/'round_trip_animation_report.json')
    if args.demo_only:
        print('SETTLEMENTS_DEMO_ASSEMBLED', mp4, gif)
        return
    evidence = OUT/'evidence'
    evidence.mkdir(exist_ok=True)
    for src, dest in [('hall-v2-final-build.log', 'blender-build.log'),
                      ('hall-v2-godot-check.log', 'godot-check.log'),
                      ('hall-v2-godot-preview.log', 'godot-preview.log'),
                      ('hall-v2-godot-import.log', 'godot-import.log')]:
        shutil.copyfile(ROOT/'work'/src, evidence/dest)
    source = [
        'blender/scripts/build_settlements_hall.py',
        'blender/scripts/export_settlements_hall.py',
        'blender/scripts/render_settlements_hall_demo.py',
        'blender/scripts/build_smoke_test.py',
        'docs/assets/SETTLEMENTS_HALL.md',
        'godot/scenes/assets/settlements_hall.tscn',
        'godot/scenes/assets/settlements_hall_preview.tscn',
        'godot/scripts/settlements_hall_asset.gd',
        'godot/scripts/settlements_hall_preview.gd',
        'tools/check_settlements_hall.gd',
        'tools/validate_settlements_hall.py', 'tools/validate_glb.py',
        'tools/package_settlements_hall.py']
    generated = [OUT/'settlements_hall.blend', GLB,
                 *[OUT/(name+'.png') for name in ('hero', 'front', 'rear', 'detail')],
                 mp4, gif, OUT/'asset_stats.json', OUT/'glb_validation.json',
                 OUT/'godot_animation_validation.json', OUT/'round_trip_animation_report.json',
                 OUT/'hand_edit_export_validation.json',
                 *sorted(evidence.glob('*.log'))]
    for path in generated:
        assert path.is_file() and path.stat().st_size > 0, str(path)
    assert generated[0].read_bytes().startswith(b'BLENDER')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    manifest = {'source_commit': commit, 'glb_sha256': sha(GLB),
                'files': [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)}
                          for p in generated + [ROOT/p for p in source]]}
    manifest_path = OUT/'deliverable_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    pack = OUT/'settlements_hall_asset_pack.zip'
    with zipfile.ZipFile(pack, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for p in generated+[ROOT/p for p in source]+[manifest_path]:
            archive.write(p, Path('SettlementsHall')/p.relative_to(ROOT))
        archive.writestr('SettlementsHall/README.md',
            '# Settlements Hall — animated asset\n\n'
            'Open blender/generated/settlements_hall/settlements_hall.blend in Blender.\n'
            'The engine asset is godot/assets/generated/settlements_hall.glb.\n'
            'Open godot/project.godot in Godot 4.6.3 for the independent viewer.\n'
            'O opens, C closes, D plays the combined demonstration.\n\n'
            '34,643 triangles, 11 PBR materials. Two independent hinges and four\n'
            'morph-animated fabric pieces. 1 unit = 1 metre. Godot facing +Z.\n\n'
            'See docs/assets/SETTLEMENTS_HALL.md for animation, editing and verification.\n'
            'The ZIP viewer is a separate project; the existing game was not changed.\n')
        archive.writestr('SettlementsHall/godot/project.godot',
            'config_version=5\n[application]\nconfig/name="Settlements Hall Asset Viewer"\n'
            'run/main_scene="res://scenes/assets/settlements_hall_preview.tscn"\n'
            'config/features=PackedStringArray("4.6", "GL Compatibility")\n'
            '[display]\nwindow/size/viewport_width=1280\nwindow/size/viewport_height=900\n'
            '[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
            'renderer/rendering_method.mobile="gl_compatibility"\n')
    with zipfile.ZipFile(pack) as archive:
        assert archive.testzip() is None
    if args.publish_dir:
        target = args.publish_dir if args.publish_dir.is_absolute() else ROOT/args.publish_dir
        target.mkdir(parents=True, exist_ok=True)
        published = [pack, *[OUT/(v+'.png') for v in ('hero', 'front', 'rear', 'detail')],
                     gif, mp4, OUT/'asset_stats.json', OUT/'glb_validation.json',
                     OUT/'godot_animation_validation.json', OUT/'round_trip_animation_report.json',
                     OUT/'hand_edit_export_validation.json',
                     manifest_path]
        for p in published:
            shutil.copyfile(p, target/p.name)
        (target/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in published))
        (target/'README.md').write_text('''# Settlements Hall — animated delivery

[Download the complete ZIP](settlements_hall_asset_pack.zip?raw=true) · [SHA-256 checksums](SHA256SUMS.txt)

Contains editable Blender source, GLB, four PNGs, demonstration, reports, source
scripts and an independent Godot 4.6.3 inspection project. Sign in with repository
access to download from this private repository.

**34,643 triangles, 11 PBR materials, 18 meshes / 22 surfaces.**
The original architecture and materials are preserved.

## Animation demonstration

Left: independently hinged double doors opening 100° and closing.
Right: lightweight looping flag deformation, with pinned pole attachment.
Both panels are CPU renders after reimporting the exported GLB.

![Four-second door and cloth demonstration](animation_demo.gif)

[MP4 download](animation_demo.mp4?raw=true) · [GIF](animation_demo.gif)

Four named clips survive GLB export: `Doors_Open`, `Doors_Close`,
`Flags_Wind-loop`, `Hall_Demo-loop`. Godot imports the suffix-marked clips as
looping `Flags_Wind` and `Hall_Demo`. Both roof flags and both entrance pennants
are separate animated objects. The optional wrapper supports independent wind
and door playback.

## Four architectural previews

| Hero | Front |
| --- | --- |
| ![Hero](hero.png) | ![Front](front.png) |
| Rear | Entrance detail |
| ![Rear](rear.png) | ![Detail](detail.png) |

Individual images: [Hero](hero.png) · [Front](front.png) · [Rear](rear.png) · [Detail](detail.png).

## Verification reports

- [Godot 4.6.3 actual playback verification](godot_animation_validation.json)
- [GLB geometry, materials and animation validation](glb_validation.json)
- [GLB round-trip pose samples and source hash](round_trip_animation_report.json)
- [Hand-edit export retains all animation clips](hand_edit_export_validation.json)
- [Asset statistics](asset_stats.json) · [File hashes and source commit](deliverable_manifest.json)

Godot verifies the two 100° hinges, closing poses, all four morph-animated fabrics,
matching loop endpoints, independent playback, glass and collision shapes.
No current-game modification or deployment is part of this delivery. Web and
physical-device performance were not measured. The original static delivery is
retained separately under `../v1-static/`.
''')
    print('SETTLEMENTS_PACKAGE_OK', pack, 'bytes='+str(pack.stat().st_size))


if __name__ == '__main__':
    main()
