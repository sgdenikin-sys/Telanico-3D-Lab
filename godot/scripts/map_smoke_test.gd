extends Node3D

const MODEL_PATH := "res://assets/generated/overworld.glb"
const MIN_ZOOM := 30.0
const MAX_ZOOM := 82.0
const INITIAL_ZOOM := 52.0

var camera: Camera3D
var island: Node3D
var touches: Dictionary = {}
var portrait_hint: ColorRect
var landmark_labels: Array[Label] = []
var label_anchors: Array[Node3D] = []
var show_landmark_labels := true


func _ready() -> void:
    camera = Camera3D.new()
    camera.name = "TabletopCamera"
    camera.position = Vector3(0.0, 65.0, 78.0)
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.size = INITIAL_ZOOM
    camera.current = true
    add_child(camera)
    camera.look_at(Vector3(0.0, 1.0, 0.0), Vector3.UP)

    var sunlight := DirectionalLight3D.new()
    sunlight.name = "SoftSun"
    sunlight.rotation_degrees = Vector3(-55.0, -25.0, 0.0)
    sunlight.light_energy = 1.2
    add_child(sunlight)

    var world_environment := WorldEnvironment.new()
    var environment := Environment.new()
    environment.background_mode = Environment.BG_COLOR
    environment.background_color = Color(0.12, 0.17, 0.22)
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = Color(0.83, 0.87, 0.91)
    environment.ambient_light_energy = 0.6
    world_environment.environment = environment
    add_child(world_environment)

    if ResourceLoader.exists(MODEL_PATH):
        var packed_scene := load(MODEL_PATH) as PackedScene
        if packed_scene:
            island = packed_scene.instantiate()
            island.name = "GeneratedIsland"
            add_child(island)
            var names_layer := CanvasLayer.new()
            add_child(names_layer)
            for anchor in island.find_children("*label anchor", "Node3D", true, false):
                var label := Label.new()
                label.text = String(anchor.name).replace(" label anchor", "").replace("VAT Tax", "VAT / Tax")
                label.text = label.text.replace(" Harbor Launch", " Launch").replace(" Tube Station", " Tube")
                label.add_theme_font_size_override("font_size", 22)
                label.add_theme_color_override("font_color", Color(0.07, 0.14, 0.16))
                label.add_theme_color_override("font_outline_color", Color(0.97, 0.94, 0.83))
                label.add_theme_constant_override("outline_size", 4)
                label.mouse_filter = Control.MOUSE_FILTER_IGNORE
                names_layer.add_child(label)
                label.size = label.get_minimum_size()
                label_anchors.append(anchor)
                landmark_labels.append(label)
    else:
        push_error("Run Blender smoke generator first: " + MODEL_PATH)
    _build_hud()
    get_viewport().size_changed.connect(_update_orientation)
    _update_orientation()
    print("TELANICO_VIEWER_READY")


func _process(_delta: float) -> void:
    # Screen-space type stays legible on a small landscape phone viewport.
    for i in range(landmark_labels.size()):
        var label := landmark_labels[i]
        var anchor := label_anchors[i]
        label.visible = show_landmark_labels and not portrait_hint.visible
        label.position = camera.unproject_position(anchor.global_position) - label.size / 2


func _build_hud() -> void:
    var hud := CanvasLayer.new()
    add_child(hud)
    var instructions := Label.new()
    instructions.text = "TELANICO · OVERWORLD\nDrag to rotate · Pinch to zoom"
    instructions.position = Vector2(24, 18)
    instructions.add_theme_font_size_override("font_size", 28)
    instructions.mouse_filter = Control.MOUSE_FILTER_IGNORE
    hud.add_child(instructions)

    var reset := Button.new()
    reset.text = "Reset view"
    reset.custom_minimum_size = Vector2(224, 88)
    reset.add_theme_font_size_override("font_size", 24)
    hud.add_child(reset)
    reset.set_anchors_preset(Control.PRESET_TOP_RIGHT)
    reset.offset_left = -248
    reset.offset_right = -24
    reset.offset_top = 18
    reset.offset_bottom = 106
    reset.pressed.connect(reset_view)

    var names_button := Button.new()
    names_button.text = "Landmarks"
    names_button.toggle_mode = true
    names_button.button_pressed = true
    names_button.add_theme_font_size_override("font_size", 24)
    hud.add_child(names_button)
    names_button.set_anchors_preset(Control.PRESET_TOP_RIGHT)
    names_button.offset_left = -484
    names_button.offset_right = -260
    names_button.offset_top = 18
    names_button.offset_bottom = 106
    names_button.toggled.connect(func(visible_names: bool):
        show_landmark_labels = visible_names)

    portrait_hint = ColorRect.new()
    portrait_hint.color = Color(0.07, 0.10, 0.13, 1.0)
    portrait_hint.mouse_filter = Control.MOUSE_FILTER_STOP
    hud.add_child(portrait_hint)
    portrait_hint.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    var label := Label.new()
    label.text = "Rotate your iPhone to landscape\nThen drag to rotate · Pinch to zoom"
    label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    label.add_theme_font_size_override("font_size", 64)
    portrait_hint.add_child(label)
    label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)


func _update_orientation() -> void:
    var size := get_viewport().get_visible_rect().size
    portrait_hint.visible = size.y > size.x
    touches.clear()


func reset_view() -> void:
    touches.clear()
    if island:
        island.rotation.y = 0.0
    camera.size = INITIAL_ZOOM


func _notification(what: int) -> void:
    if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
        touches.clear()


func _input(event: InputEvent) -> void:
    # A release over a HUD button must still clear an earlier island touch.
    if event is InputEventScreenTouch and (not event.pressed or event.canceled):
        touches.erase(event.index)


func _unhandled_input(event: InputEvent) -> void:
    if not island or portrait_hint.visible:
        return
    if event is InputEventScreenTouch:
        if event.pressed and not event.canceled:
            touches[event.index] = event.position
        else:
            touches.erase(event.index)
    elif event is InputEventScreenDrag and touches.has(event.index):
        if touches.size() == 1:
            var previous: Vector2 = touches[event.index]
            var width := maxf(get_viewport().get_visible_rect().size.x, 1.0)
            island.rotation.y += (event.position.x - previous.x) / width * TAU
        elif touches.size() == 2:
            var other_index: int = touches.keys()[0]
            if other_index == event.index:
                other_index = touches.keys()[1]
            var previous: Vector2 = touches[event.index]
            var other: Vector2 = touches[other_index]
            var old_distance := previous.distance_to(other)
            var new_distance: float = event.position.distance_to(other)
            if old_distance > 1.0 and new_distance > 1.0:
                camera.size = clampf(camera.size * old_distance / new_distance,
                                    MIN_ZOOM, MAX_ZOOM)
        touches[event.index] = event.position
    elif event is InputEventMouseMotion and touches.is_empty():
        if event.button_mask & MOUSE_BUTTON_MASK_LEFT:
            island.rotation.y += event.relative.x / maxf(
                get_viewport().get_visible_rect().size.x, 1.0) * TAU
    elif event is InputEventMouseButton and event.pressed and touches.is_empty():
        if event.button_index == MOUSE_BUTTON_WHEEL_UP:
            camera.size = clampf(camera.size * 0.9, MIN_ZOOM, MAX_ZOOM)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            camera.size = clampf(camera.size / 0.9, MIN_ZOOM, MAX_ZOOM)
