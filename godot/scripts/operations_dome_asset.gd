extends Node3D
## Operations entrance only; flags in this GLB are static.
var doors: AnimationPlayer

func _ready() -> void:
    var players := $Architecture.find_children("*", "AnimationPlayer", true, false)
    if not players.is_empty():
        doors = players[0] as AnimationPlayer
    else:
        push_warning("Operations V3: imported GLB has no AnimationPlayer")

func open_doors() -> void:
    if doors != null and doors.has_animation("Doors_Open"):
        doors.play("Doors_Open")

func close_doors() -> void:
    if doors != null and doors.has_animation("Doors_Close"):
        doors.play("Doors_Close")
