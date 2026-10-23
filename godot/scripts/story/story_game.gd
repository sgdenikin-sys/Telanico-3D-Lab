extends Node
## Presentation and world orchestration only. All quest facts/rules belong to Session.
const Adapter = preload("res://scripts/story/world_story_adapter.gd")
const Art = preload("res://scripts/story/canonical_presentation.gd")
const Invoice = preload("res://scripts/telanico_invoice_document.gd")
const Perimeter = preload("res://scripts/story/button_perimeter.gd")
const TimeTitles = preload("res://scripts/story/time_loss_titles.gd")
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
var office_scroll: ScrollContainer
var speaker: Label
var clock_label: Label
var clock_face
var modal_kind := ""
var screen := "intro"
var lines: Array[String] = []
var line_index := 0
var choices: Array = []
var reward_pending := false
var penalty_feedback_pending := false
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
var invoice_scroll: ScrollContainer
var time_titles
var assistant_slot: Control
var assistant_portrait: TextureRect
var assistant_backdrop: ColorRect
var assistant_gif_open := false
var assistant_gif_elapsed := 0.0

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
    for button in world.top_buttons.values()+world.buttons.values(): Perimeter.attach(button)
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
    ui.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
    ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
    layer.add_child(ui)
    _build_hud()
    _build_office()
    clock_face.reparent(ui)
    clock_label.reparent(ui)
    overlay = Control.new()
    overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    overlay.mouse_filter = Control.MOUSE_FILTER_STOP
    ui.add_child(overlay)
    time_titles = TimeTitles.new()
    ui.add_child(time_titles)
    session.minutes_spent.connect(time_titles.show_loss)
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
    button.custom_minimum_size = Vector2(100,52)
    button.add_theme_font_size_override("font_size",20)
    button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    var style := StyleBoxFlat.new()
    style.bg_color = Color("#112A3BEA")
    style.border_color = BRASS
    style.set_border_width_all(2)
    style.set_corner_radius_all(9)
    style.set_content_margin_all(8)
    button.add_theme_stylebox_override("normal",style)
    parent.add_child(button)
    Perimeter.attach(button)
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
    button.move_child(button.get_node("HudPerimeterRunner"),-1)
    return button

func _build_hud() -> void:
    hud = Control.new()
    hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
    ui.add_child(hud)
    for item in [["Invoice","hud_invoice_button.png"],["Menu","button_menu.png"],["Assistant","button_assistant.png"]]:
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

func _clear_modal(kind: String) -> VBoxContainer:
    _hide_assistant_gif()
    assistant_portrait = null
    assistant_slot = null
    assistant_backdrop = null
    invoice_scroll = null
    for child in overlay.get_children():
        # Keep bound invoice tweens inside the tree until queued destruction.
        # Removing first makes Web's tween scheduler call can_process off-tree.
        child.name = "RetiredModal"
        if child is Control: child.visible = false
        child.queue_free()
    invoice_document = null
    modal_kind = kind
    overlay.visible = true
    adapter.set_modal(true,kind not in ["menu","assistant","invoice"])
    var shade := ColorRect.new()
    shade.color = Color("#07131C55") if kind in ["menu","assistant","invoice"] else Color("#07131CF5")
    shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    overlay.add_child(shade)
    var panel := PanelContainer.new()
    panel.name = "ModalCard"
    var style := StyleBoxFlat.new()
    style.bg_color = Color("#112638")
    style.border_color = BRASS
    style.set_border_width_all(2)
    style.set_corner_radius_all(12)
    style.set_content_margin_all(6 if kind=="assistant" else 12)
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
        portrait.custom_minimum_size = Vector2(80,minf(140,ui.size.y*0.25))
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
    _hide_assistant_gif()
    var closed := modal_kind
    overlay.visible = false
    modal_kind = ""
    adapter.set_modal(false)
    if closed == "invoice" and (opening_draft or reward_pending):
        opening_draft = false
        show_assistant()
    elif closed == "assistant":
        session.compliance_warning_pending = false
        penalty_feedback_pending = false
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
    _art_button(controls,"button_close_invoice.png",close_modal).custom_minimum_size = Vector2(196,52)
    var scroll := ScrollContainer.new()
    invoice_scroll = scroll
    scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
    scroll.custom_minimum_size.y = maxf(96,_modal_size("invoice").y-130)
    scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    col.add_child(scroll)
    var center := CenterContainer.new()
    center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    scroll.add_child(center)
    invoice_document = Invoice.new()
    center.add_child(invoice_document)
    invoice_document.apply_state(session.invoice_state())
    invoice_document.set_fit_width(minf(620,_modal_size("invoice").x-60))

func show_assistant() -> void:
    var col := _clear_modal("assistant")
    if session.compliance_warning_pending: session.compliance_warning_shown = true
    var emotion: String = session.assistant_feedback_emotion if not session.assistant_feedback_emotion.is_empty() else "greeting"
    if session.compliance_warning_pending or session.quest_minutes>=90: emotion = "clock"
    # Reuse the canonical framed/clipped portrait and ivory speech bubble.
    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation",6)
    col.add_child(row)
    assistant_slot = Control.new()
    assistant_slot.name = "AssistantMediaSlot"
    assistant_slot.custom_minimum_size = Vector2(132,132)
    assistant_slot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
    row.add_child(assistant_slot)
    assistant_backdrop = ColorRect.new()
    assistant_backdrop.name = "RabbitPortraitBackdrop"
    assistant_backdrop.color = Color("#120e0d")
    assistant_backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
    assistant_slot.add_child(assistant_backdrop)
    assistant_backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    assistant_backdrop.offset_left = 9
    assistant_backdrop.offset_top = 12
    assistant_backdrop.offset_right = -9
    assistant_backdrop.offset_bottom = -9
    var clip := Control.new()
    clip.name = "RabbitArtworkClip"
    clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
    clip.clip_contents = true
    assistant_slot.add_child(clip)
    clip.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    clip.offset_left = 15
    clip.offset_top = 19
    clip.offset_right = -15
    clip.offset_bottom = -14
    assistant_portrait = _texture(clip,"res://assets/ui/HUD/RUNTIME/rabbit_"+emotion+".png")
    assistant_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
    assistant_portrait.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    var frame := _texture(assistant_slot,"res://assets/ui/HUD/RUNTIME/hud_assistant_video_frame.png")
    frame.name = "AssistantVideoFrame"
    frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    var speech := PanelContainer.new()
    speech.name = "RabbitSpeechBubble"
    speech.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    var bubble := StyleBoxFlat.new()
    bubble.bg_color = Color("#E6EBDDF7")
    bubble.border_color = BRASS
    bubble.set_border_width_all(1)
    bubble.set_corner_radius_all(10)
    bubble.set_content_margin_all(8)
    speech.add_theme_stylebox_override("panel",bubble)
    row.add_child(speech)
    var advice_scroll := ScrollContainer.new()
    advice_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
    advice_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
    advice_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    speech.add_child(advice_scroll)
    var text: String = session.assistant_recent_praise if not session.assistant_recent_praise.is_empty() else session._assistant_hint()
    if session.compliance_warning_pending:
        text = "OMG, Cooper! You offered a bribe?! Now we lost 45 minutes on mandatory compliance training! No invoice data was verified. We still have to finish the real checks before 14:00."
    var message := _label(advice_scroll,text,18)
    message.add_theme_color_override("font_color",Color("#183047"))
    message.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    _button(modal_footer,"CONTINUE",close_modal).size_flags_horizontal = Control.SIZE_EXPAND_FILL

func _hide_assistant_gif() -> void:
    if OS.has_feature("web") and assistant_gif_open:
        JavaScriptBridge.eval("window.VorGunRabbit?.hide()")
    assistant_gif_open = false
    assistant_gif_elapsed = 0.0

func _sync_assistant_gif(delta: float) -> void:
    if not OS.has_feature("web"): return
    if modal_kind != "assistant" or not overlay.visible or not is_instance_valid(assistant_portrait):
        _hide_assistant_gif()
        return
    assistant_gif_elapsed += delta
    if assistant_gif_open and assistant_gif_elapsed < 0.18: return
    assistant_gif_elapsed = 0.0
    var bridge = JavaScriptBridge.get_interface("VorGunRabbit")
    if bridge == null: return # The canonical PNG stays visible if GIF is unavailable.
    var rect := assistant_portrait.get_global_rect()
    var vp := get_viewport().get_visible_rect().size
    if rect.size.x <= 1 or rect.size.y <= 1: return
    if assistant_gif_open:
        bridge.sync(rect.position.x,rect.position.y,rect.size.x,rect.size.y,vp.x,vp.y)
    else:
        bridge.show(rect.position.x,rect.position.y,rect.size.x,rect.size.y,vp.x,vp.y)
        assistant_gif_open = true
    var matte: String = str(bridge.getBackgroundColor())
    if matte.begins_with("#") and matte.length() == 7:
        assistant_backdrop.color = Color(matte)

func show_menu() -> void:
    var col := _clear_modal("menu")
    _label(col,"MENU",26)
    var music_row := HBoxContainer.new()
    col.add_child(music_row)
    var music_toggle := CheckButton.new()
    music_toggle.text = "MUSIC"
    music_toggle.custom_minimum_size.y = 52
    music_toggle.button_pressed = music_on
    music_toggle.custom_minimum_size.x = 170
    music_row.add_child(music_toggle)
    music_toggle.toggled.connect(func(value):
        music_on = value
        _audio_settings())
    var music_slider := HSlider.new()
    music_slider.min_value = 0
    music_slider.max_value = 1
    music_slider.step = 0.01
    music_slider.value = music_volume
    music_slider.custom_minimum_size.y = 52
    music_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    music_row.add_child(music_slider)
    music_slider.value_changed.connect(func(value):
        music_volume = value
        _audio_settings())
    var sfx_row := HBoxContainer.new()
    col.add_child(sfx_row)
    var sfx_toggle := CheckButton.new()
    sfx_toggle.text = "SOUND EFFECTS"
    sfx_toggle.custom_minimum_size.y = 52
    sfx_toggle.button_pressed = sfx_on
    sfx_toggle.custom_minimum_size.x = 170
    sfx_row.add_child(sfx_toggle)
    sfx_toggle.toggled.connect(func(value):
        sfx_on = value
        _audio_settings())
    var sfx_slider := HSlider.new()
    sfx_slider.min_value = 0
    sfx_slider.max_value = 1
    sfx_slider.step = 0.01
    sfx_slider.value = sfx_volume
    sfx_slider.custom_minimum_size.y = 52
    sfx_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    sfx_row.add_child(sfx_slider)
    sfx_slider.value_changed.connect(func(value):
        sfx_volume = value
        _audio_settings())
    _button(modal_footer,"RESUME GAME",close_modal).size_flags_horizontal = Control.SIZE_EXPAND_FILL
    _button(modal_footer,"RESTART GAME",restart).size_flags_horizontal = Control.SIZE_EXPAND_FILL

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
    office_scroll = scroll
    scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
    scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
    scroll.follow_focus = true
    frame.add_child(scroll)
    var col := VBoxContainer.new()
    col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    col.add_theme_constant_override("separation",8)
    scroll.add_child(col)
    speaker = _label(col,"",20)
    dialogue_label = _label(col,"",20)
    # Reveal glyphs without changing wrapped height or moving dialogue choices.
    dialogue_label.visible_characters_behavior = TextServer.VC_CHARS_AFTER_SHAPING
    choice_list = VBoxContainer.new()
    col.add_child(choice_list)
    var footer := VBoxContainer.new()
    frame.add_child(footer)
    var actions := HBoxContainer.new()
    footer.add_child(actions)
    var leave := _button(actions,"LEAVE OFFICE",func(): session.leave_office())
    leave.name = "OfficeLeave"
    leave.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    # Always-reachable scroll controls are essential on short landscape phones.
    # They operate the real ScrollContainer, never the dialogue/session state.
    var up := _button(actions,"^",_scroll_office.bind(-1))
    up.custom_minimum_size = Vector2(52,52)
    var down := _button(actions,"v",_scroll_office.bind(1))
    down.custom_minimum_size = Vector2(52,52)
    var office_tools := HBoxContainer.new()
    footer.add_child(office_tools)
    var invoice_button := _art_button(office_tools,"hud_invoice_button.png",show_invoice)
    invoice_button.name = "OfficeInvoice"
    invoice_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    var assistant_button := _art_button(office_tools,"button_assistant.png",show_assistant)
    assistant_button.name = "OfficeAssistant"
    assistant_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    var menu := _art_button(office,"button_menu.png",show_menu)
    menu.name = "OfficeMenu"
    menu.position = Vector2(8,8)
    menu.size = Vector2(208,60)
    office.visible = false

func _scroll_office(direction: int) -> void:
    if office_scroll == null or not office_scroll.is_visible_in_tree(): return
    var bar := office_scroll.get_v_scroll_bar()
    var limit := maxf(0.0, bar.max_value - bar.page)
    var shift := maxf(90.0, office_scroll.size.y * 0.7)
    office_scroll.scroll_vertical = roundi(clampf(
        float(office_scroll.scroll_vertical) + direction * shift, 0.0, limit))

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
    penalty_feedback_pending = session.compliance_warning_pending
    _render_dialogue()

func _render_dialogue() -> void:
    if dialogue_label==null or lines.is_empty(): return
    if dialogue_tween!=null: dialogue_tween.kill()
    dialogue_label.text = lines[line_index]
    dialogue_label.visible_characters = 0
    dialogue_tween = create_tween()
    dialogue_tween.tween_property(dialogue_label,"visible_characters",lines[line_index].length(),clampf(lines[line_index].length()*0.009,0.15,0.85))
    for child in choice_list.get_children():
        # A pressed button must remain in-tree until its GUI callback unwinds.
        child.visible = false
        child.queue_free()
    if line_index<lines.size()-1:
        _button(choice_list,"CONTINUE >",advance_line)
    elif penalty_feedback_pending:
        _button(choice_list,"CONTINUE >",show_assistant)
    elif reward_pending:
        _button(choice_list,"CONTINUE >",show_invoice)
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
    # Keep the pressed Control in-tree until GUI/touch dispatch has returned.
    get_tree().call_deferred("reload_current_scene")

func _modal_size(kind: String) -> Vector2:
    var vp := ui.size
    match kind:
        "menu": return Vector2(minf(520,vp.x*0.80),minf(260,vp.y*0.82))
        "assistant": return Vector2(minf(520,vp.x*0.82),minf(230,vp.y-220))
        "invoice": return Vector2(minf(680,vp.x*0.82),vp.y*0.82)
    return vp-Vector2(36,24)

func _layout() -> void:
    if ui==null or not is_inside_tree(): return
    var vp := get_viewport().get_visible_rect().size
    var units := 1.0
    var safe := Vector4.ZERO
    if OS.has_feature("web"):
        var values = JSON.parse_string(str(JavaScriptBridge.eval("window.telanicoViewport?.() || '{}'")))
        if values is Dictionary and float(values.get("width",0))>0:
            units = vp.x/float(values.width)
            safe = Vector4(float(values.get("left",0)),float(values.get("top",0)),float(values.get("right",0)),float(values.get("bottom",0)))
    # Match CSS touch sizes without changing the approved Godot/Safari viewport.
    # Child hit rectangles and fonts scale together; world gestures stay untouched.
    ui.scale = Vector2(units,units)
    vp /= units
    ui.size = vp
    for i in range(ui_buttons.size()):
        var button: Button = ui_buttons.values()[i]
        var short := vp.y<500
        button.position = Vector2(safe.x+8,safe.y+12+i*(60 if short else 72))
        button.size = Vector2(200 if short else 228,54 if short else 66)
    clock_face.position = Vector2(vp.x-safe.z-280,safe.y+8)
    clock_face.size = Vector2(48,48)
    clock_label.position = Vector2(vp.x-safe.z-226,safe.y+18)
    clock_label.size = Vector2(216,32)
    if time_titles != null: time_titles.layout(vp)
    if overlay!=null:
        var card = overlay.get_node_or_null("ModalCard")
        if card!=null:
            if modal_kind=="assistant":
                var anchor: Button = ui_buttons.Assistant
                var top := anchor.position.y+anchor.size.y+8
                var height := minf(230,vp.y-safe.w-top-12)
                # Reserve footer and margins; shrink only the portrait on short phones.
                var side := minf(132,maxf(66,height-76))
                assistant_slot.custom_minimum_size = Vector2(side,side)
                card.size = Vector2(minf(520,(vp.x-safe.x-safe.z)*0.82),height)
            else:
                card.size = _modal_size(modal_kind)
            card.position = Vector2(safe.x,safe.y)+(vp-Vector2(safe.x+safe.z,safe.y+safe.w)-card.size)*0.5
            if modal_kind=="assistant":
                card.position = Vector2(ui_buttons.Assistant.position.x,ui_buttons.Assistant.position.y+ui_buttons.Assistant.size.y+8)
            if invoice_scroll != null:
                invoice_scroll.custom_minimum_size.y = maxf(96,card.size.y-130)
            if invoice_document != null:
                invoice_document.set_fit_width(minf(620,card.size.x-60))
    if office_npc!=null and office_npc.texture!=null:
        var composition: Dictionary = Art.new()._office_composition_rects(vp,session.active_dialogue_destination,office_npc.texture.get_size(),office_desk.texture.get_size())
        office_npc.position = composition.npc.position-Vector2(vp.x*0.25,0)
        office_npc.size = composition.npc.size
        office_desk.position = composition.desk.position
        office_desk.size = composition.desk.size
    if dialogue_card!=null:
        for button_name in ["OfficeLeave","OfficeInvoice","OfficeAssistant"]:
            var button = dialogue_card.find_child(button_name,true,false)
            if button!=null:
                button.custom_minimum_size=Vector2((156 if vp.x<760 else 180) if button_name!="OfficeLeave" else 130,56)
        dialogue_card.position = Vector2(vp.x*0.44,safe.y+62)
        dialogue_card.size = Vector2(vp.x*0.56-safe.z-12,vp.y-safe.y-safe.w-74)

func _process(delta: float) -> void:
    if adapter==null: return
    _sync_assistant_gif(delta)
    for key in ui_buttons: ui_buttons[key].set_meta("story_active",overlay.visible and modal_kind==key.to_lower())
    for pair in [["OfficeMenu","menu"],["OfficeInvoice","invoice"],["OfficeAssistant","assistant"]]:
        var office_button = office.find_child(pair[0],true,false)
        if office_button!=null: office_button.set_meta("story_active",overlay.visible and modal_kind==pair[1])
    for pair in [["Explore",world.inspect_mode],["Follow",world.follow_character],["Names",world.show_names]]:
        world.top_buttons[pair[0]].set_meta("story_active",pair[1])
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
        _layout()
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
    var card = overlay.get_node_or_null("ModalCard")
    var card_rect: Rect2 = card.get_global_rect() if card != null else Rect2()
    var data := {"frame":Engine.get_process_frames(),"viewport":[get_viewport().get_visible_rect().size.x,get_viewport().get_visible_rect().size.y],"controls":controls,"screen":screen,"modal":modal_kind,"office":session.current_landmark,"time":session.quest_minutes,"invoice":session.invoice_state(),"failed":session.quest_failed,"won":session.invoice_issued,"choices":choices,"line_index":line_index,"lines":lines.size(),"locked":world.navigation_locked,"hud":rects,"modal_rect":[card_rect.position.x,card_rect.position.y,card_rect.size.x,card_rect.size.y],"walk_speed":world.speed,"courier_scale":world.visual.scale.x,"clock_art":clock_face.texture.resource_path,"assistant_png":assistant_portrait.texture.resource_path if is_instance_valid(assistant_portrait) else ""}
    data["time_titles"] = {"stage":time_titles.stage,"history":time_titles.history}
    data["assistant_framed"] = is_instance_valid(assistant_slot) and assistant_slot.has_node("AssistantVideoFrame")
    data["world_visible"] = world.world.visible
    data["courier_visible"] = world.actor.visible
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
    _hide_assistant_gif()
    # Release native mixer playback before scene reload/shutdown. Web retains its
    # canonical browser singleton, so restarting never creates a second track.
    if music!=null:
        music.stop()
        music.stream = null
    if sfx!=null:
        sfx.stop()
        sfx.stream = null
