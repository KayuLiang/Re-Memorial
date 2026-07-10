# Story HUD buttons that unlock from narrative beats.

init python:
    config.overlay_screens.append("top_status")
    config.overlay_screens.append("story_hud_buttons")
    config.overlay_screens.append("rm_test_status_overlay")

    def story_hud_unlock(button_id):
        if button_id == "status":
            store.story_hud_status_unlocked = True
        elif button_id == "character_panel":
            store.story_hud_character_panel_unlocked = True
        elif button_id == "inventory":
            store.story_hud_inventory_unlocked = True
        elif button_id == "medicine":
            store.story_hud_medicine_unlocked = True
        else:
            raise Exception("Unknown story HUD button: {}".format(button_id))

        renpy.restart_interaction()

    def story_hud_lock(button_id):
        if button_id == "status":
            store.story_hud_status_unlocked = False
        elif button_id == "character_panel":
            store.story_hud_character_panel_unlocked = False
        elif button_id == "inventory":
            store.story_hud_inventory_unlocked = False
        elif button_id == "medicine":
            store.story_hud_medicine_unlocked = False
        else:
            raise Exception("Unknown story HUD button: {}".format(button_id))

        renpy.restart_interaction()

    def story_hud_clamp(value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def story_hud_clock_rotation(minutes):
        return (minutes % 720) / 720.0 * 360.0

    def story_hud_mood_cursor_offset(value):
        clamped = story_hud_clamp(value, -200, 200)
        return 223 + int(((clamped + 200) / 400.0) * 489)

    def story_hud_energy_fill_width(points, maximum):
        if maximum <= 0:
            return 0
        clamped = story_hud_clamp(points, 0, maximum)
        return int((clamped / float(maximum)) * 491)

default story_hud_status_unlocked = False
default story_hud_character_panel_unlocked = False
default story_hud_inventory_unlocked = False
default story_hud_medicine_unlocked = False
default day_count = 1
default mood_value = 55
default energy_points = 3
default max_energy_points = 4
default current_time_minutes = 13 * 60 + 30


transform story_hud_bleed_canvas:
    zoom 0.5
    xalign 0.5
    yalign 0.5


transform story_hud_button_hover:
    on hover:
        linear 0.12 yoffset -4
    on idle:
        linear 0.12 yoffset 0


label unlock_story_status_hud:
    $ story_hud_unlock("status")
    return


label unlock_character_panel_button:
    $ story_hud_unlock("character_panel")
    return


label unlock_inventory_button:
    $ story_hud_unlock("inventory")
    return


label unlock_medicine_button:
    $ story_hud_unlock("medicine")
    return


screen top_status():
    zorder 85
    default status_tooltip = None

    if not main_menu and not opening_active and story_hud_status_unlocked:
        if not rm_ui_test_skin_active:
            $ status_mood = rm_status_mood_value()
            $ status_energy = rm_status_energy_points()
            $ status_energy_max = rm_status_energy_max()

            fixed:
                xysize (1920, 1080)

                add "gui/story_ui/ui_clock_canvas.png" at story_hud_bleed_canvas

                add Transform(
                    Crop((417, 167, 61, 210), "gui/story_ui/ui_clock_hand_canvas.png"),
                    zoom=0.5,
                    anchor=(0.565, 0.855),
                    pos=(130, 119),
                    rotate=story_hud_clock_rotation(current_time_minutes),
                )

                add "gui/story_ui/ui_mood_bar_canvas.png" at story_hud_bleed_canvas

                add Transform(
                    Crop((1171, 249, 42, 93), "gui/story_ui/ui_mood_cursor_canvas.png"),
                    zoom=0.5,
                    anchor=(0.5, 0.0),
                    pos=(story_hud_mood_cursor_offset(status_mood), 70),
                )

                add "gui/story_ui/ui_energy_empty_canvas.png" at story_hud_bleed_canvas

                viewport:
                    xpos 219
                    ypos 120
                    xysize (story_hud_energy_fill_width(status_energy, status_energy_max), 58)
                    add Crop((630, 347, 982, 115), "gui/story_ui/ui_energy_full_canvas.png"):
                        zoom 0.5

                button:
                    xpos 105
                    ypos 64
                    xysize (650, 78)
                    background None
                    hover_background None
                    action NullAction()
                    hovered SetScreenVariable("status_tooltip", rm_status_mood_tooltip())
                    unhovered SetScreenVariable("status_tooltip", None)

                button:
                    xpos 219
                    ypos 120
                    xysize (491, 58)
                    background None
                    hover_background None
                    action NullAction()
                    hovered SetScreenVariable("status_tooltip", rm_status_energy_tooltip())
                    unhovered SetScreenVariable("status_tooltip", None)

                if status_tooltip:
                    frame:
                        style "top_status_tooltip_frame"
                        text status_tooltip style "top_status_tooltip_text"


screen story_hud_buttons():
    zorder 90

    if not main_menu and not opening_active:
        fixed:
            xysize (1920, 1080)

            if rm_test_flow_active:
                textbutton "操作台":
                    style "story_hud_console_button"
                    action Show("rm_test_console")

            if story_hud_character_panel_unlocked:
                imagebutton:
                    idle "gui/story_ui/ui_btn_character_canvas.png"
                    hover "gui/story_ui/ui_btn_character_canvas.png"
                    selected_idle "gui/story_ui/ui_btn_character_canvas.png"
                    selected_hover "gui/story_ui/ui_btn_character_canvas.png"
                    focus_mask True
                    selected renpy.get_screen("character_panel") is not None
                    action Show("character_panel")
                    at story_hud_bleed_canvas, story_hud_button_hover

            if story_hud_inventory_unlocked:
                imagebutton:
                    idle "gui/story_ui/ui_btn_inventory_canvas.png"
                    hover "gui/story_ui/ui_btn_inventory_canvas.png"
                    selected_idle "gui/story_ui/ui_btn_inventory_canvas.png"
                    selected_hover "gui/story_ui/ui_btn_inventory_canvas.png"
                    focus_mask True
                    selected renpy.get_screen("inventory_panel") is not None
                    action Show("inventory_panel")
                    at story_hud_bleed_canvas, story_hud_button_hover

            if story_hud_medicine_unlocked:
                imagebutton:
                    idle "gui/story_ui/ui_btn_medicine_canvas.png"
                    hover "gui/story_ui/ui_btn_medicine_canvas.png"
                    selected_idle "gui/story_ui/ui_btn_medicine_canvas.png"
                    selected_hover "gui/story_ui/ui_btn_medicine_canvas.png"
                    focus_mask True
                    selected renpy.get_screen("inventory_panel") is not None
                    action Show("inventory_panel", start_category="medicine")
                    at story_hud_bleed_canvas, story_hud_button_hover


screen rm_test_console():
    modal True
    zorder 215
    default selected_attribute = "str"

    use modal_dim_background

    key "game_menu" action Hide("rm_test_console")

    $ character = rm_ensure_player()
    $ summary = rm_status_character_summary()
    $ attr = summary["attributes"][selected_attribute]

    frame:
        style "rm_test_console_frame"

        vbox:
            spacing 16
            xfill True

            hbox:
                xfill True
                text "测试操作台" style "rm_test_console_title_text"
                null width 420
                textbutton "×":
                    style "character_panel_close_button"
                    action Hide("rm_test_console")

            hbox:
                spacing 10
                textbutton "Mood -10":
                    style "rm_test_console_button"
                    action Function(rm_test_console_adjust_mood, -10)
                textbutton "Mood +10":
                    style "rm_test_console_button"
                    action Function(rm_test_console_adjust_mood, 10)

            grid 5 1:
                spacing 8
                xfill True

                textbutton "进入高涨情绪":
                    style "rm_test_console_small_button"
                    action Function(rm_test_console_set_mood_state, "high")
                textbutton "进入低落情绪":
                    style "rm_test_console_small_button"
                    action Function(rm_test_console_set_mood_state, "low")
                textbutton "正常状态":
                    style "rm_test_console_small_button"
                    action Function(rm_test_console_set_mood_state, "stable")
                textbutton "抑郁状态":
                    style "rm_test_console_small_button"
                    action Function(rm_test_console_set_mood_state, "depression")
                textbutton "躁狂状态":
                    style "rm_test_console_small_button"
                    action Function(rm_test_console_set_mood_state, "mania")

            hbox:
                spacing 18
                xfill True

                vbox:
                    spacing 8
                    text "选择属性" style "rm_test_console_section_text"

                    for attribute in rm_core.ATTRIBUTES:
                        $ row = summary["attributes"][attribute]
                        textbutton "[row['label']]":
                            style "rm_test_console_attr_button"
                            selected selected_attribute == attribute
                            action SetScreenVariable("selected_attribute", attribute)

                vbox:
                    spacing 10
                    xfill True

                    text "[attr['label']]：正式 [attr['formal']] / 加值 [attr['value']] / 加成 [attr['bonus']] / 当前 [attr['current']] / 有效 [attr['effective']]" style "rm_test_console_value_text"

                    hbox:
                        spacing 8
                        text "特定属性" style "rm_test_console_row_label_text"
                        textbutton "-1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_formal_attribute, selected_attribute, -1)
                        textbutton "+1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_formal_attribute, selected_attribute, 1)

                    hbox:
                        spacing 8
                        text "特定属性加值" style "rm_test_console_row_label_text"
                        textbutton "-1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_attribute_value, selected_attribute, -1)
                        textbutton "+1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_attribute_value, selected_attribute, 1)

                    hbox:
                        spacing 8
                        text "特定属性加成" style "rm_test_console_row_label_text"
                        textbutton "-1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_attribute_bonus, selected_attribute, -1)
                        textbutton "+1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_attribute_bonus, selected_attribute, 1)


screen character_panel():
    modal True
    zorder 205
    default panel_tab = "summary"
    default panel_tooltip = None

    use modal_dim_background

    key "game_menu" action Hide("character_panel")
    $ summary = rm_status_character_summary()
    $ dice_pool = rm_status_dice_pool_summary()

    frame:
        style "character_panel_frame"

        vbox:
            spacing 16
            xfill True

            hbox:
                xfill True
                text "人物" style "character_panel_title_text"
                null width 400
                textbutton "×":
                    xalign 1.0
                    style "character_panel_close_button"
                    action Hide("character_panel")

            hbox:
                spacing 10
                textbutton "概览":
                    style "character_panel_tab_button"
                    selected panel_tab == "summary"
                    action SetScreenVariable("panel_tab", "summary")
                textbutton "骰组":
                    style "character_panel_tab_button"
                    selected panel_tab == "dice"
                    action SetScreenVariable("panel_tab", "dice")

            if panel_tab == "summary":
                vbox:
                    spacing 14
                    xfill True

                    grid 3 1:
                        spacing 12
                        xfill True

                        frame:
                            style "character_panel_status_tile"
                            vbox:
                                spacing 5
                                text "Mood" style "character_panel_label_text"
                                text "[summary['mood']['value']] · [summary['mood']['label']]" style "character_panel_value_text"

                        frame:
                            style "character_panel_status_tile"
                            vbox:
                                spacing 5
                                text "病程状态" style "character_panel_label_text"
                                text "[summary['disease']['label']]" style "character_panel_value_text"

                        frame:
                            style "character_panel_status_tile"
                            vbox:
                                spacing 5
                                text "精力" style "character_panel_label_text"
                                text "[summary['energy']['current']] / [summary['energy']['maximum']]" style "character_panel_value_text"

                    text "属性" style "character_panel_section_text"

                    grid 5 1:
                        spacing 8
                        xfill True

                        for attribute in rm_core.ATTRIBUTES:
                            $ row = summary["attributes"][attribute]
                            frame:
                                style "character_panel_attribute_tile"
                                vbox:
                                    spacing 4
                                    text "[row['label']]" style "character_panel_label_text"
                                    text "[row['current']] / [row['effective']]" style "character_panel_value_text"
                                    text "正式 [row['formal']]" style "character_panel_hint_text"

                    text "状态" style "character_panel_section_text"

                    if summary['statuses']:
                        hbox:
                            spacing 8
                            box_wrap True

                            for status in summary['statuses']:
                                textbutton "[status['label']] [status['value_text']]":
                                    style "character_panel_status_button"
                                    action NullAction()
                                    hovered SetScreenVariable("panel_tooltip", status["tooltip"])
                                    unhovered SetScreenVariable("panel_tooltip", None)
                    else:
                        text "暂无状态" style "character_panel_hint_text"

                    if panel_tooltip:
                        frame:
                            style "character_panel_tooltip_frame"
                            text panel_tooltip style "character_panel_tooltip_text"

            else:
                viewport:
                    xfill True
                    ymaximum 420
                    mousewheel True
                    draggable True

                    vpgrid:
                        cols 2
                        spacing 10
                        xfill True

                        for die in dice_pool:
                            frame:
                                style "character_panel_die_tile"
                                vbox:
                                    spacing 5
                                    text "[die['label']] · [die['id']]" style "character_panel_value_text"
                                    text "骰面 [die['faces_text']]" style "character_panel_hint_text"
                                    text "期望 [die['expectation_text']]  状态 [die['enchantment_label']]" style "character_panel_hint_text"


screen rm_test_status_overlay():
    zorder 88
    default status_tip = None

    if not main_menu and not opening_active and rm_test_flow_active:
        $ statuses = rm_status_statuses()

        fixed:
            xysize (1920, 1080)

            frame:
                style "rm_test_status_overlay_frame"

                vbox:
                    spacing 10
                    text "状态" style "rm_test_status_overlay_title_text"

                    viewport:
                        xysize (172, 336)
                        mousewheel True
                        draggable True

                        vpgrid:
                            cols 3
                            spacing 8
                            xfill True

                            for status in statuses:
                                textbutton "[status['label']] [status['value_text']]":
                                    style "rm_test_status_overlay_button"
                                    action NullAction()
                                    hovered SetScreenVariable("status_tip", status["tooltip"])
                                    unhovered SetScreenVariable("status_tip", None)

            if status_tip:
                frame:
                    style "rm_test_status_overlay_tooltip_frame"
                    text status_tip style "rm_test_status_overlay_tooltip_text"


style story_hud_button_row is hbox:
    xpos 1455
    ypos 35
    spacing 24

style story_hud_button is button:
    xsize 118
    ysize 118
    padding (0, 0)
    background "#e8dfcfdd"
    hover_background "#f4ecdfff"
    selected_background "#d4c7afff"

style story_hud_button_text is button_text:
    size 26
    color "#171513"
    hover_color "#000000"
    selected_color "#000000"
    xalign 0.5
    yalign 0.5

style story_hud_character_button is story_hud_button
style story_hud_inventory_button is story_hud_button
style story_hud_medicine_button is story_hud_button

style story_hud_character_button_text is story_hud_button_text
style story_hud_inventory_button_text is story_hud_button_text
style story_hud_medicine_button_text is story_hud_button_text

style story_hud_console_button is button:
    xpos 1328
    ypos 46
    xsize 118
    ysize 46
    background "#241f1adf"
    hover_background "#3a3129f2"
    padding (0, 0)

style story_hud_console_button_text is button_text:
    size 22
    color "#f3eadb"
    hover_color "#ffffff"
    xalign 0.5
    yalign 0.5

style story_hud_button_icon_text is gui_text:
    size 48
    color "#171513"
    xalign 0.5
    ypos 18

style story_hud_button_label_text is gui_text:
    size 20
    color "#171513"
    xalign 0.5
    ypos 78

style top_status_clock_frame is frame:
    xpos 32
    ypos 30
    xsize 178
    ysize 178
    background "#eee5d4dd"
    padding (0, 0)

style top_status_clock_label_text is gui_text:
    size 30
    color "#171513"
    xalign 0.5

style top_status_clock_value_text is gui_text:
    size 58
    color "#171513"
    xalign 0.5

style top_status_mood_frame is frame:
    xpos 198
    ypos 42
    xsize 462
    ysize 76
    background "#e8dfcfdd"
    padding (0, 0)

style top_status_energy_frame is frame:
    xpos 218
    ypos 130
    xsize 405
    ysize 68
    background "#e8dfcfdd"
    padding (0, 0)

style top_status_label_text is gui_text:
    size 28
    color "#171513"

style top_status_mood_icon_text is gui_text:
    size 34
    color "#171513"

style top_status_heart_full_text is gui_text:
    size 42
    color "#6c8d4d"

style top_status_heart_empty_text is gui_text:
    size 42
    color "#8d8980"

style top_status_tooltip_frame is frame:
    xpos 245
    ypos 184
    background "#241f1adf"
    padding (14, 8)

style top_status_tooltip_text is gui_text:
    size 20
    color "#f3eadb"

style character_panel_frame is frame:
    xalign 0.5
    yalign 0.5
    xsize 850
    ysize 640
    background "#eee7d8f4"
    padding (34, 30)

style character_panel_title_text is gui_text:
    size 40
    bold True
    color "#171513"

style character_panel_body_text is gui_text:
    size 26
    color "#24201c"

style rm_test_console_frame is frame:
    xalign 0.5
    yalign 0.5
    xsize 900
    ysize 620
    background "#eee7d8f4"
    padding (34, 30)

style rm_test_console_title_text is gui_text:
    size 36
    bold True
    color "#171513"

style rm_test_console_section_text is gui_text:
    size 22
    bold True
    color "#171513"

style rm_test_console_value_text is gui_text:
    size 22
    color "#171513"

style rm_test_console_row_label_text is gui_text:
    xsize 170
    size 22
    color "#171513"
    yalign 0.5

style rm_test_console_button is button:
    xsize 128
    ysize 44
    background "#d9cdbb"
    hover_background "#eadfcc"
    padding (0, 0)

style rm_test_console_button_text is button_text:
    size 20
    color "#171513"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style rm_test_console_small_button is rm_test_console_button:
    xsize 138

style rm_test_console_small_button_text is rm_test_console_button_text:
    size 17

style rm_test_console_attr_button is button:
    xsize 108
    ysize 40
    background "#d9cdbb"
    hover_background "#eadfcc"
    selected_background "#2b2520"
    padding (0, 0)

style rm_test_console_attr_button_text is button_text:
    size 19
    color "#171513"
    hover_color "#000000"
    selected_color "#f5eddf"
    xalign 0.5
    yalign 0.5

style rm_test_console_step_button is button:
    xsize 58
    ysize 38
    background "#d9cdbb"
    hover_background "#eadfcc"
    padding (0, 0)

style rm_test_console_step_button_text is button_text:
    size 22
    color "#171513"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style character_panel_close_button is button:
    xsize 48
    ysize 44
    padding (0, 0)
    background "#d8cbb7"
    hover_background "#efe3cf"

style character_panel_close_button_text is button_text:
    size 28
    color "#171513"
    xalign 0.5
    yalign 0.5

style character_panel_tab_button is button:
    xsize 108
    ysize 42
    padding (0, 0)
    background "#d9cdbb"
    hover_background "#eadfcc"
    selected_background "#2b2520"

style character_panel_tab_button_text is button_text:
    size 22
    color "#171513"
    hover_color "#171513"
    selected_color "#f5eddf"
    xalign 0.5
    yalign 0.5

style character_panel_status_tile is frame:
    xfill True
    ysize 92
    background "#f7f0e4"
    padding (16, 12)

style character_panel_attribute_tile is frame:
    xfill True
    ysize 118
    background "#f7f0e4"
    padding (12, 12)

style character_panel_die_tile is frame:
    xfill True
    ysize 112
    background "#f7f0e4"
    padding (14, 12)

style character_panel_section_text is gui_text:
    size 24
    bold True
    color "#171513"

style character_panel_label_text is gui_text:
    size 18
    color "#6d6257"

style character_panel_value_text is gui_text:
    size 24
    color "#171513"

style character_panel_hint_text is gui_text:
    size 18
    color "#5c554e"

style character_panel_status_button is button:
    ysize 38
    background "#d9cdbb"
    hover_background "#eadfcc"
    padding (12, 0)

style character_panel_status_button_text is button_text:
    size 18
    color "#171513"
    hover_color "#000000"
    yalign 0.5

style character_panel_tooltip_frame is frame:
    xfill True
    background "#241f1adf"
    padding (12, 8)

style character_panel_tooltip_text is gui_text:
    size 18
    color "#f3eadb"

style rm_test_status_overlay_frame is frame:
    xpos 70
    ypos 280
    xsize 200
    ysize 400
    background "#eee7d8e8"
    padding (14, 12)

style rm_test_status_overlay_title_text is gui_text:
    size 20
    bold True
    color "#171513"

style rm_test_status_overlay_button is button:
    xsize 52
    ysize 44
    background "#f7f0e4"
    hover_background "#eadfcc"
    padding (2, 0)

style rm_test_status_overlay_button_text is button_text:
    size 10
    color "#171513"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style rm_test_status_overlay_tooltip_frame is frame:
    xpos 290
    ypos 280
    xmaximum 520
    background "#241f1adf"
    padding (12, 8)

style rm_test_status_overlay_tooltip_text is gui_text:
    size 18
    color "#f3eadb"
