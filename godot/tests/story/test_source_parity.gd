extends SceneTree
## Fixtures executed against the unmodified original main.gd in a disposable copy.
## Source checkout remains read-only. Regenerate with tools/capture_story_reference.gd.
const Session = preload("res://scripts/story/story_session.gd")
var failures := 0
var checks := 0
func _initialize() -> void:
    var fixtures: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tests/story/source-fixtures.json"))
    assert(fixtures.source_commit == Session.SOURCE_COMMIT, "Fixture source revision mismatch")
    for example in fixtures.cases:
        var session = Session.new()
        session.quest_minutes = int(example.initial_minutes)
        for record in example.records:
            session._choose_dialogue(String(record.action))
            for key in record.expected:
                var actual: Variant
                match key:
                    "reply": actual = session.dialogue_text
                    "choices": actual = session.dialogue_options
                    "blockers": actual = Array(session._release_blockers())
                    _: actual = session.get(key)
                checks += 1
                # JSON numeric values are floats; equality supports int/float here.
                if actual != record.expected[key]:
                    failures += 1
                    push_error("%s/%s/%s expected=%s actual=%s" % [example.name, record.action, key, str(record.expected[key]), str(actual)])
    if failures == 0:
        print("TELANICO_SOURCE_PARITY_PASS %d comparisons across %d cases" % [checks, fixtures.cases.size()])
    quit(0 if failures == 0 else 1)
