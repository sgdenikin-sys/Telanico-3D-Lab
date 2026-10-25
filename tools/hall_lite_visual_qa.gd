## Isolated visual QA fixture, not a game scene. Uses the cached Godot Web engine.
extends Node3D

var camera: Camera3D
var model: Node3D
var animator: AnimationPlayer
var glass: MeshInstance3D
var glass_material: StandardMaterial3D
var panel: Node3D
var variant := "lite"
var mode := "model"
var decoded_ms := 0.0
var label: Label
var command_id := 0


func _ready() -> void:
    var world := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.18, 0.22, 0.25)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.76, 0.84, 0.92)
    env.ambient_light_energy = 0.65
    var sky := Sky.new()
    sky.sky_material = ProceduralSkyMaterial.new()
    env.sky = sky
    env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
    world.environment = env
    add_child(world)
    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-48, -35, 0)
    sun.light_color = Color(1, 0.90, 0.76)
    sun.light_energy = 1.5
    sun.shadow_enabled = true
    add_child(sun)
    camera = Camera3D.new()
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.far = 200
    camera.current = true
    add_child(camera)
    var layer := CanvasLayer.new()
    label = Label.new()
    label.position = Vector2(12, 10)
    label.add_theme_font_size_override("font_size", 16)
    layer.add_child(label)
    add_child(layer)
    load_model("lite")
    panel = Node3D.new()
    panel.visible = false
    add_child(panel)
    var colors := [Color(0.9, 0.06, 0.03), Color(0.05, 0.8, 0.1), Color(0.05, 0.1, 0.9), Color(0.9, 0.75, 0.02)]
    for i in range(4):
        var quad := MeshInstance3D.new()
        var geometry := QuadMesh.new()
        geometry.size = Vector2(2, 1.25)
        quad.mesh = geometry
        quad.position = Vector3(-1 if i % 2 == 0 else 1, 3.625 if i < 2 else 2.375, 0)
        var mat := StandardMaterial3D.new()
        mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
        mat.albedo_color = colors[i]
        quad.material_override = mat
        panel.add_child(quad)
    glass = MeshInstance3D.new()
    var pane := QuadMesh.new()
    pane.size = Vector2(4, 2.5)
    glass.mesh = pane
    glass.position = Vector3(0, 3, 1)
    glass.material_override = glass_material
    glass.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    panel.add_child(glass)


func load_model(name: String) -> void:
    if model:
        model.free()
    var start := Time.get_ticks_usec()
    var path := "res://scenes/assets/reference_v2.tscn" if name == "v2" else "res://scenes/assets/settlements_hall.tscn"
    model = (load(path) as PackedScene).instantiate()
    add_child(model)
    decoded_ms = (Time.get_ticks_usec() - start) / 1000.0
    variant = name
    for player in model.find_children("*", "AnimationPlayer", true, false):
        player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
        player.stop()
        if player.has_animation("Hall_Demo"):
            animator = player
    for instance in model.find_children("*", "MeshInstance3D", true, false):
        for i in range(instance.mesh.get_surface_count()):
            var mat: Material = instance.mesh.surface_get_material(i)
            if mat.resource_name == "Semi transparent blue tinted glass":
                glass_material = mat.duplicate()
    pose(0)
    camera.position = Vector3(27, 24, 36)
    camera.size = 22
    camera.look_at(Vector3(0, 7, 0.7))
    label.text = ("V2 / 34,643 triangles" if name == "v2" else "V3 Lite / 19,816 triangles") + "  ·  Godot 4.6.3 Compatibility"
    mode = "model"
    if panel:
        panel.visible = false


func pose(seconds: float) -> void:
    animator.play("Hall_Demo")
    animator.seek(seconds, true)
    animator.advance(0)


func glass_mode(kind: String) -> void:
    model.visible = false
    panel.visible = true
    camera.position = Vector3(0, 3, 10)
    camera.size = 5
    camera.look_at(Vector3(0, 3, 0))
    glass.visible = kind != "hidden"
    glass.material_override = glass_material
    glass_material.transparency = BaseMaterial3D.TRANSPARENCY_DISABLED if kind == "opaque" else BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
    glass_material.albedo_color.a = 1 if kind == "opaque" else 0.63
    label.text = "Imported GLB glass / " + kind
    mode = kind


func _process(_delta: float) -> void:
    if not OS.has_feature("web"):
        return
    var raw: String = JavaScriptBridge.eval("JSON.stringify(window.__HALL_COMMAND || null)")
    var command = JSON.parse_string(raw)
    if command is Dictionary:
        JavaScriptBridge.eval("window.__HALL_COMMAND=null")
        command_id = int(command.get("id", 0))
        match command.get("mode", ""):
            "lite", "v2":
                load_model(command.mode)
            "glass":
                glass_mode(command.kind)
            "pose":
                pose(float(command.seconds))
    var angles := {}
    var fabrics := {}
    for hinge in model.find_children("Door_Hinge_*", "Node3D", true, false):
        angles[hinge.name] = hinge.rotation_degrees.y
    for fabric in model.find_children("Flag_*", "MeshInstance3D", true, false):
        fabrics[fabric.name] = [fabric.get_blend_shape_value(0), fabric.get_blend_shape_value(1), fabric.get_blend_shape_value(2)]
    var state := {"ready": true, "variant": variant, "mode": mode, "command_id": command_id,
        "engine": Engine.get_version_info().string,
        "renderer": ProjectSettings.get_setting("rendering/renderer/rendering_method"),
        "fps": Engine.get_frames_per_second(), "engine_static_bytes": OS.get_static_memory_usage(),
        "decode_instantiate_ms": decoded_ms, "hinge_degrees": angles, "fabric_weights": fabrics}
    JavaScriptBridge.eval("window.__HALL_STATE=" + JSON.stringify(state))
