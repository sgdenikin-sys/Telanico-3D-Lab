extends TextureRect
var minutes := 720
func _ready() -> void:
    texture = load("res://assets/ui/HUD/RUNTIME/clock_analog_blue.png")
    expand_mode = TextureRect.EXPAND_IGNORE_SIZE
    stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    mouse_filter = Control.MOUSE_FILTER_IGNORE
func _draw() -> void:
    var center := size*0.5
    var radius := minf(size.x,size.y)*0.32
    for spec in [[float(minutes%60)/60.0,1.0,2.0],[float(minutes%720)/720.0,0.62,3.0]]:
        var angle: float = float(spec[0])*TAU-PI*0.5
        draw_line(center,center+Vector2(cos(angle),sin(angle))*radius*float(spec[1]),Color("#D7B46E"),float(spec[2]),true)
    draw_circle(center,2,Color("#D7B46E"))
