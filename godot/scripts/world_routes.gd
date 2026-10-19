extends RefCounted
## Constrained navigation on proven, physically sampled walk surfaces.
## Every edge comes from the same geometry that builds the visible promenades.
var nodes: Dictionary = {}
var adjacency: Dictionary = {}
var edges: Array = []
var virtual_points: Array = []
var units_per_minute := 9.375

func _init(data: Dictionary) -> void:
    units_per_minute = float(data.walk_units_per_story_minute)
    for key in data.nodes:
        nodes[key] = vec(data.nodes[key])
        adjacency[key] = []
    for entry in data.edges:
        var points: Array[Vector3] = []
        for p in entry.points: points.append(vec(p))
        edges.append({"a": entry.a, "b": entry.b, "points": points})
        link(entry.a, entry.b, points)

func vec(value: Array) -> Vector3:
    return Vector3(float(value[0]), float(value[1]), float(value[2]))

func path_length(points: Array) -> float:
    var total := 0.0
    for i in range(1, points.size()): total += points[i-1].distance_to(points[i])
    return total

func link(a: String, b: String, points: Array) -> void:
    var length := path_length(points)
    adjacency[a].append({"to": b, "length": length, "points": points.duplicate()})
    var reverse := points.duplicate()
    reverse.reverse()
    adjacency[b].append({"to": a, "length": length, "points": reverse})

func route(a: String, b: String) -> Dictionary:
    if not nodes.has(a) or not nodes.has(b): return {}
    if a == b: return {"points": [nodes[a]], "length": 0.0, "minutes": 0}
    var distance: Dictionary = {a: 0.0}
    var previous: Dictionary = {}
    var pending: Array = [a]
    var done: Dictionary = {}
    while not pending.is_empty():
        pending.sort_custom(func(x, y): return distance[x] < distance[y])
        var current: String = pending.pop_front()
        if done.has(current): continue
        done[current] = true
        if current == b: break
        for edge in adjacency[current]:
            var candidate: float = distance[current] + edge.length
            if candidate < float(distance.get(edge.to, INF)):
                distance[edge.to] = candidate
                previous[edge.to] = {"from": current, "edge": edge}
                pending.append(edge.to)
    if not previous.has(b): return {}
    var chains: Array = []
    var cursor := b
    while cursor != a:
        chains.push_front(previous[cursor].edge.points)
        cursor = previous[cursor].from
    var points: Array[Vector3] = []
    for chain in chains:
        for p in chain:
            if points.is_empty() or points[-1].distance_to(p) > 0.001: points.append(p)
    return {"points": points, "length": distance[b],
            "minutes": ceili(float(distance[b]) / units_per_minute)}

func project_ground(point: Vector3) -> String:
    var best := 6.0
    var edge_index := -1
    var sample_index := -1
    for i in range(edges.size()):
        for j in range(edges[i].points.size()):
            var p: Vector3 = edges[i].points[j]
            var d := Vector2(p.x-point.x, p.z-point.z).length()
            if d < best:
                best = d
                edge_index = i
                sample_index = j
    if edge_index < 0: return ""
    var edge: Dictionary = edges[edge_index]
    var ident := "ground_%d" % virtual_points.size()
    nodes[ident] = edge.points[sample_index]
    adjacency[ident] = []
    var prefix: Array = edge.points.slice(0, sample_index+1)
    var suffix: Array = edge.points.slice(sample_index)
    prefix.reverse()
    link(ident, edge.a, prefix)
    link(ident, edge.b, suffix)
    for old in virtual_points:
        if old.edge == edge_index:
            var part: Array = edge.points.slice(mini(old.sample, sample_index), maxi(old.sample, sample_index)+1)
            if old.sample < sample_index: part.reverse()
            link(ident, old.id, part)
    virtual_points.append({"id": ident, "edge": edge_index, "sample": sample_index})
    return ident
