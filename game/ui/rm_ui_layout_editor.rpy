init python:
    import copy
    import json
    import os
    import pprint

    def rm_ui_layout_get(layout_name):
        return rm_ui_layouts.get(layout_name, {})

    def rm_ui_layout_capture_initial(layout_name):
        if layout_name not in rm_ui_layout_initials and layout_name in rm_ui_layouts:
            rm_ui_layout_initials[layout_name] = copy.deepcopy(rm_ui_layouts[layout_name])

    def rm_ui_layout_item(layout_name, element_id):
        layout = rm_ui_layout_get(layout_name)
        if element_id is None:
            return None
        return layout.get(element_id)

    def rm_ui_layout_sorted_items(layout_name):
        layout = rm_ui_layout_get(layout_name)
        result = []
        for element_id, element in layout.items():
            item = dict(element)
            item["id"] = element_id
            result.append(item)
        return sorted(result, key=lambda item: (item.get("z", 0), item["id"]))

    def rm_ui_layout_first_id(layout_name):
        items = rm_ui_layout_sorted_items(layout_name)
        return items[0]["id"] if items else None

    def rm_ui_layout_select_next(layout_name, selected_id):
        items = rm_ui_layout_sorted_items(layout_name)
        ids = [item["id"] for item in items]
        if not ids:
            return None
        if selected_id not in ids:
            return ids[0]
        return ids[(ids.index(selected_id) + 1) % len(ids)]

    def rm_ui_layout_selected_info(layout_name, selected_id):
        element = rm_ui_layout_item(layout_name, selected_id)
        if not element:
            return "No selection"
        return "\n".join((
            "id: %s" % selected_id,
            "x/y: %s / %s" % (element.get("x", 0), element.get("y", 0)),
            "w/h: %s / %s" % (element.get("w", 0), element.get("h", 0)),
            "z: %s" % element.get("z", 0),
            "alpha: %.2f" % float(element.get("alpha", 1.0)),
            "rotate: %s" % element.get("rotate", 0),
            "locked: %s" % element.get("locked", False),
            "visible: %s" % element.get("visible", True),
        ))

    def rm_ui_layout_mutable_item(layout_name, selected_id):
        element = rm_ui_layout_item(layout_name, selected_id)
        if not element or element.get("locked", False):
            return None
        return element

    def rm_ui_layout_move_selected(layout_name, selected_id, dx, dy):
        element = rm_ui_layout_mutable_item(layout_name, selected_id)
        if not element:
            return
        element["x"] = int(element.get("x", 0)) + dx
        element["y"] = int(element.get("y", 0)) + dy
        renpy.restart_interaction()

    def rm_ui_layout_resize_selected(layout_name, selected_id, dw, dh):
        element = rm_ui_layout_mutable_item(layout_name, selected_id)
        if not element:
            return
        element["w"] = max(1, int(element.get("w", 1)) + dw)
        element["h"] = max(1, int(element.get("h", 1)) + dh)
        renpy.restart_interaction()

    def rm_ui_layout_rotate_selected(layout_name, selected_id, delta):
        element = rm_ui_layout_mutable_item(layout_name, selected_id)
        if not element:
            return
        element["rotate"] = int(element.get("rotate", 0)) + delta
        renpy.restart_interaction()

    def rm_ui_layout_alpha_selected(layout_name, selected_id, delta):
        element = rm_ui_layout_mutable_item(layout_name, selected_id)
        if not element:
            return
        element["alpha"] = max(0.0, min(1.0, round(float(element.get("alpha", 1.0)) + delta, 2)))
        renpy.restart_interaction()

    def rm_ui_layout_z_selected(layout_name, selected_id, delta):
        element = rm_ui_layout_mutable_item(layout_name, selected_id)
        if not element:
            return
        element["z"] = int(element.get("z", 0)) + delta
        renpy.restart_interaction()

    def rm_ui_layout_toggle_visible(layout_name, selected_id):
        element = rm_ui_layout_item(layout_name, selected_id)
        if not element or element.get("locked", False):
            return
        element["visible"] = not bool(element.get("visible", True))
        renpy.restart_interaction()

    def rm_ui_layout_toggle_locked(layout_name, selected_id):
        element = rm_ui_layout_item(layout_name, selected_id)
        if not element:
            return
        element["locked"] = not bool(element.get("locked", False))
        renpy.restart_interaction()

    def rm_ui_layout_reset_selected(layout_name, selected_id):
        rm_ui_layout_capture_initial(layout_name)
        if selected_id not in rm_ui_layout_initials.get(layout_name, {}):
            return
        rm_ui_layouts[layout_name][selected_id] = copy.deepcopy(rm_ui_layout_initials[layout_name][selected_id])
        renpy.restart_interaction()

    def rm_ui_layout_export_data(layout_name):
        result = []
        for item in rm_ui_layout_sorted_items(layout_name):
            result.append({
                "id": item["id"],
                "x": int(item.get("x", 0)),
                "y": int(item.get("y", 0)),
                "w": int(item.get("w", 0)),
                "h": int(item.get("h", 0)),
                "z": int(item.get("z", 0)),
                "alpha": float(item.get("alpha", 1.0)),
                "rotate": int(item.get("rotate", 0)),
                "visible": bool(item.get("visible", True)),
                "locked": bool(item.get("locked", False)),
            })
        return result

    def rm_ui_layout_json_path(layout_name):
        filename = "ui_layout_%s.json" % layout_name
        # dice_select saves to game/debug_output/ui_layout_dice_select.json
        return os.path.join(config.gamedir, "debug_output", filename)

    def save_ui_layout_to_json(layout_name):
        path = rm_ui_layout_json_path(layout_name)
        try:
            if not os.path.isdir(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))
            with open(path, "w", encoding="utf-8") as output:
                json.dump(rm_ui_layout_export_data(layout_name), output, ensure_ascii=False, indent=2)
            renpy.notify("Saved %s" % path)
            renpy.log("Saved UI layout: %s" % path)
            return path
        except Exception as exc:
            renpy.notify("Save failed. Layout copied/logged.")
            renpy.log("UI layout save failed: %r" % exc)
            return rm_ui_layout_copy_text(layout_name)

    def rm_ui_layout_copy_text(layout_name):
        text = pprint.pformat(rm_ui_layout_export_data(layout_name), width=120)
        if hasattr(renpy, "set_clipboard"):
            renpy.set_clipboard(text)
        renpy.log("UI layout %s:\n%s" % (layout_name, text))
        return text


screen rm_ui_layout_draw_grid():
    for grid_x in range(0, 1921, 100):
        add Solid("#ffffff24"):
            xpos grid_x
            ypos 0
            xsize 1
            ysize 1080

    for grid_y in range(0, 1081, 100):
        add Solid("#ffffff24"):
            xpos 0
            ypos grid_y
            xsize 1920
            ysize 1


screen rm_ui_layout_draw_safe_frame():
    add Solid("#ffef6f"):
        xpos 0
        ypos 0
        xsize 1920
        ysize 2
    add Solid("#ffef6f"):
        xpos 0
        ypos 1078
        xsize 1920
        ysize 2
    add Solid("#ffef6f"):
        xpos 0
        ypos 0
        xsize 2
        ysize 1080
    add Solid("#ffef6f"):
        xpos 1918
        ypos 0
        xsize 2
        ysize 1080


screen rm_ui_layout_draw_center_lines():
    add Solid("#62d7ff80"):
        xpos 960
        ypos 0
        xsize 2
        ysize 1080
    add Solid("#62d7ff80"):
        xpos 0
        ypos 540
        xsize 1920
        ysize 2


screen rm_ui_layout_element_border(item, selected=False):
    $ border_color = "#ffea00cc" if selected else "#56b8ff80"
    add Solid(border_color):
        xpos item["x"]
        ypos item["y"]
        xsize item["w"]
        ysize 2
    add Solid(border_color):
        xpos item["x"]
        ypos item["y"] + item["h"] - 2
        xsize item["w"]
        ysize 2
    add Solid(border_color):
        xpos item["x"]
        ypos item["y"]
        xsize 2
        ysize item["h"]
    add Solid(border_color):
        xpos item["x"] + item["w"] - 2
        ypos item["y"]
        xsize 2
        ysize item["h"]


screen rm_ui_layout_editor(layout_name="dice_select"):
    modal True
    zorder 300

    default selected_id = rm_ui_layout_first_id(layout_name)
    default show_grid = True
    default show_borders = True
    default mouse_pos = (0, 0)

    on "show" action Function(rm_ui_layout_capture_initial, layout_name)

    key "K_LEFT" action Function(rm_ui_layout_move_selected, layout_name, selected_id, -1, 0)
    key "K_RIGHT" action Function(rm_ui_layout_move_selected, layout_name, selected_id, 1, 0)
    key "K_UP" action Function(rm_ui_layout_move_selected, layout_name, selected_id, 0, -1)
    key "K_DOWN" action Function(rm_ui_layout_move_selected, layout_name, selected_id, 0, 1)
    key "shift_K_LEFT" action Function(rm_ui_layout_move_selected, layout_name, selected_id, -10, 0)
    key "shift_K_RIGHT" action Function(rm_ui_layout_move_selected, layout_name, selected_id, 10, 0)
    key "shift_K_UP" action Function(rm_ui_layout_move_selected, layout_name, selected_id, 0, -10)
    key "shift_K_DOWN" action Function(rm_ui_layout_move_selected, layout_name, selected_id, 0, 10)
    key "ctrl_K_LEFT" action Function(rm_ui_layout_resize_selected, layout_name, selected_id, -1, 0)
    key "ctrl_K_RIGHT" action Function(rm_ui_layout_resize_selected, layout_name, selected_id, 1, 0)
    key "ctrl_K_UP" action Function(rm_ui_layout_resize_selected, layout_name, selected_id, 0, -1)
    key "ctrl_K_DOWN" action Function(rm_ui_layout_resize_selected, layout_name, selected_id, 0, 1)
    key "K_q" action Function(rm_ui_layout_rotate_selected, layout_name, selected_id, -1)
    key "K_e" action Function(rm_ui_layout_rotate_selected, layout_name, selected_id, 1)
    key "K_a" action Function(rm_ui_layout_alpha_selected, layout_name, selected_id, -0.05)
    key "K_d" action Function(rm_ui_layout_alpha_selected, layout_name, selected_id, 0.05)
    key "K_PAGEUP" action Function(rm_ui_layout_z_selected, layout_name, selected_id, 1)
    key "K_PAGEDOWN" action Function(rm_ui_layout_z_selected, layout_name, selected_id, -1)
    key "K_TAB" action SetScreenVariable("selected_id", rm_ui_layout_select_next(layout_name, selected_id))
    key "K_DELETE" action Function(rm_ui_layout_toggle_visible, layout_name, selected_id)
    key "K_g" action ToggleScreenVariable("show_grid")
    key "K_h" action ToggleScreenVariable("show_borders")
    key "K_l" action Function(rm_ui_layout_toggle_locked, layout_name, selected_id)
    key "K_r" action Function(rm_ui_layout_reset_selected, layout_name, selected_id)
    key "K_s" action Function(save_ui_layout_to_json, layout_name)
    key "K_ESCAPE" action Return()

    timer 0.05 repeat True action SetScreenVariable("mouse_pos", renpy.get_mouse_pos())

    add Solid("#111111")

    for item in rm_ui_layout_sorted_items(layout_name):
        if item.get("visible", True):
            add Transform(item["image"], alpha=item.get("alpha", 1.0), rotate=item.get("rotate", 0), xysize=(item["w"], item["h"])):
                xpos item["x"]
                ypos item["y"]

    if show_grid:
        use rm_ui_layout_draw_grid

    use rm_ui_layout_draw_safe_frame
    use rm_ui_layout_draw_center_lines

    for item in rm_ui_layout_sorted_items(layout_name):
        if item.get("visible", True):
            if show_borders or item["id"] == selected_id:
                use rm_ui_layout_element_border(item, item["id"] == selected_id)

            button:
                xpos item["x"]
                ypos item["y"]
                xsize item["w"]
                ysize item["h"]
                background None
                hover_background Solid("#ffffff22")
                action SetScreenVariable("selected_id", item["id"])

    frame:
        xpos 18
        ypos 18
        xsize 420
        background Solid("#000000cc")
        padding (16, 14)

        vbox:
            spacing 8
            text "UI Layout Editor: [layout_name]" size 22 color "#ffffff"
            text "[rm_ui_layout_selected_info(layout_name, selected_id)]" size 18 color "#f5f0df"
            text "mouse: [mouse_pos[0]] / [mouse_pos[1]]" size 18 color "#bde8ff"

            hbox:
                spacing 8
                textbutton "Save JSON":
                    action Function(save_ui_layout_to_json, layout_name)
                textbutton "Copy Layout":
                    action Function(rm_ui_layout_copy_text, layout_name)
                textbutton "Exit":
                    action Return()
