init python:
    ATTRIBUTE_DICE_TABS = (
        ("all", "全部骰子"),
        ("usable", "可用骰子"),
        ("str", "力量骰子"),
        ("dex", "灵巧骰子"),
        ("con", "体质骰子"),
        ("int", "智识骰子"),
        ("pow", "意志骰子"),
    )

    def attribute_toggle_die_selection(selected_die_ids, die_id, max_dice):
        selected = list(selected_die_ids or [])
        if die_id in selected:
            selected.remove(die_id)
        elif len(selected) < int(max_dice):
            selected.append(die_id)
        return selected

    def attribute_dice_options_for_tab(required_stat, tab, allowed_stats=None):
        options = list(get_attribute_check_dice_options(required_stat, allowed_stats))
        if tab == "all":
            return options
        if tab == "usable":
            return [die for die in options if die["selectable"]]
        return [die for die in options if die["stat"] == tab]

    def attribute_dice_selection_error(required_stat, selected_die_ids, min_dice=1, required_die_stats=None):
        selected = normalize_attribute_die_ids(selected_die_ids)
        if len(selected) < int(min_dice):
            return "至少需要选择{}颗骰子。".format(int(min_dice))
        if required_die_stats:
            character = rm_ensure_player()
            selected_stats = set()
            for die_id in selected:
                die = character.find_die(die_id)
                if die is not None:
                    selected_stats.add(die.attribute)
            for attribute in required_die_stats:
                if attribute not in selected_stats:
                    return "本次检定至少需要一颗【{}】骰子。".format(rm_core.ATTRIBUTE_LABELS.get(attribute, attribute))
        return ""


transform attribute_die_to_stage:
    alpha 0.0
    yoffset 190
    zoom 0.72
    rotate -16
    linear 0.18 alpha 1.0 yoffset 0 zoom 1.0 rotate 0
    easeout 0.10 yoffset -12 zoom 1.04
    easein 0.10 yoffset 0 zoom 1.0

transform attribute_die_roll_body:
    subpixel True
    rotate 0
    xoffset 0
    yoffset 0
    zoom 1.0
    linear 0.07 rotate 38 xoffset -34 yoffset -20 zoom 1.06
    linear 0.07 rotate -26 xoffset 28 yoffset 14 zoom 0.98
    linear 0.07 rotate 51 xoffset -20 yoffset -12 zoom 1.08
    linear 0.07 rotate -18 xoffset 24 yoffset 8 zoom 1.0
    repeat 5

transform attribute_die_land:
    subpixel True
    rotate -8
    yoffset -10
    zoom 1.16
    easeout 0.16 rotate 0 yoffset 0 zoom 1.0
    easeout 0.10 yoffset -4
    easein 0.08 yoffset 0

transform attribute_die_result_flash:
    alpha 0.0
    zoom 0.86
    linear 0.12 alpha 1.0 zoom 1.12
    easeout 0.14 zoom 1.0


screen attribute_die_entity(die_label, faces_text, face_text="?", active=True):
    $ die_label_color = "#edf5e9" if active else "#a6aea9"
    $ die_face_color = "#ffffff" if active else "#b6bdb8"
    $ die_faces_color = "#bcd0c0" if active else "#8e9691"

    frame:
        xsize 132
        ysize 132
        background (Frame("gui/ui_test_skin/dice_card.png", 34, 34) if rm_ui_test_skin_active else Solid("#edf5e9" if active else "#606964"))
        padding (8, 8, 8, 8)

        frame:
            xfill True
            yfill True
            background Solid("#32463a" if active else "#4c5550")
            padding (8, 8, 8, 8)

            vbox:
                xalign 0.5
                yalign 0.5
                spacing 4

                text die_label:
                    xalign 0.5
                    size 20
                    color die_label_color

                text face_text:
                    xalign 0.5
                    size 48
                    color die_face_color

                text faces_text:
                    xalign 0.5
                    size 15
                    color die_faces_color


screen attribute_dice_select(required_stat, min_dice=1, max_dice=3, requirement=6, check_kind=None, action_type="instant", allowed_stats=None, required_die_stats=None):
    modal True
    zorder 230
    default selected_die_ids = []
    default selected_tab = "usable"
    default confirm_open = False
    default invalid_open = False

    use rm_allow_game_menu
    use modal_dim_background

    $ selected_preview = preview_attribute_check(required_stat, selected_die_ids, allowed_stats) if selected_die_ids else None
    $ required_stat_label = rm_core.ATTRIBUTE_LABELS[required_stat]
    $ check_header = attribute_check_header(required_stat, requirement, action_type, check_kind)
    $ energy_cost = attribute_check_energy_cost(required_stat, selected_die_ids, action_type, allowed_stats, required_die_stats)
    $ required_selection_met = attribute_selection_meets_requirements(selected_die_ids, required_die_stats)
    $ invalid_reason = attribute_dice_selection_error(required_stat, selected_die_ids, min_dice, required_die_stats)

    frame:
        style "attribute_check_panel"

        vbox:
            spacing 12
            xfill True

            text "选择骰子" style "attribute_check_title"
            text "本次行动需要使用【[required_stat_label]】骰子。选中的骰子会被放到上方检定台。" style "attribute_check_body"

            frame:
                style "attribute_check_summary_frame"
                grid 4 1:
                    spacing 12
                    xfill True

                    vbox:
                        spacing 4
                        text "检定类型" style "attribute_check_summary_label"
                        text "[check_header['kind']]" style "attribute_check_summary_value"

                    vbox:
                        spacing 4
                        text "目标数值" style "attribute_check_summary_label"
                        text "[check_header['target']]" style "attribute_check_summary_value"

                    vbox:
                        spacing 4
                        text "属性固定值" style "attribute_check_summary_label"
                        text "[check_header['fixed']]" style "attribute_check_summary_value"

                    vbox:
                        spacing 4
                        text "至少还需要投出" style "attribute_check_summary_label"
                        text "[check_header['needed_roll']]" style "attribute_check_summary_value"

            frame:
                style "attribute_stage_frame"

                vbox:
                    xfill True
                    spacing 12

                    text "检定台" style "attribute_check_section_title"

                    fixed:
                        xfill True
                        ysize 180

                        if selected_preview:
                            add Solid("#8fb39a") xalign 0.5 yalign 0.78 xsize 260 ysize 16
                            hbox:
                                xalign 0.5
                                yalign 0.45
                                spacing 12
                                at attribute_die_to_stage
                                for selected_die in selected_preview["dice"]:
                                    use attribute_die_entity(selected_die["label"], format_die_faces(selected_die["faces"]), "?", True)
                        else:
                            frame:
                                xalign 0.5
                                yalign 0.5
                                xsize 300
                                ysize 118
                                background Solid("#1d2822")
                                padding (18, 14, 18, 14)

                                text "从下方选择 1-3 颗可用骰子" xalign 0.5 yalign 0.5 style "attribute_check_muted_text"

            text "骰子池" style "attribute_check_section_title"

            hbox:
                spacing 8
                xfill True

                for tab_id, tab_label in ATTRIBUTE_DICE_TABS:
                    textbutton tab_label:
                        style "attribute_check_tab_button"
                        selected selected_tab == tab_id
                        action SetScreenVariable("selected_tab", tab_id)

            vpgrid:
                cols 3
                spacing 14
                xfill True
                ymaximum 250
                mousewheel True
                draggable True

                for die in attribute_dice_options_for_tab(required_stat, selected_tab, allowed_stats):
                    $ selectable = die["selectable"]
                    $ selected = die["id"] in selected_die_ids

                    button:
                        xsize 292
                        ysize 122
                        padding (12, 10, 12, 10)
                        background (Frame("gui/ui_test_skin/dice_card.png", 34, 34) if rm_ui_test_skin_active else Solid("#dfe7dc" if selected else ("#eef5ef" if selectable else "#4e5652")))
                        hover_background (Frame("gui/ui_test_skin/dice_card.png", 34, 34) if rm_ui_test_skin_active and selectable else Solid("#d8eadb" if selectable else "#4e5652"))
                        sensitive selectable
                        action SetScreenVariable("selected_die_ids", attribute_toggle_die_selection(selected_die_ids, die["id"], max_dice))

                        hbox:
                            spacing 12
                            yalign 0.5

                            use attribute_die_entity(die["label"], format_die_faces(die["faces"]), "?", selectable)

                            vbox:
                                yalign 0.5
                                spacing 5

                                text die["label"] style ("attribute_check_die_text" if selectable else "attribute_check_die_disabled_text")
                                text format_die_faces(die["faces"]) style ("attribute_check_faces_text" if selectable else "attribute_check_faces_disabled_text")
                                if selectable:
                                    text ("已放入检定台" if selected else "可选择") style "attribute_check_hint_text"
                                else:
                                    text "本次不可用" style "attribute_check_disabled_hint_text"

            hbox:
                xalign 1.0
                spacing 14

                if rm_ui_test_skin_active:
                    textbutton "确认骰子":
                        style "rm_ui_test_prominent_button"
                        action If(len(selected_die_ids) >= min_dice and required_selection_met, [SetScreenVariable("invalid_open", False), SetScreenVariable("confirm_open", True)], [SetScreenVariable("confirm_open", False), SetScreenVariable("invalid_open", True)])
                else:
                    textbutton "确认骰子":
                        style "attribute_check_button"
                        action If(len(selected_die_ids) >= min_dice and required_selection_met, [SetScreenVariable("invalid_open", False), SetScreenVariable("confirm_open", True)], [SetScreenVariable("confirm_open", False), SetScreenVariable("invalid_open", True)])

    if confirm_open:
        button:
            style "attribute_check_confirm_dim"
            action NullAction()

        frame:
            style "attribute_check_confirm_modal"

            vbox:
                spacing 18
                xfill True

                text "确认检定" style "attribute_check_section_title"
                text "确认要花费[energy_cost]点精力使用当前骰子组合进行[check_header['kind']]（[check_header['action_type_label']]）的检定吗？" style "attribute_check_body"

                hbox:
                    xalign 1.0
                    spacing 14

                    if rm_ui_test_skin_active:
                        textbutton "取消":
                            style "rm_ui_test_option_button"
                            action SetScreenVariable("confirm_open", False)

                        textbutton "确认":
                            style "rm_ui_test_option_button"
                            action Return(selected_die_ids)
                    else:
                        textbutton "取消":
                            style "attribute_check_button"
                            action SetScreenVariable("confirm_open", False)

                        textbutton "确认":
                            style "attribute_check_button"
                            action Return(selected_die_ids)

    if invalid_open:
        button:
            style "attribute_check_confirm_dim"
            action SetScreenVariable("invalid_open", False)

            frame:
                style "attribute_check_confirm_modal"

                vbox:
                    spacing 18
                    xfill True

                    text "骰组不合法" style "attribute_check_section_title"
                    text "[invalid_reason]" style "attribute_check_body"
                    text "点击屏幕以重新选择。" style "attribute_check_invalid_hint"

    if rm_ui_test_skin_active:
        use rm_ui_test_close_button()


screen attribute_dice_confirm(required_stat, die_ids):
    modal True
    zorder 81
    $ preview = preview_attribute_check(required_stat, die_ids)

    use rm_allow_game_menu
    use modal_dim_background

    frame:
        style "attribute_check_panel"

        vbox:
            spacing 20
            xfill True

            text "确认检定" style "attribute_check_title"

            frame:
                style "attribute_stage_frame"

                hbox:
                    xfill True
                    spacing 32

                    fixed:
                        xsize 520
                        ysize 180
                        add Solid("#8fb39a") xalign 0.5 yalign 0.82 xsize 420 ysize 16
                        hbox:
                            xalign 0.5
                            yalign 0.43
                            spacing 12
                            for selected_die in preview["dice"]:
                                use attribute_die_entity(selected_die["label"], format_die_faces(selected_die["faces"]), "?", True)

                    vbox:
                        yalign 0.5
                        spacing 10

                        text "属性：[preview['stat_label']]" style "attribute_check_body"
                        text "当前值：[preview['stat_value']]  固定值：floor([preview['stat_value']] × 0.5) = [preview['stat_half']]" style "attribute_check_body"
                        text "确认后会进入投掷演出，并结算最终点数。" style "attribute_check_body"

            hbox:
                xalign 1.0
                spacing 14

                textbutton "返回选择":
                    style "attribute_check_button"
                    action Return(False)

                textbutton "进行检定":
                    style "attribute_check_button"
                    action Return(True)


screen attribute_check_roll_animation(result):
    modal True
    zorder 231
    default roll_finished = False

    use rm_allow_game_menu
    use modal_dim_background

    timer 1.32 action Return()

    frame:
        style "attribute_check_panel"

        vbox:
            spacing 20
            xfill True

            text "检定投掷" style "attribute_check_title"

            frame:
                style "attribute_stage_frame"

                fixed:
                    xfill True
                    ysize 310

                    add Solid("#8fb39a") xalign 0.5 yalign 0.74 xsize 520 ysize 18

                    if roll_finished and result["available"] and result["rolls"]:
                        frame:
                            background None
                            xalign 0.5
                            yalign 0.44
                            at attribute_die_land
                            use attribute_die_entity(result["die_label"], result["die_faces_text"], str(result["rolls"][0]), True)

                        text str(result["rolls"][0]):
                            xalign 0.5
                            yalign 0.08
                            size 72
                            color "#ffffff"
                            at attribute_die_result_flash
                    elif roll_finished:
                        frame:
                            background None
                            xalign 0.5
                            yalign 0.44
                            use attribute_die_entity(result["die_label"], result["die_faces_text"], "!", False)

                        text "本次没有完成掷骰":
                            xalign 0.5
                            yalign 0.10
                            size 34
                            color "#ffffff"
                    else:
                        frame:
                            background None
                            xalign 0.5
                            yalign 0.44
                            at attribute_die_roll_body
                            use attribute_die_entity(result["die_label"], result["die_faces_text"], "?", True)

                    text ("点数落定" if roll_finished else "骰子滚动中……") xalign 0.5 yalign 0.94 style "attribute_check_body"

            text "掷骰结束后将自动显示结果。" style "attribute_check_body"


screen attribute_check_result(result):
    modal True
    zorder 232

    use rm_allow_game_menu
    use modal_dim_background

    frame:
        style "attribute_check_panel"

        vbox:
            spacing 18
            xfill True

            text "检定结果" style "attribute_check_title"

            hbox:
                spacing 26
                xfill True

                use attribute_die_entity(result["die_label"], result["die_faces_text"], str(result["rolls"][0]) if result["rolls"] else "!", result["available"] and result["rolls"])

                vbox:
                    yalign 0.5
                    spacing 8

                    if result["available"] and result["rolls"]:
                        text "[result['stat_label']]检定：[result['stat_half']] + 骰组[result.get('dice_total', sum(result['rolls']))] + 修正[result['mood_modifier']] = [result['total']]" style "attribute_check_body"
                        text "目标值：[result['success_threshold']]  成功级别：[attribute_check_rank_label(result['rank'])]" style "attribute_check_body"
                    else:
                        text "本次没有完成掷骰：[result['reason']]" style "attribute_check_body"
                        text "目标值：[result['success_threshold']]  结果：无法执行" style "attribute_check_body"

            if rm_ui_test_skin_active:
                textbutton "继续":
                    xalign 1.0
                    style "rm_ui_test_prominent_button"
                    action Return()
            else:
                textbutton "继续":
                    xalign 1.0
                    style "attribute_check_button"
                    action Return()


style attribute_check_panel is frame:
    xalign 0.5
    yalign 0.5
    xsize 1536
    ysize 864
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/dice_check_panel.png", 90, 90), "True", Solid("#243029"))
    padding (28, 24, 28, 24)

style attribute_stage_frame is frame:
    xfill True
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/check_stage.png", 70, 24), "True", Solid("#18241d"))
    padding (22, 18, 22, 18)

style attribute_check_summary_frame is frame:
    xfill True
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/dice_list.png", 60, 34), "True", Solid("#18241d"))
    padding (16, 12, 16, 12)

style attribute_check_summary_label is text:
    size 18
    color "#93a99a"

style attribute_check_summary_value is text:
    size 24
    color "#f1f5ed"

style attribute_check_tab_button is button:
    xsize 148
    ysize 40
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/option_button.png", 40, 16), "True", Solid("#35443a"))
    hover_background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/option_button.png", 40, 16), "True", Solid("#425846"))
    selected_background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/option_button.png", 40, 16), "True", Solid("#dfe7dc"))
    padding (0, 0)

style attribute_check_tab_button_text is button_text:
    size 18
    color "#dce5db"
    hover_color "#ffffff"
    selected_color "#1f2b23"
    xalign 0.5
    yalign 0.5

style attribute_check_confirm_dim is button:
    xfill True
    yfill True
    background Solid("#00000099")
    hover_background Solid("#00000099")
    padding (0, 0)

style attribute_check_confirm_modal is frame:
    xalign 0.5
    yalign 0.5
    xsize 760
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/dice_list.png", 60, 34), "True", Solid("#101812f2"))
    padding (26, 22, 26, 22)

style attribute_check_invalid_hint is text:
    size 18
    color "#9fb0a4"
    xalign 0.5

style attribute_check_title is text:
    size 36
    color "#f1f5ed"

style attribute_check_section_title is text:
    size 25
    color "#cfe1d1"

style attribute_check_body is text:
    size 24
    color "#dce5db"
    line_spacing 4

style attribute_check_muted_text is text:
    size 23
    color "#83918a"

style attribute_check_die_text is text:
    size 24
    color "#1f2b23"

style attribute_check_faces_text is text:
    size 19
    color "#344238"

style attribute_check_hint_text is text:
    size 18
    color "#54775f"

style attribute_check_die_disabled_text is text:
    size 24
    color "#9ca49f"

style attribute_check_faces_disabled_text is text:
    size 19
    color "#858d88"

style attribute_check_disabled_hint_text is text:
    size 18
    color "#747d78"

style attribute_check_button is button:
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/option_button.png", 40, 16), "True", Solid("#35443a"))
    hover_background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/option_button.png", 40, 16), "True", Solid("#425846"))
    padding (20, 10, 20, 10)

style attribute_check_button_text is button_text:
    size 24
    color "#f3eadb"
    hover_color "#ffffff"
