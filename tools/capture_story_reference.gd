extends SceneTree
## Run ONLY in a disposable project copy containing canonical main.gd and its
## preloaded living textures/shader; import that copy first. Never import/write
## to the source checkout. Pass the output absolute path after --.
## godot --headless --path /tmp/source-copy --script /path/to/this.gd -- /output.json
var Source = load("res://main.gd")
const WIN := ["ops_qty", "ops_report", "ops_full_documents", "trader_price", "contract_entity", "contract_verified_precision", "contract_fixing", "contract_terms", "lc_terms", "lc_docs", "lc_match", "vat_treatment", "fx_rate", "lc_original", "settlements_check", "settlements_release"]
func _initialize() -> void:
    call_deferred("run")
func make_game():
    var game = Source.new()
    game.qa_mode = true
    root.add_child(game)
    game.interaction_body = Label.new()
    game.add_child(game.interaction_body)
    game.dialogue_choices = VBoxContainer.new()
    game.add_child(game.dialogue_choices)
    return game
func snapshot(game) -> Dictionary:
    var result := {}
    for item in game.get_property_list():
        var key := String(item.name)
        if key.begins_with("known_") or key.begins_with("vat_requested_") or key in ["quest_minutes", "invoice_issued", "quest_failed", "original_pack_prepared", "original_signature_required", "ops_full_pack_requested", "trader_price_obtained", "compliance_training_offered", "compliance_warning_pending"]:
            result[key] = game.get(key)
    result["blockers"] = Array(game._release_blockers())
    result["reply"] = game.interaction_body.text + ("\n" + "\n".join(game.pending_dialogue_lines) if not game.pending_dialogue_lines.is_empty() else "")
    result["choices"] = game.pending_dialogue_choices
    return result
func run() -> void:
    var cases := []
    var game = make_game()
    var records := []
    for action in WIN:
        game._choose_dialogue(action)
        records.append({"action": action, "expected": snapshot(game)})
    cases.append({"name":"source_scenario_bot", "initial_minutes":0, "records":records})
    game.queue_free()
    for action in ["ops_estimate", "vat_treatment", "lc_match", "lc_original", "fx_rate", "contract_guess_two", "contract_guess_eight", "compliance_chocolate", "compliance_training", "contract_price", "tf_adjustment", "finance_lc_amount", "finance_fluctuation", "settlements_release"]:
        game = make_game()
        game._choose_dialogue(action)
        cases.append({"name":"initial_"+action, "initial_minutes":0, "records":[{"action":action,"expected":snapshot(game)}]})
        game.queue_free()
    game = make_game()
    game.quest_minutes = 119
    game._choose_dialogue("settlements_release")
    cases.append({"name":"deadline", "initial_minutes":119, "records":[{"action":"settlements_release","expected":snapshot(game)}]})
    game.queue_free()
    var args := OS.get_cmdline_user_args()
    assert(args.size() == 1, "Pass one absolute output path after --")
    var f := FileAccess.open(args[0], FileAccess.WRITE)
    assert(f != null, "Cannot write fixture output")
    f.store_string(JSON.stringify({"source_commit":"fc5e861f0c899ae5925625ff2191a41d7043d957", "cases":cases}, "  ")+"\n")
    print("SOURCE_FIXTURES_GENERATED ",cases.size())
    await process_frame
    quit()
