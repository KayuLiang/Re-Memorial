# Developer-only interaction coverage; screenshots live in task scratch on E:.
init python:
    def phone_test_shell_y():
        transforms = []
        def collect(displayable):
            if (isinstance(displayable, renpy.display.transform.ATLTransform)
                    and displayable.atl is phone_shell_shift.atl):
                transforms.append(displayable)
        renpy.get_screen("phone_panel").visit_all(collect)
        assert len(transforms) == 1, "Expected one shell transform, no stacked motion"
        mode = renpy.get_screen_variable("phone_mode", "phone_panel")
        assert abs(transforms[0].zoom - PHONE_MODE_SCALE[mode]) < .001
        return renpy.get_screen_variable("phone_entry_y", "phone_panel") + transforms[0].yoffset

# Use text focus for scaled textbuttons: Ren'Py 8.5's id fallback walks render
# offsets without applying zoom matrices. Scroll coordinates target visible content.

label rm_phone_test_scene:
    $ _autosave = False
    $ opening_active = False
    $ story_hud_hidden = False
    $ inventory = ["手机"]
    $ rm_hud_sync_story_time("20XX年8月18日 星期五 下午 13：30")
    scene bg bathroom
    show fro underwear default at fro_underwear_left zorder 10
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
        elif not phone_story_ami_sent and _return != "reply_ready":
            call screen phone_story_resume
        if phone_story_ami_reply_ready:
            call phone_story_reply("ami", phone_story_ami_reply_options, phone_send_story_ami_reply)
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
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_FULL
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_FULL]) < 1
    screenshot "E:/ChatGPT/Temp/rememorial-upper-focus/home.png"
    click id "phone_app_messages"
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    pause .3
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    click id "phone_contact_ami"
    assert not id "phone_send"
    assert eval phone_history("ami") == []
    click id "phone_close"
    advance until screen "phone_panel"
    assert screen "phone_panel"
    assert eval phone_unread("ami") == 1
    pause .3
    screenshot "E:/ChatGPT/Temp/rememorial-upper-focus/list.png"
    click id "phone_contact_ami"
    pause .3
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    assert eval phone_unread("ami") == 0
    click "阅读下一条消息"
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
    click "阅读下一条消息"
    pause .2
    click "阅读下一条消息"
    pause .3
    assert eval len(phone_history("ami")) == 4
    assert not id "phone_send"
    screenshot "E:/ChatGPT/Temp/rememorial-upper-focus/chat.png"
    click "继续"
    assert screen "phone_panel_background" layer "master"
    assert "独白测试。"
    pause .3
    screenshot "E:/ChatGPT/Temp/rememorial-phone-focus/monologue.png"
    advance until screen "story_phone_reply_overlay"
    assert id "story_phone_reply_option_0"
    assert not id "phone_send"
    pause .3
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    assert eval renpy.get_screen_variable("phone_scroll", "phone_panel").value >= renpy.get_screen_variable("phone_scroll", "phone_panel").range - 8
    screenshot "E:/ChatGPT/Temp/rememorial-upper-focus/reply.png"
    run Function(renpy.save, "phone-ready")
    run Function(phone_send_story_ami_reply)
    run Function(renpy.load, "phone-ready")
    pause .3
    assert eval phone_story_ami_reply_ready and not phone_story_ami_sent
    assert id "story_phone_reply_option_0"
    assert not id "phone_send"
    # Reply choices cannot exit the story; the phone remains at CONTENT.
    keysym "K_ESCAPE"
    assert screen "story_phone_reply_overlay"
    click pos (1770, 100)
    assert screen "story_phone_reply_overlay"
    assert id "story_phone_reply_option_0"
    assert not id "phone_send"
    click "谢谢你给我送的衣服，很合身。我马上出来了。"
    pause .05
    assert eval not phone_story_ami_sent and len(phone_history("ami")) == 4
    assert eval phone_reply_sending
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    # Repeated clicks at the choice position while fading cannot send twice.
    click pos (1280, 720)
    pause .28
    assert not screen "story_phone_reply_overlay"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    assert eval renpy.get_screen_variable("phone_scroll", "phone_panel").value >= renpy.get_screen_variable("phone_scroll", "phone_panel").range - 8
    assert eval phone_story_ami_sent and len(phone_history("ami")) == 5
    assert eval phone_preview("ami") == phone_story_ami_reply_text
    assert not id "phone_send"
    assert eval phone_story_ami_sent and len(phone_history("ami")) == 5
    screenshot "E:/ChatGPT/Temp/rememorial-upper-focus/sent.png"
    pause .5
    assert "回复完成。"
    run Function(renpy.save, "phone-sent")
    run SetVariable("phone_story_ami_sent", False)
    run Function(renpy.load, "phone-sent")
    assert eval phone_story_ami_sent and len(phone_history("ami")) == 5
    run Show("phone_panel", start_app="messages", start_chat="ami")
    pause .3
    assert eval len(phone_history("ami")) == 5
    assert eval renpy.get_screen_variable("phone_new_index", "phone_panel") is None
    click "返回"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    click "返回"
    click id "phone_app_calculator"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    click "7"
    click "*"
    click "8"
    click "="
    assert eval phone_calc_result == "56"
    pause .3
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    screenshot "E:/ChatGPT/Temp/rememorial-upper-focus/calculator.png"
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
    scroll amount -12 pos (1280, 960)
    pause .3
    python:
        scroll_before = renpy.get_screen_variable("phone_scroll", "phone_panel").value
    assert eval scroll_before < renpy.get_screen_variable("phone_scroll", "phone_panel").range - 100
    click "阅读下一条消息"
    pause .4
    assert eval abs(renpy.get_screen_variable("phone_scroll", "phone_panel").value - scroll_before) < 1
    assert eval phone_unread("ami") == 1
    scroll amount 100 pos (1280, 960)
    pause .3
    assert eval phone_unread("ami") == 0
    click "阅读下一条消息"
    pause .4
    assert eval renpy.get_screen_variable("phone_scroll", "phone_panel").value >= renpy.get_screen_variable("phone_scroll", "phone_panel").range - 8
    screenshot "E:/ChatGPT/Temp/rememorial-upper-focus/scroll.png"
    run Hide("phone_panel")

testcase phone.rollback:
    run Start("rm_phone_test_scene")
    advance until screen "phone_panel"
    click id "phone_contact_ami"
    click "阅读下一条消息"
    pause .2
    click "阅读下一条消息"
    pause .2
    click "阅读下一条消息"
    click "继续"
    advance until screen "story_phone_reply_overlay"
    assert eval phone_story_ami_reply_ready
    run Rollback(force=True)
    pause .3
    assert "独白测试。"
    assert eval not phone_story_ami_reply_ready and not phone_story_ami_sent
    advance until screen "story_phone_reply_overlay"
    click "谢谢你给我送的衣服，很合身。我马上出来了。"
    pause .8
    assert "回复完成。"
    run Rollback(force=True)
    pause .3
    assert screen "story_phone_reply_overlay"
    assert eval phone_story_ami_reply_ready and not phone_story_ami_sent
    assert eval len(phone_history("ami")) == 4
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    click "谢谢你给我送的衣服，很合身。我马上出来了。"
    pause .8
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
    run Show("phone_panel", start_app="messages", start_chat="ami")
    assert not id "phone_send"
    assert eval len(phone_history("ami")) == 4
    run Hide("phone_panel")
    python:
        phone_story_ami_count = 0
        phone_story_ami_sent = True
        phone_story_ami_reply_ready = False
    assert eval len(phone_history("ami")) == 5
    assert eval phone_preview("ami") == phone_story_ami_reply_text
    assert eval phone_date_text() == "8月18日  周五"

testcase phone.navigation:
    run Start("rm_phone_test_scene")
    run Show("phone_panel")
    pause .3
    click id "phone_app_messages"
    click id "phone_contact_ami"
    pause .04
    click "返回"
    pause .04
    click "返回"
    click id "phone_app_calculator"
    pause .04
    click "返回"
    pause .04
    click id "phone_app_notes"
    pause .04
    click "返回"
    pause .3
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_FULL]) < 1
    click id "phone_app_phone"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    click "返回"
    click id "phone_app_weather"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    click "返回"
    click id "phone_app_calendar"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    click "返回"
    click id "phone_app_clock"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    click "返回"
    click id "phone_app_album"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    click "返回"
    click id "phone_app_recorder"
    assert eval renpy.get_screen_variable("phone_mode", "phone_panel") == PHONE_MODE_CONTENT
    pause .04
    click id "phone_close"
    run Show("phone_panel")
    pause .3
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_FULL]) < 1
    click id "phone_app_notes"
    pause .3
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    click id "phone_close"
    run Show("phone_panel")
    pause .3
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_FULL]) < 1
    click id "phone_close"

label rm_phone_test_multiple:
    $ phone_test_confirm = True
    jump rm_phone_test_options

label rm_phone_test_direct:
    $ phone_test_confirm = False
    jump rm_phone_test_options

label rm_phone_test_options:
    $ _autosave = False
    $ opening_active = False
    $ story_hud_hidden = True
    scene bg bathroom
    $ phone_story_ami_count = 4
    $ phone_begin_story_ami()
    $ phone_prepare_story_ami_reply()
    $ phone_story_ami_reply_options = (("one", "测试回复一"), ("two", "测试回复二"), ("three", "测试回复三"))
    call phone_story_reply("ami", phone_story_ami_reply_options, phone_send_story_ami_reply, confirm=phone_test_confirm)
    "选项测试完成。"
    return

testcase phone.multiple_replies:
    run Start("rm_phone_test_multiple")
    pause .3
    assert screen "story_phone_reply_overlay"
    assert eval len(phone_history("ami")) == 4
    run Function(renpy.save, "phone-choice")
    run Function(renpy.load, "phone-choice")
    assert eval phone_reply_selection is None and not phone_story_ami_sent
    pause .2
    screenshot "E:/ChatGPT/Temp/rememorial-upper-focus/choices.png"
    click "测试回复二"
    pause .05
    assert eval phone_reply_selection == 1 and phone_reply_sending
    assert eval not phone_story_ami_sent
    pause .75
    assert "选项测试完成。"
    assert eval phone_history("ami")[-1] == ("我", "测试回复二")
    assert eval phone_preview("ami") == "测试回复二"
    run Function(phone_send_story_ami_reply, ("two", "测试回复二"))
    assert eval len(phone_history("ami")) == 5

testcase phone.direct_reply:
    run Start("rm_phone_test_direct")
    pause .3
    assert not id "phone_send"
    click "测试回复三"
    pause .05
    assert eval not phone_story_ami_sent
    pause .75
    assert "选项测试完成。"
    assert eval phone_history("ami")[-1] == ("我", "测试回复三")

testcase phone.saving_during_fade:
    run Start("rm_phone_test_multiple")
    pause .3
    click "测试回复一"
    pause .05
    assert eval phone_reply_sending and not phone_story_ami_sent
    run Function(renpy.save, "phone-fading")
    pause .75
    assert eval phone_story_ami_sent
    run Function(renpy.load, "phone-fading")
    assert eval not phone_story_ami_sent and len(phone_history("ami")) == 4
    assert eval phone_reply_selection == 0 and phone_reply_sending
    pause .75
    assert "选项测试完成。"
    assert eval phone_history("ami")[-1] == ("我", "测试回复一")
    assert eval len(phone_history("ami")) == 5

testcase phone.reply_scrolling:
    run Start("rm_phone_test_multiple")
    python:
        phone_chat_history["ami"] = list(phone_chats["ami"][:4]) * 4
    pause .3
    scroll amount -12 pos (1280, 960)
    pause .2
    python:
        reply_scroll_before = renpy.get_screen_variable("phone_scroll", "phone_panel").value
    assert eval reply_scroll_before < renpy.get_screen_variable("phone_scroll", "phone_panel").range - 100
    click "测试回复二"
    pause .32
    assert eval phone_story_ami_sent
    assert eval phone_history("ami")[-1] == ("我", "测试回复二")
    assert eval phone_preview("ami") == "测试回复二"
    assert eval abs(renpy.get_screen_variable("phone_scroll", "phone_panel").value - reply_scroll_before) < 1
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    pause .5
    assert "选项测试完成。"

label rm_phone_test_legacy_ready:
    $ phone_begin_story_ami()
    $ phone_story_ami_count = 4
    $ phone_prepare_story_ami_reply()
    # Simulate resuming the former call-screen statement, already ready to reply.
    call screen phone_panel(start_app="messages", start_chat="ami", story_mode=True)
    $ phone_test_legacy_result = _return
    jump rm_phone_test_exchange

testcase phone.legacy_reply_entry:
    run Start("rm_phone_test_legacy_ready")
    pause .3
    assert eval phone_test_legacy_result == "reply_ready"
    assert screen "story_phone_reply_overlay"
    assert eval len(phone_history("ami")) == 4
    assert eval abs(phone_test_shell_y() - PHONE_MODE_Y[PHONE_MODE_CONTENT]) < 1
    click "谢谢你给我送的衣服，很合身。我马上出来了。"
    pause .8
    assert "回复完成。"
    assert eval len(phone_history("ami")) == 5
