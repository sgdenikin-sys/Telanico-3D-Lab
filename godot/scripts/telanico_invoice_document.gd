extends Control
# Runtime Sales Invoice renderer. Only the approved RUNTIME/ PNG files are loaded.
# Coordinates are in the artist's original 1122 x 1402 pixel document space.
const SOURCE_DIR := "res://assets/ui/INVOICE/RUNTIME/"
const PAGE_SIZE := Vector2(1122.0, 1402.0)
const SPLIT_Y := 780.0
const EXTRA_ROW := 96.0
const INK := Color("#142A42")
const MUTED := Color("#344963")

var sheet: Control
var upper: TextureRect
var lower: TextureRect
var inserted_paper: TextureRect
var adjustment_row: PanelContainer
var adjustment_value: Label
var signature_art: TextureRect
var stamp_art: TextureRect
var review_mark: TextureRect
var fields: Dictionary = {}
var review_tween: Tween
var ink_tween: Tween
var pending_ink_fields: Array[String] = []
var applied_state: Dictionary = {}
var queued_mark := ""
var first_bind := true
var fit_scale := 0.65
var base_fit_scale := 0.65
var zoom_factor := 1.0

func _ready() -> void:
    mouse_filter = Control.MOUSE_FILTER_STOP
    sheet = Control.new()
    sheet.name = "InvoiceArtwork"
    sheet.mouse_filter = Control.MOUSE_FILTER_IGNORE
    sheet.position = Vector2.ZERO
    sheet.size = PAGE_SIZE
    add_child(sheet)
    var base: Texture2D = load(SOURCE_DIR + "invoice_blank_base.png")
    upper = _add_slice(base, Rect2(0, 0, PAGE_SIZE.x, SPLIT_Y), Vector2.ZERO, Vector2(PAGE_SIZE.x, SPLIT_Y))
    inserted_paper = _add_slice(base, Rect2(0, SPLIT_Y, PAGE_SIZE.x, 14), Vector2(0, SPLIT_Y), Vector2(PAGE_SIZE.x, EXTRA_ROW))
    inserted_paper.visible = false
    lower = _add_slice(base, Rect2(0, SPLIT_Y, PAGE_SIZE.x, PAGE_SIZE.y - SPLIT_Y), Vector2(0, SPLIT_Y), Vector2(PAGE_SIZE.x, PAGE_SIZE.y - SPLIT_Y))
    _field("seller", Vector2(145, 421), Vector2(395, 52), 27)
    _field("buyer", Vector2(606, 421), Vector2(398, 52), 27)
    _field("invoice_no", Vector2(148, 576), Vector2(400, 39), 24)
    _field("invoice_date", Vector2(606, 576), Vector2(400, 39), 24)
    _field("cargo", Vector2(135, 693), Vector2(390, 58), 18) # Long known product, not a mystery field.
    _field("quantity", Vector2(555, 693), Vector2(130, 57), 23, true)
    _field("unit_price", Vector2(693, 693), Vector2(154, 57), 22, true)
    _field("total", Vector2(855, 693), Vector2(150, 57), 19, true)
    # These fields move with the lower crop when the density row is inserted.
    _field("payment", Vector2(145, 845), Vector2(400, 119), 24)
    _field("bank", Vector2(609, 845), Vector2(395, 119), 23)
    _field("vat", Vector2(145, 1054), Vector2(847, 63), 23)
    _field("status", Vector2(385, 315), Vector2(390, 30), 18, true)
    adjustment_row = PanelContainer.new()
    adjustment_row.name = "DensityAdjustmentRow"
    adjustment_row.position = Vector2(121, SPLIT_Y + 9)
    adjustment_row.size = Vector2(878, EXTRA_ROW - 18)
    var style := StyleBoxFlat.new()
    style.bg_color = Color("#F1E3C8E8")
    style.border_color = INK
    style.set_border_width_all(2)
    style.set_corner_radius_all(4)
    style.set_content_margin_all(9)
    adjustment_row.add_theme_stylebox_override("panel", style)
    sheet.add_child(adjustment_row)
    var content := VBoxContainer.new()
    content.add_theme_constant_override("separation", 2)
    adjustment_row.add_child(content)
    var title := Label.new()
    title.text = "DENSITY ESCALATION / PRICE ADJUSTMENT"
    title.add_theme_color_override("font_color", INK)
    title.add_theme_font_size_override("font_size", 20)
    content.add_child(title)
    adjustment_value = Label.new()
    adjustment_value.add_theme_font_size_override("font_size", 21)
    adjustment_value.add_theme_color_override("font_color", MUTED)
    content.add_child(adjustment_value)
    adjustment_row.visible = false
    signature_art = _overlay("invoice_signature_blue_sample.png", Vector2(155, 1163), Vector2(415, 154))
    stamp_art = _overlay("invoice_company_stamp_blue_mockup.png", Vector2(748, 1158), Vector2(213, 166))
    signature_art.visible = false
    stamp_art.visible = false
    var sample := _field("sample_note", Vector2(157, 1292), Vector2(455, 23), 13)
    sample.text = "ILLUSTRATIVE SIGNATURE / STAMP — FICTIONAL PILOT"
    sample.visible = false
    review_mark = _overlay("invoice_markup_red_check.png", Vector2(960, 696), Vector2(60, 60))
    review_mark.name = "ReviewAnnotation"
    review_mark.visible = false
    set_fit_width(720.0)

func _add_slice(base: Texture2D, region: Rect2, at: Vector2, dimensions: Vector2) -> TextureRect:
    var atlas := AtlasTexture.new()
    atlas.atlas = base
    atlas.region = region
    atlas.filter_clip = true
    var rect := TextureRect.new()
    rect.texture = atlas
    rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
    rect.stretch_mode = TextureRect.STRETCH_SCALE
    rect.position = at
    rect.size = dimensions
    rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
    sheet.add_child(rect)
    return rect

func _field(key: String, at: Vector2, dims: Vector2, font: int, center: bool = false) -> Label:
    var label := Label.new()
    label.name = "Value_" + key
    label.position = at
    label.size = dims
    label.add_theme_font_size_override("font_size", font)
    label.add_theme_color_override("font_color", INK)
    label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    if center:
        label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    label.mouse_filter = Control.MOUSE_FILTER_IGNORE
    sheet.add_child(label)
    fields[key] = label
    return label

func _overlay(filename: String, at: Vector2, dims: Vector2) -> TextureRect:
    var rect := TextureRect.new()
    rect.texture = load(SOURCE_DIR + filename)
    rect.position = at
    rect.size = dims
    rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
    rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
    sheet.add_child(rect)
    return rect

func set_fit_width(available_width: float) -> void:
    base_fit_scale = clampf((available_width - 8.0) / PAGE_SIZE.x, 0.24, 1.0)
    _apply_zoom()


func set_manual_zoom(multiplier: float) -> void:
    zoom_factor = clampf(multiplier, 1.0, 3.0)
    _apply_zoom()


func _apply_zoom() -> void:
    fit_scale = base_fit_scale * zoom_factor
    sheet.scale = Vector2.ONE * fit_scale
    _resize_canvas()

func _resize_canvas() -> void:
    var extended: float = EXTRA_ROW if adjustment_row.visible else 0.0
    sheet.size = PAGE_SIZE + Vector2(0, extended)
    custom_minimum_size = sheet.size * fit_scale
    size = custom_minimum_size

func _set_field(key: String, value: String) -> void:
    (fields[key] as Label).text = value

func value_of(key: String) -> String:
    return (fields[key] as Label).text

func apply_state(state: Dictionary) -> void:
    var old_state: Dictionary = applied_state
    applied_state = state.duplicate(true)
    if not first_bind:
        for key in ["seller", "quantity", "unit_price", "total", "payment", "bank", "vat"]:
            if String(old_state.get(key, "")) != String(state.get(key, "")) and String(state.get(key, "")) != "" and not pending_ink_fields.has(key):
                pending_ink_fields.append(key)
        if String(old_state.get("adjustment", "")) != String(state.get("adjustment", "")) and String(state.get("adjustment", "")) != "" and not pending_ink_fields.has("adjustment"):
            pending_ink_fields.append("adjustment")
    for key in ["seller", "buyer", "invoice_no", "invoice_date", "cargo",
        "quantity", "unit_price", "total", "payment", "bank", "vat", "status"]:
        _set_field(key, String(state.get(key, "")))
    var expansion := bool(state.get("adjustment_visible", false))
    var shift: float = EXTRA_ROW if expansion else 0.0
    inserted_paper.visible = expansion
    adjustment_row.visible = expansion
    adjustment_value.text = String(state.get("adjustment", ""))
    lower.position.y = SPLIT_Y + shift
    for key in ["payment", "bank", "vat"]:
        var base_y := {"payment": 845.0, "bank": 845.0, "vat": 1054.0}
        (fields[key] as Label).position.y = float(base_y[key]) + shift
    signature_art.position.y = 1163.0 + shift
    stamp_art.position.y = 1158.0 + shift
    (fields["sample_note"] as Label).position.y = 1292.0 + shift
    var final: bool = bool(state.get("signed", false))
    signature_art.visible = final
    stamp_art.visible = final
    (fields["sample_note"] as Label).visible = final
    _resize_canvas()
    if first_bind:
        first_bind = false
        return
    # Missing TOTAL is a persistent educational annotation. It is not a
    # transient review stamp and must not predate the new ink animation.
    var total_missing := (String(state.get("quantity", "")) != "" or String(state.get("unit_price", "")) != "") and String(state.get("total", "")) == ""
    if not total_missing and review_mark != null:
        review_mark.visible = false
    if not bool(old_state.get("signed", false)) and final:
        queued_mark = "check"
    elif not total_missing and old_state.get("total", "") != state.get("total", "") and String(state.get("total", "")) != "":
        queued_mark = "check"
    elif not total_missing and old_state.get("vat", "") != state.get("vat", "") and String(state.get("vat", "")) != "":
        queued_mark = "circle"
    elif not total_missing and not bool(old_state.get("adjustment_visible", false)) and expansion:
        queued_mark = "question"
    if total_missing:
        queued_mark = "total_missing"


func show_review_mark() -> void:
    _reveal_new_ink()
    if queued_mark == "" or review_mark == null:
        return
    if review_tween != null and review_tween.is_running():
        review_tween.kill()
    var mode := queued_mark
    queued_mark = ""
    review_mark.texture = load(SOURCE_DIR + ("invoice_markup_red_question.png" if mode == "question" else ("invoice_markup_red_circle.png" if mode == "circle" or mode == "total_missing" else "invoice_markup_red_check.png")))
    var shift := EXTRA_ROW if adjustment_row.visible else 0.0
    review_mark.position = Vector2(852, 693) if mode == "total_missing" else (Vector2(947, SPLIT_Y + 10) if mode == "question" else (Vector2(955, 1058 + shift) if mode == "circle" else Vector2(963, 705)))
    review_mark.size = Vector2(154, 60) if mode == "total_missing" else Vector2(60, 60)
    review_mark.visible = true
    review_mark.modulate.a = 0.0
    review_mark.pivot_offset = review_mark.size * 0.5
    review_mark.scale = Vector2.ONE * 0.80
    review_tween = create_tween().set_parallel(true)
    review_tween.tween_property(review_mark, "modulate:a", 0.75, 0.24).set_trans(Tween.TRANS_SINE)
    review_tween.tween_property(review_mark, "scale", Vector2.ONE, 0.31).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
    if mode != "total_missing":
        review_tween.chain().tween_interval(0.70)
        review_tween.tween_property(review_mark, "modulate:a", 0.0, 0.40)
        review_tween.chain().tween_callback(func() -> void: review_mark.visible = false)


func stage_pending_ink() -> void:
    # Keep newly obtained values blank until the one-second reveal cue.
    for key in pending_ink_fields:
        var field_label: Label = adjustment_value if key == "adjustment" else fields.get(key) as Label
        if field_label != null:
            field_label.visible_characters = 0

func _reveal_new_ink() -> void:
    # Fast pen-like reveal of newly verified entries on the existing invoice art.
    # The text is already in the source of truth; only its presentation animates.
    if pending_ink_fields.is_empty():
        return
    if ink_tween != null and ink_tween.is_running():
        ink_tween.kill()
    ink_tween = create_tween()
    for key in pending_ink_fields:
        var field_label: Label = adjustment_value if key == "adjustment" else fields.get(key) as Label
        if field_label == null:
            continue
        field_label.visible_characters = 0
        var letters := field_label.get_total_character_count()
        ink_tween.tween_property(field_label, "visible_characters", letters, clampf(float(letters) * 0.025, 0.15, 0.48))
    pending_ink_fields.clear()
