label rm_pillbox_test_preview:
    $ opening_active = False
    $ rm_ui_test_skin_active = False
    $ rm_test_flow_active = False
    $ story_hud_hidden = False
    $ story_hud_medicine_unlocked = True
    $ story_hud_status_unlocked = True
    $ rm_player = rm_create_initial_character()
    $ rm_core.add_medicine_stock(rm_ensure_player(), "venlafaxine", 6)
    $ rm_core.add_medicine_stock(rm_ensure_player(), "trazodone", 1)
    $ rm_core.add_medicine_stock(rm_ensure_player(), "alprazolam", 3)
    $ rm_pillbox.set_prescription(rm_ensure_player(), rm_pillbox.INITIAL_SLOTS, rm_pillbox.INITIAL_RECOMMENDATIONS)
    scene bg doctor_office
    "药盒测试准备。"
    call rm_medicine_node("morning")
    "药盒节点已完成。"
    while True:
        "药盒记录检查。"

testsuite pillbox:
    before testcase:
        python:
            pillbox_saved_preferences = (_preferences.afm_enable, _preferences.fullscreen, _preferences.physical_size)
            _preferences.afm_enable = False
            _preferences.fullscreen = False
            pillbox_saved_window = renpy.display.draw.info['max_window_size']
            renpy.display.draw.info['max_window_size'] = (2560,1440)
            renpy.set_physical_size((1280,720))
    after testcase:
        python:
            _preferences.afm_enable, _preferences.fullscreen, _preferences.physical_size = pillbox_saved_preferences
            renpy.display.draw.info['max_window_size'] = pillbox_saved_window
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase pillbox.render:
    run Start("rm_pillbox_test_preview")
    advance until screen "medicine_panel"
    run Function(renpy.set_physical_size, (1280,720))
    pause .4
    assert eval renpy.get_physical_size() == (1280,720)
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/1280x720.png"
    pause .2
    run Function(renpy.set_physical_size, (1920,1080))
    pause .4
    assert eval renpy.get_physical_size() == (1920,1080)
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/1920x1080.png"
    pause .2
    run Function(renpy.set_physical_size, (2560,1440))
    pause .4
    assert eval renpy.get_physical_size() == (2560,1440)
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/2560x1440.png"
    pause .2
    run Function(rm_pillbox.set_prescription, rm_player, [None]*8, {})
    assert "空槽"
    assert not eval renpy.get_displayable('medicine_panel','pillbox_take').is_sensitive()
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/empty.png"
    run Function(rm_pillbox.set_prescription, rm_player, ['trazodone']+[None]*7, {})
    assert "曲唑酮"
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/single.png"
    python:
        for drug in rm_core.PSYCHIATRIC_MEDICINES:
            rm_core.add_medicine_stock(rm_player, drug, 8)
        rm_pillbox.set_prescription(rm_player, list(rm_core.PSYCHIATRIC_MEDICINES)+['lithium','trazodone'], {})
        renpy.restart_interaction()
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/eight.png"

testcase pillbox.interaction:
    run Start("rm_pillbox_test_preview")
    advance until screen "medicine_panel"
    pause .3
    assert id "pillbox_recommended"
    click id "pillbox_left"
    pause .3
    assert eval rm_player.current_rotation_step == 7
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/turned.png"
    assert eval rm_pillbox.selection(rm_player,'morning')['drug'] == 'trazodone'
    click id "pillbox_right"
    pause .3
    assert eval rm_player.current_rotation_step == 0
    # A broad upper compartment hit, not a tiny tablet hit.
    click pos (1280,285)
    pause .3
    assert eval rm_player.current_rotation_step == 4
    assert eval rm_pillbox.selection(rm_player,'morning')['drug'] is None
    python:
        rm_pillbox_rotate(slot=0)
        rm_pillbox_rotate(1)
        rm_pillbox_take('morning')
        renpy.restart_interaction()
    pause .3
    assert eval rm_player.current_rotation_step == 0
    assert eval rm_player.medicine_counts['venlafaxine'] == 6
    click id "pillbox_take"
    pause .16
    assert eval renpy.get_screen_variable('busy','medicine_panel') == 'take'
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/take-motion.png"
    pause .4
    assert eval rm_player.medicine_counts['venlafaxine'] == 4
    assert eval rm_player.medicine_taken_today['venlafaxine'] == 1
    assert screen "medicine_panel"
    assert id "pillbox_taken"
    click id "pillbox_take"
    assert id "pillbox_cancel_repeat"
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/repeat.png"
    click id "pillbox_cancel_repeat"
    assert eval rm_player.medicine_counts['venlafaxine'] == 4
    click id "pillbox_take"
    click id "pillbox_confirm_repeat"
    pause .5
    assert eval rm_player.medicine_counts['venlafaxine'] == 2
    assert eval rm_player.medicine_taken_today['venlafaxine'] == 2
    click id "pillbox_left"
    pause .3
    click id "pillbox_take"
    pause .5
    assert eval rm_player.current_rotation_step == 7
    assert eval renpy.get_screen_variable('busy','medicine_panel') is None
    assert eval rm_player.medicine_counts['trazodone'] == 0
    assert eval renpy.get_displayable('medicine_panel','pillbox_stock').text == ['缺药']
    assert not eval renpy.get_displayable('medicine_panel','pillbox_take').is_sensitive()
    assert eval rm_player.trazodone_sleep_bonus_day == rm_player.day
    screenshot "E:/ChatGPT/Temp/rememorial-pillbox/exhausted.png"
    click id "pillbox_left"
    pause .3
    assert eval rm_pillbox.selection(rm_player,'manual')['definition']['prn']
    run Function(rm_core.add_emotion, rm_player, rm_core.EMOTION_ANXIETY)
    click id "pillbox_take"
    pause .5
    assert eval not rm_core.emotion_layers(rm_player, rm_core.EMOTION_ANXIETY)
    click id "pillbox_finish"
    assert not screen "medicine_panel"
    assert eval rm_player.pillbox_last_session['taken'] == dict(venlafaxine=2,trazodone=1,alprazolam=1)
    assert eval rm_player.pillbox_node_days['morning'] == rm_player.day
    run Show("medicine_panel")
    assert eval rm_player.current_rotation_step == 6
    keysym "K_ESCAPE"
    assert not screen "medicine_panel"

testcase pillbox.save_rollback:
    run Start("rm_pillbox_test_preview")
    advance until screen "medicine_panel"
    pause .3
    click id "pillbox_take"
    pause .5
    click id "pillbox_left"
    pause .3
    click id "pillbox_finish"
    assert "药盒节点已完成"
    run Function(renpy.save, 'pillbox-verification', include_screenshot=False)
    python:
        rm_player.medicine_counts['venlafaxine'] = 0
        rm_player.pillbox_slots[0] = None
        rm_player.current_rotation_step = 0
    run Function(renpy.load, 'pillbox-verification')
    pause .3
    assert eval rm_player.medicine_counts['venlafaxine'] == 4
    assert eval rm_player.medicine_taken_today['venlafaxine'] == 1
    assert eval rm_player.current_rotation_step == 7
    assert eval rm_player.pillbox_slots[0] == 'venlafaxine'
    assert eval rm_player.recommended_drugs['morning'] == ['venlafaxine']
    run Rollback(force=True)
    pause .3
    assert screen "medicine_panel"
    assert eval rm_player.medicine_counts['venlafaxine'] == 6
    assert eval not rm_player.medicine_taken_today
    assert eval rm_player.current_rotation_step == 0

testcase pillbox.contexts_and_hud:
    run Start("rm_pillbox_test_preview")
    advance until screen "medicine_panel"
    click id "pillbox_finish"
    assert eval rm_player.pillbox_last_session['taken'] == {}
    run Show("medicine_panel", context="evening")
    click id "pillbox_left"
    pause .3
    assert id "pillbox_recommended"
    click id "pillbox_finish"
    run Function(rm_pillbox.set_prescription, rm_player, ['lithium','aripiprazole','lamotrigine']+[None]*5, {'morning':['lithium']})
    run Function(rm_core.add_medicine_stock, rm_player, 'lithium', 2)
    run Show("medicine_panel")
    click id "pillbox_right"
    pause .3
    assert not id "pillbox_recommended"
    click id "pillbox_take"
    pause .5
    assert eval rm_player.pending_bipolar_medications['lithium']
    assert eval any(row['id'] == 'pending_lithium' for group in rm_hud_status.snapshot(rm_player) for row in group['items'])
    click id "pillbox_finish"
