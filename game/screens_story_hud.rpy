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

    def story_hud_clamp(value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def story_hud_clock_rotation(minutes):
        return (minutes % 720) / 720.0 * 360.0

    def story_hud_mood_cursor_offset(value):
        clamped = story_hud_clamp(value, -200, 200)
        return 297 + int(((clamped + 200) / 400.0) * 652)

    def story_hud_energy_fill_width(points, maximum):
        if maximum <= 0:
            return 0
        clamped = story_hud_clamp(points, 0, maximum)
        return int((clamped / float(maximum)) * 655)

default story_hud_status_unlocked = False
default story_hud_character_panel_unlocked = False
default story_hud_inventory_unlocked = False
default story_hud_medicine_unlocked = False
default current_time_minutes = 13 * 60 + 30


transform story_hud_bleed_canvas:
    zoom (2.0 / 3.0)
    xalign 0.5
    yalign 0.5


transform story_hud_button_hover:
    on hover:
        linear 0.12 yoffset -5
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
    use rm_flat_status


screen story_hud_buttons():
    zorder 90
    use rm_flat_navigation


screen rm_test_console():
    modal True
    zorder 215
    default selected_attribute = "str"

    use modal_dim_background

    key "game_menu" action Hide("rm_test_console")

    $ summary = rm_status_character_summary()
    $ attr = summary["attributes"][selected_attribute]

    frame:
        style "rm_test_console_frame"

        vbox:
            spacing 21
            xfill True

            hbox:
                xfill True
                text "测试操作台" style "rm_test_console_title_text"
                null width 560
                textbutton "×":
                    style "character_panel_close_button"
                    action Hide("rm_test_console")

            hbox:
                spacing 13
                textbutton "Mood -10":
                    style "rm_test_console_button"
                    action Function(rm_test_console_adjust_mood, -10)
                textbutton "Mood +10":
                    style "rm_test_console_button"
                    action Function(rm_test_console_adjust_mood, 10)

            grid 5 1:
                spacing 11
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
                spacing 24
                xfill True

                vbox:
                    spacing 11
                    text "选择属性" style "rm_test_console_section_text"

                    for attribute in rm_core.ATTRIBUTES:
                        $ row = summary["attributes"][attribute]
                        textbutton "[row['label']]":
                            style "rm_test_console_attr_button"
                            selected selected_attribute == attribute
                            action SetScreenVariable("selected_attribute", attribute)

                vbox:
                    spacing 13
                    xfill True

                    text "[attr['label']]：正式 [attr['formal']] / 加值 [attr['value']] / 加成 [attr['bonus']] / 当前 [attr['current']] / 有效 [attr['effective']]" style "rm_test_console_value_text"

                    hbox:
                        spacing 11
                        text "特定属性" style "rm_test_console_row_label_text"
                        textbutton "-1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_formal_attribute, selected_attribute, -1)
                        textbutton "+1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_formal_attribute, selected_attribute, 1)

                    hbox:
                        spacing 11
                        text "特定属性加值" style "rm_test_console_row_label_text"
                        textbutton "-1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_attribute_value, selected_attribute, -1)
                        textbutton "+1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_attribute_value, selected_attribute, 1)

                    hbox:
                        spacing 11
                        text "特定属性加成" style "rm_test_console_row_label_text"
                        textbutton "-1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_attribute_bonus, selected_attribute, -1)
                        textbutton "+1":
                            style "rm_test_console_step_button"
                            action Function(rm_test_console_adjust_attribute_bonus, selected_attribute, 1)


screen character_panel(start_tab="summary"):
    modal True
    zorder 205
    default panel_tab = start_tab
    default case_attribute = "str"
    default case_filter = "all"
    default case_status = None
    default case_page = 0
    default dice_mode = "collection"
    default dice_filter = "all"
    default dice_order = "attribute"
    default dice_enchantment = "all"
    default dice_selected = None
    default dice_page = 0
    default dice_face = 0
    default dice_offset = 0
    default dice_menu = None
    default dice_growth_attribute = "str"
    default dice_opened = 0.0
    default dice_origin = (195,398)
    default dice_scroll = (float(dice_offset),float(dice_offset),0.0)
    key "game_menu" action Hide("character_panel")

    if panel_tab == "dice":
        use rm_dice_content(dice_mode, dice_filter, dice_order, dice_enchantment, dice_selected, dice_page, dice_face, dice_offset, dice_menu, dice_growth_attribute, dice_opened, dice_origin, dice_scroll)
    else:
        use rm_case_content(panel_tab, case_attribute, case_filter, case_status, case_page)


screen rm_legacy_character_panel(start_tab="dice"):
    modal True
    zorder 205
    default panel_tab = start_tab
    default panel_tooltip = None

    use modal_dim_background

    key "game_menu" action Hide("character_panel")
    $ summary = rm_status_character_summary()
    $ dice_pool = rm_status_dice_pool_summary()

    frame:
        style "character_panel_frame"

        vbox:
            spacing 21
            xfill True

            hbox:
                xfill True
                text "人物" style "character_panel_title_text"
                null width 533
                textbutton "×":
                    xalign 1.0
                    style "character_panel_close_button"
                    action Hide("character_panel")

            hbox:
                spacing 13
                textbutton "概览":
                    style "character_panel_tab_button"
                    selected panel_tab == "summary"
                    action [Hide("character_panel"), Show("character_panel", start_tab="summary")]
                textbutton "骰组":
                    style "character_panel_tab_button"
                    selected panel_tab == "dice"
                    action SetScreenVariable("panel_tab", "dice")

            if panel_tab == "summary":
                vbox:
                    spacing 19
                    xfill True

                    grid 3 1:
                        spacing 16
                        xfill True

                        frame:
                            style "character_panel_status_tile"
                            vbox:
                                spacing 7
                                text "Mood" style "character_panel_label_text"
                                text "[summary['mood']['value']] · [summary['mood']['label']]" style "character_panel_value_text"

                        frame:
                            style "character_panel_status_tile"
                            vbox:
                                spacing 7
                                text "病程状态" style "character_panel_label_text"
                                text "[summary['disease']['label']]" style "character_panel_value_text"

                        frame:
                            style "character_panel_status_tile"
                            vbox:
                                spacing 7
                                text "精力" style "character_panel_label_text"
                                text "[summary['energy']['current']] / [summary['energy']['maximum']]" style "character_panel_value_text"

                    text "属性" style "character_panel_section_text"

                    grid 5 1:
                        spacing 11
                        xfill True

                        for attribute in rm_core.ATTRIBUTES:
                            $ row = summary["attributes"][attribute]
                            frame:
                                style "character_panel_attribute_tile"
                                vbox:
                                    spacing 5
                                    text "[row['label']]" style "character_panel_label_text"
                                    text "[row['current']] / [row['effective']]" style "character_panel_value_text"
                                    text "正式 [row['formal']]" style "character_panel_hint_text"

                    text "状态" style "character_panel_section_text"

                    if summary['statuses']:
                        hbox:
                            spacing 11
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
                    ymaximum 560
                    mousewheel True
                    draggable True

                    vpgrid:
                        cols 2
                        spacing 13
                        xfill True

                        for die in dice_pool:
                            frame:
                                style "character_panel_die_tile"
                                vbox:
                                    spacing 7
                                    text "[die['label']] · [die['id']]" style "character_panel_value_text"
                                    text "骰面 [die['faces_text']]" style "character_panel_hint_text"
                                    text "期望 [die['expectation_text']]  状态 [die['enchantment_label']]" style "character_panel_hint_text"


screen rm_test_status_overlay():
    zorder 88
    use rm_flat_sides


style story_hud_console_button is button:
    xpos 1771
    ypos 61
    xsize 157
    ysize 61
    background "#241f1adf"
    hover_background "#3a3129f2"
    padding (0, 0)

style story_hud_console_button_text is button_text:
    size 29
    color "#f3eadb"
    hover_color "#ffffff"
    xalign 0.5
    yalign 0.5

style top_status_tooltip_frame is frame:
    xpos 327
    ypos 245
    background "#241f1adf"
    padding (19, 11)

style top_status_tooltip_text is gui_text:
    size 27
    color "#f3eadb"

style character_panel_frame is frame:
    xalign 0.5
    yalign 0.5
    xsize 1133
    ysize 853
    background "#eee7d8f4"
    padding (45, 40)

style character_panel_title_text is gui_text:
    size 53
    bold True
    color "#171513"

style rm_test_console_frame is frame:
    xalign 0.5
    yalign 0.5
    xsize 1200
    ysize 827
    background "#eee7d8f4"
    padding (45, 40)

style rm_test_console_title_text is gui_text:
    size 48
    bold True
    color "#171513"

style rm_test_console_section_text is gui_text:
    size 29
    bold True
    color "#171513"

style rm_test_console_value_text is gui_text:
    size 29
    color "#171513"

style rm_test_console_row_label_text is gui_text:
    xsize 227
    size 29
    color "#171513"
    yalign 0.5

style rm_test_console_button is button:
    xsize 171
    ysize 59
    background "#d9cdbb"
    hover_background "#eadfcc"
    padding (0, 0)

style rm_test_console_button_text is button_text:
    size 27
    color "#171513"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style rm_test_console_small_button is rm_test_console_button:
    xsize 184

style rm_test_console_small_button_text is rm_test_console_button_text:
    size 23

style rm_test_console_attr_button is button:
    xsize 144
    ysize 53
    background "#d9cdbb"
    hover_background "#eadfcc"
    selected_background "#2b2520"
    padding (0, 0)

style rm_test_console_attr_button_text is button_text:
    size 25
    color "#171513"
    hover_color "#000000"
    selected_color "#f5eddf"
    xalign 0.5
    yalign 0.5

style rm_test_console_step_button is button:
    xsize 77
    ysize 51
    background "#d9cdbb"
    hover_background "#eadfcc"
    padding (0, 0)

style rm_test_console_step_button_text is button_text:
    size 29
    color "#171513"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style character_panel_close_button is button:
    xsize 64
    ysize 59
    padding (0, 0)
    background "#d8cbb7"
    hover_background "#efe3cf"

style character_panel_close_button_text is button_text:
    size 37
    color "#171513"
    xalign 0.5
    yalign 0.5

style character_panel_tab_button is button:
    xsize 144
    ysize 56
    padding (0, 0)
    background "#d9cdbb"
    hover_background "#eadfcc"
    selected_background "#2b2520"

style character_panel_tab_button_text is button_text:
    size 29
    color "#171513"
    hover_color "#171513"
    selected_color "#f5eddf"
    xalign 0.5
    yalign 0.5

style character_panel_status_tile is frame:
    xfill True
    ysize 123
    background "#f7f0e4"
    padding (21, 16)

style character_panel_attribute_tile is frame:
    xfill True
    ysize 157
    background "#f7f0e4"
    padding (16, 16)

style character_panel_die_tile is frame:
    xfill True
    ysize 149
    background "#f7f0e4"
    padding (19, 16)

style character_panel_section_text is gui_text:
    size 32
    bold True
    color "#171513"

style character_panel_label_text is gui_text:
    size 24
    color "#6d6257"

style character_panel_value_text is gui_text:
    size 32
    color "#171513"

style character_panel_hint_text is gui_text:
    size 24
    color "#5c554e"

style character_panel_status_button is button:
    ysize 51
    background "#d9cdbb"
    hover_background "#eadfcc"
    padding (16, 0)

style character_panel_status_button_text is button_text:
    size 24
    color "#171513"
    hover_color "#000000"
    yalign 0.5

style character_panel_tooltip_frame is frame:
    xfill True
    background "#241f1adf"
    padding (16, 11)

style character_panel_tooltip_text is gui_text:
    size 24
    color "#f3eadb"

style rm_test_status_overlay_frame is frame:
    xpos 93
    ypos 373
    xsize 267
    ysize 533
    background "#eee7d8e8"
    padding (19, 16)

style rm_test_status_overlay_title_text is gui_text:
    size 27
    bold True
    color "#171513"

style rm_test_status_overlay_button is button:
    xsize 69
    ysize 59
    background "#f7f0e4"
    hover_background "#eadfcc"
    padding (3, 0)

style rm_test_status_overlay_button_text is button_text:
    size 13
    color "#171513"
    hover_color "#000000"
    xalign 0.5
    yalign 0.5

style rm_test_status_overlay_tooltip_frame is frame:
    xpos 387
    ypos 373
    xmaximum 693
    background "#241f1adf"
    padding (16, 11)

style rm_test_status_overlay_tooltip_text is gui_text:
    size 24
    color "#f3eadb"
