extends RefCounted
## One shadow-casting key, cached sky radiance, Compatibility SSAO and one mist plane.
static func apply(scene: Node3D, campus: Node3D) -> void:
    var sun := DirectionalLight3D.new()
    sun.name = "LateAfternoonSun_NW"
    scene.add_child(sun)
    sun.position = Vector3(-180,90,-180)
    sun.look_at(Vector3.ZERO,Vector3.UP)
    sun.light_color = Color("#FFE1B2")
    sun.light_energy = 0.90
    sun.light_specular = 0.35
    sun.light_angular_distance = 0.8
    sun.shadow_enabled = true
    sun.shadow_bias = 0.025
    sun.shadow_normal_bias = 0.18
    sun.shadow_opacity = 0.68
    sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
    sun.directional_shadow_max_distance = 320
    var environment := WorldEnvironment.new()
    environment.name = "CampusSkyAndContactAO"
    var settings := Environment.new()
    var sky := Sky.new()
    var material := ShaderMaterial.new()
    material.shader = load("res://shaders/campus_sky.gdshader")
    material.set_shader_parameter("sun_direction", sun.position.normalized())
    sky.sky_material = material
    sky.radiance_size = Sky.RADIANCE_SIZE_128
    sky.process_mode = Sky.PROCESS_MODE_QUALITY
    settings.sky = sky
    settings.background_mode = Environment.BG_SKY
    settings.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
    settings.ambient_light_color = Color("#BACFE1")
    settings.ambient_light_sky_contribution = 0.70
    settings.ambient_light_energy = 0.45
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
    var ground := _ground_materials()
    for mesh in campus.find_children("*","MeshInstance3D",true,false):
        var name_text := String(mesh.name)
        # World triplanar projection works on the unchanged, UV-less terrain.
        # Existing broad grass zones and all route/collision geometry stay intact.
        if name_text.contains("Terrain") or (name_text.contains("WalkSurface") and not name_text.contains("Bridge")):
            for surface in range(mesh.mesh.get_surface_count()):
                var source: Material = mesh.mesh.surface_get_material(surface)
                if source == null:
                    continue
                var key := String(source.resource_name)
                if ground.has(key):
                    var replacement: Material = ground[key]
                    if key == "Telanico stone" and name_text.contains("Path WalkSurface"):
                        replacement = ground["promenade"]
                    mesh.set_surface_override_material(surface, replacement)
        if String(mesh.name).begins_with("Soft Canopy Bush"):
            mesh.material_override = bush
            mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
        elif String(mesh.name).contains("Open teal water"):
            var water := StandardMaterial3D.new()
            water.albedo_color = Color("#215C63")
            water.roughness = 0.30
            water.metallic = 0.12
            mesh.material_override = water
    # One draw for all crowns instead of 36 separate foliage submissions.
    # Keep hidden source instances in the imported scene for editable GLB provenance.
    var crowns := campus.find_children("Soft Canopy Bush*","MeshInstance3D",true,false)
    if not crowns.is_empty():
        var instances := MultiMesh.new()
        instances.transform_format = MultiMesh.TRANSFORM_3D
        instances.mesh = crowns[0].mesh
        instances.use_custom_data = true
        instances.instance_count = crowns.size()
        instances.custom_aabb = AABB(Vector3(-100,-2,-70),Vector3(200,45,140))
        var root_inverse := campus.global_transform.affine_inverse()
        for i in range(crowns.size()):
            instances.set_instance_transform(i,root_inverse*crowns[i].global_transform)
            var phase := fposmod(float(i)*2.399963,TAU)/TAU
            instances.set_instance_custom_data(i,Color(phase,0,0,1))
            crowns[i].visible = false
        var foliage := MultiMeshInstance3D.new()
        foliage.name = "InstancedBushCrowns"
        foliage.multimesh = instances
        foliage.material_override = bush
        foliage.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
        campus.add_child(foliage)
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
    # Generate once synchronously: no pending texture-worker jobs on scene restart.
    var noise_texture := ImageTexture.create_from_image(noise.get_seamless_image(128,128))
    mist.set_shader_parameter("mist_noise",noise_texture)
    haze.material_override = mist
    haze.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    campus.add_child(haze)


static func _ground_material(texture_name: String, tile_metres: float) -> StandardMaterial3D:
    var ground := StandardMaterial3D.new()
    ground.resource_name = "Ground | " + texture_name
    ground.albedo_texture = load("res://assets/ground/" + texture_name + "_base_albedo.png")
    ground.vertex_color_use_as_albedo = true
    ground.roughness = 0.96
    ground.metallic = 0.0
    ground.uv1_triplanar = true
    ground.uv1_world_triplanar = true
    ground.uv1_scale = Vector3.ONE / tile_metres
    ground.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
    return ground


static func _ground_materials() -> Dictionary:
    return {
        "Telanico grass": _ground_material("grass", 5.0),
        "Telanico meadow": _ground_material("grass_meadow", 5.0),
        "Telanico grass_light": _ground_material("earth_sparse_grass", 5.0),
        "Telanico dirt": _ground_material("path_dirt", 3.0),
        "Telanico stone": _ground_material("stone_path", 2.6),
        "promenade": _ground_material("stone_path", 3.2),
    }
