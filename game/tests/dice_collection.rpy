# Isolated fixture only: never reached by the story and never writes saves.
label rm_dice_visual_preview:
    $ _autosave = False
    $ opening_active = False
    $ story_hud_hidden = False
    $ story_hud_character_panel_unlocked = True
    $ rm_player = rm_core.create_initial_character({"str":3,"dex":3,"int":2},rng=renpy.random)
    $ rm_player.dice_pool = [rm_core.RMDice("qa_%d_%s" % (n,a),a,([1,1,2,2] if n==4 else list(range(1,n+1)))) for n,a in ((6,"str"),(6,"dex"),(4,"con"),(8,"int"),(20,"pow"),(12,"str"),(10,"str"))]
    $ rm_player.dice_growth_progress = dict(zip(rm_dice_view.ORDER,(4,2,3,1,5)))
    $ story_hud_effects = []
    scene bg doctor_office
    show screen character_panel(start_tab="dice")
    while True:
        "骰组界面测试。"

testsuite dice_collection:
    parameter saved_dice_preferences = [None]
    parameter saved_dice_window = [None]
    parameter (dice_test_width,dice_test_height) = [(1920,1080),(1280,720),(2560,1440)]
    before testcase:
        python:
            saved_dice_preferences = (_preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size,_preferences.transitions)
            _preferences.afm_enable = False
            saved_dice_window = renpy.display.draw.info['max_window_size']
            renpy.display.draw.info['max_window_size'] = (max(dice_test_width,saved_dice_window[0]),max(dice_test_height,saved_dice_window[1]))
            renpy.set_physical_size((dice_test_width,dice_test_height))
    after testcase:
        python:
            _preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size,_preferences.transitions = saved_dice_preferences
            renpy.display.draw.info['max_window_size'] = saved_dice_window
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase dice_collection.pages:
    run Start("rm_dice_visual_preview")
    run Function(renpy.set_physical_size,(dice_test_width,dice_test_height))
    pause .3
    python:
        print("DICE_SIZE requested=%s actual=%s renderer=%s" % ((dice_test_width,dice_test_height),renpy.get_physical_size(),renpy.get_renderer_info()))
    assert eval renpy.get_physical_size() == (dice_test_width,dice_test_height)
    assert screen "character_panel"
    assert id "dice_distribution"
    assert not eval rm_hud_visible()
    python:
        dice_before = [(d.id,list(d.faces),d.enchantment) for d in rm_player.dice_pool]
        growth_before = dict(rm_player.dice_growth_progress)
    click id "dice_card_0"
    assert eval renpy.get_screen_variable("dice_mode","character_panel") == "collection"
    screenshot ("../../tmp/dice_collection/%dx%d/collection.png" % (dice_test_width,dice_test_height))
    click id "dice_card_0"
    pause 1.7
    assert id "dice_face_5"
    assert not id "dice_arc_next"
    assert id "dice_distribution"
    screenshot ("../../tmp/dice_collection/%dx%d/d6.png" % (dice_test_width,dice_test_height))
    click id "dice_face_4"
    assert eval renpy.get_screen_variable("dice_face","character_panel") == 4
    click id "dice_collapse"
    click id "dice_filter_int"
    click id "dice_card_0"
    click id "dice_card_0"
    pause 1.7
    assert id "dice_face_7"
    screenshot ("../../tmp/dice_collection/%dx%d/d8.png" % (dice_test_width,dice_test_height))
    click id "dice_back"
    click id "dice_filter_str"
    click id "dice_card_1"
    click id "dice_expand"
    pause 1.7
    assert id "dice_face_11"
    assert not id "dice_arc_next"
    screenshot ("../../tmp/dice_collection/%dx%d/d12.png" % (dice_test_width,dice_test_height))
    click id "dice_back"
    click id "dice_filter_pow"
    click id "dice_card_0"
    click id "dice_expand"
    pause 1.7
    assert id "dice_arc_next"
    keysym "K_END"
    pause .5
    assert id "dice_face_19"
    assert eval renpy.get_screen_variable("dice_face","character_panel") == 11
    click id "dice_face_19"
    assert eval renpy.get_screen_variable("dice_face","character_panel") == 19
    screenshot ("../../tmp/dice_collection/%dx%d/d20.png" % (dice_test_width,dice_test_height))
    keysym "K_ESCAPE"
    assert screen "character_panel"
    assert eval renpy.get_screen_variable("dice_mode","character_panel") == "collection"
    click id "dice_filter_con"
    run SetField(_preferences,"transitions",0)
    click id "dice_card_0"
    click id "dice_expand"
    pause 1.2
    assert id "dice_face_3"
    assert not id "dice_face_4"
    assert eval not _preferences.transitions
    assert eval rm_dice_view.distribution(rm_player.find_die('qa_4_con').faces) == [(1,2,.5),(2,2,.5),(3,0,0),(4,0,0)]
    screenshot ("../../tmp/dice_collection/%dx%d/d4-repeated.png" % (dice_test_width,dice_test_height))
    click id "dice_back"
    click id "dice_filter_str"
    click id "dice_card_2"
    click id "dice_expand"
    pause 1.2
    assert id "dice_face_9"
    assert not id "dice_arc_next"
    screenshot ("../../tmp/dice_collection/%dx%d/d10.png" % (dice_test_width,dice_test_height))
    click id "dice_back"
    click id "dice_tab_growth"
    click id "dice_growth_int"
    screenshot ("../../tmp/dice_collection/%dx%d/growth.png" % (dice_test_width,dice_test_height))
    click id "dice_growth_view"
    assert eval renpy.get_screen_variable("dice_filter","character_panel") == "int"
    click id "dice_enchantment"
    click id "dice_option_enchanted"
    assert id "dice_empty"
    click id "dice_enchantment"
    click id "dice_option_all"
    click id "dice_filter_all"
    click id "dice_sort"
    click id "dice_option_sides"
    click id "dice_page_next"
    assert eval renpy.get_screen_variable("dice_page","character_panel") == 1
    assert eval dice_before == [(d.id,list(d.faces),d.enchantment) for d in rm_player.dice_pool]
    assert eval growth_before == dict(rm_player.dice_growth_progress)
    click id "dice_close"
    assert not screen "character_panel"

# Unlike the page checks above, this exercises repeated entry and interrupted
# scrolling while the animations are still running. Optional native-window video.
testcase dice_collection.motion:
    run Start("rm_dice_visual_preview")
    run SetField(_preferences,"transitions",2)
    run Function(renpy.set_physical_size,(dice_test_width,dice_test_height))
    pause .5
    python:
        import os
        import subprocess
        motion_recorder = None
        if os.environ.get("RM_DICE_RECORD") and dice_test_width == 1280:
            motion_video = os.path.join(config.basedir,"tmp/dice_collection/dice-motion.mp4")
            motion_log = open(os.path.join(config.basedir,"tmp/dice_collection/motion-video.log"),"w")
            motion_recorder = subprocess.Popen([
                "D:/Program Files/Live2D Cubism 5.3/tools/ffmpeg/ffmpeg.exe",
                "-y","-hide_banner","-f","gdigrab","-framerate","30",
                "-i","title=ReMemorial","-t","20","-an","-c:v","libopenh264",
                "-vf","crop=1280:720:0:0","-b:v","6M","-pix_fmt","yuv420p",motion_video],
                stdin=subprocess.DEVNULL,stdout=motion_log,stderr=motion_log,
                creationflags=subprocess.CREATE_NO_WINDOW)
    pause 1
    click id "dice_filter_int"
    click id "dice_card_0"
    assert eval renpy.get_screen_variable("dice_mode","character_panel") == "collection"
    pause .5
    click id "dice_card_0"
    python:
        opened_once = renpy.get_screen_variable("dice_opened","character_panel")
    pause .25
    screenshot ("../../tmp/dice_collection/%dx%d/motion-entry-025.png" % (dice_test_width,dice_test_height))
    pause .4
    screenshot ("../../tmp/dice_collection/%dx%d/motion-entry-065.png" % (dice_test_width,dice_test_height))
    pause 1
    screenshot ("../../tmp/dice_collection/%dx%d/motion-entry-settled.png" % (dice_test_width,dice_test_height))
    assert eval rm_dice_elapsed(100,50) == 2.0
    assert eval rm_dice_scroll_position((0,11,100),50) == 11
    assert eval len(RMDiceArt([1,2,3,4],opened=0).frames) == len(RM_DICE_MODELS[4])
    click id "dice_face_5"
    pause .3
    assert eval renpy.get_screen_variable("dice_opened","character_panel") == opened_once
    click id "dice_back"
    pause .4
    click id "dice_card_0"
    pause .3
    assert eval renpy.get_screen_variable("dice_opened","character_panel") > opened_once
    screenshot ("../../tmp/dice_collection/%dx%d/motion-reentry.png" % (dice_test_width,dice_test_height))
    pause 1.4
    click id "dice_back"
    click id "dice_filter_pow"
    click id "dice_card_0"
    click id "dice_expand"
    pause 1.7
    scroll amount 1 pos (800,800)
    pause .15
    python:
        scrolling = renpy.get_screen_variable("dice_scroll","character_panel")
        assert 0 < rm_dice_scroll_position(scrolling,time.monotonic()) < 1
    screenshot ("../../tmp/dice_collection/%dx%d/motion-scroll.png" % (dice_test_width,dice_test_height))
    scroll amount -1 pos (800,800)
    pause .5
    assert eval renpy.get_screen_variable("dice_offset","character_panel") == 0
    keysym "K_END"
    pause .6
    click id "dice_face_19"
    assert eval renpy.get_screen_variable("dice_face","character_panel") == 19
    pause .5
    keysym "K_HOME"
    pause .6
    click id "dice_face_0"
    assert eval renpy.get_screen_variable("dice_face","character_panel") == 0
    pause .5
    click id "dice_back"
    # A card in the second row must start there, not from the first card's origin.
    click id "dice_filter_all"
    click id "dice_card_4"
    click id "dice_card_4"
    assert eval renpy.get_screen_variable("dice_origin","character_panel") == (715,930)
    pause 1.7
    keysym "K_ESCAPE"
    assert eval renpy.get_screen_variable("dice_mode","character_panel") == "collection"
    pause .5
    if eval motion_recorder is not None:
        pause until eval (motion_recorder.poll() is not None) timeout 25
    python:
        if motion_recorder is not None:
            motion_log.close()
            assert motion_recorder.poll() == 0
    click id "dice_close"
