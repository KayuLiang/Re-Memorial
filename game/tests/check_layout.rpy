screen rm_raised_rails_qa(table):
    modal True
    zorder 500
    add Solid("#eee8da")
    text "实体围边 · 贴边遮挡检查" pos (312,150) size 38 color "#282c29"
    add table pos (312,380)

label rm_check_layout_preview:
    $ _autosave = False
    $ opening_active = False
    $ rm_ui_test_skin_active = False
    $ rm_player = rm_core.create_initial_character()
    $ rm_player.energy = 6
    $ rm_player.dice_pool = [rm_core.RMDice("layout_d6","dex",[3,3,3,5,5,6]),rm_core.RMDice("layout_d4","dex",[1,2,2,4]),rm_core.RMDice("layout_d8","dex",list(range(1,9))),rm_core.RMDice("layout_str","str",[1,2,3,4,5,6])]
    scene bg train_carriage
    show fro casual default at fro_casual_left
    jump story_1_1_3_help_thief

label rm_check_layout_schedule:
    $ _autosave = False
    $ rm_ui_test_skin_active = False
    $ rm_test_start_flow()
    $ rm_core.start_turn(rm_player,"morning_1")
    jump rm_test_schedule_choice

label rm_check_layout_wake:
    $ _autosave = False
    $ rm_ui_test_skin_active = False
    $ rm_test_start_flow()
    $ rm_core.start_turn(rm_player,"sleep_decision")
    $ rm_core.continue_night(rm_player)
    $ rm_core.advance_time_slot(rm_player)
    $ rm_core.continue_night(rm_player)
    $ rm_core.begin_sleep(rm_player,renpy.random)
    call rm_test_wake_flow
    return

testsuite check_layout:
    parameter (layout_width,layout_height) = [(1280,720),(1920,1080),(2560,1440)]
    parameter layout_prefs = [None]
    parameter layout_window = [None]
    before testcase:
        python:
            layout_prefs = (_preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size,_preferences.transitions)
            _preferences.afm_enable = False
            _preferences.transitions = 2
            layout_window = renpy.display.draw.info['max_window_size']
            renpy.display.draw.info['max_window_size'] = (max(layout_width,layout_window[0]),max(layout_height,layout_window[1]))
            renpy.set_physical_size((layout_width,layout_height))
    after testcase:
        python:
            _preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size,_preferences.transitions = layout_prefs
            renpy.display.draw.info['max_window_size'] = layout_window
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase check_layout.story_selection_and_cancel:
    run Start("rm_check_layout_preview")
    advance until screen "attribute_dice_select"
    run Function(renpy.set_physical_size,(layout_width,layout_height))
    assert eval renpy.get_physical_size() == (layout_width,layout_height)
    assert eval "我是不是应该做些什么" in renpy.get_screen_variable('thought','attribute_dice_select')
    screenshot (rm_check_ui_shot("layout-empty",layout_width,layout_height))
    python:
        layout_before = (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot)
    click id "check_die_layout_d6"
    assert id "check_slot_0"
    assert eval len(renpy.get_screen_variable('actual_ids','attribute_dice_select')) == 1
    assert id "check_probability"
    assert id "check_remaining"
    assert eval renpy.get_screen_variable('preview','attribute_dice_select')['success_probability'] is not None
    screenshot (rm_check_ui_shot("layout-one",layout_width,layout_height))
    click id "check_details"
    assert id "check_details_close"
    screenshot (rm_check_ui_shot("layout-details",layout_width,layout_height))
    click id "check_details_close"
    click id "check_details"
    keysym "K_ESCAPE"
    assert not id "check_details_close"
    assert screen "attribute_dice_select"
    assert eval (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot) == layout_before
    click id "check_slot_0"
    assert eval renpy.get_screen_variable('selected_die_ids','attribute_dice_select') == []
    click id "check_die_layout_d6"
    click id "check_die_layout_d4"
    click id "check_die_layout_d8"
    assert eval renpy.get_screen_variable('preview','attribute_dice_select')['remaining'] == 3
    assert id "check_slot_2"
    click id "check_tab_all"
    pause .4
    screenshot (rm_check_ui_shot("layout-three",layout_width,layout_height))
    click id "check_review"
    screenshot (rm_check_ui_shot("layout-confirm",layout_width,layout_height))
    click id "check_cancel"
    assert screen "attribute_dice_select"
    click id "check_back"
    assert screen "choice"
    assert "做！"
    assert "还是算了"
    assert not screen "attribute_check_roll_animation"
    assert eval (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot) == layout_before
    screenshot (rm_check_ui_shot("layout-story-back",layout_width,layout_height))
    click "做！"
    advance until screen "attribute_dice_select"
    assert eval renpy.get_screen_variable('selected_die_ids','attribute_dice_select') == []

testcase check_layout.schedule_cancel:
    run Start("rm_check_layout_schedule")
    assert screen "rm_test_schedule_select"
    python:
        layout_before = (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot)
    click "负重训练（测试）"
    assert screen "attribute_dice_select"
    click id "check_back"
    assert screen "rm_test_schedule_select"
    assert eval (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot) == layout_before

testcase check_layout.tabletop_camera_and_snap:
    run Start("rm_check_layout_preview")
    advance until screen "attribute_dice_select"
    python:
        import os
        layout_record = layout_width == 1280 and bool(os.environ.get('RM_TABLETOP_RECORD'))
    if eval layout_record:
        python:
            import subprocess
            layout_title = config.window_title
            config.window_title = "ReMemorial Tabletop QA"
            renpy.display.interface.set_window_caption(force=True)
        pause .3
        python:
            layout_video_log = open("E:/ChatGPT/Temp/rememorial-tabletop/video.log","w")
            layout_video_proc = subprocess.Popen([
                "D:/Program Files/Live2D Cubism 5.3/tools/ffmpeg/ffmpeg.exe",
                "-y","-hide_banner","-f","gdigrab","-framerate","30",
                "-i","title="+renpy.display.interface.window_caption,"-t","10","-an","-c:v","libopenh264",
                "-vf","crop=1280:720:0:0","-b:v","6M","-pix_fmt","yuv420p",
                "E:/ChatGPT/Temp/rememorial-tabletop/tabletop.mp4"],
                stdin=subprocess.DEVNULL,stdout=layout_video_log,stderr=layout_video_log,
                creationflags=subprocess.CREATE_NO_WINDOW)
        pause .6
    click id "check_die_layout_d6"
    if eval layout_record:
        pause .45
    click id "check_die_layout_d4"
    if eval layout_record:
        pause .45
    click id "check_die_layout_d8"
    pause .4
    python:
        layout_stage = renpy.get_screen_variable('selection_table','attribute_dice_select')
        layout_poses = [(tuple(b['p']),b['q']) for b in layout_stage.world['bodies']]
    assert eval all(tuple(b['p']) == tuple(b['snap_to']) for b in layout_stage.world['bodies'])
    if not eval layout_record:
        screenshot (rm_check_ui_shot("tabletop-selection",layout_width,layout_height))
    click id "check_review"
    click id "check_confirm"
    pause until screen "attribute_check_roll_animation" timeout 5
    python:
        layout_roll = renpy.get_screen_variable('roll_table','attribute_check_roll_animation')
    assert eval [(tuple(b['p']),b['q']) for b in layout_roll.world['bodies']] == layout_poses
    assert eval layout_roll.world['elapsed'] == 0
    pause .35
    assert eval 0 < layout_roll.camera_elapsed < .8
    if not eval layout_record:
        screenshot (rm_check_ui_shot("tabletop-orbit",layout_width,layout_height))
    pause until eval layout_roll.camera_elapsed >= .8 timeout 3
    assert eval [(tuple(b['p']),b['q']) for b in layout_roll.world['bodies']] == layout_poses
    if not eval layout_record:
        screenshot (rm_check_ui_shot("tabletop-overhead",layout_width,layout_height))
    if eval layout_record:
        pause .4
    click id "check_roll_action"
    pause until eval renpy.get_screen_variable('roll_finished','attribute_check_roll_animation') timeout 6
    if not eval layout_record:
        screenshot (rm_check_ui_shot("tabletop-result",layout_width,layout_height))
    if eval layout_record:
        pause .7
    click id "check_roll_action"
    assert screen "attribute_check_result"
    if eval layout_record:
        pause 1.5
        python:
            layout_video_proc.wait(timeout=10)
            layout_video_log.close()
            config.window_title = layout_title
            renpy.display.interface.set_window_caption(force=True)
            assert layout_video_proc.returncode == 0

testcase check_layout.shackles_and_limit:
    run Start("rm_check_layout_preview")
    advance until screen "attribute_dice_select"
    python:
        rm_player.find_die('layout_d4').enchantment = rm_core.ENCHANT_SHACKLE
        rm_player.disease_state = rm_core.DISEASE_DEPRESSION
        layout_rng = renpy.random.getstate()
    run Function(renpy.restart_interaction)
    click id "check_die_layout_d6"
    assert eval renpy.get_screen_variable('preview','attribute_dice_select')['limit'] == 2
    assert eval renpy.get_screen_variable('actual_ids','attribute_dice_select') == ['layout_d4','layout_d6']
    click id "check_die_layout_d8"
    assert eval renpy.get_screen_variable('selected_die_ids','attribute_dice_select') == ['layout_d6']
    assert eval renpy.get_screen_variable('actual_ids','attribute_dice_select') == ['layout_d4','layout_d6']
    click id "check_slot_0"
    assert eval renpy.get_screen_variable('actual_ids','attribute_dice_select') == ['layout_d4','layout_d6']
    assert eval renpy.random.getstate() == layout_rng
    screenshot (rm_check_ui_shot("layout-shackles",layout_width,layout_height))
    click id "check_back"
    assert screen "choice"

testcase check_layout.raised_rail_views:
    run Start("rm_check_layout_preview")
    advance until screen "attribute_dice_select"
    python:
        rail_table = RMRealtimeDice([dict(faces=tuple(range(1,7)),value=1,die_id=str(i)) for i in range(3)],selection=True)
        for body,xy in zip(rail_table.world['bodies'],[(-4.1,0),(0,-1.5),(4.1,0)]):
            body['p'] = [xy[0],xy[1],rm_dice_motion.floor_height(body)]
            body['snap_from'] = body['snap_to'] = list(body['p'])
    run Show("rm_raised_rails_qa",table=rail_table)
    pause .2
    screenshot (rm_check_ui_shot("raised-rails-oblique",layout_width,layout_height))
    python:
        rail_table.selection = False
        rail_table.camera_elapsed = .8
        for body,xy in zip(rail_table.world['bodies'],[(-4.1,0),(0,1.5),(4.1,0)]):
            body['p'][:2] = xy
        renpy.redraw(rail_table,0)
    pause .2
    screenshot (rm_check_ui_shot("raised-rails-overhead",layout_width,layout_height))
    assert eval all(abs(b['p'][0]) <= 4.1 and abs(b['p'][1]) <= 1.5 for b in rail_table.world['bodies'])
    run Hide("rm_raised_rails_qa")

testcase check_layout.wake_cancel:
    run Start("rm_check_layout_wake")
    advance until screen "choice"
    click "选择起床骰子"
    assert screen "attribute_dice_select"
    python:
        import copy
        layout_before = (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot,copy.deepcopy(rm_player.sleep_pending))
    click id "check_back"
    assert screen "choice"
    assert "选择起床骰子"
    assert not screen "attribute_check_roll_animation"
    assert eval (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot,rm_player.sleep_pending) == layout_before
