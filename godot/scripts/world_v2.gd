extends Node3D

const Routes = preload("res://scripts/world_routes.gd")
const MIN_ZOOM := 12.0
const MAX_ZOOM := 190.0
const OVERVIEW_ZOOM := 124.0
var data: Dictionary
var graph: RefCounted
var world: Node3D
var camera: Camera3D
var actor: CharacterBody3D
var visual: Node3D
var animation: AnimationPlayer
var idle_animation := ""
var walk_animation := ""
var ferry: Node3D
var sites: Dictionary = {}
var current_node := "settlements"
var selected := ""
var current_island := "west"
var state := "IDLE"
var story_minutes := 0
var walk_plan: Dictionary = {}
var walk_points: Array = []
var walk_index := 0
var walk_target := ""
var pending_transport := ""
var speed := 3.125
var simulation_rate := 1.0
var elapsed_real := 0.0
var trip_real := 0.0
var last_trip: Dictionary = {}
var camera_target := Vector3(0, 2, 0)
var camera_yaw := 0.0
var camera_elevation := 60.0
var inspect_mode := false
var follow_character := false
var show_names := false
var touches: Dictionary = {}
var ui_touches: Dictionary = {}
var pointer_start := Vector2.ZERO
var pointer_last := Vector2.ZERO
var pointer_dragged := false
var pointer_orbit := false
var touch_multi := false
var route_mesh: MeshInstance3D
var selection_ring: MeshInstance3D
var hud: Control
var panel: PanelContainer
var title: Label
var info: Label
var status: Label
var hover_label: Label
var buttons: Dictionary = {}
var top_buttons: Dictionary = {}
var labels: Dictionary = {}
var portrait: ColorRect
var fade: ColorRect
var last_probe := 0.0
var build_info: Dictionary = {}
var test_mode := false
var transition_clock := 0.0
var layout_timer := 0.0
var last_layout := ""
var panel_left := 10.0
var panel_bottom := 10.0

func _ready() -> void:
    Engine.max_fps = 30
    data = JSON.parse_string(FileAccess.get_file_as_string("res://assets/generated/world_v2.json"))
    if FileAccess.file_exists("res://assets/generated/build_info.json"):
        build_info = JSON.parse_string(FileAccess.get_file_as_string("res://assets/generated/build_info.json"))
    test_mode = OS.get_cmdline_user_args().has("--test")
    if OS.has_feature("web"):
        test_mode = bool(JavaScriptBridge.eval("new URLSearchParams(location.search).get('test') === '1'"))
    if test_mode: simulation_rate = 12.0
    graph = Routes.new(data)
    world = load("res://assets/generated/overworld.glb").instantiate()
    add_child(world)
    for item in data.landmarks: sites[item.id] = item
    for node in world.find_children("*", "MeshInstance3D", true, false):
        var name_text := String(node.name)
        if name_text.contains("Terrain") or name_text.contains("WalkSurface"):
            node.create_trimesh_collision()
            if name_text.contains("Terrain"):
                for body in node.get_children():
                    if body is StaticBody3D: body.collision_layer = 8
    for ident in sites:
        _make_site_target(ident)
    ferry = world.find_child("Central Ferry", true, false)
    _make_actor()
    _make_camera_lighting()
    route_mesh = MeshInstance3D.new()
    add_child(route_mesh)
    selection_ring = MeshInstance3D.new()
    var torus := TorusMesh.new()
    torus.inner_radius = 0.90
    torus.outer_radius = 1.0
    selection_ring.mesh = torus
    var glow := StandardMaterial3D.new()
    glow.albedo_color = Color(0.87,0.66,0.27)
    glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    selection_ring.material_override = glow
    selection_ring.visible = false
    add_child(selection_ring)
    _make_ui()
    _camera_pose()
    get_viewport().size_changed.connect(_resize_view)
    _layout_ui()
    print("TELANICO_V2_READY imported world, animated courier, 15 sites")

func _make_site_target(ident: String) -> void:
    var item: Dictionary = sites[ident]
    var pos: Vector3 = graph.vec(item.position)
    var shape := BoxShape3D.new()
    shape.size = Vector3(float(item.footprint[0]), float(item.height)+1, float(item.footprint[1]))
    var area := Area3D.new()
    area.name = "Select_"+ident
    area.set_meta("site", ident)
    area.position = pos+Vector3(0, shape.size.y/2, 0)
    area.collision_layer = 2
    area.collision_mask = 0
    var collision := CollisionShape3D.new()
    collision.shape = shape
    area.add_child(collision)
    add_child(area)
    if item.kind == "office" or item.kind == "tube":
        var solid := StaticBody3D.new()
        solid.position = area.position
        var wall := CollisionShape3D.new()
        wall.shape = shape
        solid.add_child(wall)
        add_child(solid)

func _make_actor() -> void:
    actor = CharacterBody3D.new()
    actor.name = "TemporaryCourier"
    actor.floor_snap_length = 0.8
    actor.collision_layer = 4
    actor.collision_mask = 1
    var shape := CapsuleShape3D.new()
    shape.radius = 0.35
    shape.height = 2.4
    var collider := CollisionShape3D.new()
    collider.shape = shape
    collider.position.y = 1.2
    actor.add_child(collider)
    add_child(actor)
    actor.position = graph.nodes[current_node]+Vector3(0,0.2,0)
    visual = load("res://assets/generated/courier.glb").instantiate()
    actor.add_child(visual)
    animation = visual.find_child("*", true, false) as AnimationPlayer
    var players := visual.find_children("*", "AnimationPlayer", true, false)
    if not players.is_empty(): animation = players[0]
    if animation:
        for clip in animation.get_animation_list():
            if String(clip).contains("Idle"): idle_animation = clip
            if String(clip).contains("Walking_A"): walk_animation = clip
        for clip in [idle_animation, walk_animation]:
            if not clip.is_empty(): animation.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
    _animate(false)

func _animate(walking: bool) -> void:
    if animation == null: return
    var clip := walk_animation if walking else idle_animation
    if not clip.is_empty() and animation.current_animation != clip:
        animation.play(clip,0.15)
    animation.speed_scale = (1.4 if walking else 1.0) * (minf(simulation_rate, 3.0) if test_mode else 1.0)

func _make_camera_lighting() -> void:
    camera = Camera3D.new()
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.size = OVERVIEW_ZOOM
    camera.current = true
    camera.far = 800
    add_child(camera)
    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-52,-30,0)
    sun.light_energy = 0.95
    sun.shadow_enabled = not OS.has_feature("web")
    sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
    sun.directional_shadow_max_distance = 350
    add_child(sun)
    var environment := WorldEnvironment.new()
    var settings := Environment.new()
    settings.background_mode = Environment.BG_COLOR
    settings.background_color = Color(0.065,0.22,0.25)
    settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    settings.ambient_light_color = Color(0.84,0.88,0.87)
    settings.ambient_light_energy = 0.55
    environment.environment = settings
    add_child(environment)

func _camera_pose() -> void:
    var e := deg_to_rad(camera_elevation)
    camera.position = camera_target+Vector3(sin(camera_yaw)*cos(e),sin(e),cos(camera_yaw)*cos(e))*230
    camera.look_at(camera_target,Vector3.UP)

func _resize_view() -> void:
    touches.clear()
    ui_touches.clear()
    pointer_dragged = true
    touch_multi = true
    _layout_ui(true)

func reset_view() -> void:
    inspect_mode = false
    if top_buttons.has("Explore"): top_buttons.Explore.text = "Explore"
    camera_target = Vector3(0,2,0)
    camera_yaw = 0
    camera_elevation = 60
    camera.size = OVERVIEW_ZOOM
    follow_character = false
    touches.clear()
    _camera_pose()

func _make_ui() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    hud = Control.new()
    hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layer.add_child(hud)
    hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    status = Label.new()
    status.add_theme_font_size_override("font_size",20)
    status.mouse_filter = Control.MOUSE_FILTER_IGNORE
    hud.add_child(status)
    for name in ["Explore", "Follow", "Names", "Reset"]:
        var button := Button.new()
        button.text = name
        button.add_theme_font_size_override("font_size",22)
        button.pressed.connect(_top_action.bind(name))
        top_buttons[name] = button
        hud.add_child(button)
    hover_label = Label.new()
    hover_label.add_theme_font_size_override("font_size",22)
    hover_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    hud.add_child(hover_label)
    for ident in sites:
        var label := Label.new()
        label.text = sites[ident].name
        label.add_theme_font_size_override("font_size",20)
        label.add_theme_color_override("font_outline_color",Color(0.03,0.10,0.12))
        label.add_theme_constant_override("outline_size",4)
        label.mouse_filter = Control.MOUSE_FILTER_IGNORE
        hud.add_child(label)
        labels[ident] = label
    panel = PanelContainer.new()
    var style := StyleBoxFlat.new()
    style.bg_color = Color(0.035,0.10,0.13,0.96)
    style.border_color = Color(0.6,0.46,0.25)
    style.set_border_width_all(2)
    style.set_corner_radius_all(12)
    style.content_margin_left = 16
    style.content_margin_right = 16
    style.content_margin_top = 10
    style.content_margin_bottom = 10
    panel.add_theme_stylebox_override("panel",style)
    hud.add_child(panel)
    var column := VBoxContainer.new()
    panel.add_child(column)
    title = Label.new()
    title.add_theme_font_size_override("font_size",24)
    column.add_child(title)
    info = Label.new()
    info.add_theme_font_size_override("font_size",20)
    column.add_child(info)
    var row := HBoxContainer.new()
    column.add_child(row)
    for name in ["Walk", "Boat", "Tube", "Enter", "Outside", "Cancel", "Return"]:
        var button := Button.new()
        button.text = name
        button.custom_minimum_size = Vector2(100,64)
        button.add_theme_font_size_override("font_size",22)
        button.pressed.connect(_action.bind(name))
        row.add_child(button)
        buttons[name] = button
    panel.visible = false
    portrait = ColorRect.new()
    portrait.color = Color(0.03,0.1,0.13)
    hud.add_child(portrait)
    portrait.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    var turn := Label.new()
    turn.text = "Rotate to landscape to explore Telanico"
    turn.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    turn.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    turn.add_theme_font_size_override("font_size",40)
    portrait.add_child(turn)
    turn.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    fade = ColorRect.new()
    fade.color = Color(0.03,0.15,0.18,0)
    fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
    hud.add_child(fade)
    fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

func _layout_ui(force := false) -> void:
    if hud == null: return
    var viewport := get_viewport().get_visible_rect().size
    var units := 1.0
    var left := 0.0
    var right := 0.0
    var top := 0.0
    var bottom := 0.0
    if OS.has_feature("web"):
        var layout = JSON.parse_string(str(JavaScriptBridge.eval("window.telanicoViewport ? window.telanicoViewport() : '{}'")))
        if layout is Dictionary and float(layout.get("width",0))>0:
            units = viewport.x/float(layout.width)
            left = float(layout.get("left",0))*units
            right = float(layout.get("right",0))*units
            top = float(layout.get("top",0))*units
            bottom = float(layout.get("bottom",0))*units
    var signature := str([viewport,left,right,top,bottom,units])
    if not force and signature==last_layout: return
    last_layout = signature
    var index := 0
    for name in top_buttons:
        var button: Button = top_buttons[name]
        button.position = Vector2(viewport.x-right-(10+82*(4-index))*units,top+8*units)
        button.size = Vector2(78,36)*units
        button.add_theme_font_size_override("font_size",roundi(13*units))
        index += 1
    status.position = Vector2(left+10*units,top+9*units)
    status.add_theme_font_size_override("font_size",roundi(12*units))
    panel_left = left+10*units
    panel_bottom = bottom+10*units
    title.add_theme_font_size_override("font_size",roundi(16*units))
    info.add_theme_font_size_override("font_size",roundi(14*units))
    for button in buttons.values():
        button.custom_minimum_size = Vector2(88,44)*units
        button.add_theme_font_size_override("font_size",roundi(14*units))
    panel.position = Vector2(panel_left,viewport.y-panel.size.y-panel_bottom)
    portrait.visible = viewport.y>viewport.x

func _top_action(name: String) -> void:
    match name:
        "Reset": reset_view()
        "Explore":
            inspect_mode = not inspect_mode
            top_buttons.Explore.text = "Inspect" if inspect_mode else "Explore"
            if not inspect_mode:
                camera_yaw = 0
                camera_elevation = 60
        "Follow": follow_character = not follow_character
        "Names": show_names = not show_names

func _process(delta: float) -> void:
    elapsed_real += delta
    if test_mode and OS.has_feature("web") and last_probe==0:
        var command = JavaScriptBridge.eval("JSON.stringify(window.__TELANICO_COMMAND || null)")
        if command != "null":
            var request = JSON.parse_string(str(command))
            JavaScriptBridge.eval("window.__TELANICO_COMMAND=null")
            if request is Dictionary:
                if request.has("rate"): simulation_rate = clampf(float(request.rate),1,12)
                if request.has("focus") and sites.has(request.focus): camera_target = graph.vec(sites[request.focus].position)
                if request.has("size"): camera.size = clampf(float(request.size),MIN_ZOOM,MAX_ZOOM)
                if request.has("elevation"): camera_elevation = clampf(float(request.elevation),45,75)
    if follow_character: camera_target = camera_target.lerp(actor.position, minf(delta*3,1))
    _camera_pose()
    layout_timer += delta
    if layout_timer>.5:
        layout_timer = 0
        _layout_ui()
    # Container minimum sizes can settle after opening a different action row.
    panel.position = Vector2(panel_left,get_viewport().get_visible_rect().size.y-panel.size.y-panel_bottom)
    var minutes := 12*60+story_minutes
    status.text = "%02d:%02d · V2 %s\n%s" % [minutes/60,minutes%60,String(build_info.get("commit","local")).left(7),
        "Courier · temporary rig" if state=="IDLE" else state.capitalize()]
    var occupied: Array[Rect2] = []
    for ident in labels:
        var label: Label = labels[ident]
        label.visible = show_names and not portrait.visible
        if not label.visible: continue
        var point: Vector3 = graph.vec(sites[ident].position)+Vector3(0,float(sites[ident].height)+2,0)
        label.position = camera.unproject_position(point)-label.get_minimum_size()/2
        var rect := Rect2(label.position,label.get_minimum_size()+Vector2(8,6))
        for old in occupied:
            if old.intersects(rect):
                label.position.y += 24
                rect.position.y += 24
        occupied.append(rect)
    last_probe += delta
    if test_mode and last_probe>0.15:
        last_probe = 0
        _publish_probe()

func select_site(ident: String) -> void:
    if state != "IDLE" or not sites.has(ident): return
    selected = ident
    var item: Dictionary = sites[ident]
    walk_plan = graph.route(current_node,ident)
    if walk_plan.is_empty(): return
    _draw_path(walk_plan.points)
    selection_ring.visible = true
    selection_ring.position = graph.vec(item.position)+Vector3(0,0.3,0)
    selection_ring.scale = Vector3(float(item.footprint[0])*.65,.25,float(item.footprint[1])*.65)
    title.text = item.name
    info.text = "Walk %d story min · %.0f real sec\n%s island · entrance outside building" % [walk_plan.minutes,float(walk_plan.minutes)*3,item.island.capitalize()]
    _show_actions(["Walk", "Cancel"]+["Boat"] if item.kind=="boat" else ["Walk","Tube","Cancel"] if item.kind=="tube" else ["Walk","Cancel"])

func select_ground(point: Vector3) -> void:
    if state != "IDLE": return
    var ident: String = graph.project_ground(point)
    if ident.is_empty():
        hover_label.text = "Choose a promenade or a department entrance"
        return
    selected = ident
    walk_plan = graph.route(current_node,ident)
    title.text = "Walking destination"
    info.text = "Promenade point · %d story min" % walk_plan.minutes
    _draw_path(walk_plan.points)
    _show_actions(["Walk","Cancel"])

func _show_actions(names: Array) -> void:
    panel.visible = true
    for name in buttons: buttons[name].visible = names.has(name)
    panel.reset_size()
    _layout_ui.call_deferred(true)

func _action(name: String) -> void:
    match name:
        "Walk": start_walk(selected)
        "Boat": start_transfer("boat")
        "Tube": start_transfer("tube")
        "Cancel", "Outside", "Return":
            panel.visible = false
            route_mesh.mesh = null
            selection_ring.visible = false
        "Enter":
            title.text = sites[selected].name
            info.text = "Department preview only.\nOriginal interiors and quests remain unchanged."
            _show_actions(["Return"])

func start_walk(target: String) -> void:
    if state != "IDLE": return
    var plan: Dictionary = graph.route(current_node,target)
    if plan.is_empty(): return
    _begin_walk(target,plan)

func _begin_walk(target: String,plan: Dictionary) -> void:
    walk_target = target
    walk_plan = plan
    walk_points = plan.points.duplicate()
    walk_index = 1
    trip_real = 0
    state = "WALKING"
    panel.visible = false
    _animate(true)
    _draw_path(walk_points)
    if walk_points.size()<2: _arrive()

func start_transfer(kind: String) -> void:
    if state != "IDLE": return
    pending_transport = kind
    var origin := ("dock_" if kind=="boat" else "tube_")+("w" if current_island=="west" else "e")
    _begin_walk(origin,graph.route(current_node,origin))

func _physics_process(delta: float) -> void:
    if actor == null: return
    if state == "WALKING":
        trip_real += delta
        if walk_index>=walk_points.size():
            _arrive()
            return
        var point: Vector3 = walk_points[walk_index]
        var horizontal := Vector3(point.x-actor.position.x,0,point.z-actor.position.z)
        var frame_distance := speed*simulation_rate*delta
        if horizontal.length()<=maxf(0.20,frame_distance):
            actor.position.x = point.x
            actor.position.z = point.z
            walk_index += 1
            actor.velocity = Vector3(0,-3,0)
        else:
            var direction := horizontal.normalized()
            actor.velocity.x = direction.x*speed*simulation_rate
            actor.velocity.z = direction.z*speed*simulation_rate
            visual.rotation.y = lerp_angle(visual.rotation.y,atan2(direction.x,direction.z),0.25)
        if not actor.is_on_floor(): actor.velocity.y -= 18*delta
        else: actor.velocity.y = -0.5
        var prior := actor.position
        actor.move_and_slide()
        # Small curb/terrain-triangulation seams: step up only when the raised
        # capsule has a collision-free horizontal sweep. Never bypass a wall.
        if horizontal.length()>frame_distance and Vector2(actor.position.x-prior.x,actor.position.z-prior.z).length()<frame_distance*.2:
            var raised := actor.global_transform
            raised.origin.y += 0.85
            var step := horizontal.normalized()*frame_distance
            if not actor.test_move(raised,step):
                actor.position = raised.origin
                actor.velocity = horizontal.normalized()*speed*simulation_rate
                actor.move_and_slide()
    elif state == "IDLE":
        actor.velocity = Vector3(0,-3,0)
        actor.move_and_slide()
    elif state in ["BOAT","TUBE"]:
        _transport_tick(delta)

func _arrive() -> void:
    actor.position = graph.nodes[walk_target]
    current_node = walk_target
    current_island = "west" if actor.position.x<0 else "east"
    story_minutes += int(walk_plan.minutes)
    last_trip = {"kind":"walk", "minutes":walk_plan.minutes,"length":walk_plan.length,"real_seconds":trip_real}
    _animate(false)
    route_mesh.mesh = null
    if not pending_transport.is_empty():
        state = "BOAT" if pending_transport=="boat" else "TUBE"
        transition_clock = 0
        actor.collision_mask = 0
        return
    state = "IDLE"
    selected = current_node
    if sites.has(current_node):
        title.text = sites[current_node].name
        info.text = "Entrance reached · %d story min\nEnter the placeholder department or stay outside." % walk_plan.minutes
        _show_actions(["Enter","Outside"] if sites[current_node].kind=="office" else ["Boat","Outside"] if sites[current_node].kind=="boat" else ["Tube","Outside"])

func _transport_tick(delta: float) -> void:
    var kind := pending_transport
    transition_clock += delta*(3 if test_mode else 1)
    var duration := 5.0 if kind=="boat" else 2.0
    var t := minf(transition_clock/duration,1)
    var west_to_east := current_island=="west"
    var peer := ("dock_" if kind=="boat" else "tube_")+("e" if west_to_east else "w")
    if kind=="boat":
        var start_x := -9.0 if west_to_east else 9.0
        var sailing := clampf((t-.18)/.64,0,1)
        ferry.position = Vector3(lerpf(start_x,-start_x,smoothstep(0,1,sailing)),0.2,0)
        var deck := ferry.position+Vector3(2,1.3,0)
        if t<.18:
            actor.position = graph.nodes[current_node].lerp(deck,t/.18)
            _animate(true)
        elif t>.82:
            actor.position = deck.lerp(graph.nodes[peer],(t-.82)/.18)
            _animate(true)
        else:
            actor.position = deck
            _animate(false)
        actor.visible = true
    else:
        fade.color.a = sin(t*PI)*0.8
        actor.visible = t<0.2 or t>0.8
        if t>0.5: actor.position = graph.nodes[peer]
    if t>=1:
        var cost := 5 if kind=="boat" else 3
        story_minutes += cost
        actor.position = graph.nodes[peer]
        actor.visible = true
        _animate(false)
        actor.collision_mask = 1
        fade.color.a = 0
        current_node = peer
        selected = peer
        current_island = "east" if west_to_east else "west"
        last_trip = {"kind":kind,"minutes":cost,"real_seconds":duration,"wait_minutes":0}
        pending_transport = ""
        state = "IDLE"
        title.text = sites[peer].name
        info.text = "Arrived · %d story min · %.0f real seconds\nSelect the next department." % [cost,duration]
        _show_actions(["Outside"])

func _draw_path(points: Array) -> void:
    var mesh := ImmediateMesh.new()
    if points.size()>1:
        mesh.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
        for p in points: mesh.surface_add_vertex(p+Vector3(0,.2,0))
        mesh.surface_end()
    route_mesh.mesh = mesh
    var mat := StandardMaterial3D.new()
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.albedo_color = Color(1,.72,.16)
    route_mesh.material_override = mat

func _ray(screen: Vector2,mask: int,areas: bool) -> Dictionary:
    var start := camera.project_ray_origin(screen)
    var query := PhysicsRayQueryParameters3D.create(start,start+camera.project_ray_normal(screen)*1000,mask)
    query.collide_with_areas = areas
    query.collide_with_bodies = not areas
    return get_world_3d().direct_space_state.intersect_ray(query)

func _tap(screen: Vector2) -> void:
    if state != "IDLE" or portrait.visible: return
    var hit := _ray(screen,2,true)
    if not hit.is_empty():
        select_site(hit.collider.get_meta("site"))
        return
    hit = _ray(screen,9,false)
    if not hit.is_empty(): select_ground(hit.position)

func _pan(delta: Vector2) -> void:
    var units := camera.size/maxf(get_viewport().get_visible_rect().size.y,1)
    var right := camera.global_transform.basis.x
    var forward := Vector3(-sin(camera_yaw),0,-cos(camera_yaw))
    camera_target += -right*delta.x*units+forward*delta.y*units/maxf(sin(deg_to_rad(camera_elevation)),.5)
    camera_target.x = clampf(camera_target.x,-100,100)
    camera_target.z = clampf(camera_target.z,-75,75)
    follow_character = false

func _over_ui(point: Vector2) -> bool:
    if panel.visible and panel.get_global_rect().has_point(point): return true
    for button in top_buttons.values():
        if button.get_global_rect().has_point(point): return true
    return false

func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        if event.pressed and _over_ui(event.position): ui_touches[event.index] = true
        elif not event.pressed and ui_touches.has(event.index):
            ui_touches.erase.call_deferred(event.index)

func _unhandled_input(event: InputEvent) -> void:
    if portrait.visible: return
    if event is InputEventScreenTouch:
        if ui_touches.has(event.index): return
        if event.pressed:
            touches[event.index] = event.position
            if touches.size()==1:
                pointer_start = event.position
                pointer_dragged = false
                touch_multi = false
            else: touch_multi = true
        else:
            touches.erase(event.index)
            if touches.is_empty() and not pointer_dragged and not touch_multi and not event.canceled: _tap(event.position)
    elif event is InputEventScreenDrag and touches.has(event.index):
        if touches.size()==1:
            if pointer_start.distance_to(event.position)>8: pointer_dragged = true
            var drag: Vector2 = event.position-touches[event.index]
            if inspect_mode:
                camera_yaw = clampf(camera_yaw-drag.x*.004,-.8,.8)
                camera_elevation = clampf(camera_elevation+drag.y*.1,45,75)
            else: _pan(drag)
        elif touches.size()==2:
            var keys := touches.keys()
            var other = touches[keys[1] if keys[0]==event.index else keys[0]]
            var old: float = touches[event.index].distance_to(other)
            var fresh: float = event.position.distance_to(other)
            if old>2 and fresh>2: camera.size = clampf(camera.size*old/fresh,MIN_ZOOM,MAX_ZOOM)
        touches[event.index] = event.position
    elif event is InputEventMouseButton and event.device != InputEvent.DEVICE_ID_EMULATION:
        if event.button_index in [MOUSE_BUTTON_LEFT,MOUSE_BUTTON_RIGHT]:
            if event.pressed:
                pointer_start = event.position
                pointer_last = event.position
                pointer_dragged = false
                pointer_orbit = event.button_index==MOUSE_BUTTON_RIGHT and inspect_mode
            elif not pointer_dragged and event.button_index==MOUSE_BUTTON_LEFT: _tap(event.position)
        if event.pressed:
            if event.button_index==MOUSE_BUTTON_WHEEL_UP: camera.size = maxf(MIN_ZOOM,camera.size*.86)
            if event.button_index==MOUSE_BUTTON_WHEEL_DOWN: camera.size = minf(MAX_ZOOM,camera.size/.86)
    elif event is InputEventMouseMotion and event.device != InputEvent.DEVICE_ID_EMULATION:
        if event.button_mask & (MOUSE_BUTTON_MASK_LEFT|MOUSE_BUTTON_MASK_RIGHT):
            if pointer_start.distance_to(event.position)>6: pointer_dragged = true
            if pointer_orbit:
                camera_yaw = clampf(camera_yaw-event.relative.x*.004,-.8,.8)
                camera_elevation = clampf(camera_elevation+event.relative.y*.1,45,75)
            else: _pan(event.relative)
        elif state=="IDLE":
            var hit := _ray(event.position,2,true)
            hover_label.text = sites[hit.collider.get_meta("site")].name if not hit.is_empty() else ""
            hover_label.position = event.position+Vector2(14,18)
    elif event is InputEventKey and event.pressed:
        if event.keycode==KEY_ESCAPE: _action("Cancel")
        if event.keycode==KEY_R: reset_view()
        if event.keycode==KEY_I: _top_action("Explore")

func _notification(what: int) -> void:
    if what==NOTIFICATION_APPLICATION_FOCUS_OUT:
        touches.clear()
        ui_touches.clear()

func _publish_probe() -> void:
    var projected: Dictionary = {}
    for ident in sites:
        var pos: Vector3 = graph.vec(sites[ident].position)+Vector3(0,sites[ident].height*.45,0)
        var point := camera.unproject_position(pos)
        projected[ident] = [point.x,point.y]
    var ui: Dictionary = {}
    for key in buttons:
        if panel.visible and buttons[key].visible:
            var centre: Vector2 = buttons[key].global_position+buttons[key].size/2
            ui[key] = [centre.x,centre.y]
    for key in top_buttons:
        var centre: Vector2 = top_buttons[key].global_position+top_buttons[key].size/2
        ui[key] = [centre.x,centre.y]
    var probe := {"ready":true,"fps":Engine.get_frames_per_second(),"state":state,"current":current_node,"selected":selected,"island":current_island,
        "story_minutes":story_minutes,"position":[actor.position.x,actor.position.y,actor.position.z],
        "animation":animation.current_animation if animation else "", "animation_position":animation.current_animation_position if animation else 0,
        "last_trip":last_trip,"sites":projected,"ui":ui,"view":get_viewport().get_visible_rect().size,
        "viewport":[get_viewport().get_visible_rect().size.x,get_viewport().get_visible_rect().size.y],
        "camera_size":camera.size,"camera_target":[camera_target.x,camera_target.y,camera_target.z],
        "inspect":inspect_mode,"elevation":camera_elevation,"yaw":camera_yaw,"commit":build_info.get("commit","local")}
    if OS.has_feature("web"): JavaScriptBridge.eval("window.__TELANICO_STATE="+JSON.stringify(probe)+";")
