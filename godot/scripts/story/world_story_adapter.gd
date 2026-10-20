extends Node
## A single session owns story time; the world continues to own physical movement.
const Session = preload("res://scripts/story/story_session.gd")
signal office_entered(landmark: String)
signal office_returned(landmark: String)
var session = Session.new()
var world
var modal_active := false

func attach(target) -> void:
    assert(world == null, "Adapter must only attach once")
    world = target
    world.story_adapter = self
    world._layout_ui(true)
    session.changed.connect(_sync)
    session.office_left.connect(_leave)
    _sync()

func _sync() -> void:
    if world == null: return
    world.story_minutes = session.quest_minutes
    world.navigation_locked = modal_active or not session.current_landmark.is_empty() or session.quest_failed or session.invoice_issued
    # Full-screen story layers obscure the diorama. Avoid rendering its meshes
    # behind them on iPhone/CPU WebGL; collisions and authored geometry persist.
    world.world.visible = not world.navigation_locked
    if world.state == "IDLE": world.actor.visible = not world.navigation_locked
    if world.navigation_locked:
        world.touches.clear()
        world.pointer_dragged = false
        world.touch_multi = false

func set_modal(active: bool) -> void:
    modal_active = active
    _sync()

func enter(landmark: String) -> bool:
    if world.navigation_locked or world.state != "IDLE" or world.current_node != landmark:
        return false
    if not session.enter_landmark(landmark, world.actor.position):
        return false
    world.panel.visible = false
    _sync()
    office_entered.emit(landmark)
    return true

func _leave(landmark: String, entrance: Vector3) -> void:
    world.actor.position = entrance
    world.actor.velocity = Vector3.ZERO
    world.current_node = landmark
    world.selected = landmark
    world.panel.visible = false
    world.selection_ring.visible = false
    _sync()
    office_returned.emit(landmark)

func charge(minutes: int, mode: String) -> void:
    session.charge_travel(minutes, mode)
    _sync()

func boat_wait() -> int:
    return session.boat_wait_minutes(world.current_island)
