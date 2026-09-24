# The plate and pills share one centre; the shell/latch never rotate.
init -5 python:
    def rm_pillbox_get(name):
        return renpy.get_screen_variable(name, "medicine_panel")

    def rm_pillbox_set(name, value):
        renpy.set_screen_variable(name, value, "medicine_panel")

    def rm_pillbox_rotate(direction=0, slot=None):
        if rm_pillbox_get("busy") or rm_pillbox_get("repeat_confirmation"):
            return
        player = rm_ensure_player()
        step = player.current_rotation_step
        delta = direction if slot is None else rm_pillbox.shortest_turn(step, slot)
        if not delta:
            return
        rm_pillbox_set("angle_from", step * 45)
        rm_pillbox_set("angle_to", (step + delta) * 45)
        player.current_rotation_step = (step + delta) % 8
        rm_pillbox_set("busy", "rotate")
        rm_pillbox_set("message", "")

    def rm_pillbox_take(context, confirmed=False):
        if rm_pillbox_get("busy"):
            return
        player = rm_ensure_player()
        item = rm_pillbox.selection(player, context)
        result = rm_pillbox.take_selected(player, context, confirmed, rng=renpy.random)
        if result.get("reason") == "repeat_confirmation_required":
            rm_pillbox_set("repeat_confirmation", True)
            return
        rm_pillbox_set("repeat_confirmation", False)
        if result.get("available"):
            # Commit exactly once before presentation; a save/load never reapplies a dose.
            rm_pillbox_set("flying_drug", item["drug"])
            rm_pillbox_set("busy", "take")
            rm_pillbox_set("message", "已服用" + item["definition"]["display_name"])

    def rm_pillbox_finish(context, before, node):
        if rm_pillbox_get("busy") or rm_pillbox_get("repeat_confirmation"):
            return
        result = rm_pillbox.finish_session(rm_ensure_player(), context, before)
        if node:
            renpy.end_interaction(result)
        else:
            renpy.hide_screen("medicine_panel")
            renpy.restart_interaction()

transform rm_pillbox_appear:
    on show:
        alpha 0.0 zoom .975
        ease .25 alpha 1.0 zoom 1.0

transform rm_pillbox_turn(start_angle, end_angle):
    rotate_pad False
    rotate start_angle
    ease .22 rotate end_angle

transform rm_pillbox_swallow:
    xpos 510 ypos 783
    alpha 1.0 zoom 1.0
    ease .42 xpos 510 ypos 515 zoom .55 alpha 0.0

screen medicine_panel(context="manual", node=False):
    modal True
    zorder 200
    default busy = None
    default angle_from = 0
    default angle_to = 0
    default repeat_confirmation = False
    default flying_drug = None
    default message = ""
    default before = dict(rm_ensure_player().medicine_taken_today)
    $ player = rm_ensure_player()
    $ item = rm_pillbox.selection(player, context)
    $ unlocked = not busy and not repeat_confirmation
    key "game_menu" action If(repeat_confirmation, SetScreenVariable("repeat_confirmation", False), Function(rm_pillbox_finish, context, before, node))
    key "K_LEFT" action Function(rm_pillbox_rotate, -1)
    key "K_RIGHT" action Function(rm_pillbox_rotate, 1)
    if busy:
        timer (.22 if busy == "rotate" else .42) action SetScreenVariable("busy", None)

    add Solid("#0b0b0be8")
    text ({"morning":"晨间服药", "evening":"晚间服药", "manual":"药盒"}[context]):
        xalign .5 ypos 26
        style "rm_pillbox_caption"
    fixed:
        xysize (1020,1020)
        pos (1280,565) anchor (.5,.5)
        at rm_pillbox_appear
        add "gui/pillbox/pillbox_outer.png" xysize (1020,1020)
        if busy == "rotate":
            fixed:
                xysize (1020,1020) align (.5,.5)
                at rm_pillbox_turn(angle_from, angle_to)
                use rm_pillbox_tray(player, item, False, busy)
        else:
            fixed:
                xysize (1020,1020) align (.5,.5)
                at Transform(rotate=player.current_rotation_step*45, rotate_pad=False)
                use rm_pillbox_tray(player, item, unlocked, busy)
        add "gui/pillbox/pillbox_pointer.png" xysize (1020,1020)
        if busy == "take" and flying_drug:
            add rm_core.DRUG_DEFINITIONS[flying_drug]["sprite"]:
                xysize (118,118) fit "contain" anchor (.5,.5)
                at rm_pillbox_swallow

    textbutton "‹":
        id "pillbox_left"
        pos (565,485) xysize (150,160)
        style "rm_pillbox_arrow"
        sensitive unlocked
        action Function(rm_pillbox_rotate,-1)
        alt "向左旋转药盘"
    textbutton "›":
        id "pillbox_right"
        pos (1845,485) xysize (150,160)
        style "rm_pillbox_arrow"
        sensitive unlocked
        action Function(rm_pillbox_rotate,1)
        alt "向右旋转药盘"

    vbox:
        pos (1280,1085) xanchor .5 spacing 10
        hbox:
            xalign .5 spacing 22
            text (item["definition"]["display_name"] if item["definition"] else "空槽"):
                id "pillbox_name"
                style "rm_pillbox_name"
            if item["recommended"]:
                text "推荐" id "pillbox_recommended" style "rm_pillbox_caption" yalign .7
            if item["definition"] and item["definition"]["prn"]:
                text "按需" style "rm_pillbox_caption" yalign .7
        if item["definition"]:
            hbox:
                spacing 26 xalign .5
                text ("库存 %d" % item["count"] if item["count"] else "缺药"):
                    id "pillbox_stock"
                    style "rm_pillbox_caption"
                if item["definition"]["dose"] > 1:
                    text (("一次 %d 片" if item["count"] >= item["definition"]["dose"] else "不足一次剂量（需 %d 片）") % item["definition"]["dose"]) style "rm_pillbox_caption"
                if item["taken"]:
                    text "今日已服用" id "pillbox_taken" style "rm_pillbox_caption"
        else:
            text "未放置药物" style "rm_pillbox_caption" xalign .5

    button:
        id "pillbox_take"
        pos (1130,1218) xysize (300,76)
        style "rm_pillbox_button"
        sensitive unlocked and item["definition"] is not None and item["definition"]["enabled"] and item["count"] >= item["definition"]["dose"]
        action Function(rm_pillbox_take, context)
        text "服药" style "rm_pillbox_button_text"
    text message id "pillbox_message" xalign .5 ypos 1302 style "rm_pillbox_caption" size 25
    textbutton "完成":
        id "pillbox_finish"
        pos (1160,1350) xysize (240,65)
        style "rm_pillbox_finish"
        sensitive unlocked
        action Function(rm_pillbox_finish, context, before, node)

    if repeat_confirmation:
        # Screen-local confirmation: it cannot advance a called story node.
        button:
            xfill True yfill True background "#000b"
            action NullAction()
        frame:
            xysize (900,350) align (.5,.5)
            background "#f3f3ef" padding (58,46)
            vbox:
                spacing 22
                text "今天已经服用过这种药。\n还要再吃吗？" color "#141414" size 38 font rememorial_ui_font
                hbox:
                    spacing 32 xalign .5
                    textbutton "取消":
                        id "pillbox_cancel_repeat"
                        style "rm_pillbox_button"
                        action SetScreenVariable("repeat_confirmation", False)
                    textbutton "继续":
                        id "pillbox_confirm_repeat"
                        style "rm_pillbox_button"
                        action Function(rm_pillbox_take, context, True)

screen rm_pillbox_tray(player, item, enabled, busy):
    add "gui/pillbox/pillbox_inner.png" xysize (1020,1020)
    for slot, drug in enumerate(player.pillbox_slots):
        $ chosen = slot == item["slot"]
        $ definition = rm_core.DRUG_DEFINITIONS.get(drug)
        if definition and player.medicine_counts.get(drug,0) > 0 and not (chosen and busy == "take"):
            $ point = rm_pillbox.slot_position(slot, 273 if chosen else 280)
            add definition["sprite"]:
                pos point anchor (.5,.5)
                xysize (118,118) fit "contain"
                rotate (slot*45)
        imagebutton:
            id ("pillbox_slot_%d" % slot)
            idle Transform("gui/pillbox/slot_%d.png" % slot, alpha=0.0)
            hover Transform("gui/pillbox/slot_%d.png" % slot, alpha=.08)
            focus_mask ("gui/pillbox/slot_%d.png" % slot)
            sensitive enabled
            action Function(rm_pillbox_rotate, slot=slot)
            alt ("槽位 %d，%s" % (slot+1, definition["display_name"] if definition else "空槽"))

style rm_pillbox_name is gui_text:
    font rememorial_ui_font
    size 47
    color "#f3f3ef"
    outlines []
style rm_pillbox_caption is rm_pillbox_name:
    size 30
    color "#c8c8c3"
style rm_pillbox_button is button:
    background "#eaeae5"
    hover_background "#ffffff"
    insensitive_background "#383838"
    padding (42,10)
style rm_pillbox_button_text is rm_pillbox_name:
    color "#111111"
    insensitive_color "#888888"
    size 38
    align (.5,.5)
style rm_pillbox_finish is rm_pillbox_button:
    background None
    hover_background "#ffffff18"
    insensitive_background None
style rm_pillbox_finish_text is rm_pillbox_button_text:
    color "#eaeae5"
    size 32
style rm_pillbox_arrow is rm_pillbox_finish:
    padding (0,0)
style rm_pillbox_arrow_text is rm_pillbox_finish_text:
    size 100

label rm_medicine_node(context="morning"):
    call screen medicine_panel(context=context, node=True)
    return _return

label rm_pillbox_demo:
    $ rm_pillbox_demo_player = rm_player
    $ rm_player = rm_create_initial_character()
    $ rm_core.add_medicine_stock(rm_ensure_player(), "venlafaxine", 14)
    $ rm_core.add_medicine_stock(rm_ensure_player(), "trazodone", 12)
    $ rm_core.add_medicine_stock(rm_ensure_player(), "alprazolam", 5)
    $ rm_pillbox.set_prescription(rm_ensure_player(), rm_pillbox.INITIAL_SLOTS, rm_pillbox.INITIAL_RECOMMENDATIONS)
    call rm_medicine_node("morning")
    $ rm_player = rm_pillbox_demo_player
    return
