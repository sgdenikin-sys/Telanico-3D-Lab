extends Node
## Presentation and world orchestration only. All quest facts/rules belong to Session.
const Adapter = preload("res://scripts/story/world_story_adapter.gd")
const Art = preload("res://scripts/story/canonical_presentation.gd")
const Invoice = preload("res://scripts/telanico_invoice_document.gd")
const Clock = preload("res://scripts/story/story_clock.gd")
const IVORY := Color("#F4EAD5")
const BRASS := Color("#B99B59")
var world
var adapter
var session
var ui: Control
var hud: Control
var overlay: Control
var office: Control
var office_background: TextureRect
var office_npc: TextureRect
var office_desk: TextureRect
var dialogue_card: PanelContainer
var dialogue_label: Label
var choice_list: VBoxContainer
var speaker: Label
var clock_label: Label
var clock_face
var modal_kind := ""
var screen := "intro"
var lines: Array[String] = []
var line_index := 0
var choices: Array = []
var reward_pending := false
var opening_draft := false
var invoice_document
var modal_column: VBoxContainer
var modal_footer: HBoxContainer
var music: AudioStreamPlayer
var music_on := true
var sfx_on := true
var music_volume := 0.8
var sfx_volume := 0.75
var sfx: AudioStreamPlayer
var texture_cache: Dictionary = {}
var texture_recent: Array[String] = []
var test_mode := false
var ui_buttons: Dictionary = {}
var elapsed := 0.0
var last_world_state := "IDLE"
var dialogue_tween: Tween
var invoice_touches: Dictionary = {}

func _ready() -> void:
    world = load("res://scenes/main.tscn").instantiate()
    add_child(world)
    # The existing V2.1 browser suite uses the standalone navigation fixture.
    # Story tests explicitly request story_test; ordinary players always see intro.
    if OS.has_feature("web"):
        test_mode = bool(JavaScriptBridge.eval("new URLSearchParams(location.search).get('story_test') === '1'"))
        if world.test_mode and not test_mode: return
    adapter = Adapter.new()
    add_child(adapter)
    adapter.attach(world)
    session = adapter.session
    session.dialogue_changed.connect(_dialogue)
    session.changed.connect(_refresh)
    session.result_reached.connect(_result)
    adapter.office_entered.connect(_open_office)
    adapter.office_returned.connect(_return_world)
    var layer := CanvasLayer.new()
    layer.layer = 50
    add_child(layer)
    ui = Control.new()
    ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layer.add_child(ui)
    _build_hud()
    _build_office()
    overlay = Control.new()
    overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    overlay.mouse_filter = Control.MOUSE_FILTER_STOP
    ui.add_child(overlay)
    sfx = AudioStreamPlayer.new()
    add_child(sfx)
    if OS.has_feature("web"):
        AudioServer.set_bus_mute(AudioServer.get_bus_index("Master"), true)
    else:
        music = AudioStreamPlayer.new()
        add_child(music)
        var stream = load("res://assets/audio/music/original_theme.mp3")
        stream.loop = true
        music.stream = stream
        music.volume_db = linear_to_db(music_volume*0.3)
    get_viewport().size_changed.connect(_layout)
    _intro()
    _layout()

func _label(parent: Node, text: String, font_size := 20) -> Label:
    var label := Label.new()
    label.text = text
    label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    label.add_theme_font_size_override("font_size", font_size)
    label.add_theme_color_override("font_color", IVORY)
    parent.add_child(label)
    return label

func _button(parent: Node, text: String, action: Callable) -> Button:
    var button := Button.new()
    button.text = text
    button.custom_minimum_size = Vector2(100,44)
    button.add_theme_font_size_override("font_size",18)
    button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    var style := StyleBoxFlat.new()
    style.bg_color = Color("#112A3BEA")
    style.border_color = BRASS
    style.set_border_width_all(2)
    style.set_corner_radius_all(9)
    style.set_content_margin_all(8)
    button.add_theme_stylebox_override("normal",style)
    parent.add_child(button)
    button.pressed.connect(func():
        _sound("select")
        action.call())
    return button

func _texture(parent: Node, path: String) -> TextureRect:
    var image := TextureRect.new()
    image.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
    image.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    image.mouse_filter = Control.MOUSE_FILTER_IGNORE
    if not path.is_empty(): image.texture = _cached_texture(path)
    parent.add_child(image)
    return image

func _cached_texture(path: String) -> Texture2D:
    if texture_cache.has(path): return texture_cache[path]
    var texture: Texture2D = load(path)
    texture_cache[path] = texture
    texture_recent.append(path)
    while texture_recent.size()>4:
        texture_cache.erase(texture_recent.pop_front())
    return texture

func _art_button(parent: Node, filename: String, action: Callable) -> Button:
    var button := _button(parent,"",action)
    button.set_meta("artwork",filename)
    button.add_theme_stylebox_override("normal",StyleBoxEmpty.new())
    var image := _texture(button,"res://assets/ui/HUD/RUNTIME/"+filename)
    image.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    return button

func _build_hud() -> void:
    hud = Control.new()
    hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
    ui.add_child(hud)
    for item in [["Invoice","hud_invoice_button.png"],["Menu","button_menu.png"],["Diorama","button_diorama_view.png"],["Assistant","button_assistant.png"]]:
        var key: String = item[0]
        ui_buttons[key] = _art_button(hud,item[1],_hud_action.bind(key))
    clock_face = Clock.new()
    hud.add_child(clock_face)
    clock_label = _label(hud,"12:00 · 120 MIN TO 14:00",16)
    clock_label.mouse_filter = Control.MOUSE_FILTER_IGNORE

func _hud_action(key: String) -> void:
    match key:
        "Invoice": show_invoice()
        "Assistant": show_assistant()
        "Menu": show_menu()
        "Diorama":
            if not adapter.modal_active and session.current_landmark.is_empty(): world.reset_view()

func _clear_modal(kind: String) -> VBoxContainer:
    for child in overlay.get_children():
        overlay.remove_child(child)
        child.queue_free()
    invoice_document = null
    modal_kind = kind
    overlay.visible = true
    adapter.set_modal(true)
    var shade := ColorRect.new()
    shade.color = Color("#07131CF5")
    shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    overlay.add_child(shade)
    var panel := PanelContainer.new()
    panel.name = "ModalCard"
    var style := StyleBoxFlat.new()
    style.bg_color = Color("#112638")
    style.border_color = BRASS
    style.set_border_width_all(2)
    style.set_corner_radius_all(12)
    style.set_content_margin_all(12)
    panel.add_theme_stylebox_override("panel",style)
    overlay.add_child(panel)
    var frame := VBoxContainer.new()
    panel.add_child(frame)
    var scroll := ScrollContainer.new()
    scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
    frame.add_child(scroll)
    modal_footer = HBoxContainer.new()
    frame.add_child(modal_footer)
    modal_column = VBoxContainer.new()
    modal_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    modal_column.add_theme_constant_override("separation",10)
    scroll.add_child(modal_column)
    _layout.call_deferred()
    return modal_column

func _intro() -> void:
    screen = "intro"
    hud.visible = false
    var col := _clear_modal("intro")
    _label(col,"VORGUN INVOICE QUEST · PILOT",18)
    _label(col,"THE FIRST BIG DELIVERY",30)
    _label(col,Art.INTRO_TEXT,20)
    _button(modal_footer,"CHOOSE YOUR ROLE",_characters).size_flags_horizontal = Control.SIZE_EXPAND_FILL

func _characters() -> void:
    screen = "characters"
    var col := _clear_modal("characters")
    _label(col,"CHOOSE YOUR ROLE",28)
    _label(col,"Pilot character",18)
    var row := HBoxContainer.new()
    col.add_child(row)
    for spec in [["COOPER","cooper","INVOICING / SETTLEMENTS"],["WOLF","wolf","OPERATIONS"],["EAGLE","eagle","TRADER"],["RILEY","riley","TRADE FINANCE"]]:
        var card := VBoxContainer.new()
        card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        row.add_child(card)
        var portrait := _texture(card,"res://assets/mascots/TOP_DOWN/"+spec[1]+".png")
        portrait.custom_minimum_size = Vector2(80,minf(140,get_viewport().get_visible_rect().size.y*0.25))
        if spec[0]!="COOPER": portrait.modulate = Color(0.08,0.09,0.10,0.72)
        _label(card,spec[0],18)
        _label(card,spec[2],13)
        var button := _button(card,"SELECT COOPER" if spec[0]=="COOPER" else "LOCKED",start_game)
        button.disabled = spec[0]!="COOPER"
    _label(col,"Audio settings: MENU after entering the game",16)

func start_game() -> void:
    if screen != "characters": return
    if music != null and not music.playing: music.play()
    screen = "world"
    hud.visible = true
    opening_draft = true
    show_invoice()

func close_modal() -> void:
    if modal_kind in ["intro","characters","result"]: return
    invoice_touches.clear()
    var closed := modal_kind
    overlay.visible = false
    modal_kind = ""
    adapter.set_modal(false)
    if closed == "invoice" and (opening_draft or reward_pending):
        opening_draft = false
        show_assistant()
    elif closed == "assistant":
        reward_pending = false
        session.assistant_success_pending = false
        _render_dialogue()

func show_invoice() -> void:
    var col := _clear_modal("invoice")
    _label(col,"TELANICO TRADING — SALES INVOICE",22)
    var controls := HBoxContainer.new()
    col.add_child(controls)
    _button(controls,"−",func(): invoice_document.set_manual_zoom(invoice_document.zoom_factor-0.25))
    _button(controls,"+",func(): invoice_document.set_manual_zoom(invoice_document.zoom_factor+0.25))
    _art_button(controls,"button_close_invoice.png",close_modal).custom_minimum_size = Vector2(180,44)
    var scroll := ScrollContainer.new()
    scroll.custom_minimum_size.y = maxf(180,get_viewport().get_visible_rect().size.y-160)
    scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    col.add_child(scroll)
    var center := CenterContainer.new()
    center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    scroll.add_child(center)
    invoice_document = Invoice.new()
    center.add_child(invoice_document)
    invoice_document.apply_state(session.invoice_state())
    invoice_document.set_fit_width(minf(620,get_viewport().get_visible_rect().size.x-72))

func show_assistant() -> void:
    var col := _clear_modal("assistant")
    var emotion: String = session.assistant_feedback_emotion if not session.assistant_feedback_emotion.is_empty() else "greeting"
    if session.compliance_warning_pending or session.quest_minutes>=90: emotion = "clock"
    var portrait := _texture(col,"res://assets/ui/HUD/RUNTIME/rabbit_"+emotion+".png")
    portrait.custom_minimum_size = Vector2(132,132)
    var text: String = session.assistant_recent_praise if not session.assistant_recent_praise.is_empty() else session._assistant_hint()
    if session.compliance_warning_pending:
        text = "OMG, Cooper! You offered a bribe?! Now we lost 45 minutes on mandatory compliance training! No invoice data was verified. We still have to finish the real checks before 14:00."
    _label(col,text,22)
    _button(col,"CONTINUE",close_modal)

func show_menu() -> void:
    var col := _clear_modal("menu")
    _label(col,"MENU",26)
    var music_toggle := CheckButton.new()
    music_toggle.text = "MUSIC"
    music_toggle.button_pressed = music_on
    col.add_child(music_toggle)
    music_toggle.toggled.connect(func(value):
        music_on = value
        _audio_settings())
    var music_slider := HSlider.new()
    music_slider.min_value = 0
    music_slider.max_value = 1
    music_slider.step = 0.01
    music_slider.value = music_volume
    music_slider.custom_minimum_size.y = 44
    col.add_child(music_slider)
    music_slider.value_changed.connect(func(value):
        music_volume = value
        _audio_settings())
    var sfx_toggle := CheckButton.new()
    sfx_toggle.text = "SOUND EFFECTS"
    sfx_toggle.button_pressed = sfx_on
    col.add_child(sfx_toggle)
    sfx_toggle.toggled.connect(func(value):
        sfx_on = value
        _audio_settings())
    var sfx_slider := HSlider.new()
    sfx_slider.min_value = 0
    sfx_slider.max_value = 1
    sfx_slider.step = 0.01
    sfx_slider.value = sfx_volume
    sfx_slider.custom_minimum_size.y = 44
    col.add_child(sfx_slider)
    sfx_slider.value_changed.connect(func(value):
        sfx_volume = value
        _audio_settings())
    _button(col,"RETURN TO GAME",close_modal)

func _audio_settings() -> void:
    if OS.has_feature("web"):
        JavaScriptBridge.eval("window.VorGunAudio?.setMusicEnabled(%s);window.VorGunAudio?.setVolume(%f);window.VorGunAudio?.setSfxEnabled(%s);window.VorGunAudio?.setSfxVolume(%f)" % [str(music_on),music_volume,str(sfx_on),sfx_volume])
    elif music != null:
        music.stream_paused = not music_on
        music.volume_db = linear_to_db(maxf(0.0001,music_volume*0.3))

func _sound(kind: String) -> void:
    if OS.has_feature("web"):
        JavaScriptBridge.eval("window.VorGunAudio?.playAction(%s)" % JSON.stringify(kind))
    elif sfx_on and sfx!=null:
        sfx.stream = load("res://assets/audio/sfx/"+("menu_flip.wav" if kind=="menu" else "select_woosh.wav"))
        sfx.volume_db = linear_to_db(maxf(sfx_volume,0.0001))
        sfx.play()

func _door(opening: bool) -> void:
    if OS.has_feature("web"):
        JavaScriptBridge.eval("window.VorGunAudio?.playDoor(%s)" % str(opening))
    elif sfx_on:
        sfx.stream = load("res://assets/audio/sfx/"+("door_open_office.wav" if opening else "door_close_soft.wav"))
        sfx.play()

func _build_office() -> void:
    office = Control.new()
    office.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    office.mouse_filter = Control.MOUSE_FILTER_STOP
    ui.add_child(office)
    office_background = _texture(office,"")
    office_background.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
    office_background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    office_npc = _texture(office,"")
    office_desk = _texture(office,"")
    dialogue_card = PanelContainer.new()
    var style := StyleBoxFlat.new()
    style.bg_color = Color("#091C2DF2")
    style.border_color = BRASS
    style.set_border_width_all(2)
    style.set_content_margin_all(12)
    dialogue_card.add_theme_stylebox_override("panel",style)
    office.add_child(dialogue_card)
    var frame := VBoxContainer.new()
    dialogue_card.add_child(frame)
    var scroll := ScrollContainer.new()
    scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
    frame.add_child(scroll)
    var col := VBoxContainer.new()
    col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    col.add_theme_constant_override("separation",8)
    scroll.add_child(col)
    speaker = _label(col,"",20)
    dialogue_label = _label(col,"",20)
    choice_list = VBoxContainer.new()
    col.add_child(choice_list)
    var actions := HBoxContainer.new()
    frame.add_child(actions)
    _button(actions,"LEAVE OFFICE",func(): session.leave_office())
    _art_button(actions,"hud_invoice_button.png",show_invoice).custom_minimum_size = Vector2(100,44)
    _art_button(actions,"button_assistant.png",show_assistant).custom_minimum_size = Vector2(100,44)
    office.visible = false

func _open_office(_landmark: String) -> void:
    var art = Art.new()
    var dest: String = session.active_dialogue_destination
    office_background.texture = _cached_texture(art._office_background_path(dest))
    office_npc.texture = _cached_texture(art._office_portrait_path(dest))
    office_desk.texture = _cached_texture(art._office_desk_path(dest))
    speaker.text = dest
    office.visible = true
    _door(true)
    _layout()

func _return_world(_landmark: String) -> void:
    office.visible = false
    _door(false)

func _dialogue(_destination: String, text: String, options: Array) -> void:
    lines.clear()
    for line in text.split("\n",false): lines.append(line)
    line_index = 0
    choices = options.duplicate(true)
    reward_pending = session.assistant_success_pending
    _render_dialogue()

func _render_dialogue() -> void:
    if dialogue_label==null or lines.is_empty(): return
    if dialogue_tween!=null: dialogue_tween.kill()
    dialogue_label.text = lines[line_index]
    dialogue_label.visible_characters = 0
    dialogue_tween = create_tween()
    dialogue_tween.tween_property(dialogue_label,"visible_characters",lines[line_index].length(),clampf(lines[line_index].length()*0.009,0.15,0.85))
    for child in choice_list.get_children():
        choice_list.remove_child(child)
        child.queue_free()
    if line_index<lines.size()-1:
        _button(choice_list,"CONTINUE →",advance_line)
    elif reward_pending:
        _button(choice_list,"CONTINUE →",show_invoice)
    else:
        for option in choices:
            var action: String = option[1]
            var button := _button(choice_list,option[0],func(): session.choose(action))
            button.set_meta("dialogue_action",action)

func advance_line() -> void:
    if line_index<lines.size()-1:
        line_index += 1
        _render_dialogue()

func _refresh() -> void:
    if clock_label==null: return
    var now: int = 720+session.quest_minutes
    clock_label.text = "%s · %d MIN TO 14:00" % [session._format_quest_time(now),maxi(0,120-session.quest_minutes)]
    clock_label.modulate = Color("#FF996E") if session.quest_minutes>=100 else IVORY
    clock_face.minutes = now
    clock_face.queue_redraw()
    if invoice_document!=null: invoice_document.apply_state(session.invoice_state())

func _result(won: bool) -> void:
    office.visible = false
    var col := _clear_modal("result")
    _label(col,"VICTORY!" if won else "GAME OVER",34)
    _label(col,"INVOICE ISSUED & SENT" if won else "DEADLINE MISSED",24)
    _label(col,"The invoice was sent at %s. You made the 14:00 deadline!" % session._format_quest_time(720+session.quest_minutes) if won else "It's 14:00. The invoice deadline has passed, and today's payment window is lost.",20)
    _label(col,"ONE MORE ROUND?" if won else "TRY AGAIN?",20)
    _button(modal_footer,"PLAY AGAIN",restart).size_flags_horizontal = Control.SIZE_EXPAND_FILL

func restart() -> void:
    get_tree().reload_current_scene()

func _layout() -> void:
    if ui==null or not is_inside_tree(): return
    var vp := get_viewport().get_visible_rect().size
    var safe := Vector4.ZERO
    if OS.has_feature("web"):
        var values = JSON.parse_string(str(JavaScriptBridge.eval("window.telanicoViewport?.() || '{}'")))
        if values is Dictionary and float(values.get("width",0))>0:
            var scale_factor: float = vp.x/float(values.width)
            safe = Vector4(float(values.get("left",0)),float(values.get("top",0)),float(values.get("right",0)),float(values.get("bottom",0)))*scale_factor
    for i in range(4):
        var button: Button = ui_buttons.values()[i]
        button.position = Vector2(safe.x+8,safe.y+12+i*52)
        button.size = Vector2(158,48)
    clock_face.position = Vector2(vp.x-safe.z-280,safe.y+8)
    clock_face.size = Vector2(48,48)
    clock_label.position = Vector2(vp.x-safe.z-226,safe.y+18)
    clock_label.size = Vector2(216,32)
    if overlay!=null:
        var card = overlay.get_node_or_null("ModalCard")
        if card!=null:
            card.position = Vector2(safe.x+18,safe.y+12)
            card.size = Vector2(vp.x-safe.x-safe.z-36,vp.y-safe.y-safe.w-24)
    if office_npc!=null and office_npc.texture!=null:
        var composition: Dictionary = Art.new()._office_composition_rects(vp,session.active_dialogue_destination,office_npc.texture.get_size(),office_desk.texture.get_size())
        office_npc.position = composition.npc.position-Vector2(vp.x*0.25,0)
        office_npc.size = composition.npc.size
        office_desk.position = composition.desk.position
        office_desk.size = composition.desk.size
    if dialogue_card!=null:
        dialogue_card.position = Vector2(vp.x*0.44,safe.y+62)
        dialogue_card.size = Vector2(vp.x*0.56-safe.z-12,vp.y-safe.y-safe.w-74)

func _process(delta: float) -> void:
    if adapter==null: return
    # Hide the old debug status. Camera controls and the original world gestures remain.
    world.status.visible = false
    if world.state!=last_world_state:
        if world.state=="TUBE": _sound("flush")
        elif world.state=="BOAT": _sound("boat")
        last_world_state = world.state
    elapsed += delta
    if elapsed>0.25:
        elapsed = 0
        _refresh()
        if test_mode and OS.has_feature("web"): _publish_probe()

func _publish_probe() -> void:
    var rects := {}
    for key in ui_buttons: rects[key] = [ui_buttons[key].position.x,ui_buttons[key].position.y,ui_buttons[key].size.x,ui_buttons[key].size.y]
    var controls := []
    var roots: Array = [overlay] if overlay.visible else [office,hud] if office.visible else [hud]
    for control_root in roots:
        for button in control_root.find_children("*","Button",true,false):
            if button.is_visible_in_tree():
                var rect: Rect2 = button.get_global_rect()
                var clip: Rect2 = Rect2(Vector2.ZERO,get_viewport().get_visible_rect().size)
                var parent: Node = button.get_parent()
                while parent is Control:
                    if parent.clip_contents: clip = clip.intersection(parent.get_global_rect())
                    parent = parent.get_parent()
                controls.append({"clip":[clip.position.x,clip.position.y,clip.size.x,clip.size.y],"text":button.text,"action":button.get_meta("dialogue_action",""),"art":button.get_meta("artwork",""),"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"disabled":button.disabled})
    var data := {"frame":Engine.get_process_frames(),"viewport":[get_viewport().get_visible_rect().size.x,get_viewport().get_visible_rect().size.y],"controls":controls,"screen":screen,"modal":modal_kind,"office":session.current_landmark,"time":session.quest_minutes,"invoice":session.invoice_state(),"failed":session.quest_failed,"won":session.invoice_issued,"choices":choices,"line_index":line_index,"lines":lines.size(),"locked":world.navigation_locked,"hud":rects}
    JavaScriptBridge.eval("window.__TELANICO_STORY="+JSON.stringify(data))

func _input(event: InputEvent) -> void:
    if modal_kind != "invoice" or invoice_document == null: return
    if event is InputEventScreenTouch:
        if event.pressed: invoice_touches[event.index] = event.position
        else: invoice_touches.erase(event.index)
    elif event is InputEventScreenDrag and invoice_touches.has(event.index):
        if invoice_touches.size()==2:
            var keys := invoice_touches.keys()
            var old: float = invoice_touches[keys[0]].distance_to(invoice_touches[keys[1]])
            invoice_touches[event.index] = event.position
            var distance: float = invoice_touches[keys[0]].distance_to(invoice_touches[keys[1]])
            if old>1: invoice_document.set_manual_zoom(invoice_document.zoom_factor*distance/old)
            get_viewport().set_input_as_handled()
        else:
            invoice_touches[event.index] = event.position

func _exit_tree() -> void:
    # Release native mixer playback before scene reload/shutdown. Web retains its
    # canonical browser singleton, so restarting never creates a second track.
    if music!=null:
        music.stop()
        music.stream = null
    if sfx!=null:
        sfx.stop()
        sfx.stream = null
