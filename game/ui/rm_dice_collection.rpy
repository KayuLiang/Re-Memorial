# 骰组 — approved ivory / obsidian / gold composition, QHD authoring canvas.
init -9 python:
    import json
    import time
    from game.systems import rm_dice_view

    RM_DICE_PAPER = "#f0ede4"
    RM_DICE_INK = "#11191d"
    RM_DICE_GOLD = "#b69452"
    RM_DICE_STAGE = (405,420,860)
    RM_DICE_CARD_SIZE = (360,510)
    RM_DICE_CARD_ART = (50,146,260)
    RM_DICE_MODELS = {}
    RM_DICE_PAGES = {}
    for _sides in (4, 6, 8, 10, 12, 20):
        with renpy.file("gui/dice_obsidian/d%d.json" % _sides) as _file:
            RM_DICE_MODELS[_sides] = json.load(_file)
        with renpy.file("gui/dice_obsidian/d%d-page.json" % _sides) as _file:
            RM_DICE_PAGES[_sides] = json.load(_file)

    def rm_dice_ease(t):
        t = max(0.0,min(1.0,t))
        return t*t*(3-2*t)

    def rm_dice_elapsed(start,now=None):
        elapsed = (time.monotonic() if now is None else now)-start
        # Screen scope can be saved. After an OS reboot, a saved monotonic
        # timestamp can be in the future: restore the settled view, not a wait.
        return 2.0 if elapsed<0 else elapsed

    def rm_dice_open(dice_id):
        get = lambda key: renpy.get_screen_variable(key,"character_panel")
        pool = rm_dice_view.rows(rm_player,get("dice_filter"),get("dice_order"),get("dice_enchantment"))
        index = next(i for i,d in enumerate(pool) if d['id']==dice_id)%6
        now = time.monotonic()
        for key,value in (("dice_selected",dice_id),("dice_mode","expanded"),
                ("dice_face",0),("dice_offset",0),("dice_opened",now),
                ("dice_origin",(195+index%3*520,398+index//3*532)),
                ("dice_scroll",(0.0,0.0,now))):
            renpy.set_screen_variable(key,value,"character_panel")
        renpy.restart_interaction()

    def rm_dice_reset_filter(attribute="all"):
        renpy.set_screen_variable("dice_filter", attribute, "character_panel")
        renpy.set_screen_variable("dice_page", 0, "character_panel")
        renpy.set_screen_variable("dice_selected", None, "character_panel")

    def rm_dice_choose(dice_id):
        selected = renpy.get_screen_variable("dice_selected", "character_panel")
        renpy.set_screen_variable("dice_selected", dice_id, "character_panel")
        if selected == dice_id:
            rm_dice_open(dice_id)
        renpy.restart_interaction()

    def rm_dice_scroll_position(scroll, now):
        start,target,began = scroll
        return start+(target-start)*rm_dice_ease(rm_dice_elapsed(began,now)/.42)

    def rm_dice_turn(offset, maximum):
        offset = max(0,min(maximum,offset))
        selected = renpy.get_screen_variable("dice_face","character_panel")
        scroll = renpy.get_screen_variable("dice_scroll","character_panel")
        now = time.monotonic()
        position = rm_dice_scroll_position(scroll,now)
        renpy.set_screen_variable("dice_scroll",(position,float(offset),now),"character_panel")
        renpy.set_screen_variable("dice_offset", offset, "character_panel")
        renpy.set_screen_variable("dice_face", max(offset,min(selected,offset+8)), "character_panel")
        renpy.restart_interaction()

    def RMDiceMoon(index,count,size=96,selected=False):
        # Vector assets keep small circles smooth at every physical window size.
        return Transform("gui/dice_obsidian/moon-%d-%d%s.svg" %
            (count,index,"-selected" if selected else ""),xysize=(size,size))

    def rm_dice_card_stock(die):
        # Both the cabinet and tilted paper use this exact printed card.
        return Composite(RM_DICE_CARD_SIZE,
            (10,0),Transform("gui/dice_obsidian/card-stock-approved.png",
                xysize=(340,510)),
            (38,24),Text(die['label'],font=rememorial_ui_font,size=49,color=RM_DICE_PAPER),
            (236,42),Text("%02d/%02d" % (die['serial'],die['total']),font=rememorial_ui_font,
                size=25,color="#c6b98f",xsize=92,text_align=1.0),
            (90,453),Text("D%d" % die['sides'],font="gui/dice_obsidian/Almendra-Regular.ttf",
                size=41,color="#dac799",xsize=180,text_align=.5))

    class RMDiceArt(renpy.Displayable):
        """Blender mineral renders with live face numerals projected onto the facets."""
        def __init__(self, faces, size=400, opened=None, **kwargs):
            super(RMDiceArt, self).__init__(**kwargs)
            self.faces, self.size, self.opened = tuple(faces), size, opened
            self.frame_count = len(RM_DICE_MODELS[len(faces)])
            indices = range(self.frame_count) if opened is not None else (self.frame_count-1,)
            self.frames = [renpy.displayable("gui/dice_obsidian/d%d-%02d.png" % (len(faces), i)) for i in indices]
            self.letters = {}
            for value in set(faces):
                self.letters[value] = Text(str(value), font="gui/dice_obsidian/Almendra-Regular.ttf",
                    size=88 if len(str(value)) < 3 else 64, color="#e6c983",
                    outlines=[(1,"#5c431d",0,1), (1,"#fff0b5",0,-1)],
                    xsize=128, ysize=128, text_align=.5, layout="nobreak")

        def render(self, width, height, st, at):
            moving = self.opened is not None and bool(_preferences.transitions)
            elapsed = max(0,rm_dice_elapsed(self.opened)-.12) if moving else 1.2
            frame = min(self.frame_count-1,int(elapsed*(self.frame_count-1)/1.2))
            scale = self.size/800.0
            result = renpy.Render(self.size,self.size)
            result.blit(renpy.render(Transform(self.frames[frame if moving else -1],xysize=(self.size,self.size)),self.size,self.size,st,at),(0,0))
            for face in RM_DICE_MODELS[len(self.faces)][frame]:
                a,b,c,d = [v*scale/128 for v in face['basis']]
                glyph = Transform(self.letters[self.faces[face['index']]],
                    matrixtransform=Matrix([a,b,c,d]))
                rendered = renpy.render(glyph,128,128,st,at)
                x,y = face['center']
                rw,rh = rendered.get_size()
                result.blit(rendered,(int(x*scale-rw/2),int(y*scale-rh/2)))
            if moving and frame < self.frame_count-1: renpy.redraw(self,1.0/30)
            return result

        def visit(self):
            return self.frames + list(self.letters.values())

    class RMDicePage(renpy.Displayable):
        def __init__(self,die,origin,opened,**kwargs):
            super(RMDicePage,self).__init__(**kwargs)
            self.sides,self.origin,self.opened = die['sides'],origin,opened
            self.stock = rm_dice_card_stock(die)

        def render(self, width, height, st, at):
            out = renpy.Render(1680,1440)
            canvas = out.canvas()
            elapsed = rm_dice_elapsed(self.opened)
            t = rm_dice_ease(elapsed/.8) if _preferences.transitions else 1.0
            x,y = self.origin[0]-RM_DICE_CARD_ART[0],self.origin[1]-RM_DICE_CARD_ART[1]
            cw,ch = RM_DICE_CARD_SIZE
            start = [(x,y),(x+cw,y),(x+cw,y+ch),(x,y+ch)]
            sx,sy,size = RM_DICE_STAGE
            target = [(sx+px*size/800,sy+py*size/800) for px,py in RM_DICE_PAGES[self.sides]]
            # Exported corners are TL, TR, BR, BL in the card's own coordinates.
            points = [(a+(c-a)*t,b+(d-b)*t) for (a,b),(c,d) in zip(start,target)]
            canvas.polygon("#cbc7bd",[(x+5,y+7) for x,y in points])
            a,b = (points[1][0]-points[0][0])/cw,(points[3][0]-points[0][0])/ch
            c,d = (points[1][1]-points[0][1])/cw,(points[3][1]-points[0][1])/ch
            paper = Transform(self.stock,matrixtransform=Matrix([a,b,c,d]))
            rendered = renpy.render(paper,cw,ch,st,at)
            rw,rh = rendered.get_size()
            cx,cy = sum(p[0] for p in points)/4,sum(p[1] for p in points)/4
            # matrixtransform keeps the child's layout bounds and centre;
            # its visible vertices can extend beyond those bounds.
            out.blit(rendered,(cx-rw/2,cy-rh/2))
            if t<1: renpy.redraw(self,0)
            return out

        def visit(self):
            return [self.stock]

    def rm_dice_materialize_motion(origin,opened,trans,st,at):
        elapsed = rm_dice_elapsed(opened)
        t = rm_dice_ease(elapsed/.8)
        sx,sy,size = RM_DICE_STAGE
        initial_size = RM_DICE_CARD_ART[2]
        trans.zoom = (initial_size+(size-initial_size)*t)/size
        trans.xpos = absolute(origin[0]+(sx-origin[0])*t)
        trans.ypos = absolute(origin[1]+(sy-origin[1])*t-35*math.sin(math.pi*min(1,elapsed/1.32)))
        return 0 if elapsed<1.32 else None

    def rm_dice_arc_motion(index,count,opened,scroll,trans,st,at):
        now = time.monotonic()
        position = rm_dice_scroll_position(scroll,now) if _preferences.transitions else scroll[1]
        slot = index-position
        t = rm_dice_ease((rm_dice_elapsed(opened,now)-.48)/.9) if _preferences.transitions else 1.0
        target = math.pi*(.98-.96*slot/max(1,count-1))
        # One angular offset keeps the spacing intact: faces enter one by one
        # from the lower right, instead of piling up at a shared start point.
        angle = target-math.pi*1.16*(1-t)
        trans.xpos = absolute(834+674*math.cos(angle))
        trans.ypos = absolute(946-602*math.sin(angle))
        arrival = max(0,min(1,(angle+math.pi*.18)/.25))
        trans.alpha = arrival*max(0,min(1,(slot+.65)/.65,(count-.35-slot)/.65))
        return 0 if t<1 or rm_dice_elapsed(scroll[2],now)<.42 else None

    def rm_dice_moon_text(index,count):
        phase = .12+.76*index/max(1,count-1)
        return RM_DICE_INK if math.cos(math.tau*phase)<0 else RM_DICE_PAPER

transform rm_dice_materialize(origin,opened):
    subpixel True
    function renpy.curry(rm_dice_materialize_motion)(origin,opened)

transform rm_dice_arc_enter(index,count,opened,scroll):
    subpixel True
    function renpy.curry(rm_dice_arc_motion)(index,count,opened,scroll)

screen rm_dice_content(dice_mode, dice_filter, dice_order, dice_enchantment, dice_selected, dice_page, dice_face, dice_offset, dice_menu, dice_growth_attribute, dice_opened, dice_origin, dice_scroll):
    style_prefix "rm_dice"
    $ character = rm_player
    $ pool = rm_dice_view.rows(character, dice_filter, dice_order, dice_enchantment) if character else []
    $ page_count = max(1, (len(pool)+5)//6)
    $ page = min(dice_page, page_count-1)
    $ visible = pool[page*6:page*6+6]
    $ selected = next((d for d in pool if d['id'] == dice_selected), None)
    add Solid(RM_DICE_PAPER)
    text "骰组" xpos 68 ypos 0 size 96
    button:
        id "dice_close"
        alt "关闭骰组"
        xpos 2420 ypos 20 xysize (100,100)
        action Hide("character_panel")
        add RMCaseMark("close",RM_DICE_INK) align (.5,.5)
    add Solid(RM_DICE_INK) xpos 24 ypos 124 xysize (2508 if dice_mode == "growth" else 1626,2)

    if dice_mode == "expanded" and selected:
        text ("/  " + selected['label']) xpos 326 ypos 36 size 54
        textbutton "‹  返回陈列":
            id "dice_back"
            xpos 588 ypos 38
            action SetScreenVariable("dice_mode", "collection")
        key "game_menu" action SetScreenVariable("dice_mode", "collection")
        use rm_dice_expanded(selected, dice_face, dice_offset, dice_opened, dice_origin, dice_scroll)
    else:
        for index, (mode, label) in enumerate((("collection","陈列"),("growth","成长"))):
            button:
                id ("dice_tab_"+mode)
                xpos (338+index*226) ypos 28 xysize (176,80)
                background (RM_DICE_INK if dice_mode == mode else None)
                action SetScreenVariable("dice_mode",mode)
                text label align (.5,.5) size 48 color (RM_DICE_PAPER if dice_mode == mode else RM_DICE_INK)
        if dice_mode == "growth":
            use rm_dice_growth(character, selected, dice_growth_attribute)
        else:
            for index, (key, label) in enumerate((("all","全部"),)+tuple((a,rm_dice_view.LABELS[a]) for a in rm_dice_view.ORDER)):
                button:
                    id ("dice_filter_"+key)
                    xpos (70+index*153) ypos 162 xysize (134,64)
                    background (RM_DICE_INK if dice_filter == key else None)
                    action Function(rm_dice_reset_filter,key)
                    text label align (.5,.5) size 35 color (RM_DICE_PAPER if dice_filter == key else RM_DICE_INK)
            text ("%d 枚" % len(pool)) xpos 1012 ypos 174 size 32
            textbutton ("排序："+{"attribute":"属性","sides":"面数","mean":"均值"}[dice_order]+" ↓"):
                id "dice_sort"
                xpos 1140 ypos 168
                action ToggleScreenVariable("dice_menu", "sort", None)
            textbutton ("附魔"+{"all":" ↓","enchanted":"：有 ↓","plain":"：无 ↓"}[dice_enchantment]):
                id "dice_enchantment"
                xpos 1440 ypos 168
                action ToggleScreenVariable("dice_menu", "enchant", None)

            for index, die in enumerate(visible):
                button:
                    id ("dice_card_"+str(index))
                    alt ("%s D%d 第%d枚" % (die['label'],die['sides'],die['serial']))
                    xpos (145+index%3*520) ypos (252+index//3*532) xysize RM_DICE_CARD_SIZE
                    background None
                    hover_background None
                    foreground ("gui/dice_obsidian/card-focus.svg" if die['id']==dice_selected else None)
                    hover_foreground "gui/dice_obsidian/card-focus.svg"
                    action Function(rm_dice_choose,die['id'])
                    add rm_dice_card_stock(die)
                    add RMDiceArt(die['faces'],RM_DICE_CARD_ART[2]) pos RM_DICE_CARD_ART[:2]
                    $ indices = rm_dice_view.preview_indices(die['faces'])
                    for j, face_index in enumerate(indices):
                        $ angle = -math.pi/2 + j*math.tau/len(indices)
                        $ cx, cy = 180+120*math.cos(angle), 273+143*math.sin(angle)
                        add RMDiceMoon(j,len(indices),64) pos (int(cx),int(cy)) anchor (.5,.5)
                        text ("…" if face_index is None else str(die['faces'][face_index])):
                            pos (int(cx),int(cy)-3) anchor (.5,.5)
                            size 36 color rm_dice_moon_text(j,len(indices))
            if not visible:
                text "暂无骰子" id "dice_empty" xpos 675 ypos 650 size 52 color "#77786f"
            text ("%d / %d" % (page+1,page_count)) xpos 800 ypos 1340 xanchor .5 size 37
            textbutton "‹":
                id "dice_page_prev"
                xpos 670 ypos 1322 xysize (72,80)
                sensitive page > 0
                action [SetScreenVariable("dice_page",page-1),SetScreenVariable("dice_selected",None)]
            textbutton "›":
                id "dice_page_next"
                xpos 875 ypos 1322 xysize (72,80)
                sensitive page+1 < page_count
                action [SetScreenVariable("dice_page",page+1),SetScreenVariable("dice_selected",None)]
            use rm_dice_detail(selected or (visible[0] if visible else None), False)
            if dice_menu:
                frame:
                    xpos (1140 if dice_menu == "sort" else 1400) ypos 232 xsize 250
                    background RM_DICE_INK padding (12,12)
                    vbox:
                        for key, label in ((("attribute","按属性"),("sides","按面数"),("mean","按平均面值")) if dice_menu == "sort" else (("all","全部"),("enchanted","有附魔"),("plain","无附魔"))):
                            textbutton label:
                                id ("dice_option_"+key)
                                xsize 226 ysize 64 text_color RM_DICE_PAPER
                                action [SetScreenVariable("dice_order" if dice_menu == "sort" else "dice_enchantment",key), SetScreenVariable("dice_menu",None), SetScreenVariable("dice_page",0), SetScreenVariable("dice_selected",None)]

screen rm_dice_distribution(die, y=794):
    style_prefix "rm_dice"
    text "面值分布" id "dice_distribution" xpos 1756 ypos y size 39 color RM_DICE_PAPER
    text "面数" xpos 2448 xanchor 1.0 ypos (y+8) size 26 color "#aeb0a9"
    $ dist = rm_dice_view.distribution(die['faces'])
    $ step = 690.0/max(1,len(dist))
    $ peak = max(row[1] for row in dist)
    add Solid("#858a86") xpos 1756 ypos (y+255) xysize (692,1)
    for i, (value, count, probability) in enumerate(dist):
        $ bx = int(1756+step*i+step*.15)
        $ bw = max(8,int(step*.7))
        $ bh = int(128*count/peak)
        add Solid(RM_DICE_GOLD) xpos bx ypos (y+254-bh) xysize (bw,bh)
        text str(count) pos (int(bx+bw/2),int(y+232-bh)) anchor (.5,.5) size 26 color RM_DICE_PAPER
        $ label_y = y+284+(34 if len(dist)>12 and i%2 else 0)
        if len(dist)>12:
            add Solid("#737973") xpos int(bx+bw/2) ypos (y+256) xysize (1,42 if i%2 else 9)
        text str(value) pos (int(bx+bw/2),int(label_y)) anchor (.5,.5) size (26 if len(dist)>12 else 29) color RM_DICE_PAPER

screen rm_dice_detail(die, expanded=False, dice_face=0):
    style_prefix "rm_dice"
    add Solid(RM_DICE_INK) xpos 1682 ypos 110 xysize (878,1330)
    if die:
        text ("骰面" if expanded else die['label']) xpos 1756 ypos 176 size 108 color RM_DICE_PAPER
        text ("%02d / %02d" % (dice_face+1,die['sides']) if expanded else "D%d · %02d" % (die['sides'],die['serial'])) xpos 1760 ypos 320 size 52 color RM_DICE_PAPER
        add Solid("#b8b9af") xpos 1756 ypos 428 xysize (692,2)
        if expanded:
            text "面值" xpos 1756 ypos 462 size 35 color RM_DICE_PAPER
            text str(die['faces'][dice_face]) xpos 1750 ypos 494 size 120 color RM_DICE_PAPER
            text "单面概率" xpos 2116 ypos 462 size 35 color RM_DICE_PAPER
            text (("%.2f" % (100.0/die['sides'])).rstrip('0').rstrip('.')+"%") xpos 2110 ypos 526 size 66 color RM_DICE_PAPER
        else:
            text "平均面值" xpos 1756 ypos 462 size 35 color RM_DICE_PAPER
            text die['expectation_text'] xpos 1750 ypos 516 size 84 color RM_DICE_PAPER
            add Solid("#b8b9af") xpos 2084 ypos 471 xysize (1,124)
            text "面值范围" xpos 2160 ypos 462 size 35 color RM_DICE_PAPER
            text ("%s–%s" % (die['minimum'],die['maximum'])) xpos 2154 ypos 516 size 77 color RM_DICE_PAPER
        add Solid("#b8b9af") xpos 1756 ypos 644 xysize (692,2)
        text "附魔" xpos 1756 ypos 680 size 35 color RM_DICE_PAPER
        text die['enchantment_label'] xpos 1920 ypos 672 size 48 color RM_DICE_PAPER
        if die['temporary']:
            text "临时" xpos 2448 xanchor 1.0 ypos 680 size 35 color "#dac799"
        use rm_dice_distribution(die)
        button:
            id ("dice_expand" if not expanded else "dice_collapse")
            xpos 1756 ypos 1230 xysize (692,110)
            background RM_DICE_PAPER hover_background "#ded3b3"
            action (Function(rm_dice_open,die['id']) if not expanded else SetScreenVariable("dice_mode","collection"))
            text ("收起骰面  ←" if expanded else "展开骰面  →") align (.5,.5) size 51
    else:
        text "选择一枚骰子" xpos 1756 ypos 230 size 74 color RM_DICE_PAPER

screen rm_dice_expanded(die, dice_face, dice_offset, dice_opened, dice_origin, dice_scroll):
    style_prefix "rm_dice"
    text ("D%d" % die['sides']) xpos 68 ypos 151 size 192
    $ names = {4:"四面骰",6:"六面骰",8:"八面骰",10:"十面骰",12:"十二面骰",20:"二十面骰"}
    text names[die['sides']] xpos 76 ypos 365 size 45
    add Solid(RM_DICE_INK) xpos 76 ypos 450 xysize (72,4)
    add RMDicePage(die,dice_origin,dice_opened)
    if not _preferences.transitions:
        add RMDiceArt(die['faces'],RM_DICE_STAGE[2]) pos RM_DICE_STAGE[:2]
    else:
        add RMDiceArt(die['faces'],RM_DICE_STAGE[2],dice_opened) at rm_dice_materialize(dice_origin,dice_opened)
    $ faces = rm_dice_view.visible_faces(die['faces'],dice_offset)
    $ token_size = 108 if die['sides']>=10 and die['sides']<=12 else 154
    for physical_index in range(die['sides']):
        button:
            id ("dice_face_"+str(physical_index))
            alt ("第%d面，面值%s" % (physical_index+1,die['faces'][physical_index]))
            anchor (.5,.5) xysize (token_size,token_size)
            background None
            hover_background None
            hover_foreground Transform("gui/dice_obsidian/moon-focus.svg",xysize=(token_size,token_size))
            at rm_dice_arc_enter(physical_index,len(faces),dice_opened,dice_scroll)
            sensitive physical_index in faces
            action SetScreenVariable("dice_face",physical_index)
            add RMDiceMoon(physical_index,die['sides'],token_size,physical_index==dice_face)
            text str(die['faces'][physical_index]) align (.5,.45) size (57 if token_size==108 else 82) color rm_dice_moon_text(physical_index,die['sides'])
    if die['sides'] > 12:
        key "mousedown_4" action Function(rm_dice_turn,dice_offset-1,die['sides']-len(faces))
        key "mousedown_5" action Function(rm_dice_turn,dice_offset+1,die['sides']-len(faces))
        key "K_LEFT" action Function(rm_dice_turn,dice_offset-1,die['sides']-len(faces))
        key "K_RIGHT" action Function(rm_dice_turn,dice_offset+1,die['sides']-len(faces))
        key "K_HOME" action Function(rm_dice_turn,0,die['sides']-len(faces))
        key "K_END" action Function(rm_dice_turn,die['sides']-len(faces),die['sides']-len(faces))
        textbutton "‹":
            id "dice_arc_prev"
            xpos 74 ypos 1200 xysize (90,85)
            sensitive dice_offset > 0
            action Function(rm_dice_turn,dice_offset-1,die['sides']-len(faces))
        textbutton "›":
            id "dice_arc_next"
            xpos 1480 ypos 1200 xysize (90,85)
            sensitive dice_offset+len(faces)<die['sides']
            action Function(rm_dice_turn,dice_offset+1,die['sides']-len(faces))
        text ("%02d–%02d / %02d" % (faces[0]+1,faces[-1]+1,die['sides'])) xpos 825 ypos 1390 xanchor .5 size 31
    use rm_dice_detail(die,True,dice_face)

screen rm_dice_growth(character, selected, dice_growth_attribute):
    style_prefix "rm_dice"
    $ attribute = dice_growth_attribute
    $ owned = rm_dice_view.rows(character, attribute) if character else []
    add Solid(RM_DICE_INK) xpos 52 ypos 160 xysize (810,1220)
    text rm_dice_view.LABELS[attribute] xpos 116 ypos 240 size 108 color RM_DICE_PAPER
    if owned:
        $ die = owned[0]
        text ("D%d" % die['sides']) xpos 118 ypos 396 size 62 color RM_DICE_PAPER
        add RMDiceArt(die['faces'],940) xpos -15 ypos 465
    else:
        text "暂无骰子" xpos 118 ypos 600 size 44 color RM_DICE_PAPER
    text "累计进度" xpos 2470 xanchor 1.0 ypos 182 size 39
    for i, (key,label,progress,pending) in enumerate(rm_dice_view.growth(character) if character else []):
        $ y = 262+i*197
        button:
            id ("dice_growth_"+key)
            xpos 938 ypos y xysize (1570,190)
            background ("#e6e1d4" if key==attribute else None)
            action SetScreenVariable("dice_growth_attribute",key)
            if key==attribute:
                add Solid(RM_DICE_GOLD) xsize 10
            add Solid("#b5b4aa") ypos 1 xysize (1570,2)
            text label xpos 38 ypos 36 size 88
            for j in range(6):
                add Solid(RM_DICE_INK if j<min(progress,6) else "#a4a59c") xpos (382+j*132) ypos 52 xysize (86,86)
                if j>=min(progress,6):
                    add Solid(RM_DICE_PAPER) xpos (385+j*132) ypos 55 xysize (80,80)
            text ("%d / 6" % progress) xpos 1270 ypos 39 size 77
            if pending:
                text ("待选择 %d" % pending) xpos 1270 ypos 135 size 30
    button:
        id "dice_growth_view"
        xpos 1920 ypos 1290 xysize (580,100)
        background RM_DICE_INK
        action [Function(rm_dice_reset_filter,attribute), SetScreenVariable("dice_mode","collection")]
        text "查看骰子  →" align (.5,.5) size 50 color RM_DICE_PAPER

style rm_dice_text is gui_text:
    font rememorial_ui_font
    color "#11191d"
    size 36
    outlines []
style rm_dice_button is button:
    padding (0,0)
    background None
    hover_background "#b6945222"
    keyboard_focus True
style rm_dice_button_text is rm_dice_text:
    size 35
    hover_color "#977331"
    insensitive_color "#a6a69d"
    yalign .5
style rm_dice_frame is frame:
    padding (0,0)
