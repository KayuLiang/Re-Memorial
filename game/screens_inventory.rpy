# Native inventory, approved 2026-09-22 six-column composition.
default inventory_message = ""
default rm_inventory_seen = []

init -5 python:
    from game.systems import rm_inventory
    INV_INK = "#111c20"
    INV_MUTED = "#777970"
    INV_PAPER = "#f7f5ee"
    INV_GOLD = "#b38e50"

    def rm_inventory_art(item, size):
        index = item.get("art")
        if index is None:
            return Text("图片待补", font=rememorial_ui_font, size=32, color=INV_MUTED)
        x0, x1 = round(index % 4 * 1774 / 4), round((index % 4 + 1) * 1774 / 4)
        y0, y1 = round(index // 4 * 887 / 2), round((index // 4 + 1) * 887 / 2)
        return Transform(Crop((x0,y0,x1-x0,y1-y0), "gui/inventory/items-placeholder.png"), xysize=(size,size), fit="contain")

    def rm_inventory_seen_item(item_id):
        if item_id and item_id not in store.rm_inventory_seen:
            store.rm_inventory_seen = store.rm_inventory_seen + [item_id]

    def rm_inventory_choose(item_id):
        renpy.set_screen_variable("selected_item", item_id, "inventory_panel")
        renpy.set_screen_variable("inspect", False, "inventory_panel")
        renpy.get_screen_variable("detail_scroll", "inventory_panel").change(0)
        rm_inventory_seen_item(item_id)

    def rm_inventory_filter(category):
        first = rm_inventory.selected(rm_inventory.rows(store.inventory, category))
        renpy.set_screen_variable("current_category", category, "inventory_panel")
        rm_inventory_choose(first["id"] if first else None)
        renpy.get_screen_variable("grid_scroll", "inventory_panel").change(0)

    def rm_inventory_zoom(delta=0, reset=False):
        get = lambda key: renpy.get_screen_variable(key,"inventory_panel")
        zoom = 1.0 if reset else max(.5,min(2.0,get("image_zoom")+delta))
        renpy.set_screen_variable("image_zoom",zoom,"inventory_panel")
        get("image_x").change(max(0,(1200*zoom-1900)/2))
        get("image_y").change(max(0,(1200*zoom-980)/2))

    def rm_ui_take_medicine(medicine, confirm_repeat=False):
        result = rm_core.take_medicine(rm_ensure_player(), medicine, rng=renpy.random, confirm_repeat=confirm_repeat)
        if result.get("available"):
            store.inventory_message = "已服用{}。".format(rm_core.MEDICINE_LABELS[medicine])
        elif result.get("reason") == "out_of_stock":
            store.inventory_message = "库存不足。"
        return result

    class RMInventoryMark(renpy.Displayable):
        def __init__(self, kind="search", color=INV_PAPER, **kwargs):
            super(RMInventoryMark,self).__init__(**kwargs)
            self.kind,self.color = kind,color
        def render(self,width,height,st,at):
            rv = renpy.Render(60,60)
            canvas = rv.canvas()
            if self.kind == "dot":
                canvas.circle(self.color,(30,30),8)
            else:
                canvas.circle(self.color,(25,25),17,5)
                canvas.line(self.color,(38,38),(53,53),6)
            return rv

screen inventory_panel(start_category="all"):
    modal True
    zorder 200
    style_prefix "rm_inventory"
    default current_category = start_category
    default selected_item = None
    default grid_scroll = ui.adjustment()
    default detail_scroll = ui.adjustment()
    default inspect = False
    default image_zoom = 1.0
    default image_x = ui.adjustment()
    default image_y = ui.adjustment()
    $ rows = rm_inventory.rows(inventory,current_category)
    $ item = rm_inventory.selected(rows,selected_item)
    on "show" action If(selected_item is None,Function(rm_inventory_filter,start_category))

    add "gui/inventory/paper.png" xysize (2560,1440)
    add Solid("#fffdf716") xysize (2560,1440)
    add Solid(INV_INK) pos (40,134) xysize (2460,2)

    if inspect and item:
        key "game_menu" action SetScreenVariable("inspect",False)
        key "mousedown_4" action Function(rm_inventory_zoom,.1)
        key "mousedown_5" action Function(rm_inventory_zoom,-.1)
        text item["name"] pos (72,28) size 66
        button:
            id "inventory_image_back"
            pos (2400,28) xysize (104,94)
            action SetScreenVariable("inspect",False)
            alt "返回背包"
            add RMCaseMark() align (.5,.5)
        viewport:
            id "inventory_image_viewport"
            pos (330,180) xysize (1900,980)
            xadjustment image_x yadjustment image_y
            draggable True
            arrowkeys True
            fixed:
                xysize (max(1900,int(1200*image_zoom)),max(980,int(1200*image_zoom)))
                add rm_inventory_art(item,int(1200*image_zoom)) align (.5,.5)
        hbox:
            pos (860,1220) spacing 22
            textbutton "缩小" id "inventory_zoom_out" style "rm_inventory_textbutton" action Function(rm_inventory_zoom,-.25)
            textbutton "还原" id "inventory_zoom_reset" style "rm_inventory_textbutton" action Function(rm_inventory_zoom,reset=True)
            textbutton "放大" id "inventory_zoom_in" style "rm_inventory_textbutton" action Function(rm_inventory_zoom,.25)
    else:
        key "game_menu" action Hide("inventory_panel")
        text "背包" pos (72,20) size 80
        button:
            id "inventory_close"
            pos (2400,28) xysize (104,94)
            action Hide("inventory_panel")
            alt "关闭背包"
            add RMCaseMark() align (.5,.5)
        for index,(key,label) in enumerate(rm_inventory.CATEGORIES):
            button:
                id ("inventory_category_"+key)
                pos (60,220+index*132) xysize (262,96)
                background (INV_INK if current_category == key else None)
                hover_background ("#28363a" if current_category == key else "#dbd6c9")
                action Function(rm_inventory_filter,key)
                text label align (.5,.5) size 52 color (INV_PAPER if current_category == key else INV_INK)

        if rows:
            viewport:
                id "inventory_grid"
                pos (366,210) xysize (1334,1092)
                yadjustment grid_scroll
                mousewheel True
                draggable True
                arrowkeys True
                pagekeys True
                vbox:
                    spacing 16
                    for row_index in range(max(5,(len(rows)+5)//6)):
                        hbox:
                            spacing 16
                            for col in range(6):
                                $ index = row_index*6+col
                                if index < len(rows):
                                    $ cell = rows[index]
                                    $ chosen = item and item["id"] == cell["id"]
                                    button:
                                        id ("inventory_item_%d" % index)
                                        xysize (209,205)
                                        padding (2,2)
                                        background (INV_GOLD if chosen else "#bfbcb2")
                                        hover_background INV_GOLD
                                        action Function(rm_inventory_choose,cell["id"])
                                        alt (cell["name"]+"，%d 件" % cell["count"])
                                        fixed:
                                            add Solid("#f7f1e4" if chosen else INV_PAPER)
                                            add Solid("#c9c5ba66") ysize 2
                                            if cell.get("art") is not None:
                                                add rm_inventory_art(cell,184) align (.5,.5)
                                            text str(cell["count"]) pos (157,149) size 34
                                            if cell["id"] not in rm_inventory_seen:
                                                add RMInventoryMark("dot","#9c4239") pos (153,-6)
                                else:
                                    frame:
                                        xysize (209,205) padding (2,2)
                                        background "#bfbcb2"
                                        add Solid(INV_PAPER)
            if len(rows)>30:
                vbar:
                    id "inventory_scrollbar"
                    pos (1713,210) xysize (8,1092)
                    adjustment grid_scroll
        else:
            text "暂无物品" id "inventory_empty" pos (810,590) size 48 color INV_MUTED

        if item:
            text item["name"] id "inventory_name" pos (1780,199) xsize 722 ysize 96 size 58 layout "subtitle"
            button:
                id "inventory_preview"
                pos (1780,297) xysize (720,525)
                background INV_INK
                hover_background "#202e32"
                action [SetScreenVariable("inspect",True),Function(rm_inventory_zoom,reset=True)]
                sensitive item.get("art") is not None
                alt "检视物品图片"
                if item.get("art") is not None:
                    add rm_inventory_art(item,500) align (.5,.5)
                else:
                    text "图片待补" align (.5,.5) size 40 color "#c6c6bd"
                if item.get("art") is not None:
                    add RMInventoryMark() pos (620,412)
            viewport:
                id "inventory_details"
                pos (1780,858) xysize (720,285)
                yadjustment detail_scroll
                mousewheel True
                draggable True
                vbox:
                    spacing 26
                    text item["description"] size 39
                    if item.get("source"):
                        text item["source"] size 32 color INV_MUTED
                    if item.get("effect"):
                        null height 10
                        text ("食用后" if item["category"] == "food" else "服用后") size 44
                        text item["effect"] size 34 color INV_MUTED
            if item.get("verb"):
                button:
                    id "inventory_use"
                    style "rm_inventory_textbutton"
                    pos (1780,1190) xysize (405,118)
                    action NullAction()
                    sensitive False
                    alt (item["verb"]+"，"+rm_inventory.use_blocked_reason(item))
                    text item["verb"] style "rm_inventory_textbutton_text"
    text "物品美术为示意" pos (58,1363) size 27 color "#85877d"

# Medicine keeps its simple interim layout, using the same catalog and stock.
screen medicine_panel():
    default repeat_confirmation = None
    modal True
    zorder 200
    use modal_dim_background
    key "game_menu" action Hide("medicine_panel")
    $ medicine_state = rm_ensure_player()
    $ medicines = [(medicine, count) for medicine, count in medicine_state.medicine_counts.items() if count > 0]
    frame:
        pos (448,331) xysize (1664,779) padding (53,43) background "#f3eee3"
        vbox:
            spacing 32
            hbox:
                xfill True
                text "药盒" size 51 color INV_INK
                button:
                    xalign 1.0 xysize (80,80) background None
                    action Hide("medicine_panel")
                    alt "关闭药盒"
                    add RMCaseMark() align (.5,.5)
            if not medicines:
                text "药盒里没有可用药物。" size 35 color INV_MUTED
            else:
                for medicine, count in medicines:
                    hbox:
                        spacing 32
                        text "{} ×{}".format(rm_core.MEDICINE_LABELS[medicine], count) size 40 color INV_INK xsize 900
                        $ repeated = int(getattr(medicine_state, "medicine_taken_today", {}).get(medicine, 0)) > 0
                        textbutton ("确认重复服用" if repeat_confirmation == medicine else "服用"):
                            style "rm_inventory_textbutton"
                            if repeated and repeat_confirmation != medicine:
                                action SetScreenVariable("repeat_confirmation", medicine)
                            else:
                                action [Function(rm_ui_take_medicine, medicine, repeated), SetScreenVariable("repeat_confirmation", None)]
                if inventory_message:
                    text inventory_message size 32 color INV_MUTED

style rm_inventory_text is gui_text:
    font rememorial_ui_font
    color INV_INK
    outlines []
    line_spacing 8

style rm_inventory_button is button:
    padding (0,0)
    background None
    hover_background "#d9d3c7"

style rm_inventory_frame is frame:
    padding (0,0)

style rm_inventory_textbutton is rm_inventory_button:
    background INV_INK
    hover_background "#354347"
    insensitive_background "#343d3e"
    padding (36,16)

style rm_inventory_textbutton_text is rm_inventory_text:
    size 55
    color INV_PAPER
    insensitive_color "#c6c6bd"
    xalign .5
    yalign .5

style rm_inventory_vbar is vbar:
    base_bar "#d7d1c4"
    thumb "#857a63"
    thumb_offset 0
