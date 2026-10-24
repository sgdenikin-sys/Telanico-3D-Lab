extends RefCounted
## One shadow-casting key, cached sky radiance, Compatibility SSAO and one mist plane.
static func apply(scene: Node3D, campus: Node3D) -> void:
    var sun := DirectionalLight3D.new()
    sun.name = "LateAfternoonSun_NE"
    scene.add_child(sun)
    sun.position = Vector3(180,90,-180)
    sun.look_at(Vector3.ZERO,Vector3.UP)
    sun.light_color = Color("#FFE1B2")
    sun.light_energy = 1.05
    sun.light_specular = 0.35
    sun.light_angular_distance = 1.5
    sun.shadow_enabled = true
    sun.shadow_bias = 0.10
    sun.shadow_normal_bias = 0.8
    sun.shadow_opacity = 0.60
    sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
    sun.directional_shadow_max_distance = 320
    var environment := WorldEnvironment.new()
    environment.name = "CampusSkyAndContactAO"
    var settings := Environment.new()
    var sky := Sky.new()
    var material := ShaderMaterial.new()
    material.shader = load("res://shaders/campus_sky.gdshader")
    sky.sky_material = material
    sky.radiance_size = Sky.RADIANCE_SIZE_128
    sky.process_mode = Sky.PROCESS_MODE_QUALITY
    settings.sky = sky
    settings.background_mode = Environment.BG_SKY
    settings.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
    settings.ambient_light_color = Color("#BACFE1")
    settings.ambient_light_sky_contribution = 0.70
    settings.ambient_light_energy = 0.65
    settings.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
    # Godot 4.6 Compatibility supports the simplified radius/intensity AO pass.
    settings.ssao_enabled = true
    settings.ssao_radius = 1.25
    settings.ssao_intensity = 0.65
    settings.fog_enabled = true
    settings.fog_light_color = Color("#B5D1D6")
    settings.fog_light_energy = 0.75
    settings.fog_density = 0.00022
    settings.fog_height = 0.5
    settings.fog_height_density = 0.025
    settings.fog_sun_scatter = 0.15
    environment.environment = settings
    scene.add_child(environment)
    var bush := ShaderMaterial.new()
    bush.shader = load("res://shaders/bush_breeze.gdshader")
    for mesh in campus.find_children("*","MeshInstance3D",true,false):
        if String(mesh.name).begins_with("Soft Canopy Bush"):
            mesh.material_override = bush
            mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
        elif String(mesh.name).contains("Open teal water"):
            var water := StandardMaterial3D.new()
            water.albedo_color = Color("#215C63")
            water.roughness = 0.30
            water.metallic = 0.12
            mesh.material_override = water
    var haze := MeshInstance3D.new()
    haze.name = "LowWaterHaze"
    var plane := PlaneMesh.new()
    plane.size = Vector2(215,155)
    haze.mesh = plane
    haze.position.y = 0.65
    var mist := ShaderMaterial.new()
    mist.shader = load("res://shaders/water_haze.gdshader")
    var noise := FastNoiseLite.new()
    noise.seed = 24019
    noise.frequency = 0.05
    noise.fractal_octaves = 2
    var noise_texture := NoiseTexture2D.new()
    noise_texture.width = 128
    noise_texture.height = 128
    noise_texture.seamless = true
    noise_texture.noise = noise
    mist.set_shader_parameter("mist_noise",noise_texture)
    haze.material_override = mist
    haze.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    campus.add_child(haze)
