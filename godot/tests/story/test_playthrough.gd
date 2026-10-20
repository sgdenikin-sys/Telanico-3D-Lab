extends SceneTree
var game
var world
var checks := 0
func _initialize(): call_deferred("run")
func check(condition: bool, text: String):
    checks += 1
    assert(condition,text)
func walk(target:String):
    var before:int = game.session.quest_minutes
    var minutes:int = world.graph.route(world.current_node,target).minutes
    world.select_site(target)
    world._action("Walk")
    for i in range(3600):
        await physics_frame
        if world.state=="IDLE":break
    check(world.current_node==target,"Arrived at "+target)
    check(game.session.quest_minutes==before+minutes,"Single walking charge")
func travel(target:String):
    if (world.graph.nodes[world.current_node].x<0)!=(world.graph.nodes[target].x<0):
        var west:bool = world.current_island=="west"
        var origin:String = "tube_w" if west else "tube_e"
        var peer:String = "tube_e" if west else "tube_w"
        var direct:int = world.graph.route(world.current_node,target).minutes
        var tube:int = world.graph.route(world.current_node,origin).minutes+3+world.graph.route(peer,target).minutes
        if tube<direct:
            await walk(origin)
            var before:int = game.session.quest_minutes
            world.start_transfer("tube")
            for i in range(1800):
                await physics_frame
                if world.state=="IDLE":break
            check(world.current_node==peer and game.session.quest_minutes==before+3,"Visible tube transfer")
    await walk(target)
func finish_reply():
    while game.line_index<game.lines.size()-1: game.advance_line()
    if game.penalty_feedback_pending:
        var before:int = game.session.quest_minutes
        game.show_assistant()
        check(game.session.compliance_warning_shown,"Assistant warns about chocolate penalty")
        game.close_modal()
        check(game.session.quest_minutes==before,"Reading penalty feedback is free")
    if game.reward_pending:
        game.show_invoice()
        check(game.invoice_document.applied_state==game.session.invoice_state(),"Rendered invoice uses shared facts")
        game.close_modal()
        check(game.modal_kind=="assistant","Assistant follows verified invoice review")
        game.close_modal()
func answer(action:String):
    finish_reply()
    var button = null
    for candidate in game.choice_list.get_children():
        if candidate.is_visible_in_tree() and candidate.get_meta("dialogue_action","")==action: button=candidate
    check(button!=null,"Canonical choice visible: "+action)
    button.pressed.emit()
    if not game.session.invoice_issued: finish_reply()
func visit(target:String,actions:Array):
    await travel(target)
    check(game.session.current_landmark.is_empty(),"Outside before Enter")
    world._action("Enter")
    check(game.office.visible and world.navigation_locked,"Original office is open")
    check(game.office_npc.texture!=null and game.office_background.texture!=null and game.office_desk.texture!=null,"Original layered art available")
    finish_reply()
    if game.session._office_is_closed(game.session.active_dialogue_destination):answer("__wait_lunch__")
    elif game.session.dialogue_options.any(func(c):return c[1]=="greet_polite"):answer("greet_polite")
    for action in actions: answer(action)
    print("PLAYTHROUGH ",target," ",game.session.quest_minutes)
    if not game.session.invoice_issued:
        var entrance:Vector3 = world.actor.position
        game.session.leave_office()
        check(not game.office.visible and world.actor.position==entrance,"Leave restores exact entrance")
func run():
    game = load("res://scenes/story_game.tscn").instantiate()
    root.add_child(game)
    await process_frame
    world = game.world
    world.test_mode = true
    world.simulation_rate = 12
    check(game.screen=="intro" and world.navigation_locked,"Original story opens modally")
    game._characters()
    check(game.screen=="characters","Character selection follows intro")
    game.start_game()
    check(game.modal_kind=="invoice" and game.session.quest_minutes==0,"Opening draft at 12:00")
    check(game.invoice_document.value_of("cargo")=="High Quality Energy (Physical Oil)","Known product rendered")
    game.close_modal()
    game.close_modal()
    check(not world.navigation_locked,"Map enabled after initial guidance")
    await visit("operations",["ops_qty","ops_report","ops_full_documents"])
    await visit("contracts",["contract_entity","contract_terms","contract_fixing","contract_verified_precision"])
    await visit("trader",["trader_price"])
    await visit("vat",["vat_treatment"])
    await visit("fx",["fx_rate"])
    await visit("lc",["lc_terms","lc_docs","lc_match","lc_original"])
    await visit("settlements",["settlements_check","settlements_release"])
    check(game.session.invoice_issued and not game.session.quest_failed,"Entire actual-geography scenario wins")
    check(game.modal_kind=="result" and world.navigation_locked,"Original victory result blocks map")
    print("TELANICO_PLAYTHROUGH_PASS %d assertions; victory at %s" % [checks,game.session._format_quest_time(720+game.session.quest_minutes)])
    game.queue_free()
    await process_frame
    await create_timer(0.25).timeout
    quit(0)
