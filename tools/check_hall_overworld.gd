## Focused runtime check: V3 Lite replaces only the Settlements Hall mesh.
## Run after normal Godot import with staged godot/assets/generated/settlements_hall.glb.
extends SceneTree

func _initialize() -> void:
    call_deferred("run")

func run() -> void:
    var game := load("res://scenes/main.tscn").instantiate()
    root.add_child(game)
    await process_frame
    assert(game.sites.size() == 15, "Canonical site registry changed")
    assert(game.graph.route("settlements", "operations") != {}, "Navigation route lost")
    var legacy := game.world.find_child("Site_settlements", true, false) as Node3D
    assert(legacy != null and not legacy.visible, "Old Hall visible or missing")
    var hall: Node3D = game.settlements_hall
    assert(hall != null and hall.name == "SettlementsHallV3Lite", "V3 Lite not instantiated")
    var expected: Vector3 = game.graph.vec(game.sites["settlements"].position) + Vector3(0, 0.04, 2.5)
    assert(hall.position.distance_to(expected) < 0.01, "Hall location not aligned")
    assert(absf(hall.scale.x - 0.55) < 0.001, "Hall footprint changed")
    var optional_body := hall.get_node("OptionalBuildingCollision") as StaticBody3D
    assert(optional_body.collision_layer == 0, "Overlapping preview collisions enabled")
    var players = hall.get_node("Architecture").find_children("*", "AnimationPlayer", true, false)
    assert(players.size() == 1, "GLB animation player not imported")
    var doors := players[0] as AnimationPlayer
    for name in ["Doors_Open", "Doors_Close", "Flags_Wind", "Hall_Demo"]:
        assert(doors.has_animation(name), "Missing V3 clip: " + name)
    var wind := hall.get_node("WindPlayer") as AnimationPlayer
    assert(wind.is_playing(), "Flags did not start independent looping wind")
    hall.call("open_doors")
    assert(doors.current_animation == "Doors_Open", "Doors do not open")
    hall.call("close_doors")
    assert(doors.current_animation == "Doors_Close", "Doors do not close")
    assert(game.sites["settlements"].kind == "office", "Existing office interaction lost")
    print("TELANICO_HALL_GAME_PASS V3 Lite visuals, placement, animations, 15 sites and original navigation")
    quit(0)
