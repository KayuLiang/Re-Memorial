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
        return 292 + story_hud_energy_fill_width(points, maximum)


screen rm_ui_test_close_button(action=Return("__rm_ui_test_exit__")):
    textbutton "X":
        xpos 2365
        ypos 64
        style "rm_ui_test_close_button_style"
        action action


screen rm_ui_test_skin_hud_surface(origin_x=48, origin_y=37):
    $ status_mood = rm_status_mood_value()
    $ status_energy = rm_status_energy_points()
    $ status_energy_max = rm_status_energy_max()

    fixed:
        xysize (2560, 307)

        add "gui/ui_test_skin/clock_face.png":
            xpos origin_x
            ypos origin_y
            xysize (200, 200)

        add Transform(
            "gui/ui_test_skin/clock_hand.png",
            zoom=0.16,
            anchor=(0.5, 0.82),
            pos=(origin_x + 100, origin_y + 104),
            rotate=story_hud_clock_rotation(current_time_minutes),
        )

        add "gui/story_ui/ui_mood_bar_canvas.png" at story_hud_bleed_canvas

        add "gui/story_ui/ui_energy_empty_canvas.png" at story_hud_bleed_canvas

        viewport:
            xpos 292
            ypos 160
            xysize (story_hud_energy_fill_width(status_energy, status_energy_max), 77)
            add Crop((630, 347, 982, 115), "gui/story_ui/ui_energy_full_canvas.png"):
                zoom (2.0 / 3.0)

        add "gui/ui_test_skin/mood_cursor.png":
            xpos rm_ui_test_mood_cursor_offset(status_mood)
            ypos 61
            xysize (45, 109)

        add "gui/ui_test_skin/mood_cursor.png":
            xpos rm_ui_test_energy_cursor_offset(status_energy, status_energy_max)
            ypos 136
            xysize (45, 109)

        text "心境 [status_mood]":
            xpos 980
            ypos 99
            size 32
            color "#000000"

        text "精力 [status_energy]/[status_energy_max]":
            xpos 980
            ypos 157
            size 32
            color "#000000"


screen rm_ui_test_skin_hud():
    zorder 86

    if not main_menu and not opening_active and rm_test_flow_active and rm_ui_test_skin_active:
        use rm_ui_test_skin_hud_surface(48, 37)


screen rm_ui_test_dialogue_preview():
    modal True
    zorder 240

    use rm_allow_game_menu
    add Solid("#00000099")

    fixed:
        xysize (2560, 1440)

        add Solid("#0b0a09e6"):
            xpos 0
            ypos 1080
            xsize 2560
            ysize 360

        add "gui/story_ui/ui_notebook_canvas.png" at story_ui_bleed_canvas

        add "gui/ui_test_skin/dialogue_photo_avatar.png":
            xpos 301
            ypos 779
            xysize (493, 493)

        add "gui/ui_test_skin/name_tape.png":
            xpos 456
            ypos 1013
            xysize (400, 96)

        text "阿弥":
            xpos 593
            ypos 1035
            xsize 227
            size 37
            color "#000000"

        text "这是一段 UI 测试对白。这里用于检查纸张文本区、角色照片模块、姓名标签和字体位置是否协调。":
            xpos notebook_dialogue_x
            ypos notebook_dialogue_y
            xsize 1013
            size 43
            line_spacing 12
            color "#000000"

        textbutton "返回":
            xpos 1877
            ypos 1200
            style "rm_ui_test_prominent_button"
            action Return()

        use rm_ui_test_close_button(Return())


screen rm_ui_test_hud_preview():
    modal True
    zorder 240

    use rm_allow_game_menu
    add Solid("#00000099")

    fixed:
        xysize (2560, 1440)

        add "gui/ui_test_skin/dice_check_panel.png":
            xalign 0.5
            yalign 0.5
            xysize (1227, 920)

        use rm_ui_test_skin_hud_surface(570, 300)

        text "时钟 + 心境温度计条":
            xpos 867
            ypos 693
            size 48
            color "#000000"

        text "心境条读取当前 mood，并用游标标记位置。这个温度计式长条不表示体温或精力。":
            xpos 867
            ypos 771
            xsize 827
            size 35
            line_spacing 9
            color "#000000"

        textbutton "返回":
            xpos 1640
            ypos 1083
            style "rm_ui_test_prominent_button"
            action Return()

        use rm_ui_test_close_button(Return())


style rm_ui_test_prominent_button is button:
    xsize 293
    ysize 91
    background Frame("gui/ui_test_skin/prominent_tab.png", 72, 22, 72, 22)
    hover_background Frame("gui/ui_test_skin/prominent_tab.png", 72, 22, 72, 22)
    padding (27, 0)

style rm_ui_test_prominent_button_text is button_text:
    size 32
    color "#000000"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style rm_ui_test_option_button is button:
    xsize 229
    ysize 77
    background Frame("gui/ui_test_skin/option_button.png", 42, 18, 42, 18)
    hover_background Frame("gui/ui_test_skin/option_button.png", 42, 18, 42, 18)
    padding (27, 0)

style rm_ui_test_option_button_text is button_text:
    size 32
    color "#000000"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style rm_ui_test_close_button_style is button:
    xsize 99
    ysize 99
    background Frame("gui/ui_test_skin/close_circle.png", 32, 32)
    hover_background Frame("gui/ui_test_skin/close_circle.png", 32, 32)
    padding (0, 0)

style rm_ui_test_close_button_style_text is button_text:
    size 37
    bold True
    color "#000000"
    hover_color "#000000"
    insensitive_color "#000000"
    xalign 0.5
    yalign 0.5
