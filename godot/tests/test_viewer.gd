extends SceneTree


func touch(viewer: Node, index: int, position: Vector2, pressed: bool) -> void:
    var event := InputEventScreenTouch.new()
    event.index = index
    event.position = position
    event.pressed = pressed
    viewer._unhandled_input(event)


func drag(viewer: Node, index: int, position: Vector2) -> void:
    var event := InputEventScreenDrag.new()
    event.index = index
    event.position = position
    viewer._unhandled_input(event)


func _initialize() -> void:
    var viewer = load("res://scenes/main.tscn").instantiate()
    root.add_child(viewer)
    await process_frame
    var island: Node3D = viewer.get_node("GeneratedIsland")
    var meshes := island.find_children("*", "MeshInstance3D", true, false)
    assert(meshes.size() >= 100 and meshes.size() <= 260, "Overworld mesh budget exceeded")
    for expected in ["Settlements Hall", "Trade Finance", "Compliance", "LC Desk",
                     "Coffee Area", "Operations", "Contracts", "VAT Tax", "FX Desk",
                     "Archive Rotunda", "West Tube Station", "East Tube Station",
                     "West Harbor Launch", "East Harbor Launch", "Pedestrian Bridge",
                     "West Island coast", "East Island coast"]:
        assert(island.find_child(expected, true, false) != null, expected)
    assert(viewer.landmark_labels.size() == 14, "Every destination needs a label")
    var west = island.find_child("West Tube Station", true, false)
    var east = island.find_child("East Tube Station", true, false)
    assert(west.position.x < 0 and east.position.x > 0, "Island roles must stay west/east")
    assert(west.find_children("*", "MeshInstance3D", true, false).size() ==
           east.find_children("*", "MeshInstance3D", true, false).size(), "Tube towers must match")
    for name in ["West Harbor Launch", "East Harbor Launch"]:
        var dock = island.find_child(name, true, false)
        assert(absf(dock.position.x) < 8 and absf(dock.position.z) < 3, "Docks must be central")
    var vertices := 0
    for mesh in meshes:
        for surface in range(mesh.mesh.get_surface_count()):
            vertices += mesh.mesh.surface_get_array_len(surface)
    assert(vertices < 100000, "Overworld vertex budget exceeded")
    for mesh in meshes:
        assert(mesh.mesh.get_surface_count() > 0)

    touch(viewer, 3, Vector2(100, 200), true)
    drag(viewer, 3, Vector2(250, 200))
    assert(not is_zero_approx(island.rotation.y), "One-finger drag must rotate")
    var yaw: float = island.rotation.y
    touch(viewer, 7, Vector2(450, 200), true)
    drag(viewer, 7, Vector2(650, 200))
    assert(is_equal_approx(viewer.camera.size, viewer.MIN_ZOOM), "Pinch outward zooms in and clamps")
    assert(is_equal_approx(island.rotation.y, yaw), "Pinch must not also rotate")
    drag(viewer, 7, Vector2(252, 200))
    assert(is_equal_approx(viewer.camera.size, viewer.MAX_ZOOM), "Pinch inward clamps zoom out")
    touch(viewer, 7, Vector2(252, 200), false)
    drag(viewer, 3, Vector2(300, 200))
    assert(not is_equal_approx(island.rotation.y, yaw), "Drag resumes after pinch")
    touch(viewer, 3, Vector2(300, 200), false)
    assert(viewer.touches.is_empty())

    touch(viewer, 1, Vector2(100, 200), true)
    var canceled := InputEventScreenTouch.new()
    canceled.index = 1
    canceled.canceled = true
    viewer._input(canceled)
    assert(viewer.touches.is_empty(), "Canceled touches must clear even over HUD")
    touch(viewer, 1, Vector2(100, 200), true)
    viewer._notification(MainLoop.NOTIFICATION_APPLICATION_FOCUS_OUT)
    assert(viewer.touches.is_empty(), "Focus loss clears touches")
    viewer.reset_view()
    assert(is_zero_approx(island.rotation.y))
    assert(is_equal_approx(viewer.camera.size, viewer.INITIAL_ZOOM))
    print("TELANICO_TEST_OK: two islands, 14 destinations, mesh/vertex budgets; touch rotation, pinch, clamps, release, focus, reset")
    quit(0)
