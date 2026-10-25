extends SceneTree
func _initialize():call_deferred("run")
func run():
    var game=load("res://scenes/story_game.tscn").instantiate()
    root.add_child(game)
    await process_frame
    var world=game.world
    var sun: DirectionalLight3D=world.get_node("LateAfternoonSun_NW")
    assert(sun.position.x<0 and sun.position.z<0 and sun.position.y>0)
    var elevation=rad_to_deg(asin(sun.position.normalized().y))
    assert(elevation>17 and elevation<24,"Late afternoon, not a horizon/below-ground sun")
    var environment: Environment=world.get_node("CampusSkyAndContactAO").environment
    assert(environment.background_mode==Environment.BG_SKY and environment.sky!=null)
    assert(environment.ssao_enabled and environment.ssao_radius<2)
    assert(environment.fog_enabled and not environment.volumetric_fog_enabled)
    assert(world.world.get_node("LowWaterHaze").cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
    var bushes=world.world.find_children("Soft Canopy Bush*","MeshInstance3D",true,false)
    assert(bushes.size()==36)
    assert(world.world.get_node("InstancedBushCrowns").multimesh.instance_count==36)
    var material=bushes[0].material_override
    for bush in bushes:
        assert(not bush.visible,"Source nodes must not double-draw the instanced crowns")
        assert(bush.material_override==material,"Share the wind material")
        assert(bush.get_child_count()==0,"Decoration must not add path blockers")
        assert(bush.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
    assert(world.world.find_children("CC0 tree*","MeshInstance3D",true,false).size()==38)
    for button in world.top_buttons.values()+world.buttons.values():
        assert(not button.has_node("HudPerimeterRunner"),"No animated edges on translucent 3D controls")
    assert(world.top_buttons.Explore.size.is_equal_approx(Vector2(104,52)),"Desktop control size must stay unchanged")
    for button in game.ui_buttons.values():
        assert(button.has_node("HudPerimeterRunner"),"Asset HUD retains animation")
    # This renderer/UI fixture must not start native MP3/WAV playback just before
    # process shutdown. Audio/opening/restart have separate existing regressions.
    game.music.queue_free()
    game.music = null
    game.sfx_on = false
    game._characters();game.start_game();game.close_modal();game.close_modal()
    assert(game.adapter.enter("settlements"))
    for button in game.choice_list.get_children():
        if button is Button:assert(button.has_node("HudPerimeterRunner"),"Dialogue retains click feedback")
    var feedback: Button=game._button(game.ui,"Feedback",func():pass)
    feedback.position=Vector2(10,root.size.y-64)
    feedback.size=Vector2(150,52)
    await process_frame
    assert(not feedback.get_node("HudPerimeterRunner").visible,"Hover/focus alone must not animate")
    var point=feedback.get_global_rect().get_center()
    for down in [true,false]:
        var event:=InputEventMouseButton.new()
        event.button_index=MOUSE_BUTTON_LEFT
        event.pressed=down
        event.position=point
        event.global_position=point
        root.push_input(event,true)
        await process_frame
        if down:assert(feedback.get_node("HudPerimeterRunner").visible,"Dialogue-style buttons animate immediately on press, before the action replaces them")
    game.queue_free()
    await process_frame
    await process_frame
    print("TELANICO_ATMOSPHERE_PASS NW sun, cached sky, AO/fog, 38 trees/36 bushes, shared materials, correct UI effects")
    quit(0)
