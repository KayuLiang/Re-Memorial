# Developer-only render/interaction exercise; never called by the story.
label rm_hud_visual_preview:
    $ opening_active = False
    $ rm_ui_test_skin_active = False
    $ rm_test_flow_active = False
    $ story_hud_hidden = False
    $ story_hud_status_unlocked = True
    $ story_hud_character_panel_unlocked = True
    $ story_hud_inventory_unlocked = True
    $ story_hud_medicine_unlocked = True
    $ inventory = ["手机", "药盒", "钱包"]
    $ rm_player = rm_core.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=renpy.random)
    $ rm_player.mood = -40
    $ rm_player.energy = 2
    $ rm_hud_sync_story_time("20XX年8月18日 星期五 下午 15：30")
    $ story_hud_quests = [{"kind": "main", "title": "主线排版测试", "description": "测试内容，不写入正式剧情。"}, {"kind": "side", "title": "支线排版测试一", "description": "测试内容。"}, {"kind": "side", "title": "支线排版测试二", "description": "测试内容。"}]
    $ story_hud_effects = [{"label": "状态排版测试", "tooltip": "测试内容，不写入正式规则。"}]
    scene bg doctor_office
    show fro casual default at fro_casual_left
    show ami casual default at ami_casual_right
    show pal casual default:
        xalign .5
        yalign 1.0
        zoom 1.2
    fro "界面排版测试。左、中、右三个人物同时出现时，顶部保留数值和功能入口，两侧留出任务与状态的位置。"
    "旁白仍使用同一块对白区域，不改变排版。"
    # Longest current authored paragraph (84 characters), copied only for fit.
    "（分支结算：mood+10，获得状态：成就感。mood+30，持续一天。获得状态·特质：热心。如果能帮到别人的话会更开心吧。与他人友好互动时获得的mood值奖励+5。）"
    ami "阿弥照片占位测试。"
    while True:
        "界面测试结束。可继续检查功能入口，或返回主菜单。"

label rm_qhd_opening_preview:
    $ opening_active = True
    $ story_hud_hidden = True
    scene black
    show screen opening_system_desktop("opening_identity_preview_body")
    pause
    hide screen opening_system_desktop
    return

testsuite hud_flat:
    parameter saved_hud_preferences = [None]
    parameter saved_test_window_limit = [None]
    parameter (test_width, test_height) = [(2560, 1440), (1920, 1080), (1280, 720)]
    before testcase:
        # Test scope survives Start(); restore user preferences even on failure.
        python:
            saved_hud_preferences = (_preferences.afm_enable, _preferences.afm_time, _preferences.skip_unseen, config.skip_delay, _preferences.fullscreen, _preferences.physical_size)
            _preferences.afm_enable = False
            # Test-only: allow a full QHD client area plus Windows title bar.
            # The production window still uses Ren'Py's normal desktop limits.
            saved_test_window_limit = renpy.display.draw.info["max_window_size"]
            renpy.display.draw.info["max_window_size"] = (max(test_width, saved_test_window_limit[0]), max(test_height, saved_test_window_limit[1]))
            renpy.set_physical_size((test_width, test_height))

    after testcase:
        python:
            _preferences.afm_enable, _preferences.afm_time, _preferences.skip_unseen, config.skip_delay, _preferences.fullscreen, _preferences.physical_size = saved_hud_preferences
            renpy.display.draw.info["max_window_size"] = saved_test_window_limit
            renpy.display.draw.resize()
        assert eval (_preferences.afm_enable, _preferences.afm_time, _preferences.skip_unseen, config.skip_delay, _preferences.fullscreen, _preferences.physical_size) == saved_hud_preferences
        run MainMenu(confirm=False)

testcase hud_flat.visual:
    run Start("rm_hud_visual_preview")
    pause .5
    assert eval (config.screen_width, config.screen_height) == (2560, 1440)
    python:
        print("QHD render size requested=%s actual=%s" % ((test_width, test_height), renpy.get_physical_size()))
    assert eval renpy.get_physical_size() == (test_width, test_height)
    assert eval rm_hud_visible()
    # Names and story bodies retain Huiwen; only global UI uses SemiBold Song.
    assert eval style.default.font is rememorial_ui_font
    assert eval style.rm_hud_white_text.font is rememorial_ui_font and opening_document_font is rememorial_ui_font
    assert eval renpy.get_displayable("say", "what").style.font is rememorial_dialogue_font
    assert eval renpy.get_displayable("say", "who").style.font is rememorial_dialogue_font
    assert eval not renpy.get_displayable("say", "who").style.bold
    assert eval style.history_text.font is rememorial_dialogue_font and style.history_name_text.font is rememorial_dialogue_font
    assert eval rm_hud_fraction(-10, 10) == 0
    assert eval rm_hud_fraction(12, 10) == 1
    assert eval rm_hud_fraction(4, 0) == 0
    assert eval rm_hud_clock_data()[3] == 0
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/day.png" % (test_width, test_height))
    # Five tabs use the same real hit bounds; hover must not advance dialogue.
    move pos (1467, 800)
    pause .2
    move id "dialogue_article" pos (.5, .4)
    pause .3
    assert id "dialogue_control_tip"
    assert "界面排版测试"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/history-tab.png" % (test_width, test_height))
    move pos (1467, 800)
    pause .2
    assert not id "dialogue_control_tip"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/tabs-rest.png" % (test_width, test_height))
    move pos (869, 101)
    pause .2
    assert id "hud_meter_tip"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/mood-tooltip.png" % (test_width, test_height))
    click "人物"
    assert screen "character_panel"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/character.png" % (test_width, test_height))
    assert eval not rm_hud_visible()
    run Hide("character_panel")
    click "骰组"
    assert eval renpy.get_screen_variable("panel_tab", "character_panel") == "dice"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/dice.png" % (test_width, test_height))
    run Hide("character_panel")
    click "背包"
    assert screen "inventory_panel"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/inventory.png" % (test_width, test_height))
    run Hide("inventory_panel")
    click "手机"
    assert screen "phone_panel"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/phone.png" % (test_width, test_height))
    run Hide("phone_panel")
    click "药盒"
    assert screen "medicine_panel"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/medicine.png" % (test_width, test_height))
    run Hide("medicine_panel")
    run SetVariable("current_time_minutes", 23 * 60)
    move pos (1467, 293)
    pause .2
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/night.png" % (test_width, test_height))
    click "继续"
    pause .2
    assert "旁白仍使用同一块对白区域"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/narration.png" % (test_width, test_height))
    # Component fixtures exercise 8/11 holes; they do not create gameplay rounds.
    run SetVariable("current_time_minutes", 15 * 60 + 30)
    run Show("rm_hud_clock", date_text="8月18日", weekday_text="周五", day_number=1, round_count=8, round_index=3)
    pause .2
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/eight-round-layout.png" % (test_width, test_height))
    run Hide("rm_hud_clock")
    run SetVariable("current_time_minutes", 23 * 60)
    run Show("rm_hud_clock", date_text="8月25日", weekday_text="周五", day_number=8, round_count=11, round_index=7)
    pause .2
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/eleven-round-layout.png" % (test_width, test_height))
    run Hide("rm_hud_clock")
    click "继续"
    pause .2
    assert "分支结算"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/long-dialogue.png" % (test_width, test_height))
    click "继续"
    pause .2
    assert "阿弥照片占位测试"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/ami-portrait.png" % (test_width, test_height))
    # Exercise the real icon actions, native wheel navigation and Esc menu.
    click id "dialogue_article"
    assert screen "history"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/history.png" % (test_width, test_height))
    keysym "K_ESCAPE"
    assert screen "say"
    click id "dialogue_sliders-horizontal"
    assert screen "preferences"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/preferences.png" % (test_width, test_height))
    keysym "K_ESCAPE"
    keysym "K_ESCAPE"
    assert screen "save"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/save.png" % (test_width, test_height))
    assert "读取游戏"
    keysym "K_ESCAPE"
    click id "dialogue_eye-slash"
    assert eval _windows_hidden
    assert not id "dialogue_article"
    assert not id "hud_nav_user-square"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/interface-hidden.png" % (test_width, test_height))
    click pos (1467, 800)
    assert eval not _windows_hidden
    assert "阿弥照片占位测试"
    click button 4 pos (1467, 800)
    assert "分支结算"
    click button 5 pos (1467, 800)
    assert "阿弥照片占位测试"
    run SetField(_preferences, "afm_enable", False)
    run SetField(_preferences, "afm_time", 30)
    click id "dialogue_arrows-clockwise"
    assert eval _preferences.afm_enable
    move pos (1467, 800)
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/auto-active.png" % (test_width, test_height))
    # Let hover rebuild the tab before the test posts mouse-down/up together.
    move id "dialogue_arrows-clockwise"
    pause .2
    click id "dialogue_arrows-clockwise"
    assert eval not _preferences.afm_enable
    run SetField(_preferences, "skip_unseen", True)
    run SetField(config, "skip_delay", 1000)
    click id "dialogue_fast-forward"
    assert eval config.skipping == "slow"
    click id "dialogue_fast-forward"
    assert eval not config.skipping
    move pos (1467, 800)
    pause .2
    move id "dialogue_eye-slash" pos (.5, .4)
    pause .3
    assert id "dialogue_control_tip"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/dialogue-controls.png" % (test_width, test_height))
    run SetVariable("story_hud_character_panel_unlocked", False)
    assert not id "hud_nav_user-square"
    run SetVariable("story_hud_hidden", True)
    assert eval not rm_hud_visible()

testcase hud_flat.opening:
    run Start("rm_qhd_opening_preview")
    pause .4
    assert eval (config.screen_width, config.screen_height) == (2560, 1440)
    assert eval renpy.get_physical_size() == (test_width, test_height)
    assert screen "opening_system_desktop"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/opening-desktop.png" % (test_width, test_height))
    run Show("opening_consent_document")
    pause .3
    assert screen "opening_consent_document"
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/opening-consent-top.png" % (test_width, test_height))
    move pos (1280, 700)
    scroll amount 60
    pause .3
    assert eval opening_consent_at_bottom(renpy.get_screen_variable("consent_adjustment", "opening_consent_document"))
    pause .2
    screenshot ("../../tmp/hud_qhd/%dx%d/opening-consent-bottom.png" % (test_width, test_height))
    run Hide("opening_consent_document")
