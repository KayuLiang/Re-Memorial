default opening_active = False


label complete_opening_sequence:
    $ opening_active = True
    jump opening_scene_00


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
    $ opening_play_sound("audio/opening/water_drop_primary.ogg")
    call screen opening_water_drop(auto=True)
    $ opening_play_sound("audio/opening/water_drop_soft.ogg")
    call screen opening_water_drop(auto=True)
    $ opening_play_sound("audio/opening/water_drop_soft.ogg")
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
    $ hue_separation_start("glitch", scope="fullscreen")
    show screen crt_effect(mode="subtle")
    fro "我听到有人在叫我的名字。"
    jump opening_scene_06


label opening_scene_06:
    $ lines = []

    $ opening_play_sound("audio/opening/footsteps_urgent.ogg")
    $ lines.append("一阵急促的脚步声。")
    show screen opening_memory_overlay(lines)
    pause 0.48

    $ opening_play_sound("audio/opening/heavy_impact.ogg")
    $ lines.append("重物落地的闷响。")
    show screen opening_memory_overlay(lines)
    pause 0.52

    $ opening_play_sound("audio/opening/emergency_radio.ogg")
    $ lines.append("“现场安全，患者雄性，意识模糊——”")
    show screen opening_memory_overlay(lines)
    pause 0.72

    hide screen opening_memory_overlay
    with Dissolve(0.30)
    jump opening_scene_07


label opening_scene_07:
    show screen crt_effect(mode="interference")
    $ opening_play_sound("audio/opening/electrical_burst.ogg")
    show screen opening_system_desktop("opening_notice_body", ("精神卫生系统已介入。",))
    system "精神卫生系统已介入。"
    pause 0.28
    show screen opening_system_desktop("opening_notice_body", ("载入中。",))
    system "载入中。"
    jump opening_scene_08


label opening_scene_08:
    $ opening_play_sound("audio/opening/keyboard_fast.ogg")
    show screen opening_system_desktop("opening_records_body", (12, "正在整理病历……"))
    pause 0.34

    show screen opening_system_desktop("opening_records_body", (31, "正在校准心境……"))
    pause 0.32

    $ opening_play_sound("audio/opening/paper_flip.ogg")
    show screen opening_system_desktop("opening_records_body", (49, "正在归档记忆……"))
    pause 0.36

    show screen opening_system_desktop("opening_records_body", (68, "正在写入访谈记录……"))
    pause 0.34

    $ opening_play_sound("audio/opening/electronic_low.ogg")
    show screen opening_system_desktop("opening_records_body", (91, "正在恢复基础认知……"))
    pause 0.38

    show screen opening_flash_once
    pause 0.06
    hide screen opening_flash_once
    show screen opening_system_desktop("opening_records_body", (100, "载入完成。"))
    pause 0.18
    jump opening_scene_09


label opening_scene_09:
    $ lines = []

    $ opening_play_sound("audio/opening/wind_gap.ogg")
    $ lines.append("风掠过车窗缝隙的尖啸。")
    show screen opening_memory_overlay(lines)
    pause 0.48

    $ opening_play_sound("audio/opening/stretcher_wheels.ogg")
    $ opening_play_sound("audio/opening/metal_scrape.ogg", channel="opening_foley")
    $ lines.append("金属的滚轮快速摩擦地面的叮铃声，担架床吱呀好像就要散架。")
    show screen opening_memory_overlay(lines)
    pause 0.62

    $ opening_play_sound("audio/opening/handoff_shout.ogg")
    $ lines.append("“交接！手术室准备！”")
    show screen opening_memory_overlay(lines)
    pause 0.52

    $ opening_play_sound("audio/opening/isolation_door.ogg")
    $ lines.append("然后是厚实的隔离门缓缓关上。")
    show screen opening_memory_overlay(lines)
    pause 0.72

    hide screen opening_memory_overlay
    with Dissolve(0.34)
    jump opening_scene_10


label opening_scene_10:
    show screen crt_effect(mode="subtle")
    show screen opening_system_desktop("opening_notice_body", ("您好，这里是市立精神卫生中心服务系统，请仔细阅读术前须知。",))
    system "您好，这里是市立精神卫生中心服务系统，请仔细阅读术前须知。"
    jump opening_scene_11


label opening_scene_11:
    show screen opening_system_desktop("opening_consent_body")
    fro "应该怎么做？"
    system "请滑动滚轮以阅读全文。"
    fro "然后呢？"
    system "点击屏幕下方的‘下一页’按钮。"
    call screen opening_consent_document
    jump opening_scene_12


label opening_scene_12:
    show screen opening_system_desktop("opening_identity_preview_body")
    system "请核对个人信息。"
    fro "姓名——"

    show screen opening_name_insert
    pause 0.8
    hide screen opening_name_insert
    show screen opening_system_desktop("opening_identity_preview_body")

    fro "日期——"

    show screen opening_date_insert
    pause 0.8
    hide screen opening_date_insert
    show screen opening_system_desktop("opening_identity_preview_body")

    fro "上面的初始属性——这是什么？"
    system "关于你在这场手术中物质的使用，一经确认无法更改，请保证你充分利用它们的价值。"
    system "个人信息确认无误后，请长按‘确认’按钮完成签名。"
    call screen opening_identity_document

    jump opening_scene_13


label opening_scene_13:
    show screen crt_effect(mode="interference")
    show screen opening_system_desktop("opening_verification_body", ("核验通过。", 35))
    pause 0.35
    show screen opening_system_desktop("opening_verification_body", ("医疗单元已就位。", 72))
    pause 0.35
    show screen opening_system_desktop("opening_verification_body", ("意识将在 3 秒内重启。", 100))
    pause 0.35

    hide screen crt_effect
    show screen crt_effect(mode="shutdown")
    pause 0.45

    $ hue_separation_stop()
    hide screen opening_system_desktop
    hide screen opening_memory_overlay
    hide screen opening_flash_once
    hide screen opening_countdown
    hide screen crt_effect
    scene black
    jump opening_scene_14


label opening_scene_14:
    $ renpy.music.stop(channel="sound")
    $ renpy.music.stop(channel="opening_foley")
    scene black
    show screen opening_countdown(3)
    pause 0.8
    hide screen opening_countdown
    show screen opening_countdown(2)
    pause 0.8
    hide screen opening_countdown
    show screen opening_countdown(1)
    pause 0.8
    hide screen opening_countdown

    scene black
    $ renpy.pause(2.5, hard=True, modal=False)

    hide screen opening_disclaimer_one
    hide screen opening_disclaimer_two
    hide screen opening_tap_to_start
    hide screen opening_water_wait
    hide screen opening_water_drop
    hide screen opening_countdown
    hide screen opening_memory_overlay
    hide screen opening_flash_once
    hide screen opening_consent_document
    hide screen opening_name_insert
    hide screen opening_date_insert
    hide screen opening_identity_document
    hide screen opening_system_desktop
    $ opening_active = False
    hide screen crt_effect
    jump mountain_memory_start
