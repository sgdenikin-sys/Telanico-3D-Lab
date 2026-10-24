## Optional standalone asset inspection; never changes the game's main scene.
extends Node3D

var camera: Camera3D
var azimuth := 0.64
var elevation := 0.43
var distance := 42.0


func _ready() -> void:
    var environment := Environment.new()
    environment.background_mode = Environment.BG_COLOR
    environment.background_color = Color(0.18, 0.22, 0.25)
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = Color(0.76, 0.84, 0.92)
    environment.ambient_light_energy = 0.65
    var sky_material := ProceduralSkyMaterial.new()
    sky_material.sky_top_color = Color(0.24, 0.36, 0.50)
    sky_material.sky_horizon_color = Color(0.68, 0.73, 0.77)
    sky_material.ground_horizon_color = Color(0.55, 0.53, 0.48)
    sky_material.ground_bottom_color = Color(0.19, 0.21, 0.23)
    var sky := Sky.new()
    sky.sky_material = sky_material
    environment.sky = sky
    environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
    var world := WorldEnvironment.new()
    world.environment = environment
    add_child(world)
    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-48, -35, 0)
    sun.light_color = Color(1.0, 0.90, 0.76)
    sun.light_energy = 1.5
    sun.shadow_enabled = true
    sun.directional_shadow_max_distance = 75
    add_child(sun)
    camera = Camera3D.new()
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.size = 29.5
    camera.current = true
    camera.far = 200
    add_child(camera)
    _update_camera()
    var hud := CanvasLayer.new()
    var label := Label.new()
    label.text = "TELANICO / SETTLEMENTS HALL\nDrag to orbit · Wheel to zoom · F front · R rear\nO open · C close · D animation demo · 1 unit = 1 metre"
    label.position = Vector2(20, 18)
    label.add_theme_font_size_override("font_size", 18)
    label.add_theme_color_override("font_color", Color(0.95, 0.90, 0.78))
    label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    hud.add_child(label)
    add_child(hud)
    get_node("SettlementsHall").play_demo()
    print("SETTLEMENTS_PREVIEW_READY Godot ", Engine.get_version_info().string,
        " renderer=", ProjectSettings.get_setting("rendering/renderer/rendering_method"))


func _update_camera() -> void:
    var target := Vector3(0, 7, 0.7)
    camera.position = target + distance * Vector3(
        sin(azimuth) * cos(elevation), sin(elevation), cos(azimuth) * cos(elevation))
    camera.look_at(target)


func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseMotion and event.button_mask & MOUSE_BUTTON_MASK_LEFT:
        azimuth -= event.relative.x * 0.006
        elevation = clampf(elevation + event.relative.y * 0.004, 0.08, 1.2)
        _update_camera()
    elif event is InputEventMouseButton and event.pressed:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP:
            camera.size = clampf(camera.size * 0.9, 12, 42)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            camera.size = clampf(camera.size / 0.9, 12, 42)
    elif event is InputEventKey and event.pressed:
        if event.keycode == KEY_F:
            azimuth = 0
        elif event.keycode == KEY_R:
            azimuth = PI
        elif event.keycode == KEY_O:
            get_node("SettlementsHall").open_doors()
        elif event.keycode == KEY_C:
            get_node("SettlementsHall").close_doors()
        elif event.keycode == KEY_D:
            get_node("SettlementsHall").play_demo()
        _update_camera()
