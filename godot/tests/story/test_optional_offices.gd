extends "res://tests/story/test_playthrough.gd"
func run():
    game = load("res://scenes/story_game.tscn").instantiate()
    root.add_child(game)
    await process_frame
    world = game.world
    world.test_mode = true
    world.simulation_rate = 12
    game._characters()
    game.start_game()
    game.close_modal()
    game.close_modal()
    await visit("finance",["tf_bank","tf_documents"])
    check(game.session.known_lc_bank and not game.session.known_lc_requirements,"Trade Finance directs documentary requirements to LC Desk")
    check(not game.session.known_signature,"Trade Finance cannot sign original")
    var before:int = game.session.quest_minutes
    await visit("finance",["tf_documents"])
    check(game.session.quest_minutes==before+1,"Repeat visit preserves facts and charges only meaningful answer")
    await visit("compliance",["compliance_chocolate","compliance_training"])
    check(game.session.known_compliance_clearance and not game.session.quest_failed,"Training clears optional warning after real travel")
    check(not game.session.invoice_issued,"Optional visit invents no invoice release")
    print("TELANICO_OPTIONAL_OFFICES_PASS %d assertions; actual Trade Finance/repeat and Compliance/chocolate/assistant/training" % checks)
    game.queue_free()
    await process_frame
    await create_timer(0.25).timeout
    quit(0)
