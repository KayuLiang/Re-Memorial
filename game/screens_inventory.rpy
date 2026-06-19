# Inventory screens for Re: Memorial.

init python:
    config.overlay_screens.append("inventory_button")

default inventory_message = ""

define item_categories = [
    ("all", "全部"),
    ("important", "重要物品"),
    ("medicine", "药物"),
]

define item_data = {
    "药盒": {
        "name": "药盒",
        "category": "medicine",
        "category_label": "药物",
        "description": "说明占位：医生开给弗洛的药物，后续补充药品说明和副作用提示。",
        "use_text": "使用占位：药物使用效果尚未实装。",
    },
    "手机": {
        "name": "手机",
        "category": "important",
        "category_label": "重要物品",
        "description": "说明占位：可用来查看消息，手机界面尚未实装。",
        "use_text": "使用占位：手机交互界面尚未实装。",
    },
    "神秘的项链": {
        "name": "神秘的项链",
        "category": "important",
        "category_label": "重要物品",
        "description": "说明占位：入院时被代管的项链，具体来历尚未揭示。",
        "use_text": "使用占位：项链的剧情效果尚未实装。",
    },
}

screen inventory_button():
    zorder 90

    if not main_menu and not opening_active:
        textbutton "背包":
            style "inventory_side_button"
            action Show("inventory_panel")

screen inventory_panel():
    modal True
    zorder 200
    default current_category = "all"
    default selected_item = None

    key "game_menu" action Hide("inventory_panel")

    frame:
        style "inventory_fullscreen_frame"

        vbox:
            spacing 22
            xfill True
            yfill True

            hbox:
                xfill True
                text "背包":
                    style "inventory_title_text"
                textbutton "❌":
                    xalign 1.0
                    action Hide("inventory_panel")

            hbox:
                spacing 10
                for category_id, category_name in item_categories:
                    textbutton category_name:
                        selected current_category == category_id
                        action [
                            SetScreenVariable("current_category", category_id),
                            SetScreenVariable("selected_item", None),
                        ]

            $ visible_items = [item_id for item_id in inventory if item_id in item_data and (current_category == "all" or item_data[item_id]["category"] == current_category)]

            hbox:
                spacing 24
                xfill True
                yfill True

                frame:
                    style "inventory_list_frame"
                    viewport:
                        mousewheel True
                        scrollbars "vertical"
                        vbox:
                            spacing 8

                            if visible_items:
                                for item_id in visible_items:
                                    textbutton item_data[item_id]["name"]:
                                        selected selected_item == item_id
                                        action SetScreenVariable("selected_item", item_id)
                            else:
                                text "暂无物品" style "inventory_empty_text"

                frame:
                    style "inventory_detail_frame"
                    if selected_item and selected_item in item_data and selected_item in inventory:
                        $ item = item_data[selected_item]
                        vbox:
                            spacing 14
                            text item["name"] style "inventory_item_name_text"
                            text item["category_label"] style "inventory_category_text"
                            text item["description"] style "inventory_description_text"
                            textbutton "使用":
                                action SetVariable("inventory_message", item["use_text"])
                    else:
                        text "选择一件物品查看详情。" style "inventory_empty_text"

            if inventory_message:
                text inventory_message style "inventory_message_text"

style inventory_side_button is button:
    xalign 1.0
    yalign 0.42
    xsize 110
    ysize 54

style inventory_fullscreen_frame is frame:
    xfill True
    yfill True
    padding (80, 60)

style inventory_list_frame is frame:
    xsize 360
    yfill True
    padding (18, 18)

style inventory_detail_frame is frame:
    xfill True
    yfill True
    padding (24, 24)

style inventory_title_text is gui_text:
    size 44
    bold True

style inventory_item_name_text is gui_text:
    size 34
    bold True

style inventory_category_text is gui_text:
    size 22
    color gui.accent_color

style inventory_description_text is gui_text:
    size 24

style inventory_empty_text is gui_text:
    size 24
    color "#888888"

style inventory_message_text is gui_text:
    size 22
    color gui.accent_color
