"""Check overworld layout invariants and its illustrative travel calibration."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'blender/scripts'))
from overworld_layout import ISLANDS, LANDMARKS, NODES, ROUTES


def inside(point, polygon):
    x,y=point
    result=False
    for (ax,ay),(bx,by) in zip(polygon,polygon[1:]+polygon[:1]):
        if (ay>y)!=(by>y) and x < (bx-ax)*(y-ay)/(by-ay)+ax:
            result=not result
    return result


def validate():
    report=json.loads((ROOT/'blender/generated/overworld_layout.json').read_text())
    expected_west={'Settlements Hall','Trade Finance','Compliance','LC Desk','Coffee Area',
                   'West Tube Station','West Harbor Launch'}
    expected_east={'Operations','Contracts','VAT Tax','FX Desk','Archive Rotunda',
                   'East Tube Station','East Harbor Launch'}
    for side,names in [('west',expected_west),('east',expected_east)]:
        assert {n for n,v in LANDMARKS.items() if v[0]==side}==names
        for name in names:
            _,kind,x,y,z=LANDMARKS[name]
            if kind!='dock': assert inside((x,y),ISLANDS[side.title()]), name
            assert report['landmarks'][name]['position']==[x,y,z]
    bridges=[r for r in ROUTES if r[3]=='bridge']
    assert len(bridges)==1, 'Exactly one pedestrian bridge'
    assert bridges[0][1:3]==('bridge_west','bridge_east')
    for key in ['west_dock','east_dock']:
        x,y,_=NODES[key]
        assert abs(x)<7 and abs(y)<3, 'Main docks belong in the central channel'
    assert LANDMARKS['West Tube Station'][1]==LANDMARKS['East Tube Station'][1]=='tube'
    assert set(r[3] for r in ROUTES)=={'primary','secondary','trail','bridge'}
    for name,a,b,kind,_ in ROUTES:
        # Every land route stays on its assigned side; the bridge alone spans water.
        if kind!='bridge': assert NODES[a][0]*NODES[b][0]>0, name
    times=report['representative_walk_minutes']
    for key,lo,hi in [('Hall to Compliance',4,6),('Hall to LC Desk',8,12),
        ('LC Desk to Trade Finance',12,18),('Operations to VAT Tax',8,12),
        ('Archive to FX Desk',12,18),('Civic hub to civic hub via bridge',15,20),
        ('Central dock to central dock via bridge',15,20)]:
        assert lo<=times[key]<=hi, (key,times[key])
    assert 6<=report['transfer_estimates']['boat_dock_to_dock_minutes']<=8
    assert report['transfer_estimates']['tube_station_to_station_minutes']<6
    assert times['Central dock to central dock via bridge'] > 2*report['transfer_estimates']['boat_dock_to_dock_minutes']
    assert len(report['routes'])==len(ROUTES)
    adjacency={node:set() for node in NODES}
    for _,a,b,_,_ in ROUTES:
        adjacency[a].add(b);adjacency[b].add(a)
    seen=set();pending=['west_hub']
    while pending:
        current=pending.pop()
        if current not in seen:
            seen.add(current);pending.extend(adjacency[current]-seen)
    assert seen==set(NODES), 'Every approach must connect to the walking graph'
    print('LAYOUT_OK: west/east assignments, central docks, one bridge, matching tubes, travel bands')


if __name__=='__main__': validate()
