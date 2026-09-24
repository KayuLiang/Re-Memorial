# Developer-only fixtures: these statuses are not applied to authored scenes.
init python:
    def rm_status_test_transform(widget_id):
        widget = renpy.get_displayable("rm_test_status_overlay", widget_id)
        def find(node, parent=None):
            if isinstance(node, Transform) and getattr(node.function, "func", None) is rm_status_motion:
                parent = node
            if node is widget:
                return parent
            for child in node.visit():
                if child is not None:
                    found = find(child, parent)
                    if found is not None:
                        return found
            return None
        return find(renpy.get_screen("rm_test_status_overlay"))

    def rm_status_test_player():
        player = rm_core.create_initial_character()
        player.ember = 180
        player.ect_residual_days = 27
        player.drug_dependence = True
        player.pending_bipolar_medications.update(lithium=True, aripiprazole=True, lamotrigine=True)
        player.trazodone_sleep_bonus_day = player.day
        player.current_weather = rm_core.WEATHER_CLOUDY
        player.current_temperature = 50
        player.fatigue_layers = 2
        player.hunger_level = 1
        player.palpitations = True
        player.intoxication = 1
        player.good_routine = True
        for emotion, layers in (("anxiety", 2), ("distraction", 3), ("joy", 1)):
            rm_core.add_emotion(player, emotion, layers)
        player.long_emotions.update(confidence=True, doubt=True)
        player.injuries.update(fracture=dict(reinjury=0), strain=dict(reinjury=0), sprain=dict(reinjury=1))
        player.digestive_disorder = dict(layers=1)
        player.malnutrition = dict(layers=2)
        player.training_fatigue.update({key: 2 for key in rm_core.TEST_TRAINING_SCHEDULE_ATTRIBUTES})
        player.time_habits.update({"morning:study": True, "afternoon:training": True})
        return player

testsuite status_hud:
    parameter saved_status_preferences = [None]
    parameter saved_status_limit = [None]
    parameter (status_width, status_height) = [(2560, 1440), (1920, 1080), (1280, 720)]
    before testcase:
        python:
            saved_status_preferences = (_preferences.afm_enable, _preferences.transitions, _preferences.fullscreen, _preferences.physical_size)
            _preferences.afm_enable = False
            _preferences.transitions = 2
            saved_status_limit = renpy.display.draw.info["max_window_size"]
            renpy.display.draw.info["max_window_size"] = (max(status_width, saved_status_limit[0]), max(status_height, saved_status_limit[1]))
            renpy.set_physical_size((status_width, status_height))
    after testcase:
        python:
            _preferences.afm_enable, _preferences.transitions, _preferences.fullscreen, _preferences.physical_size = saved_status_preferences
            renpy.display.draw.info["max_window_size"] = saved_status_limit
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase status_hud.flow:
    run Start("rm_hud_visual_preview")
    run SetVariable("story_hud_effects", [])
    pause .3
    assert not id "status_hud"
    run SetVariable("rm_player", rm_status_test_player())
    pause .4
    assert eval renpy.get_physical_size() == (status_width, status_height)
    assert id "status_expand"
    assert id "status_group_treatment"
    assert id "status_group_current"
    assert id "status_group_injury"
    assert id "status_group_life"
    assert not id "status_item_weather"
    python:
        print("Status HUD environment:", rm_status_environment())
    assert id "hud_environment"
    assert eval renpy.render(renpy.get_displayable("top_status", "hud_environment"), 440, 100, 0, 0).get_size()[1] == 78
    assert eval rm_status_environment() == ["多云 · 适温", "医院"]
    assert eval rm_status_text_width("WWW") > rm_status_text_width("iii")
    assert eval isinstance(rm_status_text_width("余烬"), int)
    move pos (1200, 700)
    pause .1
    assert eval renpy.get_displayable("rm_test_status_overlay", "status_group_treatment").style.xmaximum == RM_STATUS_NARROW
    assert eval int(rm_status_test_transform("status_group_treatment").xpos) == RM_STATUS_WIDE - RM_STATUS_NARROW
    assert eval int(rm_status_test_transform("status_group_treatment").ypos) == 40
    assert eval int(rm_status_test_transform("status_item_ember").ypos) == 28
    screenshot ("../../tmp/status_hud/%dx%d/collapsed.png" % (status_width, status_height))
    assert id "status_more_treatment"
    click id "status_more_treatment"
    pause .3
    assert eval renpy.get_displayable("rm_test_status_overlay", "status_group_treatment").style.xmaximum == RM_STATUS_WIDE
    assert "界面排版测试"
    click id "status_expand"
    pause .3
    run Function(renpy.set_focus, "rm_test_status_overlay", "status_more_treatment")
    keysym "K_RETURN"
    pause .3
    assert eval renpy.get_displayable("rm_test_status_overlay", "status_group_treatment").style.xmaximum == RM_STATUS_WIDE
    click id "status_expand"
    pause .3
    run Function(renpy.set_focus, "rm_test_status_overlay", "status_expand")
    keysym "K_RETURN"
    pause .08
    assert eval int(rm_status_test_transform("status_item_pending_lithium").ypos) == 70
    screenshot ("../../tmp/status_hud/%dx%d/expanding.png" % (status_width, status_height))
    pause .3
    assert eval renpy.get_displayable("rm_test_status_overlay", "status_group_treatment").style.xmaximum == RM_STATUS_WIDE
    assert eval int(rm_status_test_transform("status_group_treatment").xpos) == 0
    assert eval RM_HUD_SIDE_Y + rm_status_test_transform("status_expand").ypos + 40 <= RM_HUD_DIALOGUE_Y - 96 - 8
    assert eval renpy.render(renpy.get_displayable("rm_test_status_overlay", "status_item_ember"), RM_STATUS_WIDE, 100, 0, 0).get_size()[0] < 150
    assert not screen "rm_hud_details"
    assert screen "say"
    assert "界面排版测试"
    move pos (1200, 700)
    pause .1
    screenshot ("../../tmp/status_hud/%dx%d/expanded.png" % (status_width, status_height))
    run Function(renpy.hide, "pal")
    pause .2
    screenshot ("../../tmp/status_hud/%dx%d/two-characters.png" % (status_width, status_height))
    move id "status_item_ember"
    pause .2
    assert id "status_hud_tip"
    screenshot ("../../tmp/status_hud/%dx%d/detail.png" % (status_width, status_height))
    click id "status_item_ember"
    assert "界面排版测试"
    run Function(renpy.set_focus, "rm_test_status_overlay", "status_item_ember")
    keysym "K_RETURN"
    assert "界面排版测试"
    move pos (1200, 700)
    click id "status_expand"
    pause .3
    assert eval renpy.get_displayable("rm_test_status_overlay", "status_group_treatment").style.xmaximum == RM_STATUS_NARROW
    # Rapid toggles must leave a valid end layout and never advance the dialogue.
    click id "status_expand"
    click id "status_expand"
    pause .3
    assert eval renpy.get_displayable("rm_test_status_overlay", "status_group_treatment").style.xmaximum == RM_STATUS_NARROW
    assert "界面排版测试"
    run SetField(_preferences, "transitions", 0)
    click id "status_expand"
    pause .1
    assert eval renpy.get_displayable("rm_test_status_overlay", "status_group_treatment").style.xmaximum == RM_STATUS_WIDE
    # Dark background, one right-side character; positions are the production transforms.
    run Function(renpy.hide, "fro")
    run Function(renpy.hide, "pal")
    run Function(renpy.show, "bg", what=Solid("#182129"), zorder=-1)
    pause .3
    screenshot ("../../tmp/status_hud/%dx%d/dark-right-character.png" % (status_width, status_height))
    click id "status_expand"
    run SetVariable("rm_player", rm_core.create_initial_character())
    run SetVariable("story_hud_effects", [dict(id="emotion_anxiety", label="焦虑", category="emotion", display_count=2, tooltip="测试状态详情。")])
    pause .3
    assert id "status_group_current"
    assert not id "status_group_treatment"
    assert not id "status_group_injury"
    assert not id "status_group_life"
    assert not id "status_expand"
    assert not id "status_more_current"
    screenshot ("../../tmp/status_hud/%dx%d/sparse.png" % (status_width, status_height))
    # A long authored label keeps its complete name in accessible detail, not beyond the sidebar.
    run SetVariable("story_hud_effects", [dict(id="long_label", label="很长的剧情长期状态名称用于测试自动省略与完整详情", display_count=180, tooltip="测试内容。")])
    pause .3
    move id "status_item_long_label"
    pause .2
    assert id "status_hud_tip"
    screenshot ("../../tmp/status_hud/%dx%d/long-label.png" % (status_width, status_height))
