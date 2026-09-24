init -8 python:
    import pygame
    from game.systems import rm_dice_motion

    with renpy.file("gui/dice_obsidian/realtime.json") as _file:
        RM_REALTIME_MODELS = json.load(_file)
    with renpy.file("gui/dice_obsidian/tabletop.json") as _file:
        RM_TABLETOP = json.load(_file)

    def rm_live_atlas(faces):
        parts = []
        for index,value in enumerate(faces):
            glyph = Fixed(Text(str(value),font="fonts/source-han-serif/SourceHanSerifSC-SemiBold.otf",
                size=min(112 if len(faces)==4 else 94,int(180/max(1,len(str(value))))),color="#efd292",
                outlines=[(1,"#725126",0,1)],xalign=.5,yalign=.5,yoffset=-5,layout="nobreak"),xysize=(128,128))
            parts.extend(((index*128,0),glyph))
        return Composite((128*len(faces),128),*parts)

    def rm_live_stone(faces,atlas,pose,cam,resolution=240):
        return (Model(size=(resolution,resolution)).texture(atlas).shader("rm.live_die_"+str(len(faces)))
            .uniform("u_dice_q",pose).uniform("u_dice_view",cam['view'])
            .uniform("u_dice_up",cam['up']).uniform("u_dice_scale",cam['scale']))

    def rm_live_thumbnail(faces,size=180):
        model = RM_REALTIME_MODELS[str(len(faces))]
        return rm_live_stone(faces,rm_live_atlas(faces),rm_dice_motion.staging_pose(model),rm_dice_motion.camera(0),size)

    class RMRealtimeDice(renpy.Displayable):
        """One live table: drag input, fixed-step motion and projected convex dice."""
        def __init__(self, rows, selection=False, **kwargs):
            super(RMRealtimeDice, self).__init__(**kwargs)
            self.selection = selection
            self.signature = None
            self.rows = []
            self.world = dict(bodies=[])
            self.table = {name:GLTFModel("gui/dice_obsidian/"+part['file'],shader="rm.check_table")
                for name,part in RM_TABLETOP['parts'].items()}
            self.camera_elapsed = 0.0
            self.snap_elapsed = 0.0
            self.atlases = []
            self.sync(rows)
            self.drag_origin = None
            self.drag_tip = None
            self.last_st = None
            self.needs_refresh = False

        def sync(self,rows):
            signature = tuple((r.get('die_id',str(i)),tuple(r['faces'])) for i,r in enumerate(rows))
            if signature == self.signature:
                return
            previous = {r.get('die_id',str(i)):body for i,(r,body) in enumerate(zip(self.rows,self.world['bodies']))}
            self.world = rm_dice_motion.make_world(rows,RM_REALTIME_MODELS)
            for i,(row,body) in enumerate(zip(rows,self.world['bodies'])):
                body['q'] = rm_dice_motion.staging_pose(body['model'])
                body['p'] = [(i-(len(rows)-1)/2)*2.5,0,rm_dice_motion.floor_height(body)]
                body['snap_to'] = list(body['p'])
                old = previous.get(row.get('die_id',str(i)))
                body['snap_from'] = list(old['p']) if old else [body['p'][0],-1.4,body['p'][2]+.3]
                if self.selection:
                    body['p'] = list(body['snap_from'])
            self.rows = list(rows)
            self.signature = signature
            self.atlases = [rm_live_atlas(r['faces']) for r in rows]
            self.snap_elapsed = 0
            renpy.redraw(self,0)

        def launch(self, dx=0, dy=-240):
            if rm_dice_motion.throw(self.world,dx,dy,not _preferences.transitions):
                self.drag_origin = self.drag_tip = None
                self.last_st = None
                renpy.redraw(self,0)
                renpy.restart_interaction()

        def finish_snap(self):
            self.snap_elapsed = .32
            for body in self.world['bodies']:
                body['p'] = list(body['snap_to'])
            renpy.redraw(self,0)

        def per_interact(self):
            # Resume smoothly after a menu. Native loading re-enters call
            # screen and builds a ready table for the same saved check result.
            # Ordinary UI refreshes also call this hook. Resetting last_st here
            # drops a frame on every refresh and can stall a roll under load.
            renpy.redraw(self,0)

        def render(self,width,height,st,at):
            was_rolling = self.world['phase'] == 'rolling'
            dt = max(0,min(.1,st-self.last_st)) if self.last_st is not None else 0
            self.last_st = st
            if self.selection:
                self.snap_elapsed += dt
                t = rm_dice_ease(self.snap_elapsed/.32) if _preferences.transitions else 1
                for body in self.world['bodies']:
                    body['p'] = [a+(b-a)*t for a,b in zip(body['snap_from'],body['snap_to'])]
                cam = rm_dice_motion.camera(0,selection=True)
            else:
                before = self.camera_elapsed
                self.camera_elapsed = self.camera_elapsed+dt if _preferences.transitions else .8
                cam = rm_dice_motion.camera(self.camera_elapsed/.8)
                # Early input may queue a throw, but motion starts after the orbit.
                rm_dice_motion.advance(self.world,max(0,self.camera_elapsed-.8)-max(0,before-.8))
            result = renpy.Render(1936,320 if self.selection else 690)
            shadows = [tuple(body['p'])+(1.0,) for body in self.world['bodies']]+[(0,0,0,0)]*3
            palette = RM_TABLETOP['palette']
            def draw_part(name):
                tabletop = Transform(self.table[name],gl_depth=True,u_table_surface=0.0 if name=='deck' else 1.0,
                    u_table_up=cam['up'],u_table_view=cam['view'],u_table_projection=cam['center']+(cam['scale'],),
                    u_table_inner=tuple(RM_TABLETOP['wall_inner_planes']),
                    u_table_deck=tuple(palette['deck']),u_table_shell=tuple(palette['shell']),
                    u_table_cap=tuple(palette['cap']),u_table_accent=tuple(palette['accent']),u_table_shade=tuple(palette['shadow']),
                    u_table_shadow0=shadows[0],u_table_shadow1=shadows[1],u_table_shadow2=shadows[2])
                result.blit(renpy.render(tabletop,1936,690,st,at),(0,0))
            draw_part('deck')
            draw_part('north')
            for index,body in sorted(enumerate(self.world['bodies']),key=lambda item:rm_dice_motion.dot(item[1]['p'],cam['view'])):
                stone = rm_live_stone(body['faces'],self.atlases[index],body['q'],cam)
                drawn = renpy.render(stone,240,240,st,at)
                cx,cy = rm_dice_motion.project(body['p'],cam)
                result.blit(drawn,(cx-120,cy-120))
            for name in ('west','east','south'):
                draw_part(name)
            if self.drag_origin:
                guide = renpy.Render(1936,690)
                ink = guide.canvas()
                ink.line("#ddbf79",self.drag_origin,self.drag_tip,5)
                ink.circle("#ddbf79",self.drag_origin,12,2)
                ink.circle("#f3ddb0",self.drag_tip,8)
                power = min(1,math.dist(self.drag_origin,self.drag_tip)/520)
                ink.rect("#555744",(768,644,400,7))
                ink.rect("#ddbf79",(768,644,int(400*power),7))
                result.blit(guide,(0,0))
            if was_rolling and self.world['phase'] == 'settled':
                self.needs_refresh = True
                renpy.timeout(0)
            if self.world['phase'] == 'rolling' or (self.selection and self.snap_elapsed < .32) or (not self.selection and self.camera_elapsed < .8):
                renpy.redraw(self,0)
            return result

        def event(self,ev,x,y,st):
            if self.selection:
                return
            if self.needs_refresh:
                self.needs_refresh = False
                renpy.restart_interaction()
            if self.world['phase'] == 'settled':
                return
            if self.world['phase'] != 'ready':
                return
            inside = 0 <= x < 1936 and 0 <= y < 690
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and inside:
                self.drag_origin = self.drag_tip = (x,y)
                renpy.redraw(self,0)
                raise renpy.IgnoreEvent()
            if self.drag_origin and ev.type == pygame.MOUSEMOTION:
                self.drag_tip = (max(20,min(1916,x)),max(20,min(670,y)))
                renpy.redraw(self,0)
                raise renpy.IgnoreEvent()
            if self.drag_origin and ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                dx,dy = x-self.drag_origin[0],y-self.drag_origin[1]
                self.launch(dx,dy)
                raise renpy.IgnoreEvent()
            if self.drag_origin and ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.drag_origin = self.drag_tip = None
                renpy.redraw(self,0)
                raise renpy.IgnoreEvent()

        def visit(self):
            return list(self.table.values())+self.atlases
