# Reusable Win7 medical system shell for opening screens.

define opening_color_desktop = "#6f8078"
define opening_color_desktop_dark = "#46534f"
define opening_color_border = "#5b8db8"
define opening_color_border_dark = "#315f88"
define opening_color_paper = "#e7e4d9"
define opening_color_phosphor = "#a8c7aa"
define opening_scope_wave_span = 635
define opening_document_font = rememorial_ui_font


init python:
    renpy.music.register_channel("opening_foley", mixer="sfx", loop=False)

    def opening_play_sound(path, channel="sound", loop=False):
        if renpy.loadable(path):
            renpy.music.play(path, channel=channel, loop=loop)

    def opening_consent_at_bottom(adjustment):
        return (
            getattr(adjustment, "_opening_range_measured", False)
            and (
                adjustment.range <= 0
                or adjustment.value >= adjustment.range - 4
            )
        )

    def opening_consent_adjustment_ranged(adjustment):
        was_measured = getattr(adjustment, "_opening_range_measured", False)
        was_at_bottom = getattr(adjustment, "_opening_was_at_bottom", None)
        at_bottom = (
            adjustment.range <= 0
            or adjustment.value >= adjustment.range - 4
        )
        adjustment._opening_range_measured = True
        adjustment._opening_was_at_bottom = at_bottom
        if not was_measured or at_bottom != was_at_bottom:
            renpy.restart_interaction()
        return None

    def opening_consent_adjustment_changed(adjustment, value):
        at_bottom = adjustment.range <= 0 or value >= adjustment.range - 4
        was_at_bottom = getattr(adjustment, "_opening_was_at_bottom", False)
        if at_bottom != was_at_bottom:
            adjustment._opening_was_at_bottom = at_bottom
            renpy.restart_interaction()
        return None

    def opening_start_signature_hold():
        current_screen = renpy.current_screen()
        if current_screen is None:
            return

        scope = current_screen.scope
        scope["signature_started_at"] = renpy.get_game_runtime()
        scope["signature_holding"] = True
        scope["signature_progress"] = 0.0
        renpy.restart_interaction()


transform opening_scope_scroll(distance=opening_scope_wave_span):
    xoffset 0
    linear 4.8 xoffset -distance
    repeat


transform opening_ui_dimmed:
    matrixcolor TintMatrix("#b3b3b3")


screen opening_system_desktop(body_screen, body_args=None):
    zorder -10
    $ body_args = tuple(body_args or ())

    frame:
        style "opening_shell_desktop_frame"
        at opening_ui_dimmed

        add Solid(opening_color_desktop_dark) alpha 0.24

        frame:
            style "opening_shell_ghost_window_frame"

            vbox:
                spacing 13
                xfill True
                yfill True

                text "INTERVIEW_RECORD_04" style "opening_shell_ghost_title_text"
                text "ARCHIVE / CASE NOTES / RESTRICTED" style "opening_shell_ghost_body_text"
                text "RECOVERED MATERIAL INDEX  04" style "opening_shell_ghost_body_text"
                text "STATUS  STANDBY" style "opening_shell_ghost_body_text"

        use opening_window_frame(
            "市立精神卫生中心服务系统",
            body_screen,
            body_args=body_args,
        )

        frame:
            style "opening_shell_taskbar_frame"

            add Solid("#a8bfd0") xpos 0 ypos 0 xsize config.screen_width ysize 3

            frame:
                style "opening_shell_taskbar_content_frame"

                hbox:
                    xfill True
                    yfill True
                    spacing 19

                    frame:
                        style "opening_shell_taskbar_start_frame"

                        hbox:
                            spacing 11
                            xalign 0.5
                            yalign 0.5

                            text "⊕" style "opening_shell_taskbar_start_icon_text"
                            text "开始" style "opening_shell_taskbar_start_text"

                    frame:
                        style "opening_shell_taskbar_program_frame"

                        text "特殊治疗管理系统" style "opening_shell_taskbar_program_text"

                    null width 0 xfill True

                    vbox:
                        spacing 0
                        xalign 1.0
                        yalign 0.5

                        text "13:30" style "opening_shell_taskbar_time_text" xalign 1.0
                        text "2026-06-19 / 网络 / 待机" style "opening_shell_taskbar_status_text" xalign 1.0


screen opening_window_frame(title, body_screen, body_args=None):
    $ body_args = tuple(body_args or ())

    frame:
        style "opening_shell_window_outer_frame"

        frame:
            style "opening_shell_window_inner_frame"

            vbox:
                xfill True
                yfill True
                spacing 0

                frame:
                    style "opening_shell_title_bar_frame"

                    hbox:
                        xfill True
                        yalign 0.5

                        hbox:
                            spacing 13
                            yalign 0.5

                            text title style "opening_shell_title_text"
                            text "RECOVERY MODE" style "opening_shell_title_meta_text"

                        null width 0 xfill True

                        hbox:
                            spacing 5
                            yalign 0.5

                            frame:
                                style "opening_shell_window_control_frame"
                                text "—" style "opening_shell_window_control_text"

                            frame:
                                style "opening_shell_window_control_frame"
                                text "□" style "opening_shell_window_control_text"

                            frame:
                                style "opening_shell_window_close_frame"
                                text "×" style "opening_shell_window_control_text"

                frame:
                    style "opening_shell_menu_bar_frame"

                    hbox:
                        spacing 35
                        yalign 0.5

                        text "文件" style "opening_shell_menu_text"
                        text "查看" style "opening_shell_menu_text"
                        text "病历" style "opening_shell_menu_text"
                        text "监测" style "opening_shell_menu_text"
                        text "帮助" style "opening_shell_menu_text"

                frame:
                    style "opening_shell_window_body_frame"

                    use expression body_screen pass (*body_args)


screen opening_scope_wave_segment(segment_x):
    fixed:
        xpos segment_x
        xsize opening_scope_wave_span
        ysize 136

        for beat_x in range(0, opening_scope_wave_span, 91):
            add Solid(opening_color_phosphor + "b0") xpos beat_x ypos 83 xsize 37 ysize 3
            add Solid(opening_color_phosphor + "b0") xpos beat_x + 37 ypos 77 xsize 3 ysize 8
            add Solid(opening_color_phosphor + "b0") xpos beat_x + 40 ypos 77 xsize 11 ysize 3
            add Solid(opening_color_phosphor + "b0") xpos beat_x + 51 ypos 29 xsize 3 ysize 51
            add Solid(opening_color_phosphor + "b0") xpos beat_x + 53 ypos 29 xsize 4 ysize 3
            add Solid(opening_color_phosphor + "b0") xpos beat_x + 57 ypos 29 xsize 3 ysize 56
            add Solid(opening_color_phosphor + "b0") xpos beat_x + 60 ypos 83 xsize 31 ysize 3


screen opening_oscilloscope():
    frame:
        style "opening_shell_scope_panel_frame"

        fixed:
            xfill True
            yfill True
            clipping True

            text "BIO-SIGNAL MONITOR" style "opening_shell_scope_title_text" xpos 24 ypos 19

            for x in range(24, 629, 43):
                add Solid(opening_color_phosphor + "24") xpos x ypos 72 xsize 1 ysize 240

            for y in range(72, 313, 32):
                add Solid(opening_color_phosphor + "20") xpos 24 ypos y xsize 600 ysize 1

            viewport:
                xpos 24
                ypos 93
                xsize 600
                ysize 136
                draggable False
                mousewheel False
                clipping True

                fixed:
                    xsize opening_scope_wave_span * 2
                    ysize 136
                    at opening_scope_scroll

                    use opening_scope_wave_segment(0)
                    use opening_scope_wave_segment(opening_scope_wave_span)

            hbox:
                xpos 24
                ypos 264
                spacing 35

                text "HR  72" style "opening_shell_scope_metric_text"
                text "SpO2  98%" style "opening_shell_scope_metric_text"
                text "GAIN  x1" style "opening_shell_scope_metric_text"


style opening_shell_desktop_frame is frame:
    xfill True
    yfill True
    background Solid(opening_color_desktop)
    padding (0, 0)

style opening_shell_ghost_window_frame is frame:
    xpos 1920
    ypos 104
    xsize 480
    ysize 283
    background Solid(opening_color_desktop_dark + "d8")
    padding (24, 21, 24, 21)

style opening_shell_ghost_title_text is gui_text:
    size 31
    color opening_color_paper + "88"
    bold True

style opening_shell_ghost_body_text is gui_text:
    size 24
    color opening_color_paper + "68"

style opening_shell_window_outer_frame is frame:
    xpos 180
    ypos 127
    xsize 2120
    ysize 1040
    background Solid(opening_color_border_dark)
    padding (5, 5, 5, 5)

style opening_shell_window_inner_frame is frame:
    xfill True
    yfill True
    background Solid("#d6dbd8")
    padding (0, 0)

style opening_shell_title_bar_frame is frame:
    xfill True
    ysize 51
    background Solid(opening_color_border)
    padding (19, 8, 19, 8)

style opening_shell_title_text is gui_text:
    size 29
    color "#f2f7fb"
    bold True

style opening_shell_title_meta_text is gui_text:
    size 21
    color "#dbe8f3"

style opening_shell_window_control_frame is frame:
    xsize 40
    ysize 27
    background Solid("#85a7c5")
    padding (0, 0)

style opening_shell_window_close_frame is frame:
    xsize 40
    ysize 27
    background Solid("#b5707c")
    padding (0, 0)

style opening_shell_window_control_text is gui_text:
    size 23
    bold True
    color "#f7fbff"
    xalign 0.5
    yalign 0.5

style opening_shell_menu_bar_frame is frame:
    xfill True
    ysize 35
    background Solid("#edf2f5")
    padding (19, 4, 19, 4)

style opening_shell_menu_text is gui_text:
    size 23
    color "#435765"

style opening_shell_window_body_frame is frame:
    xfill True
    yfill True
    background Solid("#c5cbc7")
    padding (24, 24, 24, 24)
    clipping True

style opening_shell_scope_panel_frame is frame:
    xfill True
    yfill True
    background Solid("#51615a")
    padding (0, 0)

style opening_shell_scope_title_text is gui_text:
    size 27
    color opening_color_phosphor + "cc"
    bold True

style opening_shell_scope_metric_text is gui_text:
    size 24
    color opening_color_phosphor + "b4"

style opening_shell_taskbar_frame is frame:
    xpos 0
    ypos 1381
    xsize 2560
    ysize 59
    background Solid("#273138")
    padding (0, 0)

style opening_shell_taskbar_content_frame is frame:
    xfill True
    yfill True
    background None
    padding (19, 8, 19, 8)

style opening_shell_taskbar_start_frame is frame:
    xsize 117
    ysize 37
    background Solid("#405560")
    padding (13, 5, 13, 5)

style opening_shell_taskbar_start_icon_text is gui_text:
    size 27
    bold True
    color "#d8e7f3"

style opening_shell_taskbar_start_text is gui_text:
    size 23
    color "#edf4f8"

style opening_shell_taskbar_program_frame is frame:
    xsize 304
    ysize 37
    background Solid("#39434b")
    padding (16, 5, 16, 5)

style opening_shell_taskbar_program_text is gui_text:
    size 23
    color "#dde8ee"

style opening_shell_taskbar_status_text is gui_text:
    size 15
    color "#b8c7d2"

style opening_shell_taskbar_time_text is gui_text:
    size 19
    color "#e7eff5"


transform opening_prompt_blink:
    alpha 0.28
    linear 0.56 alpha 1.0
    linear 0.56 alpha 0.28
    repeat


transform opening_loading_soft_pulse(delay=0.0):
    alpha 0.2
    pause delay
    linear 0.24 alpha 1.0
    linear 0.44 alpha 0.2
    pause 0.24
    repeat


transform opening_drop_fall:
    xalign 0.5
    ypos -96
    alpha 0.0
    linear 0.08 alpha 1.0
    linear 0.48 ypos 645
    linear 0.06 alpha 0.0


screen opening_disclaimer_one():
    modal True

    add Solid("#000000")

    vbox:
        xalign 0.5
        yalign 0.5
        xsize 1840
        spacing 56

        text (
            "【免责声明】\n\n"
            "本作品为虚构故事。作品中的人物、团体、事件、医疗与心理描写均经过艺术加工；若与现实相似，均属巧合。\n\n"
            "本作品涉及精神疾病、创伤记忆、失忆、血腥暴力、自伤意念、死亡及其他可能引起不适的内容。相关描写不构成医学、心理、法律或其他专业建议，也不应在现实中模仿或尝试。\n\n"
            "本作品包含闪烁画面、快速转场、画面抖动、强对比图像等视觉刺激。若您曾有癫痫、晕厥、光敏反应或相关病史，请在游玩前咨询专业医师。游玩中如出现头晕、恶心、视物异常、抽搐、意识模糊或其他不适，请立即停止游玩并寻求帮助。\n\n"
            "继续游玩即表示您已阅读并理解以上内容。"
        ) style "opening_disclaimer_text"

        hbox:
            xalign 0.5
            spacing 37

            textbutton "是":
                style "opening_disclaimer_button"
                action Return(True)

            textbutton "否":
                style "opening_disclaimer_button"
                action [SetVariable("opening_active", False), MainMenu(confirm=False)]


screen opening_disclaimer_two():
    modal True

    add Solid("#000000")

    vbox:
        xalign 0.5
        yalign 0.5
        xsize 1760
        spacing 56

        text (
            "本作品包含闪烁画面、快速转场、画面抖动、强对比图像等视觉刺激。若您曾有癫痫、晕厥、光敏反应或相关病史，请在游玩前咨询专业医师。游玩中如出现头晕、恶心、视物异常、抽搐、意识模糊或其他不适，请立即停止游玩并寻求帮助。\n\n"
            "继续游玩即表示您已阅读并理解以上内容。"
        ) style "opening_disclaimer_text"

        hbox:
            xalign 0.5
            spacing 37

            textbutton "是":
                style "opening_disclaimer_button"
                action Return(True)

            textbutton "否":
                style "opening_disclaimer_button"
                action [SetVariable("opening_active", False), MainMenu(confirm=False)]


screen opening_tap_to_start():
    modal True

    add Solid("#000000")

    button:
        style "opening_clear_fullscreen_button"
        action Return()

    key "dismiss" action Return()

    text "TAP TO START" at opening_prompt_blink:
        style "opening_tap_prompt_text"


screen opening_water_wait():
    modal True

    add Solid("#000000")

    button:
        style "opening_clear_fullscreen_button"
        action Return()

    key "dismiss" action Return()


screen opening_water_drop(auto=True):
    modal True

    add Solid("#000000")

    if auto:
        timer 1.10 action Return()
    else:
        button:
            style "opening_clear_fullscreen_button"
            action Return()
        key "dismiss" action Return()

    text "●" at opening_drop_fall:
        style "opening_water_drop_text"


screen opening_flash_once():
    zorder 120
    add Solid("#ffffff")


screen opening_memory_overlay(lines):
    zorder 30

    add Solid("#00000080")

    vbox:
        xalign 0.5
        yalign 0.5
        xsize 1707
        spacing 24

        for line in lines:
            text line style "opening_memory_text"


screen opening_loading_body():
    hbox:
        xfill True
        yfill True
        spacing 32

        frame:
            style "opening_loading_panel_frame"

            vbox:
                xfill True
                yfill True
                spacing 27

                text "SYSTEM INITIAL LOAD" style "opening_loading_heading_text"

                text "正在建立神经恢复链路。" style "opening_loading_body_text"
                text "正在同步基础生命体征。" style "opening_loading_body_text"
                text "正在加载记忆缓冲区……" style "opening_loading_body_text"

                hbox:
                    spacing 13

                    text "■" at opening_loading_soft_pulse(0.00):
                        style "opening_loading_indicator_text"

                    text "■" at opening_loading_soft_pulse(0.12):
                        style "opening_loading_indicator_text"

                    text "■" at opening_loading_soft_pulse(0.24):
                        style "opening_loading_indicator_text"

                text "LOADING / LINKING / STABILIZING" style "opening_loading_status_text"

        use opening_oscilloscope


screen opening_records_body(progress, status_text):
    hbox:
        xfill True
        yfill True
        spacing 32

        frame:
            style "opening_records_panel_frame"

            fixed:
                xfill True
                yfill True

                frame:
                    style "opening_records_back_page_frame"
                    xpos 69
                    ypos 51

                frame:
                    style "opening_records_back_page_frame"
                    xpos 35
                    ypos 25

                frame:
                    style "opening_records_front_page_frame"

                    vbox:
                        xfill True
                        yfill True
                        spacing 24

                        text "病历 / 访谈 / 诊断记录" style "opening_records_heading_text"
                        text "CASE FILE  ████████" style "opening_records_meta_text"
                        text "精神状态校准记录" style "opening_records_line_text"
                        text "近期访谈归档" style "opening_records_line_text"
                        text "基础认知恢复评估" style "opening_records_line_text"

                        null height 0 yfill True

                        text status_text style "opening_records_status_text"
                        bar value StaticValue(progress, 100.0) style "opening_records_progress_bar"
                        text "[progress]%" style "opening_records_percent_text"

        use opening_oscilloscope


screen opening_notice_body(message):
    hbox:
        xfill True
        yfill True
        spacing 32

        frame:
            style "opening_notice_panel_frame"

            vbox:
                xfill True
                yfill True
                spacing 32

                text "SYSTEM NOTICE" style "opening_notice_meta_text"
                add Solid(opening_color_border_dark) xsize 1013 ysize 5
                text message style "opening_notice_message_text"
                null height 0 yfill True
                text "市立精神卫生中心 / SERVICE TERMINAL" style "opening_notice_footer_text"

        use opening_oscilloscope


screen opening_verification_body(status_text, progress):
    hbox:
        xfill True
        yfill True
        spacing 32

        frame:
            style "opening_verification_panel_frame"

            vbox:
                xfill True
                yfill True
                spacing 32

                text "SYSTEM VERIFICATION" style "opening_verification_meta_text"
                add Solid(opening_color_border_dark) xsize 1013 ysize 5

                null height 0 yfill True

                text status_text style "opening_verification_status_text"
                bar value StaticValue(progress, 100.0) style "opening_verification_progress_bar"
                text "[progress]%" style "opening_verification_percent_text"

                null height 0 yfill True

                text "NEURAL LINK / MEDICAL UNIT / CONSCIOUSNESS" style "opening_verification_footer_text"

        use opening_oscilloscope


screen opening_countdown(number):
    zorder 200

    add Solid("#000000")

    text "[number]":
        xalign 0.5
        yalign 0.5
        size 192
        color "#ffffff"
        bold True


screen opening_consent_body():
    hbox:
        xfill True
        yfill True
        spacing 32

        frame:
            style "opening_consent_preview_frame"

            vbox:
                xfill True
                yfill True
                spacing 19

                text "市立精神卫生中心" style "opening_consent_center_text"
                text "特殊治疗知情同意书" style "opening_consent_title_text"
                add Solid("#627168") xsize 1133 ysize 3 xalign 0.5
                text "姓名：弗洛　性别：男　年龄：24" style "opening_consent_preview_text"
                text "病历号：████████" style "opening_consent_preview_text"
                text "患者已知悉并理解以上信息。" style "opening_consent_note_text"
                text "请核对个人信息。" style "opening_consent_note_text"
                text "请确认签署。" style "opening_consent_note_text"

        frame:
            style "opening_consent_side_frame"

            vbox:
                spacing 27
                xfill True

                text "DOCUMENT STATUS" style "opening_notice_meta_text"
                text "等待患者阅读全文" style "opening_consent_side_text"
                text "滚轮 / 拖动滚动条" style "opening_consent_side_text"
                null height 0 yfill True
                use opening_oscilloscope


screen opening_consent_document():
    modal True
    zorder 20
    style_prefix "opening_consent"
    default consent_adjustment = ui.adjustment(raw_changed=opening_consent_adjustment_changed, ranged=opening_consent_adjustment_ranged)

    frame:
        style "opening_consent_dialog_frame"

        vbox:
            xfill True
            yfill True
            spacing 16

            viewport:
                xfill True
                ysize 763
                yadjustment consent_adjustment
                mousewheel True
                draggable True
                scrollbars "vertical"

                vbox:
                    xsize 1867
                    spacing 19

                    text "市立精神卫生中心" style "opening_consent_center_text"
                    text "特殊治疗知情同意书" style "opening_consent_title_text"
                    text "姓名：弗洛；性别：男；年龄：24；病历号：████████；诊断：█████████████████；拟行治疗：███████；治疗日期：████年██月██日" style "opening_consent_document_text"

                    text "一、治疗目的" style "opening_consent_section_text"
                    text "因患者目前存在████、████、████及████能力下降等情况，拟实施本次治疗，以稳定精神状态、降低风险，并协助患者恢复基本生活与认知功能。" style "opening_consent_document_text"

                    text "二、治疗方式" style "opening_consent_section_text"
                    text "治疗过程中可能使用镇静、监测、████、精神状态校准及必要的辅助药物。具体方案将由医师根据患者情况调整。" style "opening_consent_document_text"

                    text "三、可能风险" style "opening_consent_section_text"
                    text "本治疗可能出现以下情况：" style "opening_consent_document_text"
                    text "头痛、恶心、乏力、嗜睡；" style "opening_consent_document_text"
                    text "短暂████或███障碍；" style "opening_consent_document_text"
                    text "近期或远期████；" style "opening_consent_document_text"
                    text "情绪波动、焦虑、恐惧或抑郁加重；" style "opening_consent_document_text"
                    text "对████、████或████产生混淆；" style "opening_consent_document_text"
                    text "治疗效果不佳，需追加治疗或调整方案；" style "opening_consent_document_text"
                    text "极少数情况下可能发生严重不良反应，甚至危及生命。" style "opening_consent_document_text"

                    text "四、替代方案" style "opening_consent_section_text"
                    text "患者及家属已知悉可选择药物治疗、心理治疗、观察治疗、转院治疗或暂缓治疗。但延误治疗可能导致病情加重或出现其他风险。" style "opening_consent_document_text"

                    text "五、信息核对" style "opening_consent_section_text"
                    text "患者确认，已如实提供并核对个人信息、病史资料、诊断信息、拟行治疗项目及初始评估结果。" style "opening_consent_document_text"
                    text "上述信息一经签署，将作为本次治疗及后续系统评估的依据。如有遗漏、错误或隐瞒，患者及家属/监护人已知悉可能产生相应风险。" style "opening_consent_document_text"
                    text "姓名：弗洛；性别：男；年龄：24；ID：██████████████████" style "opening_consent_document_text"
                    text "初始属性（剩余可分配点数：x）" style "opening_consent_document_text"
                    text "力量 灵巧 体质 智识 意志" style "opening_consent_document_text"
                    text "患者已知悉并理解以上信息。" style "opening_consent_note_text"
                    text "请核对个人信息。" style "opening_consent_note_text"

                    text "六、患者声明" style "opening_consent_section_text"
                    text "本人已阅读并理解以上内容。医务人员已向本人说明治疗目的、方式、风险、替代方案及可能后果。本人知悉本治疗不保证██████，不保证完全消除症状。" style "opening_consent_document_text"
                    text "本人自愿接受本次治疗。" style "opening_consent_document_text"
                    text "患者签名：______________；家属/监护人签名：______________；医师签名：______________；日期：████年██月██日" style "opening_consent_document_text"
                    text "请确认签署。" style "opening_consent_note_text"

            textbutton "下一页":
                style "opening_consent_next_button"
                sensitive opening_consent_at_bottom(consent_adjustment)
                action Return()


screen opening_identity_preview_body():
    hbox:
        xfill True
        yfill True
        spacing 32

        frame:
            style "opening_identity_preview_frame"

            vbox:
                xfill True
                yfill True
                spacing 24

                text "个人信息核对" style "opening_consent_title_text"
                add Solid("#627168") xsize 1133 ysize 3 xalign 0.5
                text "姓名：弗洛" style "opening_identity_field_text"
                text "性别：男" style "opening_identity_field_text"
                text "年龄：24" style "opening_identity_field_text"
                text "ID：████████" style "opening_identity_field_text"

                hbox:
                    spacing 24
                    text "治疗日期：" style "opening_identity_field_text" yalign 0.5
                    frame:
                        background Solid("#526158")
                        padding (4, 4, 4, 4)

                        frame:
                            xsize 227
                            ysize 56
                            background Solid(opening_color_paper)
                            padding (0, 0, 0, 0)

                null height 0 yfill True
                text "请核对个人信息。" style "opening_consent_note_text"

        frame:
            style "opening_consent_side_frame"

            vbox:
                spacing 27
                xfill True

                text "IDENTITY VERIFICATION" style "opening_notice_meta_text"
                text "等待患者确认" style "opening_consent_side_text"
                text "术前资料 / 初始评估" style "opening_consent_side_text"
                null height 0 yfill True
                use opening_oscilloscope


screen opening_name_insert():
    modal True
    zorder 50

    add Solid("#000000")

    timer 0.8 action Return()

    button:
        style "opening_clear_fullscreen_button"
        action Return()

    key "dismiss" action Return()

    text "弗洛":
        xalign 0.5
        yalign 0.5
        size 77
        color "#ffffff"


screen opening_date_insert():
    modal True
    zorder 50

    add Solid("#000000")

    timer 0.8 action Return()

    button:
        style "opening_clear_fullscreen_button"
        action Return()

    key "dismiss" action Return()

    frame:
        xalign 0.5
        yalign 0.5
        xsize 200
        ysize 200
        background Solid("#ffffff")
        padding (7, 7, 7, 7)

        frame:
            xfill True
            yfill True
            background Solid("#000000")
            padding (0, 0, 0, 0)


screen opening_stat_row(label_text, stat_name, value, locked=False):
    frame:
        style "opening_stat_row_frame"

        hbox:
            xfill True
            yalign 0.5
            spacing 21

            text label_text style "opening_stat_label_text"
            text "[value]" style "opening_stat_value_text"
            null width 0 xfill True

            if locked:
                text "固定" style "opening_stat_locked_text"
            else:
                textbutton "−":
                    style "opening_stat_button"
                    sensitive opening_can_adjust_stat(stat_name, -1)
                    action Function(opening_adjust_stat, stat_name, -1)

                textbutton "+":
                    style "opening_stat_button"
                    sensitive opening_can_adjust_stat(stat_name, 1)
                    action Function(opening_adjust_stat, stat_name, 1)


screen opening_identity_body(signature_hovered, signature_progress):
    hbox:
        xfill True
        yfill True
        spacing 40

        vbox:
            xsize 813
            spacing 20

            text "个人信息核对" style "opening_consent_title_text"
            add Solid("#627168") xsize 800 ysize 3 xalign 0.5
            text "姓名：弗洛" style "opening_identity_field_text"
            text "性别：男" style "opening_identity_field_text"
            text "年龄：24" style "opening_identity_field_text"
            text "ID：████████" style "opening_identity_field_text"

            hbox:
                spacing 24
                text "治疗日期：" style "opening_identity_field_text" yalign 0.5
                frame:
                    background Solid("#526158")
                    padding (4, 4, 4, 4)

                    frame:
                        xsize 227
                        ysize 56
                        background Solid(opening_color_paper)
                        padding (0, 0, 0, 0)

            null height 0 yfill True
            text "确认后，初始属性无法更改。" style "opening_consent_note_text"

        vbox:
            xfill True
            yfill True
            spacing 12

            text "初始属性" style "opening_consent_section_text"
            use opening_stat_row("体质", "con", rm_opening_attribute_value("con"), locked=True)
            use opening_stat_row("力量", "str", rm_opening_attribute_value("str"))
            use opening_stat_row("灵巧", "dex", rm_opening_attribute_value("dex"))
            use opening_stat_row("智识", "int", rm_opening_attribute_value("int"))
            use opening_stat_row("意志", "pow", rm_opening_attribute_value("pow"), locked=True)
            text "剩余可分配点数：[opening_stat_points_remaining()]" style "opening_identity_remaining_text"

            frame:
                style "opening_signature_frame"
                background Solid("#6f8d79" if signature_hovered else "#617e6d")

                fixed:
                    xfill True
                    yfill True

                    frame:
                        xfill True
                        yfill True
                        background None
                        padding (29, 20, 29, 20)

                        vbox:
                            xfill True
                            spacing 11

                            if opening_stats_complete():
                                text "按住确认 1.5 秒完成签名" style "opening_signature_text"
                            else:
                                text "请先分配全部属性点" style "opening_signature_text"

                            bar value StaticValue(signature_progress, 1.5) style "opening_signature_progress_bar"

                    mousearea:
                        area (0, 0, 1.0, 1.0)
                        hovered SetScreenVariable("signature_hovered", True)
                        unhovered [
                            SetScreenVariable("signature_hovered", False),
                            SetScreenVariable("signature_holding", False),
                            SetScreenVariable("signature_progress", 0.0),
                            SetScreenVariable("signature_started_at", None),
                        ]


screen opening_identity_document():
    modal True
    zorder 20
    default signature_hovered = False
    default signature_holding = False
    default signature_progress = 0.0
    default signature_complete = False
    default signature_started_at = None

    $ signature_elapsed = 0.0
    if signature_holding and signature_started_at is not None:
        $ signature_elapsed = max(
            0.0,
            min(1.5, renpy.get_game_runtime() - signature_started_at),
        )

    key "mousedown_1" action If(
        signature_hovered and opening_stats_complete() and not signature_complete,
        Function(opening_start_signature_hold),
        NullAction(),
    )
    key "mouseup_1" action If(
        signature_holding
        and signature_started_at is not None
        and opening_stats_complete()
        and not signature_complete
        and renpy.get_game_runtime() - signature_started_at >= 1.5,
        [
            SetScreenVariable("signature_holding", False),
            SetScreenVariable("signature_progress", 1.5),
            SetScreenVariable("signature_complete", True),
            SetScreenVariable("signature_started_at", None),
            Return(),
        ],
        [
            SetScreenVariable("signature_holding", False),
            SetScreenVariable("signature_progress", 0.0),
            SetScreenVariable("signature_started_at", None),
        ],
    )

    if signature_holding:
        timer 0.05 repeat True action If(
            opening_stats_complete()
            and signature_started_at is not None
            and not signature_complete,
            If(
                renpy.get_game_runtime() - signature_started_at >= 1.5,
                [
                    SetScreenVariable("signature_progress", 1.5),
                    SetScreenVariable("signature_holding", False),
                    SetScreenVariable("signature_complete", True),
                    SetScreenVariable("signature_started_at", None),
                    Return(),
                ],
                SetScreenVariable("signature_progress", signature_elapsed),
            ),
            [
                SetScreenVariable("signature_holding", False),
                SetScreenVariable("signature_progress", 0.0),
                SetScreenVariable("signature_started_at", None),
            ],
        )

    frame:
        style "opening_identity_document_frame"

        use opening_identity_body(signature_hovered, signature_progress)


style opening_disclaimer_text is gui_text:
    xalign 0.0
    text_align 0.0
    size 40
    color "#f2f2f2"
    line_spacing 13
    xfill True
    outlines [(3, "#000000", 0, 0)]

style opening_disclaimer_button is button:
    background Solid("#1f1f1f")
    hover_background Solid("#343434")
    xminimum 240
    yminimum 83
    padding (32, 16, 32, 16)

style opening_disclaimer_button_text is gui_text:
    size 37
    color "#f8f8f8"
    xalign 0.5
    yalign 0.5

style opening_clear_fullscreen_button is button:
    background None
    hover_background None
    xfill True
    yfill True
    padding (0, 0, 0, 0)

style opening_tap_prompt_text is gui_text:
    xalign 0.5
    yalign 0.5
    size 72
    color "#f3f3f3"
    bold True
    kerning 11
    outlines [(4, "#000000", 0, 0)]

style opening_water_drop_text is gui_text:
    size 64
    color "#f1f1f1"
    outlines [(3, "#000000", 0, 0)]

# The project layered Ming font does not include a true handwritten style, so this
# uses italic + wider kerning and a softened gray-white color.
# and a softened gray-white color to approximate a drifting memory script.
style opening_memory_text is gui_text:
    size 44
    color "#d8d2ca"
    italic True
    kerning 3
    text_align 0.5
    xalign 0.5
    outlines [(3, "#00000060", 0, 0)]

style opening_loading_panel_frame is frame:
    xsize 1213
    yfill True
    background Solid("#d8ddd8")
    padding (45, 40, 45, 40)

style opening_loading_heading_text is gui_text:
    size 45
    color "#5c6261"
    bold True
    kerning 3

style opening_loading_body_text is gui_text:
    size 32
    color "#666d6a"
    line_spacing 5

style opening_loading_indicator_text is gui_text:
    size 40
    color "#909694"

style opening_loading_status_text is gui_text:
    size 28
    color "#7c8380"
    kerning 3

style opening_records_panel_frame is frame:
    xsize 1213
    yfill True
    background Solid("#b8c1bb")
    padding (27, 27, 27, 27)

style opening_records_back_page_frame is frame:
    xsize 1053
    ysize 760
    background Solid("#c9c8bb")
    padding (0, 0)

style opening_records_front_page_frame is frame:
    xsize 1053
    ysize 760
    background Solid(opening_color_paper)
    padding (43, 37, 43, 37)

style opening_records_heading_text is gui_text:
    size 41
    color "#46564d"
    bold True

style opening_records_meta_text is gui_text:
    font opening_document_font
    size 24
    color "#7a817c"
    kerning 1

style opening_records_line_text is gui_text:
    size 32
    color "#56635b"

style opening_records_status_text is gui_text:
    size 33
    color "#3f6552"
    bold True

style opening_records_progress_bar is bar:
    xsize 947
    ysize 35
    left_bar Solid("#729b83")
    right_bar Solid("#b9c1bb")

style opening_records_percent_text is gui_text:
    size 24
    color "#65736a"
    xalign 1.0

style opening_notice_panel_frame is frame:
    xsize 1213
    yfill True
    background Solid("#d7ddd8")
    padding (59, 53, 59, 53)

style opening_notice_meta_text is gui_text:
    size 25
    color "#6f7c75"
    bold True
    kerning 3

style opening_notice_message_text is gui_text:
    size 45
    color "#40574b"
    line_spacing 11

style opening_notice_footer_text is gui_text:
    size 21
    color "#7b8580"

style opening_verification_panel_frame is frame:
    xsize 1213
    yfill True
    background Solid("#d7ddd8")
    padding (59, 53, 59, 53)

style opening_verification_meta_text is gui_text:
    size 25
    color "#6f7c75"
    bold True
    kerning 3

style opening_verification_status_text is gui_text:
    size 51
    color "#40574b"
    bold True
    xalign 0.5
    text_align 0.5

style opening_verification_progress_bar is bar:
    xfill True
    ysize 45
    left_bar Solid("#729b83")
    right_bar Solid("#b9c1bb")

style opening_verification_percent_text is gui_text:
    size 29
    color "#65736a"
    xalign 1.0

style opening_verification_footer_text is gui_text:
    size 21
    color "#7b8580"
    kerning 1

style opening_consent_preview_frame is frame:
    xsize 1373
    yfill True
    background Solid(opening_color_paper)
    padding (56, 40, 56, 40)

style opening_consent_side_frame is frame:
    xfill True
    yfill True
    background Solid("#5f6f68")
    padding (27, 27, 27, 27)

style opening_consent_side_text is gui_text:
    size 27
    color "#c3d1c6"

style opening_consent_dialog_frame is frame:
    xpos 204
    ypos 237
    xsize 2072
    ysize 907
    background Solid(opening_color_paper)
    padding (45, 32, 45, 32)

style opening_consent_vscrollbar is vscrollbar:
    xsize 24
    base_bar Solid("#4d5a52")
    thumb Solid("#617e6d")

style opening_consent_center_text is gui_text:
    size 31
    color "#45564d"
    bold True
    xalign 0.5
    text_align 0.5

style opening_consent_title_text is gui_text:
    size 45
    color "#34483d"
    bold True
    xalign 0.5
    text_align 0.5

style opening_consent_preview_text is gui_text:
    font opening_document_font
    size 29
    color "#4f5c54"

style opening_consent_section_text is gui_text:
    size 33
    color "#3d5046"
    bold True
    top_margin 11

style opening_consent_document_text is gui_text:
    font opening_document_font
    size 27
    color "#4a564f"
    line_spacing 7
    xsize 1813

style opening_consent_note_text is gui_text:
    size 25
    color "#667c70"
    italic True

style opening_consent_next_button is button:
    xalign 1.0
    xminimum 240
    yminimum 64
    background Solid("#617e6d")
    hover_background Solid("#769682")
    insensitive_background Solid("#a8aea9")
    padding (32, 12, 32, 12)

style opening_consent_next_button_text is gui_text:
    size 31
    color "#f4f2e8"
    insensitive_color "#d8d8d1"
    xalign 0.5
    yalign 0.5

style opening_identity_preview_frame is frame:
    xsize 1373
    yfill True
    background Solid(opening_color_paper)
    padding (56, 40, 56, 40)

style opening_identity_document_frame is frame:
    xpos 204
    ypos 237
    xsize 2072
    ysize 907
    background Solid(opening_color_paper)
    padding (51, 40, 51, 40)

style opening_identity_field_text is gui_text:
    font opening_document_font
    size 33
    color "#46574e"

style opening_stat_row_frame is frame:
    xfill True
    ysize 76
    background Solid("#d5d8ce")
    padding (21, 9, 21, 9)

style opening_stat_label_text is gui_text:
    xsize 123
    size 31
    color "#405248"
    bold True
    yalign 0.5

style opening_stat_value_text is gui_text:
    xsize 77
    size 33
    color "#33493d"
    bold True
    text_align 0.5
    yalign 0.5

style opening_stat_locked_text is gui_text:
    xsize 176
    size 27
    color "#7a827c"
    text_align 0.5
    yalign 0.5

style opening_stat_button is button:
    xsize 83
    ysize 56
    background Solid("#617e6d")
    hover_background Solid("#769682")
    insensitive_background Solid("#afb5b0")
    padding (11, 4, 11, 4)

style opening_stat_button_text is gui_text:
    size 39
    color "#f4f2e8"
    insensitive_color "#d8d8d1"
    xalign 0.5
    yalign 0.5

style opening_identity_remaining_text is gui_text:
    size 29
    color "#41584b"
    bold True
    xalign 1.0

style opening_signature_frame is frame:
    xfill True
    ysize 131
    background Solid("#617e6d")
    padding (0, 0, 0, 0)

style opening_signature_text is gui_text:
    size 29
    color "#f4f2e8"
    xalign 0.5
    text_align 0.5

style opening_signature_progress_bar is bar:
    xfill True
    ysize 24
    left_bar Solid("#d7e4d8")
    right_bar Solid("#40564a")
