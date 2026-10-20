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
    for screen in [Vector2i(844,390),Vector2i(667,375),Vector2i(1920,1080)]:
        root.size = screen
        await process_frame
        game._layout()
        for button in game.ui_buttons.values():
            assert(button.size.y>=44 and button.position.x>=0 and button.position.y>=0)
        game.show_invoice()
        assert(game.invoice_document.applied_state.cargo=="High Quality Energy (Physical Oil)")
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
    game.restart()
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
