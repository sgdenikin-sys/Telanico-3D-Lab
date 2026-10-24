"""Build the standalone Settlements Hall; no map or gameplay changes.

Blender 4.3+: blender -b --python-exit-code 1 --python
blender/scripts/build_settlements_hall.py -- --render

Default outputs follow the repository's ignored generated-asset conventions.
Use --output-dir PATH to put the blend, GLB, statistics and review renders together.
All materials use glTF core metallic/roughness; no textures or add-ons required.
"""
from pathlib import Path
import argparse
import json
import math
import sys
from collections import defaultdict

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_smoke_test import cube, material

ROOT = Path(__file__).resolve().parents[2]
TAU = math.tau
M = {}
COL = None
ASSET = []
CACHE = {}
# The full preset reproduces the approved V2; lite is a separate, opt-in mobile LOD.
QUALITY = 'full'


def lite():
    return QUALITY == 'lite'


def collection(name):
    global COL
    COL = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(COL)
    return COL


def register(obj):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    COL.objects.link(obj)
    ASSET.append(obj)
    return obj


def mesh(name, verts, faces, mat, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    COL.objects.link(obj)
    ASSET.append(obj)
    data.materials.append(mat)
    for face in data.polygons:
        face.use_smooth = smooth
    return obj


def block(name, pos, dims, mat, bevel=.025):
    # Avoid bevel tessellation on tiny seams in the mobile LOD.
    if lite() and bevel <= .030 and min(dims) < .35:
        bevel = 0
    obj = register(cube(name, pos, dims, mat, 0))
    if bevel:
        modifier = obj.modifiers.new('Single architectural edge bevel', 'BEVEL')
        modifier.width, modifier.segments = min(bevel, min(dims)*.20), 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def instance(source, name, pos=(0, 0, 0), angle=0):
    obj = bpy.data.objects.new(name, source.data)
    COL.objects.link(obj)
    obj.location = pos
    obj.rotation_euler.z = angle
    ASSET.append(obj)
    return obj


def lathe(name, profile, mat, segments=32, pos=(0, 0, 0), phase=0, caps=True):
    """Radius/Z profile, smooth sides and flat ledges. Only a top cap is needed:
    the foot of each lathe sits on another solid stone or metal component.
    """
    if lite():
        segments = min(segments, 24)
    verts = [(r*math.cos(TAU*i/segments+phase),
              r*math.sin(TAU*i/segments+phase), z)
             for r, z in profile for i in range(segments)]
    faces = [(j*segments+i, j*segments+(i+1)%segments,
              (j+1)*segments+(i+1)%segments, (j+1)*segments+i)
             for j in range(len(profile)-1) for i in range(segments)]
    if caps:
        faces += [tuple((len(profile)-1)*segments+i for i in range(segments))]
    obj = mesh(name, verts, faces, mat)
    for p in obj.data.polygons:
        p.use_smooth = abs(p.normal.z) < .95
    obj.location = pos
    return obj


def tube(name, points, radius, mat, sides=4):
    # Hairline ornament is invisible from the normal elevated game camera.
    if lite() and radius <= .023:
        return None
    verts = []
    for i, point in enumerate(points):
        tangent = Vector(points[min(i+1, len(points)-1)])-Vector(points[max(0, i-1)])
        tangent.normalize()
        ref = Vector((0, 0, 1)) if abs(tangent.z) < .9 else Vector((0, 1, 0))
        u = tangent.cross(ref).normalized()
        v = tangent.cross(u).normalized()
        for j in range(sides):
            verts.append(Vector(point)+radius*(math.cos(TAU*j/sides)*u+math.sin(TAU*j/sides)*v))
    faces = [(i*sides+j, i*sides+(j+1)%sides, (i+1)*sides+(j+1)%sides,
              (i+1)*sides+j) for i in range(len(points)-1) for j in range(sides)]
    faces += [tuple(reversed(range(sides))),
              tuple((len(points)-1)*sides+j for j in range(sides))]
    return mesh(name, verts, faces, mat, sides >= 6)


def prism(name, outline, low, high, mat, bevel=0):
    n = len(outline)
    verts = [(x, y, low) for x, y in outline]+[(x, y, high) for x, y in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n, n*2))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    obj = mesh(name, verts, faces, mat)
    if bevel:
        mod = obj.modifiers.new('Small stone arris', 'BEVEL')
        mod.width, mod.segments = bevel, 2
    return obj


def arch_points(width, bottom, spring, segments=None):
    segments = (7 if lite() else 12) if segments is None else segments
    r = width/2
    return [(-r, bottom), (r, bottom)]+[
        (r*math.cos(math.pi*i/segments), spring+r*math.sin(math.pi*i/segments))
        for i in range(segments+1)]


def arch_slab(name, width, bottom, spring, front, back, mat):
    p = arch_points(width, bottom, spring)
    n = len(p)
    if mat in (M.get('glass'), M.get('shadow')):
        return mesh(name, [(x, front, z) for x, z in p], [tuple(range(n))], mat)
    verts = [(x, y, z) for y in (front, back) for x, z in p]
    # Front is -Y; CCW XZ has a -Y normal.
    faces = [tuple(range(n)), tuple(reversed(range(n, 2*n)))]
    faces += [(i, n+i, n+(i+1)%n, (i+1)%n) for i in range(n)]
    return mesh(name, verts, faces, mat)


def arch_ring(name, width, bottom, spring, band, front, back, mat, segments=10):
    if lite():
        segments = min(segments, 6)
    r = width/2
    inner = [(-r, bottom), (-r, spring)]+[
        (r*math.cos(math.pi-math.pi*i/segments), spring+r*math.sin(math.pi*i/segments))
        for i in range(1, segments+1)]+[(r, bottom)]
    outer = [(-r-band, bottom), (-r-band, spring)]+[
        ((r+band)*math.cos(math.pi-math.pi*i/segments), spring+(r+band)*math.sin(math.pi*i/segments))
        for i in range(1, segments+1)]+[(r+band, bottom)]
    count = len(inner)
    verts = [(x, y, z) for y in (front, back) for contour in (inner, outer) for x, z in contour]
    faces = []
    for i in range(count-1):
        j = i+1
        faces += [(i, j, count+j, count+i),
                  (i, 2*count+i, 2*count+j, j),
                  (count+i, count+j, 3*count+j, 3*count+i)]
    faces += [(0, count, 3*count, 2*count),
              (count-1, 3*count-1, 4*count-1, 2*count-1)]
    return mesh(name, verts, faces, mat)


def wall_arch(name, total_width, bottom, top, opening_width, opening_bottom, spring, depth=.32):
    """Real opening, assembled analytically: no Boolean modifiers or backing cube."""
    r, w = opening_width/2, total_width/2
    # Build a single connected front/back mesh by welding adjoining strip corners.
    verts, faces, lookup = [], [], {}
    def vertex(x, y, z):
        key = tuple(round(n, 6) for n in (x, y, z))
        if key not in lookup:
            lookup[key] = len(verts)
            verts.append((x, y, z))
        return lookup[key]
    def quad(points):
        faces.append(tuple(vertex(*p) for p in points))
    arcs = 6 if lite() else 10
    contour = [(-r, spring)]+[
        (-r*math.cos(math.pi*i/arcs), spring+r*math.sin(math.pi*i/arcs))
        for i in range(1, arcs+1)]
    for y, reverse in ((0, False), (depth, True)):
        polygons = [[(-w, bottom), (-r, bottom), (-r, top), (-w, top)],
                    [(r, bottom), (w, bottom), (w, top), (r, top)]]
        if opening_bottom > bottom:
            polygons.append([(-r, bottom), (r, bottom), (r, opening_bottom), (-r, opening_bottom)])
        polygons += [[(a[0], a[1]), (b[0], b[1]), (b[0], top), (a[0], top)]
                     for a, b in zip(contour, contour[1:])]
        for p in polygons:
            q = [(x, y, z) for x, z in p]
            quad(list(reversed(q)) if reverse else q)
    hole = [(-r, opening_bottom), (-r, spring)]+contour[1:]+[(r, opening_bottom)]
    for a, b in zip(hole, hole[1:]):
        quad([(a[0], 0, a[1]), (a[0], depth, a[1]),
              (b[0], depth, b[1]), (b[0], 0, b[1])])
    if opening_bottom > bottom:
        quad([(-r, 0, opening_bottom), (r, 0, opening_bottom),
              (r, depth, opening_bottom), (-r, depth, opening_bottom)])
    for a, b in [((-w, bottom), (-w, top)), ((-w, top), (w, top)),
                 ((w, top), (w, bottom)), ((w, bottom), (-w, bottom))]:
        quad([(a[0], 0, a[1]), (b[0], 0, b[1]),
              (b[0], depth, b[1]), (a[0], depth, a[1])])
    return mesh(name, verts, faces, M['ivory'])


def place_module(objects, x, y, angle, prefix):
    for obj in objects:
        obj.name = prefix+' | '+obj.name
        obj.location.x += x
        obj.location.y += y
        obj.rotation_euler.z = angle


def window_bay(width=2.9, bottom=1.4, top=7.35, opening=1.5,
               sill=2.05, spring=4.85, door=False):
    before = len(ASSET)
    wall_arch('Pier wall with arch opening', width, bottom, top, opening, sill, spring)
    arch_ring('Limestone archivolt', opening, sill, spring, .18, -.13, .04, M['ivory'])
    arch_ring('Bronze glazing frame', opening-.13, sill+.04, spring, .055, -.055, .09, M['bronze'])
    transom = spring-.45
    pane = arch_slab('Fixed blue arched fanlight' if door else 'Recessed tinted glass',
                    opening-.20, transom if door else sill+.08, spring, .07, .15 if door else .095,
                    M['door'] if door else M['glass'])
    # An interior shadow well behind transparent glass, rather than opaque wall.
    arch_slab('Unlit interior reveal', opening-.22, sill+.08, spring, .48, .50, M['shadow'])
    block('Projecting stone sill', (0, -.14, sill-.04), (opening+.44, .48, .14), M['paving'], .02)
    mid = (sill+spring)/2
    tube('Central mullion', [(0, -.018, transom if door else sill+.1), (0, -.018, spring+opening/2-.12)], .026, M['brass'])
    tube('Transom', [(-opening/2+.12, -.02, spring-.45), (opening/2-.12, -.02, spring-.45)], .025, M['brass'])
    # Two restrained radial bars in the fanlight.
    for sign in (-1, 1):
        tube('Fanlight ray', [(0, -.025, spring-.45),
                             (sign*opening*.30, -.025, spring+opening*.32)], .021, M['brass'])
    if door:
        for sign in (-1, 1):
            start = len(ASSET)
            leaf_width = (opening-.20)/2
            leaf_low, leaf_high = sill+.08, transom-.025
            mid_leaf = (leaf_low+leaf_high)/2
            block('Hinged blue door leaf', (sign*leaf_width/2, .11, mid_leaf),
                  (leaf_width-.012, .08, leaf_high-leaf_low), M['door'], .014)
            block('Door inset brass border', (sign*leaf_width/2, -.025, mid_leaf),
                  (leaf_width-.12, .035, leaf_high-leaf_low-.14), M['brass'], .007)
            block('Painted inset panel', (sign*leaf_width/2, -.048, mid_leaf),
                  (leaf_width-.20, .035, leaf_high-leaf_low-.22), M['door'], .007)
            tube('Door pull', [(sign*.13, -.16, sill+1.05), (sign*.13, -.16, sill+1.42)], .027, M['brass'], 6)
            tube('Door meeting stile', [(sign*.018, -.018, leaf_low),
                                        (sign*.018, -.018, leaf_high)], .018, M['brass'])
            for part in ASSET[start:]:
                part['motion_group'] = 'Door_Leaf_'+('L' if sign < 0 else 'R')
        compass('Entrance compass crest', (0, -.16, spring+.10), .39, M['brass'], vertical=True)
    else:
        tube('Lower transom', [(-opening/2+.12, -.02, mid-.25),
                               (opening/2-.12, -.02, mid-.25)], .018, M['bronze'])
    # Keystone, the only ornament repeated above the arch.
    block('Arch keystone', (0, -.16, spring+opening/2+.09), (.24, .24, .38), M['paving'], .03)
    parts = ASSET[before:]
    for obj in parts:
        matrix = obj.matrix_basis.copy()
        obj.data.transform(matrix)
        obj.matrix_basis.identity()
    return parts


def compass(name, pos, size, mat, vertical=False):
    verts = [pos]
    for i in range(16):
        a = TAU*i/16
        r = size if i % 2 == 0 else size*.25
        if i % 4 == 2:
            r *= .70
        offset = (math.sin(a)*r, -.012, math.cos(a)*r) if vertical else (math.sin(a)*r, math.cos(a)*r, .006)
        verts.append(tuple(pos[j]+offset[j] for j in range(3)))
    faces = [(0, 1+i, 1+(i+1)%16) for i in range(16)]
    return mesh(name, verts, faces, mat)


def column(name, x, y, low, high, radius=.30):
    key = (round(high-low, 3), radius)
    if key not in CACHE:
        h = high-low
        # Entasis, torus-shaped mouldings and capital are one editable lathe.
        profile = [(radius*1.43, 0), (radius*1.43, .13),
                   (radius*1.18, .26),
                   (radius*.97, .34), (radius*.96, h*.30),
                   (radius*.88, h-.53), (radius*1.07, h-.45),
                   (radius*1.07, h-.33), (radius*1.34, h-.23),
                   (radius*1.40, h)]
        segments = (8 if radius >= .3 else 6) if lite() else (12 if radius >= .3 else 8)
        shaft = lathe('Ivory entasis column', profile, M['ivory'], segments, caps=False)
        # Brass confined to the capital collar and foot band.
        collar = lathe('Aged brass collars', [(radius*1.20, .16), (radius*1.20, .24)], M['brass'], segments, caps=False)
        crown = lathe('Capital brass neck', [(radius*1.09, h-.44), (radius*1.09, h-.34)], M['brass'], segments, caps=False)
        plinth = block('Square beveled plinth', (0, 0, .01), (radius*3.2, radius*3.2, .20), M['paving'])
        abacus = block('Square abacus', (0, 0, h+.015), (radius*3.15, radius*3.15, .16), M['ivory'])
        # Apply part offsets into mesh coordinates so modules share local origins.
        parts = [shaft, collar, crown, plinth, abacus]
        for p in parts:
            for v in p.data.vertices:
                v.co += p.location
            p.location = (0, 0, 0)
        CACHE[key] = parts
        for p in parts:
            p.location = (x, y, low)
            p.name = name+' | '+p.name
    else:
        for p in CACHE[key]:
            instance(p, name+' | '+p.data.name, (x, y, low))


def dome(name, radius, base, height, mat, pos=(0, 0, 0), segments=64, rings=16):
    if lite():
        segments, rings = min(segments, 36), min(rings, 10)
    profile = [(radius*math.cos(math.pi*.5*i/rings), base+height*math.sin(math.pi*.5*i/rings))
               for i in range(rings)]
    profile.append((.025, base+height))
    return lathe(name, profile, mat, segments, pos, caps=False)


def build_rotunda():
    collection('01 | Rotunda — twelve editable arch bays')
    # Base cornice, floor and plinth; sealed body, without an unnecessary interior.
    lathe('Stepped circular podium', [(5.70, .24), (5.82, .30), (5.82, .48),
          (5.63, .55), (5.63, 1.21), (5.82, 1.27), (5.82, 1.43)], M['paving'], 36)
    lathe('Podium dark rebate', [(5.66, .66), (5.66, .72)], M['sandstone'], 36)
    lathe('Rotunda floor', [(5.28, 1.39), (5.28, 1.43)], M['shadow'], 48)
    # Faceted wall uses a 12-sided tangent plan. Each window is a real opening.
    radius = 5.24
    half = radius*math.tan(math.pi/12)
    template = None
    for i in range(12):
        a = -math.pi/2+i*TAU/12
        x, y = radius*math.cos(a), radius*math.sin(a)
        angle = a+math.pi/2
        if i == 0:
            parts = window_bay(half*2, opening=2.12, sill=1.43, spring=4.63, door=True)
        elif template is None:
            parts = window_bay(half*2)
            template = parts
        else:
            parts = [instance(p, p.data.name) for p in template]
        place_module(parts, x, y, angle, f'Rotunda bay {i+1:02}')
    for i in range(12):
        a = -math.pi/2+(i+.5)*TAU/12
        column(f'Peristyle column {i+1:02}', 5.77*math.cos(a), 5.77*math.sin(a), 1.44, 7.05)
    lathe('Deep classical entablature', [(5.40, 6.78), (5.85, 6.84),
          (5.85, 7.06), (5.68, 7.14), (5.68, 7.43), (5.98, 7.53),
          (5.98, 7.70), (5.80, 7.78)], M['ivory'], 36)
    lathe('Cornice brass fillet', [(5.86, 7.27), (5.86, 7.32)], M['brass'], 36)
    # Low sloping annular roof below the raised dome drum.
    lathe('Rotunda annular standing seam roof', [(5.80, 7.78), (4.40, 8.53)], M['teal'], 36, caps=False)
    for i in range(12 if lite() else 24):
        a = i*TAU/(12 if lite() else 24)
        tube('Annular roof seam', [(5.77*math.cos(a), 5.77*math.sin(a), 7.80),
                                  (4.40*math.cos(a), 4.40*math.sin(a), 8.55)], .022, M['bronze'])
    # Balustrade crown posts are sparse to preserve the silhouette.
    n_post = 6 if lite() else 12
    for i in range(n_post):
        a = -math.pi/2+(i+.5)*TAU/n_post
        x, y = 5.65*math.cos(a), 5.65*math.sin(a)
        block('Parapet pedestal', (x, y, 7.98), (.49, .49, .53), M['ivory'], .025)
        lathe('Parapet brass acorn', [(.17, 8.26), (.22, 8.40), (.12, 8.57), (.01, 8.70)], M['brass'], 10, (x, y, 0))


def rectangular_ring(name, width, low, high, inner_width, inner_low, inner_high, front, back, mat):
    outer = [(-width/2, low), (width/2, low), (width/2, high), (-width/2, high)]
    inner = [(-inner_width/2, inner_low), (inner_width/2, inner_low),
             (inner_width/2, inner_high), (-inner_width/2, inner_high)]
    verts = [(x, y, z) for y in (front, back) for contour in (outer, inner) for x, z in contour]
    faces = []
    for i in range(4):
        j = (i+1)%4
        faces += [(i, j, 4+j, 4+i), (8+i, 12+i, 12+j, 8+j),
                  (i, 8+i, 8+j, j), (4+i, 4+j, 12+j, 12+i)]
    return mesh(name, verts, faces, mat)


def build_crown():
    collection('02 | Clerestory and ribbed dome')
    r = 4.30
    n_drum = 16 if lite() else 24
    w = 2*r*math.tan(math.pi/n_drum)
    template = None
    for i in range(n_drum):
        a = -math.pi/2+i*TAU/n_drum
        if template is None:
            start = len(ASSET)
            rectangular_ring('Clerestory cut stone bay', w, 8.36, 9.96,
                             .48, 8.65, 9.58, 0, .26, M['ivory'])
            rectangular_ring('Clerestory bronze frame', .52, 8.61, 9.62,
                             .42, 8.69, 9.54, -.045, .045, M['bronze'])
            mesh('Clerestory tinted pane', [(-.22, .06, 8.67), (.22, .06, 8.67),
                 (.22, .06, 9.56), (-.22, .06, 9.56)], [(0, 1, 2, 3)], M['glass'])
            mesh('Clerestory interior shadow', [(-.23, .38, 8.66), (.23, .38, 8.66),
                 (.23, .38, 9.57), (-.23, .38, 9.57)], [(0, 1, 2, 3)], M['shadow'])
            tube('Clerestory vertical brass mullion', [(0, -.01, 8.70), (0, -.01, 9.53)], .018, M['brass'])
            parts = ASSET[start:]
            template = parts
        else:
            parts = [instance(p, p.data.name) for p in template]
        place_module(parts, r*math.cos(a), r*math.sin(a), a+math.pi/2, f'Clerestory {i+1:02}')
    lathe('Drum lower bead', [(4.38, 8.35), (4.47, 8.41), (4.47, 8.56)], M['ivory'], 36)
    lathe('Dome spring cornice', [(4.32, 9.78), (4.60, 9.86), (4.60, 10.05), (4.49, 10.14)], M['ivory'], 36)
    lathe('Dome brass waterline', [(4.49, 10.12), (4.53, 10.19), (4.53, 10.26)], M['brass'], 36)
    dome('Smooth deep blue metal dome', 4.48, 10.20, 4.95, M['teal'])
    for i in range(12):
        a = TAU*i/12
        points = []
        rib_steps = 10 if lite() else 16
        for j in range(rib_steps):
            t = math.pi*.5*j/rib_steps
            r = 4.50*math.cos(t)
            points.append((r*math.cos(a), r*math.sin(a), 10.22+4.96*math.sin(t)))
        tube('Raised brass dome rib', points, .050, M['brass'], 4)
    lathe('Lantern stepped brass base', [(.39, 14.99), (.56, 15.08), (.56, 15.20),
          (.40, 15.26), (.30, 15.38)], M['brass'], 32)
    lathe('Crown blue jewel', [(.18, 15.36), (.36, 15.64), (.22, 16.05), (.01, 16.20)], M['teal'], 8)
    for i in range(8):
        a = TAU*i/8
        tube('Lantern cage', [(.18*math.cos(a), .18*math.sin(a), 15.36),
                              (.36*math.cos(a), .36*math.sin(a), 15.64),
                              (.22*math.cos(a), .22*math.sin(a), 16.05), (0, 0, 16.20)], .022, M['brass'])
    lathe('Crown finial', [(.08, 16.17), (.14, 16.28), (.07, 16.40), (.001, 16.47)], M['brass'], 12)


def hipped_roof(cx, cy, width, depth, low, high):
    x, y, inset = width/2, depth/2, .82
    verts = [(cx-x, cy-y, low), (cx+x, cy-y, low),
             (cx+x, cy+y, low), (cx-x, cy+y, low),
             (cx-x+inset, cy-y+inset, high), (cx+x-inset, cy-y+inset, high),
             (cx+x-inset, cy+y-inset, high), (cx-x+inset, cy+y-inset, high)]
    mesh('Blue hipped pavilion roof', verts, [(0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)], M['teal'])
    for i in range(4):
        tube('Hipped roof brass arris', [verts[i], verts[i+4]], .036, M['brass'])
    # Standing seams run down all four slopes, not a texture that will vanish.
    for sign in (-1, 1):
        seam_count = 4 if lite() else 8
        for i in range(1, seam_count+1):
            xx = cx-x+width*i/(seam_count+1)
            tube('Pavilion folded seam', [(xx, cy+sign*y, low+.015),
                 (cx+(xx-cx)*(x-inset)/x, cy+sign*(y-inset), high+.015)], .018, M['bronze'])
        side_seams = 3 if lite() else 6
        for i in range(1, side_seams+1):
            yy = cy-y+depth*i/(side_seams+1)
            tube('Pavilion side folded seam', [(cx+sign*x, yy, low+.015),
                 (cx+sign*(x-inset), cy+(yy-cy)*(y-inset)/y, high+.015)], .018, M['bronze'])


def build_wing(sign):
    side = 'West' if sign < 0 else 'East'
    collection(('03' if sign < 0 else '04')+' | '+side+' wing')
    cx, cy = sign*8.35, .50
    width, depth = 5.70, 7.00
    # Wings meet the rotunda at x=5.5; no invisible overlap volumes.
    block(side+' foundation', (cx, cy, .43), (6.12, 7.42, .38), M['paving'], .065)
    block(side+' plinth', (cx, cy, .74), (5.88, 7.15, .28), M['sandstone'], .035)
    # Real arched windows on three exposed sides.
    for label, count, axis, face_pos, angle, span in [
            ('front', 2, 'x', cy-depth/2, 0, width),
            ('rear', 2, 'x', cy+depth/2, math.pi, width),
            ('outer', 3, 'y', cx+sign*width/2, sign*math.pi/2, depth)]:
        for i in range(count):
            offset = -span/2+span/count*(i+.5)
            parts = window_bay(span/count, .86, 5.45, 1.35, 1.40, 3.70)
            x = cx+offset if axis == 'x' else face_pos
            y = face_pos if axis == 'x' else cy+offset
            place_module(parts, x, y, angle, f'{side} {label} bay {i+1}')
    # Short inner return walls, mostly behind the central hall.
    block(side+' inner return', (cx-sign*width/2, cy+1.8, 3.10), (.28, 3.40, 4.48), M['ivory'])
    for yy in (cy-depth/2-.08, cy+depth/2+.08):
        for xx in (cx-width/2, cx, cx+width/2):
            column(side+' facade column', xx, yy, .89, 5.20, .22)
    # Low tiered cornice and a visibly shaped roof, not a flat slab.
    for z, w, d, h, mat in [(5.23, 5.94, 7.24, .18, M['ivory']),
                          (5.43, 6.16, 7.46, .20, M['ivory']),
                          (5.56, 6.19, 7.49, .06, M['brass'])]:
        block(side+' eaves moulding', (cx, cy, z), (w, d, h), mat, .025)
    hipped_roof(cx, cy, 6.13, 7.43, 5.61, 6.64)
    # Upper parapet with corner finials.
    for yy in (cy-2.77, cy+2.77):
        block(side+' upper parapet', (cx, yy, 6.80), (4.77, .19, .34), M['ivory'])
        block(side+' parapet coping', (cx, yy, 7.00), (4.94, .29, .10), M['paving'])
    for xx in (cx-2.20, cx+2.20):
        block(side+' upper side parapet', (xx, cy, 6.80), (.19, 5.36, .34), M['ivory'])
        for yy in (cy-2.77, cy+2.77):
            block(side+' rooftop pedestal', (xx, yy, 6.98), (.43, .43, .65), M['ivory'])
            lathe(side+' roof acorn', [(.13, 7.30), (.20, 7.41), (.12, 7.57), (.01, 7.69)], M['brass'], 10, (xx, yy, 0))
    compass(side+' roof compass', (cx, cy, 6.663), .80, M['brass'])


def build_entry():
    collection('05 | Entrance, stairs and banner piers')
    # 7 physically plausible 170 mm rises, 310 mm treads. Podium top = 1.43 m.
    # Plaza surface .24 m, stair rise 1.19 m. Door clear height 4.25 m.
    for i in range(7):
        h = .17*(i+1)
        front = -7.70+i*.31
        back = -5.12
        block(f'Entrance step {i+1:02} — 170 mm rise', (0, (front+back)/2, .24+h/2),
              (2.62, back-front, h), M['paving'], .018)
    # Raised side cheeks follow the staircase slope.
    for sign in (-1, 1):
        x, front, back = sign*1.50, -7.74, -5.23
        verts = [(x+dx, y, z) for dx in (-.13, .13)
                 for y, z in ((front, .24), (back, .24), (back, 1.55), (front, .38))]
        mesh('Solid stone stair cheek', verts,
             [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
              (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], M['paving'])
        pts = [(sign*1.50, -7.74, .38), (sign*1.50, -5.23, 1.55)]
        tube('Stair cheek coping', pts, .12, M['ivory'], 4)
    # Stone heraldic piers frame the doorway without obscuring the columns.
    for sign in (-1, 1):
        x, y = sign*2.05, -5.44
        lathe('Banner pier foot', [(.40, .24), (.43, .35), (.43, .48), (.34, .54)], M['paving'], 16, (x, y, 0))
        lathe('Banner pier', [(.33, .53), (.33, 1.96), (.40, 2.02), (.40, 2.16)], M['ivory'], 16, (x, y, 0))
        lathe('Banner pier cap', [(.35, 2.16), (.42, 2.23), (.30, 2.34), (.05, 2.46)], M['brass'], 12, (x, y, 0))
        hanging_banner(x, y-.35, .58, .69, 1.48)


def nla_action(owner, action, clip, active=False):
    owner.animation_data_create()
    owner.animation_data.action = None
    track = owner.animation_data.nla_tracks.new()
    track.name = clip
    strip = track.strips.new(clip, 1, action)
    strip.blend_type = 'REPLACE'
    strip.extrapolation = 'NOTHING'
    track.mute = not active


def animated_cloth(parts, name, wind):
    """One deformable object per fabric piece, including its attached decoration."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:
        obj.select_set(True)
    ASSET[:] = [p for p in ASSET if p not in parts]
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    ASSET.append(obj)
    obj['motion_group'] = name
    obj['cloth_loop_seconds'] = 4.0
    obj.shape_key_add(name='Basis')
    cosine = obj.shape_key_add(name='Wind_Cosine')
    plus = obj.shape_key_add(name='Wind_Sine_Positive')
    minus = obj.shape_key_add(name='Wind_Sine_Negative')
    for i, vertex in enumerate(obj.data.vertices):
        a, b, vertical = wind(vertex.co)
        cosine.data[i].co.y -= 2*a
        plus.data[i].co.y += b
        minus.data[i].co.y -= b
        plus.data[i].co.z -= vertical
        minus.data[i].co.z += vertical
    keys = obj.data.shape_keys
    action = bpy.data.actions.new(name+'__Wind')
    keys.animation_data_create()
    keys.animation_data.action = action
    for frame in range(1, 122, 5):
        angle = TAU*(frame-1)/60
        cosine.value = (1-math.cos(angle))/2
        plus.value = max(0, -math.sin(angle))
        minus.value = max(0, math.sin(angle))
        for key in (cosine, plus, minus):
            key.keyframe_insert(data_path='value', frame=frame)
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'
    nla_action(keys, action, 'Flags_Wind-loop')
    nla_action(keys, action, 'Hall_Demo-loop', active=True)
    for key in (cosine, plus, minus):
        key.value = 0
    return obj


def setup_door_rig():
    """Two real vertical hinges, with independently addressable rotation tracks."""
    col = bpy.data.collections['01 | Rotunda — twelve editable arch bays']
    for side, sign in [('L', -1), ('R', 1)]:
        hinge = bpy.data.objects.new('Door_Hinge_'+side, None)
        col.objects.link(hinge)
        hinge.location = (sign*.96, -5.17, 1.51)
        hinge.empty_display_type = 'ARROWS'
        hinge.empty_display_size = .25
        hinge['door_hinge'] = True
        bpy.context.view_layer.update()
        for obj in ASSET:
            if obj.get('motion_group') == 'Door_Leaf_'+side:
                matrix = obj.matrix_world.copy()
                obj.parent = hinge
                obj.matrix_world = matrix
        for clip, samples in [
                ('Doors_Open', [(1, 0), (31, 100)]),
                ('Doors_Close', [(1, 100), (31, 0)]),
                ('Hall_Demo-loop', [(1, 0), (31, 100), (61, 100), (91, 0), (121, 0)])]:
            action = bpy.data.actions.new('Door_'+side+'__'+clip)
            hinge.animation_data_create()
            hinge.animation_data.action = action
            for frame, degrees in samples:
                hinge.rotation_euler.z = sign*math.radians(degrees)
                hinge.keyframe_insert(data_path='rotation_euler', index=2, frame=frame)
            for curve in action.fcurves:
                for point in curve.keyframe_points:
                    point.handle_left_type = point.handle_right_type = 'AUTO_CLAMPED'
            nla_action(hinge, action, clip, active=clip == 'Hall_Demo-loop')
        hinge.rotation_euler.z = 0
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.frame_start, scene.frame_end = 1, 121
    scene.frame_set(1)


def hanging_banner(x, y, bottom, width, height):
    start = len(ASSET)
    p = [(-width/2, bottom+height), (-width/2, bottom),
         (0, bottom+.15), (width/2, bottom), (width/2, bottom+height)]
    cols, rows = (3, 3) if lite() else (4, 4)
    verts = [(x+(u-.5)*width, y, bottom+height-v*(height-.15*(1-abs(2*u-1))))
             for v in [j/rows for j in range(rows+1)] for u in [i/cols for i in range(cols+1)]]
    faces = [(j*(cols+1)+i, j*(cols+1)+i+1, (j+1)*(cols+1)+i+1, (j+1)*(cols+1)+i)
             for j in range(rows) for i in range(cols)]
    obj = mesh('Hanging blue heraldic pennant', verts, faces, M['fabric'], True)
    for a, b in zip(p, p[1:]+p[:1]):
        tube('Pennant stitched gold edging', [(x+a[0], y-.012, a[1]), (x+b[0], y-.012, b[1])], .014, M['brass'])
    compass('Pennant compass insignia', (x, y-.023, bottom+height*.58), width*.28, M['brass'], True)
    def wind(co):
        u = max(0, min(1, (co.x-x)/width+.5))
        v = max(0, min(1, (bottom+height-co.z)/(height-.15*(1-abs(2*u-1)))))
        return .055*v+.025*math.sin(math.pi*u)*math.sin(math.pi*v), \
               .035*v+.018*math.sin(TAU*u)*math.sin(math.pi*v), .012*v
    return animated_cloth(ASSET[start:], 'Flag_Entry_'+('L' if x < 0 else 'R'), wind)


def build_flags():
    collection('06 | Flags and decorative metalwork')
    # Roof flagpoles follow the reference's asymmetric flag arrangement, while
    # the architecture remains symmetrical. Three small morph targets animate
    # the existing wave; decorative hems and insignia deform with the cloth.
    for sign in (-1, 1):
        x, y, base = sign*8.55, 1.55, 6.65
        lathe('Flagpole stepped socket', [(.36, 0), (.36, .14), (.25, .20), (.22, .43)], M['brass'], 16, (x, y, base))
        lathe('Bronze flagpole', [(.083, .38), (.065, 5.05)], M['bronze'], 12, (x, y, base))
        for z in (.58, 3.08, 4.90):
            lathe('Flagpole brass collar', [(.112, z), (.112, z+.10)], M['brass'], 12, (x, y, base))
        lathe('Flagpole spear', [(.07, 5.08), (.18, 5.30), (.075, 5.58), (.001, 5.70)], M['brass'], 10, (x, y, base))
        start = len(ASSET)
        # Cloth runs toward the outer wing; total span stays within the plaza.
        w, h = 2.30, 1.38
        cols, rows = (8, 4) if lite() else (12, 6)
        def flag_point(u, v, behind=0):
            xx = x+sign*(.09+w*u)
            yy = y-.12+.22*math.sin(u*math.pi*2.3-v*.8)*u+behind
            zz = base+4.89-h*v-.28*u+.09*math.sin(u*math.pi)*v
            return xx, yy, zz
        verts = [flag_point(i/cols, j/rows) for j in range(rows+1) for i in range(cols+1)]
        faces = [(j*(cols+1)+i, j*(cols+1)+i+1,
                  (j+1)*(cols+1)+i+1, (j+1)*(cols+1)+i)
                 for j in range(rows) for i in range(cols)]
        mesh('Waving blue roof flag', verts, faces, M['fabric'], True)
        for v in (0, 1):
            tube('Flag brass hem', [flag_point(i/cols, v, -.012) for i in range(cols+1)], .018, M['brass'])
        tube('Flag fly hem', [flag_point(1, j/rows, -.012) for j in range(rows+1)], .018, M['brass'])
        # Compass emblem follows the same surface as the cloth (no floating decal).
        center_u, center_v = .53, .47
        verts = [flag_point(center_u, center_v, -.018)]
        for i in range(16):
            a = i*TAU/16
            r = .33 if i%2 == 0 else .095
            verts.append(flag_point(center_u+math.sin(a)*r/w, center_v+math.cos(a)*r/h, -.018))
        mesh('Roof flag compass insignia', verts, [(0, 1+i, 1+(i+1)%16) for i in range(16)], M['brass'])
        def wind(co):
            u = max(0, min(1, (sign*(co.x-x)-.09)/w))
            v = max(0, min(1, (base+4.89-.28*u-co.z)/(h-.09*math.sin(u*math.pi))))
            phase = u*math.pi*2.3-v*.8
            return .22*u*math.sin(phase), .22*u*math.cos(phase), .035*u*v
        animated_cloth(ASSET[start:], 'Flag_Roof_'+('L' if sign < 0 else 'R'), wind)


def build_plaza():
    collection('07 | Optional entrance platform — remove independently')
    outline = [(-11.95, -5.0), (-10.7, -7.2), (-7.7, -8.0),
               (-5.0, -9.5), (5.0, -9.5), (7.7, -8.0), (10.7, -7.2),
               (11.95, -5.0), (11.95, 6.4), (-11.95, 6.4)]
    prism('Shaped pale stone entrance platform', outline, 0, .24, M['paving'], .055)
    # Retain the iconic compass and plaza; omit tiny stone joints in the LOD.
    for x in (() if lite() else (-3.5, 3.5)):
        block('Forecourt inset paving', (x, -7.70, .245), (2.30, 2.6, .012), M['paving_alt'], .025)
    for y in (() if lite() else (-8.95, -8.30, -7.65)):
        tube('Paving joint', [(-4.7, y, .251), (4.7, y, .251)], .009, M['sandstone'])
    for x in (() if lite() else (-4.65, -2.35, 2.35, 4.65)):
        tube('Paving joint', [(x, -9.1, .251), (x, -6.8, .251)], .009, M['sandstone'])
    # Simplified reference compass, placed in front of the steps.
    x, y = 0, -8.47
    lathe('Forecourt compass blue inset', [(1.02, .245), (1.02, .258)], M['teal'], 36, (x, y, 0))
    for r in ((.86,) if lite() else (.86, 1.04)):
        pts = [(x+r*math.sin(TAU*i/32), y+r*math.cos(TAU*i/32), .266) for i in range(33)]
        tube('Forecourt compass brass circle', pts, .022, M['brass'])
    compass('Forecourt compass rose', (x, y, .275), .84, M['brass'])


def make_materials():
    specs = {
        'ivory': ('Warm ivory limestone', (.76, .685, .535), .82, 0),
        'sandstone': ('Recessed warm sandstone', (.43, .36, .265), .90, 0),
        'teal': ('Deep petrol blue metal roofing', (.018, .115, .175), .39, .73),
        'brass': ('Restrained aged brass', (.58, .335, .105), .36, .80),
        'bronze': ('Dark bronze window frames', (.14, .101, .057), .43, .72),
        'glass': ('Semi transparent blue tinted glass', (.058, .205, .27), .19, .12),
        'door': ('Deep blue painted entrance doors', (.018, .062, .10), .51, .12),
        'fabric': ('Woven blue banner fabric', (.022, .108, .185), .91, 0),
        'paving': ('Pale limestone steps and platform', (.68, .61, .49), .87, 0),
        'paving_alt': ('Subtle paving stone variation', (.60, .535, .42), .89, 0),
        'shadow': ('Unlit interior shadow', (.011, .024, .029), .98, 0),
    }
    for key, (name, color, roughness, metallic) in specs.items():
        mat = material(name, color, roughness)
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Metallic'].default_value = metallic
        mat.metallic = metallic
        mat.roughness = roughness
        M[key] = mat
    glass = M['glass']
    # Core glTF alpha blending works in Godot Compatibility. No transmission
    # extension, refraction, screen-space textures or Blender-only shader graph.
    glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = .63
    glass.diffuse_color = (*glass.diffuse_color[:3], .63)
    glass.surface_render_method = 'BLENDED'
    glass.use_backface_culling = False
    M['fabric'].use_backface_culling = False
    M['brass'].use_backface_culling = False  # Single-surface cloth insignia.
    for key in ('ivory', 'paving', 'teal', 'door', 'bronze', 'shadow', 'sandstone', 'paving_alt'):
        M[key].use_backface_culling = True


def uv_and_normals():
    # Stable box-projected UV0 on every unique mesh, including linked modules.
    # These are an editable starting point for texturing, not a lightmap atlas.
    for data in {o.data for o in ASSET}:
        layer = data.uv_layers.new(name='Architectural metres')
        for p in data.polygons:
            major = max(range(3), key=lambda j: abs(p.normal[j]))
            axes = ((1, 2), (0, 2), (0, 1))[major]
            for li in p.loop_indices:
                co = data.vertices[data.loops[li].vertex_index].co
                layer.data[li].uv = (co[axes[0]]*.25, co[axes[1]]*.25)


def configure_studio():
    collection('STUDIO | Cameras and CPU lighting — excluded from GLB')
    # A neutral studio ground is a presentation aid, outside the asset export.
    ground = cube('Studio ground — presentation only', (0, 0, -.16), (200, 200, .20),
                  material('Studio warm grey', (.225, .245, .255), .95), .01)
    for owner in list(ground.users_collection):
        owner.objects.unlink(ground)
    COL.objects.link(ground)
    ground.hide_select = True
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = 1500, 1300
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.world = bpy.data.worlds.new('Neutral studio world')
    scene.world.color = (.35, .35, .35)
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (.52, .62, .72, 1)
    bg.inputs['Strength'].default_value = .65
    scene.view_settings.view_transform = 'AgX'
    for name, pos, power, size, color in [
            ('Large warm key', (-12, -15, 24), 5800, 12, (1, .88, .72)),
            ('Cool frontal fill', (12, -8, 16), 3100, 10, (.70, .84, 1)),
            ('Dome rim light', (0, 12, 23), 6600, 9, (1, .91, .77))]:
        bpy.ops.object.light_add(type='AREA', location=pos)
        obj = bpy.context.object
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        COL.objects.link(obj)
        obj.name = name
        obj.data.energy, obj.data.size, obj.data.color = power, size, color
        obj.rotation_euler = (Vector((0, 0, 7))-obj.location).to_track_quat('-Z', 'Y').to_euler()
    cameras = {}
    for name, pos, target, scale in [
            ('hero', (27, -36, 25), (0, -.7, 7.0), 29.5),
            ('front', (0, -42, 22), (0, -.9, 7.0), 28.5),
            ('rear', (-27, 31, 23), (0, -.1, 7.0), 29.5),
            ('detail', (10, -20, 11), (0, -3.2, 4.8), 15.0)]:
        bpy.ops.object.camera_add(location=pos)
        cam = bpy.context.object
        for owner in list(cam.users_collection):
            owner.objects.unlink(cam)
        COL.objects.link(cam)
        cam.name = 'Review camera | '+name
        cam.rotation_euler = (Vector(target)-cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.type, cam.data.ortho_scale = 'ORTHO', scale
        cam.data.lens = 50
        cameras[name] = cam
    scene.camera = cameras['hero']
    # Open the blend with useful material preview framing, rather than the cube view.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.clip_end = 500
                area.spaces.active.shading.type = 'MATERIAL'
    return cameras


def export_runtime(path):
    """Batch static architecture and each rigid leaf separately; preserve cloth
    morphs, hinge hierarchy and four named NLA clips on temporary export copies.
    """
    import bmesh
    scene = bpy.context.scene
    scene.frame_set(1)
    export_col = bpy.data.collections.new('TEMP | Runtime export')
    scene.collection.children.link(export_col)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    batches = defaultdict(list)
    cloth = []
    for obj in ASSET:
        if obj.data.shape_keys:
            cloth.append(obj)
        else:
            if len(obj.data.materials) != 1:
                raise ValueError('Keep one material per rigid authoring part: '+obj.name)
            batches[(obj.data.materials[0], obj.get('motion_group', ''))].append(obj)
    runtime, renamed, hinges = [], [], {}
    section_stats = defaultdict(int)
    source_triangles = 0
    for obj in ASSET:
        evaluated = obj.evaluated_get(depsgraph)
        data = evaluated.to_mesh()
        data.calc_loop_triangles()
        count = len(data.loop_triangles)
        source_triangles += count
        section_stats[obj.users_collection[0].name] += count
        evaluated.to_mesh_clear()

    def clone_animated(source):
        name = source.name
        source.name = name+'__authoring'
        renamed.append((source, name))
        obj = source.copy()
        if source.type == 'MESH':
            obj.data = source.data.copy()
        obj.name = name
        export_col.objects.link(obj)
        runtime.append(obj)
        return obj

    for source in sorted({o.parent for o in ASSET if o.parent and o.parent.get('door_hinge')}, key=lambda o: o.name):
        hinges[source] = clone_animated(source)
    for source in cloth:
        clone_animated(source)
    for (mat, group), objects in batches.items():
        parent = objects[0].parent if group else None
        local_from_world = parent.matrix_world.inverted() if parent else None
        verts, faces, uvs, smooth = [], [], [], []
        for source in objects:
            evaluated = source.evaluated_get(depsgraph)
            data = evaluated.to_mesh()
            offset = len(verts)
            transform = local_from_world @ source.matrix_world if parent else source.matrix_world
            verts += [transform@v.co for v in data.vertices]
            for face in data.polygons:
                faces.append(tuple(offset+i for i in face.vertices))
                smooth.append(face.use_smooth)
                uvs.append([tuple(data.uv_layers.active.data[li].uv) for li in face.loop_indices])
            evaluated.to_mesh_clear()
        data = bpy.data.meshes.new((group or 'Static')+' | '+mat.name)
        data.from_pydata(verts, [], faces)
        data.materials.append(mat)
        data.update()
        uv = data.uv_layers.new(name='UVMap')
        for face, coords, sm in zip(data.polygons, uvs, smooth):
            face.use_smooth = sm
            for li, coord in zip(face.loop_indices, coords):
                uv.data[li].uv = coord
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(data)
        bm.free()
        obj = bpy.data.objects.new((group or 'Static')+'__'+mat.name, data)
        export_col.objects.link(obj)
        if parent:
            obj.parent = hinges[parent]
        runtime.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in runtime:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(o for o in runtime if o.type == 'MESH')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB',
                              use_selection=True, export_apply=False,
                              export_cameras=False, export_lights=False,
                              export_extras=True, export_yup=True,
                              export_materials='EXPORT', export_texcoords=True,
                              export_animations=True, export_animation_mode='NLA_TRACKS',
                              export_anim_slide_to_zero=True, export_morph=True,
                              export_morph_normal=True, export_morph_animation=True)
    mesh_count = sum(o.type == 'MESH' for o in runtime)
    for obj in reversed(runtime):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
    for source, name in renamed:
        source.name = name
    bpy.data.collections.remove(export_col)
    bpy.ops.object.select_all(action='DESELECT')
    scene.frame_set(1)
    return {'source_triangles': source_triangles,
            'source_mesh_objects': len(ASSET),
            'unique_source_meshes': len({o.data for o in ASSET}),
            'runtime_meshes': mesh_count,
            'material_count': len(M), 'section_triangles': dict(section_stats),
            'animated_door_hinges': 2, 'animated_fabric_objects': len(cloth),
            'animation_clips': ['Doors_Open', 'Doors_Close', 'Flags_Wind-loop', 'Hall_Demo-loop'],
            'wind_loop_seconds': 4.0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    global QUALITY
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--quality', choices=('full', 'lite'), default='full',
                        help='Full V2 reference or lower-detail mobile experimental model')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--views', nargs='+', default=['hero', 'front', 'rear', 'detail'])
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    QUALITY = args.quality
    out = args.output_dir.resolve() if args.output_dir else ROOT/('blender/generated/settlements_hall_lite' if lite() else 'blender/generated/settlements_hall')
    glb = out/'settlements_hall.glb' if (args.output_dir or lite()) else ROOT/'godot/assets/generated/settlements_hall.glb'
    out.mkdir(parents=True, exist_ok=True)
    glb.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    make_materials()
    build_rotunda()
    build_crown()
    build_wing(-1)
    build_wing(1)
    build_entry()
    build_flags()
    build_plaza()
    setup_door_rig()
    uv_and_normals()
    bpy.context.view_layer.update()
    stats = export_runtime(glb)
    corners = [o.matrix_world@Vector(c) for o in ASSET for c in o.bound_box]
    stats['dimensions_metres'] = [round(max(v[j] for v in corners)-min(v[j] for v in corners), 3) for j in range(3)]
    stats['quality_preset'] = QUALITY
    stats['blender_version'] = bpy.app.version_string
    stats['front_axis_blender'] = '-Y'
    stats['front_axis_godot'] = '+Z'
    stats['origin'] = 'Ground plane, centre of circular hall'
    stats['stair_rise_metres'] = .17
    stats['stair_tread_metres'] = .31
    stats['door_clear_width_metres'] = 1.99
    stats['door_clear_height_metres'] = 2.645
    stats['entrance_arch_height_metres'] = 4.155
    stats['notes'] = 'Exterior landmark; no navigable interior. Hinged doors and four morph-animated fabric pieces. Core glTF PBR; no external dependencies.'
    (out/'asset_stats.json').write_text(json.dumps(stats, indent=2)+'\n')
    cameras = configure_studio()
    scene['asset'] = 'TELANICO | Settlements Hall'
    scene['asset_notes'] = stats['notes']
    scene['units'] = '1 Blender unit = 1 metre; 1.8 m adult reference scale'
    scene['regenerate'] = ('blender -b --python blender/scripts/build_settlements_hall.py -- --quality '+QUALITY+' --render')
    scene['runtime_export'] = 'Static material batches plus separate hinged leaves and four morph-animated fabric pieces'
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'settlements_hall.blend'))
    print('SETTLEMENTS_HALL_STATS '+json.dumps(stats), flush=True)
    if args.render:
        for view in args.views:
            scene.render.resolution_percentage = 100 if view == 'hero' else 75
            scene.cycles.samples = 64 if view == 'hero' else 32
            scene.camera = cameras[view]
            scene.render.filepath = str(out/(view+'.png'))
            bpy.ops.render.render(write_still=True)
    print('SETTLEMENTS_HALL_OK '+str(out), flush=True)


if __name__ == '__main__':
    main()
