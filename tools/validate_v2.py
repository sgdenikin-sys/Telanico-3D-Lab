"""Geometry, asset provenance and conservative walk-corridor acceptance gates."""
from pathlib import Path
import sys,json,math,struct,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender/scripts'))
import world_v2_layout as L

def glb(path):
    raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
    assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,8)[0]==len(raw)
    return json.loads(raw[20:20+size])

def validate():
    data=json.loads((ROOT/'godot/assets/generated/world_v2.json').read_text())
    assert len(data['landmarks'])==15 and len({p['id'] for p in data['landmarks']})==15
    sites={p['id']:p for p in data['landmarks']}
    assert sites['operations']['island']=='west' and sites['trader']['island']=='east'
    assert sites['tube_w']['position'][0]<-65 and sites['tube_e']['position'][0]>65
    assert sites['tube_w']['position'][2]>25 and sites['tube_e']['position'][2]<-25
    assert math.dist(sites['tube_w']['position'],sites['tube_e']['position'])>150
    for key in ('dock_w','dock_e'):assert abs(sites[key]['position'][2])<1 and abs(sites[key]['position'][0])<20
    assert sum(e['kind']=='bridge' for e in data['edges'])==1
    # A terrace is a walkable district, not a sloping circular obstacle.
    for ident,_,_,_,(x,y),(w,d),kind in L.SITES:
        if kind=='office':
            centre=L.height(x,y)
            assert abs(L.NODES[ident][2]-.24-centre)<.05,(ident,'entrance not on level court')
    assert L.height(-63,24)-L.height(-30,-19)>7,'High civic terrace must read above low dispatch district'
    assert data['boat_story_minutes']==5 and data['tube_story_minutes']==3
    assert data['walk_units_per_story_minute']==1.5*data['pilot_scale']
    assert max(p[0] for poly in L.POLYGONS.values() for p in poly)-min(p[0] for poly in L.POLYGONS.values() for p in poly)>=170
    for edge in L.route_data():
        for p,q in zip(edge['points'],edge['points'][1:]):
            horizontal=math.dist(p[:2],q[:2])
            if horizontal>.1:assert abs(p[2]-q[2])/horizontal<.65,(edge['a'],edge['b'],'steep slope')
        for x,y,z in edge['points']:
            if edge['kind']=='bridge':continue
            if abs(x)<22 and abs(y)<7:continue
            assert L.inside(x,y,'west' if x<0 else 'east'),(edge,'water')
            for ident,_,_,_,(cx,cy),(w,d),kind in L.SITES:
                if kind!='boat':assert not(abs(x-cx)<w/2+.6 and abs(y-cy)<d/2+.6),(edge['a'],edge['b'],ident,'wall')
    for item in data['landmarks']:
        if item['kind']=='office':
            x,h,z=item['entrance'];cx,cy=L.SITES[[s[0] for s in L.SITES].index(item['id'])][4]
            assert abs(-z-cy)>item['footprint'][1]/2+1
    assert data['examples'][0]['walk']>2*data['examples'][0]['boat']
    assert data['examples'][1]['walk']>data['examples'][1]['boat']
    assert data['examples'][3]['tube']==3 and data['examples'][3]['walk']>20
    for entry in json.loads((ROOT/'tools/assets.lock.json').read_text()):
        assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']
    doc=glb(ROOT/'godot/assets/generated/overworld.glb')
    imported=[n for n in doc['nodes'] if 'asset_source' in n.get('extras',{})]
    assert len(imported)>=35 and len(data['asset_models'])>=12,'Real imported architecture AND nature required'
    vertex_count=sum(a['count'] for a in doc['accessors'] if a.get('type')=='VEC3' and 'min' in a)
    assert vertex_count<300000 and len(doc['meshes'])<400
    char=glb(ROOT/'godot/assets/generated/courier.glb')
    assert char.get('skins') and len(char['animations'])==2
    assert any('Idle' in a['name'] for a in char['animations'])
    assert any('Walking_A' in a['name'] for a in char['animations'])
    print('V2_VALIDATION_OK 15 sites; canonical geography; swept corridors; genuine CC0 meshes; real rig/animations;',vertex_count,'vertices')

if __name__=='__main__':validate()
