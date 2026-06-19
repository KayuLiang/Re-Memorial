# Phone screens for Re: Memorial.

init python:
    config.overlay_screens.append("phone_button")

    def phone_calculate():
        expr = store.phone_calc_expr
        if not expr:
            store.phone_calc_result = "0"
            return

        allowed = set("0123456789+-*/(). ")
        if any(ch not in allowed for ch in expr):
            store.phone_calc_result = "\u8f93\u5165\u9519\u8bef"
            return

        try:
            value = eval(expr, {"__builtins__": {}}, {})
            store.phone_calc_result = str(value)
        except Exception:
            store.phone_calc_result = "\u8ba1\u7b97\u9519\u8bef"

    def phone_send_message(contact_id):
        msg = store.phone_draft_message.strip()
        if not msg:
            return
        store.phone_chat_history.setdefault(contact_id, []).append(("\u6211", msg))
        store.phone_draft_message = ""

    def phone_send_story_ami_reply():
        store.phone_story_ami_sent = True
        store.phone_story_ami_reply_ready = False
        store.phone_draft_message = ""

    def phone_story_open_ami_chat():
        if store.phone_story_ami_count < 1:
            store.phone_story_ami_count = 1

    def phone_prepare_story_ami_reply():
        store.phone_draft_message = store.phone_story_ami_reply_text
        store.phone_story_ami_reply_ready = True

default phone_calc_expr = ""
default phone_calc_result = "0"
default phone_draft_message = ""
default phone_chat_history = {}
default phone_story_ami_count = 0
default phone_story_ami_reply_ready = False
default phone_story_ami_sent = False

define phone_story_ami_reply_text = "\u8c22\u8c22\u4f60\u7ed9\u6211\u9001\u7684\u8863\u670d\uff0c\u5f88\u5408\u8eab\u3002\u6211\u9a6c\u4e0a\u51fa\u6765\u4e86\u3002"

define phone_apps = [
    ("phone", "\u7535\u8bdd", "\u260e", "#34C759"),
    ("messages", "\u4fe1\u606f", "\u25cf", "#32D74B"),
    ("weather", "\u5929\u6c14", "\u2601", "#5AC8FA"),
    ("calendar", "\u65e5\u5386", "16", "#FF3B30"),
    ("notes", "\u7b14\u8bb0", "\u270e", "#FFD60A"),
    ("recorder", "\u5f55\u97f3\u673a", "\u25cf", "#FF453A"),
    ("clock", "\u65f6\u949f", "\u25f7", "#8E8E93"),
    ("album", "\u76f8\u518c", "\u25a7", "#AF52DE"),
    ("calculator", "\u8ba1\u7b97\u5668", "+", "#1C1C1E"),
]

define phone_contacts = [
    ("ami", "\u963f\u5f25", "\u51fa\u9662\u5feb\u4e50\uff01"),
    ("doctor", "\u533b\u751f", "\u590d\u8bca\u4fe1\u606f\u5360\u4f4d"),
    ("mom", "\u5988\u5988", "\u5185\u5bb9\u5360\u4f4d\uff0c\u5f85\u8865\u5145"),
    ("hospital", "\u533b\u9662\u516c\u4f17\u53f7", "\u533b\u7597\u62a5\u544a\u5360\u4f4d"),
]

define phone_chats = {
    "ami": [
        ("\u963f\u5f25", "\u5f17\u6d1b\uff0c\u6211\u628a\u4f60\u4e4b\u524d\u5f04\u810f\u7684\u8863\u670d\u90fd\u62ff\u56de\u53bb\u6d17\u4e86\u3002"),
        ("\u963f\u5f25", "\u65b0\u7684\u6362\u6d17\u8863\u670d\u4e5f\u8ba9\u62a4\u58eb\u5e2e\u5fd9\u5e26\u8fdb\u53bb\u4e86\uff0c\u4f60\u8bb0\u5f97\u627e\u5979\u62ff\u4e00\u4e0b\u3002"),
        ("\u963f\u5f25", "\u6536\u62fe\u597d\u4e1c\u897f\u5c31\u51fa\u6765\u627e\u6211\u5427\uff0c\u6211\u5728\u4e2d\u5fc3\u7684\u5927\u5385\u7b49\u4f60\uff01"),
        ("\u963f\u5f25", "\u4e24\u4e2a\u6708\u6ca1\u89c1\u4e86\uff0c\u6211\u5bf9\u4f60\u53ef\u662f\u53c8\u62c5\u5fc3\u53c8\u60f3\u7684\uff0c\u8fd8\u4e0d\u5feb\u70b9\u51fa\u6765\u8ba9\u6211\u62b1\u4e00\u4e0b\u3002"),
        ("\u6211", "\u8c22\u8c22\u4f60\u7ed9\u6211\u9001\u7684\u8863\u670d\uff0c\u5f88\u5408\u8eab\u3002\u6211\u9a6c\u4e0a\u51fa\u6765\u4e86\u3002"),
    ],
    "doctor": [("\u533b\u751f", "\u5185\u5bb9\u5360\u4f4d\uff1a\u590d\u8bca\u65f6\u95f4\u548c\u533b\u7597\u62a5\u544a\u5c1a\u672a\u5b9e\u88c5\u3002")],
    "mom": [("\u5988\u5988", "\u5185\u5bb9\u5360\u4f4d\uff1a\u5bb6\u5ead\u76f8\u5173\u5bf9\u8bdd\u5c1a\u672a\u5b9e\u88c5\u3002")],
    "hospital": [("\u533b\u9662\u516c\u4f17\u53f7", "\u5185\u5bb9\u5360\u4f4d\uff1a\u533b\u9662\u901a\u77e5\u5c1a\u672a\u5b9e\u88c5\u3002")],
}

screen phone_button():
    zorder 90

    if not main_menu and not opening_active and "\u624b\u673a" in inventory:
        textbutton "\u624b\u673a":
            style "phone_side_button"
            action Show("phone_panel")

screen phone_panel(start_app="home", start_chat=None, story_mode=False):
    modal True
    zorder 210
    default phone_app = start_app
    default chat_contact = start_chat

    key "game_menu" action If(chat_contact is not None, SetScreenVariable("chat_contact", None), If(phone_app != "home", SetScreenVariable("phone_app", "home"), If(story_mode, Return(), Hide("phone_panel"))))

    frame:
        style "phone_overlay_frame"

        textbutton "\u2715":
            style "phone_close_button"
            action If(story_mode, Return(), Hide("phone_panel"))

        frame:
            style "phone_device_frame"

            vbox:
                spacing 12
                xfill True
                yfill True

                hbox:
                    xfill True
                    text "13:30" style "phone_status_text"
                    text "\u25cf\u25cf\u25cf  5G     82%" style "phone_status_text" xalign 1.0

                if phone_app == "home":
                    use phone_home
                elif phone_app == "messages":
                    if chat_contact:
                        use phone_chat(chat_contact, story_mode)
                    else:
                        use phone_messages(story_mode)
                elif phone_app == "phone":
                    use phone_placeholder("\u7535\u8bdd", "\u8054\u7cfb\u4eba\u548c\u901a\u8bdd\u8bb0\u5f55\u5360\u4f4d\u3002")
                elif phone_app == "weather":
                    use phone_placeholder("\u5929\u6c14", "\u5929\u6c14\u6570\u636e\u5360\u4f4d\uff1a\u5e02\u7acb\u7cbe\u795e\u536b\u751f\u4e2d\u5fc3\uff0c\u6674\u8f6c\u591a\u4e91\u3002")
                elif phone_app == "calendar":
                    use phone_placeholder("\u65e5\u5386", "\u65e5\u7a0b\u5360\u4f4d\uff1a\u4e24\u5468\u540e\u590d\u8bca\u3002")
                elif phone_app == "notes":
                    use phone_placeholder("\u7b14\u8bb0", "\u8bb0\u5fc6\u788e\u7247\u548c\u7ebf\u7d22\u5360\u4f4d\u3002")
                elif phone_app == "recorder":
                    use phone_placeholder("\u5f55\u97f3\u673a", "\u5f55\u97f3\u5217\u8868\u5360\u4f4d\u3002")
                elif phone_app == "clock":
                    use phone_placeholder("\u65f6\u949f", "\u95f9\u949f\u548c\u65f6\u95f4\u5360\u4f4d\u3002")
                elif phone_app == "album":
                    use phone_album
                elif phone_app == "calculator":
                    use phone_calculator

                textbutton "\u25ac":
                    xalign 0.5
                    action [SetScreenVariable("phone_app", "home"), SetScreenVariable("chat_contact", None)]


screen phone_panel_background(start_chat=None, story_mode=False):
    modal False
    zorder 1

    frame:
        style "phone_overlay_frame"

        frame:
            style "phone_device_frame"

            vbox:
                spacing 12
                xfill True
                yfill True

                hbox:
                    xfill True
                    text "13:30" style "phone_status_text"
                    text "\u25cf\u25cf\u25cf  5G     82%" style "phone_status_text" xalign 1.0

                if start_chat:
                    use phone_chat(start_chat, story_mode, True)
                else:
                    use phone_messages(story_mode)


screen phone_home():
    vbox:
        spacing 18
        xfill True
        yfill True

        grid 3 3:
            xalign 0.5
            yalign 0.5
            spacing 28

            for app_id, app_name, app_icon, app_color in phone_apps:
                button:
                    style "phone_app_button"
                    action SetScreenVariable("phone_app", app_id)

                    vbox:
                        spacing 6
                        xalign 0.5
                        frame:
                            style "phone_app_icon_frame"
                            background Solid(app_color)
                            text app_icon style "phone_app_icon_text"
                        text app_name style "phone_app_name_text"

screen phone_messages(story_mode=False):
    vbox:
        spacing 12
        hbox:
            spacing 12
            textbutton "\u2b05":
                style "phone_back_button"
                action SetScreenVariable("phone_app", "home")
            text "\u4fe1\u606f" style "phone_app_title_text"

        for contact_id, contact_name, preview in phone_contacts:
            button:
                style "phone_list_button"
                if story_mode and contact_id == "ami":
                    action [Function(phone_story_open_ami_chat), SetScreenVariable("chat_contact", contact_id)]
                else:
                    action SetScreenVariable("chat_contact", contact_id)
                hbox:
                    xfill True
                    vbox:
                        text contact_name style "phone_list_title_text"
                        text preview style "phone_list_preview_text"
                    if story_mode and contact_id == "ami" and phone_story_ami_count == 0 and not phone_story_ami_sent:
                        frame:
                            style "phone_unread_badge"
                            text "1" style "phone_unread_badge_text"

screen phone_chat(contact_id, story_mode=False, background=False):
    $ contact_name = dict((c[0], c[1]) for c in phone_contacts).get(contact_id, "")
    if story_mode and contact_id == "ami":
        $ chat_lines = phone_chats["ami"][:phone_story_ami_count]
        if phone_story_ami_sent:
            $ chat_lines = chat_lines + [phone_chats["ami"][4]]
    else:
        $ chat_lines = phone_chats.get(contact_id, []) + phone_chat_history.get(contact_id, [])

    vbox:
        spacing 12

        hbox:
            spacing 12
            textbutton "\u2b05":
                style "phone_back_button"
                action SetScreenVariable("chat_contact", None)
            text contact_name style "phone_app_title_text"

        viewport:
            ymaximum 620
            mousewheel True
            scrollbars "vertical"
            vbox:
                spacing 10
                for i, (who, msg) in enumerate(chat_lines):
                    hbox:
                        spacing 8
                        xfill True
                        if who == "\u6211":
                            null width 72
                        frame:
                            style ("phone_bubble_self" if who == "\u6211" else "phone_bubble_other")
                            vbox:
                                text who style "phone_bubble_name_text"
                                text msg style "phone_bubble_text"
                        if story_mode and contact_id == "ami" and who != "\u6211" and i == len(chat_lines) - 1 and phone_story_ami_count < 4:
                            textbutton "\u2193":
                                style "phone_next_message_button"
                                action SetVariable("phone_story_ami_count", phone_story_ami_count + 1)

        if story_mode and contact_id == "ami" and phone_story_ami_count >= 4 and not phone_story_ami_reply_ready and not phone_story_ami_sent:
            if not background:
                timer 0.01 action Return("reply_prompt")
            null height 72
        elif story_mode and contact_id == "ami" and phone_story_ami_sent:
            text "\u5df2\u53d1\u9001" style "phone_list_preview_text" xalign 0.5
        else:
            hbox:
                spacing 10
                frame:
                    style "phone_input_frame"
                    input value VariableInputValue("phone_draft_message") length 28 style "phone_input_text"
                textbutton "\u53d1\u9001":
                    style "phone_send_button"
                    if story_mode and contact_id == "ami":
                        action Function(phone_send_story_ami_reply)
                    else:
                        action Function(phone_send_message, contact_id)

screen phone_album():
    vbox:
        spacing 14
        hbox:
            spacing 12
            textbutton "\u2b05":
                style "phone_back_button"
                action SetScreenVariable("phone_app", "home")
            text "\u76f8\u518c" style "phone_app_title_text"
        text "\u89d2\u8272\u7acb\u7ed8\u5360\u4f4d" style "phone_list_preview_text"

        grid 2 2:
            spacing 16
            for name in ["\u5f17\u6d1b", "\u963f\u5f25", "\u5e15\u5c14", "\u795e\u79d8\u7684\u4ed6"]:
                frame:
                    style "phone_album_card"
                    vbox:
                        text name style "phone_list_title_text"
                        text "\u7acb\u7ed8\u5360\u4f4d" style "phone_list_preview_text"

screen phone_calculator():
    vbox:
        spacing 12
        hbox:
            spacing 12
            textbutton "\u2b05":
                style "phone_back_button"
                action SetScreenVariable("phone_app", "home")
            text "\u8ba1\u7b97\u5668" style "phone_app_title_text"
        frame:
            style "phone_calc_display_frame"
            vbox:
                text phone_calc_expr style "phone_calc_expr_text"
                text phone_calc_result style "phone_calc_result_text"

        grid 4 5:
            spacing 8
            for key in ["7", "8", "9", "/", "4", "5", "6", "*", "1", "2", "3", "-", "0", ".", "=", "+", "C", "(", ")", "<"]:
                textbutton key:
                    style "phone_calc_button"
                    if key == "=":
                        action Function(phone_calculate)
                    elif key == "C":
                        action [SetVariable("phone_calc_expr", ""), SetVariable("phone_calc_result", "0")]
                    elif key == "<":
                        action SetVariable("phone_calc_expr", phone_calc_expr[:-1])
                    else:
                        action SetVariable("phone_calc_expr", phone_calc_expr + key)

screen phone_placeholder(title, body):
    vbox:
        spacing 18
        hbox:
            spacing 12
            textbutton "\u2b05":
                style "phone_back_button"
                action SetScreenVariable("phone_app", "home")
            text title style "phone_app_title_text"
        text body style "phone_placeholder_text"

style phone_side_button is button:
    xalign 1.0
    yalign 0.34
    xsize 110
    ysize 54

style phone_overlay_frame is frame:
    xfill True
    yfill True
    background "#111111cc"
    padding (0, 0)

style phone_device_frame is frame:
    xalign 0.5
    yalign 0.5
    xsize 520
    ysize 900
    background "#f3f4f7"
    padding (28, 22)

style phone_close_button is button:
    xalign 0.86
    yalign 0.05
    xsize 56
    ysize 56
    background "#b00020"

style phone_close_button_text is gui_text:
    size 34
    bold True
    color "#ffffff"
    xalign 0.5
    yalign 0.5

style phone_back_button is button:
    xsize 54
    ysize 48

style phone_back_button_text is gui_text:
    size 34
    bold True
    color "#000000"
    xalign 0.5
    yalign 0.5

style phone_status_text is gui_text:
    size 18
    color "#1c1c1e"

style phone_app_button is button:
    xsize 128
    ysize 132

style phone_app_icon_frame is frame:
    xsize 74
    ysize 74
    padding (0, 0)

style phone_app_icon_text is gui_text:
    size 34
    color "#ffffff"
    xalign 0.5
    yalign 0.5

style phone_app_name_text is gui_text:
    size 18
    color "#1c1c1e"
    xalign 0.5

style phone_app_title_text is gui_text:
    size 34
    bold True
    color "#1c1c1e"

style phone_list_button is button:
    xfill True
    yminimum 78

style phone_list_title_text is gui_text:
    size 24
    bold True
    color "#1c1c1e"

style phone_list_preview_text is gui_text:
    size 18
    color "#6e6e73"

style phone_unread_badge is frame:
    xalign 1.0
    yalign 0.5
    xsize 34
    ysize 34
    background "#ff3b30"
    padding (0, 0)

style phone_unread_badge_text is gui_text:
    size 20
    bold True
    color "#ffffff"
    xalign 0.5
    yalign 0.5

style phone_bubble_other is frame:
    xalign 0.0
    xmaximum 380
    background "#ffffff"
    padding (14, 10)

style phone_bubble_self is frame:
    xalign 1.0
    xmaximum 380
    background "#95ec69"
    padding (14, 10)

style phone_bubble_name_text is gui_text:
    size 14
    color "#6e6e73"

style phone_bubble_text is gui_text:
    size 20
    color "#1c1c1e"

style phone_next_message_button is button:
    xsize 38
    ysize 38
    yalign 0.5
    background "#000000"

style phone_next_message_button_text is gui_text:
    size 22
    bold True
    color "#ffffff"
    xalign 0.5
    yalign 0.5

style phone_input_frame is frame:
    xsize 370
    ysize 56
    background "#ffffff"
    padding (12, 8)

style phone_input_text is gui_text:
    size 20
    color "#1c1c1e"

style phone_send_button is button:
    xsize 96
    ysize 56
    background "#07c160"

style phone_send_button_text is gui_text:
    size 20
    bold True
    color "#ffffff"
    xalign 0.5
    yalign 0.5

style phone_album_card is frame:
    xsize 210
    ysize 150
    background "#ffffff"
    padding (16, 16)

style phone_placeholder_text is gui_text:
    size 22
    color "#3a3a3c"

style phone_calc_display_frame is frame:
    xfill True
    ysize 120
    background "#1c1c1e"
    padding (18, 12)

style phone_calc_expr_text is gui_text:
    size 22
    color "#a1a1a6"
    xalign 1.0

style phone_calc_result_text is gui_text:
    size 38
    color "#ffffff"
    xalign 1.0

style phone_calc_button is button:
    xsize 100
    ysize 62
    background "#ffffff"
