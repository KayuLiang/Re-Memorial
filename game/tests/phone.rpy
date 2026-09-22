# Developer-only interaction coverage; screenshots live in task scratch on E:.
label rm_phone_test_scene:
    $ _autosave = False
    $ opening_active = False
    $ story_hud_hidden = True
    $ inventory = ["手机"]
    $ rm_hud_sync_story_time("20XX年8月18日 星期五 下午 13：30")
    scene bg bathroom
    "手机交互测试。"
    jump rm_phone_test_exchange

label rm_phone_test_exchange:
    $ phone_begin_story_ami()
    while not phone_story_ami_sent:
        call screen phone_panel(start_app="messages", start_chat=("ami" if phone_story_ami_reply_ready or phone_story_ami_sent else None), story_mode=True)
        if _return == "reply_prompt":
            show screen phone_panel_background(start_chat="ami", story_mode=True) onlayer master
            "独白测试。"
            hide screen phone_panel_background onlayer master
            $ phone_prepare_story_ami_reply()
        elif not phone_story_ami_sent:
            call screen phone_story_resume
    "回复完成。"
    pause
    return

testsuite phone:
    parameter saved_preferences = [None]
    parameter saved_window_limit = [None]
    before testcase:
        python:
            saved_preferences = (_preferences.afm_enable, _preferences.fullscreen, _preferences.physical_size)
            _preferences.afm_enable = False
            saved_window_limit = renpy.display.draw.info["max_window_size"]
            renpy.display.draw.info["max_window_size"] = (max(1920, saved_window_limit[0]), max(1080, saved_window_limit[1]))
            renpy.set_physical_size((1920, 1080))
    after testcase:
        python:
            _preferences.afm_enable, _preferences.fullscreen, _preferences.physical_size = saved_preferences
            renpy.display.draw.info["max_window_size"] = saved_window_limit
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase phone.interaction:
    run Start("rm_phone_test_scene")
    run Function(renpy.set_physical_size, (1920, 1080))
    pause .3
    python:
        print("PHONE SIZE", renpy.get_physical_size())
    assert eval renpy.get_physical_size() == (1920, 1080)
    assert eval phone_history("ami") == []
    assert eval phone_preview("ami") == "暂无消息"
    run Show("phone_panel")
    pause .4
    screenshot "E:/ChatGPT/Temp/rememorial-phone/home.png"
    click id "phone_app_messages"
    pause .3
    click id "phone_contact_ami"
    assert not id "phone_send"
    assert eval phone_history("ami") == []
    click id "phone_close"
    advance until screen "phone_panel"
    assert screen "phone_panel"
    assert eval phone_unread("ami") == 1
    pause .3
    screenshot "E:/ChatGPT/Temp/rememorial-phone/list.png"
    click id "phone_contact_ami"
    pause .3
    assert eval phone_unread("ami") == 0
    click id "phone_next"
    pause .3
    assert eval len(phone_history("ami")) == 2
    run Function(renpy.save, "phone-count-two")
    run SetVariable("phone_story_ami_count", 4)
    run Function(renpy.load, "phone-count-two")
    pause .3
    assert eval phone_story_ami_count == 2 and not phone_story_ami_sent
    click id "phone_close"
    assert screen "phone_story_resume"
    assert not eval phone_story_ami_sent
    click id "phone_resume"
    click id "phone_contact_ami"
    assert eval renpy.get_screen_variable("phone_new_index", "phone_panel") is None
    click id "phone_next"
    pause .2
    click id "phone_next"
    pause .3
    assert eval len(phone_history("ami")) == 4
    assert not id "phone_send"
    screenshot "E:/ChatGPT/Temp/rememorial-phone/chat.png"
    click id "phone_reply_prompt"
    assert screen "phone_panel_background" layer "master"
    assert "独白测试。"
    advance until screen "phone_panel"
    assert id "phone_send"
    pause .3
    screenshot "E:/ChatGPT/Temp/rememorial-phone/reply.png"
    run Function(renpy.save, "phone-ready")
    run Function(phone_send_story_ami_reply)
    run Function(renpy.load, "phone-ready")
    pause .3
    assert eval phone_story_ami_reply_ready and not phone_story_ami_sent
    assert id "phone_send"
    click id "phone_close"
    assert screen "phone_story_resume"
    click id "phone_resume"
    assert id "phone_send"
    click id "phone_send"
    pause .3
    assert eval phone_story_ami_sent and len(phone_history("ami")) == 5
    assert eval phone_preview("ami") == phone_story_ami_reply_text
    assert not id "phone_send"
    run Function(renpy.save, "phone-sent")
    run SetVariable("phone_story_ami_sent", False)
    run Function(renpy.load, "phone-sent")
    pause .3
    assert eval phone_story_ami_sent and len(phone_history("ami")) == 5
    screenshot "E:/ChatGPT/Temp/rememorial-phone/sent.png"
    click id "phone_done"
    assert "回复完成。"
    run Show("phone_panel", start_app="messages", start_chat="ami")
    pause .3
    assert eval len(phone_history("ami")) == 5
    assert eval renpy.get_screen_variable("phone_new_index", "phone_panel") is None
    click id "phone_back"
    click id "phone_back"
    click id "phone_app_calculator"
    click id "phone_calc_7"
    click id "phone_calc_*"
    click id "phone_calc_8"
    click id "phone_calc_="
    assert eval phone_calc_result == "56"
    pause .3
    screenshot "E:/ChatGPT/Temp/rememorial-phone/calculator.png"
    run SetVariable("current_time_minutes", 14 * 60 + 30)
    assert eval phone_clock_text() == "14:30"
    click id "phone_close"

testcase phone.scrolling:
    run Start("rm_phone_test_scene")
    run Function(renpy.set_physical_size, (1920, 1080))
    run Function(phone_begin_story_ami)
    # Long legacy history exercises an actual overflowing viewport.
    python:
        phone_chat_history["ami"] = list(phone_chats["ami"][:4]) * 4
    run Show("phone_panel", start_app="messages", start_chat="ami", story_mode=True)
    pause .4
    assert eval renpy.get_screen_variable("phone_scroll", "phone_panel").range > 1000
    scroll amount -12 id "phone_chat_viewport" pos (.5, .5)
    pause .3
    python:
        scroll_before = renpy.get_screen_variable("phone_scroll", "phone_panel").value
    assert eval scroll_before < renpy.get_screen_variable("phone_scroll", "phone_panel").range - 100
    click id "phone_next"
    pause .4
    assert eval abs(renpy.get_screen_variable("phone_scroll", "phone_panel").value - scroll_before) < 1
    assert eval phone_unread("ami") == 1
    scroll amount 100 id "phone_chat_viewport" pos (.5, .5)
    pause .3
    assert eval phone_unread("ami") == 0
    click id "phone_next"
    pause .4
    assert eval renpy.get_screen_variable("phone_scroll", "phone_panel").value >= renpy.get_screen_variable("phone_scroll", "phone_panel").range - 8
    screenshot "E:/ChatGPT/Temp/rememorial-phone/scroll.png"
    run Hide("phone_panel")

testcase phone.rollback:
    run Start("rm_phone_test_scene")
    advance until screen "phone_panel"
    click id "phone_contact_ami"
    click id "phone_next"
    pause .2
    click id "phone_next"
    pause .2
    click id "phone_next"
    click id "phone_reply_prompt"
    advance until screen "phone_panel"
    assert eval phone_story_ami_reply_ready
    run Rollback(force=True)
    pause .3
    assert "独白测试。"
    assert eval not phone_story_ami_reply_ready and not phone_story_ami_sent
    advance until screen "phone_panel"
    click id "phone_send"
    click id "phone_done"
    assert "回复完成。"
    run Rollback(force=True)
    pause .3
    assert screen "phone_panel"
    assert eval phone_story_ami_reply_ready and not phone_story_ami_sent
    assert eval len(phone_history("ami")) == 4
    click id "phone_send"
    click id "phone_done"
    assert eval len(phone_history("ami")) == 5

testcase phone.legacy_progress:
    run Start("rm_phone_test_scene")
    python:
        phone_story_ami_count = 2
        phone_story_ami_active = False
        phone_read_counts = {}
    assert eval len(phone_history("ami")) == 2 and phone_unread("ami") == 0
    assert eval phone_preview("ami") == phone_chats["ami"][1][1]
    run Show("phone_panel", start_app="messages", start_chat="ami", story_mode=True)
    assert id "phone_next"
    assert eval phone_story_ami_active and not phone_can_reply(False)
    run Hide("phone_panel")
    python:
        phone_story_ami_count = 4
        phone_story_ami_reply_ready = True
        phone_story_ami_active = False
        phone_draft_message = phone_story_ami_reply_text
    run Show("phone_panel", start_app="messages", start_chat="ami", story_mode=True)
    assert id "phone_send"
    assert eval len(phone_history("ami")) == 4
    run Hide("phone_panel")
    python:
        phone_story_ami_count = 0
        phone_story_ami_sent = True
        phone_story_ami_reply_ready = False
    assert eval len(phone_history("ami")) == 5
    assert eval phone_preview("ami") == phone_story_ami_reply_text
    assert eval phone_date_text() == "8月18日  周五"
