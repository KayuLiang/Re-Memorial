# Narrow native phone, in the project's 2560 x 1440 logical coordinates.
# 552 x 1226 becomes 414 x 920 in a 1920 x 1080 window.

init python:
    def phone_round(color="white"):
        return Frame("gui/phone_modern/" + color + ".png", 22, 22)

    def phone_chat_event(adjustment, send=False):
        # Motion belongs to this visible interaction, never to saved chat records.
        follow = adjustment.value if adjustment.value >= adjustment.range - 8 else None
        before = len(phone_history("ami"))
        if send:
            phone_send_story_ami_reply()
        else:
            phone_next_story_ami(store.phone_story_ami_count)
        if len(phone_history("ami")) > before:
            renpy.set_screen_variable("phone_new_index", before, "phone_panel")
            renpy.set_screen_variable("phone_follow", follow, "phone_panel")

    def phone_scroll_latest(adjustment, previous_value):
        # Read the new range after layout; preserve any intervening manual scroll.
        if abs(adjustment.value - previous_value) < 1:
            adjustment.change(adjustment.range)

transform phone_open:
    alpha 0.0
    yoffset 38
    easeout .28 alpha 1.0 yoffset 0

transform phone_page_in(direction=1):
    alpha .35
    xoffset (direction * 32)
    easeout .20 alpha 1.0 xoffset 0

transform phone_message_in:
    alpha 0.0
    yoffset 9
    easeout .16 alpha 1.0 yoffset 0

transform phone_still:
    alpha 1.0
    yoffset 0

screen phone_panel(start_app="home", start_chat=None, story_mode=False):
    modal True
    zorder 210
    default phone_app = start_app
    default chat_contact = start_chat
    default phone_direction = 1
    default phone_scroll = ui.adjustment()
    default phone_new_index = None
    default phone_follow = None
    if story_mode:
        on "show" action [Function(renpy.retain_after_load), Function(phone_begin_story_ami)]
    else:
        on "show" action Function(renpy.retain_after_load)

    $ close_action = Return("closed") if story_mode else Hide("phone_panel")
    $ home_action = [SetScreenVariable("phone_direction", -1), SetScreenVariable("phone_app", "home"), SetScreenVariable("chat_contact", None), SetScreenVariable("phone_new_index", None)]
    $ back_action = [SetScreenVariable("phone_direction", -1), SetScreenVariable("chat_contact", None), SetScreenVariable("phone_new_index", None)] if chat_contact else home_action
    key "game_menu" action (back_action if phone_app != "home" else close_action)
    use modal_dim_background
    fixed:
        at phone_open
        use phone_device(phone_app, chat_contact, story_mode, False, phone_direction, phone_scroll, phone_new_index, phone_follow)
    textbutton "收起手机":
        id "phone_close"
        style "phone_close_button"
        xpos 1588
        ypos 137
        action close_action

screen phone_panel_background(start_chat=None, story_mode=False):
    zorder 1
    # Read-only: no timers, input, marks, or repeated message animations.
    use phone_device("messages", start_chat, story_mode, True)

screen phone_device(app, contact, story_mode, background, phone_direction=1, phone_scroll=None, phone_new_index=None, phone_follow=None):
    fixed:
        pos (1004, 107)
        xysize (552, 1226)
        add "gui/phone_modern/device.svg"
        text phone_clock_text() style "phone_status_text" pos (51, 43)
        # No invented signal strength or battery percentage.
        text "RE / M" style "phone_status_text" size 17 color "#8993a2" pos (405, 47)
        fixed:
            pos (34, 106)
            xysize (484, 1050)
            if background:
                if contact:
                    use phone_chat(contact, story_mode, True)
                else:
                    use phone_messages(story_mode, True)
            else:
                for page_key index page_key in [(app, contact)]:
                    fixed:
                        at phone_page_in(phone_direction)
                        if app == "home":
                            use phone_home
                        elif app == "messages":
                            if contact:
                                use phone_chat(contact, story_mode, False, phone_scroll, phone_new_index, phone_follow)
                            else:
                                use phone_messages(story_mode)
                        elif app == "calculator":
                            use phone_calculator
                        else:
                            use phone_placeholder(dict((a[0], a[1]) for a in phone_apps).get(app, "应用"))
        button:
            id "phone_home_gesture"
            pos (186, 1168)
            xysize (180, 40)
            background None
            sensitive not background
            action [SetScreenVariable("phone_direction", -1), SetScreenVariable("phone_app", "home"), SetScreenVariable("chat_contact", None), SetScreenVariable("phone_new_index", None)]
            add Solid("#344050", xsize=152, ysize=5) align (.5, .5)

screen phone_header(title, background=False):
    fixed:
        xysize (484, 86)
        button:
            id "phone_back"
            xysize (62, 72)
            background None
            sensitive not background
            action ([SetScreenVariable("phone_direction", -1), SetScreenVariable("chat_contact", None), SetScreenVariable("phone_new_index", None)] if title in [c[1] for c in phone_contacts] else [SetScreenVariable("phone_direction", -1), SetScreenVariable("phone_app", "home")])
            add "gui/phone_modern/back.svg" xysize (36, 36) align (.5, .5)
        if title != "信息":
            text title style "phone_title" xalign .5 ypos 18
        add Solid("#e0e5ec", xsize=452, ysize=1) pos (16, 83)

screen phone_avatar(contact_id, edge=72):
    fixed:
        xysize (edge, edge)
        add phone_round("avatar") xysize (edge, edge)
        if contact_id == "ami":
            # Reuse the existing full-size art, with a head-and-shoulders crop.
            add Transform(Crop((890, 540, 770, 770), "images/sprites/ami/spr_ami_casual_default.png"), xysize=(edge, edge))
        else:
            text dict((c[0], c[1][0]) for c in phone_contacts).get(contact_id, "我") style "phone_text" size (edge // 2) align (.5, .5) color "#597080"

screen phone_home():
    text phone_date_text() style "phone_muted" xalign .5 ypos 68
    text phone_clock_text() style "phone_text" size 90 xalign .5 ypos 110 color "#20364e"
    text "Re: Memorial" style "phone_muted" size 20 xalign .5 ypos 228
    grid 3 3:
        xpos 17
        ypos 352
        spacing 26
        for app_id, app_name, app_icon, app_color in phone_apps:
            button:
                id ("phone_app_" + app_id)
                xysize (132, 142)
                padding (0, 0)
                background None
                action [SetScreenVariable("phone_direction", 1), SetScreenVariable("phone_app", app_id)]
                vbox:
                    xalign .5
                    spacing 12
                    frame:
                        xalign .5
                        xysize (90, 90)
                        padding (0, 0)
                        background phone_round("blue" if app_id == "messages" else "dark")
                        add ("gui/phone_modern/" + app_id + ".svg") xysize (54, 54) align (.5, .5)
                        if app_id == "messages" and phone_unread("ami"):
                            frame:
                                background phone_round("blue")
                                xysize (30, 30)
                                padding (0, 0)
                                align (1.12, -.12)
                                text str(phone_unread("ami")) style "phone_badge"
                    text app_name style "phone_text" size 23 xalign .5

screen phone_messages(story_mode=False, background=False):
    use phone_header("信息", background)
    text "信息" style "phone_title" size 48 pos (20, 115)
    $ unread = sum(phone_unread(c[0]) for c in phone_contacts)
    text ("%d 条未读消息" % unread if unread else "所有消息已读") style "phone_muted" pos (23, 186)
    vbox:
        pos (12, 260)
        spacing 2
        for contact_id, contact_name, unused_preview in phone_contacts:
            button:
                id ("phone_contact_" + contact_id)
                xysize (460, 135)
                padding (14, 18)
                background None
                hover_background phone_round("white")
                sensitive not background
                action [SetScreenVariable("phone_direction", 1), SetScreenVariable("phone_scroll", ui.adjustment()), SetScreenVariable("phone_new_index", None), SetScreenVariable("phone_follow", None), SetScreenVariable("chat_contact", contact_id)]
                hbox:
                    spacing 18
                    use phone_avatar(contact_id, 74)
                    vbox:
                        xsize 290
                        spacing 10
                        text contact_name style "phone_text" size 29
                        $ preview = phone_preview(contact_id)
                        text (preview[:11] + "…" if len(preview) > 12 else preview) style "phone_muted" xmaximum 290 substitute False
                    if phone_unread(contact_id):
                        frame:
                            background phone_round("blue")
                            padding (0, 0)
                            xysize (28, 28)
                            text str(phone_unread(contact_id)) style "phone_badge"
            add Solid("#e0e5ec", xsize=350, ysize=1) xalign 1.0
    text "消息会随故事逐步出现" style "phone_muted" size 21 xalign .5 ypos 988

screen phone_chat(contact_id, story_mode=False, background=False, phone_scroll=None, phone_new_index=None, phone_follow=None):
    $ contact_name = dict((c[0], c[1]) for c in phone_contacts).get(contact_id, "")
    $ chat_lines = phone_history(contact_id)
    $ can_reply = contact_id == "ami" and phone_can_reply(story_mode)
    use phone_header(contact_name, background)
    viewport:
        id "phone_chat_viewport"
        pos (8, 104)
        xysize (468, 724 if can_reply else 782)
        mousewheel not background
        draggable not background
        arrowkeys not background
        pagekeys not background
        yinitial 1.0
        if not background:
            yadjustment phone_scroll
        vbox:
            xsize 468
            spacing 22
            null height 8
            if not chat_lines:
                text "暂无聊天记录" style "phone_muted" xalign .5
            for i, line index i in enumerate(chat_lines):
                $ who, msg = line
                hbox:
                    xsize 468
                    spacing 12
                    at (phone_message_in if not background and i == phone_new_index else phone_still)
                    if who != "我":
                        use phone_avatar(contact_id, 48)
                    else:
                        null width 62
                    frame:
                        background phone_round("blue" if who == "我" else "white")
                        padding (19, 16)
                        xmaximum 384
                        text msg style "phone_bubble_text" color ("#ffffff" if who == "我" else "#253244") xmaximum 342 substitute False
            null height 16
    if not background:
        timer .15 repeat True action Function(phone_mark_read, contact_id, phone_scroll, _update_screens=False)
        if phone_follow is not None:
            timer .02 action [Function(phone_scroll_latest, phone_scroll, phone_follow), SetScreenVariable("phone_follow", None)]
        if phone_new_index is not None:
            timer .18 action SetScreenVariable("phone_new_index", None)
        if story_mode and contact_id == "ami" and phone_story_ami_active:
            if phone_story_ami_count < 4:
                textbutton "阅读下一条消息":
                    id "phone_next"
                    style "phone_primary_button"
                    pos (20, 916)
                    xysize (444, 70)
                    action Function(phone_chat_event, phone_scroll)
            elif not phone_story_ami_reply_ready and not phone_story_ami_sent:
                # Give the fourth line its own reading beat; no auto-dismiss timer.
                textbutton "回复阿弥":
                    id "phone_reply_prompt"
                    style "phone_primary_button"
                    pos (20, 916)
                    xysize (444, 70)
                    action Return("reply_prompt")
        if can_reply:
            frame:
                pos (10, 850)
                xysize (464, 188)
                padding (16, 15)
                background phone_round("white")
                vbox:
                    spacing 12
                    text phone_draft_message style "phone_text" size 24 xmaximum 426 substitute False
                    textbutton "发送":
                        id "phone_send"
                        style "phone_primary_button"
                        xalign 1.0
                        xysize (104, 52)
                        action Function(phone_chat_event, phone_scroll, True)
        elif contact_id == "ami" and phone_story_ami_sent:
            text "已发送" style "phone_muted" xalign .5 ypos 914
            if story_mode:
                textbutton "完成":
                    id "phone_done"
                    style "phone_primary_button"
                    pos (20, 966)
                    xysize (444, 66)
                    action Return("sent")
        elif not (story_mode and contact_id == "ami"):
            frame:
                pos (12, 944)
                xysize (460, 76)
                padding (20, 20)
                background phone_round("soft")
                text "暂无可发送的回复" style "phone_muted" size 23

screen phone_calculator():
    use phone_header("计算器")
    frame:
        pos (12, 135)
        xysize (460, 232)
        padding (24, 24)
        background phone_round("dark")
        vbox:
            spacing 20
            viewport:
                xysize (412, 60)
                mousewheel "horizontal"
                xinitial 1.0
                text (phone_calc_expr or "0") style "phone_text" size 30 color "#b9c6d9" layout "nobreak"
            viewport:
                xysize (412, 80)
                mousewheel "horizontal"
                xinitial 1.0
                text phone_calc_result style "phone_text" size 48 color "#ffffff" layout "nobreak"
    grid 4 5:
        pos (12, 414)
        spacing 12
        for key in ["7", "8", "9", "/", "4", "5", "6", "*", "1", "2", "3", "-", "0", ".", "=", "+", "C", "(", ")", "<"]:
            textbutton key:
                style "phone_calc_button"
                id ("phone_calc_" + key)
                if key == "=":
                    action Function(phone_calculate)
                elif key == "C":
                    action [SetVariable("phone_calc_expr", ""), SetVariable("phone_calc_result", "0")]
                elif key == "<":
                    action SetVariable("phone_calc_expr", phone_calc_expr[:-1])
                else:
                    action SetVariable("phone_calc_expr", phone_calc_expr + key)

screen phone_placeholder(title):
    use phone_header(title)
    text title style "phone_title" size 42 xalign .5 ypos 340
    text "此应用尚未开放" style "phone_muted" xalign .5 ypos 411

screen phone_story_resume():
    zorder 211
    textbutton "继续回复消息":
        id "phone_resume"
        style "phone_primary_button"
        align (.88, .28)
        padding (30, 18)
        action Return()

style phone_text is text:
    font "SourceHanSansLite.ttf"
    size 27
    color "#253244"
    line_spacing 5
    outlines []

style phone_muted is phone_text:
    size 23
    color "#758193"

style phone_status_text is phone_text:
    size 23
    bold True

style phone_title is phone_text:
    size 30
    bold True

style phone_bubble_text is phone_text:
    size 27
    line_spacing 8

style phone_badge is phone_text:
    size 19
    color "#ffffff"
    align (.5, .5)

style phone_primary_button is button:
    background phone_round("blue")
    hover_background phone_round("dark")
    padding (18, 10)

style phone_primary_button_text is phone_text:
    size 25
    color "#ffffff"
    align (.5, .5)

style phone_close_button is phone_primary_button:
    background phone_round("dark")
    padding (24, 15)

style phone_close_button_text is phone_primary_button_text

style phone_calc_button is phone_primary_button:
    xysize (106, 100)
    background phone_round("white")
    hover_background phone_round("soft")

style phone_calc_button_text is phone_text:
    size 34
    align (.5, .5)
