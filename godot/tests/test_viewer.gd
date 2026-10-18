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
    assert(meshes.size() == 35, "Expected both offices and the Coffee Area")
    for expected in ["Settlements Hall body", "Trade Office body", "Coffee Area kiosk",
                     "Coffee Area cup sign", "Coffee Area cup handle", "Coffee Area bench seat"]:
        assert(island.find_child(expected, true, false) != null, expected)
    for mesh in meshes:
        assert(mesh.mesh.get_surface_count() > 0)

    touch(viewer, 3, Vector2(100, 200), true)
    drag(viewer, 3, Vector2(250, 200))
    assert(not is_zero_approx(island.rotation.y), "One-finger drag must rotate")
    var yaw: float = island.rotation.y
    touch(viewer, 7, Vector2(450, 200), true)
    drag(viewer, 7, Vector2(650, 200))
    assert(is_equal_approx(viewer.camera.size, 7.0), "Pinch outward zooms in and clamps")
    assert(is_equal_approx(island.rotation.y, yaw), "Pinch must not also rotate")
    drag(viewer, 7, Vector2(252, 200))
    assert(is_equal_approx(viewer.camera.size, 18.0), "Pinch inward clamps zoom out")
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
    assert(is_equal_approx(viewer.camera.size, 12.0))
    print("TELANICO_TEST_OK: 35 meshes; touch rotation, pinch, clamps, release, focus, reset")
    quit(0)
