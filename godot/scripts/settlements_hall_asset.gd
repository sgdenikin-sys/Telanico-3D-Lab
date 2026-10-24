## Standalone asset controls. Wind and door animations run independently.
extends Node3D

var doors: AnimationPlayer
var wind: AnimationPlayer


func _ready() -> void:
    var architecture := get_node("Architecture")
    doors = architecture.find_children("*", "AnimationPlayer", true, false)[0]
    wind = AnimationPlayer.new()
    wind.name = "WindPlayer"
    wind.root_node = NodePath("../Architecture")
    add_child(wind)
    var loop := doors.get_animation("Flags_Wind").duplicate() as Animation
    # Godot adds constant rest-rotation tracks during glTF import. Keep the
    # wind player's tracks limited to cloth so it never overrides the doors.
    for i in range(loop.get_track_count() - 1, -1, -1):
        if loop.track_get_type(i) != Animation.TYPE_BLEND_SHAPE:
            loop.remove_track(i)
    loop.loop_mode = Animation.LOOP_LINEAR
    var library := AnimationLibrary.new()
    library.add_animation("Wind", loop)
    wind.add_animation_library("", library)
    for fabric in architecture.find_children("Flag_*", "MeshInstance3D", true, false):
        fabric.extra_cull_margin = 0.6
    wind.play("Wind")


func open_doors() -> void:
    if not wind.is_playing():
        wind.play("Wind")
    doors.play("Doors_Open")


func close_doors() -> void:
    if not wind.is_playing():
        wind.play("Wind")
    doors.play("Doors_Close")


func play_demo() -> void:
    wind.stop()
    doors.play("Hall_Demo")
