"""Painter UV revision; load approved V1 geometry, never rebuild or write runtime.

blender -b -t 8 --python-exit-code 1 --python blender/scripts/reunwrap_transport.py -- --asset pneumatic_station
Run and commit one asset before the next. MAIN and TRIM are both 2048².
Both sheets share a physical texel density. No stacked/overlapping UV islands.
"""
from pathlib import Path
import argparse, collections, hashlib, json, math, shutil, struct, subprocess, sys
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--asset',required=True,choices=['pneumatic_station','commuter_ferry','harbor_launch'])
A=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
OUT=ROOT/'artifacts/transport_production/v2-painter-uv'/A.asset
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'artifacts/transport_production/v1'/A.asset/(A.asset+'.blend')))
OBJECTS=[o for o in bpy.context.scene.objects if o.type=='MESH' and 'uv_region' in o]
BYNAME={o.name:o for o in OBJECTS}
CHARTS=[]; GROUPED=collections.defaultdict(list)
RES={'MAIN':2048,'TRIM':2048}


def geometry_hash():
    h=hashlib.sha256()
    for o in sorted(OBJECTS,key=lambda o:o.name):
        h.update(o.name.encode())
        for row in o.matrix_world:
            h.update(struct.pack('<4f',*row))
        for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
        for f in o.data.polygons:h.update(struct.pack('<I',len(f.vertices))+struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return h.hexdigest()


BEFORE=geometry_hash()


def entry(o,f,xy=None):
    uv=o.data.uv_layers.active.data
    return {'object':o.name,'face':f.index,'facing':normal_group(f.normal),'xy':xy or [tuple(uv[i].uv) for i in f.loop_indices]}


def add_chart(label,sheet,faces):
    if not faces:return
    CHARTS.append({'label':label,'sheet':sheet,'faces':faces})


def normal_group(n):
    axis=max(range(3),key=lambda i:abs(n[i]))
    return ('RIGHT' if n.x>0 else 'LEFT') if axis==0 else ('BACK' if n.y>0 else 'FRONT') if axis==1 else ('TOP' if n.z>0 else 'BOTTOM')


def plane_coords(o,f):
    n=f.normal;axis=max(range(3),key=lambda i:abs(n[i]))
    axes=(0,1) if axis==2 else (0,2) if axis==1 else (1,2)
    return [(o.data.vertices[v].co[axes[0]],o.data.vertices[v].co[axes[1]]) for v in f.vertices]


def ring_size(o):
    """Detect the existing ordered circular rings, including bent tubing."""
    me=o.data;nv=len(me.vertices);edges={tuple(sorted(e.vertices)) for e in me.edges}
    for n in (4,6,8,10,12,16,20,24,32,48,64):
        if nv%n or nv//n<2:continue
        good=True
        for j in (0,(nv//n)//2,nv//n-1):
            pts=[me.vertices[j*n+i].co for i in range(n)];c=sum(pts,Vector())/n
            radii=[(p-c).length for p in pts];r=sum(radii)/n
            # V1 station has a vertical scale baked into its upper vertices,
            # so a few bent pipe rings are ellipses rather than perfect circles.
            normal=(pts[1]-pts[0]).cross(pts[2]-pts[0]).normalized()
            if r<1e-7 or max(abs(x-r) for x in radii)>r*.32 or max(abs((p-c).dot(normal)) for p in pts)>1e-5:
                good=False;break
            if sum(tuple(sorted((j*n+i,j*n+(i+1)%n))) in edges for i in range(n))<n:good=False;break
        if good:return n
    return None


def unwrap(o,sheet):
    me=o.data
    for uv in list(me.uv_layers):me.uv_layers.remove(uv)
    me.uv_layers.new(name='UV0')
    for e in me.edges:e.use_seam=False
    for p in me.polygons:p.select=True
    name=o.name.lower();groups={};spine=None
    flat=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices)<1e-5
    if len(me.polygons)==1 or flat:
        for f in me.polygons:
            for i,p in zip(f.loop_indices,plane_coords(o,f)):me.uv_layers.active.data[i].uv=p
        add_chart(o.name,sheet,[entry(o,f) for f in me.polygons]);return
    if name=='hollow_navy_hull_shell':
        for f in me.polygons:
            rows={v//64 for v in f.vertices};band=min(rows)
            side='RIGHT' if f.center.x>0 else 'LEFT'
            groups[f.index]='HULL_BOTTOM' if len(rows)==1 else ('HULL_'+side if band<3 else 'GUNWALE_UNDERSIDE' if band==3 else 'INTERIOR_BULWARK_'+side)
    elif name=='removable_pressure_cap':
        for f in me.polygons:
            p=sum((me.vertices[v].co for v in f.vertices),Vector())/len(f.vertices)
            groups[f.index]='ROOF_GORE_'+str(int(((math.atan2(p.y,p.x)+math.pi)%(math.tau))/math.tau*8)+1)
    else:
        n=ring_size(o)
        if n:
            spine=n
            annulus=any(k in name for k in ('plinth_outer_step','floor_inlay_border','structural_crown_ring','deep_navy_cornice'))
            for f in me.polygons:
                rows={v//n for v in f.vertices}
                if len(rows)==1:groups[f.index]='CAP_'+str(next(iter(rows)))
                elif annulus:groups[f.index]='BAND_'+str(min(rows))
                else:groups[f.index]='WRAP'
        else:
            groups={f.index:normal_group(f.normal) for f in me.polygons}
    edges=collections.defaultdict(list)
    for f in me.polygons:
        for k in f.edge_keys:edges[tuple(sorted(k))].append(f.index)
    # A cube net: four sides unfold off TOP, BOTTOM attaches to FRONT.
    tree={frozenset(('TOP',g)) for g in ('FRONT','BACK','LEFT','RIGHT')}
    tree.add(frozenset(('FRONT','BOTTOM')))
    for e in me.edges:
        fs=edges[tuple(sorted(e.vertices))]
        if len(fs)==2:
            a,b=(groups[i] for i in fs)
            if a!=b:e.use_seam=spine is not None or name in ('hollow_navy_hull_shell','removable_pressure_cap') or frozenset((a,b)) not in tree
        if spine and all(v%spine==0 for v in e.vertices):e.use_seam=True
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='CONFORMAL',margin=0,correct_aspect=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Closed horizontal annuli should remain literal top-down rings. LSCM can
    # fold very thin unslit rings; planar projection is exact and needs no cut.
    if any(g.startswith('BAND_') for g in groups.values()):
        for group in set(groups.values()):
            faces=[f for f in me.polygons if groups[f.index]==group]
            zs=[me.vertices[v].co.z for f in faces for v in f.vertices]
            if max(zs)-min(zs)<1e-6:
                for f in faces:
                    for li,v in zip(f.loop_indices,f.vertices):me.uv_layers.active.data[li].uv=me.vertices[v].co.xy
    # Collect actual connected UV islands, including bevel faces attached to nets.
    parent=list(range(len(me.polygons)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    uv=me.uv_layers.active.data
    def edge_uv(f,vs):
        return {v:Vector(uv[i].uv) for v,i in zip(f.vertices,f.loop_indices) if v in vs}
    for k,fs in edges.items():
        if len(fs)!=2:continue
        a,b=(me.polygons[i] for i in fs);ua,ub=edge_uv(a,k),edge_uv(b,k)
        if all((ua[v]-ub[v]).length<1e-6 for v in k):parent[find(a.index)]=find(b.index)
    islands=collections.defaultdict(list)
    for f in me.polygons:islands[find(f.index)].append(f)
    for i,faces in enumerate(islands.values()):
        dominant=max(faces,key=lambda f:f.area)
        suffix=groups[dominant.index] if name in ('hollow_navy_hull_shell','removable_pressure_cap') or spine else 'NET'
        add_chart(o.name+' / '+suffix+(' '+str(i+1) if len(islands)>1 else ''),sheet,[entry(o,f) for f in faces])


def analytic_surfaces(o):
    """Stitch UVs across separate source objects without merging any geometry."""
    name=o.name
    if name.startswith('Canopy_glass_'):
        # The barrel is an extrusion: its faceted arc length gives an exact,
        # distortion-free rectangle, continuous over all eighty source panels.
        w=1.45;h=2.08;sill=1.45
        profile=[Vector((w*math.cos(j*math.pi/16),sill+h*math.sin(j*math.pi/16))) for j in range(17)]
        lengths=[0]
        for a,b in zip(profile,profile[1:]):lengths.append(lengths[-1]+(b-a).length)
        for f in o.data.polygons:
            xy=[]
            for v in f.vertices:
                p=o.data.vertices[v].co;j=min(range(17),key=lambda j:(profile[j]-Vector((p.x,p.z))).length)
                xy.append((lengths[j],p.y))
            GROUPED[('MAIN','ROOF / GLASS CANOPY — continuous')].append(entry(o,f,xy))
        return True
    if name.startswith('Cockpit_windscreen_'):
        for f in o.data.polygons:
            xy=[]
            for v in f.vertices:
                p=o.data.vertices[v].co;t=math.atan2((p.y+1.3)/1.12,p.x/1.22)
                if t<math.pi-1e-5:t+=math.tau
                # Faceted elliptical arc with exact segment-length coordinates.
                j=round((t-math.pi)/math.pi*12);j=max(0,min(12,j))
                pts=[Vector((1.22*math.cos(math.pi+i*math.pi/12),1.12*math.sin(math.pi+i*math.pi/12))) for i in range(13)]
                u=sum((pts[k+1]-pts[k]).length for k in range(j));xy.append((u,p.z))
            GROUPED[('MAIN','WINDOWS / COCKPIT continuous')].append(entry(o,f,xy))
        return True
    if name.startswith('Mosaic_glazing_') or name=='Entry_upper_glazing':
        for f in o.data.polygons:
            pts=[o.data.vertices[v].co for v in f.vertices];mean=sum(pts,Vector())/len(pts)
            t=math.atan2(mean.y,mean.x)
            q=int(((t+math.pi/4)%(math.tau))/math.tau*4)
            label=['RIGHT','BACK','LEFT','FRONT'][q];centre=q*math.pi/2
            xy=[]
            for p in pts:
                a=math.atan2(p.y,p.x);a=centre+(a-centre+math.pi)%math.tau-math.pi
                xy.append((a*3.05,p.z))
            GROUPED[('MAIN','WINDOWS / '+label+' panorama')].append(entry(o,f,xy))
        return True
    return False


def area2(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2


def prepare():
    for o in OBJECTS:
        if analytic_surfaces(o):continue
        mat=o.data.materials[0].name.lower()
        sheet='TRIM' if mat.startswith(('brass','bronze')) else 'MAIN'
        unwrap(o,sheet)
    for (sheet,label),faces in GROUPED.items():add_chart(label,sheet,faces)
    # Normalize each chart's average area to physical m², then keep a shared
    # pixels/m scale over both sheets. Curved surfaces retain conformal shapes.
    for c in CHARTS:
        uv_area=sum(area2(f['xy']) for f in c['faces'])
        physical=sum(BYNAME[f['object']].data.polygons[f['face']].area for f in c['faces'])
        assert uv_area>1e-13,(c['label'],uv_area)
        factor=math.sqrt(physical/uv_area)
        pts=[p for f in c['faces'] for p in f['xy']];lo=[min(p[k] for p in pts) for k in (0,1)]
        for f in c['faces']:f['xy']=[((x-lo[0])*factor,(y-lo[1])*factor) for x,y in f['xy']]
        c['w']=max(p[0] for f in c['faces'] for p in f['xy']);c['h']=max(p[1] for f in c['faces'] for p in f['xy'])


def pack(sheet,density):
    size=RES[sheet];free=[(8,8,size-16,size-16)];result={};pad=6
    for i,c in sorted(enumerate(CHARTS),key=lambda p:-max(p[1]['w'],p[1]['h'])):
        if c['sheet']!=sheet:continue
        w,h=c['w']*density+2*pad,c['h']*density+2*pad
        options=[]
        for j,(x,y,fw,fh) in enumerate(free):
            for rot,(ww,hh) in enumerate(((w,h),(h,w))):
                if ww<=fw and hh<=fh:options.append((min(fw-ww,fh-hh),max(fw-ww,fh-hh),j,rot,ww,hh))
        if not options:return None
        _,_,j,rot,ww,hh=min(options);x,y,fw,fh=free.pop(j)
        result[i]=(x+pad,y+pad,bool(rot))
        # Non-overlapping guillotine bins, with a short-side split.
        if fw-ww>fh-hh:
            free.extend([(x+ww,y,fw-ww,fh),(x,y+hh,ww,fh-hh)])
        else:free.extend([(x+ww,y,fw-ww,hh),(x,y+hh,fw,fh-hh)])
        free=[r for r in free if r[2]>1e-6 and r[3]>1e-6]
    return result


def assign():
    low=0;high=2000
    for _ in range(28):
        mid=(low+high)/2
        if all(pack(s,mid) is not None for s in RES):low=mid
        else:high=mid
    density=low*.99;placed={s:pack(s,density) for s in RES}
    sequence=collections.Counter();face_meta={}
    for i,c in enumerate(CHARTS):
        sheet=c['sheet'];size=RES[sheet];sequence[sheet]+=1;c['id']=('M' if sheet=='MAIN' else 'T')+f'{sequence[sheet]:03}'
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
    return density,face_meta


def check_uv():
    # Check within each chart; chart bounding boxes are disjoint by construction.
    # Triangle intersection excludes shared boundaries; grid bounds limit work.
    from mathutils.geometry import intersect_line_line_2d
    def clip(poly,a,b):
        out=[]
        def side(p):return (b.x-a.x)*(p.y-a.y)-(b.y-a.y)*(p.x-a.x)
        for p,q in zip(poly,poly[1:]+poly[:1]):
            sp,sq=side(p),side(q)
            if sp>=-1e-12:out.append(p)
            if (sp>0 and sq<0) or (sp<0 and sq>0):out.append(p+(q-p)*(sp/(sp-sq)))
        return out
    failures=[];max_stretch=0;triangles=0
    for c in CHARTS:
        seen=collections.defaultdict(list)
        for f in c['faces']:
            pts=[Vector(p) for p in f['uv']]
            assert all(0<p.x<1 and 0<p.y<1 for p in pts)
            for tri in tessellate_polygon([[Vector((p.x,p.y,0)) for p in pts]]):
                t=[pts[p].copy() if isinstance(p,int) else Vector((p.x,p.y)) for p in tri];triangles+=1
                ar=area2([tuple(p) for p in t]);assert ar>1e-16,(c['label'],f['face'])
                cross=(t[1]-t[0]).cross(t[2]-t[0])
                if cross<0:t.reverse()
                lo=[min(p[k] for p in t) for k in (0,1)];hi=[max(p[k] for p in t) for k in (0,1)]
                keys=[(x,y) for x in range(int(lo[0]*64),int(hi[0]*64)+1) for y in range(int(lo[1]*64),int(hi[1]*64)+1)]
                candidates={id(q):q for k in keys for q in seen[k]}
                for q in candidates.values():
                    p=t
                    for a,b in zip(q,q[1:]+q[:1]):
                        p=clip(p,a,b)
                        if len(p)<3:break
                    if len(p)>=3 and area2([tuple(v) for v in p])>max(1e-12,ar*1e-5):
                        failures.append(c['label']);break
                for k in keys:seen[k].append(t)
    assert not failures,('Overlapping UV chart',sorted(set(failures)))
    return triangles


def exports(face_meta):
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJECTS:o.select_set(True)
    bpy.context.view_layer.objects.active=OBJECTS[0]
    bpy.ops.preferences.addon_enable(module='io_mesh_uv_layout')
    for sheet,size in RES.items():
        for o in OBJECTS:
            for f in o.data.polygons:f.select=face_meta[(o.name,f.index)][0]==sheet
        bpy.ops.uv.export_layout(filepath=str(OUT/(sheet.lower()+'_native.svg')),mode='SVG',export_all=False,size=(size,size),opacity=0,modified=False)
    subprocess.run([shutil.which('python') or shutil.which('python3'),str(Path(__file__).with_name('draw_painter_uv.py')),str(OUT)],check=True)
    # Preserve approved constant PBR appearance. An unused image node on each
    # material is ready for the painter; connect it after painting, not before.
    images={s:bpy.data.images.load(str(OUT/(s.lower()+'_paint.png'))) for s in RES}
    for image in images.values():image.pack()
    materials={}
    for o in OBJECTS:
        original=list(o.data.materials);slots=[]
        for f in o.data.polygons:
            sheet=face_meta[(o.name,f.index)][0];src=original[f.material_index];key=(sheet,src.name)
            if key not in materials:
                m=src.copy();m.name=sheet+'__'+src.name;m['paint_atlas']=sheet.lower()+'_paint.png'
                m['uv_layout']=sheet.lower()+'_layout.png'
                n=m.node_tree.nodes.new('ShaderNodeTexImage');n.name='PAINT_ATLAS';n.label='Connect Color to Base Color AFTER painting'
                n.image=images[sheet];m.node_tree.nodes.active=n;materials[key]=m
            m=materials[key]
            if m not in slots:slots.append(m)
        for f in o.data.polygons:
            sheet=face_meta[(o.name,f.index)][0];src=original[f.material_index]
            f.material_index=slots.index(materials[(sheet,src.name)])
        o.data.materials.clear()
        for m in slots:o.data.materials.append(m)
        o['painting_revision']='V2 Painter UV'
    pivots=[o for o in bpy.context.scene.objects if o.type=='EMPTY' and o.animation_data]
    for o in pivots:
        for t in o.animation_data.nla_tracks:t.mute=True
        o.rotation_euler.z=o['closed_angle']
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJECTS+pivots:o.select_set(True)
    bpy.context.view_layer.objects.active=OBJECTS[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/(A.asset+'.glb')),export_format='GLB',use_selection=True,
        export_animations=True,export_animation_mode='NLA_TRACKS',export_texcoords=True,export_cameras=False,export_lights=False,export_extras=True)
    for o in pivots:o.rotation_euler.z=o['closed_angle']
    bpy.context.view_layer.update()
    assert geometry_hash()==BEFORE,'Source geometry or transforms changed'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(A.asset+'.blend')))
    # Two small targeted diagnostic renders: exterior and roofless interior.
    scene=bpy.context.scene;scene.render.resolution_x=scene.render.resolution_y=1024
    scene.cycles.samples=8;scene.cycles.use_denoising=False
    saved={o.name:list(o.data.materials) for o in OBJECTS};diag={}
    for sheet in RES:
        m=bpy.data.materials.new('REVIEW_'+sheet);m.use_nodes=True
        shader=m.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.9
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/(sheet.lower()+'_checker.png')))
        m.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);diag[sheet]=m
    for o in OBJECTS:
        sheets=[m['paint_atlas'].split('_')[0].upper() for m in o.data.materials]
        o.data.materials.clear()
        for s in sheets:o.data.materials.append(diag[s])
    scene.render.filepath=str(OUT/'mapping_exterior.png');bpy.ops.render.render(write_still=True)
    for o in bpy.data.collections['ROOF_removable'].objects:o.hide_render=True
    for o in OBJECTS:
        if any(m.diffuse_color[3]<.99 for m in saved[o.name]):o.hide_render=True
    for o in pivots:o.rotation_euler.z=o['closed_angle']+math.radians(o['opening_degrees'])
    if A.asset=='pneumatic_station':
        scene.camera.location=(10,-12,16)
        scene.camera.rotation_euler=(Vector((0,0,1.8))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
        scene.camera.data.ortho_scale=11.5
    scene.render.filepath=str(OUT/'mapping_interior.png');bpy.ops.render.render(write_still=True)
    # Diagnostics do not modify the saved asset, materials or animation poses.
    for p in OUT.glob('*.blend1'):p.unlink()


prepare();density,face_meta=assign();triangles=check_uv()
payload={'asset':A.asset,'revision':'V2 Painter UV','sheets':RES,'pixels_per_meter':density,'charts':CHARTS}
(OUT/'surface_mapping.json').write_text(json.dumps(payload,indent=2)+'\n')
exports(face_meta)
data=(OUT/(A.asset+'.glb')).read_bytes();n=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+n])
assert {a['name'] for a in g['animations']}=={'Doors_Open','Doors_Close'}
assert all('TEXCOORD_0' in p['attributes'] for m in g['meshes'] for p in m['primitives'])
old=json.loads((ROOT/'artifacts/transport_production/v1'/A.asset/'surface_mapping.json').read_text())
checks={'asset':A.asset,'geometry_sha256_unchanged':BEFORE,'triangles_checked':triangles,
    'charts':dict(collections.Counter(c['sheet'] for c in CHARTS)),'old_face_islands':len(old['surfaces']),
    'density_px_per_m':round(density,3),'padding_px_between_chart_bounds':12,
    'uv':'complete UV0; bounds and positive triangle areas; exact triangle intersection check passed per chart; disjoint chart packing',
    'animations':[a['name'] for a in g['animations']],'runtime':'not changed; no engine build or deployment'}
(OUT/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(OUT/'README.md').write_text(f'''# {A.asset} — V2 Painter UV

Geometry, pivots and animation actions are unchanged from V1. This is a separate
painting source, NOT installed in the live game. Old V1 UVs do not match these maps.

Two atlases, both on UV0, selected by material prefix (MAIN__ / TRIM__):
- MAIN: 2048×2048, hull/walls, roof, glass, doors and interior furnishings.
- TRIM: 2048×2048, continuous metal wraps, rails, frames and hardware.
- Shared physical density: {density:.2f} pixels/m. Unique UVs, no stacked duplicates.

`main_layout.png` / `trim_layout.png`: clean transparent ISLAND BOUNDARIES.
`main_wire.png` / `trim_wire.png`: full native Blender SVG export rasterized to PNG.
`main_guide.png` / `trim_guide.png`: exactly the same coordinates, chart IDs and colors.
`main_key.png` / `trim_key.png`, `surface_mapping.csv`: names and face correspondence.
`main_paint.png` / `trim_paint.png`: blank white painting canvases at correct size.
`main_checker.png` / `trim_checker.png`: temporary chart-ID checker diagnostics.
`mapping_exterior.png` / `mapping_interior.png`: actual mapped Blender renders.
`{A.asset}.blend` / `{A.asset}.glb`: models that MATCH these UVs.

Paint on a separate layer using layout/guide as a locked reference. Hide all guide
and checker layers before saving the painted atlas; never resize or move islands.
In Blender connect the matching PAINT_ATLAS image node Color to Principled Base Color.
The image nodes are deliberately unconnected to preserve the approved PBR appearance.
For opacity keep the original glass Alpha values; for Godot use white albedo tint
when assigning a full-color atlas. Every material records `paint_atlas` in extras.

MAIN and TRIM coordinates may coincide because they are DIFFERENT images/materials.
There is no overlap within either sheet. Keep the original dimensions and padding.
Roof remains separately selectable; Doors_Open and Doors_Close remain separate clips.
`checks.json` records geometry identity and UV checks; no gameplay regression.
''')
print('PAINTER_UV_COMPLETE '+json.dumps(checks))
