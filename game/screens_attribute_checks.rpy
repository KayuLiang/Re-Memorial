init python:
    from collections import Counter
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



    def rm_check_die_label(die, faces=None):
        serial = next(i for i, item in enumerate(rm_ensure_player().dice_for(die.attribute), 1) if item.id == die.id)
        return "{} d{} · {:02d}".format(rm_core.ATTRIBUTE_LABELS[die.attribute],len(die.faces if faces is None else faces),serial)

    def rm_check_rows(result):
        core = result.get("_result")
        ids = core.dice_ids if core else result.get("die_ids", (result.get("die_id"),))
        values = [item["value"] for item in core.dice_results] if core else result.get("rolls", ())
        rows = []
        for index, value in enumerate(values):
            die = rm_ensure_player().find_die(ids[index]) if index < len(ids) else None
            entry = core.dice_results[index] if core else {}
            # Old saves predate face snapshots; only those use the live die.
            faces = tuple(entry.get("faces", die.faces if die else result.get("die_faces", ())))
            label = rm_check_die_label(die,faces) if die else "骰子 {}".format(index+1)
            attempts = entry.get("rolls", ())
            mode = entry.get("mode", "normal")
            attempts_text = " / ".join(str(v) for v in attempts) if len(attempts)>1 else ""
            if attempts_text:
                attempts_text += " · " + {"bonus":"取较高", "penalty":"取较低", "normal":"普通投掷"}[mode]
            rows.append(dict(die_id=entry.get('die_id',ids[index] if index<len(ids) else str(index)),label=label, value=value, faces=faces, attempts=attempts_text))
        return rows

    def rm_check_reason(reason):
        labels = dict(energy_shortage="精力不足", forced_energy_shortage="精力不足，强制行动按失败结算",
            no_usable_dice="没有可用骰子", no_usable_con_die="没有可用的体质骰子",
            attribute_dice_not_configured="尚未配置属性骰子", storm_blocks_outdoors="暴风雨阻止了户外行动",
            rain_blocks_outdoor_sport="当前降雨阻止了户外运动", weather_blocked="当前天气阻止了行动")
        if reason and reason.startswith("missing_required_die:"):
            return "缺少必需的{}骰子".format(rm_core.ATTRIBUTE_LABELS.get(reason.split(":")[1], ""))
        return labels.get(reason, reason or "未完成投掷")

    def rm_check_formula(preview, attribute):
        value = "骰面合计 × {:g}  +  {}贡献 {:g}".format(preview['dice_multiplier'], rm_core.ATTRIBUTE_LABELS[attribute], preview['attribute_modifier'])
        if preview['extra_modifier']:
            value += "  {:+g}".format(preview['extra_modifier'])
        if preview['final_multiplier'] != 1:
            value = "（{}）× {:g}".format(value, preview['final_multiplier'])
        return value + "  ≥  目标 {:g}".format(preview['target'])

    def rm_check_face_summary(faces):
        if len(faces) >= 8 and tuple(faces) == tuple(range(1,len(faces)+1)):
            return "1–{} · 各一面".format(len(faces))
        if len(faces) <= 6 or tuple(faces) == tuple(range(1,21)):
            return format_die_faces(faces)
        return " / ".join(str(value) if count == 1 else "{}×{}".format(value,count) for value,count in sorted(Counter(faces).items()))

screen attribute_dice_select(required_stat, min_dice=1, max_dice=3, requirement=6, check_kind=None, action_type="instant", allowed_stats=None, required_die_stats=None, thought=None):
    modal True
    zorder 230
    default selected_die_ids = []
    default selected_tab = "usable"
    default confirm_open = False
    default details_open = False
    default selection_table = RMRealtimeDice([],selection=True)
    use rm_allow_game_menu
    use modal_dim_background
    $ character = rm_ensure_player()
    $ allowed = _normal_attribute_tuple(allowed_stats, required_stat)
    $ spec = rm_core.CheckSpec(required_stat, requirement, selected_die_ids, action_type=action_type, max_dice=max_dice, min_dice=min_dice, allowed_dice_attributes=allowed, required_dice_attributes=tuple(required_die_stats or ()), is_late_night=character.current_time_slot in rm_core.TIME_SLOTS[6:])
    if action_type == rm_core.ACTION_WAKE:
        # This caller already passes the effective cap. Match perform_wake_check's
        # base spec so the mood reduction is applied exactly once.
        $ spec = rm_core.CheckSpec("pow", requirement, selected_die_ids, action_type=rm_core.ACTION_WAKE)
    $ preview = rm_dice_view.check_selection(character, spec, renpy.random)
    $ actual_ids = [die.id for die in preview['dice']]
    $ selection_table.sync([dict(die_id=die.id,faces=tuple(die.faces),value=die.faces[0]) for die in preview['dice']])
    $ check_header = attribute_check_header(required_stat, requirement, action_type, check_kind)
    $ invalid_reason = attribute_dice_selection_error(required_stat, actual_ids, min_dice, required_die_stats)
    $ options = attribute_dice_options_for_tab(required_stat, selected_tab, allowed_stats)
    $ can_confirm = not invalid_reason and not preview['reason']

    $ usable_count = len(attribute_dice_options_for_tab(required_stat, "usable", allowed_stats))
    fixed:
        align (.5,.5) xysize (2048,1360)
        frame:
            xysize (2048,1240) padding (56,36)
            background "#f3eee3"
            fixed:
                text check_header['kind'] style "attribute_check_title" id "check_title"
                text check_header['action_type_label'] style "attribute_check_muted_text" xalign 1.0 ypos 18
                add Solid("#b4aa96") ypos 76 xysize (1936,2)
                # Match the existing Fro avatar crop used by the phone.
                add Transform(Crop((1060,210,750,750), "images/sprites/fro/spr_fro_casual_default.png"), xysize=(160,160)) pos (0,92)
                add "gui/dice_obsidian/check-thought-tail.svg" pos (172,142)
                frame:
                    pos (198,100) xysize (1738,165) padding (28,16)
                    background "#e6dfd0"
                    vbox:
                        spacing 4
                        text "弗洛 · 心想" style "attribute_check_hint_text" size 24
                        text (thought or "（弗洛对现状的理解，文案待补充。）") style "attribute_check_body" size 30 xsize 1682 id "check_thought"
                text rm_check_formula(preview,required_stat):
                    id "check_formula"
                    style "attribute_check_section_title"
                    xalign .5 ypos 286
                    size 34
                vbox:
                    pos (0,388) xsize 440 spacing 10
                    text "当前组合成功率" style "attribute_check_hint_text"
                    text rm_dice_view.probability_text(preview['success_probability']) style "attribute_check_total" id "check_probability"
                    text ("含困难成功与大成功" if preview['success_probability'] is not None else ("精力不足，无法投掷" if preview['remaining'] < 0 else "选齐骰组后显示")) style "attribute_check_hint_text" size 24
                vbox:
                    pos (1570,388) xsize 366 spacing 14
                    text "本次精力" style "attribute_check_hint_text"
                    text ("消耗 {}".format(preview['cost'])) style "attribute_check_section_title" id "check_cost"
                    text (("投后剩余 {}".format(preview['remaining'])) if preview['remaining'] >= 0 else "还差 {} 精力".format(-preview['remaining'])):
                        style "attribute_check_body"
                        color ("#292923" if preview['remaining'] >= 0 else "#8b4436")
                        id "check_remaining"
                    text ("当前 {}".format(character.energy)) style "attribute_check_hint_text" size 24
                add selection_table pos (0,310) id "check_selection_table"
                if not preview['dice']:
                    text "从下方卡片选择骰子" style "attribute_check_hint_text" xalign .5 ypos 470
                for slot,selected_die in enumerate(preview['dice']):
                    button:
                        id ("check_slot_"+str(slot))
                        pos (int(968+(slot-(len(actual_ids)-1)/2)*280-112),350)
                        xysize (224,240) padding (0,0)
                        background None hover_background None
                        action (SetScreenVariable("selected_die_ids", attribute_toggle_die_selection(selected_die_ids,selected_die.id,preview['limit'])) if selected_die.id in selected_die_ids else NullAction())
                        fixed:
                            text rm_check_die_label(selected_die) style "attribute_check_body" size 24 xalign .5 ypos 172
                            text ("点击移除" if selected_die.id in selected_die_ids else "枷锁联动加入") style "attribute_check_hint_text" size 22 color "#eee8d8" xalign .5 ypos 210
                hbox:
                    ypos 628 spacing 46
                    text ("可用 {}".format(usable_count)) style "attribute_check_body"
                    text ("已选 {} / {}".format(len(actual_ids),preview['limit'])) style "attribute_check_body" id "check_selected_count"
                text ("可用属性："+"、".join(rm_core.ATTRIBUTE_LABELS[a] for a in allowed)) style "attribute_check_hint_text" xpos 520 ypos 632 xsize 610
                textbutton "骰面与规则详情":
                    id "check_details"
                    style "attribute_check_tab_button"
                    xalign 1.0 ypos 612 xsize 360
                    action SetScreenVariable("details_open", True)
                add Solid("#b4aa96") ypos 676 xysize (1936,2)
                hbox:
                    ypos 686 spacing 10
                    for tab_id, tab_label in ATTRIBUTE_DICE_TABS:
                        textbutton tab_label.replace("骰子", ""):
                            id ("check_tab_"+tab_id)
                            style "attribute_check_tab_button"
                            xsize 268
                            selected selected_tab == tab_id
                            action SetScreenVariable("selected_tab", tab_id)
                vpgrid:
                    id "check_pool"
                    ypos 754 xalign .5 xysize (min(6,max(1,len(options)))*288+min(6,max(1,len(options)))*24,414)
                    cols min(6,max(1,len(options))) spacing 24
                    mousewheel True draggable True
                    scrollbars "vertical"
                    vscrollbar_xsize 10
                    vscrollbar_base_bar "#dfd7c8"
                    vscrollbar_thumb "#9c8d70"
                    vscrollbar_hover_thumb "#6c6048"
                    vscrollbar_unscrollable "hide"
                    for die in options:
                        $ chosen = die['id'] in actual_ids
                        $ manual_choice = die['id'] in selected_die_ids
                        $ clickable = die['selectable'] and (manual_choice or (not chosen and len(actual_ids) < preview['limit']))
                        $ change = rm_dice_view.check_selection_change(character, spec, renpy.random, die['id']) if clickable else None
                        button:
                            id ("check_die_"+die['id'])
                            style "attribute_check_choice"
                            padding (20,12) xysize (288,402)
                            background Transform("gui/dice_obsidian/card-stock-approved.png",xysize=(288,402))
                            hover_background Transform("gui/dice_obsidian/card-stock-approved.png",xysize=(288,402),matrixcolor=BrightnessMatrix(.10))
                            selected_background Transform("gui/dice_obsidian/card-stock-approved.png",xysize=(288,402),matrixcolor=BrightnessMatrix(.06))
                            selected_hover_background Transform("gui/dice_obsidian/card-stock-approved.png",xysize=(288,402),matrixcolor=BrightnessMatrix(.14))
                            insensitive_background Transform("gui/dice_obsidian/card-stock-approved.png",xysize=(288,402),matrixcolor=SaturationMatrix(0))
                            selected chosen
                            sensitive clickable and not confirm_open and not details_open
                            action SetScreenVariable("selected_die_ids", attribute_toggle_die_selection(selected_die_ids, die['id'], preview['limit']))
                            fixed:
                                text rm_check_die_label(character.find_die(die['id'])) style "attribute_check_body" size 26 color "#f0ede4" xalign .5
                                text (("已选" if manual_choice else "联动") if chosen else (("已满" if len(actual_ids) >= preview['limit'] else "可选") if die['selectable'] else ("封印" if character.find_die(die['id']).is_sealed() else "属性不符"))) style "attribute_check_hint_text" size 20 color "#ead09a" xalign 1.0 ypos 36
                                text rm_core.enchantment_label(character.find_die(die['id']).enchantment) style "attribute_check_hint_text" size 20 color "#c6b98f" ypos 36
                                add rm_live_thumbnail(die['faces'],size=192) xalign .5 ypos 68
                                text rm_check_face_summary(die['faces']) style "attribute_check_faces_text" size 20 line_spacing 0 color "#eee4ce" xsize 248 text_align .5 ypos 244
                                text (rm_dice_view.check_change_text(preview,change,manual_choice).replace(" · ","\n") if change else ("自动参与骰组" if chosen else ("先移除一颗已选骰" if die['selectable'] else "本次不可选"))):
                                    style "attribute_check_hint_text"
                                    size 20 line_spacing 0 color "#ead09a" xsize 248 text_align .5 ypos 306
                if not options:
                    text "此分类没有骰子，请切换上方分类。" style "attribute_check_muted_text" xalign .5 ypos 898
        textbutton "取消":
            id "check_back"
            style "attribute_check_button"
            ypos 1272 xsize 420
            action Return("__rm_check_cancel__")
        textbutton "确认":
            id "check_review"
            style "attribute_check_button"
            xpos 1628 ypos 1272 xsize 420
            sensitive can_confirm and not confirm_open and not details_open
            action [Function(selection_table.finish_snap),SetScreenVariable("confirm_open", True)]
        text (invalid_reason or (rm_check_reason(preview['reason']) if preview['reason'] else "点击上方骰子可移除；确认后进入投掷。")):
            style "attribute_check_hint_text"
            color "#f3eee3"
            xalign .5 ypos 1284 xsize 1120 text_align .5
    if confirm_open:
        key "game_menu" action SetScreenVariable("confirm_open", False)
        button:
            style "attribute_check_confirm_dim"
            action SetScreenVariable("confirm_open", False)
        frame:
            style "attribute_check_confirm_modal"
            vbox:
                spacing 28 xfill True
                text "确认检定" style "attribute_check_title"
                text ("参与骰组："+"、".join(rm_check_die_label(die) for die in preview['dice'])) style "attribute_check_body"
                text ("目标 {}  ·  成功率 {}".format(preview['target'], rm_dice_view.probability_text(preview['success_probability']))) style "attribute_check_section_title"
                text ("消耗精力 {}  ·  投后剩余 {}".format(preview['cost'], preview['remaining'])) style "attribute_check_body"
                text "取消可继续调整骰组。" style "attribute_check_muted_text"
                hbox:
                    xalign 1.0 spacing 24
                    textbutton "取消" id "check_cancel" style "attribute_check_button" action SetScreenVariable("confirm_open", False)
                    textbutton "确认" id "check_confirm" style "attribute_check_button" action Return(actual_ids)
    if details_open:
        key "game_menu" action SetScreenVariable("details_open", False)
        button:
            style "attribute_check_confirm_dim"
            action SetScreenVariable("details_open", False)
        frame:
            style "attribute_check_confirm_modal"
            xsize 1500
            vbox:
                spacing 22 xfill True
                text "骰面与规则" style "attribute_check_title"
                text "成功率按实际骰面和当前修正计算，包含所有成功等级。" style "attribute_check_hint_text"
                viewport:
                    ysize 650 mousewheel True draggable True
                    scrollbars "vertical"
                    vscrollbar_xsize 10
                    vscrollbar_base_bar "#dfd7c8"
                    vscrollbar_thumb "#9c8d70"
                    vscrollbar_hover_thumb "#6c6048"
                    vscrollbar_unscrollable "hide"
                    vbox:
                        xsize 1340 spacing 20
                        text rm_check_formula(preview, required_stat) style "attribute_check_body"
                        if preview['total_range']:
                            text ("最终值范围 {:g}–{:g} · 失败率 {}".format(*preview['total_range'],rm_dice_view.probability_text(1-preview['success_probability']))) style "attribute_check_body"
                        text ("心境：{} · 骰面倍率 ×{:g}".format(rm_core.mood_label(rm_core.mood_state(character)),preview['dice_multiplier'])) style "attribute_check_body"
                        text ("奖励来源 {} / 惩罚来源 {} · 抵消后逐次重投；奖励可选目标，惩罚随机。".format(preview['advantage'],preview['disadvantage'])) style "attribute_check_hint_text"
                        for factor in rm_dice_view.check_factor_details(character,spec,len(actual_ids)):
                            text factor style "attribute_check_hint_text"
                        if preview['dice']:
                            for index, selected_die in enumerate(preview['dice']):
                                frame:
                                    background "#e6dfd0" padding (24,18) xfill True
                                    vbox:
                                        spacing 6
                                        text (rm_check_die_label(selected_die)+" · "+rm_core.enchantment_label(selected_die.enchantment)) style "attribute_check_body"
                                        text ("骰面："+format_die_faces(selected_die.faces)) style "attribute_check_hint_text" xsize 1240
                                        text ({'normal':'投一次，采用该点数','bonus':'投两次，取较高点数','penalty':'投两次，取较低点数'}[preview['modes'][index]]) style "attribute_check_hint_text"
                        else:
                            text "先选骰子，再查看本次骰面的投掷规则。" style "attribute_check_hint_text"
                        text "重复的面值会分别计入概率；更换骰组后，概率与精力同步更新。" style "attribute_check_hint_text"
                textbutton "返回选骰":
                    id "check_details_close"
                    style "attribute_check_button"
                    xalign 1.0
                    action SetScreenVariable("details_open", False)
    if rm_ui_test_skin_active:
        use rm_ui_test_close_button()

screen attribute_check_choose_bonus_dice(dice_ids, count):
    modal True
    zorder 230
    default chosen = []
    use rm_allow_game_menu
    use modal_dim_background
    frame:
        style "attribute_check_confirm_modal"
        align (.5, .5)
        xsize 900
        vbox:
            spacing 22
            text "选择奖励骰重投目标" style "attribute_check_title"
            text "每个奖励骰重投一颗已投入骰并取较高点数；可重复选择同一颗。" style "attribute_check_body"
            text "已选择 [len(chosen)] / [count]" style "attribute_check_section_title"
            if len(chosen) < count:
                for die_id in dice_ids:
                    $ die = rm_ensure_player().find_die(die_id)
                    if die is not None:
                        textbutton rm_check_die_label(die):
                            style "attribute_check_button"
                            action SetScreenVariable("chosen", chosen + [die_id])
            else:
                textbutton "开始投骰":
                    style "attribute_check_button"
                    action Return(chosen)

screen attribute_check_roll_animation(result):
    modal True
    zorder 231
    default roll_table = RMRealtimeDice(rm_check_rows(result))
    use rm_allow_game_menu
    use modal_dim_background
    $ rows = rm_check_rows(result)
    $ phase = roll_table.world['phase']
    $ roll_finished = phase == "settled"
    if phase == "ready" and rows:
        key "K_SPACE" action Function(roll_table.launch)
    frame:
        style "attribute_check_panel"
        xysize (2048,1240) padding (56,36) yoffset -60
        fixed:
            text ("点数落定" if roll_finished else "掷出骰子") style "attribute_check_title"
            text ("目标 {:g}".format(result['success_threshold'])) style "attribute_check_section_title" xalign 1.0 ypos 10
            text ({'ready':'按住桌面，向想投出的方向拖拽后松手；也可以点击掷骰。','rolling':'骰子正在翻滚……','settled':'点数已落定，确认后查看完整结算。'}[phase]) style "attribute_check_hint_text" ypos 82
            if rows:
                add roll_table pos (0,145) id "check_roll_table"
                hbox:
                    xalign .5 ypos 854 spacing 60
                    for index,row in enumerate(rows):
                        vbox:
                            id ("check_roll_die_"+str(index))
                            xsize 560 spacing 8
                            text (row['label']+(("  ·  "+str(row['value'])) if roll_finished else "")) style "attribute_check_section_title" xalign .5
                            if roll_finished and row['attempts']:
                                text ("投出 "+row['attempts']) style "attribute_check_hint_text" xalign .5 size 26
            else:
                text rm_check_reason(result.get('reason')) style "attribute_check_section_title" align (.5,.5)
            add Solid("#b4aa96") ypos 958 xysize (1936,2)
            text ("拖拽方向与距离决定投掷轨迹" if phase == 'ready' else "本次投掷已确认") style "attribute_check_hint_text" ypos 1002
            textbutton ("查看结果" if roll_finished or not rows else ("掷出骰子" if phase == 'ready' else "骰子滚动中")):
                id "check_roll_action"
                style "attribute_check_button"
                xpos 1516 ypos 984 xsize 420
                sensitive phase != 'rolling'
                action (Return() if roll_finished or not rows else Function(roll_table.launch))

screen attribute_check_result(result):
    modal True
    zorder 232
    use rm_allow_game_menu
    use modal_dim_background
    $ core = result.get('_result')
    $ rows = rm_check_rows(result)
    $ completed = result.get('available', False)
    frame:
        style "attribute_check_panel"
        fixed:
            text "检定结果" style "attribute_check_title"
            add Solid("#b4aa96") ypos 88 xysize (1936,2)
            vbox:
                xpos 0 ypos 138 spacing 28 xsize 1080
                text (attribute_check_rank_label(result['rank']) if completed else "无法执行") style "attribute_check_total" id "check_rank"
                if rows:
                    text ("最终值 {:g}  /  目标 {:g}".format(result['total'], result['success_threshold'])) style "attribute_check_title"
                    text "各骰落点" style "attribute_check_section_title"
                    for index, row in enumerate(rows):
                        frame:
                            id ("check_result_die_"+str(index))
                            background "#e6dfd0" padding (24,16) xsize 1080
                            fixed:
                                ysize 56
                                text row['label'] style "attribute_check_body" xsize 360
                                text str(row['value']) style "attribute_check_section_title" xpos 390
                                if row['attempts']:
                                    text ("投出 "+row['attempts']) style "attribute_check_muted_text" xpos 580
                else:
                    text rm_check_reason(result.get('reason')) style "attribute_check_body"
            add Solid("#b4aa96") xpos 1192 ypos 138 xysize (1,740)
            vbox:
                xpos 1232 ypos 146 spacing 28 xsize 704
                text "结算明细" style "attribute_check_section_title"
                if rows:
                    text ("属性贡献  {:g}".format(result['stat_half'])) style "attribute_check_body"
                    text ("骰组点数  {:g}".format(core.dice_total if core else result.get('dice_total', sum(result['rolls'])))) style "attribute_check_body"
                    if core:
                        text ("骰组倍率  ×{:g}".format(core.dice_multiplier)) style "attribute_check_body"
                    text ("额外修正  {:+g}".format(result['mood_modifier'])) style "attribute_check_body"
                    if core:
                        text ("总值倍率  ×{:g}".format(getattr(core, 'final_multiplier', 1.0))) style "attribute_check_body"
                if core:
                    text ("精力成本  {}".format(core.energy_cost if core.available else 0)) style "attribute_check_section_title"
                text "继续后回到当前行动，查看后续结果。" style "attribute_check_muted_text"
            add Solid("#b4aa96") ypos 958 xysize (1936,2)
            textbutton "继续":
                id "check_continue"
                style "attribute_check_button"
                xpos 1516 ypos 984 xsize 420
                action Return()

style attribute_check_panel is frame:
    align (.5,.5)
    xysize (2048,1152)
    background "#f3eee3"
    padding (56,48)
style attribute_check_title is gui_text:
    font rememorial_ui_font
    size 52
    color "#292923"
    bold False
    outlines []
style attribute_check_total is attribute_check_title:
    size 92
style attribute_check_section_title is attribute_check_title:
    size 38
style attribute_check_body is attribute_check_title:
    size 32
    line_spacing 6
style attribute_check_muted_text is attribute_check_body:
    color "#625b50"
style attribute_check_hint_text is attribute_check_muted_text:
    size 28
style attribute_check_faces_text is attribute_check_body:
    size 26
style attribute_check_notice is attribute_check_body:
    color "#8b4436"
style attribute_check_button is button:
    background "#393c32"
    hover_background "#6c6048"
    insensitive_background "#d9d2c4"
    padding (28,18)
    keyboard_focus True
style attribute_check_button_text is attribute_check_body:
    color "#f3eee3"
    hover_color "#ffffff"
    insensitive_color "#81796c"
    align (.5,.5)
style attribute_check_tab_button is attribute_check_button:
    xsize 155
    padding (0,14)
    background "#e6dfd0"
    hover_background "#d4c7af"
    selected_background "#393c32"
style attribute_check_tab_button_text is attribute_check_body:
    size 28
    color "#292923"
    selected_color "#f3eee3"
    align (.5,.5)
style attribute_check_choice is button:
    background "#e6dfd0"
    hover_background "#ddd0b7"
    selected_background "#c9bb9e"
    selected_hover_background "#bfae89"
    insensitive_background "#eee9df"
    padding (24,18)
    keyboard_focus True
style attribute_check_die_frame is frame:
    background "#e6dfd0"
    padding (36,48)
    xysize (480,340)
style attribute_check_confirm_dim is button:
    xfill True
    yfill True
    background "#292923aa"
    hover_background "#292923aa"
    padding (0,0)
style attribute_check_confirm_modal is frame:
    align (.5,.5)
    xsize 1200
    background "#f3eee3"
    padding (56,48)
