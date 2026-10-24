"""Compare optional mobile LOD against approved Settlements Hall V2 metadata.

Usage:
python tools/compare_settlements_hall_lod.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'artifacts/settlements_hall/v2-animated/asset_stats.json'
LITE = ROOT / 'blender/generated/settlements_hall_lite/asset_stats.json'
REQUIRED = {'Doors_Open', 'Doors_Close', 'Flags_Wind-loop', 'Hall_Demo-loop'}


def main():
    base = json.loads(BASE.read_text())
    light = json.loads(LITE.read_text())
    before, after = base['source_triangles'], light['source_triangles']
    assert light.get('quality_preset') == 'lite', 'Not the explicit mobile preset'
    assert 0 < after < before, 'No triangle reduction'
    assert after <= 22000, f'Lite geometry too heavy: {after}, target 15–20k, hard review ceiling 22k'
    assert light['material_count'] == base['material_count'] == 11, 'PBR surface regressions'
    assert light['animated_door_hinges'] == 2, 'Both animated door pivots required'
    assert light['animated_fabric_objects'] == 4, 'Four separate animated fabrics required'
    assert REQUIRED.issubset(light['animation_clips']), 'Four V2 animation clips required'
    assert light['wind_loop_seconds'] == 4.0
    assert len(light['dimensions_metres']) == 3
    for b, a in zip(base['dimensions_metres'], light['dimensions_metres']):
        assert abs(b-a) < 0.12, 'Changed landmark silhouette/footprint beyond tolerance'
    print(json.dumps({
        'result': 'SETTLEMENTS_LOD_STATS_PASS', 'baseline_triangles': before,
        'lite_triangles': after, 'reduction_percent': round(100*(before-after)/before, 1),
        'review_target_met': after <= 20000, 'materials': light['material_count'],
        'animation_clips': sorted(light['animation_clips']),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
