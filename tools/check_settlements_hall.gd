## Run after import: godot --headless --path godot --script ../tools/check_settlements_hall.gd
extends SceneTree


func _initialize() -> void:
    _run.call_deferred()


func fail(message: String) -> void:
    push_error(message)
    quit(1)


func cloth_values(fabrics: Array[Node]) -> Array:
    var values := []
    for fabric in fabrics:
        for i in range(fabric.mesh.get_blend_shape_count()):
            values.append(fabric.get_blend_shape_value(i))
    return values


func _run() -> void:
    var hall := (load("res://scenes/assets/settlements_hall.tscn") as PackedScene).instantiate()
    root.add_child(hall)
    var player: AnimationPlayer = hall.doors
    var wind_player: AnimationPlayer = hall.wind
    player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
    wind_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
    wind_player.stop()
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
                fail("Expected StandardMaterial3D")
                return
            if mat.resource_name == "Semi transparent blue tinted glass":
                glass_ok = mat.transparency in [BaseMaterial3D.TRANSPARENCY_ALPHA, BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS] and mat.albedo_color.a > 0 and mat.albedo_color.a < 1
            if mat.resource_name == "Woven blue banner fabric":
                fabric_ok = mat.cull_mode == BaseMaterial3D.CULL_DISABLED and mat.metallic == 0
    if triangles < 12000 or triangles > 35000 or surfaces != 22 or meshes.size() != 18 or not glass_ok or not fabric_ok:
        fail("Geometry/material contract failed")
        return
    var hinges := hall.find_children("Door_Hinge_*", "Node3D", true, false)
    var fabrics := hall.find_children("Flag_*", "MeshInstance3D", true, false)
    if hinges.size() != 2 or fabrics.size() != 4:
        fail("Separate moving objects did not survive import")
        return
    for flag in fabrics:
        if flag.mesh.get_blend_shape_count() != 3:
            fail("Missing cloth morph targets")
            return
    var clips := {}
    for clip in ["Doors_Open", "Doors_Close", "Flags_Wind", "Hall_Demo"]:
        if not player.has_animation(clip):
            fail("Missing imported clip: " + clip)
            return
        var animation := player.get_animation(clip)
        clips[clip] = {"seconds": animation.length, "tracks": animation.get_track_count(), "loop": animation.loop_mode}
    if player.get_animation("Flags_Wind").loop_mode != Animation.LOOP_LINEAR or player.get_animation("Hall_Demo").loop_mode != Animation.LOOP_LINEAR:
        fail("Godot did not import the loop suffixes")
        return
    player.play("Doors_Open")
    player.seek(0, true)
    player.advance(0)
    var closed := [hinges[0].quaternion, hinges[1].quaternion]
    var pivots := [hinges[0].global_position, hinges[1].global_position]
    var tips := []
    for hinge in hinges:
        tips.append(hinge.to_global(Vector3(0.94 if hinge.name.ends_with("_L") else -0.94, 1.3, 0)))
    player.seek(1.0, true)
    player.advance(0)
    var opening_degrees := []
    for i in range(2):
        var angle := rad_to_deg((closed[i] as Quaternion).angle_to(hinges[i].quaternion))
        opening_degrees.append(angle)
        var open_tip: Vector3 = hinges[i].to_global(Vector3(0.94 if hinges[i].name.ends_with("_L") else -0.94, 1.3, 0))
        if hinges[i].global_position.distance_to(pivots[i]) > 0.001 or open_tip.z < (tips[i] as Vector3).z + 0.8:
            fail("Door pivot moved or leaf failed to open outward")
            return
        if angle < 99 or angle > 101:
            fail("Door rotation did not reach 100 degrees")
            return
    player.play("Doors_Close")
    player.seek(1.0, true)
    player.advance(0)
    for i in range(2):
        if (closed[i] as Quaternion).angle_to(hinges[i].quaternion) > 0.001:
            fail("Close clip did not return the door to its hinge rest pose")
            return
    player.play("Flags_Wind")
    player.seek(0, true)
    player.advance(0)
    var rest := cloth_values(fabrics)
    player.seek(0.5, true)
    player.advance(0)
    var moving := cloth_values(fabrics)
    for i in range(4):
        if absf(float(moving[i*3+2])-float(rest[i*3+2])) < 0.9:
            fail("Imported fabric does not deform: " + fabrics[i].name)
            return
    player.seek(4.0, true)
    player.advance(0)
    var seam := cloth_values(fabrics)
    for i in range(rest.size()):
        if absf(float(rest[i])-float(seam[i])) > 0.001:
            fail("Cloth loop seam does not close")
            return
    # The wrapper filters importer-created rest tracks, allowing both controllers
    # to advance concurrently without wind resetting the door rotations.
    hall.open_doors()
    player.advance(0.5)
    wind_player.advance(0.5)
    var concurrent := cloth_values(fabrics)
    if (closed[0] as Quaternion).angle_to(hinges[0].quaternion) < 0.4 or float(concurrent[2]) < 0.9:
        fail("Independent wind and door playback failed")
        return
    var collisions := hall.find_children("*", "CollisionShape3D", true, false)
    if collisions.size() != 5:
        fail("Missing coarse collision shapes")
        return
    var report := {"engine": Engine.get_version_info().string, "triangles": triangles,
        "meshes": meshes.size(), "surfaces": surfaces, "glass_alpha": glass_ok,
        "double_sided_fabric": fabric_ok, "clips": clips,
        "door_opening_degrees": opening_degrees, "morph_fabric_objects": fabrics.size(),
        "cloth_loop_seam_verified": true, "independent_playback_verified": true,
        "hinge_positions_fixed": true, "outward_opening_verified": true,
        "colliders": collisions.size()}
    var args := OS.get_cmdline_user_args()
    if args.size() > 0:
        var file := FileAccess.open(args[0], FileAccess.WRITE)
        file.store_string(JSON.stringify(report, "  ") + "\n")
    print("SETTLEMENTS_GODOT_ANIMATIONS_OK ", JSON.stringify(report))
    hall.queue_free()
    quit(0)
