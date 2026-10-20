extends SceneTree

const Session = preload("res://scripts/story/story_session.gd")
var failures: Array[String] = []
var assertions := 0

func check(condition: bool, message: String) -> void:
    assertions += 1
    if not condition:
        failures.append(message)
        push_error(message)

func _initialize() -> void:
    call_deferred("run")

func run() -> void:
    test_canonical_scenario()
    test_evidence_and_wrong_answers()
    test_transitions_and_persistence()
    test_lunch_and_transport()
    test_deadline_and_compliance()
    if failures.is_empty():
        print("TELANICO_STORY_SESSION_PASS %d assertions" % assertions)
        quit(0)
    else:
        quit(1)

func test_canonical_scenario() -> void:
    # Source tests/navigation_regression.gd:test_scenario_bot, same 16 actions.
    var game = Session.new()
    var draft: Dictionary = game.invoice_state()
    check(game.quest_minutes == 0, "Start at 12:00")
    check(draft.cargo == "High Quality Energy (Physical Oil)", "Product initially known")
    for field in ["seller", "quantity", "unit_price", "total", "invoice_no", "invoice_date", "vat", "bank"]:
        check(draft[field] == "", "No premature invoice fact: " + field)
    check(not draft.signed, "Draft has no authorised signature")
    var actions := ["ops_qty", "ops_report", "ops_full_documents", "trader_price",
        "contract_entity", "contract_verified_precision", "contract_fixing", "contract_terms",
        "lc_terms", "lc_docs", "lc_match", "vat_treatment", "fx_rate", "lc_original",
        "settlements_check", "settlements_release"]
    for action in actions:
        game._choose_dialogue(action)
    check(game.invoice_issued and not game.quest_failed, "Canonical source route wins")
    check(game.quest_minutes == 16, "Canonical choices cost exactly 16 minutes")
    var invoice: Dictionary = game.invoice_state()
    check(invoice.quantity == "8,470 MT", "Final quantity, never 8,500 estimate")
    check(invoice.unit_price == "USD 612.5000000000", "Ten decimal places")
    check(invoice.total == "" and invoice.invoice_date == "", "No invented numeric total/date")
    check(invoice.signed and invoice.status == "ISSUED", "Signed issued invoice")
    check(not game.known_payment_currency, "EUR cutoff is not settlement currency evidence")
    check(not game.known_escalation_clause and not game.known_fluctuation_clause, "No obsolete density escalation dependency")
    check(game._release_blockers().is_empty(), "Every actual release prerequisite satisfied")

func test_evidence_and_wrong_answers() -> void:
    var game = Session.new()
    game._choose_dialogue("ops_estimate")
    check(not game.known_final_quantity and game.quest_minutes == 1, "Wrong estimate costs time without verification")
    game._choose_dialogue("ops_qty")
    check(not game._dialogue_options("OPERATIONS").any(func(c): return c[1] == "ops_full_documents"), "Quantity alone does not advertise customs answer")
    game._choose_dialogue("vat_treatment")
    check(not game.known_vat_treatment and game.vat_requested_customs_status, "VAT rejects missing evidence")
    game._choose_dialogue("ops_full_documents")
    game._choose_dialogue("vat_treatment")
    check(game.known_vat_treatment, "Requested supporting papers allow VAT approval")
    game._choose_dialogue("lc_match")
    game._choose_dialogue("lc_original")
    check(not game.known_lc_amount_match and not game.known_signature and game.original_pack_prepared, "Pack preparation cannot bypass LC verification")
    game._choose_dialogue("fx_rate")
    check(not game.known_fx_rate, "FX rejects unconfirmed date/currency")
    var before: Dictionary = game._assistant_verified_fact_map()
    game._choose_dialogue("contract_guess_two")
    check(game._assistant_newly_verified(before).is_empty(), "Incorrect answer earns no praise/facts")
    game._choose_dialogue("contract_entity")
    game._choose_dialogue("contract_fixing")
    game._choose_dialogue("fx_rate")
    check(game.known_fx_rate and game.invoice_state().bank.contains("direction unconfirmed"), "FX verification retains unapproved quote direction")

func test_transitions_and_persistence() -> void:
    var game = Session.new()
    var entrance := Vector3(-20, 3, 8)
    var exits: Array = []
    game.office_left.connect(func(id, point): exits.append([id, point]))
    check(game.enter_landmark("operations", entrance), "Explicit Enter opens mapped office")
    check(game.quest_minutes == 0, "Reading opening is free")
    check(not game.enter_landmark("vat", Vector3.ZERO), "Cannot replace active office")
    check(not game.choose("ops_qty"), "Cannot invoke an option before greeting")
    check(game.choose("greet_polite") and game.choose("ops_qty"), "Displayed canonical choices work")
    var praise: String = game.assistant_recent_praise
    check(not praise.is_empty() and game.assistant_success_pending, "New evidence queues assistant feedback")
    game.leave_office()
    check(exits.size() == 1 and exits[0][0] == "operations" and exits[0][1] == entrance, "Leave returns exact 3D entrance")
    check(game.known_final_quantity and game.quest_minutes == 2, "Office transition preserves invoice/time")
    check(game.enter_landmark("operations", entrance), "Repeat visit opens office")
    check(game.dialogue_options.any(func(c): return c[1] == "ops_report"), "Repeat visit derives choices from shared facts")
    check(game.assistant_recent_praise == praise, "Assistant praise survives transition")
    game.leave_office()
    for id in Session.NON_STORY_LANDMARKS:
        check(not game.enter_landmark(id, Vector3.ZERO), "No invented office quest for " + id)
    check(Session.LANDMARK_DESTINATIONS.size() + Session.NON_STORY_LANDMARKS.size() == 15, "All 15 landmarks classified")

func test_lunch_and_transport() -> void:
    var game = Session.new()
    game.charge_travel(3, "tube")
    game.charge_travel(3, "tube")
    check(game.quest_minutes == 6 and game.boat_wait_minutes("west") == 4, "Source west boat departs on :00/:10")
    game.charge_travel(game.boat_wait_minutes("west") + 5, "boat")
    check(game.quest_minutes == 15 and game.boat_wait_minutes("east") == 0, "Wait + five-minute crossing; east :05/:15")
    game.quest_minutes = 40
    check(game.enter_landmark("contracts", Vector3.ZERO), "Can inspect closed office")
    check(game.dialogue_text.contains("13:00"), "Canonical lunch notice shown")
    check(game.choose("__wait_lunch__"), "Wait until return action available")
    check(game.quest_minutes == 60 and not game._office_is_closed("CONTRACTS"), "Lunch wait charges only remaining window")
    check(game.office_lunch_return_seen.get("CONTRACTS", false), "Lunch return persists")

func test_deadline_and_compliance() -> void:
    var game = Session.new()
    var before: Dictionary = game._assistant_verified_fact_map()
    game._choose_dialogue("compliance_chocolate")
    check(game.quest_minutes == 45 and game.compliance_warning_pending, "Bribe costs exactly 45 minutes")
    check(before == game._assistant_verified_fact_map(), "Bribe verifies no invoice data")
    game._choose_dialogue("compliance_training")
    check(game.quest_minutes == 45 and game.known_compliance_clearance, "Training completion not charged twice")
    check(not game._release_blockers().has("compliance"), "Compliance remains optional canonical detour")
    game.quest_minutes = 119
    game._choose_dialogue("settlements_release")
    check(game.quest_failed and not game.invoice_issued and game.quest_minutes == 120, "Choice at 13:59 fails at 14:00")
    game.charge_travel(20, "walk")
    check(game.quest_minutes == 120, "Failed session cannot continue accruing time")
    var fresh = Session.new()
    check(fresh.quest_minutes == 0 and not fresh.quest_failed and not fresh.known_final_quantity, "New session clears all progress for restart")
    check(Session.EUR_PAYMENT_CUTOFF_MINUTES == 870, "Separate EUR cutoff remains 14:30")
