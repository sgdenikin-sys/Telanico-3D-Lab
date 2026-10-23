extends SceneTree
func _initialize(): call_deferred("run")
func run():
    var game = load("res://scenes/story_game.tscn").instantiate()
    root.add_child(game)
    current_scene = game
    await process_frame
    game._characters()
    game.start_game()
    game.close_modal()
    game.close_modal()
    assert(not game.ui_buttons.has("Diorama"))
    assert(is_equal_approx(game.world.speed,9.375))
    assert(game.world.visual.scale.is_equal_approx(Vector3.ONE*3))
    assert(absf(game.clock_face.texture.get_size().aspect()-1.0)<0.1,
        "Clock must use the round canonical dial, not a wide HUD plate")
    for screen in [Vector2i(844,390),Vector2i(667,375),Vector2i(1920,1080)]:
        # Exercise the same CSS-space layout used by the Web presenter.
        root.content_scale_size = screen
        root.size = screen
        await process_frame
        game._layout()
        for button in game.ui_buttons.values():
            assert(button.size.y>=44 and button.position.x>=0 and button.position.y>=0)
        game.show_invoice()
        game._layout()
        for frame in range(3): await process_frame
        var card: Control = game.overlay.get_node("ModalCard")
        assert(card.size.x<screen.x*0.90 and card.size.y<screen.y*0.90,
            "Invoice must leave the world visible: %s" % card.size)
        assert(game.world.world.visible and game.world.actor.visible)
        assert(game.invoice_document.applied_state.cargo=="High Quality Energy (Physical Oil)")
        game.close_modal()
        for kind in ["assistant","menu"]:
            if kind=="assistant":game.show_assistant()
            else:game.show_menu()
            game._layout()
            for frame in range(3):await process_frame
            card=game.overlay.get_node("ModalCard")
            assert(card.size.x<screen.x*0.90 and card.size.y<screen.y*0.90,
                "%s must be compact: %s" % [kind,card.size])
            assert(game.world.navigation_locked,"Modal must block movement")
            assert(game.world.world.visible and game.world.actor.visible,
                "Compact windows must retain the actual 3D world behind them")
            for button in game.modal_footer.get_children():
                var bounds: Rect2 = button.get_global_rect()
                assert(bounds.position.x>=0 and bounds.end.x<=screen.x and bounds.end.y<=screen.y)
                assert(bounds.size.y>=44)
            game.close_modal()
        assert(game.adapter.enter("settlements"))
        for frame in range(3): await process_frame
        game.dialogue_tween.kill()
        var choice_top := 0.0
        for count in [0,12,30,-1]:
            game.dialogue_label.visible_characters=count
            for frame in range(3): await process_frame
            var top: float = game.choice_list.get_global_rect().position.y
            if count==0:choice_top=top
            else:assert(is_equal_approx(top,choice_top),"Typewriter must not move dialogue hit targets")
        for button_name in ["OfficeLeave","OfficeInvoice","OfficeAssistant"]:
            var button = game.dialogue_card.find_child(button_name,true,false)
            var rect: Rect2 = button.get_global_rect()
            assert(rect.position.x>=0 and rect.end.x<=screen.x and rect.end.y<=screen.y,
                "Office footer must remain reachable at %s: %s" % [screen,rect])
            assert(rect.size.y>=44)
        var arrows=game.dialogue_card.find_children("*","Button",true,false)
        for button in arrows:
            if button.text in ["^","v"]:
                assert(button.get_theme_font("font").has_char(button.text.unicode_at(0)),
                    "Scroll utility glyph must be present in bundled Web font")
        if game.office_scroll.get_v_scroll_bar().max_value>game.office_scroll.size.y:
            for button in arrows:
                if button.text=="v":button.pressed.emit()
            assert(game.office_scroll.scroll_vertical>0,"Office arrow must scroll actual overflowing content")
            for button in arrows:
                if button.text=="^":button.pressed.emit()
            assert(game.office_scroll.scroll_vertical==0)
        game.session.leave_office()
    game.show_menu()
    var toggles=game.modal_column.find_children("*","CheckButton",true,false)
    for toggle in toggles:toggle.button_pressed=false
    assert(not game.music_on and not game.sfx_on)
    for toggle in toggles:toggle.button_pressed=true
    var sliders=game.modal_column.find_children("*","HSlider",true,false)
    for slider in sliders:slider.value=0.3
    assert(is_equal_approx(game.music_volume,0.3) and is_equal_approx(game.sfx_volume,0.3))
    game.close_modal()
    assert(game.adapter.enter("settlements"))
    assert(game.clock_face.get_parent()==game.ui and game.clock_face.is_visible_in_tree())
    assert(game.office.get_node("OfficeMenu").is_visible_in_tree())
    game.session.leave_office()
    # Presentation-level penalty feedback; canonical 45-minute rule is also
    # independently covered by source parity and session regressions.
    game.session.active_dialogue_destination = "COMPLIANCE"
    game.session._choose_dialogue("compliance_chocolate")
    assert(game.penalty_feedback_pending and game.session.quest_minutes==45)
    game.show_assistant()
    assert(game.session.compliance_warning_shown)
    game.close_modal()
    assert(not game.session.compliance_warning_pending and not game.penalty_feedback_pending)
    game.session.quest_minutes = 119
    game.session.charge_travel(1,"walk")
    assert(game.modal_kind=="result" and game.session.quest_failed and game.world.navigation_locked)
    # Dispatch a real GUI press/release, not a direct restart() call. Scene
    # replacement must wait until the pressed button's input callback unwinds.
    await process_frame
    await process_frame
    var restart_button: Button
    for button in game.modal_footer.find_children("*","Button",true,false):
        if button.text=="PLAY AGAIN":restart_button=button
    assert(restart_button!=null)
    var restart_point := restart_button.get_global_rect().get_center()
    for pressed in [true,false]:
        var event := InputEventMouseButton.new()
        event.button_index=MOUSE_BUTTON_LEFT
        event.pressed=pressed
        event.position=restart_point
        event.global_position=restart_point
        root.push_input(event,true)
    await process_frame
    await process_frame
    var restarted = current_scene
    assert(restarted!=null and restarted!=game)
    assert(restarted.screen=="intro" and restarted.session.quest_minutes==0 and not restarted.session.quest_failed)
    print("TELANICO_STORY_UI_PASS landscape HUD/invoice, deadline result and real scene restart")
    restarted.queue_free()
    await process_frame
    await process_frame
    quit(0)
