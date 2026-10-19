"""Canonical pilot correspondence, physical terrain and constrained path network.

Blender metres, XY ground; Godot export rotates Z-up to Y-up. Walk costs derive
from physical route length and the pilot's 1.5 units/min at a 6.25x pilot scale.
"""
import math
import heapq

PILOT_SCALE=6.25
WALK_UNITS_PER_MINUTE=1.5*PILOT_SCALE
REAL_SECONDS_PER_STORY_MINUTE=3.0
# id, name, island, model, centre XY, permitted building footprint, kind
SITES=[
 ('settlements','Settlements Hall','west','castle',(-63,24),(14,12),'office'),
 ('operations','Operations','west','barracks',(-30,-19),(14,10),'office'),
 ('finance','Trade Finance','west','home_B',(-48,34),(9,8),'office'),
 ('lc','LC Desk','west','home_A',(-55,-25),(10,7),'office'),
 ('compliance','Compliance Annex','west','blacksmith',(-24,21),(9,9),'office'),
 ('coffee','Coffee Area','west','market',(-72,-4),(7,5),'office'),
 ('tube_w','West Pneumatic Station','west','tube',(-72,-33),(8,8),'tube'),
 ('dock_w','West Harbor Launch','west','dock',(-16,0),(12,8),'boat'),
 ('trader','Trader · Eagle','east','tavern',(59,24),(13,11),'office'),
 ('contracts','Contracts','east','archeryrange',(32,29),(11,9),'office'),
 ('vat','VAT / Tax','east','home_A',(49,-18),(10,9),'office'),
 ('fx','FX Desk','east','tower_A',(71,-35),(9,9),'office'),
 ('archive','Archive Rotunda','east','tower_B',(74,2),(12,12),'office'),
 ('tube_e','East Pneumatic Station','east','tube',(76,39),(8,8),'tube'),
 ('dock_e','East Harbor Launch','east','dock',(16,0),(12,8),'boat'),
]
POLYGONS={
 'west':[(x*2.5,y*2.5) for x,y in [(-32,-15),(-29,-21),(-18,-22),(-8,-18),(-6,-9),(-7,3),(-5,14),(-10,21),(-23,23),(-31,17),(-34,4),(-33,-6)]],
 'east':[(x*2.5,y*2.5) for x,y in [(6,-15),(10,-21),(24,-23),(32,-17),(34,-3),(32,8),(34,15),(26,23),(13,23),(7,17),(5,9),(7,0)]],
}

def inside(x,y,side):
    poly=POLYGONS[side];result=False
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:result=not result
    return result

def base_height(x,y):
    h=2.2+.35*math.sin(x*.065)*math.cos(y*.07)
    for cx,cy,amp,r in [(-71,23,5.4,17),(67,34,5.8,18),(71,-32,3.6,15)]:
        h+=amp*math.exp(-((x-cx)**2+(y-cy)**2)/(r*r))
    return h

def height(x,y):
    h=base_height(x,y)
    for _,_,_,_,(cx,cy),(w,d),kind in SITES:
        if kind=='boat':continue
        distance=max(abs(x-cx)-w/2-1.2,abs(y-cy)-d/2-1.2,0)
        if distance<10:
            t=min(1,distance/10);t=t*t*(3-2*t)
            h=base_height(cx,cy)*(1-t)+h*t
    return h

def xyz(x,y):return (x,y,height(x,y)+.24)

NODES={name:xyz(x,y) for name,(x,y) in {
 'w_hub':(-38,10),'w_civic':(-48,12),'w_south':(-48,-12),'w_dispatch':(-39,-7),
 'w_north':(-38,40),'w_shore':(-24,34),'bridge_w':(-20.5,43),
 'bridge_e':(20.5,43),'e_shore':(22,35),'e_hub':(38,10),
 'e_south':(40,-8),'e_southern':(56,-30),'e_market':(60,8),'e_outer':(64,34),
}.items()}
for ident,_,_,_,(x,y),(w,d),kind in SITES:
    NODES[ident]=xyz(x,y-d/2-2.5) if kind!='boat' else xyz(x,y)
NODES['bridge_w']=xyz(-20.5,43);NODES['bridge_e']=xyz(20.5,43)
# Each edge is authored outside building rectangles. Sampling is shared by the
# terrain generator, route-cost calculation and runtime walking controller.
EDGES=[
 ('w_hub','w_civic',[], 'main'),('w_civic','settlements',[(-63,12)],'main'),
 ('w_civic','finance',[],'stone'),('w_hub','compliance',[(-24,10)],'stone'),
 ('w_civic','w_south',[],'main'),('w_south','lc',[(-64,-12),(-64,-31)],'stone'),
 ('w_south','coffee',[(-65,-12),(-72,-9)],'trail'),
 ('w_south','w_dispatch',[],'main'),('w_dispatch','operations',[(-39,-28),(-30,-28)],'main'),
 ('lc','tube_w',[(-65,-32),(-66,-40),(-72,-40)],'stone'),
 ('w_hub','dock_w',[(-23,6)],'main'),
 ('w_hub','w_north',[(-38,30)],'main'),('w_north','w_shore',[(-21,40)],'stone'),
 ('dock_w','w_shore',[(-18,6),(-17.5,15),(-17.5,28)],'stone'),
 ('w_shore','bridge_w',[(-24,43)],'main'),
 ('bridge_w','bridge_e',[(0,43)],'bridge'),
 ('bridge_e','e_shore',[(22,43)],'main'),
 ('e_shore','e_hub',[(22,15)],'main'),
 ('e_shore','contracts',[(25,20),(32,20)],'stone'),
 ('e_hub','dock_e',[(23,6)],'main'),('dock_e','e_shore',[(21,6),(21,18)],'stone'),
 ('e_hub','e_south',[],'main'),('e_hub','e_market',[],'main'),
 ('e_market','trader',[(59,14)],'main'),
 ('e_market','archive',[(66,-8),(74,-8)],'stone'),
 ('e_south','vat',[(40,-27),(49,-27)],'stone'),
 ('e_south','e_southern',[(37,-30)],'main'),
 ('e_southern','fx',[(56,-43),(71,-43)],'stone'),
 ('e_market','e_outer',[(67,10),(67,34)],'stone'),
 ('e_outer','tube_e',[(76,32)],'main'),
 ('contracts','e_outer',[(42,22),(47,35),(64,35)],'trail'),
]

def sample_edge(a,b,via,kind):
    raw=[NODES[a][:2],*via,NODES[b][:2]]
    points=[raw[0]]
    for point in raw[1:]:
        if math.dist(point,points[-1])>.01:points.append(point)
    # Quadratic rounded corners, followed by <=1.5 m linear samples.
    smooth=[points[0]]
    for i in range(1,len(points)-1):
        p,q,r=points[i-1:i+2]
        d1=math.dist(p,q);d2=math.dist(q,r);radius=min(2,d1*.2,d2*.2)
        u=tuple(q[j]+(p[j]-q[j])*radius/d1 for j in range(2))
        v=tuple(q[j]+(r[j]-q[j])*radius/d2 for j in range(2))
        smooth.append(u)
        for k in range(1,6):
            t=k/5;smooth.append(tuple((1-t)**2*u[j]+2*t*(1-t)*q[j]+t*t*v[j] for j in range(2)))
    smooth.append(points[-1]);sampled=[]
    for p,q in zip(smooth,smooth[1:]):
        n=max(1,math.ceil(math.dist(p,q)/1.5))
        for k in range(n):
            t=k/n;x=p[0]+(q[0]-p[0])*t;y=p[1]+(q[1]-p[1])*t
            t=(x-NODES[a][0])/(NODES[b][0]-NODES[a][0]) if kind=='bridge' else 0
            z=NODES[a][2]*(1-t)+NODES[b][2]*t+3.2*math.sin(math.pi*t) if kind=='bridge' else height(x,y)+.24
            sampled.append((x,y,z))
    sampled.append(NODES[b]);sampled[0]=NODES[a]
    return sampled

def route_data():
    return [dict(a=a,b=b,kind=k,points=sample_edge(a,b,v,k)) for a,b,v,k in EDGES]

def shortest(a,b,mode='walk'):
    adjacency={n:[] for n in NODES}
    for edge in route_data():
        length=sum(math.dist(p,q) for p,q in zip(edge['points'],edge['points'][1:]));cost=length/WALK_UNITS_PER_MINUTE
        adjacency[edge['a']].append((edge['b'],cost));adjacency[edge['b']].append((edge['a'],cost))
    if mode!='walk':
        u,v,cost=('dock_w','dock_e',5) if mode=='boat' else ('tube_w','tube_e',3)
        adjacency[u].append((v,cost));adjacency[v].append((u,cost))
    queue=[(0,a)];seen=set()
    while queue:
        cost,node=heapq.heappop(queue)
        if node==b:return round(cost,2)
        if node in seen:continue
        seen.add(node)
        for other,extra in adjacency[node]:heapq.heappush(queue,(cost+extra,other))
    raise ValueError('Disconnected route')
