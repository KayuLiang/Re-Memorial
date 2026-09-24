# Actual game rendering; this fixture is never entered from the story.
screen rm_realtime_atlas_qa(table):
    zorder 500
    modal True
    add Solid("#888888")
    for atlas_row in range(2):
        add Transform(table.atlases[0],crop=(atlas_row*1280,0,1280,128)) pos (100,300+atlas_row*200)
        for atlas_i in range(11):
            add Solid("#ff0000") pos (100+128*atlas_i,300+atlas_row*200) xysize (1,128)
        add Solid("#ff0000") pos (100,364+atlas_row*200) xysize (1280,1)
    text "128 px face cells; red centerline" pos (100,200)

screen rm_d4_corner_qa():
    zorder 500
    modal True
    add Solid("#eee8da")
    text "D4 · 每面三角标 / 顶角读数" pos (120,20) size 38 color "#282c29"
    for slot in range(4):
        for overhead in range(2):
            add rm_live_stone((1,2,3,4),rm_live_atlas((1,2,3,4)),rm_dice_motion.landing_pose(RM_REALTIME_MODELS['4'],slot),rm_dice_motion.camera(overhead),520) pos (120+slot*570,80+overhead*620)
        text ("顶角 = "+str(slot+1)) pos (260+slot*570,610) size 32 color "#282c29"

label rm_roll_preview:
    $ _autosave = False
    $ opening_active = False
    $ rm_player = rm_core.create_initial_character()
    $ rm_player.energy = 20
    $ rm_player.dice_pool = [rm_core.RMDice("roll_%d" % n,"str", [1,1,2,2] if n==4 else list(range(1,n+1))) for n in roll_shapes]
    $ rm_player.dice_pool[0].enchantment = rm_core.ENCHANT_SWIFT
    if len(rm_player.dice_pool) > 1:
        $ rm_player.dice_pool[1].enchantment = rm_core.ENCHANT_SLUGGISH
    $ roll_ids = [d.id for d in rm_player.dice_pool]
    $ roll_core = rm_core.perform_check(rm_player,rm_core.CheckSpec("str",6,roll_ids,action_type=rm_core.ACTION_INSTANT),rng=renpy.random)
    $ roll_result = rm_test_result_dict_for_schedule(roll_core,rm_player,roll_ids,"test_strength_training")
    $ roll_rng = renpy.random.getstate()
    $ roll_faces = [list(d.faces) for d in rm_player.dice_pool]
    $ roll_energy = rm_player.energy
    scene bg doctor_office
    if roll_record:
        python:
            import subprocess
            roll_saved_title = config.window_title
            config.window_title = "ReMemorial Dice Roll QA"
        pause .3
        python:
            roll_video_log = open("E:/ChatGPT/Temp/rememorial-realtime-dice/video.log","w")
            roll_recorder = subprocess.Popen([
                "D:/Program Files/Live2D Cubism 5.3/tools/ffmpeg/ffmpeg.exe",
                "-y","-hide_banner","-f","gdigrab","-framerate","30",
                "-i","title=ReMemorial Dice Roll QA","-t","7","-an","-c:v","libopenh264",
                "-vf","crop=1280:720:0:0","-b:v","6M","-pix_fmt","yuv420p",
                "E:/ChatGPT/Temp/rememorial-realtime-dice/realtime-dice.mp4"],
                stdin=subprocess.DEVNULL,stdout=roll_video_log,stderr=roll_video_log,
                creationflags=subprocess.CREATE_NO_WINDOW)
        pause .8
    call screen attribute_check_roll_animation(roll_result)
    call screen attribute_check_result(roll_result)
    if roll_record:
        pause 1
        python:
            roll_recorder.wait(timeout=10)
            roll_video_log.close()
            config.window_title = roll_saved_title
            assert roll_recorder.returncode == 0
    "投掷测试完成。"
    return

testsuite dice_roll:
    parameter (roll_width,roll_height) = [(1280,720),(1920,1080),(2560,1440)]
    parameter roll_saved_preferences = [None]
    parameter roll_saved_window = [None]
    before testcase:
        python:
            roll_saved_preferences = (_preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size,_preferences.transitions)
            _preferences.afm_enable = False
            _preferences.transitions = 2
            roll_saved_window = renpy.display.draw.info['max_window_size']
            renpy.display.draw.info['max_window_size'] = (max(roll_width,roll_saved_window[0]),max(roll_height,roll_saved_window[1]))
            renpy.set_physical_size((roll_width,roll_height))
    after testcase:
        python:
            _preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size,_preferences.transitions = roll_saved_preferences
            renpy.display.draw.info['max_window_size'] = roll_saved_window
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase dice_roll.small:
    python:
        roll_shapes = (4,6,8)
        import os
        roll_record = roll_width == 1280 and bool(os.environ.get('RM_DICE_ROLL_RECORD'))
    run Start("rm_roll_preview")
    pause until screen "attribute_check_roll_animation" timeout 5
    assert id "check_roll_die_2"
    assert eval renpy.get_physical_size() == (roll_width,roll_height)
    assert eval renpy.get_screen_variable('roll_table','attribute_check_roll_animation').world['phase'] == 'ready'
    screenshot (rm_check_ui_shot("roll-ready",roll_width,roll_height))
    drag id "check_roll_table" pos (.45,.75) to id "check_roll_table" pos (.7,.2) steps 12
    if not eval roll_record:
        pause .25
        screenshot (rm_check_ui_shot("roll-small-air",roll_width,roll_height))
        pause .4
        screenshot (rm_check_ui_shot("roll-small-bounce",roll_width,roll_height))
    pause until eval renpy.get_screen_variable('roll_finished','attribute_check_roll_animation') timeout 6
    if not eval roll_record:
        screenshot (rm_check_ui_shot("roll-small-settled",roll_width,roll_height))
    assert eval renpy.get_screen_variable('roll_table','attribute_check_roll_animation').world['throws'] == 1
    click id "check_roll_action"
    pause until screen "attribute_check_result" timeout 5
    assert eval renpy.random.getstate() == roll_rng
    assert eval [list(d.faces) for d in rm_player.dice_pool] == roll_faces
    assert eval rm_player.energy == roll_energy
    assert eval [r['value'] for r in rm_check_rows(roll_result)] == [r['value'] for r in roll_core.dice_results]
    assert eval '取较高' in rm_check_rows(roll_result)[0]['attempts']
    assert eval '取较低' in rm_check_rows(roll_result)[1]['attempts']
    screenshot (rm_check_ui_shot("roll-reroll-result",roll_width,roll_height))
    click id "check_continue"
    if eval roll_record:
        pause 1.2

testcase dice_roll.large:
    python:
        roll_shapes = (10,12,20)
        roll_record = False
    run Start("rm_roll_preview")
    pause until screen "attribute_check_roll_animation" timeout 5
    assert id "check_roll_die_2"
    click id "check_roll_action"
    pause .35
    screenshot (rm_check_ui_shot("roll-large-air",roll_width,roll_height))
    pause until eval renpy.get_screen_variable('roll_finished','attribute_check_roll_animation') timeout 6
    screenshot (rm_check_ui_shot("roll-large-settled",roll_width,roll_height))
    click id "check_roll_action"
    pause until screen "attribute_check_result" timeout 5
    assert eval renpy.random.getstate() == roll_rng
    assert eval [list(d.faces) for d in rm_player.dice_pool] == roll_faces
    click id "check_continue"

testcase dice_roll.face_binding_and_reduced_motion:
    python:
        from collections import Counter
        for sides in (4,6,8,10,12,20):
            faces = ([1,1,2,2] if sides == 4 else list(range(1,sides+1)))
            for value in set(faces):
                table = RMRealtimeDice([dict(faces=faces,value=value)])
                body = table.world['bodies'][0]
                assert body['faces'][body['result_face']] == value
                assert Counter(body['faces']) == Counter(faces)
                assert rm_dice_motion.outcome(body['model'],body['target']) == body['result_face']
        roll_shapes = (6,)
        roll_record = False
        _preferences.transitions = 0
    run Start("rm_roll_preview")
    pause until screen "attribute_check_roll_animation" timeout 5
    assert id "check_roll_die_0"
    keysym "K_SPACE"
    assert eval renpy.get_screen_variable('roll_finished','attribute_check_roll_animation')
    screenshot (rm_check_ui_shot("roll-reduced",roll_width,roll_height))
    click id "check_roll_action"
    pause until screen "attribute_check_result" timeout 3
    assert eval renpy.random.getstate() == roll_rng
    click id "check_continue"

testcase dice_roll.save_and_menu_resume:
    python:
        roll_shapes = (6,12,20)
        roll_record = False
    run Start("rm_roll_preview")
    assert screen "attribute_check_roll_animation"
    run Function(renpy.save,"realtime-dice-qa")
    click id "check_roll_action"
    pause .2
    run Function(renpy.load,"realtime-dice-qa")
    assert screen "attribute_check_roll_animation"
    assert eval renpy.get_screen_variable('roll_table','attribute_check_roll_animation').world['phase'] == 'ready'
    click id "check_roll_action"
    pause .2
    run Function(renpy.save,"realtime-dice-moving-qa")
    keysym "K_ESCAPE"
    pause .25
    keysym "K_ESCAPE"
    assert screen "attribute_check_roll_animation"
    pause until eval renpy.get_screen_variable('roll_finished','attribute_check_roll_animation') timeout 6
    run Function(renpy.load,"realtime-dice-moving-qa")
    # Ren'Py resumes at call screen: replay the presentation of the saved
    # mechanical result, never perform_check or energy payment a second time.
    assert eval renpy.get_screen_variable('roll_table','attribute_check_roll_animation').world['phase'] == 'ready'
    assert eval [row['value'] for row in rm_check_rows(roll_result)] == [r['value'] for r in roll_core.dice_results]
    click id "check_roll_action"
    pause until eval renpy.get_screen_variable('roll_finished','attribute_check_roll_animation') timeout 6
    assert eval renpy.get_screen_variable('roll_table','attribute_check_roll_animation').world['throws'] == 1
    assert eval renpy.random.getstate() == roll_rng
    assert eval rm_player.energy == roll_energy
    click id "check_roll_action"
    assert screen "attribute_check_result"
    click id "check_continue"

testcase dice_roll.atlas_alignment:
    python:
        roll_shapes = (6,)
        roll_record = False
    run Start("rm_roll_preview")
    run Show("rm_realtime_atlas_qa",table=RMRealtimeDice([dict(faces=tuple(range(1,21)),value=6)]))
    screenshot (rm_check_ui_shot("roll-atlas",roll_width,roll_height))
    run Hide("rm_realtime_atlas_qa")

testcase dice_roll.confirmed_faces_survive_upgrade:
    python:
        roll_shapes = (6,)
        roll_record = False
    run Start("rm_roll_preview")
    python:
        roll_old_faces = tuple(rm_player.dice_pool[0].faces)
        rm_player.dice_pool[0].faces[:] = [16]*8
        roll_snapshot_rows = rm_check_rows(roll_result)
        roll_snapshot_table = RMRealtimeDice(roll_snapshot_rows)
    assert eval roll_snapshot_rows[0]['faces'] == roll_old_faces
    assert eval 'd6' in roll_snapshot_rows[0]['label']
    assert eval len(roll_snapshot_table.world['bodies'][0]['model']['faces']) == 6
    assert eval renpy.random.getstate() == roll_rng
    click id "check_roll_action"
    pause until eval renpy.get_screen_variable('roll_finished','attribute_check_roll_animation') timeout 6
    click id "check_roll_action"
    assert screen "attribute_check_result"
    python:
        roll_next = rm_core.roll_die(rm_player.dice_pool[0],rng=renpy.random)
    assert eval roll_next['faces'] == (16,)*8 and roll_next['value'] == 16
    click id "check_continue"

testcase dice_roll.d4_corner_readout:
    python:
        roll_shapes = (4,)
        roll_record = False
    run Start("rm_roll_preview")
    run Show("rm_d4_corner_qa")
    screenshot (rm_check_ui_shot("d4-corner-readout",roll_width,roll_height))
    run Hide("rm_d4_corner_qa")
    assert eval all(rm_dice_motion.outcome(RM_REALTIME_MODELS['4'],rm_dice_motion.landing_pose(RM_REALTIME_MODELS['4'],i)) == i for i in range(4))
