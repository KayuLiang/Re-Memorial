# 病例 — approved paper/index layout, at the project's native 2560 × 1440.
default rm_case_history = {}
default rm_case_owner = None
default rm_case_snapshot = None

init -10 python:
    import math
    from game.systems import rm_case

    RM_CASE_PAPER = "#eee9dd"
    RM_CASE_INK = "#22241f"
    RM_CASE_RULE = "#858477"
    RM_CASE_RED = "#b7624d"
    RM_CASE_TABS = (("summary", "概览"), ("attributes", "属性"), ("statuses", "状态"), ("skills", "技能"), ("spells", "法术"))

    def rm_case_sync():
        player = getattr(store, "rm_player", None)
        if player is None or renpy.predicting():
            return
        if store.rm_case_owner is not player:
            store.rm_case_owner = player
            store.rm_case_history = {}
        snapshot = rm_case.snapshot(player, getattr(store, "story_hud_effects", []))
        history = rm_case.remember(store.rm_case_history, snapshot["statuses"])
        if history != store.rm_case_history:
            store.rm_case_history = history
        if snapshot != store.rm_case_snapshot:
            store.rm_case_snapshot = snapshot

    # Interaction boundary, not screen evaluation. Assign new store values so
    # the archive participates in normal save/load and rollback.
    config.interact_callbacks.append(rm_case_sync)

    def rm_case_icon(attribute, size=130, light=False):
        crops = {"str": (12, 200, 303, 326), "dex": (316, 224, 306, 302),
                 "con": (636, 234, 266, 281), "int": (921, 219, 291, 311),
                 "pow": (1224, 226, 300, 290)}
        r, g, b = Color(RM_CASE_PAPER if light else RM_CASE_INK).rgb
        # Convert the approved black-on-white atlas into a tinted ink mask.
        # Premultiplied RGB and alpha all use (1 - luminance).
        matrix = Matrix([-r, 0, 0, r, -g, 0, 0, g, -b, 0, 0, b, -1, 0, 0, 1])
        return Transform(Crop(crops[attribute], "gui/case/attribute_atlas.png"),
                         xysize=(size, size), fit="contain", matrixcolor=matrix)

    class RMCaseMark(renpy.Displayable):
        def __init__(self, kind="close", color=RM_CASE_INK, **kwargs):
            super(RMCaseMark, self).__init__(**kwargs)
            self.kind, self.color = kind, color

        def render(self, width, height, st, at):
            result = renpy.Render(64, 64)
            canvas = result.canvas()
            if self.kind == "close":
                canvas.line(self.color, (12, 12), (52, 52), 15)
                canvas.line(self.color, (12, 52), (52, 12), 15)
            else:
                points = [(22, 10), (44, 32), (22, 54)]
                if self.kind == "back":
                    points = [(64 - x, y) for x, y in points]
                canvas.lines(self.color, False, points, 12)
            return result

    class RMCaseRadar(renpy.Displayable):
        def __init__(self, fractions, **kwargs):
            super(RMCaseRadar, self).__init__(**kwargs)
            self.fractions = fractions

        def render(self, width, height, st, at):
            result = renpy.Render(780, 650)
            canvas = result.canvas()
            center, radius = (390, 330), 268
            def point(i, fraction):
                angle = -math.pi / 2 + i * 2 * math.pi / 5
                return (int(center[0] + radius * fraction * math.cos(angle)),
                        int(center[1] + radius * fraction * math.sin(angle)))
            for fraction in (.25, .5, .75, 1):
                canvas.polygon("#aaa79a", [point(i, fraction) for i in range(5)], 2)
            for i in range(5):
                canvas.line("#aaa79a", center, point(i, 1), 2)
            points = [point(i, self.fractions[i]) for i in range(5)]
            canvas.polygon("#74706566", points)
            canvas.polygon(RM_CASE_INK, points, 4)
            for point_xy in points:
                canvas.circle(RM_CASE_INK, point_xy, 7)
            return result

transform rm_case_slip(angle):
    rotate angle
    rotate_pad False

screen rm_case_content(tab, attribute, filter_key, selected_status, page):
    style_prefix "rm_case"
    $ data = rm_case_snapshot
    add Solid(RM_CASE_PAPER)
    # Quiet paper edge: no photographic texture or unrelated ornament.
    add Solid("#ded8ca") xpos 2526 xsize 34
    add Solid("#e6e0d3") xpos 2515 xsize 11
    add Solid(RM_CASE_INK) xsize 294

    text "病\n例" xpos 70 ypos 56 size 148 line_spacing -64 color RM_CASE_PAPER
    for index, (key, label) in enumerate(RM_CASE_TABS):
        button:
            id ("case_tab_" + key)
            xpos 34 ypos (424 + index * 140) xysize (260, 124)
            background (RM_CASE_PAPER if tab == key else None)
            hover_background (RM_CASE_PAPER if tab == key else "#383a32")
            action [SetScreenVariable("panel_tab", key), SetScreenVariable("case_page", 0)]
            if tab == key:
                add Solid(RM_CASE_RED) xsize 16
            text label xalign .5 yalign .5 size 60 color (RM_CASE_INK if tab == key else RM_CASE_PAPER)

    add Solid("#cbc7bc") xpos 58 ypos 1249 xysize (192, 2)
    button:
        id "case_back"
        xpos 45 ypos 1280 xysize (226, 90)
        action Hide("character_panel")
        add RMCaseMark("back", RM_CASE_PAPER) yalign .5
        text "返回" xpos 78 yalign .5 size 49 color RM_CASE_PAPER
    button:
        id "case_close"
        alt "关闭病例"
        xpos 2380 ypos 24 xysize (110, 100)
        action Hide("character_panel")
        add RMCaseMark() align (.5, .5)

    if data:
        if tab == "summary":
            use rm_case_overview(data)
        elif tab == "attributes":
            use rm_case_attributes(data, attribute)
        elif tab == "statuses":
            use rm_case_statuses(data, filter_key, selected_status, page)
        else:
            text ("技能" if tab == "skills" else "法术") xpos 362 ypos 98 size 180
            add Solid(RM_CASE_RULE) xpos 366 ypos 386 xysize (2034, 2)
            text "暂无内容" id "case_empty" xpos 366 ypos 484 size 48 color "#767467"

screen rm_case_overview(data):
    style_prefix "rm_case"
    # Use the original transparent sprite, without a duplicate shadow layer.
    viewport:
        xpos 294 ypos 0 xysize (1141, 1440)
        add "images/sprites/fro/spr_fro_casual_default.png":
            xpos 166 ypos -44 zoom .57
    text "弗洛" xpos 364 ypos 100 size 188
    add Solid(RM_CASE_INK) xpos 368 ypos 368 xysize (75, 4)
    text "概览" xpos 366 ypos 396 size 72
    text "Mood" xpos 368 ypos 603 size 37
    text "[data['mood']['value']]" xpos 366 ypos 638 size 87
    text "[data['mood']['label']]" xpos (366 + max(120, len(str(data['mood']['value'])) * 43 + 20)) ypos 678 size 43
    text "精力" xpos 368 ypos 795 size 43
    text "[data['energy']['current']]/[data['energy']['maximum']]" xpos 366 ypos 844 size 79
    add Solid(RM_CASE_RULE) xpos 1435 ypos 156 xysize (2, 1170)

    button:
        id "case_radar"
        xpos 1518 ypos 141 xysize (920, 750)
        action [SetScreenVariable("panel_tab", "attributes"), SetScreenVariable("case_attribute", "str")]
        text "属性" size 72
        add Solid(RM_CASE_RULE) xpos 194 ypos 59 xysize (640, 2)
        add RMCaseMark("next") xpos 850 ypos 15
        add RMCaseRadar(rm_case.radar_fractions(data['attributes'])) xpos 50 ypos 103
        text "力量" pos (440, 116) xanchor .5 size 42
        text "敏捷" pos (830, 353) xanchor .5 size 42
        text "体质" pos (662, 666) xanchor .5 size 42
        text "智力" pos (194, 666) xanchor .5 size 42
        text "意志" pos (57, 353) xanchor .5 size 42

    add Solid(RM_CASE_RULE) xpos 1518 ypos 929 xysize (920, 2)
    button:
        id "case_status_link"
        xpos 1518 ypos 960 xysize (920, 90)
        action [SetScreenVariable("panel_tab", "statuses"), SetScreenVariable("case_filter", "owned"), SetScreenVariable("case_page", 0)]
        text "状态" size 67
        add Solid(RM_CASE_RULE) xpos 155 ypos 46 xysize (679, 2)
        add RMCaseMark("next") xpos 850 ypos 10
    $ statuses = data['statuses']
    $ offsets = ((235, 0, -8), (25, 90, 7), (380, 175, -10))
    for index, status in enumerate(statuses[:3]):
        $ dx, dy, angle = offsets[index]
        button:
            id ("case_slip_" + str(index))
            xpos (1580 + dx) ypos (1035 + dy)
            xsize min(520, max(300, len(status['label']) * 42 + 70)) ysize 75
            at rm_case_slip(angle)
            background Solid("#b3aea0")
            hover_background Solid(RM_CASE_RED)
            padding (2, 2)
            action [SetScreenVariable("panel_tab", "statuses"), SetScreenVariable("case_filter", "owned"), SetScreenVariable("case_status", status['id']), SetScreenVariable("case_page", 0)]
            frame:
                background Solid("#f6f2e8")
                padding (16, 5)
                xfill True yfill True
                text (status['label'] if len(status['label']) <= 11 else status['label'][:10] + "…") size 42 align (.5, .5)
    if not statuses:
        text "暂无状态" xpos 1580 ypos 1100 size 42 color "#767467"
    elif len(statuses) > 3:
        text ("共 %d 项 · 点击“状态”查看全部" % len(statuses)) xpos 1518 ypos 1390 size 25

screen rm_case_attributes(data, selected_attribute):
    style_prefix "rm_case"
    text "属性" xpos 362 ypos 98 size 180
    add Solid(RM_CASE_INK) xpos 366 ypos 345 xysize (65, 4)
    text "弗洛" xpos 366 ypos 374 size 62
    add Solid(RM_CASE_RULE) xpos 1494 ypos 153 xysize (2, 1175)

    for index, key in enumerate(rm_case.ATTRIBUTES):
        $ row = data['attributes'][key]
        $ chosen = key == selected_attribute
        button:
            id ("case_attribute_" + key)
            xpos 350 ypos (484 + index * 171) xysize (1096, 163)
            background (RM_CASE_INK if chosen else None)
            hover_background (RM_CASE_INK if chosen else "#e0dacc")
            action SetScreenVariable("case_attribute", key)
            if chosen:
                add Solid(RM_CASE_RED) xsize 20
            else:
                add Solid(RM_CASE_RULE) ypos 162 xysize (1096, 1)
            add rm_case_icon(key, 130, chosen) xpos 58 yalign .5
            text rm_case.LABELS[key] xpos 270 yalign .5 size 69 color (RM_CASE_PAPER if chosen else RM_CASE_INK)
            text str(row['current']) xpos 1030 xanchor 1.0 yalign .5 size 89 color (RM_CASE_PAPER if chosen else RM_CASE_INK)

    $ selected = data['attributes'][selected_attribute]
    add rm_case_icon(selected_attribute, 196) xpos 1555 ypos 165
    text rm_case.LABELS[selected_attribute] xpos 1782 ypos 192 size 125
    add Solid(RM_CASE_RULE) xpos 1560 ypos 386 xysize (892, 2)
    text "左侧数值由基础值、属性加值与临时加成相加。" xpos 1560 ypos 422 xsize 892 size 36

    $ details = (("基础值", selected['formal']), ("属性加值", selected['value']), ("临时加成", selected['bonus']), ("生效上限", 20))
    for index, (label, number) in enumerate(details):
        fixed:
            xpos 1560 ypos (484 + index * 171) xysize (892, 163)
            text label xpos 12 yalign .5 size 48
            text str(number) xpos 868 xanchor 1.0 yalign .5 size 55
            add Solid(RM_CASE_RULE) ypos 162 xysize (892, 1)

screen rm_case_statuses(data, filter_key, selected_status, page):
    style_prefix "rm_case"
    text "状态" xpos 362 ypos 98 size 180
    for index, (key, label) in enumerate(rm_case.FILTERS):
        button:
            id ("case_filter_" + key)
            xpos (352 + index * 310) ypos 295 xysize (292, 99)
            action [SetScreenVariable("case_filter", key), SetScreenVariable("case_page", 0), SetScreenVariable("case_status", None)]
            text label align (.5, .45) size 49
            if key == filter_key:
                add Solid(RM_CASE_INK) ypos 91 xysize (272, 8)
                add Solid(RM_CASE_RED) ypos 91 xysize (18, 8)
    add Solid(RM_CASE_RULE) xpos 352 ypos 396 xysize (1220, 2)
    add Solid(RM_CASE_RULE) xpos 1638 ypos 301 xysize (2, 1045)
    $ rows = rm_case.dictionary_rows(data['statuses'], rm_case_history, filter_key)
    $ visible, actual_page, count = rm_case.page_rows(rows, page)
    $ detail = next((row for row in visible if row['id'] == selected_status), visible[0] if visible else None)
    for index, row in enumerate(visible):
        $ chosen = detail and row['id'] == detail['id']
        button:
            id ("case_status_row_" + str(index))
            xpos (352 + (index % 2) * 630) ypos (454 + (index // 2) * 151) xysize (590, 132)
            background (RM_CASE_INK if chosen else None)
            hover_background (RM_CASE_INK if chosen else "#e0dacc")
            action SetScreenVariable("case_status", row['id'])
            add Solid(RM_CASE_RULE) ypos 131 xysize (590, 1)
            text (row['label'] if len(row['label']) <= 10 else row['label'][:9] + "…") xpos 22 yalign .5 xsize 367 size 36 color (RM_CASE_PAPER if chosen else RM_CASE_INK)
            frame:
                xpos 405 yalign .5 xysize (168, 55)
                background Solid("#e8e3d7" if chosen else "#d8d2c4")
                padding (5, 4)
                text row['badge'] align (.5, .5) size 31 color RM_CASE_INK
    if not visible:
        text "暂无记录" xpos 388 ypos 490 size 48 color "#767467"
    if count > 1:
        button:
            id "case_page_prev"
            xpos 780 ypos 1120 xysize (80, 80)
            sensitive actual_page > 0
            action [SetScreenVariable("case_page", actual_page - 1), SetScreenVariable("case_status", None)]
            add RMCaseMark("back")
        button:
            id "case_page_next"
            xpos 1040 ypos 1120 xysize (80, 80)
            sensitive actual_page + 1 < count
            action [SetScreenVariable("case_page", actual_page + 1), SetScreenVariable("case_status", None)]
            add RMCaseMark("next")
    text ("%d / %d" % (actual_page + 1, count)) xpos 950 xanchor .5 ypos 1130 size 43

    if detail:
        $ detail_title = detail['label'] if detail['unlocked'] else "未解锁"
        text (detail_title if len(detail_title) <= 30 else detail_title[:29] + "…") xpos 1708 ypos 354 xsize 738 size (92 if len(detail_title) <= 6 else 61 if len(detail_title) <= 12 else 42)
        text detail['badge'] xpos 1708 ypos 507 size 37 color "#68675e"
        add Solid(RM_CASE_RULE) xpos 1708 ypos 585 xysize (740, 2)
        text "说明" xpos 1708 ypos 628 size 64
        viewport:
            id "case_status_description"
            xpos 1708 ypos 730 xysize (740, 540)
            mousewheel True
            draggable True
            scrollbars "vertical"
            yinitial 0
            vbox:
                spacing 32
                if len(detail_title) > 30:
                    text detail_title xsize 726 size 42
                if detail['owned'] and detail.get('value_text'):
                    text detail['value_text'] size 50
                text detail['tooltip'] xsize 726 size 42 line_spacing 16
        add Solid(RM_CASE_RULE) xpos 1708 ypos 1320 xysize (740, 2)

style rm_case_text is gui_text:
    font rememorial_ui_font
    color "#22241f"
    size 42
    outlines []

style rm_case_button is button:
    padding (0, 0)
    background None
    hover_background None
    keyboard_focus True

style rm_case_frame is frame:
    padding (0, 0)

style rm_case_vscrollbar is vscrollbar:
    xsize 8
    base_bar Solid("#d2ccbd")
    thumb Solid("#777366")
    hover_thumb Solid("#22241f")
    unscrollable "hide"
