default opening_active = False


label complete_opening_sequence:
    $ opening_active = True
    call opening_scene_00
    $ opening_active = False
    hide screen opening_memory_overlay
    hide screen opening_flash_once
    hide screen crt_effect
    hide screen opening_system_desktop
    return


label opening_scene_00:
    scene black
    show screen opening_disclaimer_one
    $ renpy.pause(3.0, hard=True, modal=False)
    hide screen opening_disclaimer_one
    jump opening_scene_01


label opening_scene_01:
    scene black
    call screen opening_disclaimer_two
    jump opening_scene_02


label opening_scene_02:
    scene black
    call screen opening_tap_to_start
    jump opening_scene_03


label opening_scene_03:
    scene black
    call screen opening_water_wait
    call screen opening_water_drop(auto=True)
    call screen opening_water_drop(auto=True)
    call screen opening_water_drop(auto=True)
    jump opening_scene_04


label opening_scene_04:
    scene black
    centered "弗洛，弗洛——"
    pause 0.8
    jump opening_scene_05


label opening_scene_05:
    scene black
    show screen opening_flash_once
    pause 0.08
    hide screen opening_flash_once
    show screen opening_system_desktop("opening_loading_body")
    show screen crt_effect(mode="subtle")
    fro "我听到有人在叫我的名字。"
    jump opening_scene_06


label opening_scene_06:
    $ lines = []

    $ lines.append("一阵急促的脚步声。")
    show screen opening_memory_overlay(lines)
    pause 0.48

    $ lines.append("重物落地的闷响。")
    show screen opening_memory_overlay(lines)
    pause 0.52

    $ lines.append("“现场安全，患者雄性，意识模糊——”")
    show screen opening_memory_overlay(lines)
    pause 0.72

    hide screen opening_memory_overlay
    with Dissolve(0.30)
    $ opening_active = False
    hide screen crt_effect
    hide screen opening_system_desktop
    return
