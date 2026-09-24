# Same HUD skeleton; one narrow, right-anchored status component.
default story_hud_location_text = ""

init -8 python:
    from functools import lru_cache
    from functools import partial
    from math import ceil
    from game.systems import rm_hud_status

    RM_STATUS_NARROW = 312
    RM_STATUS_WIDE = 416
    RM_STATUS_HEIGHT = 600  # Ends 8px above the dialogue tabs' actual hit area (y971).

    @lru_cache(maxsize=512)
    def rm_status_text_width(text, count=False):
        displayable = Text(text, style="rm_status_count" if count else "rm_status_name", substitute=False)
        # Render sizes can be floats. Screen-language float sizes mean fractions
        # of the parent, so round up to explicit pixel integers at this boundary.
        return int(ceil(renpy.render(displayable, 4096, 128, 0, 0).get_size()[0]))

    def rm_status_hud_layout(groups, expanded):
        return rm_hud_status.flow(groups, RM_STATUS_WIDE if expanded else RM_STATUS_NARROW,
                                  rm_status_text_width, lambda value: rm_status_text_width(value, True),
                                  RM_STATUS_HEIGHT)

    def rm_status_environment():
        return rm_hud_status.environment(rm_ensure_player(), renpy.get_attributes("bg") or (),
                                         story_hud_location_text, story_hud_effects)

    def rm_status_motion(x, y, reflow, trans, st, at):
        # SL2 transfers the previous transform's placement on replacement, but
        # does not send image-tag 'show/replace' ATL events to screen children.
        if not hasattr(trans, "status_origin"):
            trans.status_origin = (x if trans.xpos is None else trans.xpos,
                                   y if trans.ypos is None else trans.ypos)
            trans.status_started = st
        progress = min(1.0, max(0.0, (st - trans.status_started) / .22)) if _preferences.transitions else 1.0
        ease = progress * progress * (3 - 2 * progress)
        start_x, start_y = trans.status_origin
        if reflow:
            # Rewrapped slips fade at their destination rather than crossing
            # neighbouring text on the way to a different row.
            trans.pos = (x, y)
            trans.alpha = .3 + .7 * ease if (start_x, start_y) != (x, y) else 1.0
        else:
            trans.pos = (start_x + (x - start_x) * ease, start_y + (y - start_y) * ease)
        # Float coordinates are explicitly pixels, not fractional parent positions.
        trans.pos = tuple(absolute(value) for value in trans.pos)
        return 0 if progress < 1 else None

    @lru_cache(maxsize=256)
    def rm_status_move(x, y, reflow=False):
        return Transform(function=partial(rm_status_motion, x, y, reflow))


screen rm_status_hud():
    default expanded = False
    $ groups = rm_hud_status.snapshot(rm_ensure_player(), story_hud_effects)
    $ layout = rm_status_hud_layout(groups, expanded)
    $ origin = RM_STATUS_WIDE - layout['width']
    if groups:
        # Transparent maximum bounds. Only the actual paper slips obscure the scene.
        # Moving their stable transforms avoids scaling text during a width change.
        fixed:
            id "status_hud"
            pos (RM_HUD_RIGHT - RM_STATUS_WIDE, RM_HUD_SIDE_Y)
            xysize (RM_STATUS_WIDE, RM_STATUS_HEIGHT)
            text "状态" style "rm_status_title" xalign 1.0
            for group index group['id'] in layout['groups']:
                fixed:
                    id ("status_group_" + group['id'])
                    at rm_status_move(origin, group['y'])
                    xysize (layout['width'], group['height'])
                    use rm_status_group(group, SetLocalVariable("expanded", True), expanded)
            if expanded or layout['hidden']:
                textbutton ("收起 ›" if expanded else "‹ 展开  +{}".format(layout['hidden'])):
                    id "status_expand"
                    style "rm_status_toggle"
                    at rm_status_move(RM_STATUS_WIDE - 180, layout['footer_y'])
                    selected expanded
                    alt ("收起状态区" if expanded else "展开状态区，还有{}项".format(layout['hidden']))
                    action ToggleLocalVariable("expanded")
                if expanded and layout['hidden']:
                    text ("+{}".format(layout['hidden'])):
                        id "status_remaining"
                        style "rm_status_toggle_text"
                        xalign 0.0
                        at rm_status_move(origin, layout['footer_y'])
                        alt "另有{}项未在摘要中显示".format(layout['hidden'])
        $ status_tip = GetTooltip()
        if status_tip:
            frame:
                id "status_hud_tip"
                xpos RM_HUD_RIGHT
                xanchor 1.0
                ypos 963
                yanchor 1.0
                xsize RM_STATUS_WIDE
                background "#292923f2"
                padding (16, 12)
                text status_tip size 26 color RM_HUD_IVORY substitute False


screen rm_status_group(group, expand_action, expanded):
    text group['title'] style "rm_status_group_title"
    for item index item['id'] in group['items']:
        button:
            id ("status_item_" + item['id'])
            at rm_status_move(item['x'], item['y'], reflow=True)
            style "rm_status_slip"
            xysize (item['width'], 36)
            tooltip item['tooltip']
            alt ("{}，计数{}。{}".format(item['display_name'], item['display_count'], item['tooltip']))
            action NullAction()
            use rm_status_slip(item)
    if group['overflow']:
        $ more = group['overflow']
        button:
            id ("status_more_" + group['id'])
            at rm_status_move(more['x'], more['y'], reflow=True)
            style "rm_status_slip"
            xysize (more['width'], 36)
            tooltip ("本组还有{}项未显示" if expanded else "展开状态区，本组还有{}项").format(group['hidden'])
            alt ("{}，还有{}项{}".format(group['title'], group['hidden'], "" if expanded else "，展开状态区"))
            action expand_action
            use rm_status_slip(more)


screen rm_status_slip(item):
    fixed:
        xysize (item['width'], 36)
        add Solid("#f3eee3") pos (1, 1) xysize (item['width'] - 2, 34)
        # Main glyph and count have separate sizes and vertical origins, not subscript glyphs.
        text item['text'] style "rm_status_name" pos (10, 3) substitute False
        text item['display_count'] style "rm_status_count" pos (14 + item['name_width'], 0) substitute False


style rm_status_title is rm_hud_white_text:
    size 32

style rm_status_group_title is rm_hud_white_text:
    size 22
    color "#e3dfd4"

style rm_status_slip is button:
    padding (0, 0)
    background "#b4aa96"
    hover_background "#625849"

style rm_status_name is gui_text:
    font rememorial_ui_font
    size 26
    color "#292923"
    bold False
    outlines []
    layout "nobreak"

style rm_status_count is rm_status_name:
    size 18
    color "#514c42"

style rm_status_toggle is button:
    xsize 180
    ysize 40
    background None
    hover_background None
    padding (0, 0)

style rm_status_toggle_text is rm_hud_white_text:
    size 26
    xalign 1.0
    yalign .5
    hover_color "#e7cf96"
    selected_color "#f3eee3"
