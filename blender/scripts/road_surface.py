"""One connected, terrain-conforming road surface; route samples remain authoritative."""
import math
import bpy
from mathutils import Vector

def build(edges,layout,stone,dirt):
    buckets={}
    for edge in edges:
        if edge['kind']=='bridge':continue
        radius={'main':1.45,'stone':1.05,'trail':.72}[edge['kind']]
        for a,b in zip(edge['points'],edge['points'][1:]):
            record=(a,b,radius,edge['kind']=='trail')
            for i in range(math.floor((min(a[0],b[0])-radius-1)/8),math.floor((max(a[0],b[0])+radius+1)/8)+1):
                for j in range(math.floor((min(a[1],b[1])-radius-1)/8),math.floor((max(a[1],b[1])+radius+1)/8)+1):buckets.setdefault((i,j),[]).append(record)
    def field(x,y):
        best=99;kind=False
        for a,b,r,d in buckets.get((math.floor(x/8),math.floor(y/8)),[]):
            dx,dy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/max(dx*dx+dy*dy,.00001)))
            distance=math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)-r
            if distance<best:best,kind=distance,d
        return best,kind
    from mathutils.bvhtree import BVHTree
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get()
    terrain={side:BVHTree.FromObject(bpy.data.objects[side+' Island Terrain'],dg) for side in ('west','east')}
    vertices=[];faces=[];materials=[];lookup={};step=.45
    def vert(p):
        key=(round(p[0],5),round(p[1],5))
        if key not in lookup:
            lookup[key]=len(vertices)
            hit,_,_,_=terrain['west' if key[0]<0 else 'east'].ray_cast(Vector((*key,100)),Vector((0,0,-1)))
            z=max(layout.height(*key),hit.z if hit is not None else -100)+.14
            vertices.append((*key,z))
        return lookup[key]
    for i in range(-200,201):
        for j in range(-145,146):
            x,y=i*step,j*step
            if (math.floor(x/8),math.floor(y/8)) not in buckets:continue
            points=[(x,y),(x+step,y),(x+step,y+step),(x,y+step)]
            values=[field(*p)[0] for p in points]
            for tri in [(0,1,2),(0,2,3)]:
                polygon=[]
                for a,b in zip(tri,tri[1:]+tri[:1]):
                    if values[a]<=0:polygon.append(points[a])
                    if (values[a]<=0)!=(values[b]<=0):
                        t=values[a]/(values[a]-values[b]);polygon.append(tuple(points[a][k]+t*(points[b][k]-points[a][k]) for k in range(2)))
                if len(polygon)>=3:
                    faces.append(tuple(vert(p) for p in polygon));centre=tuple(sum(p[k] for p in polygon)/len(polygon) for k in range(2));materials.append(int(field(*centre)[1]))
    mesh=bpy.data.meshes.new('Unified road paving');mesh.from_pydata(vertices,[],faces);mesh.materials.append(stone);mesh.materials.append(dirt);mesh.update()
    obj=bpy.data.objects.new('Path WalkSurface unified paving',mesh);bpy.context.collection.objects.link(obj)
    uv=mesh.uv_layers.new(name='World metres');colors=mesh.color_attributes.new(name='EdgeTint',type='FLOAT_COLOR',domain='CORNER')
    for face,material in zip(mesh.polygons,materials):
        face.material_index=material;face.use_smooth=True
        for li in face.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=(v.x/3.2,v.y/3.2)
            distance=field(v.x,v.y)[0];t=max(0,min(1,-distance/.3));colors.data[li].color=(.78+.22*t,.77+.23*t,.73+.27*t,1)
    return obj
