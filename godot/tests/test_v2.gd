extends SceneTree
var game
func fail(message):
    push_error(message)
    quit(1)
func _initialize():
    call_deferred("run")
func travel(target):
    game.start_walk(target)
    var frames=0
    while game.state != "IDLE" and frames<1800:
        await physics_frame
        frames+=1
        if frames%300==0:
            print("WALK_PROGRESS ",target," ",game.actor.position," waypoint ",game.walk_index," next ",game.walk_points[game.walk_index])
            for n in range(game.actor.get_slide_collision_count()): print("COLLIDER ",game.actor.get_slide_collision(n).get_collider().get_parent().name, " normal ",game.actor.get_slide_collision(n).get_normal())
    assert(game.state=="IDLE", "Walking stalled: "+target)
    assert(game.current_node==target)
    assert(game.actor.position.distance_to(game.graph.nodes[target])<1)
func run():
    game=load("res://scenes/main.tscn").instantiate()
    root.add_child(game)
    await process_frame
    game.simulation_rate=12
    assert(game.sites.size()==15)
    assert(game.animation != null and not game.idle_animation.is_empty() and not game.walk_animation.is_empty())
    assert(game.current_node=="settlements")
    game.select_site("finance")
    assert(game.panel.visible and game.walk_plan.minutes>0)
    game._action("Cancel")
    assert(game.story_minutes==0 and game.state=="IDLE")
    await travel("finance")
    await travel("operations")
    await travel("dock_w")
    var before=game.story_minutes
    var bridge=game.graph.route("dock_w","dock_e")
    await travel("dock_e")
    assert(game.story_minutes-before==bridge.minutes and bridge.minutes>=14)
    before=game.story_minutes
    game.start_transfer("boat")
    for i in range(1800):
        await physics_frame
        if game.state=="IDLE":break
    assert(game.current_node=="dock_w" and game.last_trip.kind=="boat")
    assert(game.story_minutes-before==5)
    await travel("tube_w")
    before=game.story_minutes
    game.start_transfer("tube")
    for i in range(600):
        await physics_frame
        if game.state=="IDLE":break
    assert(game.current_node=="tube_e" and game.story_minutes-before==3)
    await travel("trader")
    await travel("archive")
    await travel("fx")
    game._top_action("Explore")
    assert(game.inspect_mode)
    game._top_action("Explore")
    game.reset_view()
    assert(game.camera_yaw==0 and game.camera_elevation==60)
    print("TELANICO_TEST_OK real physics walking, bridge, boat, tube, rig, entrances, cancellation")
    quit(0)
