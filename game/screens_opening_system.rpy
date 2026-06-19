# Reusable Win7 medical system shell for opening screens.

define opening_color_desktop = "#6f8078"
define opening_color_desktop_dark = "#46534f"
define opening_color_border = "#5b8db8"
define opening_color_border_dark = "#315f88"
define opening_color_paper = "#e7e4d9"
define opening_color_phosphor = "#a8c7aa"
define opening_scope_wave_span = 476


transform opening_scope_scroll(distance=opening_scope_wave_span):
    xoffset 0
    linear 4.8 xoffset -distance
    repeat


screen opening_system_desktop(body_screen, body_args=None):
    zorder 8
    $ body_args = tuple(body_args or ())

    frame:
        style "opening_shell_desktop_frame"

        add Solid(opening_color_desktop_dark) alpha 0.24

        frame:
            style "opening_shell_ghost_window_frame"

            vbox:
                spacing 10
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

            add Solid("#a8bfd0") xpos 0 ypos 0 xsize config.screen_width ysize 2

            frame:
                style "opening_shell_taskbar_content_frame"

                hbox:
                    xfill True
                    yfill True
                    spacing 14

                    frame:
                        style "opening_shell_taskbar_start_frame"

                        hbox:
                            spacing 8
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
                            spacing 10
                            yalign 0.5

                            text title style "opening_shell_title_text"
                            text "RECOVERY MODE" style "opening_shell_title_meta_text"

                        null width 0 xfill True

                        hbox:
                            spacing 4
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
                        spacing 26
                        yalign 0.5

                        text "文件" style "opening_shell_menu_text"
                        text "查看" style "opening_shell_menu_text"
                        text "病历" style "opening_shell_menu_text"
                        text "监测" style "opening_shell_menu_text"
                        text "帮助" style "opening_shell_menu_text"

                frame:
                    style "opening_shell_window_body_frame"

                    use expression body_screen pass (*body_args)


screen opening_oscilloscope():
    frame:
        style "opening_shell_scope_panel_frame"

        fixed:
            xfill True
            yfill True
            clipping True

            text "BIO-SIGNAL MONITOR" style "opening_shell_scope_title_text" xpos 18 ypos 14

            for x in range(18, 472, 32):
                add Solid(opening_color_phosphor + "24") xpos x ypos 54 xsize 1 ysize 180

            for y in range(54, 235, 24):
                add Solid(opening_color_phosphor + "20") xpos 18 ypos y xsize 450 ysize 1

            viewport:
                xpos 18
                ypos 70
                xsize 450
                ysize 102
                draggable False
                mousewheel False
                clipping True

                fixed:
                    xsize opening_scope_wave_span * 2
                    ysize 102

                    text "▁▁▂▅▂▁▁▁▂▆▂▁▁▁▂▅▂▁▁▁▂▇▂▁▁▁▂▅▂▁▁▁▂▆▂▁▁▁▂▅▂▁▁▁▂▇▂▁" style "opening_shell_scope_wave_text" at opening_scope_scroll
                    text "▁▁▂▅▂▁▁▁▂▆▂▁▁▁▂▅▂▁▁▁▂▇▂▁▁▁▂▅▂▁▁▁▂▆▂▁▁▁▂▅▂▁▁▁▂▇▂▁" style "opening_shell_scope_wave_text" xpos opening_scope_wave_span at opening_scope_scroll

            hbox:
                xpos 18
                ypos 198
                spacing 26

                text "HR  72" style "opening_shell_scope_metric_text"
                text "SpO2  98%" style "opening_shell_scope_metric_text"
                text "GAIN  x1" style "opening_shell_scope_metric_text"


screen opening_shell_preview_body():
    hbox:
        xfill True
        yfill True
        spacing 24

        frame:
            style "opening_shell_preview_paper_frame"

            vbox:
                spacing 16
                xfill True
                yfill True

                text "电休克治疗知情同意确认书" style "opening_shell_preview_heading_text"
                text "患者姓名：弗洛" style "opening_shell_preview_body_text"
                text "档案号：INTERVIEW_RECORD_04" style "opening_shell_preview_body_text"
                text "病历正文占位。后续任务可在此区域接入左侧约 68% 的病历、表单或访谈内容。" style "opening_shell_preview_body_text"
                text "该纸张区域保持旧纸色、硬边裁切和轻微像素感，不越出主窗口正文边界。" style "opening_shell_preview_body_text"

        frame:
            style "opening_shell_preview_scope_frame"

            use opening_oscilloscope


style opening_shell_desktop_frame is frame:
    xfill True
    yfill True
    background Solid(opening_color_desktop)
    padding (0, 0)

style opening_shell_ghost_window_frame is frame:
    xpos 1440
    ypos 78
    xsize 360
    ysize 212
    background Solid(opening_color_desktop_dark + "d8")
    padding (18, 16, 18, 16)

style opening_shell_ghost_title_text is gui_text:
    size 23
    color opening_color_paper + "88"
    bold True

style opening_shell_ghost_body_text is gui_text:
    size 18
    color opening_color_paper + "68"

style opening_shell_window_outer_frame is frame:
    xpos 135
    ypos 95
    xsize 1590
    ysize 780
    background Solid(opening_color_border_dark)
    padding (4, 4, 4, 4)

style opening_shell_window_inner_frame is frame:
    xfill True
    yfill True
    background Solid("#d6dbd8")
    padding (0, 0)

style opening_shell_title_bar_frame is frame:
    xfill True
    ysize 38
    background Solid(opening_color_border)
    padding (14, 6, 14, 6)

style opening_shell_title_text is gui_text:
    size 22
    color "#f2f7fb"
    bold True

style opening_shell_title_meta_text is gui_text:
    size 16
    color "#dbe8f3"

style opening_shell_window_control_frame is frame:
    xsize 30
    ysize 20
    background Solid("#85a7c5")
    padding (0, 0)

style opening_shell_window_close_frame is frame:
    xsize 30
    ysize 20
    background Solid("#b5707c")
    padding (0, 0)

style opening_shell_window_control_text is gui_text:
    size 17
    bold True
    color "#f7fbff"
    xalign 0.5
    yalign 0.5

style opening_shell_menu_bar_frame is frame:
    xfill True
    ysize 26
    background Solid("#edf2f5")
    padding (14, 3, 14, 3)

style opening_shell_menu_text is gui_text:
    size 17
    color "#435765"

style opening_shell_window_body_frame is frame:
    xfill True
    yfill True
    background Solid("#c5cbc7")
    padding (18, 18, 18, 18)
    clipping True

style opening_shell_preview_paper_frame is frame:
    xsize 1030
    yfill True
    background Solid(opening_color_paper)
    padding (34, 30, 34, 30)

style opening_shell_preview_scope_frame is frame:
    xfill True
    yfill True
    background Solid("#5f6f68")
    padding (12, 12, 12, 12)

style opening_shell_preview_heading_text is gui_text:
    size 31
    color "#415248"
    bold True

style opening_shell_preview_body_text is gui_text:
    size 22
    color "#4d5a52"
    line_spacing 5

style opening_shell_scope_panel_frame is frame:
    xfill True
    yfill True
    background Solid("#51615a")
    padding (0, 0)

style opening_shell_scope_title_text is gui_text:
    size 20
    color opening_color_phosphor + "cc"
    bold True

style opening_shell_scope_wave_text is gui_text:
    size 34
    color opening_color_phosphor + "c0"

style opening_shell_scope_metric_text is gui_text:
    size 18
    color opening_color_phosphor + "b4"

style opening_shell_taskbar_frame is frame:
    xpos 0
    ypos 1036
    xsize 1920
    ysize 44
    background Solid("#273138")
    padding (0, 0)

style opening_shell_taskbar_content_frame is frame:
    xfill True
    yfill True
    background None
    padding (14, 6, 14, 6)

style opening_shell_taskbar_start_frame is frame:
    xsize 88
    ysize 28
    background Solid("#405560")
    padding (10, 4, 10, 4)

style opening_shell_taskbar_start_icon_text is gui_text:
    size 20
    bold True
    color "#d8e7f3"

style opening_shell_taskbar_start_text is gui_text:
    size 17
    color "#edf4f8"

style opening_shell_taskbar_program_frame is frame:
    xsize 228
    ysize 28
    background Solid("#39434b")
    padding (12, 4, 12, 4)

style opening_shell_taskbar_program_text is gui_text:
    size 17
    color "#dde8ee"

style opening_shell_taskbar_status_text is gui_text:
    size 11
    color "#b8c7d2"

style opening_shell_taskbar_time_text is gui_text:
    size 14
    color "#e7eff5"


transform opening_prompt_blink:
    alpha 0.28
    linear 0.28 alpha 1.0
    linear 0.28 alpha 0.28
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
    ypos -72
    alpha 0.0
    linear 0.08 alpha 1.0
    linear 0.48 ypos 484
    linear 0.06 alpha 0.0


transform opening_ripple_expand:
    xalign 0.5
    ypos 474
    alpha 0.0
    zoom 0.18
    pause 0.46
    linear 0.06 alpha 0.82 zoom 0.34
    linear 0.42 alpha 0.0 zoom 2.15


screen opening_disclaimer_one():
    modal True

    add Solid("#000000")

    text (
        "【免责声明】\n\n"
        "本作品为虚构故事。作品中的人物、团体、事件、医疗与心理描写均经过艺术加工；若与现实相似，均属巧合。\n\n"
        "本作品涉及精神疾病、创伤记忆、失忆、血腥暴力、自伤意念、死亡及其他可能引起不适的内容。相关描写不构成医学、心理、法律或其他专业建议，也不应在现实中模仿或尝试。"
    ) style "opening_disclaimer_text"


screen opening_disclaimer_two():
    modal True

    add Solid("#000000")

    vbox:
        xalign 0.5
        yalign 0.5
        xsize 1320
        spacing 42

        text (
            "本作品包含闪烁画面、快速转场、画面抖动、强对比图像等视觉刺激。若您曾有癫痫、晕厥、光敏反应或相关病史，请在游玩前咨询专业医师。游玩中如出现头晕、恶心、视物异常、抽搐、意识模糊或其他不适，请立即停止游玩并寻求帮助。\n\n"
            "继续游玩即表示您已阅读并理解以上内容。"
        ) style "opening_disclaimer_text"

        hbox:
            xalign 0.5
            spacing 28

            textbutton "是":
                style "opening_disclaimer_button"
                action Return(True)

            textbutton "否":
                style "opening_disclaimer_button"
                action MainMenu(confirm=False)


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

    text "○" at opening_ripple_expand:
        style "opening_water_ripple_text"


screen opening_flash_once():
    zorder 120
    add Solid("#ffffff")


screen opening_memory_overlay(lines):
    zorder 30

    add Solid("#00000080")

    vbox:
        xalign 0.5
        yalign 0.5
        xsize 1280
        spacing 18

        for line in lines:
            text line style "opening_memory_text"


screen opening_loading_body():
    hbox:
        xfill True
        yfill True
        spacing 24

        frame:
            style "opening_loading_panel_frame"

            vbox:
                xfill True
                yfill True
                spacing 20

                text "SYSTEM INITIAL LOAD" style "opening_loading_heading_text"

                text "正在建立神经恢复链路。" style "opening_loading_body_text"
                text "正在同步基础生命体征。" style "opening_loading_body_text"
                text "正在加载记忆缓冲区……" style "opening_loading_body_text"

                hbox:
                    spacing 10

                    text "■" at opening_loading_soft_pulse(0.00):
                        style "opening_loading_indicator_text"

                    text "■" at opening_loading_soft_pulse(0.12):
                        style "opening_loading_indicator_text"

                    text "■" at opening_loading_soft_pulse(0.24):
                        style "opening_loading_indicator_text"

                text "LOADING / LINKING / STABILIZING" style "opening_loading_status_text"

        use opening_oscilloscope


style opening_disclaimer_text is gui_text:
    xalign 0.5
    yalign 0.5
    text_align 0.5
    size 30
    color "#f2f2f2"
    line_spacing 10
    xsize 1380
    outlines [(2, "#000000", 0, 0)]

style opening_disclaimer_button is button:
    background Solid("#1f1f1f")
    hover_background Solid("#343434")
    xminimum 180
    yminimum 62
    padding (24, 12, 24, 12)

style opening_disclaimer_button_text is gui_text:
    size 28
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
    size 54
    color "#f3f3f3"
    bold True
    kerning 8
    outlines [(3, "#000000", 0, 0)]

style opening_water_drop_text is gui_text:
    size 48
    color "#f1f1f1"
    outlines [(2, "#000000", 0, 0)]

style opening_water_ripple_text is gui_text:
    size 64
    color "#d7d7d7"
    outlines [(2, "#000000", 0, 0)]

# SourceHanSansLite does not include 楷体, so this uses italic + wider kerning
# and a softened gray-white color to approximate a drifting memory script.
style opening_memory_text is gui_text:
    size 33
    color "#d8d2ca"
    italic True
    kerning 2
    text_align 0.5
    xalign 0.5
    outlines [(2, "#00000060", 0, 0)]

style opening_loading_panel_frame is frame:
    xsize 910
    yfill True
    background Solid("#d8ddd8")
    padding (34, 30, 34, 30)

style opening_loading_heading_text is gui_text:
    size 34
    color "#5c6261"
    bold True
    kerning 2

style opening_loading_body_text is gui_text:
    size 24
    color "#666d6a"
    line_spacing 4

style opening_loading_indicator_text is gui_text:
    size 30
    color "#909694"

style opening_loading_status_text is gui_text:
    size 21
    color "#7c8380"
    kerning 2
