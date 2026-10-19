"""Generate the first Telanico two-island overworld, without external assets.

blender --background --python-exit-code 1 --python blender/scripts/build_overworld.py
Append -- --render to produce the committed review images with CPU Cycles.
"""
from pathlib import Path
import sys
import math
import json
import heapq

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_smoke_test import material, cube, cylinder, sphere
from overworld_layout import LANDMARKS, ISLANDS, NODES, ROUTES, WALK_MINUTES_PER_UNIT

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'blender/generated'
GLB = ROOT / 'godot/assets/generated/overworld.glb'
M = {}


def empty(name, location=(0,0,0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj


def parent_keep(obj, parent):
    bpy.context.view_layer.update()
    matrix = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = matrix


def prism(name, outline, bottom, top, mat, bevel=0.25):
    n = len(outline)
    vertices = [(x,y,bottom) for x,y in outline] + [(x,y,top) for x,y in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('Soft coastline','BEVEL')
        mod.width, mod.segments = bevel, 3
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.modifiers.new('Weighted coast normals','WEIGHTED_NORMAL')
    return obj


def ribbon(name, points, width, mat, thickness=0.08):
    # A continuous mitered strip: no disconnected road tiles at the bends.
    sides = []
    for i, p in enumerate(points):
        prev = Vector(points[max(i-1,0)][:2])
        nxt = Vector(points[min(i+1,len(points)-1)][:2])
        direction = (nxt-prev).normalized()
        normal = Vector((-direction.y,direction.x)) * width/2
        sides += [(p[0]+normal.x,p[1]+normal.y,p[2]+0.025),
                  (p[0]-normal.x,p[1]-normal.y,p[2]+0.025)]
    verts = sides + [(x,y,z-thickness) for x,y,z in sides]
    count = len(sides)
    faces = []
    for i in range(len(points)-1):
        a = i*2
        faces += [(a,a+1,a+3,a+2), (count+a+2,count+a+3,count+a+1,count+a),
                  (a,a+2,count+a+2,count+a),(a+3,a+1,count+a+1,count+a+3)]
    faces += [(1,0,count,count+1),(count-2,count-1,2*count-1,2*count-2)]
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def torus(name, pos, radius, thickness, mat):
    bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=8,
        location=pos,major_radius=radius,minor_radius=thickness)
    obj=bpy.context.object
    obj.name=name
    obj.data.materials.append(mat)
    for face in obj.data.polygons: face.use_smooth=True
    return obj


def cone(name, pos, radius, height, mat, top=0.25, vertices=48):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=radius,radius2=top,
        depth=height,location=pos)
    obj=bpy.context.object
    obj.name=name
    obj.data.materials.append(mat)
    return obj


def make_building(name, kind, x, y, z, side):
    root=empty(name,(x,y,z))
    before=set(bpy.data.objects)
    ivory, roof, bronze = M['ivory'], M['teal'], M['bronze']
    def block(part, dx,dy,dz, sx,sy,sz, mat=ivory, radius=.15):
        return cube(name+' '+part,(x+dx,y+dy,z+dz),(sx,sy,sz),mat,radius)
    if kind not in ('tube','dock'):
        block('foundation',0,0,.10,7.2 if kind in ('hall','operations') else 5.7,
              5.5 if kind in ('hall','operations') else 4.9,.20,M['stone'])
    if kind=='hall':
        block('body',0,0,1.85,6.4,4.6,3.5)
        block('roof',0,0,3.72,7.0,5.1,.38,roof,.18)
        block('upper pavilion',0,.2,4.5,2.9,2.7,1.25)
        block('pavilion crown',0,.2,5.20,3.3,3.1,.25,roof)
        block('portico',0,-2.8,2.25,3.4,1.3,.28,bronze)
        for dx in (-1.2,1.2): block('portico pier',dx,-3.1,1.16,.32,.32,2.10)
        block('entrance',0,-2.34,1.25,1.10,.13,2.2,M['glass'])
        for dx in (-2.25,2.25): block('window',dx,-2.34,1.85,.9,.12,1.35,M['glass'])
    elif kind=='operations':
        block('body',0,0,1.9,7.0,4.8,3.6)
        block('lower roof',-.85,0,3.85,5.6,5.25,.32,roof)
        block('dispatch lantern',2.0,.3,3.3,1.9,3.9,5.0)
        block('lantern crown',2.0,.3,5.93,2.25,4.25,.25,roof)
        block('dispatch slit',2.0,-1.70,4.25,.65,.12,2.1,M['glass'])
        block('front glazing',-1,-2.44,1.9,3.6,.12,1.25,M['glass'])
        block('canopy',-1,-2.85,2.4,3.8,1.0,.22,bronze)
    elif kind=='trade':
        block('body',0,.35,1.55,4.8,3.4,2.9)
        block('exchange wing',-1.1,-1.35,1.05,2.3,1.7,1.9)
        block('main roof',0,.35,3.1,5.2,3.8,.3,roof)
        block('wing roof',-1.1,-1.35,2.1,2.6,2.0,.22,bronze)
        block('ledger window',1.05,-1.4,1.7,1.25,.12,1.2,M['glass'])
    elif kind=='compliance':
        block('body',0,0,1.8,3.5,3.3,3.4)
        block('restrained crown',0,0,3.6,4.0,3.8,.35,M['sage'])
        block('central portal',0,-1.7,1.55,.9,.12,2.6,M['glass'])
        for dx in (-1.15,1.15): block('control fin',dx,-1.82,1.85,.20,.24,3.2,bronze)
    elif kind=='lc':
        block('body',0,0,1.25,5.1,3.2,2.3)
        block('long roof',0,0,2.55,5.5,3.7,.3,M['blue'])
        block('desk clerestory',0,0,2.95,3.4,1.3,.65)
        block('top ribbon',0,0,3.33,3.7,1.55,.18,bronze)
        block('document window',0,-1.65,1.35,3.0,.12,.9,M['glass'])
    elif kind=='contracts':
        block('body',0,0,1.5,4.6,4.2,2.8)
        for dx,angle in ((-1.3,-.18),(1.3,.18)):
            piece=block('open folio roof',dx,0,3.05,2.8,4.6,.28,M['clay'])
            piece.rotation_euler.y=angle
        block('folio spine',0,0,3.30,.20,4.6,.25,bronze)
        block('entrance',0,-2.15,1.35,1.2,.12,2.2,M['glass'])
    elif kind=='tax':
        block('body',0,0,1.4,4.7,3.8,2.6)
        block('upper ledger',.5,.3,3.05,3.1,2.8,.9)
        block('lower cornice',0,0,2.8,5.1,4.2,.25,M['ochre'])
        block('upper cornice',.5,.3,3.6,3.5,3.2,.25,M['ochre'])
        block('entrance',0,-1.95,1.3,1.2,.12,2.1,M['glass'])
    elif kind=='fx':
        cylinder(name+' body',(x,y,z+1.5),2.0,2.8,ivory,32)
        cylinder(name+' roof',(x,y,z+3.05),2.35,.3,M['plum'],48)
        for dx in (-.5,.5): block('exchange fin',dx,0,3.8,.28,2.8,1.4,bronze)
        block('entrance',0,-2.0,1.35,.9,.15,2.1,M['glass'])
    elif kind=='archive':
        cylinder(name+' body',(x,y,z+1.7),2.8,3.2,ivory,64)
        torus(name+' archive belt',(x,y,z+2.9),2.8,.12,bronze)
        cone(name+' radial roof',(x,y,z+3.65),3.25,.85,roof,.65,64)
        cylinder(name+' oculus',(x,y,z+4.15),.68,.22,bronze,32)
        for i in range(8):
            angle=i*math.tau/8
            pier=block('archive rib',2.8*math.cos(angle),2.8*math.sin(angle),1.6,.25,.30,2.8)
            pier.rotation_euler.z=angle
        block('entry portal',0,-2.85,1.4,1.1,.18,2.35,M['glass'])
    elif kind=='coffee':
        block('kiosk',0,.5,.95,2.8,1.8,1.7)
        block('serving window',0,-.43,1.1,2.0,.12,.65,M['glass'])
        block('counter',0,-.7,.85,3.2,.65,.18,bronze)
        block('rounded canopy',0,.1,1.95,3.7,2.8,.28,M['clay'])
        cylinder(name+' cup sign',(x,y+.1,z+2.55),.38,.9,M['ivory'],32)
        cylinder(name+' coffee surface',(x,y+.1,z+3.01),.31,.03,M['wood'],32)
        handle=torus(name+' cup handle',(x+.48,y+.1,z+2.6),.23,.07,ivory)
        handle.rotation_euler.x=math.pi/2
        block('bench seat',0,-1.55,.6,2.4,.6,.18,M['clay'])
        for dx in (-.85,.85): block('bench foot',dx,-1.55,.3,.25,.5,.45,M['wood'])
    elif kind=='tube':
        cylinder(name+' octagonal platform',(x,y,z+.15),2.6,.3,M['stone'],32)
        cylinder(name+' body',(x,y,z+2.8),1.05,5.3,ivory,48)
        for h in (.65,4.8):
            cylinder(name+' teal collar',(x,y,z+h),1.2,.32,roof,48)
        cylinder(name+' dark throat',(x,y,z+5.5),.72,.3,M['glass'],48)
        torus(name+' mouth rim',(x,y,z+5.7),.89,.2,bronze)
        direction=1 if side=='west' else -1
        block('pneumatic spine',-direction*.88,0,2.9,.22,.45,4.8,bronze)
        block('inward signal',direction*1.25,0,4.6,1.5,.7,.5,roof,.20)
    elif kind=='dock':
        block('landing',0,0,-.05,4.6,3.5,.32,M['wood'])
        block('pale quay',0,1.45,.12,4.6,.35,.22,M['stone'])
        direction=1 if side=='west' else -1
        for dx in (-1.6,1.6):
            cylinder(name+' mooring post',(x+dx,y-1.25,z+.35),.15,.8,bronze,16)
        block('launch marker',-direction*1.65,1.15,.8,.5,.5,1.35,roof)
    for obj in set(bpy.data.objects)-before:
        parent_keep(obj,root)
    label=empty(name+' label anchor',(x,y,z+(6.1 if kind=='tube' else 6 if kind in ('hall','operations') else 2 if kind=='dock' else 4.6)))
    parent_keep(label,root)
    root['island']=side
    root['department']=name
    return root


def boat(name,x,y,angle=0,scale=1):
    root=empty(name,(x,y,.3))
    before=set(bpy.data.objects)
    points=[(-1.8,-.65),(1.1,-.65),(1.8,0),(1.1,.65),(-1.8,.65)]
    prism(name+' hull',[(x+a*scale,y+b*scale) for a,b in points],.10,.52,M['ivory'],.12)
    cube(name+' cabin',(x-.25*scale,y,.86),(1.3*scale,1.0*scale,.7),M['teal'],.13)
    cube(name+' roof',(x-.25*scale,y,1.27),(1.6*scale,1.25*scale,.16),M['stone'],.08)
    for obj in set(bpy.data.objects)-before: parent_keep(obj,root)
    root.rotation_euler.z=angle
    return root


def terrain():
    cube('Tabletop sea tray',(0,0,-1.1),(78,57,1.6),M['tray'],1.3)
    cube('Central channel water',(0,0,-.18),(76,55,.45),M['water'],1.1)
    for name,points in ISLANDS.items():
        prism(name+' Island coast',points,-.2,1.32,M['cliff'],.45)
        cx=-19 if name=='West' else 19
        inset=[(cx+(x-cx)*.98,y*.98) for x,y in points]
        prism(name+' Island grass',inset,1.20,1.43,M['grass'],.24)
    # Broad terraces, two low hills, and a short retaining edge; no mountains.
    cube('West LC raised terrace',(-25,15,1.70),(8,7,.9),M['cliff'],.8)
    cube('West LC terrace lawn',(-25,15,2.20),(7.8,6.8,.10),M['sage'],.5)
    cylinder('East archive terrace',(28,16,1.7),5.0,.9,M['cliff'],64)
    cylinder('East archive lawn',(28,16,2.20),4.8,.10,M['sage'],64)
    cylinder('FX detached terrace',(21,-17,1.60),4.3,.9,M['cliff'],64)
    cylinder('FX terrace lawn',(21,-17,2.10),4.05,.10,M['grass'],64)
    for i,(x,y,sx,sy,h) in enumerate([(-30,6,3,5,1.5),(31,6,2.8,4.5,1.5)]):
        sphere('Gentle hill '+str(i),(x,y,1.2),(sx,sy,h),M['sage'])
    # Three broad steps on the hall's outer terrace are decorative, not the main ramp.
    for i in range(3):
        cube('LC garden step '+str(i),(-29.2,9.5+i*.7,1.5+i*.22),
             (2.0,.8,.22),M['stone'],.07)


def landscaping():
    # Sparse clusters leave the walking courtyards and silhouettes open.
    for i,(x,y,h) in enumerate([(-30,-15,2.5),(-30,-11,2.8),(-31,1,3),
        (-20,20,2.7),(-16,19,2.4),(-8,-14,2.4),(8,-16,2.7),
        (30,-12,2.7),(31,-9,2.5),(32,2,2.4),(20,20,2.8),(23,21,2.4)]):
        cylinder('Tree trunk '+str(i),(x,y,2.0),.21,1.3,M['wood'],12)
        sphere('Tree crown '+str(i),(x,y,2.5+h*.35),(1.0,1.0,h*.65),M['leaves'])
    for i,(x,y) in enumerate([(-34,-7),(-31,18),(34,-4),(31,21)]):
        sphere('Coastal boulder '+str(i),(x,y,.6),(1.15,.8,.95),M['cliff'])
    boat('Harbor Launch central ferry',0,-.5,0,1.05)
    for i,(x,y,a) in enumerate([(-32,-23,-.3),(34,-20,.7),(35,17,1.2)]):
        boat('Decorative coastal boat '+str(i),x,y,a,.62)
    for i in range(3):
        ribbon('Central ferry wake '+str(i),[(-3+i*.8,-1.8-i*.25,.06),
            (-.7+i*.8,-1.8-i*.25,.06)],.08,M['foam'],.01)
    # Quiet lengthwise strokes make the central river-like passage legible.
    for i,(x,y) in enumerate([(-1,19),(1,6),(-1,-9),(1,-19)]):
        ribbon('Channel current '+str(i),[(x,y-2,.06),(x+.3,y,.06),(x,y+2,.06)],.10,M['foam'],.01)


def routes():
    for order,(name,start,end,kind,via) in enumerate(ROUTES):
        pts=[(x,y,z+order*.001) for x,y,z in [NODES[start],*via,NODES[end]]]
        width={'primary':2.4,'secondary':1.4,'trail':.85,'bridge':2.4}[kind]
        mat=M['dirt'] if kind=='trail' else M['stone']
        if kind != 'bridge' and any(p[2] > 1.5 for p in pts):
            ribbon(name+' ramp support',[(x,y,z-.08) for x,y,z in pts],width+.16,M['cliff'],.82)
        road=ribbon(name,pts,width,mat,.12 if kind=='bridge' else .08)
        road['route_hierarchy']=kind
        if kind=='bridge':
            root=empty('Pedestrian Bridge')
            parent_keep(road,root)
            for side in (-1,1):
                rail=ribbon('Bridge parapet '+str(side),[(x,y+side*1.28,z+.55) for x,y,z in pts],.22,M['cliff'],.55)
                parent_keep(rail,root)
                cap=ribbon('Bridge bronze cap '+str(side),[(x,y+side*1.28,z+.58) for x,y,z in pts],.28,M['bronze'],.06)
                parent_keep(cap,root)


def manifest():
    graph={node:[] for node in NODES}
    route_data=[]
    for name,a,b,kind,via in ROUTES:
        pts=[NODES[a],*via,NODES[b]]
        length=sum((Vector(q)-Vector(p)).length for p,q in zip(pts,pts[1:]))
        minutes=length*WALK_MINUTES_PER_UNIT
        graph[a].append((b,minutes)); graph[b].append((a,minutes))
        route_data.append(dict(name=name,start=a,end=b,hierarchy=kind,
            points=pts,length=round(length,2),walk_minutes=round(minutes,2)))
    def shortest(a,b):
        todo=[(0,a)]; seen=set()
        while todo:
            cost,node=heapq.heappop(todo)
            if node==b: return round(cost,1)
            if node in seen: continue
            seen.add(node)
            for other,value in graph[node]: heapq.heappush(todo,(cost+value,other))
    data=dict(landmarks={name:dict(island=s,kind=k,position=[x,y,z])
        for name,(s,k,x,y,z) in LANDMARKS.items()}, routes=route_data,
        nodes=NODES,minutes_per_world_unit=WALK_MINUTES_PER_UNIT,
        transfer_estimates=dict(boat_dock_to_dock_minutes=7,tube_station_to_station_minutes=2),
        representative_walk_minutes={
            'Hall to Compliance':shortest('hall','compliance'),
            'Hall to LC Desk':shortest('hall','lc'),
            'LC Desk to Trade Finance':shortest('lc','trade'),
            'Operations to VAT Tax':shortest('operations','tax'),
            'Archive to FX Desk':shortest('archive','fx'),
            'Civic hub to civic hub via bridge':shortest('west_hub','east_hub')})
    (OUT/'overworld_layout.json').write_text(json.dumps(data,indent=2)+'\n')
    return data


def camera(name, position, target, size):
    bpy.ops.object.camera_add(location=position)
    obj=bpy.context.object
    obj.name=name
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    obj.data.type='ORTHO';obj.data.ortho_scale=size
    return obj


def render_reviews():
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=24;scene.cycles.use_denoising=False
    scene.render.image_settings.file_format='PNG'
    out=ROOT/'docs/overworld';out.mkdir(parents=True,exist_ok=True)
    for name,pos,size,target in [('overview',(38,-74,85),100,(0,0,1)),
        ('top-down',(0,0,100),90,(0,0,0))]:
        cam=camera('Review '+name,pos,target,size)
        scene.camera=cam
        scene.render.resolution_x=1600;scene.render.resolution_y=1100
        scene.render.resolution_percentage=100
        scene.render.filepath=str(out/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam,do_unlink=True)


def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for name,color in dict(ivory=(.76,.72,.60),teal=(.16,.32,.34),bronze=(.58,.43,.23),
        stone=(.73,.69,.56),cliff=(.46,.46,.38),grass=(.43,.53,.38),sage=(.37,.47,.34),
        water=(.17,.39,.43),tray=(.17,.24,.25),leaves=(.25,.39,.30),wood=(.34,.25,.18),
        clay=(.60,.35,.27),ochre=(.63,.48,.25),blue=(.31,.44,.49),plum=(.38,.30,.37),
        glass=(.12,.23,.26),dirt=(.59,.50,.35),foam=(.44,.62,.60)).items():
        M[name]=material('Telanico '+name,color)
    terrain();routes()
    for name,(side,kind,x,y,z) in LANDMARKS.items():
        make_building(name,kind,x,y,z,side)
    landscaping()
    cam=camera('Overworld editable camera',(52,-70,75),(0,0,1),87)
    bpy.context.scene.camera=cam
    bpy.ops.object.light_add(type='AREA',location=(-20,-30,60))
    key=bpy.context.object;key.name='Soft studio key';key.data.energy=45000
    key.data.shape='DISK';key.data.size=45
    bpy.context.scene.world.use_nodes=True
    background=bpy.context.scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value=(.72,.74,.70,1)
    background.inputs['Strength'].default_value=.4
    OUT.mkdir(parents=True,exist_ok=True);GLB.parent.mkdir(parents=True,exist_ok=True)
    report=manifest()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'overworld.blend'))
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',
        export_cameras=False,export_lights=False,export_extras=True,export_apply=True)
    print('OVERWORLD_OK',json.dumps(report['representative_walk_minutes']))
    print('OVERWORLD_OUTPUT',OUT/'overworld.blend',GLB)
    if '--render' in sys.argv: render_reviews()


if __name__=='__main__': main()
