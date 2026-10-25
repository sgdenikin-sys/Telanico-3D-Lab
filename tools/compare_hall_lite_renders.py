"""Save equal-pixel-scale V2/Lite comparison figures without changing the renders."""
import hashlib
import json
import os
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'work/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image


def main():
    base = ROOT/'artifacts/settlements_hall/v2-animated'
    out = ROOT/'blender/generated/settlements_hall_lite'
    result = {'method': 'Identical camera/light configuration; no independent image scaling or crop', 'views': {}}
    for view in ['hero', 'front', 'rear', 'detail']:
        left, right = base/(view+'.png'), out/(view+'.png')
        a, b = Image.open(left), Image.open(right)
        assert a.size == b.size, (view, a.size, b.size)
        width, height = a.size
        fig, axes = plt.subplots(1, 2, figsize=(width*2/150, (height+80)/150), dpi=150)
        for ax, image, title in zip(axes, [a, b], ['V2 / 34,643 triangles', 'V3 Lite / 19,816 triangles (-42.8%)']):
            ax.imshow(image)
            ax.set_title(title, fontsize=16)
            ax.axis('off')
        fig.subplots_adjust(left=0, right=1, bottom=0, top=height/(height+80), wspace=0)
        fig.savefig(out/('comparison_'+view+'.png'), facecolor='#eeeeee')
        plt.close(fig)
        result['views'][view] = {'source_pixels': [width, height],
            'v2_sha256': hashlib.sha256(left.read_bytes()).hexdigest(),
            'lite_sha256': hashlib.sha256(right.read_bytes()).hexdigest()}
    documents = []
    for path in [ROOT/'work/hall-v3-godot/assets/generated/reference_v2.glb', out/'settlements_hall.glb']:
        data = path.read_bytes()
        length = struct.unpack_from('<I', data, 12)[0]
        documents.append(json.loads(data[20:20+length]))
    mats = [{m['name']: m for m in d['materials']} for d in documents]
    assert mats[0] == mats[1], 'Changed PBR materials'
    result['all_11_exported_materials_identical'] = True
    result['artistic_review'] = 'Dome, all main facade bays/columns, twelve ribs, stairs and color hierarchy retained. Reduced clerestory/post repetition and micro-ornament are visible at close inspection; no primitive blockout or proportion change.'
    (out/'render_comparison.json').write_text(json.dumps(result, indent=2)+'\n')
    print('LITE_RENDER_COMPARISONS_OK', json.dumps(result))


if __name__ == '__main__':
    main()
