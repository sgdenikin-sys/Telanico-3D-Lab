"""World-space blockout plan (Blender XY, Z up), independent of bpy.

Travel costs are design estimates, not gameplay or quest implementation.
"""
WALK_MINUTES_PER_UNIT = 0.36
GROUND = 1.45
LANDMARKS = {
    'Settlements Hall': ('west', 'hall', -22, 6, GROUND),
    'Trade Finance': ('west', 'trade', -26, -6, GROUND),
    'Compliance': ('west', 'compliance', -12, 0, GROUND),
    'LC Desk': ('west', 'lc', -25, 15, 2.25),
    'Coffee Area': ('west', 'coffee', -21, -15, GROUND),
    'West Tube Station': ('west', 'tube', -10, -8, GROUND),
    'West Harbor Launch': ('west', 'dock', -6, 0, GROUND),
    'Operations': ('east', 'operations', 23, 7, GROUND),
    'Contracts': ('east', 'contracts', 12, 15, GROUND),
    'VAT Tax': ('east', 'tax', 28, -4, GROUND),
    'FX Desk': ('east', 'fx', 21, -17, 2.15),
    'Archive Rotunda': ('east', 'archive', 28, 16, 2.25),
    'East Tube Station': ('east', 'tube', 10, -8, GROUND),
    'East Harbor Launch': ('east', 'dock', 6, 0, GROUND),
}
ISLANDS = {
    'West': [(-32,-15),(-29,-21),(-18,-22),(-8,-18),(-6,-9),(-7,3),
             (-5,14),(-10,21),(-23,23),(-31,17),(-34,4),(-33,-6)],
    'East': [(6,-15),(10,-21),(24,-23),(32,-17),(34,-3),(32,8),
             (34,15),(26,23),(13,23),(7,17),(5,9),(7,0)],
}
NODES = {
    'west_hub': (-16,2,GROUND), 'west_north': (-12,9,GROUND),
    'west_lc_junction': (-13,14,GROUND), 'west_south': (-16,-8,GROUND),
    'hall': (-22,3.4,GROUND), 'trade': (-26,-8.4,GROUND),
    'compliance': (-12,-2.0,GROUND), 'lc': (-25,12.5,2.25),
    'coffee': (-21,-16.6,GROUND), 'west_tube': (-10,-10,GROUND),
    'west_dock': (-4.5,0,GROUND), 'bridge_west': (-6,11.5,GROUND),
    'bridge_east': (6,11.5,GROUND), 'east_hub': (17,1,GROUND),
    'east_north': (17,10,GROUND), 'east_south': (18,-8,GROUND),
    'operations': (23,4.3,GROUND), 'contracts': (12,12.5,GROUND),
    'tax': (28,-6.4,GROUND), 'fx': (21,-19,2.15),
    'archive': (28,12.5,2.25), 'east_tube': (10,-10,GROUND),
    'east_dock': (4.5,0,GROUND),
}
# name, from, to, route hierarchy, intermediate ramp / turn points
ROUTES = [
    ('West civic promenade','west_hub','west_north','primary',[]),
    ('West upper promenade','west_north','west_lc_junction','primary',[]),
    ('West south promenade','west_hub','west_south','primary',[]),
    ('Hall forecourt','west_hub','hall','primary',[]),
    ('Trade approach','west_south','trade','secondary',[(-26,-9,GROUND)]),
    ('Compliance approach','west_hub','compliance','secondary',[(-16,-3,GROUND),(-12,-3,GROUND)]),
    ('LC terrace ramp','west_lc_junction','lc','secondary',[(-19,11,GROUND)]),
    ('Coffee garden walk','west_south','coffee','secondary',[(-16,-14,GROUND)]),
    ('West tube approach','west_south','west_tube','secondary',[(-13,-10,GROUND)]),
    ('West harbor promenade','west_hub','west_dock','primary',[(-10,5,GROUND),(-7,1,GROUND)]),
    ('West bridge approach','west_north','bridge_west','primary',[]),
    ('Pedestrian bridge','bridge_west','bridge_east','bridge',[(0,11.5,2.15)]),
    ('East bridge approach','bridge_east','east_north','primary',[(8,10,GROUND)]),
    ('East civic promenade','east_hub','east_north','primary',[]),
    ('East south promenade','east_hub','east_south','primary',[]),
    ('Operations forecourt','east_hub','operations','primary',[]),
    ('Contracts approach','east_north','contracts','secondary',[(12,11,GROUND)]),
    ('Archive ramp','east_north','archive','secondary',[(19,13,GROUND),(23,12,GROUND)]),
    ('VAT approach','east_south','tax','secondary',[(28,-8,GROUND)]),
    ('FX southern ramp','east_south','fx','secondary',[(16,-14,GROUND),(18,-19,2.15)]),
    ('East tube approach','east_south','east_tube','secondary',[(13,-10,GROUND)]),
    ('East harbor promenade','east_hub','east_dock','primary',[(10,4,GROUND),(7,1,GROUND)]),
    ('West garden shortcut','trade','coffee','trail',[(-28,-13,GROUND)]),
    ('East meadow shortcut','tax','fx','trail',[(28,-12,GROUND),(25,-18,2.15)]),
]
