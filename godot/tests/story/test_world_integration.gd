extends SceneTree
const Adapter = preload("res://scripts/story/world_story_adapter.gd")
var world
var adapter
var checks := 0
func _initialize(): call_deferred("run")
func check(value: bool, message: String):
    checks += 1
    assert(value, message)
func walk(id: String):
    var expected: int = world.graph.route(world.current_node, id).minutes
    var before: int = adapter.session.quest_minutes
    world.select_site(id)
    world._action("Walk")
    for i in range(3600):
        await physics_frame
        if world.state == "IDLE": break
    check(world.current_node == id and world.state == "IDLE", "Physical arrival: " + id)
    check(adapter.session.quest_minutes == before+expected, "Walking charges once: " + id)
    var charged: int = adapter.session.quest_minutes
    world._arrive()
    check(adapter.session.quest_minutes == charged, "Duplicate arrival cannot recharge")
func transfer(mode: String):
    var wait_minutes: int = adapter.boat_wait() if mode == "boat" else 0
    var before: int = adapter.session.quest_minutes
    world.start_transfer(mode)
    for i in range(1800):
        await physics_frame
        if world.state == "IDLE": break
    check(world.state == "IDLE", "Transfer finished")
    check(adapter.session.quest_minutes == before+wait_minutes+(5 if mode=="boat" else 3), "Canonical transfer charge including wait")
    check(world.story_minutes == adapter.session.quest_minutes, "World clock mirrors authoritative session")
func run():
    world = load("res://scenes/main.tscn").instantiate()
    root.add_child(world)
    await process_frame
    world.test_mode = true
    world.simulation_rate = 12
    adapter = Adapter.new()
    root.add_child(adapter)
    adapter.attach(world)
    check(not adapter.enter("operations"), "Cannot enter before physical arrival")
    await walk("operations")
    check(adapter.session.current_landmark.is_empty(), "Arrival remains outside")
    var entrance: Vector3 = world.actor.position
    world._action("Enter")
    check(adapter.session.current_landmark=="operations" and world.navigation_locked, "Explicit Enter opens shared session")
    var previous: String = world.current_node
    world.start_walk("vat")
    world.start_transfer("tube")
    world.select_site("vat")
    check(world.current_node==previous and world.state=="IDLE", "Office blocks navigation commands")
    adapter.session.choose("greet_polite")
    adapter.session.choose("ops_qty")
    adapter.session.leave_office()
    check(not world.navigation_locked and world.actor.position==entrance, "Return to exact entrance")
    check(adapter.session.known_final_quantity, "Invoice progress survives return")
    adapter.set_modal(true)
    world.start_walk("lc")
    check(world.state=="IDLE", "Modal blocks world movement")
    adapter.set_modal(false)
    await walk("dock_w")
    var bridge = world.graph.route("dock_w","dock_e")
    check(bridge.minutes>=14, "Bridge remains slow crossing")
    await walk("dock_e")
    await transfer("boat")
    check(world.current_node=="dock_w", "Scheduled boat returns through inner docks")
    await walk("tube_w")
    await transfer("tube")
    check(world.current_node=="tube_e", "Tube reaches matching station")
    check(not adapter.enter("archive") and not adapter.enter("coffee"), "No invented non-quest interior")
    print("TELANICO_WORLD_STORY_PASS %d assertions; physical walking, bridge, scheduled ferry, tube, explicit office and modal lock" % checks)
    quit(0)
