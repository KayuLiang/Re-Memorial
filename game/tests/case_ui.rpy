# Native render/interaction exercise. Test content never enters the story.
label rm_case_visual_preview:
    $ opening_active = False
    $ story_hud_hidden = False
    $ story_hud_character_panel_unlocked = True
    $ rm_player = rm_core.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=renpy.random)
    $ rm_player.attribute_values["str"] = 1
    $ rm_player.training_fatigue["test_jogging"] = 1
    $ story_hud_effects = []
    scene bg doctor_office
    show screen character_panel
    "病例界面运行测试。"
    while True:
        "病例界面运行测试。"

label rm_case_archive_preview:
    $ opening_active = False
    $ rm_player = rm_core.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=renpy.random)
    $ story_hud_effects = []
    scene bg doctor_office
    "状态记录前。"
    $ story_hud_effects = [{"id": "case_test_archive", "label": "记录测试", "tooltip": "这是原生存档与回滚测试。"}]
    "状态生效。"
    $ story_hud_effects = []
    "状态结束。"
    while True:
        "记录测试结束。"

testsuite case_ui:
    parameter case_saved_preferences = [None]
    parameter case_saved_window = [None]
    parameter (case_width, case_height) = [(2560, 1440), (1920, 1080), (1280, 720)]
    before testcase:
        python:
            case_saved_preferences = (_preferences.afm_enable, _preferences.fullscreen, _preferences.physical_size)
            _preferences.afm_enable = False
            case_saved_window = renpy.display.draw.info["max_window_size"]
            renpy.display.draw.info["max_window_size"] = (max(case_width, case_saved_window[0]), max(case_height, case_saved_window[1]))
            renpy.set_physical_size((case_width, case_height))
    after testcase:
        python:
            _preferences.afm_enable, _preferences.fullscreen, _preferences.physical_size = case_saved_preferences
            renpy.display.draw.info["max_window_size"] = case_saved_window
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase case_ui.pages:
    run Start("rm_case_visual_preview")
    pause .4
    assert eval renpy.get_physical_size() == (case_width, case_height)
    assert screen "character_panel"
    assert id "case_radar"
    assert id "case_slip_0"
    assert eval not rm_hud_visible()
    screenshot ("../../tmp/case_ui/%dx%d/overview.png" % (case_width, case_height))
    click id "case_radar"
    assert id "case_attribute_str"
    assert eval renpy.get_screen_variable("panel_tab", "character_panel") == "attributes"
    screenshot ("../../tmp/case_ui/%dx%d/attributes.png" % (case_width, case_height))
    click id "case_attribute_int"
    assert eval renpy.get_screen_variable("case_attribute", "character_panel") == "int"
    click id "case_tab_summary"
    click id "case_slip_1"
    assert eval renpy.get_screen_variable("case_status", "character_panel") == "attr_value_str_1"
    assert id "case_status_description"
    screenshot ("../../tmp/case_ui/%dx%d/status-owned.png" % (case_width, case_height))
    click id "case_filter_locked"
    assert "未解锁"
    assert id "case_page_next"
    click id "case_page_next"
    assert eval renpy.get_screen_variable("case_page", "character_panel") == 1
    click id "case_filter_all"
    screenshot ("../../tmp/case_ui/%dx%d/status-all.png" % (case_width, case_height))
    python:
        rm_player.attribute_values["str"] = 0
        rm_case_sync()
    click id "case_filter_unlocked"
    assert eval "attr_value_str_1" in rm_case_history
    assert eval not any(row["id"] == "attr_value_str_1" for row in rm_case_snapshot['statuses'])
    click id "case_status_row_2"
    screenshot ("../../tmp/case_ui/%dx%d/status-archive.png" % (case_width, case_height))
    click id "case_tab_skills"
    assert id "case_empty"
    pause .2
    screenshot ("../../tmp/case_ui/%dx%d/skills.png" % (case_width, case_height))
    assert eval renpy.get_widget("character_panel", "case_empty").get_all_text() == "暂无内容"
    click id "case_tab_spells"
    assert id "case_empty"
    click id "case_close"
    assert not screen "character_panel"
    run Show("character_panel", start_tab="dice")
    assert eval renpy.get_screen_variable("panel_tab", "character_panel") == "dice"
    pause .2
    assert eval len(rm_status_dice_pool_summary()) > 0
    click id "dice_close"
    run Show("character_panel")
    assert id "case_radar"
    run Hide("character_panel")
    run Show("character_panel")
    click id "case_back"
    assert not screen "character_panel"

testcase case_ui.archive:
    run Start("rm_case_archive_preview")
    assert eval "case_test_archive" not in rm_case_history
    advance until "状态生效。"
    assert eval "case_test_archive" in rm_case_history
    advance until "状态结束。"
    assert eval not any(row['id'] == "case_test_archive" for row in rm_case_snapshot['statuses'])
    assert eval "case_test_archive" in rm_case_history
    run Function(renpy.save, "case-ui-archive-test", include_screenshot=False)
    run SetVariable("rm_case_history", {})
    assert eval "case_test_archive" not in rm_case_history
    run Function(renpy.load, "case-ui-archive-test")
    pause .2
    assert eval "case_test_archive" in rm_case_history
    assert eval rm_case_owner is rm_player
    run Rollback()
    pause .2
    assert eval any(row['id'] == "case_test_archive" for row in rm_case_snapshot['statuses'])
    run Rollback()
    pause .2
    assert eval "case_test_archive" not in rm_case_history
    assert eval not any(row['id'] == "case_test_archive" for row in rm_case_snapshot['statuses'])

testcase case_ui.dense:
    run Start("rm_case_visual_preview")
    python:
        rm_player.mood = -200
        story_hud_effects = [{"id": "case_dense_%d" % i, "label": "用于检查长名称显示的状态测试第%d项" % i, "tooltip": "排版测试说明。" * 65} for i in range(12)]
        rm_case_sync()
    click id "case_tab_summary"
    screenshot ("../../tmp/case_ui/%dx%d/overview-dense.png" % (case_width, case_height))
    click id "case_status_link"
    click id "case_status_row_3"
    screenshot ("../../tmp/case_ui/%dx%d/status-dense.png" % (case_width, case_height))
    assert id "case_page_next"
    click id "case_page_next"
    assert eval renpy.get_screen_variable("case_page", "character_panel") == 1
    click id "case_status_row_5"
    assert id "case_status_description"
