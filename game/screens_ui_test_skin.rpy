default rm_ui_test_skin_active = False

init python:
    if "rm_ui_test_skin_hud" not in config.overlay_screens:
        config.overlay_screens.append("rm_ui_test_skin_hud")

    def rm_ui_test_clamp(value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def rm_ui_test_mood_cursor_offset(value):
        clamped = rm_ui_test_clamp(value, -200, 200)
        return story_hud_mood_cursor_offset(clamped)

    def rm_ui_test_energy_cursor_offset(points, maximum):
        return 219 + story_hud_energy_fill_width(points, maximum)


screen rm_ui_test_close_button(action=Return("__rm_ui_test_exit__")):
    textbutton "X":
        xpos 1774
        ypos 48
        style "rm_ui_test_close_button_style"
        action action


screen rm_ui_test_skin_hud_surface(origin_x=36, origin_y=28):
    $ status_mood = rm_status_mood_value()
    $ status_energy = rm_status_energy_points()
    $ status_energy_max = rm_status_energy_max()

    fixed:
        xysize (1920, 230)

        add "gui/ui_test_skin/clock_face.png":
            xpos origin_x
            ypos origin_y
            xysize (150, 150)

        add Transform(
            "gui/ui_test_skin/clock_hand.png",
            zoom=0.12,
            anchor=(0.5, 0.82),
            pos=(origin_x + 75, origin_y + 78),
            rotate=story_hud_clock_rotation(current_time_minutes),
        )

        add "gui/story_ui/ui_mood_bar_canvas.png" at story_hud_bleed_canvas

        add "gui/story_ui/ui_energy_empty_canvas.png" at story_hud_bleed_canvas

        viewport:
            xpos 219
            ypos 120
            xysize (story_hud_energy_fill_width(status_energy, status_energy_max), 58)
            add Crop((630, 347, 982, 115), "gui/story_ui/ui_energy_full_canvas.png"):
                zoom 0.5

        add "gui/ui_test_skin/mood_cursor.png":
            xpos rm_ui_test_mood_cursor_offset(status_mood)
            ypos 46
            xysize (34, 82)

        add "gui/ui_test_skin/mood_cursor.png":
            xpos rm_ui_test_energy_cursor_offset(status_energy, status_energy_max)
            ypos 102
            xysize (34, 82)

        text "心境 [status_mood]":
            xpos 735
            ypos 74
            size 24
            color "#211b15"

        text "精力 [status_energy]/[status_energy_max]":
            xpos 735
            ypos 118
            size 24
            color "#211b15"


screen rm_ui_test_skin_hud():
    zorder 86

    if not main_menu and not opening_active and rm_test_flow_active and rm_ui_test_skin_active:
        use rm_ui_test_skin_hud_surface(36, 28)


screen rm_ui_test_dialogue_preview():
    modal True
    zorder 240

    use rm_allow_game_menu
    add Solid("#00000099")

    fixed:
        xysize (1920, 1080)

        add Solid("#0b0a09e6"):
            xpos 0
            ypos 810
            xsize 1920
            ysize 270

        add "gui/story_ui/ui_notebook_canvas.png" at story_ui_bleed_canvas

        add "gui/ui_test_skin/dialogue_photo_avatar.png":
            xpos 226
            ypos 584
            xysize (370, 370)

        add "gui/ui_test_skin/name_tape.png":
            xpos 342
            ypos 760
            xysize (300, 72)

        text "阿弥":
            xpos 445
            ypos 776
            xsize 170
            size 28
            color "#1f1a15"

        text "这是一段 UI 测试对白。这里用于检查纸张文本区、角色照片模块、姓名标签和字体位置是否协调。":
            xpos notebook_dialogue_x
            ypos notebook_dialogue_y
            xsize 760
            size 32
            line_spacing 9
            color "#211b15"

        textbutton "返回":
            xpos 1408
            ypos 900
            style "rm_ui_test_prominent_button"
            action Return()

        use rm_ui_test_close_button(Return())


screen rm_ui_test_hud_preview():
    modal True
    zorder 240

    use rm_allow_game_menu
    add Solid("#00000099")

    fixed:
        xysize (1920, 1080)

        add "gui/ui_test_skin/dice_check_panel.png":
            xalign 0.5
            yalign 0.5
            xysize (920, 690)

        use rm_ui_test_skin_hud_surface(570, 300)

        text "时钟 + 心境温度计条":
            xpos 650
            ypos 520
            size 36
            color "#211b15"

        text "心境条读取当前 mood，并用游标标记位置。这个温度计式长条不表示体温或精力。":
            xpos 650
            ypos 578
            xsize 620
            size 26
            line_spacing 7
            color "#3f352b"

        textbutton "返回":
            xpos 1230
            ypos 812
            style "rm_ui_test_prominent_button"
            action Return()

        use rm_ui_test_close_button(Return())


style rm_ui_test_prominent_button is button:
    xsize 220
    ysize 68
    background Frame("gui/ui_test_skin/prominent_tab.png", 72, 22, 72, 22)
    hover_background Frame("gui/ui_test_skin/prominent_tab.png", 72, 22, 72, 22)
    padding (20, 0)

style rm_ui_test_prominent_button_text is button_text:
    size 24
    color "#211b15"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style rm_ui_test_option_button is button:
    xsize 172
    ysize 58
    background Frame("gui/ui_test_skin/option_button.png", 42, 18, 42, 18)
    hover_background Frame("gui/ui_test_skin/option_button.png", 42, 18, 42, 18)
    padding (20, 0)

style rm_ui_test_option_button_text is button_text:
    size 24
    color "#211b15"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style rm_ui_test_close_button_style is button:
    xsize 74
    ysize 74
    background Frame("gui/ui_test_skin/close_circle.png", 32, 32)
    hover_background Frame("gui/ui_test_skin/close_circle.png", 32, 32)
    padding (0, 0)

style rm_ui_test_close_button_style_text is button_text:
    size 28
    bold True
    color "#211b15"
    hover_color "#000000"
    insensitive_color "#f3eadb"
    xalign 0.5
    yalign 0.5
