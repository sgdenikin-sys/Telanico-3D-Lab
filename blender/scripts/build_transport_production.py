"""Standalone original VorGun transport models; never writes game/runtime assets.

blender -b -t 8 --python-exit-code 1 --python blender/scripts/build_transport_production.py -- --asset pneumatic_station
Repeat explicitly for commuter_ferry and harbor_launch after committing each asset.
UV0 is an isometric per-face unwrap: semantic groups are packed together, with
one physical texel density, unique rectangles and >= 4 px island clearance.
Native Blender UV export and guide share the exact saved UV0 coordinates.
"""
import argparse
import collections
import json
import math
from pathlib import Path
import subprocess
import sys
import shutil

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import build_settlements_hall as H

P = argparse.ArgumentParser()
P.add_argument('--asset', required=True, choices=['pneumatic_station', 'commuter_ferry', 'harbor_launch'])
A = P.parse_args(sys.argv[sys.argv.index('--') + 1:])
OUT = ROOT / 'artifacts/transport_production/v1' / A.asset
OUT.mkdir(parents=True, exist_ok=True)
TAU = math.tau
OBJECTS = []
M = {}
ROOF = None


def material(name, color, metallic=0, rough=.6, alpha=1):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, alpha)
    m.use_nodes = True
    s = m.node_tree.nodes.get('Principled BSDF')
    s.inputs['Base Color'].default_value = (*color, alpha)
    s.inputs['Metallic'].default_value = metallic
    s.inputs['Roughness'].default_value = rough
    s.inputs['Alpha'].default_value = alpha
    if alpha < 1:
        m.surface_render_method = 'DITHERED'
        m.use_backface_culling = False
    return m


def record(o, group, mat):
    o['uv_region'] = group
    o['surface_id'] = f'{len(OBJECTS) + 1:03d}'
    o.data.materials.clear()
    o.data.materials.append(M[mat])
    if group == 'ROOF':
        for c in list(o.users_collection): c.objects.unlink(o)
        ROOF.objects.link(o)
        o['removable_roof'] = True
    OBJECTS.append(o)
    return o


def mesh(name, verts, faces, mat='ivory', group='FRONT', smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = smooth
    return record(o, group, mat)


def box(name, pos, dims, mat='ivory', group='FRONT', bevel=.025):
    o = H.block(name, pos, dims, M[mat], bevel)
    # H owns its own scratch collection; retain the final mesh in this asset.
    return record(o, group, mat)


def rod(name, pts, r=.04, mat='brass', group='FRONT', sides=8):
    o = H.tube(name, pts, r, M[mat], sides)
    return record(o, group, mat)


def ring(name, r, inner, low, high, mat='ivory', group='FRONT', n=48):
    v = [(rr*math.cos(TAU*i/n), rr*math.sin(TAU*i/n), z)
         for rr,z in [(r,low),(r,high),(inner,high),(inner,low)] for i in range(n)]
    f = []
    for j in range(4):
        for i in range(n):
            k=(i+1)%n; nj=(j+1)%4
            f.append((j*n+i,j*n+k,nj*n+k,nj*n+i))
    return mesh(name,v,f,mat,group,True)


def disk(name,r,low,high,mat,group,n=48):
    v=[(r*math.cos(TAU*i/n),r*math.sin(TAU*i/n),z) for z in (low,high) for i in range(n)]
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,v,f,mat,group)


def sector(name, a, b, r, thickness, low, high, mat, group):
    v=[(rr*math.cos(t),rr*math.sin(t),z) for z in (low,high)
       for rr in (r,r-thickness) for t in (a,b)]
    return mesh(name,v,[(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5),(4,5,7,6),(0,2,3,1)],mat,group)


def pane(name, pts, variant=0, group='WINDOWS'):
    return mesh(name,pts,[tuple(range(len(pts)))],f'glass{variant%3}',group)


def door(name, hinge, width, height, angle=0, side=1, glass=True):
    """Independent actual hinge origin, no solid wall behind the door leaf."""
    pivot=bpy.data.objects.new(name+'_HINGE',None)
    bpy.context.scene.collection.objects.link(pivot)
    pivot.location=hinge; pivot.rotation_euler.z=angle
    pivot['hinge_axis']='local Z'; pivot['opening_degrees']=side*100
    pivot['closed_angle']=angle
    start=len(OBJECTS)
    # All parts begin in the hinge's local XY frame. No micro crossbar above door.
    box(name+'_lower_panel',(width/2,0,.34),(width,.12,.68),'navy','DOORS',.035)
    for x in (.055,width-.055):
        box(name+'_stile',(x,0,height/2),(.11,.13,height),'bronze','DOORS',.015)
    box(name+'_upper_rail',(width/2,0,height-.055),(width,.13,.11),'bronze','DOORS',.012)
    if glass:
        pane(name+'_glass',[(.11,-.012,.68),(width-.11,-.012,.68),(width-.11,-.012,height-.11),(.11,-.012,height-.11)],1,'DOORS')
    else:
        box(name+'_upper_panel',(width/2,0,(height+.68)/2),(width-.22,.10,height-.79),'navy','DOORS',.035)
    rod(name+'_pull',[(width-.18,-.11,1.0),(width-.18,-.11,1.35)],.032,'brass','DOORS')
    for z in (.28,height-.28):
        rod(name+'_hinge_pin',[(0,0,z-.07),(0,0,z+.07)],.055,'brass','DOORS')
    for o in OBJECTS[start:]: o.parent=pivot
    for action_name,values in [('Doors_Open',(0,side*math.radians(100))),('Doors_Close',(side*math.radians(100),0))]:
        act=bpy.data.actions.new(name+'_'+action_name)
        pivot.animation_data_create(); pivot.animation_data.action=act
        for frame,value in [(1,values[0]),(31,values[1])]:
            pivot.rotation_euler.z=angle+value
            pivot.keyframe_insert(data_path='rotation_euler',frame=frame,index=2)
        for fc in act.fcurves:
            for k in fc.keyframe_points:k.interpolation='BEZIER'
        track=pivot.animation_data.nla_tracks.new(); track.name=action_name
        strip=track.strips.new(act.name,1,act); strip.action_frame_start=1; strip.action_frame_end=31
    pivot.animation_data.action=None
    pivot.rotation_euler.z=angle
    return pivot


def station():
    # A walk-in, spacious interpretation of the original cylindrical dispatch tower.
    disk('Foundation_octagonal_stone',3.72,0,.28,'stone','FLOOR',32)
    ring('Plinth_outer_step',3.55,3.03,.28,.42,'ivory','FLOOR',32)
    ring('Hall_floor_inlay_border',3.12,2.87,.40,.45,'brass','FLOOR',48)
    disk('Hall_walkable_floor',2.88,.35,.44,'stone','FLOOR',48)
    n=16; delta=TAU/n; r=3.05
    for i in range(n):
        mid=-math.pi/2+i*delta; a=mid-delta/2+.025; b=mid+delta/2-.025
        g='FRONT' if math.sin(mid)<-.5 else 'BACK' if math.sin(mid)>.5 else 'RIGHT' if math.cos(mid)>0 else 'LEFT'
        if i not in (0,):
            sector(f'{g}_wall_base_{i:02}',a,b,r,.19,.44,1.18,'navy',g)
            sector(f'Inner_wainscot_{i:02}',a,b,r-.20,.045,.46,1.12,'ivory','INTERIOR')
            # A single transparent pane, not an opaque black backing.
            pane(f'Mosaic_glazing_{i:02}',[(r*math.cos(a),r*math.sin(a),1.19),(r*math.cos(b),r*math.sin(b),1.19),
                 (r*math.cos(b),r*math.sin(b),5.48),(r*math.cos(a),r*math.sin(a),5.48)],i)
            for z in (1.18,3.42,5.48):
                rod(f'Window_rim_{i:02}_{z}',[(r*math.cos(a),r*math.sin(a),z),(r*math.cos(b),r*math.sin(b),z)],.035,'brass',g)
        t=mid-delta/2
        x,y=r*math.cos(t),r*math.sin(t)
        rod(f'Primary_pier_{i:02}',[(x,y,.44),(x,y,5.68)],.105,'bronze',g,10)
        for z in (.58,1.16,5.43):
            o=H.lathe(f'Pier_collar_{i:02}',[(.14,z),(.14,z+.12)],M['brass'],12,(x,y,0))
            record(o,g,'brass')
    # The front bay itself is absent from the wall, leaving a clear 1.1 m opening.
    edge=r*math.sin(delta/2); front=-r*math.cos(delta/2)
    door('Entry_left',(-edge,front,.44),edge,2.55,0,-1)
    door('Entry_right',(edge,front,.44),edge,2.55,math.pi,1)
    pane('Entry_upper_glazing',[(-edge,front,3.02),(edge,front,3.02),(edge,front,5.48),(-edge,front,5.48)],0)
    ring('Structural_crown_ring',3.27,2.78,5.49,5.83,'brass','ROOF')
    ring('Deep_navy_cornice',3.30,2.81,5.83,6.00,'navy','ROOF')
    roof=H.lathe('Removable_pressure_cap',[(3.22,6.0),(2.92,6.35),(2.27,6.90),(1.25,7.22),(.50,7.25)],M['teal'],48,caps=False)
    record(roof,'ROOF','teal')
    for i in range(8):
        t=i*TAU/8
        rod(f'Crown_rib_{i}',[(r*math.cos(t),r*math.sin(t),z) for r,z in [(3.23,6.01),(2.93,6.36),(2.28,6.91),(1.25,7.25),(.5,7.28)]],.044,'brass','ROOF')
    o=H.lathe('Pressure_valve_lantern',[(.65,7.25),(.65,7.38),(.38,7.42),(.38,7.84),(.56,7.88),(.30,8.1),(.04,8.18)],M['bronze'],24)
    record(o,'ROOF','brass')
    # Interior stations stay peripheral; central floor is deliberately unobstructed.
    for i,t in enumerate((.35,1.4,2.5)):
        x,y=2.38*math.cos(t),2.38*math.sin(t)
        o=box(f'Dispatch_console_{i}',(x,y,.94),(.85,.5,1.0),'navy','INTERIOR',.065);o.rotation_euler.z=t-math.pi/2
        o=box(f'Console_ivory_top_{i}',(x,y,1.48),(.92,.55,.1),'ivory','INTERIOR',.035);o.rotation_euler.z=t-math.pi/2
        rod(f'Pneumatic_receiver_{i}',[(x,y,1.54),(x,y,2.05)],.19,'bronze','INTERIOR',16)
    # External dispatch tube preserves the distinctive pneumatic silhouette.
    rod('Service_pipe_ivory',[(-3.05,.2,1.1),(-3.85,.2,1.1),(-4.03,.2,1.35),(-4.03,.2,3.25),(-3.85,.2,3.45)],.20,'ivory','LEFT',12)
    for z in (1.5,2.8):
        o=H.lathe('Service_brass_coupler',[(.24,z),(.24,z+.16)],M['brass'],16,(-4.03,.2,0));record(o,'LEFT','brass')
    for i in range(2):
        box(f'Entrance_step_{i}',(0,-3.48-.24*i,.30-.12*i),(1.72,.48,.16),'stone','FLOOR',.025)
    # Keep the original tower's tall silhouette while retaining a spacious floor.
    # Door dimensions remain human-scaled; only the upper glazed hall stretches.
    for o in OBJECTS:
        if o.parent:continue
        for v in o.data.vertices:
            z=v.co.z+o.location.z
            if z>3.02:v.co.z += (z-3.02)*.4
        o.data.update()


def outline(length,width,n=64):
    # Bow (-Y) fine and pointed, stern fuller. No paper-thin solid cube hull.
    return [(width/2*math.sin(t)*(.79+.21*math.cos(t)),length/2*math.cos(t)) for t in [TAU*i/n for i in range(n)]]


def boat_hull(length,width):
    n=64; pts=outline(length,width,n)
    rings=[(.48,.12),(.76,.36),(1,1.18),(1,1.36),(.87,1.36),(.87,.75)]
    v=[(x*s,y*(.82+.18*s),z) for s,z in rings for x,y in pts]
    f=[]
    for j in range(len(rings)-1):
        for i in range(n): f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    f.append(tuple(reversed(range(n))))
    o=mesh('Hollow_navy_hull_shell',v,f,'navy','HULL',True)
    # Separate flat walkable interior floor, exposed in the open cockpit and cabin.
    p=[(x*.865,y*.976,.78) for x,y in pts]
    mesh('Usable_interior_deck',p,[tuple(range(n))],'deck','FLOOR')
    v=[(x*s,y*(.82+.18*s),z) for s,z in [(1.02,1.375),(.87,1.375)] for x,y in pts]
    mesh('Ivory_walkaround_gunwale',v,[(i,(i+1)%n,n+(i+1)%n,n+i) for i in range(n)],'ivory','DECK')
    # Closed foredeck, while cockpit/cabin remain truly open below their roofs.
    cut=-3.18 if length>10 else -2.60
    inner=[(x*.87,y*.976) for x,y in pts];bow=[]
    for i,p in enumerate(inner):
        q=inner[(i+1)%n]
        if p[1]<=cut:bow.append((p[0],p[1],1.375))
        if (p[1]<cut)!=(q[1]<cut):
            t=(cut-p[1])/(q[1]-p[1]);bow.append((p[0]+t*(q[0]-p[0]),cut,1.375))
    mesh('Ivory_solid_foredeck',bow,[tuple(range(len(bow)))],'ivory','DECK')
    for z,s,mat in [(1.38,1.015,'brass'),(.95,1.0,'ivory'),(.39,.79,'brass')]:
        rod('Continuous_rubbing_strake',[(x*s,y*(.82+.18*s),z) for x,y in pts]+[(pts[0][0]*s,pts[0][1]*(.82+.18*s),z)],.035,mat,'HULL')
    # Sparse practical deck fittings rather than tiny ornamental beams.
    for side in (-1,1):
        for y in (-length*.28,length*.27):
            x=side*width*.42
            rod('Deck_grab_rail',[(x,y-.4,1.39),(x,y-.4,1.57),(x,y+.4,1.57),(x,y+.4,1.39)],.04,'brass','DECK')
            box('Mooring_cleat',(x,y+.64,1.43),(.25,.12,.10),'bronze','DECK',.02)


def seat(name,x,y,z=.82,width=.72):
    box(name+'_plinth',(x,y,z+.24),(width-.14,.65,.46),'navy','INTERIOR',.04)
    box(name+'_cushion',(x,y-.05,z+.51),(width,.72,.16),'ivory','INTERIOR',.065)
    box(name+'_back',(x,y+.31,z+.95),(width,.18,.85),'ivory','INTERIOR',.06)
    box(name+'_back_insert',(x,y+.20,z+1.0),(width-.18,.045,.53),'teal','INTERIOR',.025)


def helm(x,y):
    box('Helm_console',(x,y,1.38),(.72,.48,1.05),'navy','CABIN',.08)
    o=box('Helm_ivory_dashboard',(x,y-.05,1.96),(.8,.52,.12),'ivory','CABIN',.035)
    # Wheel lies in XZ, at comfortable standing/seated hand height.
    center=Vector((x,y+.27,1.95)); radius=.27
    rod('Wheel_rim',[tuple(center+Vector((radius*math.cos(t),0,radius*math.sin(t)))) for t in [TAU*i/24 for i in range(25)]],.034,'bronze','CABIN')
    for t in (0,TAU/3,2*TAU/3):
        rod('Wheel_spoke',[center,center+Vector((radius*math.cos(t),0,radius*math.sin(t)))],.022,'brass','CABIN')
    for dx in (-.23,0,.23):
        rod('Dashboard_dial',[(x+dx,y-.06,2.04),(x+dx,y-.06,2.07)],.07,'brass','CABIN',12)


def ferry():
    boat_hull(11.5,4.25)
    w=1.45; z=.80; sill=1.45; arch_height=2.08
    # Full rounded glass canopy follows the original boat, rather than a box cabin.
    # Double boarding doors are in the flat aft end, below the arched glazing.
    for side,g in [(-1,'LEFT'),(1,'RIGHT')]:
        x=side*w
        box(g+'_cabin_sill',(x,-.05,1.12),(.13,6.22,.64),'navy',g,.03)
        rod(g+'_brass_sill',[(x,-3.17,sill),(x,3.07,sill)],.065,'brass',g)
    front=-3.15;back=3.05
    # Forward end is a broad continuous, genuinely transparent panoramic pane.
    box('FRONT_cabin_base',(0,front,1.11),(2*w,.13,.62),'ivory','FRONT',.04)
    arc=[(w*math.cos(j*math.pi/16),front,sill+arch_height*math.sin(j*math.pi/16)) for j in range(17)]
    pane('FRONT_panoramic_arch',arc,1)
    rod('FRONT_windscreen_center',[(0,front,sill),(0,front,sill+arch_height)],.045,'brass','FRONT')
    # Actual rear opening: no wall or pane extends behind either hinged leaf.
    half=.64;door_top=z+2.15
    for side in (-1,1):
        box('BACK_entry_sidewall',(side*(w+half)/2,back,1.11),(w-half,.14,.62),'ivory','BACK',.035)
    door('Aft_entry_left',(-half,back,z),half,2.15,0,1)
    door('Aft_entry_right',(half,back,z),half,2.15,math.pi,-1)
    t=math.acos(half/w);ztop=sill+arch_height*math.sin(t)
    right=[(half,back,sill),(w,back,sill)]+[(w*math.cos(t*j/8),back,sill+arch_height*math.sin(t*j/8)) for j in range(1,9)]
    pane('BACK_glass_right',right,0)
    pane('BACK_glass_left',[(-x,y,zz) for x,y,zz in reversed(right)],2)
    crown=[(-half,back,door_top),(half,back,door_top),(half,back,ztop)]+[
        (w*math.cos(t+(math.pi-2*t)*j/8),back,sill+arch_height*math.sin(t+(math.pi-2*t)*j/8)) for j in range(1,9)]
    pane('BACK_glass_above_entry',crown,1)
    # Structural end jambs, no decorative thin crossbars over the entry opening.
    for x in (-half,half):rod('BACK_door_jamb',[(x,back,z),(x,back,ztop)],.065,'bronze','BACK')
    for k in range(5):
        ya=-3.15+k*1.24;yb=ya+1.24
        for j in range(16):
            a=j*math.pi/16;b=(j+1)*math.pi/16
            pts=[(w*math.cos(t),yy,sill+arch_height*math.sin(t)) for yy,t in [(ya,a),(yb,a),(yb,b),(ya,b)]]
            pane(f'Canopy_glass_{k:02}_{j:02}',pts,j,'ROOF')
    for k in range(6):
        yy=-3.15+k*1.24
        rod(f'Canopy_brass_hoop_{k}',[(w*math.cos(j*math.pi/32),yy,sill+arch_height*math.sin(j*math.pi/32)) for j in range(33)],.055,'brass','ROOF')
    for row,yy in enumerate((-1.65,-.40,.85)):
        for side in (-1,1):seat(f'Passenger_{row}_{side}',side*.87,yy,width=.82)
    seat('Pilot',.66,-2.5,width=.66);helm(.66,-2.92)
    # Stern boarding space stays clear behind the double doorway.
    for side in (-1,1):box('Aft_side_bench',(side*1.05,3.66,1.08),(.55,.72,.52),'ivory','INTERIOR',.08)
    box('Bow_access_hatch',(0,-4.35,1.46),(.85,1.0,.16),'ivory','DECK',.07)
    rod('Bow_hatch_handle',[(-.15,-4.34,1.56),(.15,-4.34,1.56)],.035,'brass','DECK')


def launch():
    boat_hull(8.9,3.70)
    # Forward open cockpit with sculpted, low wrap-around windscreen.
    for j in range(12):
        a=math.pi+j*math.pi/12;b=math.pi+(j+1)*math.pi/12
        pts=[(1.22*math.cos(t),-1.3+1.12*math.sin(t),z) for z,t in [(1.38,a),(1.38,b),(2.28,b),(2.28,a)]]
        pane(f'Cockpit_windscreen_{j:02}',pts,j)
    rod('Windscreen_top_rail',[(1.22*math.cos(math.pi+j*math.pi/24),-1.3+1.12*math.sin(math.pi+j*math.pi/24),2.28) for j in range(25)],.045,'brass','CABIN')
    for x in (-1.22,0,1.22):
        yy=-2.42 if x==0 else -1.3
        rod('Windscreen_primary_frame',[(x,yy,1.38),(x,yy,2.28)],.045,'bronze','CABIN')
    # Keep the complete 100-degree cabin-door sweep clear of both seat backs.
    for side in (-1,1):seat(f'Cockpit_seat_{side}',side*.67,-.95,width=.72)
    helm(.67,-1.75)
    # Aft cargo/passenger cabin, with an actual central door opening facing cockpit.
    w=1.18;front=.70;back=2.66;low=.80;top=3.05
    for side,g in [(-1,'LEFT'),(1,'RIGHT')]:
        box(g+'_cabin_lower',(side*w,(front+back)/2,1.25),(.16,back-front,.9),'ivory',g,.04)
        box(g+'_cabin_upper',(side*w,(front+back)/2,2.92),(.16,back-front,.26),'ivory',g,.035)
        for yy in (front,back):box(g+'_cabin_pier',(side*w,yy,1.93),(.19,.18,2.26),'ivory',g,.025)
        pane(g+'_cabin_glass',[(side*w,front+.10,1.71),(side*w,back-.10,1.71),(side*w,back-.10,2.78),(side*w,front+.10,2.78)],1)
        rod(g+'_window_brass_sill',[(side*w*1.01,front+.08,1.69),(side*w*1.01,back-.08,1.69)],.045,'brass',g)
    box('BACK_cabin_wall',(0,back,1.93),(2*w,.18,2.26),'ivory','BACK',.04)
    for side in (-1,1):
        box('FRONT_door_sidewall',(side*.85,front,1.93),(.66,.18,2.26),'ivory','FRONT',.035)
    box('FRONT_door_lintel',(0,front,2.95),(1.04,.18,.20),'ivory','FRONT',.035)
    door('Cabin_entry',(-.50,front-.10,low),1.00,2.04,0,-1)
    # Solid rounded pressure-cover silhouette from the original small launch.
    profile=[(-1.32,3.03),(-1.32,3.13),(-1.29,3.25),(-1.20,3.35),
             (-1.07,3.42),(-.90,3.44),(.90,3.44),(1.07,3.42),
             (1.20,3.35),(1.29,3.25),(1.32,3.13),(1.32,3.03)]
    n=len(profile);v=[(x,y,z) for y in (.55,2.81) for x,z in profile]
    f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    roof=mesh('Removable_rounded_ivory_cabin_roof',v,f,'ivory','ROOF')
    for p in roof.data.polygons:p.use_smooth=p.index>=2 and abs(p.normal.z)<.99
    box('Navy_roof_access_panel',(0,1.68,3.475),(1.10,1.40,.07),'navy','ROOF',.06)
    for side in (-1,1):rod('Roof_brass_edge',[(side*1.32,.56,3.08),(side*1.32,2.80,3.08)],.045,'brass','ROOF')
    box('Cabin_port_bench',(-.78,1.68,1.12),(.57,1.34,.64),'navy','INTERIOR',.06)
    box('Cabin_port_cushion',(-.78,1.68,1.49),(.62,1.40,.14),'ivory','INTERIOR',.05)
    box('Cabin_starboard_storage',(.82,2.13,1.17),(.46,.65,.72),'navy','INTERIOR',.045)
    box('Bow_hatch',(0,-3.25,1.46),(.65,.63,.16),'ivory','DECK',.055)
    rod('Bow_hatch_pull',[(-.12,-3.27,1.56),(.12,-3.27,1.56)],.03,'brass','DECK')


def shelf_pack(items,width,pad):
    x=y=row=0; result={}
    for key,w,h in sorted(items,key=lambda it:-it[2]):
        w+=2*pad;h+=2*pad
        if x+w>width and x>0:x=0;y+=row;row=0
        result[key]=(x+pad,y+pad);x+=w;row=max(row,h)
    return result,y+row


def unwrap():
    """Planar faces use their exact metric basis, including all bevel/interior faces.

    Non-planar quads are triangulated before unwrap; no projection distortion.
    Face islands intentionally have seams. Semantic region blocks are contiguous.
    """
    groups=collections.defaultdict(list); records=[]
    for o in OBJECTS:
        # Retain planar ngons/quads; split warped faces for metric-accurate UVs.
        bm=bmesh.new();bm.from_mesh(o.data)
        warped=[f for f in bm.faces if any(abs((v.co-f.verts[0].co).dot(f.normal))>1e-5 for v in f.verts)]
        if warped:bmesh.ops.triangulate(bm,faces=warped)
        bm.to_mesh(o.data);bm.free();o.data.update()
        uv=o.data.uv_layers.new(name='UV0')
        for f in o.data.polygons:
            coords=[o.data.vertices[i].co for i in f.vertices]
            edge=max([(coords[(i+1)%len(coords)]-v) for i,v in enumerate(coords)],key=lambda v:v.length)
            u=edge.normalized();v=f.normal.cross(u).normalized();origin=coords[0]
            xy=[((p-origin).dot(u),(p-origin).dot(v)) for p in coords]
            lo=[min(p[k] for p in xy) for k in (0,1)]; hi=[max(p[k] for p in xy) for k in (0,1)]
            w,h=[max(hi[k]-lo[k],.00001) for k in (0,1)]
            if h>w:xy=[(y,x) for x,y in xy];w,h=h,w;lo=lo[::-1]
            rec={'object':o.name,'id':o['surface_id'],'face':f.index,'region':o['uv_region'],
                 'xy':[(x-lo[0],y-lo[1]) for x,y in xy],'w':w,'h':h,'loops':list(f.loop_indices)}
            groups[o['uv_region']].append(len(records));records.append(rec)
    # Pack metric face rectangles within semantic blocks, then pack those blocks.
    # Iterate padding to guarantee four pixels BETWEEN neighboring islands at 2048.
    pad=.035
    for attempt in range(12):
        blocks=[];local={}
        for group,indices in groups.items():
            area=sum((records[i]['w']+2*pad)*(records[i]['h']+2*pad) for i in indices)
            width=max(max(records[i]['w']+2*pad for i in indices),math.sqrt(area)*1.30)
            positions,height=shelf_pack([(i,records[i]['w'],records[i]['h']) for i in indices],width,pad)
            local[group]=positions;blocks.append((group,width,height))
        area=sum(w*h for _,w,h in blocks)
        width=max(max(w for _,w,_ in blocks)+2*pad,math.sqrt(area)*1.15)
        bp,height=shelf_pack(blocks,width,pad*2)
        size=max(width,height)+pad*4
        if 2*pad/size*2048>=4.1:break
        pad*=1.45
    assert 2*pad/size*2048>=4, 'UV padding budget failed'
    objmap={o.name:o for o in OBJECTS}
    for i,r in enumerate(records):
        ox,oy=bp[r['region']];x,y=local[r['region']][i]
        pts=[((xx+x+ox+pad*2)/size,(yy+y+oy+pad*2)/size) for xx,yy in r['xy']]
        uv=objmap[r['object']].data.uv_layers.active.data
        for loop,p in zip(r['loops'],pts):uv[loop].uv=p
        r['uv']=pts
        del r['xy'];del r['loops']
    regions={g:{'x':(bp[g][0]+pad*2)/size,'y':(bp[g][1]+pad*2)/size,'w':w/size,'h':h/size}
             for g,w,h in blocks}
    payload={'asset':A.asset,'resolution':2048,'uv_layer':'UV0','pixels_per_meter':2048/size,
             'minimum_island_gap_px':2*pad/size*2048,'regions':regions,'surfaces':records}
    (OUT/'surface_mapping.json').write_text(json.dumps(payload,indent=2))
    # Basic UV integrity: all loops mapped, non-degenerate, bounds, rectangle disjointness.
    rects=[]
    for r in records:
        xs=[p[0] for p in r['uv']];ys=[p[1] for p in r['uv']]
        assert 0<min(xs)<max(xs)<1 and 0<min(ys)<max(ys)<1
        area=abs(sum(r['uv'][j][0]*r['uv'][(j+1)%len(xs)][1]-r['uv'][(j+1)%len(xs)][0]*r['uv'][j][1] for j in range(len(xs))))/2
        assert area>1e-15,(r['object'],r['face'])
        rects.append((min(xs),max(xs),min(ys),max(ys)))
    active=[]
    for rect in sorted(rects):
        active=[q for q in active if q[1]>rect[0]+1e-9]
        assert all(min(rect[3],q[3])-max(rect[2],q[2])<1e-9 for q in active),'UV rectangle overlap'
        active.append(rect)
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJECTS:o.select_set(True)
    bpy.context.view_layer.objects.active=OBJECTS[0]
    bpy.ops.preferences.addon_enable(module='io_mesh_uv_layout')
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    # Blender's PNG exporter needs GPUOffScreen even with a CPU render device.
    # Its native SVG path works headlessly; rasterize that exact vector export.
    bpy.ops.uv.export_layout(filepath=str(OUT/'uv_layout.svg'),mode='SVG',export_all=True,size=(2048,2048),opacity=0,modified=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Annotation uses native UV export as the exact pixel overlay, never repacks.
    subprocess.run([shutil.which('python') or shutil.which('python3'),str(Path(__file__).with_name('transport_uv_guide.py')),str(OUT)],check=True)
    return payload


def camera_and_lights():
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16
    scene.cycles.use_denoising=False
    scene.render.resolution_x=scene.render.resolution_y=2048;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.world.color=(.36,.41,.46)
    scene.view_settings.view_transform='AgX'
    for name,pos,power,size in [('Key',(-9,-12,16),2300,8),('Fill',(10,-2,10),1500,9),('Rim',(1,9,13),2000,7)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
        o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos
        o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add()
    c=bpy.context.object;c.name='REVIEW_Isometric';c.data.type='ORTHO'
    if A.asset=='pneumatic_station':pos=(12,-17,14);target=(0,0,4.8);scale=13.8
    else:pos=(12,-14,12);target=(0,0,1.4);scale=14.2 if A.asset=='commuter_ferry' else 11.8
    c.location=pos;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale
    scene.camera=c
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.08))
    floor=bpy.context.object;floor.name='REVIEW_Ground_not_exported';floor.data.materials.append(M['studio'])
    return scene


def main():
    global ROOF
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    H.collection('Editable_components');H.QUALITY='full'
    ROOF=bpy.data.collections.new('ROOF_removable');bpy.context.scene.collection.children.link(ROOF)
    for name,color,metal,rough,alpha in [
        ('ivory',(.73,.68,.55),0,.76,1),('stone',(.58,.56,.49),0,.83,1),
        ('navy',(.018,.064,.091),.35,.42,1),('teal',(.028,.15,.20),.55,.38,1),
        ('brass',(.48,.30,.105),.82,.34,1),('bronze',(.18,.115,.05),.78,.42,1),
        ('deck',(.25,.28,.27),0,.78,1),('studio',(.15,.185,.20),0,.9,1),
        ('glass0',(.12,.40,.46),0,.22,.30),('glass1',(.16,.44,.48),0,.24,.34),('glass2',(.13,.34,.42),0,.26,.32)]:
        M[name]=material(name,color,metal,rough,alpha)
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.render.fps=30
    bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=31
    {'pneumatic_station':station,'commuter_ferry':ferry,'harbor_launch':launch}[A.asset]()
    uv=unwrap()
    scene=camera_and_lights();scene.frame_set(1)
    # Isometric clean render with all doors closed, free of overlapping NLA evaluation.
    pivots=[o for o in scene.objects if o.type=='EMPTY' and o.animation_data]
    for o in pivots:
        for t in o.animation_data.nla_tracks:t.mute=True
        o.rotation_euler.z=o['closed_angle']
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(A.asset+'.blend')))
    scene.render.filepath=str(OUT/'isometric.png');bpy.ops.render.render(write_still=True)
    for o in ROOF.objects:o.hide_render=True
    for o in pivots:o.rotation_euler.z+=math.radians(o['opening_degrees'])
    scene.render.filepath=str(OUT/'interior_doors_open.png');bpy.ops.render.render(write_still=True)
    for o in ROOF.objects:o.hide_render=False
    for o in pivots:o.rotation_euler.z-=math.radians(o['opening_degrees'])
    # Diagnostic atlas is temporary; never used for the delivered PBR materials.
    original={o.name:list(o.data.materials) for o in OBJECTS}
    guide=bpy.data.images.load(str(OUT/'uv_guide.png'))
    diag=material('REVIEW_UV_diagnostic',(1,1,1),0,.75)
    nodes=diag.node_tree.nodes;tex=nodes.new('ShaderNodeTexImage');tex.image=guide
    diag.node_tree.links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
    for o in OBJECTS:o.data.materials.clear();o.data.materials.append(diag)
    scene.render.filepath=str(OUT/'model_to_uv.png');bpy.ops.render.render(write_still=True)
    for o in OBJECTS:
        o.data.materials.clear()
        for m in original[o.name]:o.data.materials.append(m)
    # Blender 4.3's NLA_TRACKS exporter samples named tracks even when muted.
    # Keep them muted here so the default exported node pose remains CLOSED.
    # Export with NLA tracks merged by exact clip name across independently hinged doors.
    bpy.ops.object.select_all(action='DESELECT')
    for o in OBJECTS+pivots:o.select_set(True)
    bpy.context.view_layer.objects.active=OBJECTS[0]
    bpy.ops.export_scene.gltf(filepath=str(OUT/(A.asset+'.glb')),export_format='GLB',use_selection=True,
        export_animations=True,export_animation_mode='NLA_TRACKS',export_nla_strips_merged_animation_name='Animation',
        export_texcoords=True,export_cameras=False,export_lights=False,export_extras=True)
    for o in pivots:
        for t in o.animation_data.nla_tracks:t.mute=True
        o.rotation_euler.z=o['closed_angle']
    # Saved file opens with doors closed; clips are available in labeled NLA tracks.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(A.asset+'.blend')))
    report={'asset':A.asset,'triangles':sum(len(p.vertices)-2 for o in OBJECTS for p in o.data.polygons),
        'editable_meshes':len(OBJECTS),'hinged_doors':len(pivots),'clips':['Doors_Open','Doors_Close'],
        'uv0':'all mesh loops mapped, non-degenerate, unique face rectangles, uniform metric texel density',
        'minimum_uv_gap_px':uv['minimum_island_gap_px'],'texel_density_px_per_m':uv['pixels_per_meter'],
        'materials':'glTF metallic/roughness, alpha BLEND tinted separate glass; no final textures',
        'roof_collection':'ROOF_removable','units':'meters','checks':'Blender geometry, UV bounds/overlap/padding and GLB animation payload only; no game build'}
    # Inspect real binary glTF output, including separate animation channels and UV0.
    import struct
    data=(OUT/(A.asset+'.glb')).read_bytes();length,kind=struct.unpack_from('<II',data,12)
    gltf=json.loads(data[20:20+length]);animations=gltf.get('animations',[])
    report['exported_animation_channels']={a['name']:len(a['channels']) for a in animations}
    assert {a['name'] for a in animations}=={'Doors_Open','Doors_Close'},report
    assert all(len(a['channels'])==len(pivots) for a in animations),report
    # Check the actual binary quaternion samples, not merely clip/channel names.
    binary=data[28+length:]
    def samples(accessor):
        a=gltf['accessors'][accessor];v=gltf['bufferViews'][a['bufferView']]
        dim={'SCALAR':1,'VEC4':4}[a['type']]
        offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',4*dim)
        return [struct.unpack_from('<'+'f'*dim,binary,offset+j*stride) for j in range(a['count'])]
    def same_rotation(a,b):return abs(sum(x*y for x,y in zip(a,b)))>.99999
    for animation in animations:
        for channel in animation['channels']:
            node=gltf['nodes'][channel['target']['node']];extra=node['extras']
            closed=extra['closed_angle'];opened=closed+math.radians(extra['opening_degrees'])
            qclosed=(0,math.sin(closed/2),0,math.cos(closed/2))
            qopen=(0,math.sin(opened/2),0,math.cos(opened/2))
            sampler=animation['samplers'][channel['sampler']]
            q=samples(sampler['output']);times=samples(sampler['input'])
            expected=(qclosed,qopen) if animation['name']=='Doors_Open' else (qopen,qclosed)
            assert same_rotation(q[0],expected[0]) and same_rotation(q[-1],expected[1])
            assert same_rotation(node.get('rotation',(0,0,0,1)),qclosed)
            assert abs(times[-1][0]-times[0][0]-1)<1e-5
    report['exported_door_motion']='binary samples verified: closed default pose, independent 100 degree hinges, inverse open/close endpoints, 1 second'
    assert all('TEXCOORD_0' in p['attributes'] for m in gltf['meshes'] for p in m['primitives'])
    assert any(m.get('alphaMode')=='BLEND' for m in gltf['materials'])
    (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'README.md').write_text(f'''# {A.asset}\n\nStandalone editable original VorGun derivative, meters/Z-up Blender, Y-up glTF.\n\n- `{A.asset}.blend`: separate named components, real interior and removable `ROOF_removable` collection.\n- `{A.asset}.glb`: standalone PBR, independent hinged doors; `Doors_Open` / `Doors_Close`, 1 second at 30 fps.\n- `uv_layout.svg`: native Blender UV0 export.\n- `uv_layout.png`: exact native SVG rasterized at 2048², transparent background (no GPU needed).\n- `uv_guide.png`: color/ID annotation on exactly the same island coordinates.\n- `model_to_uv.png`: actual atlas applied temporarily to model, for painting correspondence.\n- `surface_mapping.json`: exact object IDs, semantic regions, polygon indices and UV coordinates.\n- `isometric.png`, `interior_doors_open.png`: actual Blender renders.\n- `checks.json`: measured geometry, UV and exported animation checks.\n\nAtlas regions are labeled by function. Every face has its own intentionally separated\nplanar island, allowing all interior/exterior surfaces to be painted without overlap.\nUniform physical texel density; minimum 4 px separation at 2048². Small bevel islands\ncan share their region's base color when painted. No final texture painting.\n\nThe saved Blend opens with NLA tracks muted to show closed doors. Unmute ONLY the\nchosen `Doors_Open` OR `Doors_Close` track on each hinge when previewing. Both tracks\nare exported as separate synchronized glTF clips. The roof is removable, not animated.\nThe inspection ground/lights/camera are excluded from GLB export.\n\nReference: `docs/assets/VORGUN_VISUAL_REFERENCES_FOR_3D_BATCH.md`;\noriginal `{'pneumatic_tube_station.png' if A.asset=='pneumatic_station' else 'commuter_boat.png' if A.asset=='commuter_ferry' else 'courier_mini_launch.png'}`.\nRebuild with `blender -b -t 8 --python-exit-code 1 --python blender/scripts/build_transport_production.py -- --asset {A.asset}`.\nNo game integration, asset overwrite or deployment.\n''')
    # Blender save backups are not deliverables.
    for p in OUT.glob('*.blend1'):p.unlink()
    print('TRANSPORT_ASSET_COMPLETE '+json.dumps(report))


if __name__=='__main__':main()
