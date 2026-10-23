extends Control
## Presentation only: actual charged minutes arrive from the authoritative session.
var label: Label
var pending: Array[Dictionary] = []
var history: Array[Dictionary] = []
var playing := false
var stage := ""
var animation: Tween

func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_IGNORE
    label = Label.new()
    label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    label.add_theme_color_override("font_color",Color("#F4EAD5"))
    label.add_theme_color_override("font_outline_color",Color("#07131CEF"))
    label.add_theme_constant_override("outline_size",8)
    add_child(label)
    label.visible = false

func layout(view_size: Vector2) -> void:
    size = view_size
    label.size = Vector2(minf(420,view_size.x-24),minf(240,view_size.y-32))
    label.position = (view_size-label.size)*0.5
    label.pivot_offset = label.size*0.5
    label.add_theme_font_size_override("font_size",44 if view_size.y<500 else 60)

func show_loss(minutes: int, reason: String) -> void:
    if minutes<=0: return
    var event := {"minutes":minutes,"reason":reason}
    history.append(event)
    # Bounded diagnostics; queued events are never merged or silently overwritten.
    if history.size()>100: history.pop_front()
    pending.append(event)
    if not playing: _next()

func _beat(text: String) -> void:
    stage = text
    label.text = text

func _next() -> void:
    if pending.is_empty():
        playing = false
        stage = ""
        label.visible = false
        return
    playing = true
    var event: Dictionary = pending.pop_front()
    var number := str(event.minutes)
    _beat(number)
    label.visible = true
    label.modulate.a = 0
    label.scale = Vector2.ONE*0.84
    animation = create_tween()
    animation.tween_property(label,"modulate:a",1.0,0.12)
    animation.parallel().tween_property(label,"scale",Vector2.ONE,0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
    animation.tween_interval(0.20)
    animation.tween_callback(_beat.bind(number+"\nMINUTES"))
    animation.tween_interval(0.25)
    animation.tween_callback(_beat.bind(number+"\nMINUTES\nLOST!"))
    animation.tween_interval(0.65)
    animation.tween_property(label,"modulate:a",0.0,0.30)
    animation.tween_callback(_next)
