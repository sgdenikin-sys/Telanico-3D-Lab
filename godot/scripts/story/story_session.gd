extends RefCounted
## Canonical story rules extracted from VorGun main.gd at fc5e861.
## No scene, renderer, input or viewport ownership. See docs/v2-2/MIGRATION.md.
signal changed
signal minutes_spent(amount: int, reason: String)
signal dialogue_changed(destination: String, text: String, choices: Array)
signal office_left(landmark: String, entrance: Vector3)
signal result_reached(won: bool)
signal invoice_requested
signal next_line_requested

const SOURCE_COMMIT := "fc5e861f0c899ae5925625ff2191a41d7043d957"
const QUEST_START_MINUTES := 12 * 60
const QUEST_DEADLINE_MINUTES := 14 * 60
const EUR_PAYMENT_CUTOFF_MINUTES := 14 * 60 + 30
const LANDMARK_DESTINATIONS := {
    "settlements": "SETTLEMENTS HALL", "operations": "OPERATIONS",
    "finance": "TRADE FINANCE", "lc": "LC DESK", "compliance": "COMPLIANCE",
    "trader": "TRADER", "contracts": "CONTRACTS", "vat": "VAT", "fx": "FX TOWER"
}
const NON_STORY_LANDMARKS := ["coffee", "archive", "tube_w", "tube_e", "dock_w", "dock_e"]
var quest_minutes := 0
var current_landmark := ""
var return_entrance := Vector3.ZERO
var dialogue_text := ""
var dialogue_options: Array = []
const PILOT_INVOICE_CURRENCY := "USD"
# Identified from the opening draft. Not a discoverable quest fact.
const PILOT_PRODUCT_NAME := "High Quality Energy (Physical Oil)"
const ASSISTANT_PRAISE := [
    "Nice one, Cooper!", "That's properly checked!", "Another blank defeated!",
    "Excellent detective work!", "Actual evidence. Beautiful!", "Look at you, doing Settlements!"
]
const PILOT_UNIT_PRICE := "612.50"
const PILOT_UNIT_PRICE_PRECISE := PILOT_UNIT_PRICE + "00000000"
const PILOT_QUANTITY := "8,470"
const PILOT_FX_REFERENCE_RATE := "1.0834"
var operations_visit_count := 0
var vat_requested_customs_status := false
var known_final_quantity := false
var known_customs_status := false
var known_currency := false
var known_price_currency := false
var known_payment_currency := false # EUR cut-off alone is not contractual settlement evidence.
var known_lc_bank := false
var known_payment_terms := false
var known_fx_rate := false
var assistant_auto_seen: Dictionary = {}
var assistant_recent_praise := ""
var assistant_success_pending := false
var verified_invoice_review_pending := false
var reward_sequence_id := 0
var reward_invoice_animation_pending := false
var reward_interaction_locked := false
var assistant_feedback_emotion := ""
var assistant_last_praise_index := -1
var office_warm_cache: Dictionary = {}
var office_warm_elapsed := 0.0
var active_dialogue_destination := ""
var office_visit_counts: Dictionary = {}
var office_relationships: Dictionary = {}
var known_unit_price := false
var known_vat_treatment := false
var known_legal_entity := false
var known_lc_requirements := false
var known_signature := false
var known_price_precision := false
var known_density := false
var known_discharge_location := false
var vat_requested_discharge_location := false
var known_lc_amount_match := false
var known_fluctuation_clause := false
var known_fx_rate_date := false
var known_compliance_clearance := false
var known_invoice_date := false
var invoice_issued := false
var choosing_price_decimals := false
var quest_failed := false
var deadline_worry_shown := false
var known_escalation_clause := false
var density_problem_revealed := false
var original_pack_prepared := false
var original_signature_required := false
var ops_full_pack_requested := false
var trader_good_intro := false
var trader_price_obtained := false
var trader_price_acknowledged := false
var trader_commission_used := false
var eagle_followup_unlocked := false
var compliance_training_offered := false
var compliance_warning_pending := false
var compliance_warning_shown := false
var office_lunch_return_seen: Dictionary = {}
var npc_lunch_windows := {
    "OPERATIONS": Vector2i(13*60,13*60+20),
    "CONTRACTS": Vector2i(12*60+40,13*60),
    "VAT": Vector2i(13*60+10,13*60+30),
    "FX TOWER": Vector2i(12*60+45,13*60+5),
    "TRADE FINANCE": Vector2i(13*60+15,13*60+35),
    "TRADER": Vector2i(13*60+5,13*60+25)
}


func _format_quest_time(total_minutes: int) -> String:
    return "%02d:%02d" % [total_minutes / 60, total_minutes % 60]

func _boat_wait_minutes(island: String, at_minutes: int = -1) -> int:
    # A leaves on :00/:10; B leaves on :05/:15. Never cache departures.
    var now: int = QUEST_START_MINUTES + quest_minutes if at_minutes < 0 else at_minutes
    var offset: int = 5 if island == "B" else 0
    return posmod(offset - now, 10)

func _assistant_context_stage() -> String:
    if invoice_issued or quest_failed:
        return ""
    if quest_minutes >= 90:
        return "clock"
    if known_lc_amount_match and not known_signature:
        return "original"
    if known_final_quantity and not known_lc_amount_match:
        return "verified_facts"
    if not known_final_quantity and not known_unit_price:
        return "draft"
    return ""

func _assistant_verified_fact_map() -> Dictionary:
    # Compare only evidence-backed progress, never dialogue attempts or guesses.
    return {
        "FINAL QUANTITY": known_final_quantity,
        "UNIT PRICE": known_unit_price,
        "PRICE PRECISION": known_price_precision,
        "SELLER": known_legal_entity,
        "INVOICE CURRENCY": known_currency,
        "DENSITY READING": known_density,
        "ESCALATION CLAUSE": known_escalation_clause,
        "DISCHARGE LOCATION": known_discharge_location,
        "CUSTOMS MOVEMENT": known_customs_status,
        "LC TERMS": known_payment_terms,
        "RECEIVING BANK": known_lc_bank,
        "LC DOCUMENTS": known_lc_requirements,
        "LC AMOUNT MATCH": known_lc_amount_match,
        "FLUCTUATION CLAUSE": known_fluctuation_clause,
        "FIXING DATE": known_fx_rate_date,
        "FX REFERENCE": known_fx_rate,
        "VAT TREATMENT": known_vat_treatment,
        "SIGNED ORIGINAL": known_signature,
        "COMPLIANCE TRAINING": known_compliance_clearance
    }

func _assistant_newly_verified(before: Dictionary) -> PackedStringArray:
    var gained := PackedStringArray()
    for field in _assistant_verified_fact_map():
        if bool(_assistant_verified_fact_map()[field]) and not bool(before.get(field, false)):
            gained.append(String(field))
    return gained

func _assistant_hint() -> String:
    # Suggested next checks, never unearned answers, tax conclusions or a route.
    if quest_minutes >= 90 and not invoice_issued:
        return "Clock check: send before 14:00; 14:30 is only the EUR cut-off."
    if not known_final_quantity:
        return "A delivery estimate is not a final billable quantity."
    if not known_unit_price:
        return "The trade quote needs a verified unit price."
    
    if not known_price_precision:
        return "Read the signed price-precision clause before rounding."
    if not known_unit_price:
        return "Ask the Trader for the fixed price: it has not reached Contracts."
    if (vat_requested_discharge_location or vat_requested_customs_status) and (not known_discharge_location or not known_customs_status):
        return "VAT asked for discharge and customs evidence. A guess won't pass."
    if not known_payment_terms or not known_lc_requirements:
        return "Payment terms and the bank's document list are different checks."
    if not known_lc_amount_match:
        return "The LC amount needs exact reconciliation, not an approximation."
    if not known_fx_rate_date or not known_fx_rate:
        return "A rate without its contractual fixing date is just a number."
    if not known_vat_treatment:
        return "VAT needs supporting evidence before treatment can be confirmed."
    if not known_signature:
        return "Check whether the authorised original is signed and stamped."
    return "Check the remaining release conditions before pressing SEND."

func _assistant_open_fields_short(limit: int = 3) -> String:
    var missing := _release_blockers()
    if missing.is_empty():
        return "none required"
    var shown := PackedStringArray()
    for i in range(mini(limit, missing.size())):
        shown.append(missing[i])
    var remaining := missing.size() - shown.size()
    return ", ".join(shown) + (" (+%d more)" % remaining if remaining > 0 else "")

func _assistant_success_line(gained: PackedStringArray) -> String:
    if gained.is_empty():
        return ""
    # Avoid the immediately previous phrase while keeping selection random.
    var index := randi_range(0, ASSISTANT_PRAISE.size() - 2)
    if index >= assistant_last_praise_index and assistant_last_praise_index >= 0:
        index += 1
    assistant_last_praise_index = index
    var praise: String = "Nice! First field populated, well done! Hurry with the rest of the invoice!" if _assistant_verified_fact_map().values().count(true) == 1 else ASSISTANT_PRAISE[index]
    # The updated invoice shows the fact itself; the rabbit should not read a checklist aloud.
    assistant_recent_praise = praise
    assistant_success_pending = true
    assistant_feedback_emotion = "approval" if ("LC AMOUNT MATCH" in gained or "VAT TREATMENT" in gained or "SIGNED ORIGINAL" in gained) else ("documents" if ("FINAL QUANTITY" in gained or "UNIT PRICE" in gained or "PRICE PRECISION" in gained) else "greeting")
    return "Assistant: " + assistant_recent_praise + " Plenty more information to gather. Keep going!"

func _assistant_status_lines() -> PackedStringArray:
    # Factual status rather than newly authored character dialogue. Never expose
    # unknown escalation or VAT document requirements before discovery.
    var verified := PackedStringArray()
    if known_unit_price:
        verified.append("UNIT PRICE")
    if known_final_quantity:
        verified.append("DELIVERED QUANTITY")
    if known_density:
        verified.append("DENSITY READING")
    if known_currency:
        verified.append("INVOICE CURRENCY")
    if known_lc_bank:
        verified.append("RECEIVING BANK")
    if known_lc_requirements:
        verified.append("LC DOCUMENTS")
    if known_vat_treatment:
        verified.append("VAT")
    var open := PackedStringArray()
    if not known_unit_price:
        open.append("UNIT PRICE")
    if not known_final_quantity:
        open.append("ACTUAL QUANTITY")


    if (vat_requested_discharge_location or vat_requested_customs_status) and (not known_discharge_location or not known_customs_status):
        open.append("DISCHARGE / CUSTOMS PAPERS")
    if known_payment_terms and not known_lc_requirements:
        open.append("LC DOCUMENT REQUIREMENTS")
    if known_lc_requirements and not known_lc_amount_match:
        open.append("LC AMOUNT CHECK")
    if known_fx_rate_date and not known_fx_rate:
        open.append("FX REFERENCE CHECK")
    if known_lc_amount_match and known_vat_treatment and not known_signature:
        open.append("SIGNED ORIGINAL")
    return PackedStringArray([
        "VERIFIED: PRODUCT (" + PILOT_PRODUCT_NAME + ")" + (", " + ", ".join(verified) if not verified.is_empty() else ""),
        "OPEN: " + (", ".join(open) if not open.is_empty() else "REVIEW THE DRAFT"),
        "REQUIRED STILL OPEN: " + _assistant_open_fields_short(99),
        "PILOT DISPLAY BLANKS: invoice number, invoice date, adjusted numerical total."
    ])

func _office_schedule(destination_name: String) -> String:
    if not npc_lunch_windows.has(destination_name):
        return ""
    var window: Vector2i = npc_lunch_windows[destination_name]
    if destination_name == "CONTRACTS":
        return "OUT FOR LUNCH — BACK AT 13:00"
    if destination_name == "FX TOWER":
        return "GENEVA LUNCH — BACK AT 13:05"
    return "LUNCH %s–%s" % [_format_quest_time(window.x), _format_quest_time(window.y)]

func _office_is_closed(destination_name: String) -> bool:
    if not npc_lunch_windows.has(destination_name):
        return false
    var window: Vector2i = npc_lunch_windows[destination_name]
    var now: int = QUEST_START_MINUTES + quest_minutes
    return now >= window.x and now < window.y

func _show_closed_office(destination_name: String) -> void:
    var lines := {
        "CONTRACTS": "Cooper: A signed contract can wait. Apparently, so can I.",
        "OPERATIONS": "Cooper: The cargo's delivered. The paperwork has apparently gone to lunch.",
        "TRADER": "Cooper: Even money takes a lunch break.",
        "VAT": "Cooper: Please tell me tax treatment doesn't depend on lunchtime.",
        "TRADE FINANCE": "Cooper: Payment instructions. Closed for lunch. Excellent combination.",
        "FX TOWER": "Cooper: It's noon!\nFiona: Exactly."
    }
    _show_dialogue(destination_name,
        "NOTICE: %s\n%s" % [_office_schedule(destination_name), String(lines.get(destination_name, ""))],
        [["WAIT UNTIL RETURN", "__wait_lunch__"], ["LEAVE", "__leave_no_cost__"]])

func _wait_for_office_return() -> void:
    var destination_name := active_dialogue_destination
    if not _office_is_closed(destination_name):
        return
    var window: Vector2i = npc_lunch_windows[destination_name]
    _spend_minutes(window.y - (QUEST_START_MINUTES + quest_minutes), "LUNCH WAIT")
    if quest_failed:
        return
    office_visit_counts[destination_name] = int(office_visit_counts.get(destination_name, 0)) + 1
    var line := {
        "CONTRACTS": "Benny: Back from lunch. Which clause has ruined your afternoon?",
        "OPERATIONS": "Wolf: All right. What's missing this time?",
        "TRADER": "Eagle: You've waited twenty minutes. This had better involve money.",
        "VAT": "Nora: Right. Let's see whether your documents have improved.",
        "TRADE FINANCE": "Finance Specialist: Back again? Let's look at those payment instructions.",
        "FX TOWER": "Fiona: Back from lunch. Please tell me you brought the fixing date."
    }
    office_lunch_return_seen[destination_name] = true
    _show_dialogue(destination_name, String(line.get(destination_name, "")), _dialogue_options(destination_name))

func _office_greeting_options(destination_name: String) -> Array:
    var choices := {
        "TRADER": [
            ["Nice to finally meet you! I'm Cooper from Settlements. Could I borrow a minute?", "greet_polite"],
            ["Our High Quality Energy (Physical Oil) delivery is complete. We could get paid today.", "greet_commercial"],
            ["I need some information for an invoice. Won't take long.", "greet_demanding"]
        ],
        "CONTRACTS": [
            ["Good afternoon, Benny. Could you help me check our first delivery terms?", "greet_polite"],
            ["I just need the contract details.", "greet_neutral"],
            ["The Trader gave me the price. That's enough, isn't it?", "greet_demanding"]
        ],
        "OPERATIONS": [
            ["Good afternoon, Wolf. Cargo's delivered, and I'm trying to get us paid.", "greet_polite"],
            ["I need the final quantity." if not known_final_quantity else ("Could I check the full final delivery report?" if not known_density else "Could I check the complete discharge and customs movement papers?"), "greet_neutral"],
            ["The invoice doesn't work. What went wrong in Operations?", "greet_demanding"]
        ],
        "VAT": [
            ["Good afternoon, Nora. Could you help me verify the VAT treatment?", "greet_polite"],
            ["Can you approve the invoice quickly?", "greet_neutral"],
            ["It's somewhere in Europe. Can we use zero VAT?", "greet_demanding"]
        ],
        "FX TOWER": [
            ["We have a %s invoice and a EUR payment deadline. Can you reconcile the currencies?" % PILOT_INVOICE_CURRENCY, "greet_polite"],
            ["Could I have the exchange rate, please?", "greet_neutral"],
            ["Let's just use today's rate.", "greet_demanding"]
        ],
        "LC DESK": [
            ["Hello! Cooper from Settlements. Let's check the payment documents.", "greet_polite"],
            ["Which bank is paying us?", "greet_neutral"],
            ["Can you release the money without checking the LC?", "greet_demanding"]
        ],
        "TRADE FINANCE": [
            ["I'm Cooper. Our first invoice needs its payment instructions verified.", "greet_polite"],
            ["I need the bank details.", "greet_neutral"],
            ["Can you make the customer pay immediately?", "greet_demanding"]
        ],
        "COMPLIANCE": [
            ["I want to make sure our documentation meets company requirements.", "greet_polite"],
            ["I brought chocolate. Could we speed things up?", "greet_demanding"],
            ["It's excellent chocolate.", "greet_chocolate"]
        ]
    }
    var result: Array = choices.get(destination_name, [])
    result = result.duplicate(true)
    result.append(["Sorry, I'll come back later.", "greet_leave"])
    return result

func _office_greeting(destination_name: String, returning: bool) -> String:
    if destination_name == "TRADER" and known_unit_price and not trader_price_obtained and not trader_price_acknowledged:
        return "Eagle: Cooper! Back for another price?\nCooper: No, I've got the price. I'm checking the rest of the deal.\nEagle: Then make it quick. I still have trades to close."
    if returning:
        if destination_name == "OPERATIONS" and not known_unit_price:
            return "Wolf: Pricing is fixed. Eagle has the confirmation, not me."
        return {
            "OPERATIONS": "Wolf: Back already? Someone asked you a question you didn't ask me?",
            "CONTRACTS": "Benny: Back again? Let me guess. The numbers aren't behaving?",
            "TRADER": "Eagle: Back again? This had better be about getting paid."
        }.get(destination_name, "Back again, Cooper? What did we miss?")
    return {
        "TRADER": "Eagle: If you're not bringing me a profitable deal or a serious problem, you've picked a terrible time. I'm closing a trade.",
        "CONTRACTS": "Benny: Before you ask, yes, I've read the contract. Unlike some people.",
        "OPERATIONS": "Wolf: Unless you've brought the cargo back, I'd say our job is done.",
        "VAT": "Nora: Please tell me you brought the documents. I haven't had enough coffee for another geographical guessing game.",
        "FX TOWER": "Fiona: Please tell me you know which exchange rate you need. And don't say 'today's'.",
        "TRADE FINANCE": "Finance Specialist: Another payment question? Let me guess. You want it today.",
        "LC DESK": "Riley: Good afternoon. If you're here about a letter of credit, I hope you brought more than optimism.",
        "COMPLIANCE": "Compliance Officer: Compliance Annex. Please state the purpose of your visit.",
        "SETTLEMENTS HALL": "Invoice Team: Back already? You look like you've met everyone in the company."
    }.get(destination_name, "Good afternoon, Cooper.")

func _greeting_reply(destination_name: String, action: String) -> String:
    var polite: bool = action in ["greet_polite", "greet_commercial"]
    if action == "greet_chocolate":
        return "Compliance Officer: Mandatory compliance training. Immediately. Chocolate cannot clear this review."
    match destination_name:
        "TRADER":
            if action == "greet_commercial":
                return "Eagle: Getting paid today? Now you've got my attention. What's holding up the cash?"
            return "Eagle: Settlements, huh? Make it quick." if polite else "Eagle: That's what Contracts is for. Fine. One question."
        "CONTRACTS":
            return "Benny: Finally. Someone asking before sending an invoice." if polite else "Benny: It's a contract, not a fortune cookie. Be specific."
        "OPERATIONS":
            return "Wolf: Getting paid? Now that's a useful reason to visit." if polite else "Wolf: Interesting way to ask for help."
        "VAT":
            return "Nora: Of course. Let's start with the facts." if polite else "Nora: Europe is a continent, Cooper. Not a VAT treatment."
        "FX TOWER":
            return "Fiona: Good. You've identified the problem." if polite else "Fiona: Which date? Contracts frowns upon creative exchange rates."
        "TRADE FINANCE":
            return "Finance Specialist: Good. At least someone is thinking about the cash." if polite else "Finance Specialist: Straight to business, then."
        "LC DESK":
            return "Riley: Excellent. It's easier to fix documents before the bank rejects them." if polite else "Riley: The bank is only half the story. Check the LC first."
        "COMPLIANCE":
            return "Compliance Officer: Very sensible. What exactly would you like reviewed?" if polite else "Compliance Officer: Did you just offer a gift in exchange for approval?"
    return "Let's get to the question."

func _dialogue_options(destination_name: String) -> Array:
    # Every call derives HIDE / REPLACE / KEEP from live facts. Never cache
    # outdated options after a successful answer or on another NPC's visit.
    match destination_name:
        "OPERATIONS":
            var ops: Array = []
            if not known_final_quantity:
                ops.append(["Can you confirm the final delivered quantity?", "ops_qty"])
                ops.append(["Is the estimated quantity close enough?", "ops_estimate"])
            if known_final_quantity and not ops_full_pack_requested:
                ops.append(["Could I check the full final delivery report?", "ops_report"])
            if (ops_full_pack_requested or vat_requested_discharge_location or vat_requested_customs_status) and (not known_discharge_location or not known_customs_status):
                if known_discharge_location:
                    ops.append(["I've got Rotterdam. Can we verify the customs movement status?", "ops_full_documents"])
                elif known_customs_status:
                    ops.append(["I have the customs status. Can you confirm the exact discharge port?", "ops_full_documents"])
                else:
                    ops.append(["Could I check the complete discharge and customs movement papers?", "ops_full_documents"])
            ops.append(["Thanks. That's all I need.", "ops_exit"])
            return ops
        "CONTRACTS":
            var contracts: Array = []
            if not known_unit_price:
                contracts.append(["Has the Trader sent over the fixed price?", "contract_price"])
            if not known_legal_entity or not known_currency:
                contracts.append(["Please tell me whose name goes on the invoice.", "contract_entity"])

            if not known_fx_rate_date:
                contracts.append(["Which fixing date applies to the payment conversion?", "contract_fixing"])
            if not known_price_precision:
                contracts.append(["Can we round the unit price?", "contract_verified_precision"])
            if not known_payment_terms:
                contracts.append(["What documentary payment terms did we agree?", "contract_terms"])
            contracts.append(["I should probably stop asking questions.", "contracts_exit"])
            return contracts
        "TRADER":
            if not known_unit_price:
                return [["What price did we agree for the cargo?", "trader_price"], ["Thanks. I'll take it from here.", "trader_exit"]]
            if not trader_good_intro and trader_price_obtained:
                return [["Thanks. I'll take it from here.", "trader_exit"]]
            var trader: Array = []
            if not known_final_quantity:
                trader.append(["Who confirms what actually arrived?", "trader_ops_owner"])
            elif not known_discharge_location or not known_customs_status:
                trader.append(["Is there anything beyond the delivered quantity I should worry about?", "trader_ops_context"])

            if trader_good_intro and not trader_commission_used:
                trader.append(["How about a commission for getting us paid?", "trader_commission"])
            trader.append(["Thanks. I'll take it from here.", "trader_exit"])
            return trader
        "LC DESK":
            var lc: Array = []
            if not known_payment_terms or not known_lc_bank:
                lc.append(["Can you confirm the letter of credit and receiving bank?", "lc_terms"])
            if not known_lc_requirements:
                lc.append(["What does the LC require?", "lc_docs"])
            if not known_lc_amount_match:
                lc.append(["What must match in the invoice amount?", "lc_match"])
            if not original_signature_required and not known_signature:
                lc.append(["Do we need an original signature and stamp?", "lc_signature_notice"])
            if not known_signature:
                lc.append(["Can we prepare the original now?", "lc_original"])
            lc.append(["That's enough. Thank you.", "lc_exit"])
            return lc
        "TRADE FINANCE":
            var tf: Array = []
            if not known_lc_bank:
                tf.append(["Can you confirm the receiving bank?", "tf_bank"])
            if not known_lc_requirements:
                tf.append(["Can you confirm the full LC documentation?", "tf_documents"])
            if not known_lc_amount_match:
                tf.append(["Can we reconcile fixed pricing with the LC?", "tf_adjustment"])
            if not known_fx_rate:
                tf.append(["What about the payment currency?", "tf_fx"])
            tf.append(["Thanks. That's all.", "tf_exit"])
            return tf
        "VAT":
            var vat: Array = []
            if not known_vat_treatment:
                vat.append(["Can we confirm the VAT treatment?", "vat_treatment"])
                if vat_requested_customs_status or vat_requested_discharge_location:
                    vat.append_array([
                        ["Could I use 'somewhere in Europe'?", "vat_location"],
                        ["I'll get the discharge and movement papers.", "vat_exit"],
                        ["Can we proceed without the customs status?", "vat_customs_wrong"]
                    ])
            vat.append(["That's all, thank you.", "vat_exit"])
            return vat
        "FX TOWER":
            var fx: Array = []
            if not known_fx_rate:
                fx.append(["Can we verify the contractual fixing date and rate?", "fx_rate"])
                fx.append(["Can't we make an exception?", "fx_exception"])
                fx.append(["What exactly needs matching?", "fx_matching"])
            if not known_fx_rate_date:
                fx.append(["I'll check the signed terms with Benny.", "fx_exit"])
            else:
                fx.append(["That's all, thank you.", "fx_exit"])
            return fx
        "COMPLIANCE":
            var compliance: Array = [["I brought chocolate. Could it help with approval?", "compliance_chocolate"]]
            if compliance_training_offered and not known_compliance_clearance:
                compliance.append(["Complete mandatory training.", "compliance_training"])
            compliance.append(["I'll come back another time.", "compliance_exit"])
            return compliance
        _:
            return [
                ["The invoice looks good. Can we sign and stamp it?", "settlements_check"],
                ["Check it and SEND THE INVOICE.", "settlements_release"] if not invoice_issued else ["I'll return when the documents are ready.", "settlements_exit"],
                ["I'll return when the documents are ready.", "settlements_exit"]
            ]

# Only the opening line below is directly verified from Anna's screenshots.
# The alternative replies are authored pilot choices, not claimed as her exact words.

func _ops_density_answer_options() -> Array:
    return [
        ["Does density change the fixed price?", "ops_density_guess_factor"],
        ["Who can confirm our fixed unit price?", "ops_density_confirm_terms"],
        ["Can I use estimated quantity for this invoice?", "ops_density_guess_estimate"],
        ["Can I check the delivery documentation?", "ops_density_check_report"]
    ]

func _release_blockers() -> PackedStringArray:
    var missing := PackedStringArray()
    if not known_legal_entity: missing.append("invoicing entity")
    if not known_final_quantity: missing.append("final quantity")
    if not known_discharge_location: missing.append("discharge location")
    if not known_unit_price: missing.append("Trader-confirmed fixed unit price")
    if not known_price_precision: missing.append("price decimals")
    if not known_currency: missing.append("currency")
    if not known_fx_rate: missing.append("FX rate/date")
    if not known_payment_terms: missing.append("payment terms")
    if not known_customs_status: missing.append("customs status")
    if not known_lc_requirements: missing.append("LC documents")
    if not known_lc_amount_match: missing.append("LC amount match")
    if not known_vat_treatment: missing.append("VAT treatment")
    # Compliance is an optional detour, never a mandatory invoice field.
    # The old invoice-date joke is not an approval requirement.
    if not known_signature: missing.append("signed/stamped original")
    return missing

func _choose_dialogue(action: String) -> void:
    if action == "__review_verified_invoice__":
        verified_invoice_review_pending = true
        invoice_requested.emit()
        return
    if action == "__next_line__":
        next_line_requested.emit()
        return
    if reward_interaction_locked:
        return
    if quest_failed:
        return
    if action == "__leave_no_cost__":
        _close_interaction()
        return
    if action == "__wait_lunch__":
        _wait_for_office_return()
        return
    # Only meaningful Cooper answers spend one game minute.
    if action in ["greet_leave", "lc_exit", "settlements_exit", "ops_exit", "trader_exit", "contracts_exit", "fx_exit", "vat_exit", "tf_exit", "compliance_exit"]:
        _close_interaction()
        return
    if action == "compliance_chocolate":
        # One irreversible ethical error: the entire mandatory training costs
        # exactly 45 game minutes, never 1 + 45 or 10 more later.
        _spend_minutes(45, "MANDATORY COMPLIANCE TRAINING")
    elif action != "compliance_training":
        _spend_dialogue_minute()
    if quest_failed:
        return
    if action.begins_with("greet_"):
        office_relationships[active_dialogue_destination] = action
        if active_dialogue_destination == "TRADER":
            trader_good_intro = action == "greet_commercial"
        _show_dialogue(active_dialogue_destination, _greeting_reply(active_dialogue_destination, action), _dialogue_options(active_dialogue_destination))
        return
    var verified_before := _assistant_verified_fact_map()
    var reply := ""
    var followup_choices: Array = []
    match action:
        "tf_bank":
            known_lc_bank = true
            reply = "Finance Specialist: TreeBank is the receiving bank. Anything else about the payment instructions?"
        "tf_payment":
            known_payment_terms = true
            reply = "Finance Specialist: Payment is LC-backed. Please confirm full documentary requirements with Riley at the LC Desk."
        "tf_adjustment":
            reply = "Finance Specialist: The Trader fixed the unit price. Verify quantity, precision and LC amount with Riley; the FX conversion is a separate check."
        "tf_documents":
            reply = "Finance Specialist: For documentary requirements, you need Riley at the LC Desk."
        "tf_fx":
            reply = "Finance Specialist: Your trade price is in dollars. Your payment deadline refers to euros. Fiona needs to confirm the contractual conversion."
        "lc_terms":
            known_payment_terms = true
            known_lc_bank = true
            reply = "Riley: TreeBank letter of credit. The bank won't pay because your invoice looks convincing. It has to match the LC."
        "lc_docs":
            known_lc_requirements = true
            reply = "Riley: Original bill of lading, certificates, transport documents, and a signed and stamped invoice."
        "lc_match":
            if known_final_quantity and known_unit_price and trader_price_obtained and known_price_precision and known_lc_requirements and known_payment_terms and known_currency and known_price_currency and known_lc_bank:
                known_lc_amount_match = true
                reply = "Riley: Fixed price confirmed by Trader, delivered quantity and price precision verified. The LC reconciles. Density does not affect pricing."
            else:
                reply = "Riley: We still need Trader-fixed price, final quantity, agreed decimals and documentary terms. There is no density escalation."
        "lc_signature_notice":
            original_signature_required = true
            reply = "Riley: Yes. And I would strongly recommend arranging both before your last five minutes."
        "lc_original":
            if known_lc_requirements and known_lc_amount_match and known_vat_treatment:
                original_pack_prepared = true
                known_signature = true
                reply = "Riley: Everything matches. I'll have the authorised original signed and stamped."
            else:
                original_pack_prepared = true
                reply = "Riley: We can prepare the document pack. The authorised signatory signs the verified original, not a guess."
        "lc_exit":
            _close_interaction()
            return
        "ops_qty":
            known_final_quantity = true
            reply = "Cooper: Can you confirm the final delivered quantity for High Quality Energy (Physical Oil)?\nWolf: Eight thousand four hundred and seventy metric tons. Not the estimate.\nWolf: Anything else? I've got another delivery waiting."
        "ops_report":
            if known_final_quantity:
                ops_full_pack_requested = true
                known_density = true
                reply = "Wolf: Final report verified. Density is cargo documentation only; it does not change the fixed price agreed by Trader."
        "ops_full_documents":
            if known_final_quantity and (ops_full_pack_requested or vat_requested_customs_status or vat_requested_discharge_location):
                if known_discharge_location and not known_customs_status:
                    known_customs_status = true
                    reply = "Cooper: I've got Rotterdam. Can we verify the customs movement status?\nWolf: T1. Here it is in the movement papers."
                elif known_customs_status and not known_discharge_location:
                    known_discharge_location = true
                    reply = "Wolf: Rotterdam, Netherlands. That's the discharge port and country."
                else:
                    known_discharge_location = true
                    known_customs_status = true
                    reply = "Cooper: Could I check the complete discharge and customs movement papers?\nWolf: Rotterdam, Netherlands. Customs movement status T1. Both are in the supporting documents."
            else:
                reply = "Wolf: Let's confirm the final delivered quantity first."
        "ops_estimate":
            reply = "Cooper: Is the estimated quantity close enough?\nWolf: Close enough for a guess. Not for an invoice."
        "ops_density_context":
            reply = "Wolf: Density does not affect this fixed-price deal. Ask Eagle for the agreed rate."
        "ops_density":
            reply = "Wolf: No density escalation on this deal. The Trader fixed the price."
            followup_choices = _ops_density_answer_options()
        "ops_density_guess_factor":
            reply = "Wolf: Density does not change this fixed price. Ask Eagle for his confirmation."
            followup_choices = _ops_density_answer_options()
        "ops_density_guess_estimate":
            reply = "Wolf: We delivered 8,470 MT. Estimated quantity is not invoice evidence."
            followup_choices = _ops_density_answer_options()
        "ops_density_confirm_terms":
            known_density = true
            reply = "Wolf: Eagle owns the fixed price. My team verifies the physical quantity and delivery evidence."
        "ops_density_check_report":
            known_density = true
            reply = "Wolf: Here is the delivery report. Density is for cargo records; no price adjustment is involved."
        "ops_location":
            if vat_requested_discharge_location:
                known_discharge_location = true
                reply = "Wolf: Rotterdam, Netherlands. That's the discharge port and country.\nCooper: I nearly wrote 'Europe'.\nWolf: Please don't."
            else:
                reply = "Wolf: Find out exactly what VAT needs before I start searching the archives."
        "ops_customs":
            if vat_requested_customs_status:
                known_customs_status = true
                reply = "Wolf: T1 movement status. It's in the customs pack.\nCooper: You had this the whole time?\nWolf: You didn't ask the whole question."
            else:
                reply = "Wolf: Customs what? A code? Status? Movement evidence?\nCooper: I was hoping 'customs stuff' would be enough.\nWolf: Try VAT first."
        "ops_docs":
            reply = "Wolf: The delivery report and customs movement document are different things. Don't make me explain this twice."
        "contract_entity":
            known_legal_entity = true
            known_currency = true
            known_price_currency = true
            reply = "Benny: VorGun Trading is the invoicing entity. The trade price is in %s. Now, Cooper. Did you come for the answer, or did you come to understand the contract?" % PILOT_INVOICE_CURRENCY
        "contract_escalation":
            reply = "Benny: No escalation. Eagle fixed the price but has not sent the confirmation to Contracts. Ask the Trader."
        "contract_fixing":
            known_fx_rate_date = true
            reply = "Benny: Previous business day. It's written in the signed terms, not in the stars."
        "contract_verified_precision":
            known_price_precision = true
            choosing_price_decimals = false
            reply = "Benny: Ten decimal places in the signed amendment. Not ten if you feel like it. Ten because we agreed."
        "contract_terms":
            known_payment_terms = true
            reply = "Benny: Letter of credit. If you're looking for the bank's documentary requirements, Riley has them."
        "contract_price":
            reply = "Benny: Eagle fixed the price, but has not provided his confirmation to Contracts. Get it from Trader. I can verify decimals and FX fixing."
        "contract_precision":
            if known_unit_price:
                choosing_price_decimals = true
            reply = "Benny: Price decimals? Tell me what the contract says.\nCooper: Two? Eight?\nBenny: Reading is also an option."
        "contract_guess_two":
            reply = "Benny: Wrong. Your bank account has more digits than that. Try reading the signed amendment.\n⚠ WRONG PRICE PRECISION — 1 MIN LOST."
        "contract_guess_eight":
            reply = "Benny: Still wrong. This is an excellent way to meet the customer rejection team.\n⚠ WRONG PRICE PRECISION — 1 MIN LOST."
        "contract_guess_ten", "contract_read_clause":
            known_price_precision = true
            choosing_price_decimals = false
            reply = "Benny: TEN decimal places on the contractual unit-price calculation. Yes, ten.\nCooper: Why does one invoice need more decimals than my bank account?\nBenny: Because the contract said so.\n✓ CONTRACT PRECISION VERIFIED."
        "vat_treatment":
            if known_discharge_location and known_customs_status:
                known_vat_treatment = true
                reply = "Nora: I need the exact discharge location and customs movement status.\nCooper: Rotterdam, Netherlands. T1. I've brought the documents.\nNora: Excellent. Actual evidence. How unusual."
            else:
                vat_requested_customs_status = true
                vat_requested_discharge_location = true
                reply = "Nora: I need the exact discharge location and customs movement status.\nCooper: The cargo was delivered. Isn't that enough?\nNora: For Operations, perhaps. For VAT, no."
        "vat_customs":
            vat_requested_customs_status = true
            reply = "Nora: Not 'customs stuff'. I need the exact movement status. Ask Operations.\nCooper: This island should really have a frequent-flyer programme."
        "vat_location":
            reply = "Nora: You could. If you're trying to make this worse."
        "vat_customs_wrong":
            reply = "Nora: No. A port tells me where. The status tells me how."
        "vat_deadline":
            reply = "Nora: My lunch window is on the board. Tax treatment can't be determined by enthusiasm alone."
        "fx_date":
            reply = "Fiona: Invoice currency, settlement currency, fixing date, reference rate. Four different things, Cooper."
        "fx_rate":
            if known_currency and known_fx_rate_date:
                known_fx_rate = true
                reply = "Fiona: You have a %s invoice and a EUR payment deadline. Which contractual fixing date applies?\nCooper: Previous business day, as stated in the signed contract.\nFiona: Perfect. Now we can use the correct reference rate: %s." % [PILOT_INVOICE_CURRENCY, PILOT_FX_REFERENCE_RATE]
            else:
                reply = "Fiona: You have a %s invoice and a EUR payment deadline. Which contractual fixing date applies?\nCooper: Today's rate?\nFiona: Today's rate is very interesting. Unfortunately, your contract doesn't care." % PILOT_INVOICE_CURRENCY
        "fx_exception":
            reply = "Fiona: You can ask. The contract can still say no."
        "fx_matching":
            reply = "Fiona: Invoice currency, settlement currency, fixing date, reference rate. Four different things, Cooper."
        "fx_signature":
            reply = "Fiona: FX confirms the contractual fixing, not signatures. The LC Desk can explain original-document requirements; an authorised signatory must sign and stamp the original."
        "fx_currency":
            reply = "Fiona: Contracts owns invoice currency. I own the reference rate — a much smaller headache."
        "fx_lunch":
            reply = "Fiona: Geneva is at lunch.\nCooper: It's noon!\nFiona: Exactly."
        "trader_price":
            if not known_unit_price:
                known_unit_price = true
                known_price_currency = true
                trader_price_obtained = true
            reply = "Cooper: What fixed price did you agree?\nEagle: %s %s per MT. I have not passed the confirmation to Benny yet. Density cannot change this price." % [PILOT_INVOICE_CURRENCY, PILOT_UNIT_PRICE]
            if not trader_good_intro:
                followup_choices = [["Thanks. I'll take it from here.", "trader_exit"]]
        "trader_ops_owner":
            reply = "Cooper: Who confirms what actually arrived?\nEagle: Wolf. Operations. Final delivery report. Don't confuse the estimate with reality."
        "trader_ops_context":
            reply = "Cooper: Is there anything beyond the delivered quantity I should worry about?\nEagle: Quantity tells you what arrived. It doesn't tell you everything in the delivery report."
        "trader_contract_clause":
            reply = "Eagle: The price is fixed. Benny verifies contractual decimals, LC terms and fixing date; not my price."
        "trader_commission":
            trader_commission_used = true
            reply = "Eagle: Get the invoice right first. Then we'll discuss your future."
        "trader_contract":
            reply = "Eagle: The signed recap is with Benny. And don't guess the decimal places — he's waiting for someone to do that."
        "trader_chat":
            reply = "Eagle: Are we celebrating or pretending this is normal?\nCooper: At 12:00, celebrating. At 13:59, probably hiding under a desk."
        "compliance_chocolate":
            compliance_training_offered = true
            compliance_warning_pending = true
            reply = "Compliance Officer: Cooper, offering chocolate for approval is a bribe. You have just been assigned mandatory compliance training — forty-five minutes.\nCooper: Forty-five?!\nCompliance Officer: Yes. And the invoice is still unfinished."
        "compliance_training":
            if compliance_training_offered:
                known_compliance_clearance = true
                reply = "Compliance Officer: Mandatory training completed. Certificate issued."
            else:
                reply = "Compliance Officer: No training was requested."
        "compliance_warning":
            reply = "Compliance (intercom): Good judgement beats shortcuts. If someone offers chocolate to clear a warning, decline it.\nCooper: Hypothetically speaking, of course."
        "finance_lc":
            if known_payment_terms:
                known_lc_bank = true
                known_lc_requirements = true
                reply = "Riley (LC desk): TreeBank LC. Signed invoice, transport evidence, original B/L and certificates.\nCooper: All of them?\nRiley: An approximate B/L is not a thing."
            else:
                reply = "Riley: Are we cash-against-documents or under LC?\nCooper: ...Yes?\nRiley: Find the payment clause in Contracts first."
        "finance_lc_amount":
            if known_final_quantity and known_unit_price and trader_price_obtained and known_price_precision and known_lc_requirements and known_discharge_location:
                known_lc_amount_match = true
                reply = "Riley (LC desk): Quantity checked, ten-digit calculation verified, and the LC amount reconciles.\nCooper: Approximately?\nRiley: Exactly. That's the word we like."
            else:
                reply = "Riley (LC desk): Does the invoice amount match the LC?\nCooper: Of course. Approximately?\nRiley: No. Fix quantity, price precision and LC wording. Then we'll talk."
        "finance_fluctuation":
            if known_lc_amount_match:
                reply = "Riley: There is no fluctuation adjustment on the fixed price. FX conversion is still separate."
            else:
                reply = "Riley: Reconcile the fixed-price amount against the LC first. Then verify FX conversion separately."
        "finance_terms":
            reply = "Riley: If you haven't checked the signed payment terms, I won't invent a banking instruction for you."
        "finance_chat":
            reply = "Riley: Want one thing you don't want to discover at 13:59? A missing LC clause.\nCooper: Noted. Unfortunately."
        "settlements_start":
            reply = "Assistant: Check the draft, not your confidence. A verified quantity is useful; an approximate LC amount isn't."
        "settlements_deadline":
            reply = "Assistant: EUR cut-off 14:30. Invoice must be sent by 14:00. Each choice costs one minute, even when someone says 'no'."
        "settlements_check":
            var draft_missing := _release_blockers()
            draft_missing.erase("signed/stamped original")
            if not draft_missing.is_empty():
                reply = "Invoice Team: Cooper, go finish the invoice first. We cannot sign or stamp an incomplete draft."
            elif not known_signature:
                reply = "Invoice Team: The invoice checks out. Now it needs the authorised signature and stamp. Arrange the original with the LC Desk."
            else:
                reply = "Invoice Team: The invoice is complete, signed and stamped. Ready to send."
        "settlements_release":
            var missing := _release_blockers()
            if not missing.is_empty():
                reply = "Invoice Team: Cooper, go finish the invoice first." if missing.size() > 1 or not missing.has("signed/stamped original") else "Invoice Team: The invoice is complete, but we still need the authorised signature and stamp."
            elif QUEST_START_MINUTES + quest_minutes >= QUEST_DEADLINE_MINUTES:
                reply = "Invoice Team: All documents correct. But it's after 14:00. The customer cannot pay at today's EUR cut-off.\nCooper: So I won the paperwork and lost the clock."
            else:
                invoice_issued = true
                reply = "Invoice Team: Send it.\n✓ INVOICE ISSUED & SENT — %s" % _format_quest_time(QUEST_START_MINUTES + quest_minutes)
        _:
            reply = "Cooper: Another question mark. Excellent."
    var gained := _assistant_newly_verified(verified_before)
    _assistant_success_line(gained)
    _show_dialogue(active_dialogue_destination, reply, followup_choices if not followup_choices.is_empty() else _dialogue_options(active_dialogue_destination))
    changed.emit()
    if invoice_issued:
        result_reached.emit(true)

func invoice_state() -> Dictionary:
    # Currency canon: invoice and unit price are USD. EUR cut-off is not a
    # confirmed settlement currency. The FX quote direction is unapproved.
    var quantity := PILOT_QUANTITY + " MT" if known_final_quantity else ""
    var unit := PILOT_UNIT_PRICE_PRECISE if known_unit_price and known_price_precision else (PILOT_UNIT_PRICE if known_unit_price else "")
    var verified_price := (PILOT_INVOICE_CURRENCY + " " + unit) if unit != "" else ""
    var adjustment_visible := false
    var adjustment := ""
    # No approved numerical LC total exists in the story;
    # show LC reconciliation as a verified status, not a fabricated USD figure.
    var total_text := "" # No approved numeric adjusted amount exists in this scenario yet.
    var payment_text := "Letter of credit" if known_payment_terms else ""
    var bank_text := "TreeBank (receiving bank)" if known_lc_bank else ""
    if known_lc_amount_match:
        payment_text += ("\n" if payment_text != "" else "") + "LC amount: reconciled"
    if known_fx_rate and known_fx_rate_date:
        payment_text += ("\n" if payment_text != "" else "") + "FX fixing: previous business day"
        bank_text += ("\n" if bank_text != "" else "") + "Reference: " + PILOT_FX_REFERENCE_RATE + " (direction unconfirmed)"
    var vat_text := "Zero-rated / Rotterdam, Netherlands / T1 verified" if known_vat_treatment else ""
    var signed := known_signature and original_pack_prepared and known_lc_requirements and known_vat_treatment and known_lc_amount_match
    var values := {
        "seller": "VorGun Trading" if known_legal_entity else "",
        "buyer": "ABC Forest Trading",
        "invoice_no": "",
        "invoice_date": "",
        "cargo": PILOT_PRODUCT_NAME, # Known from the very first draft.
        "quantity": quantity,
        "unit_price": verified_price,
        "total": total_text,
        "adjustment_visible": adjustment_visible,
        "adjustment": adjustment,
        "payment": payment_text,
        "bank": bank_text,
        "vat": vat_text,
        "signed": signed,
        "status": "ISSUED" if invoice_issued else "DRAFT"
    }
    return values

## Called only after the world confirms arrival and the player presses Enter.
## The caller supplies the exact current entrance; the session never moves actors.
func enter_landmark(landmark: String, entrance: Vector3) -> bool:
    if quest_failed or invoice_issued or not current_landmark.is_empty():
        return false
    if not LANDMARK_DESTINATIONS.has(landmark):
        return false # Coffee/Archive have no canonical office quest; never use default Settlements.
    current_landmark = landmark
    return_entrance = entrance
    active_dialogue_destination = LANDMARK_DESTINATIONS[landmark]
    if _office_is_closed(active_dialogue_destination):
        _show_closed_office(active_dialogue_destination)
    else:
        var returning := int(office_visit_counts.get(active_dialogue_destination, 0)) > 0
        office_visit_counts[active_dialogue_destination] = int(office_visit_counts.get(active_dialogue_destination, 0)) + 1
        if active_dialogue_destination == "TRADER" and known_unit_price and not trader_price_obtained:
            trader_price_acknowledged = true
        var options: Array = _dialogue_options(active_dialogue_destination) if returning or active_dialogue_destination == "SETTLEMENTS HALL" else _office_greeting_options(active_dialogue_destination)
        _show_dialogue(active_dialogue_destination, _office_greeting(active_dialogue_destination, returning), options)
    return true

func choose(action: String) -> bool:
    if current_landmark.is_empty() or quest_failed or invoice_issued:
        return false
    if not dialogue_options.any(func(option): return String(option[1]) == action):
        return false # Only actual displayed choices are actionable.
    _choose_dialogue(action)
    return true

func leave_office() -> void:
    _close_interaction()

func _close_interaction() -> void:
    if quest_failed or current_landmark.is_empty():
        return
    var landmark := current_landmark
    current_landmark = ""
    active_dialogue_destination = ""
    dialogue_options.clear()
    reward_sequence_id += 1
    reward_interaction_locked = false
    office_left.emit(landmark, return_entrance)
    changed.emit()

func _show_dialogue(destination: String, text: String, choices: Array) -> void:
    active_dialogue_destination = destination
    dialogue_text = text
    dialogue_options = choices.duplicate(true)
    dialogue_changed.emit(destination, text, dialogue_options)

func _spend_dialogue_minute() -> void:
    _spend_minutes(1, "CONVERSATION")

func _spend_minutes(amount: int, reason: String) -> void:
    if amount <= 0 or quest_failed or invoice_issued:
        return
    var before := quest_minutes
    if QUEST_START_MINUTES + quest_minutes + amount >= QUEST_DEADLINE_MINUTES:
        quest_minutes = QUEST_DEADLINE_MINUTES - QUEST_START_MINUTES
        quest_failed = true
    else:
        quest_minutes += amount
    if quest_minutes>before: minutes_spent.emit(quest_minutes-before,reason)
    changed.emit()
    if quest_failed:
        result_reached.emit(false)

## World route minutes already use V2.1's calibrated distance / 9.375.
## Do not charge real animation seconds, or charge both arrival and departure.
func charge_travel(minutes: int, mode: String) -> void:
    _spend_minutes(minutes, mode)

func boat_wait_minutes(island: String) -> int:
    return _boat_wait_minutes("B" if island == "east" else "A")
