extends RefCounted
## Unchanged source presentation helpers; VorGun fc5e861.
const INTRO_TEXT = "In another corner of the multiverse, a group of animals started a trading company.\nEveryone grabbed a role. Operations. Contracts. Trading. Finance.\n\nCooper joined last and chose the easy job: issue the invoice, collect the money. Easy.\n\n12:00 — our High Quality Energy (Physical Oil) delivery is complete. The customer is happy:\n\"Everything looks good. Send us the invoice 30 minutes before the EUR cut-off and we'll pay today.\"\n\nEUR cut-off: 14:30. Invoice deadline: 14:00.\nCooper opens his draft... and discovers that half of it is blank."
func _office_background_path(destination_name: String) -> String:
    if destination_name in ["OPERATIONS", "FX TOWER", "TRADE FINANCE", "TRADER"]:
        return "res://assets/story_scenes/background_harbor_office.png"
    return "res://assets/story_scenes/background_archive_hall.png"

func _office_desk_path(destination_name: String) -> String:
    if destination_name in ["FX TOWER", "TRADE FINANCE", "LC DESK"]:
        return "res://assets/story_scenes/ornate_navy_finance_reception_desk.png"
    if destination_name in ["CONTRACTS", "TRADER"]:
        return "res://assets/story_scenes/ornate_navy_and_gold_executive_desk.png"
    if destination_name == "COMPLIANCE":
        return "res://assets/story_scenes/ornate_nautical_steampunk_reception_desk.png"
    return "res://assets/story_scenes/ornate_navy_and_gold_reception_desk.png"

func _office_portrait_path(destination_name: String) -> String:
    # Existing approved individual characters, never TOP_DOWN navigation art.
    var portraits := {
        "OPERATIONS": "confident_wolf_in_leather_and_denim.png",
        "CONTRACTS": "fennec_fox_business_professional.png",
        "VAT": "professional_beaver_tax_advisor.png",
        "FX TOWER": "professional_otter_finance_consultant.png",
        "TRADER": "suited_bald_eagle_welcoming_gesture.png",
        "TRADE FINANCE": "professional_tortoise_consultant_with_laptop.png",
        "LC DESK": "professional_red_panda_archivist.png",
        "SETTLEMENTS HALL": "friendly_badger_in_denim_and_sneakers.png",
        "COMPLIANCE": "professional_sloth_with_binder.png"
    }
    var filename: String = String(portraits.get(destination_name, ""))
    return "res://assets/mascots/" + filename if filename != "" else ""

func _office_composition_rects(screen: Vector2, destination_name: String, npc_texture_size: Vector2, desk_texture_size: Vector2) -> Dictionary:
    # Source PNG measurements (Godot CI, 2026-10-11): characters 1024x1536,
    # desks 1983x793. Visible tabletops appear around 32-40% down the desk PNG.
    # Calibrated PNG content brings the VISIBLE worktop to 50-55% of the screen.
    var portrait := screen.y > screen.x
    var npc_height_ratios := {
        "OPERATIONS": 0.63, "TRADE FINANCE": 0.60, "COMPLIANCE": 0.59
    }
    var npc_top_ratios := {
        "OPERATIONS": 0.20, "TRADE FINANCE": 0.21, "COMPLIANCE": 0.22
    }
    var npc_height_ratio: float = float(npc_height_ratios.get(destination_name, 0.61)) if portrait else 0.87
    var npc_top_ratio: float = float(npc_top_ratios.get(destination_name, 0.21)) if portrait else 0.065
    var npc_aspect: float = npc_texture_size.x / maxf(npc_texture_size.y, 1.0)
    var npc_height: float = screen.y * npc_height_ratio
    var npc_width: float = npc_height * npc_aspect
    var max_npc_width: float = screen.x * (0.79 if portrait else 0.39)
    if npc_width > max_npc_width:
        npc_width = max_npc_width
        npc_height = npc_width / maxf(npc_aspect, 0.01)
    var npc_rect := Rect2(Vector2((screen.x - npc_width) * 0.5, screen.y * npc_top_ratio), Vector2(npc_width, npc_height))

    # Keep the desk's original aspect ratio; extend it beyond the left/right
    # viewport rather than stretching the furniture into a shallow strip.
    var desk_aspect: float = desk_texture_size.x / maxf(desk_texture_size.y, 1.0)
    var desk_width: float = screen.x * (2.50 if portrait else 1.08)
    var desk_height: float = desk_width / maxf(desk_aspect, 0.01)
    var worktop_alpha_rows := {
        "OPERATIONS": 0.40, "TRADE FINANCE": 0.32,
        "FX TOWER": 0.32, "LC DESK": 0.32, "COMPLIANCE": 0.33
    }
    var worktop_row: float = float(worktop_alpha_rows.get(destination_name, 0.38))
    var worktop_y: float = screen.y * (0.50 if portrait else 0.54)
    var desk_rect := Rect2(Vector2((screen.x - desk_width) * 0.5, worktop_y - worktop_row * desk_height), Vector2(desk_width, desk_height))
    return {"npc": npc_rect, "desk": desk_rect, "worktop_y": worktop_y}

