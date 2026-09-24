# Flat old-object HUD. Positions are native 2560x1440 pixels.
# Common edges/centres/baselines, not a forced number of equal columns.
define RM_HUD_LEFT = 64
define RM_HUD_RIGHT = 2496
define RM_HUD_TOP = 43
define RM_HUD_METERS_X = 576
define RM_HUD_TRACK_X = 640
define RM_HUD_TRACK_WIDTH = 720
define RM_HUD_ENERGY_WIDTH = 480
define RM_HUD_NAV_X = 1684
define RM_HUD_NAV_STEP = 171
define RM_HUD_SIDE_Y = 363
define RM_HUD_DIALOGUE_Y = 1067
define RM_HUD_IVORY = "#f3eee3"
define RM_HUD_INK = "#292923"

# Presentation inputs only. The story owns content; absent data stays absent.
default story_hud_date_text = ""
default story_hud_weekday_text = ""
default story_hud_hidden = False
default story_hud_quests = []
default story_hud_effects = []

init python:
    import re as rm_hud_re
    import math as rm_hud_math

    class RMHealthRing(renpy.Displayable):
        """Progress stroke only; keep the approved library heart and 85px bounds."""
        def __init__(self, fraction, **kwargs):
            super(RMHealthRing, self).__init__(**kwargs)
            self.fraction = fraction

        def render(self, width, height, st, at):
            result = renpy.Render(85, 85)
            canvas = result.canvas()
            if self.fraction > 0:
                steps = max(2, int(160 * self.fraction))
                radius = 29 * 85 / 64.0
                points = [(42.5 + radius * rm_hud_math.sin(2 * rm_hud_math.pi * self.fraction * i / steps),
                           42.5 - radius * rm_hud_math.cos(2 * rm_hud_math.pi * self.fraction * i / steps))
                          for i in range(steps + 1)]
                canvas.lines("#f3eee3", False, points, 3)
            return result

    def rm_hud_visible():
        return not (main_menu or opening_active or story_hud_hidden or rm_ui_test_skin_active or renpy.get_screen([
            "character_panel", "inventory_panel", "medicine_panel", "phone_panel",
            "phone_panel_background", "rm_test_console", "rm_hud_details",
            "attribute_dice_select", "attribute_check_roll_animation",
            "attribute_check_result", "rm_test_schedule_select", "story_centered_mask",
            "rm_test_pending_die_choice", "rm_test_pending_card_choice", "rm_test_pending_face_choice",
        ]))

    def rm_hud_sync_story_time(time_text):
        # Read the timestamp already authored by the story; no invented calendar.
        match = rm_hud_re.search(r"(\d+)月(\d+)日\s+星期([一二三四五六日天]).*?(\d{1,2})[：:](\d{2})", time_text)
        if match:
            month, day, weekday, hour, minute = match.groups()
            store.story_hud_date_text = "{}月{}日".format(int(month), int(day))
            store.story_hud_weekday_text = "周" + weekday
            store.current_time_minutes = int(hour) * 60 + int(minute)

    def rm_hud_clock_data():
        player = rm_ensure_player()
        if rm_test_flow_active:
            count, index = rm_core.action_clock_progress(player)
            return ("", "周" + "一二三四五六日"[(player.weekday - 1) % 7], rm_test_day,
                    count, index)
        # Punched holes count action rounds only; meals/decisions are given by dialogue.
        count, index = rm_core.action_clock_progress(player) if player.current_time_slot is not None else (0, 0)
        return (story_hud_date_text, story_hud_weekday_text, player.day, count, index)

    def rm_hud_fraction(value, maximum):
        return max(0.0, min(1.0, float(value) / maximum)) if maximum > 0 else 0.0

screen rm_flat_status():
    default meter_tip = None
    if rm_hud_visible() and story_hud_status_unlocked:
        $ status_mood = rm_status_mood_value()
        $ status_energy = rm_status_energy_points()
        $ status_energy_max = rm_status_energy_max()
        $ status_health, status_health_max = rm_status_health()
        $ date_text, weekday_text, day_number, round_count, round_index = rm_hud_clock_data()
        use rm_hud_clock(date_text, weekday_text, day_number, round_count, round_index)
        vbox:
            id "hud_environment"
            pos (RM_HUD_LEFT + 27, 280)
            spacing 6
            for environment_line in rm_status_environment():
                frame:
                    style "rm_status_slip"
                    padding (1, 1)
                    frame:
                        background "#f3eee3"
                        padding (9, 2)
                        ysize 34
                        text environment_line style "rm_status_name" size 25 substitute False

        # Mood is longest; the short energy meter and reserved rings share y205.
        add "gui/hud_flat/neuron.svg" pos (544, 32)
        add "gui/hud_flat/mood_track.svg" pos (635, 85)
        add "gui/hud_flat/needle.svg":
            pos (RM_HUD_TRACK_X + int(rm_hud_fraction(status_mood + 200, 400) * RM_HUD_TRACK_WIDTH), 101)
            anchor (.5, .5)

        add "gui/hud_flat/lightning_track.svg" pos (RM_HUD_METERS_X, 171)
        if status_energy > 0:
            add Crop((0, 0, 64 + int(rm_hud_fraction(status_energy, status_energy_max) * RM_HUD_ENERGY_WIDTH), 69), "gui/hud_flat/lightning_fill.svg") pos (RM_HUD_METERS_X, 171)
        add "gui/hud_flat/needle.svg":
            pos (RM_HUD_TRACK_X + int(rm_hud_fraction(status_energy, status_energy_max) * RM_HUD_ENERGY_WIDTH), 205)
            anchor (.5, .5)

        add "gui/hud_flat/heart_reserved.svg" pos (1163, 163)
        add RMHealthRing(rm_hud_fraction(status_health, status_health_max)) pos (1163, 163)
        add "gui/hud_flat/star_reserved.svg" pos (1280, 163)

        for tip_x, tip_y, tip_width, tip_height, tip_text in ((560, 59, 816, 75, rm_status_mood_tooltip()), (560, 171, 581, 69, rm_status_energy_tooltip()), (1163, 163, 85, 85, rm_status_health_tooltip()), (1280, 163, 85, 85, "魔力：预留，尚未启用。")):
            button:
                pos (tip_x, tip_y)
                xysize (tip_width, tip_height)
                background None
                hover_background None
                padding (0, 0)
                alt tip_text
                action SetLocalVariable("meter_tip", tip_text)
                hovered SetLocalVariable("meter_tip", tip_text)
                unhovered SetLocalVariable("meter_tip", None)
        if meter_tip:
            frame:
                pos (RM_HUD_METERS_X, 309)
                xmaximum 800
                padding (21, 16)
                background "#292923f2"
                text meter_tip size 29 color RM_HUD_IVORY:
                    id "hud_meter_tip"


screen rm_hud_clock(date_text, weekday_text, day_number, round_count, round_index):
    zorder 95
    $ minutes = current_time_minutes % 1440
    $ clock_mode = "night" if minutes >= 23 * 60 or minutes < 6 * 60 else "day"
    $ clock_color = "#cd5047" if clock_mode == "night" else RM_HUD_IVORY
    $ clock_digits = "{:02d}{:02d}".format(minutes // 60, minutes % 60)
    fixed:
        pos (RM_HUD_LEFT, RM_HUD_TOP)
        xysize (448, 224)
        add "gui/hud_flat/clock_case.svg"
        text date_text pos (27, 16) size 32 color clock_color
        text weekday_text xpos 421 ypos 16 xanchor 1.0 size 32 color clock_color
        for i, digit_x in enumerate((72, 139, 232, 299)):
            add "gui/hud_flat/digit_[clock_mode]_[clock_digits[i]].svg" pos (digit_x, 64) xysize (64, 85)
        add "gui/hud_flat/colon_[clock_mode].svg" pos (205, 64) xysize (19, 85)
        for hole in range(round_count):
            $ hole_state = "past" if hole < round_index else ("current" if hole == round_index else "future")
            add "gui/hud_flat/hole_[hole_state].svg" pos (24 + hole * 25, 177)
        text "第[day_number]天" xpos 421 ypos 173 xanchor 1.0 size 29 color clock_color


screen rm_flat_navigation():
    if rm_hud_visible():
        # Keep each slot fixed even before its story unlock.
        fixed:
            pos (RM_HUD_NAV_X, RM_HUD_TOP)
            xysize (812, 160)
            if story_hud_medicine_unlocked:
                use rm_hud_nav_item(0, "pill", "药盒", Show("medicine_panel"))
            if "手机" in inventory:
                use rm_hud_nav_item(1, "device-mobile", "手机", Show("phone_panel"))
            if story_hud_inventory_unlocked:
                use rm_hud_nav_item(2, "backpack", "背包", Show("inventory_panel"))
            if story_hud_character_panel_unlocked:
                use rm_hud_nav_item(3, "dice-five", "骰组", Show("character_panel", start_tab="dice"))
                use rm_hud_nav_item(4, "user-square", "人物", Show("character_panel"))
        if rm_test_flow_active:
            textbutton "操作台" pos (RM_HUD_NAV_X, 229) style "rm_hud_text_button" action Show("rm_test_console")


screen rm_hud_nav_item(slot, icon, caption, target):
    button:
        id ("hud_nav_" + icon)
        pos (slot * RM_HUD_NAV_STEP, 0)
        xysize (128, 160)
        padding (0, 0)
        background None
        hover_background None
        action target
        alt caption
        fixed:
            add ("gui/hud_flat/" + icon + "_idle.svg") pos (16, 5)
            text caption style "rm_hud_white_text" xalign .5 ypos 112
        hover_foreground Solid("#f3eee318")


screen rm_flat_sides():
    if rm_hud_visible() and story_hud_status_unlocked:
        if story_hud_quests:
            vbox:
                pos (RM_HUD_LEFT, RM_HUD_SIDE_Y)
                xsize 331
                spacing 21
                for kind, heading, limit in (("main", "主线", 1), ("side", "支线", 2)):
                    $ quests = [q for q in story_hud_quests if q['kind'] == kind]
                    if quests:
                        text heading style "rm_hud_white_text" size 40
                        for quest in quests[:limit]:
                            textbutton quest['title']:
                                style "rm_hud_text_button"
                                xsize 331
                                text_size 32
                                action Show("rm_hud_details", title=heading, rows=quests)
                textbutton "全部任务" style "rm_hud_text_button" action Show("rm_hud_details", title="任务", rows=story_hud_quests)
        use rm_status_hud


screen rm_hud_details(title, rows):
    modal True
    zorder 210
    key "game_menu" action Hide("rm_hud_details")
    use modal_dim_background
    frame:
        xalign .5
        yalign .5
        xysize (1013, 880)
        background RM_HUD_IVORY
        padding (43, 37)
        vbox:
            spacing 32
            hbox:
                xfill True
                text title size 48 color RM_HUD_INK
                textbutton "关闭" xalign 1.0 action Hide("rm_hud_details")
            viewport:
                ysize 693
                xfill True
                mousewheel True
                draggable True
                scrollbars "vertical"
                vbox:
                    spacing 32
                    for row in rows:
                        text row.get('title', row.get('label', '')) size 37 color RM_HUD_INK
                        text row.get('tooltip', row.get('description', '')) size 32 color RM_HUD_INK


style rm_hud_white_text is gui_text:
    size 35
    color "#f3eee3"
    outlines [(1, "#292923c0", 0, 1)]

style rm_hud_text_button is button:
    background None
    hover_background None
    padding (0, 5)
    yminimum 53

style rm_hud_text_button_text is rm_hud_white_text:
    hover_color "#d9c991"
    size 32
