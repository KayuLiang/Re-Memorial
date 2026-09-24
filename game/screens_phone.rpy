# Shared phone shell and app content. Device presets live in phone_layout.rpy.

init python:
    def phone_round(color="white"):
        return Frame("gui/phone_modern/" + color + ".png", 22, 22)

    def phone_chat_event(adjustment):
        # Motion belongs to this visible interaction, never to saved chat records.
        follow = adjustment.value if adjustment.value >= adjustment.range - 8 else None
        before = len(phone_history("ami"))
        phone_next_story_ami(store.phone_story_ami_count)
        if len(phone_history("ami")) > before:
            renpy.set_screen_variable("phone_new_index", before, "phone_panel")
            renpy.set_screen_variable("phone_follow", follow, "phone_panel")

    def phone_scroll_latest(adjustment, previous_value):
        # Read the new range after layout; preserve any intervening manual scroll.
        if abs(adjustment.value - previous_value) < 1:
            adjustment.animate(adjustment.range - adjustment.value, .12, renpy.atl.warpers["easeout"])

transform phone_open:
    alpha 0.0
    easeout .28 alpha 1.0

transform phone_page_in(direction=1):
    alpha .35
    easeout .20 alpha 1.0

transform phone_message_in:
    alpha 0.0
    yoffset 9
    easeout .16 alpha 1.0 yoffset 0

transform phone_still:
    alpha 1.0
    yoffset 0

screen phone_panel(start_app="home", start_chat=None, story_mode=False, reply_session=False):
    modal True
    zorder 210
    default phone_app = start_app
    default chat_contact = start_chat
    default phone_direction = 1
    default phone_scroll = ui.adjustment()
    default phone_new_index = None
    default phone_follow = None
    default phone_mode = phone_page_mode(start_app, start_chat, story_mode)
    # The existing story re-enters here after the read-only monologue background.
    default phone_reply_entry = (story_mode and start_chat == "ami" and phone_can_reply(story_mode))
    default phone_entry_mode = phone_mode
    default phone_entry_y = PHONE_MODE_Y[phone_entry_mode]
    on "show" action Function(phone_panel_enter, start_app, start_chat, story_mode)

    $ close_action = Return("closed") if story_mode else Hide("phone_panel")
    key "game_menu" action (NullAction() if reply_session else (Function(phone_back) if phone_app != "home" else close_action))
    if not reply_session:
        use modal_dim_background
    fixed:
        at (phone_still if phone_reply_entry or reply_session else phone_open)
        use phone_shell(phone_app, chat_contact, story_mode, False, phone_mode, phone_entry_y, phone_entry_mode, phone_direction, phone_scroll, phone_new_index, phone_follow)
    if not reply_session:
        textbutton "收起手机":
            id "phone_close"
            style "phone_close_button"
            xpos (1280 + int(PHONE_WIDTH * PHONE_MODE_SCALE[PHONE_MODE_CONTENT] / 2) + 40)
            ypos 76
            action close_action
    if story_mode and not reply_session:
        # Resume old saves paused in the former in-phone composer through the story.
        if phone_can_reply(story_mode):
            timer .01 action Return("reply_ready")
        elif phone_story_ami_sent:
            timer .40 action Return("sent")

screen phone_panel_background(start_chat=None, story_mode=False):
    zorder 20
    # Same preset as the interactive reader; entirely read-only.
    $ background_mode = phone_page_mode("messages", start_chat, story_mode)
    use phone_shell("messages", start_chat, story_mode, True, background_mode, PHONE_MODE_Y[background_mode], background_mode)

screen phone_shell(app, contact, story_mode, background, mode, entry_y, entry_mode, direction=1, scroll=None, new_index=None, follow=None):
    fixed:
        pos (PHONE_X, entry_y)
        xysize (PHONE_WIDTH, PHONE_HEIGHT)
        fixed:
            at phone_shell_motion(mode, entry_y, entry_mode)
            xysize (PHONE_WIDTH, PHONE_HEIGHT)
            add "gui/phone_modern/device.svg" id "phone_device_art"
            use phone_status_bar
            fixed:
                at phone_page_motion(mode, entry_mode)
                pos (PHONE_PAGE_X, PHONE_PAGE_Y)
                xysize (PHONE_PAGE_WIDTH, PHONE_PAGE_HEIGHT)
                for page_key index page_key in [(app, contact)]:
                    fixed:
                        at (phone_still if background or phone_navigation_locked() else phone_page_in(direction))
                        use phone_page(app, contact, story_mode, background, mode, scroll, new_index, follow)
            button:
                id "phone_home_gesture"
                pos ((PHONE_WIDTH - 180) // 2, PHONE_HEIGHT - 52)
                xysize (180, 38)
                background None
                sensitive not background and not phone_navigation_locked()
                action Function(phone_navigate, "home", direction=-1)
                add Solid("#344050", xsize=152, ysize=5) align (.5, .5)

screen phone_status_bar():
    text phone_clock_text() style "phone_status_text" pos (54, 45)
    text "RE / M" style "phone_status_text" size 19 color "#8993a2" pos (PHONE_WIDTH - 130, 49)

screen phone_page(app, contact, story_mode, background, mode, scroll, new_index, follow):
    if app == "home":
        use phone_home
    elif app == "messages":
        if contact:
            use phone_chat(contact, story_mode, background, mode, scroll, new_index, follow)
        else:
            use phone_messages(story_mode, background)
    elif app == "calculator":
        use phone_calculator
    else:
        use phone_placeholder(dict((a[0], a[1]) for a in phone_apps).get(app, "应用"))

screen phone_header(title, background=False, continue_action=None):
    fixed:
        xysize (PHONE_PAGE_WIDTH, 88)
        button:
            id "phone_back"
            alt "返回"
            xysize (64, 72)
            background None
            sensitive not background and not phone_navigation_locked()
            action Function(phone_back)
            add "gui/phone_modern/back.svg" xysize (38, 38) align (.5, .5) alpha (.3 if phone_navigation_locked() else 1.0)
        if title != "信息":
            text title style "phone_title" xalign .5 ypos 16
        if continue_action is not None and not background:
            textbutton "继续":
                id "phone_reply_prompt"
                style "phone_quiet_button"
                xalign 1.0
                ysize 72
                action continue_action
        add Solid("#e0e5ec", xsize=PHONE_PAGE_WIDTH-24, ysize=1) pos (12, 85)

screen phone_avatar(contact_id, edge=72):
    fixed:
        xysize (edge, edge)
        add phone_round("avatar") xysize (edge, edge)
        if contact_id == "ami":
            # Reuse the existing full-size art, with a head-and-shoulders crop.
            add Transform(Crop((890, 540, 770, 770), "images/sprites/ami/spr_ami_casual_default.png"), xysize=(edge, edge))
        elif contact_id == "fro":
            add Transform(Crop((1060, 210, 750, 750), "images/sprites/fro/spr_fro_casual_default.png"), xysize=(edge, edge))
        else:
            text dict((c[0], c[1][0]) for c in phone_contacts).get(contact_id, "我") style "phone_text" size (edge // 2) align (.5, .5) color "#597080"

screen phone_home():
    text phone_date_text() style "phone_muted" xalign .5 ypos 98
    text phone_clock_text() style "phone_text" size 104 xalign .5 ypos 147 color "#20364e"
    text "Re: Memorial" style "phone_muted" size 22 xalign .5 ypos 280
    grid 3 3:
        xalign .5
        ypos 414
        spacing 30
        for app_id, app_name, app_icon, app_color in phone_apps:
            button:
                id ("phone_app_" + app_id)
                xysize (150, 164)
                padding (0, 0)
                background None
                action Function(phone_navigate, app_id)
                vbox:
                    xalign .5
                    spacing 14
                    frame:
                        xalign .5
                        xysize (104, 104)
                        padding (0, 0)
                        background phone_round("blue" if app_id == "messages" else "dark")
                        add ("gui/phone_modern/" + app_id + ".svg") xysize (60, 60) align (.5, .5)
                        if app_id == "messages" and phone_unread("ami"):
                            frame:
                                background phone_round("blue")
                                xysize (32, 32)
                                padding (0, 0)
                                align (1.12, -.12)
                                text str(phone_unread("ami")) style "phone_badge"
                    text app_name style "phone_text" size 27 xalign .5

screen phone_messages(story_mode=False, background=False):
    use phone_header("信息", background)
    text "信息" style "phone_title" size 52 pos (16, 108)
    $ unread = sum(phone_unread(c[0]) for c in phone_contacts)
    text ("%d 条未读消息" % unread if unread else "所有消息已读") style "phone_muted" pos (18, 182)
    vbox:
        pos (4, 254)
        spacing 4
        for contact_id, contact_name, unused_preview in phone_contacts:
            button:
                id ("phone_contact_" + contact_id)
                xysize (PHONE_PAGE_WIDTH-8, 140)
                padding (14, 22)
                background None
                hover_background phone_round("white")
                sensitive not background
                action Function(phone_navigate, "messages", contact_id)
                hbox:
                    spacing 20
                    use phone_avatar(contact_id, 82)
                    vbox:
                        xsize 364
                        spacing 12
                        text contact_name style "phone_text" size 33
                        $ preview = phone_preview(contact_id)
                        text (preview[:12] + "…" if len(preview) > 13 else preview) style "phone_muted" xmaximum 364 substitute False
                    if phone_unread(contact_id):
                        frame:
                            background phone_round("blue")
                            padding (0, 0)
                            xysize (30, 30)
                            text str(phone_unread(contact_id)) style "phone_badge"
            add Solid("#e0e5ec", xsize=440, ysize=1) xalign 1.0

screen phone_chat(contact_id, story_mode=False, background=False, mode=PHONE_MODE_CONTENT, phone_scroll=None, phone_new_index=None, phone_follow=None):
    $ contact_name = dict((c[0], c[1]) for c in phone_contacts).get(contact_id, "")
    $ chat_lines = phone_history(contact_id)
    $ phase = phone_chat_phase(contact_id, story_mode)
    $ footer_y = phone_visible_page_height(mode) - (70 if phase == "incoming" else 0)
    use phone_header(contact_name, background, Return("reply_prompt") if phase == "reply_prompt" else None)
    viewport:
        id "phone_chat_viewport"
        pos (8, 112)
        xysize (PHONE_PAGE_WIDTH-16, footer_y-134)
        mousewheel not background
        draggable not background
        arrowkeys not background
        pagekeys not background
        yinitial 1.0
        if not background:
            yadjustment phone_scroll
        vbox:
            xsize (PHONE_PAGE_WIDTH-16)
            spacing 0
            null height 8
            if not chat_lines:
                text "暂无聊天记录" style "phone_muted" xalign .5
            for i, line index i in enumerate(chat_lines):
                $ who, msg = line
                $ continuation = i > 0 and chat_lines[i-1][0] == who
                if i:
                    null height (12 if continuation else 24)
                fixed:
                    xsize (PHONE_PAGE_WIDTH-16)
                    yfit True
                    at (phone_message_in if not background and i == phone_new_index else phone_still)
                    if who != "我":
                        hbox:
                            spacing 14
                            if continuation:
                                null width 54
                            else:
                                use phone_avatar(contact_id, 54)
                            use phone_bubble(msg)
                    else:
                        hbox:
                            xalign 1.0
                            spacing 14
                            frame:
                                style "phone_sent_bubble"
                                text msg style "phone_bubble_text" color "#ffffff" substitute False
                            if continuation:
                                null width 54
                            else:
                                use phone_avatar("fro", 54)
            null height 14
    if not background:
        timer .15 repeat True action Function(phone_mark_read, contact_id, phone_scroll, _update_screens=False)
        if phone_follow is not None:
            timer .02 action [Function(phone_scroll_latest, phone_scroll, phone_follow), SetScreenVariable("phone_follow", None)]
        if phone_new_index is not None:
            timer .18 action SetScreenVariable("phone_new_index", None)
        if phase == "incoming":
            textbutton "阅读下一条消息":
                id "phone_next"
                style "phone_quiet_button"
                xalign .5
                ypos footer_y
                ysize 56
                action Function(phone_chat_event, phone_scroll)

screen phone_bubble(msg):
    frame:
        style "phone_received_bubble"
        text msg style "phone_bubble_text" substitute False

screen phone_calculator():
    use phone_header("计算器")
    frame:
        pos (10, 132)
        xysize (PHONE_PAGE_WIDTH-20, 176)
        padding (24, 22)
        background phone_round("dark")
        vbox:
            spacing 8
            viewport:
                xysize (PHONE_PAGE_WIDTH-68, 46)
                mousewheel "horizontal"
                xinitial 1.0
                text (phone_calc_expr or "0") style "phone_text" size 32 color "#b9c6d9" layout "nobreak"
            viewport:
                xysize (PHONE_PAGE_WIDTH-68, 66)
                mousewheel "horizontal"
                xinitial 1.0
                text phone_calc_result style "phone_text" size 54 color "#ffffff" layout "nobreak"
    grid 4 5:
        pos (10, 336)
        spacing 14
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
    text title style "phone_title" size 46 xalign .5 ypos 300
    text "此应用尚未开放" style "phone_muted" xalign .5 ypos 374

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
    size 31
    color "#253244"
    line_spacing 5
    outlines []

style phone_muted is phone_text:
    size 27
    color "#758193"

style phone_status_text is phone_text:
    size 25
    bold True

style phone_title is phone_text:
    size 35
    bold True

style phone_bubble_text is phone_text:
    size 27
    line_spacing 6
    xmaximum 376

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
    xysize (127, 90)
    background phone_round("white")
    hover_background phone_round("soft")

style phone_calc_button_text is phone_text:
    size 34
    align (.5, .5)

style phone_received_bubble is frame:
    background phone_round("white")
    padding (18, 12)
    xmaximum 412

style phone_sent_bubble is phone_received_bubble:
    background phone_round("blue")

style phone_quiet_button is button:
    background None
    hover_background phone_round("soft")
    padding (16, 8)

style phone_quiet_button_text is phone_text:
    size 28
    color "#2868c7"
    align (.5, .5)
