"""Asset-first Telanico V2. Reviewed source bytes are fetched by fetch_assets.py.
Headless generation: blender -b --python-exit-code 1 --python .../build_world_v2.py
Optional -- --render emits comparable 30/38/40/45/55-degree CPU review frames.
"""
from pathlib import Path
import sys,json,math,struct,random
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_overworld import cube,cylinder,torus,ribbon,empty,parent_keep,material
import world_v2_layout as L
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'blender/generated';ASSETS=ROOT/'godot/assets/generated'
VENDOR=ROOT/'assets/vendor/world/addons/kaykit_medieval_hexagon_pack/Assets/gltf'
M={};CACHE={};USED=set()


def reset():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)


def courier():
    reset()
    source=ROOT/'assets/vendor/character/addons/kaykit_character_pack_adventures/Characters/gltf/Rogue_Hooded.glb'
    data=source.read_bytes();length,kind=struct.unpack_from('<I4s',data,12)
    doc=json.loads(data[20:20+length]);doc['animations']=[a for a in doc['animations'] if a['name'] in ('Idle','Walking_A')]
    chunk=json.dumps(doc,separators=(',',':')).encode();chunk+=b' '*((-len(chunk))%4)
    tail=data[20+length:];content=struct.pack('<I4s',len(chunk),b'JSON')+chunk+tail
    curated=OUT/'courier-source.glb';curated.write_bytes(struct.pack('<4sII',b'glTF',2,len(content)+12)+content)
    bpy.ops.import_scene.gltf(filepath=str(curated))
    root=empty('Temporary courier - KayKit rig, not approved Cooper likeness')
    original=[o for o in bpy.context.scene.objects if o!=root]
    for o in original:
        if o.parent is None:parent_keep(o,root)
    bpy.context.view_layer.update()
    verts=[o.matrix_world@Vector(c) for o in original if o.type=='MESH' for c in o.bound_box]
    lo=min(v.z for v in verts);hi=max(v.z for v in verts)
    root.scale=(2.4/(hi-lo),)*3;root.location.z=-lo*root.scale.z
    root['source']='KayKit Adventurers 1.0 / Rogue_Hooded / CC0'
    for action in bpy.data.actions:
        if 'Idle' in action.name or 'Walking' in action.name:
            for curve in getattr(action,'fcurves',[]):
                for key in curve.keyframe_points:key.interpolation='LINEAR'
    bpy.context.scene.render.fps=30
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'courier.blend'))
    bpy.ops.export_scene.gltf(filepath=str(ASSETS/'courier.glb'),export_format='GLB',export_extras=True)
    print('COURIER_OK real imported rig; Idle and Walking_A only')
    reset()


def atlas_material():
    path=VENDOR/'buildings/blue/hexagons_medieval.png'
    image=bpy.data.images.load(str(path),check_existing=True)
    image.scale(512,512)
    pixels=list(image.pixels[:])
    for i in range(0,len(pixels),4):
        r,g,b=pixels[i:i+3]
        if b>r*1.18 and b>g*1.02:
            t=max(r,g,b);r,g,b=t*.30,t*.61,t*.66
        elif g>r*1.18 and g>b*1.08:r,g,b=r*.85+.025,g*.78+.025,b*.85+.02
        else:
            grey=(r+g+b)/3;r,g,b=r*.8+grey*.2,g*.8+grey*.2,b*.8+grey*.2
        pixels[i:i+3]=[r,g,b]
    image.pixels[:]=pixels
    image.filepath_raw=str(OUT/'telanico-kaykit-atlas.png');image.file_format='PNG';image.save();image.pack()
    mat=material('Telanico remapped KayKit atlas',(.7,.7,.7))
    texture=mat.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image
    mat.node_tree.links.new(texture.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    return mat


def asset(name,position,footprint,part='building'):
    folder='buildings/blue' if part=='building' else 'decoration/nature'
    filename=f'building_{name}_blue' if part=='building' else name
    if filename not in CACHE:
        before=set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(VENDOR/folder/(filename+'.gltf')))
        meshes=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
        bpy.ops.object.select_all(action='DESELECT')
        for o in meshes:o.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join()
        obj=bpy.context.object;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        bpy.context.view_layer.update()
        corners=[obj.matrix_world@Vector(v) for v in obj.bound_box]
        low=Vector(tuple(min(v[j] for v in corners) for j in range(3)))
        high=Vector(tuple(max(v[j] for v in corners) for j in range(3)))
        centre=Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
        for v in obj.data.vertices:v.co=obj.matrix_world@v.co-centre
        mesh=obj.data.copy();mesh.materials.clear();mesh.materials.append(M['atlas'])
        for poly in mesh.polygons:poly.material_index=0
        CACHE[filename]=(mesh,high-low)
        for o in list(set(bpy.data.objects)-before):bpy.data.objects.remove(o,do_unlink=True)
    mesh,size=CACHE[filename]
    obj=bpy.data.objects.new('CC0 '+filename,mesh);bpy.context.collection.objects.link(obj)
    scale=min(footprint[0]/max(size.x,.01),footprint[1]/max(size.y,.01))
    obj.scale=(scale,)*3;obj.location=position
    obj['asset_source']=f'KayKit Medieval Hexagon 1.0 / {filename} / CC0'
    USED.add(filename)
    return obj,size.z*scale


def boundary(side,angle):
    cx=-49 if side=='west' else 49;dx,dy=math.cos(angle),math.sin(angle)
    best=1e6;poly=L.POLYGONS[side]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        ex,ey=q[0]-p[0],q[1]-p[1];cross=dx*ey-dy*ex
        if abs(cross)<1e-8:continue
        ax,ay=p[0]-cx,p[1]
        t=(ax*ey-ay*ex)/cross;u=(ax*dy-ay*dx)/cross
        if t>0 and 0<=u<=1:best=min(best,t)
    return best+.35*math.sin(angle*11)+.2*math.cos(angle*17)


ROAD_BUCKETS={}
def road_subgrade(x,y):
    # Grade the soil below the paved surface. Different triangle diagonals in
    # terrain and road meshes must never poke grass through the promenade.
    if not ROAD_BUCKETS:
        for edge in L.route_data():
            if edge['kind']=='bridge':continue
            radius=1.9 if edge['kind']=='main' else 1.3 if edge['kind']=='stone' else .8
            for px,py,_ in edge['points']:
                ROAD_BUCKETS.setdefault((math.floor(px/8),math.floor(py/8)),[]).append((px,py,radius))
    bx,by=math.floor(x/8),math.floor(y/8);distance=99
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for px,py,radius in ROAD_BUCKETS.get((bx+dx,by+dy),[]):
                distance=min(distance,math.hypot(x-px,y-py)-radius)
    t=max(0,min(1,(distance-.8)/2))
    return .55*(1-t*t*(3-2*t))

def terrain(side):
    cx=-49 if side=='west' else 49;sectors=192;rings=45
    vertices=[(cx,0,L.height(cx,0)-road_subgrade(cx,0))]
    for ring in range(1,rings+1):
        t=ring/rings
        for i in range(sectors):
            a=math.tau*i/sectors;r=boundary(side,a)*t;x=cx+r*math.cos(a);y=r*math.sin(a)
            vertices.append((x,y,L.height(x,y)-road_subgrade(x,y)))
    faces=[(0,1+i,1+(i+1)%sectors) for i in range(sectors)]
    for ring in range(rings-1):
        a=1+ring*sectors;b=a+sectors
        faces += [(a+i,b+i,b+(i+1)%sectors,a+(i+1)%sectors) for i in range(sectors)]
    mesh=bpy.data.meshes.new(side+' continuous height terrain');mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(side+' Island Terrain',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(M['grass'])
    for key in ('meadow','grass_light'):obj.data.materials.append(M[key])
    # Broad mottled meadow patches follow the land; no added texture payload.
    for p in obj.data.polygons:
        centre=sum((obj.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
        variation=math.sin(centre.x*.17)+math.cos(centre.y*.14)+.5*math.sin((centre.x+centre.y)*.22)
        p.material_index=1 if variation>1.1 else 2 if variation<-.9 else 0
    for p in obj.data.polygons:p.use_smooth=True
    rim=vertices[-sectors:];v=[]
    # Four uneven coastal strata expose meaningful vertical depth at 40 degrees.
    for level in range(4):
        for i,(x,y,z) in enumerate(rim):
            dx,dy=x-cx,y;length=math.hypot(dx,dy)
            offset=(0,.6,1.3,.5)[level]*(1+.3*math.sin(i*.27))
            h=(z-.18,z*.64-.8,z*.22-1.1,-1.8)[level]
            v.append((x+dx/length*offset,y+dy/length*offset,h))
    faces=[(j*sectors+i,j*sectors+(i+1)%sectors,(j+1)*sectors+(i+1)%sectors,(j+1)*sectors+i) for j in range(3) for i in range(sectors)]
    mesh=bpy.data.meshes.new(side+' rocky coast');mesh.from_pydata(v,[],faces)
    coast=bpy.data.objects.new(side+' Cliff',mesh);bpy.context.collection.objects.link(coast)
    for key in ('cliff','cliff_light','cliff_dark'):coast.data.materials.append(M[key])
    for p in mesh.polygons:p.material_index=(p.index//sectors+p.index//11)%3
    # Shallow coastal band, rather than a rectangular water tray.
    for name,inner,outer,z,mat in [('Lagoon',.2,7,-.11,M['lagoon']),('Foam',.2,1,-.07,M['foam'])]:
        verts=[]
        for delta in (inner,outer):
            for i in range(sectors):
                a=math.tau*i/sectors;r=boundary(side,a)+delta;verts.append((cx+r*math.cos(a),r*math.sin(a),z))
        me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[(i,(i+1)%sectors,sectors+(i+1)%sectors,sectors+i) for i in range(sectors)])
        o=bpy.data.objects.new(side+' '+name,me);bpy.context.collection.objects.link(o);o.data.materials.append(mat)


def validate_surface_clearance():
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get()
    trees={side:BVHTree.FromObject(bpy.data.objects[side+' Island Terrain'],depsgraph) for side in ('west','east')}
    checked=0;minimum=99
    for obj in bpy.data.objects:
        if not obj.name.startswith('Path WalkSurface'):continue
        obj.data.calc_loop_triangles();half=len(obj.data.vertices)//2
        for triangle in obj.data.loop_triangles:
            if any(v>=half for v in triangle.vertices):continue
            centre=sum((obj.data.vertices[v].co for v in triangle.vertices),Vector((0,0,0)))/3
            hit,_,_,_=trees['west' if centre.x<0 else 'east'].ray_cast(Vector((centre.x,centre.y,100)),Vector((0,0,-1)))
            if hit is not None:
                gap=centre.z-hit.z;minimum=min(minimum,gap);checked+=1
                assert gap>.025,('Terrain intersects promenade',obj.name,tuple(centre),gap)
    print('SURFACE_CLEARANCE_OK',checked,'triangles; minimum clearance',minimum)

def build_site(site):
    ident,name,side,model,(x,y),(w,d),kind=site;z=L.height(x,y)
    root=empty('Site_'+ident,(x,y,z));before=set(bpy.data.objects)
    if model not in ('tube','dock'):
        cube(name+' foundation terrace',(x,y,z+.28),(w+.7,d+.7,.65),M['cliff_light'],.22)
        obj,h=asset(model,(x,y,z+.65),(w,d))
        prominence=.90 if ident=='archive' else 1.30 if ident in ('settlements','operations','trader') else 1.12
        obj.scale.z*=prominence;h=h*prominence+.65
        # Kit-derived rear pavilion, contained by the reserved collision footprint.
        if ident in ('settlements','operations','trader'):
            wing,wh=asset('tower_B' if ident=='settlements' else 'home_B',(x-w*.27,y+d*.18,z+.65),(w*.28,d*.40))
            wing.scale.z*=1.35
        for step in range(3):
            cube(name+' entrance step',(x,y-d/2-.45-step*.43,z+.12+(2-step)*.16),(w*.42,.65,.24+(2-step)*.32),M['stone'],.08)
        cylinder(name+' WalkSurface forecourt',(x,y-d/2-1,z+.08),max(w*.4,3),.16,M['stone'],48)
        # Distinct departmental additions complement the imported architecture.
        if ident=='archive':
            cylinder('Archive bronze drum',(x,y,z+h*.78),w*.34,.7,M['bronze'],48)
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=12,location=(x,y,z+h*.94))
            dome=bpy.context.object;dome.name='Archive bespoke dome';dome.scale=(w*.35,w*.35,h*.24);dome.data.materials.append(M['teal'])
        if ident in ('finance','lc','vat'):
            cube(name+' ledger cornice',(x,y-d*.3,z+h*.60),(w*.8,1,.4),M['bronze'],.12)
        if ident=='coffee':
            cylinder('Coffee ceramic cup',(x,y,z+h+.6),.55,1,M['ivory'],32)
            torus('Coffee cup handle',(x+.7,y,z+h+.6),.35,.09,M['bronze']).rotation_euler.x=math.pi/2
            for dx in (-2.5,2.5):
                cube('Coffee bench',(x+dx,y-4,z+.8),(2.1,.7,.3),M['wood'],.12)
        if ident in ('settlements','operations','trader'):
            cube(name+' civic portico',(x,y-d/2-.5,z+4.0),(w*.55,2,.4),M['bronze'],.15)
            for dx in (-w*.22,w*.22):cylinder('Ivory civic pier',(x+dx,y-d/2-1,z+2),.30,4,M['ivory'],20)
    elif model=='tube':
        h=13
        cylinder(name+' platform',(x,y,z+.2),4.2,.4,M['stone'],48)
        cylinder(name+' ivory core',(x,y,z+6.3),1.65,12.2,M['ivory'],48)
        for level in (1,5.5,11.5):torus(name+' bronze pressure ring',(x,y,z+level),1.8,.22,M['bronze'])
        cylinder(name+' teal cap',(x,y,z+12.6),2.0,.7,M['teal'],48)
        direction=1 if side=='west' else -1
        cube(name+' inward nozzle',(x+direction*2,y,z+11),(3,1.3,1.2),M['bronze'],.4)
        for dx in (-.9,.9):cylinder(name+' pressure pipe',(x+dx,y-.9,z+6.3),.22,11,M['teal'],24)
    else:
        h=3
        cube(name+' WalkSurface',(x,y,z-.08),(14,9,.45),M['wood'],.2)
        direction=1 if side=='west' else -1
        for step in range(6):
            height=max(.5,z-(step+1)*.35)
            cube('Harbor waterside stair',(x+direction*(step+.5),y-4.9,height/2),(1.15,1.5,height),M['cliff_light'],.08)
        for dy in (-3.6,3.6):
            for dx in (-5,5):cylinder('Harbor bollard',(x+dx,y+dy,z+.6),.22,1.5,M['bronze'],16)
        cube(name+' launch sign',(x,y+3.8,z+1.8),(2.5,.3,2),M['teal'],.15)
    for obj in set(bpy.data.objects)-before:parent_keep(obj,root)
    root['stable_id']=ident;root['island']=side
    return dict(id=ident,name=name,island=side,kind=kind,position=[x,z,-y],
        footprint=[w,d],height=round(h,3),entrance=godot(L.NODES[ident]),node=ident)


def godot(point):x,y,z=point;return [round(x,4),round(z,4),round(-y,4)]


def ferry():
    root=empty('Central Ferry',(-9,0,.2));before=set(bpy.data.objects)
    x=-9
    cube('Ferry hull',(x,0,.7),(9,4,1.3),M['ivory'],.65)
    cube('Ferry teal cabin',(x-1,0,2.1),(3.6,3,1.8),M['teal'],.4)
    cube('Ferry bronze roof',(x-1,0,3.15),(4.1,3.5,.3),M['bronze'],.2)
    for o in set(bpy.data.objects)-before:parent_keep(o,root)
    for i,(x,y,a) in enumerate([(-80,53,.5),(85,-42,-.4),(85,44,1.1)]):
        boat=empty('Decorative boat '+str(i),(x,y,0));before=set(bpy.data.objects)
        cube('Coastal hull',(x,y,.5),(5,2,1),M['wood'],.65)
        cube('Coastal cabin',(x-.7,y,1.3),(1.9,1.5,.9),M['ivory'],.2)
        for o in set(bpy.data.objects)-before:parent_keep(o,boat)
        boat.rotation_euler.z=a


def report(sites,edges):
    pairs=[]
    for a,b in [('dock_w','dock_e'),('w_hub','e_hub'),('settlements','trader'),('tube_w','tube_e')]:
        pairs.append(dict(origin=a,destination=b,**{m:L.shortest(a,b,m) for m in ('walk','boat','tube')}))
    data=dict(version=2,pilot_scale=L.PILOT_SCALE,pilot_walk_units_per_minute=1.5,
        walk_units_per_story_minute=L.WALK_UNITS_PER_MINUTE,real_seconds_per_story_minute=L.REAL_SECONDS_PER_STORY_MINUTE,
        boat_story_minutes=5,tube_story_minutes=3,boat_wait_minutes=0,
        landmarks=sites,nodes={key:godot(value) for key,value in L.NODES.items()},
        edges=[dict(a=e['a'],b=e['b'],kind=e['kind'],points=[godot(p) for p in e['points']]) for e in edges],
        examples=pairs,asset_models=sorted(USED),temporary_character='KayKit Rogue Hooded: imported rig, Idle / Walking_A; not approved Cooper likeness')
    (ASSETS/'world_v2.json').write_text(json.dumps(data,indent=2)+'\n');(OUT/'overworld_layout.json').write_text(json.dumps(data,indent=2)+'\n')


def reviews():
    out=ROOT/'docs/v2-1';out.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=False
    scene.render.resolution_x=1440;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    for elevation in (30,38,40,45,55):
        angle=math.radians(elevation);cam=scene.camera;cam.location=(0,-180*math.cos(angle),180*math.sin(angle))
        cam.rotation_euler=(Vector((0,0,5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=200
        scene.render.filepath=str(out/f'world-{elevation}.png');bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True,exist_ok=True);ASSETS.mkdir(parents=True,exist_ok=True)
    courier()
    for name,color in dict(grass=(.19,.29,.13),meadow=(.21,.31,.14),grass_light=(.23,.33,.16),cliff=(.34,.33,.26),cliff_light=(.42,.39,.30),cliff_dark=(.28,.30,.25),water=(.025,.10,.12),lagoon=(.06,.23,.23),foam=(.30,.47,.41),
        stone=(.50,.46,.36),ivory=(.62,.57,.46),teal=(.12,.29,.32),bronze=(.58,.40,.21),wood=(.37,.27,.18),dirt=(.52,.43,.29)).items():M[name]=material('Telanico '+name,color)
    M['atlas']=atlas_material()
    cylinder('Open teal water',(0,0,-.35),230,.4,M['water'],160)
    terrain('west');terrain('east');edges=L.route_data()
    for i,e in enumerate(edges):
        kind=e['kind'];width=5 if kind=='bridge' else 3.8 if kind=='main' else 2.6 if kind=='stone' else 1.6
        pts=[(x,y,z+i*.0005) for x,y,z in e['points']]
        road=ribbon(('Bridge WalkSurface' if kind=='bridge' else 'Path WalkSurface')+str(i),pts,width,M['dirt'] if kind=='trail' else M['stone'],.70)
        if kind!='bridge':
            for vertex in road.data.vertices:
                old=vertex.co.z
                # Conform both edges to terrain; flat cross-sections create
                # tall side walls where sloping promenades meet.
                vertex.co.z=L.height(vertex.co.x,vertex.co.y)+.265-(.70 if vertex.index>=len(road.data.vertices)//2 else 0)
        if kind=='bridge':
            # Deep curved spandrels reveal the opening instead of a thin strip.
            for side in (-1,1):
                ribbon('Bridge arch spandrel',[(x,y+side*2.35,z-.25) for x,y,z in pts],.65,M['cliff_light'],1.55)
            for px in (-19,19):
                pz=L.height(px,43)
                cube('Bridge abutment',(px,43,pz/2),(3.0,6.3,pz+1.1),M['cliff'],.25)
            for side in (-1,1):ribbon('Bridge stone parapet',[(x,y+side*2.7,z+.8) for x,y,z in pts],.35,M['cliff'],.8)
    validate_surface_clearance()
    sites=[build_site(site) for site in L.SITES]
    rng=random.Random(19)
    for i in range(24):
        for _ in range(200):
            side='west' if i<12 else 'east';x=rng.uniform(-82,-18) if side=='west' else rng.uniform(18,82);y=rng.uniform(-48,48)
            if not L.inside(x,y,side):continue
            if any(abs(x-cx)<w/2+7 and abs(y-cy)<d/2+7 for _,_,_,_,(cx,cy),(w,d),_ in L.SITES):continue
            if any(math.dist((x,y),p[:2])<6 for e in edges for p in e['points']):continue
            break
        asset('tree_single_A' if i%2 else 'tree_single_B',(x,y,L.height(x,y)),(rng.uniform(3,5),rng.uniform(3,5)),'nature')
    for i,(x,y) in enumerate([(-79,22),(-80,27),(-76,30),(-78,-40),(-75,-46),(80,32),(82,27),(78,46),(77,-41),(73,-47)]):
        asset('rock_single_B' if i%2 else 'rock_single_C',(x,y,L.height(x,y)-1),(3.5,4),'nature')
    ferry();report(sites,edges)
    bpy.ops.object.camera_add(location=(0,-200*math.cos(math.radians(40)),5+200*math.sin(math.radians(40))));cam=bpy.context.object;cam.name='V2.1 40 degrees ABOVE HORIZONTAL';cam.rotation_euler=(Vector((0,0,5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=200;bpy.context.scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-60,-80,130));light=bpy.context.object;light.data.energy=180000;light.data.size=95
    world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.72,.75,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'overworld.blend'))
    bpy.ops.export_scene.gltf(filepath=str(ASSETS/'overworld.glb'),export_format='GLB',export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
    print('V2_WORLD_OK imported assets',len(USED),'landmarks',len(sites))
    if '--render' in sys.argv:reviews()

if __name__=='__main__':main()
