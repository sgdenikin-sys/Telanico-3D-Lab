"""Separate ~10k Settlements Hall derivative and exact 2048px painter UV kit.

Uses approved V3 Lite source, existing UV/chart rasterizer and Hall animation
exporter. Never writes game assets. Run with Blender --python-exit-code 1.
"""
from pathlib import Path
import ast, collections, hashlib, json, math, shutil, struct, subprocess, sys
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import build_settlements_hall as H
OUT=ROOT/'artifacts/settlements_hall/v4-painter-10k'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'artifacts/settlements_hall/v3-lite/settlements_hall.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OBJECTS=sorted([o for o in bpy.context.scene.objects if o.type=='MESH' and any(c.name[:2] in ('01','02','03','04','05','06','07') for c in o.users_collection)],key=lambda o:o.name)

def triangles(me):
    me.calc_loop_triangles();return len(me.loop_triangles)
depsgraph=bpy.context.evaluated_depsgraph_get()
BEFORE=sum(triangles(o.evaluated_get(depsgraph).data) for o in OBJECTS)
# Solve at source-mesh granularity so linked repeated details remain identical.
# Thin rectangles, panes, doors and four morph meshes are protected completely.
mult=collections.Counter(o.data for o in OBJECTS);representatives={o.data:o for o in OBJECTS}
def subset(me,faces):
    # Keep original visible vertices and boundaries; discard buried shell faces.
    used=sorted({v for f in faces for v in f.vertices});lookup={v:i for i,v in enumerate(used)}
    new=bpy.data.meshes.new(me.name+' exterior shell')
    new.from_pydata([me.vertices[i].co.copy() for i in used],[],[tuple(lookup[v] for v in f.vertices) for f in faces])
    for m in me.materials:new.materials.append(m)
    new.update()
    for dst,src in zip(new.polygons,faces):dst.use_smooth=src.use_smooth
    return new
for me,o in representatives.items():
    n=triangles(me);name=me.name.lower();linked=[p for p in OBJECTS if p.data==me]
    if 'pier wall with arch opening' in name:
        # The exterior front and every window reveal are original V3 geometry.
        # Only the rear wall face, hidden behind the dark window wells, is cut.
        o.data=subset(me,[f for f in me.polygons if f.normal.y<.99])
    elif any(k in name for k in ('limestone archivolt','bronze glazing frame')):
        # Source arch_ring has groups of front / inner reveal / buried outer.
        o.data=subset(me,[f for f in me.polygons if f.index%3!=2 and f.index<len(me.polygons)-2])
    elif any(k in name for k in ('clerestory cut stone bay','clerestory bronze frame')):
        # Each original rectangular_ring group: front / rear / outer / inner.
        o.data=subset(me,[f for f in me.polygons if f.index%4 in (0,3)])
    elif name.split('.')[0] in ('central mullion','transom'):
        # The invisible back half of a tiny glazing bar adds no silhouette.
        o.data=subset(me,[f for f in me.polygons if f.normal.y<-.01])
    elif 'raised brass dome rib' in name:
        # Retain the exact smooth rib path and its visible half cross-section.
        keep=[]
        for f in me.polygons:
            c=sum((me.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
            if f.normal.dot(Vector((c.x,c.y,(c.z-10.2)*.82)))>=0:keep.append(f)
        o.data=subset(me,keep)
    elif 'ivory entasis column' in name:
        # Symmetric lathe reduction, not arbitrary vertex collapse on columns.
        nring=next(i for i,v in enumerate(me.vertices) if abs(v.co.z-me.vertices[0].co.z)>1e-5)
        profile=[me.vertices[i*nring].co.copy() for i in (0,1,3,5,7,9)]
        seg=6 if nring==8 else 4;verts=[]
        for p in profile:
            r=math.hypot(p.x,p.y)
            verts.extend([(r*math.cos(math.tau*j/seg),r*math.sin(math.tau*j/seg),p.z) for j in range(seg)])
        new=bpy.data.meshes.new(me.name+' six profile rings');new.from_pydata(verts,[],[(i*seg+j,i*seg+(j+1)%seg,(i+1)*seg+(j+1)%seg,(i+1)*seg+j) for i in range(5) for j in range(seg)])
        for m in me.materials:new.materials.append(m)
        new.update()
        for f in new.polygons:f.use_smooth=abs(f.normal.z)<.95
        o.data=new
    elif name.split('.')[0] in ('rotunda annular standing seam roof','blue hipped pavilion roof'):continue
    elif me.shape_keys or n<=16 or o.get('motion_group') or any(k in o.name.lower() for k in ('glass','pane')):continue
    else:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        mod=o.modifiers.new('V4 architectural reduction','DECIMATE')
        mod.ratio=.70 if 'Smooth deep blue' in o.name else .28
        o.data=me.copy()
        for existing in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=existing.name)
    for p in linked:p.data=o.data
# Work on independent source meshes before assigning the documented repeat UVs.
for o in OBJECTS:
    o.data=o.data.copy()
    if not o.data.shape_keys:
        # Dissolve internal coplanar edges left by reduction, retain sharp edges.
        import bmesh
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(.1),verts=list(bm.verts),edges=list(bm.edges),use_dissolve_boundaries=False)
        bm.to_mesh(o.data);bm.free();o.data.update()
    for uv in list(o.data.uv_layers):o.data.uv_layers.remove(uv)
    o.data.uv_layers.new(name='UV0')
AFTER=sum(triangles(o.data) for o in OBJECTS)
print('HALL_REDUCED',BEFORE,AFTER,flush=True)
assert 9000<=AFTER<=11000,AFTER

# Reuse the existing proven packing, overlap check and atlas rasterization.
# Load function definitions only: transport CLI/export steps are not executed.
source=Path(__file__).with_name('reunwrap_transport.py')
tree=ast.parse(source.read_text())
functions=['entry','add_chart','normal_group','plane_coords','ring_size','unwrap','area2','pack','assign','check_uv']
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in functions],type_ignores=[]),str(source),'exec'))
BYNAME={o.name:o for o in OBJECTS};CHARTS=[];RES={'MAIN':2048,'ROOF':2048,'TRIM':2048}
# Identical repeated modules intentionally share the same painted motif. This
# makes windows/columns practical to paint once instead of hundreds of times.
# Doors and animated cloth always remain independent.
masters={};ALIASES={};UVOBJECTS=[]
for o in OBJECTS:
    me=o.data
    signature=json.dumps({'v':[[round(x,6) for x in v.co] for v in me.vertices],
        'f':[(list(f.vertices),f.material_index) for f in me.polygons],
        'm':[m.name for m in me.materials]},sort_keys=True)
    if me.shape_keys or o.get('motion_group'):signature=o.name
    if signature in masters:ALIASES[o.name]=masters[signature].name
    else:masters[signature]=o;UVOBJECTS.append(o)



def sheet_for(o):
    name=o.name.lower();mat=o.data.materials[0].name.lower()
    if o.data.shape_keys or o.get('motion_group'):return 'MAIN'
    if any(k in mat for k in ('brass','bronze')):return 'TRIM'
    if any(k in name for k in ('dome','roof')) and 'pier' not in name:return 'ROOF'
    if any(k in name for k in ('podium','floor','platform','foundation','plinth','entablature','cornice','bead','eaves moulding','rebate')):return 'TRIM'
    return 'MAIN'

DENSITIES={}
def assign():
    placed={};face_meta={};sequence=collections.Counter()
    for sheet in RES:
        low,high=0,2000
        for _ in range(28):
            mid=(low+high)/2
            if pack(sheet,mid) is not None:low=mid
            else:high=mid
        DENSITIES[sheet]=low*.99;placed[sheet]=pack(sheet,DENSITIES[sheet])
    for i,c in enumerate(CHARTS):
        sheet=c['sheet'];size=RES[sheet];density=DENSITIES[sheet]
        sequence[sheet]+=1;c['id']=sheet[0]+f'{sequence[sheet]:03}'
        x,y,rot=placed[sheet][i]
        for f in c['faces']:
            pts=[]
            for a,b in f.pop('xy'):
                if rot:a,b=b,c['w']-a
                pts.append(((x+a*density)/size,(y+b*density)/size))
            f['uv']=pts;o=BYNAME[f['object']];poly=o.data.polygons[f['face']]
            for li,uv in zip(poly.loop_indices,pts):o.data.uv_layers.active.data[li].uv=uv
            face_meta[(o.name,poly.index)]=(sheet,c['id'])
        c['physical_width_m']=c.pop('w');c['physical_height_m']=c.pop('h')
    return min(DENSITIES.values()),face_meta

def dome_unwrap(o,sheet):
    """Eight seam-cut continuous dome gores; no per-triangle confetti."""
    me=o.data;facegroups={}
    for f in me.polygons:
        p=sum((me.vertices[v].co for v in f.vertices),Vector())/len(f.vertices)
        facegroups[f.index]=int((math.atan2(p.y,p.x)%math.tau)/(math.tau/8))
    edges=collections.defaultdict(list)
    for f in me.polygons:
        for e in f.edge_keys:edges[tuple(sorted(e))].append(f.index)
    for e in me.edges:
        fs=edges[tuple(sorted(e.vertices))];e.use_seam=len(fs)==2 and facegroups[fs[0]]!=facegroups[fs[1]]
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.unwrap(method='CONFORMAL',margin=0);bpy.ops.object.mode_set(mode='OBJECT')
    for g in range(8):add_chart('ROOF / DOME GORE '+str(g+1),sheet,[entry(o,f) for f in me.polygons if facegroups[f.index]==g])


def projected_fallback(o,sheet):
    """Exact metric projection per connected coplanar patch, for irregular parts."""
    me=o.data;groups=collections.defaultdict(list)
    for f in me.polygons:
        # Coplanar front/back faces remain one identifiable architectural chart.
        n=f.normal;key=tuple(round(float(v),4) for v in n)+(round(n.dot(f.center),4),)
        groups[key].append(f)
    for k,faces in groups.items():
        n=faces[0].normal;u=n.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();v=n.cross(u).normalized()
        add_chart(o.name+' / '+normal_group(n),sheet,[entry(o,f,[(me.vertices[i].co.dot(u),me.vertices[i].co.dot(v)) for i in f.vertices]) for f in faces])

for o in UVOBJECTS:
    name=o.name.lower();mat=o.data.materials[0].name.lower()
    sheet=sheet_for(o)
    if name=='smooth deep blue metal dome':dome_unwrap(o,sheet)
    elif o.data.shape_keys:
        # One paintable cloth chart per front/back side; the waving geometry
        # is only projected, never flattened or modified. Gold emblems separate.
        groups=collections.defaultdict(list)
        for f in o.data.polygons:
            if abs(f.normal.y)>.6:groups[(f.material_index,'FRONT' if f.normal.y<0 else 'BACK')].append(f)
            else:groups[(f.material_index,'EDGE '+str(f.index))].append(f)
        for (mi,side),faces in groups.items():
            label=o.name+' / '+('FABRIC' if mi==0 else 'EMBLEM')+' / '+side
            if side.startswith('EDGE'):add_chart(label,sheet,[entry(o,f,plane_coords(o,f)) for f in faces])
            else:add_chart(label,sheet,[entry(o,f,[(o.data.vertices[i].co.x,o.data.vertices[i].co.z) for i in f.vertices]) for f in faces])
    else:unwrap(o,sheet)

# Identify and repair only charts which fold during conformal unwrap. The same
# exact triangle-intersection check then runs once on the final entire atlas.
# A local per-object fallback uses no geometry changes or UV stacking.
def normalize_charts():
    for c in CHARTS:
        uvarea=sum(area2(f['xy']) for f in c['faces'])
        physical=sum(BYNAME[f['object']].data.polygons[f['face']].area for f in c['faces'])
        factor=math.sqrt(physical/max(uvarea,1e-20))
        pts=[p for f in c['faces'] for p in f['xy']];lo=[min(p[k] for p in pts) for k in (0,1)]
        for f in c['faces']:f['xy']=[((x-lo[0])*factor,(y-lo[1])*factor) for x,y in f['xy']]
        c['w']=max(p[0] for f in c['faces'] for p in f['xy']);c['h']=max(p[1] for f in c['faces'] for p in f['xy'])
normalize_charts()
# One focused UV repair if conformal unwrap folds on the reduced architecture.
import copy
rawcharts=copy.deepcopy(CHARTS)
density,face_meta=assign()
try:uvtriangles=check_uv()
except AssertionError as exc:
    message=exc.args[0]
    if not isinstance(message,tuple) or message[0]!='Overlapping UV chart':raise
    badlabels=set(message[1]);badnames={f['object'] for c in CHARTS if c['label'] in badlabels for f in c['faces']}
    CHARTS[:]=[c for c in rawcharts if not any(f['object'] in badnames for f in c['faces'])]
    for name in badnames:
        o=BYNAME[name];mat=o.data.materials[0].name.lower();sheet=sheet_for(o)
        projected_fallback(o,sheet)
    # Existing charts are already normalized; newly projected charts must match.
    for c in CHARTS:
        if 'w' not in c:
            uvarea=sum(area2(f['xy']) for f in c['faces']);physical=sum(BYNAME[f['object']].data.polygons[f['face']].area for f in c['faces'])
            factor=math.sqrt(physical/uvarea);pts=[p for f in c['faces'] for p in f['xy']];lo=[min(p[k] for p in pts) for k in (0,1)]
            for f in c['faces']:f['xy']=[((x-lo[0])*factor,(y-lo[1])*factor) for x,y in f['xy']]
            c['w']=max(p[0] for f in c['faces'] for p in f['xy']);c['h']=max(p[1] for f in c['faces'] for p in f['xy'])
    density,face_meta=assign();uvtriangles=check_uv()
    print('UV_LOCAL_REPAIR',len(badnames),flush=True)

# Propagate deliberate repeat UVs to matching geometry, without merging objects.
for name,master in ALIASES.items():
    o=BYNAME[name];src=BYNAME[master]
    for a,b in zip(o.data.uv_layers.active.data,src.data.uv_layers.active.data):a.uv=b.uv
    for f in o.data.polygons:face_meta[(name,f.index)]=face_meta[(master,f.index)]
payload={'intentional_repeat_uvs':ALIASES,'asset':'Settlements Hall V4 Painter 10k','revision':'V4 Painter 10k','sheets':RES,'pixels_per_meter':DENSITIES,'charts':CHARTS}
(OUT/'surface_mapping.json').write_text(json.dumps(payload,indent=2)+'\n')
bpy.ops.object.select_all(action='DESELECT')
for o in OBJECTS:o.select_set(True)
bpy.context.view_layer.objects.active=OBJECTS[0]
bpy.ops.preferences.addon_enable(module='io_mesh_uv_layout')
for sheet,size in RES.items():
    for o in OBJECTS:
        for f in o.data.polygons:f.select=face_meta[(o.name,f.index)][0]==sheet
    bpy.ops.uv.export_layout(filepath=str(OUT/(sheet.lower()+'_native.svg')),mode='SVG',export_all=False,size=(size,size),opacity=0,modified=False)
subprocess.run([shutil.which('python'),str(Path(__file__).with_name('draw_painter_uv.py')),str(OUT)],check=True)
# Include every repeat in the face-to-atlas CSV, not just canonical modules.
import csv
with (OUT/'surface_mapping.csv').open(newline='',encoding='utf-8-sig') as f:rows=list(csv.reader(f))
byobject=collections.defaultdict(list)
for row in rows[1:]:byobject[row[3]].append(row)
with (OUT/'surface_mapping.csv').open('a',newline='',encoding='utf-8') as f:
    writer=csv.writer(f)
    for name,master in ALIASES.items():
        for row in byobject[master]:
            r=row.copy();r[3]=name;writer.writerow(r)

# Add blank packed painter canvases; retain the original visual materials.
images={s:bpy.data.images.load(str(OUT/(s.lower()+'_paint.png'))) for s in RES}
for im in images.values():im.pack()
materials={}
for o in OBJECTS:
    sheet=face_meta[(o.name,0)][0]
    new=[]
    for src in o.data.materials:
        key=(sheet,src.name)
        if key not in materials:
            m=src.copy();m.name=sheet+'__'+src.name;m['paint_atlas']=sheet.lower()+'_paint.png';m['uv_layout']=sheet.lower()+'_layout.png'
            n=m.node_tree.nodes.new('ShaderNodeTexImage');n.name='PAINT_ATLAS';n.label='Paint canvas: connect Color to Base Color after painting';n.image=images[sheet];m.node_tree.nodes.active=n;materials[key]=m
        new.append(materials[key])
    o.data.materials.clear()
    for m in new:o.data.materials.append(m)
    o['painting_revision']='V4 Painter 10k'
# Preserve the proven export batching and each individual moving part.
H.ASSET[:]=OBJECTS;H.M.update({m.name:m for o in OBJECTS for m in o.data.materials})
scene=bpy.context.scene;scene.frame_set(1)
scene['asset']='TELANICO | Settlements Hall V4 Painter 10k'
scene['regenerate']='blender -b --python blender/scripts/prepare_hall_painter.py'
scene['runtime_export']='Use blender/scripts/export_settlements_hall.py with explicit --output. UVs match this V4 kit only.'
stats=H.export_runtime(OUT/'settlements_hall.glb')
assert stats['source_triangles']==AFTER
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'settlements_hall.blend'))
# Actual matched-angle original-material and chart checker renders.
scene.render.resolution_x=1200;scene.render.resolution_y=1040;scene.render.resolution_percentage=100
scene.cycles.samples=16;scene.cycles.use_denoising=False
scene.camera=bpy.data.objects['Review camera | hero']
scene.render.filepath=str(OUT/'isometric.png');bpy.ops.render.render(write_still=True)
saved={o.name:list(o.data.materials) for o in OBJECTS};diag={}
for sheet in RES:
    m=bpy.data.materials.new('REVIEW_'+sheet);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.9
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/(sheet.lower()+'_checker.png')));m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);diag[sheet]=m
for o in OBJECTS:
    sheets=[m['paint_atlas'].split('_')[0].upper() for m in o.data.materials];o.data.materials.clear()
    for s in sheets:o.data.materials.append(diag[s])
scene.render.filepath=str(OUT/'mapping_front.png');bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['Review camera | rear'];scene.render.filepath=str(OUT/'mapping_rear.png');bpy.ops.render.render(write_still=True)
# Saved Blend was written before diagnostic overrides; no checker ships as albedo.
raw=(OUT/'settlements_hall.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n])
exported=sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives'])
assert exported==AFTER,(exported,AFTER)
assert all('TEXCOORD_0' in p['attributes'] for m in g['meshes'] for p in m['primitives'])
clips={a['name'] for a in g['animations']};assert clips=={'Doors_Open','Doors_Close','Flags_Wind-loop','Hall_Demo-loop'}
flags=[n for n in g['nodes'] if n.get('name','').startswith('Flag_')];assert len(flags)==4
for n in flags:assert all(len(p.get('targets',[]))==3 for p in g['meshes'][n['mesh']]['primitives'])
assert all(m.get('alphaMode')=='BLEND' for m in g['materials'] if 'glass' in m['name'])
checks={'source':'V3 Lite','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'original_triangles':BEFORE,'triangles':AFTER,'reduction_percent':round((1-AFTER/BEFORE)*100,1),'source_mesh_objects':len(OBJECTS),'charts':dict(collections.Counter(c['sheet'] for c in CHARTS)),'density_px_per_m':{k:round(v,3) for k,v in DENSITIES.items()},'padding_px':12,'intentional_shared_repeat_objects':len(ALIASES),'unique_paint_modules':len(UVOBJECTS),'uv_check':'UV0 complete; positive UV triangle areas; exact triangle intersection check; disjoint chart bounds; identical modules intentionally share UVs (listed in surface_mapping.json)','animations':sorted(clips),'animated_flags':len(flags),'materials':'Original PBR and glass alpha retained; unconnected PAINT_ATLAS image nodes','runtime':'Not changed; no game build or deploy'}
(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
for f in OUT.glob('*.blend1'):f.unlink()
print('HALL_PAINTER_COMPLETE '+json.dumps(checks),flush=True)
