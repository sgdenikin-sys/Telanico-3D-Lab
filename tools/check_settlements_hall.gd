## Run after import: godot --headless --path godot --script ../tools/check_settlements_hall.gd
extends SceneTree


func _initialize() -> void:
    var packed := load("res://scenes/assets/settlements_hall.tscn") as PackedScene
    if not packed:
        push_error("Settlements Hall wrapper could not be loaded")
        quit(1)
        return
    var hall := packed.instantiate()
    root.add_child(hall)
    var meshes := hall.find_children("*", "MeshInstance3D", true, false)
    var triangles := 0
    var surfaces := 0
    var glass_ok := false
    var fabric_ok := false
    for instance in meshes:
        var mesh := (instance as MeshInstance3D).mesh
        for i in range(mesh.get_surface_count()):
            surfaces += 1
            triangles += mesh.surface_get_array_index_len(i) / 3
            var mat := mesh.surface_get_material(i) as StandardMaterial3D
            if not mat:
                push_error("Expected a StandardMaterial3D")
                quit(1)
                return
            if mat.resource_name == "Semi transparent blue tinted glass":
                glass_ok = mat.transparency in [BaseMaterial3D.TRANSPARENCY_ALPHA, BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS] and mat.albedo_color.a > 0 and mat.albedo_color.a < 1
            if mat.resource_name == "Woven blue banner fabric":
                fabric_ok = mat.cull_mode == BaseMaterial3D.CULL_DISABLED and mat.metallic == 0
    var collisions := hall.find_children("*", "CollisionShape3D", true, false)
    if triangles < 12000 or triangles > 35000 or surfaces != 11 or not glass_ok or not fabric_ok or collisions.size() != 5:
        push_error("Asset contract failed: triangles=%s surfaces=%s glass=%s fabric=%s collisions=%s" % [triangles, surfaces, glass_ok, fabric_ok, collisions.size()])
        quit(1)
        return
    print("SETTLEMENTS_GODOT_OK version=%s triangles=%s meshes=%s surfaces=%s alpha_glass=%s double_sided_fabric=%s coarse_colliders=%s" % [Engine.get_version_info().string, triangles, meshes.size(), surfaces, glass_ok, fabric_ok, collisions.size()])
    hall.queue_free()
    quit(0)
