extends Node3D

const MODEL_PATH := "res://assets/generated/smoke_test.glb"

func _ready() -> void:
    var camera := Camera3D.new()
    camera.name = "TabletopCamera"
    camera.position = Vector3(8.0, 9.0, 10.5)
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.size = 12.0
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
            var island := packed_scene.instantiate()
            island.name = "GeneratedIsland"
            add_child(island)
    else:
        push_warning("Run Blender smoke generator first: " + MODEL_PATH)
