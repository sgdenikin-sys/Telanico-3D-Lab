extends ColorRect
## Original VorGun #85DEFF perimeter runner; ignores input and preserves artwork.
static func attach(button: BaseButton) -> void:
    if button.has_node("HudPerimeterRunner"): return
    var runner := ColorRect.new()
    runner.set_script(load("res://scripts/story/button_perimeter.gd"))
    runner.name = "HudPerimeterRunner"
    runner.color = Color("#85DEFF")
    runner.mouse_filter = Control.MOUSE_FILTER_IGNORE
    runner.visible = false
    button.add_child(runner)
    button.pressed.connect(func(): button.set_meta("clicked_active",true))

var chase_time := 0.0
func _process(delta: float) -> void:
    var button := get_parent() as BaseButton
    chase_time += delta
    visible = not button.disabled and (bool(button.get_meta("story_active",false)) or (bool(button.get_meta("clicked_active",false)) and (button.has_focus() or button.is_pressed())))
    if not visible: return
    var w := button.size.x
    var h := button.size.y
    if w < 23 or h < 23: return
    var d := fposmod(chase_time * 105.0,2.0*(w+h))
    if d < w:
        size=Vector2(22,3)
        position=Vector2(clampf(d,0,w-22),0)
    elif d < w+h:
        size=Vector2(3,22)
        position=Vector2(w-3,clampf(d-w,0,h-22))
    elif d < 2*w+h:
        size=Vector2(22,3)
        position=Vector2(clampf(2*w+h-d-22,0,w-22),h-3)
    else:
        size=Vector2(3,22)
        position=Vector2(0,clampf(2*(w+h)-d-22,0,h-22))
