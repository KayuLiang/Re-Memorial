# One device geometry and one shared mode for every phone page (QHD coordinates).
define PHONE_WIDTH = 660
define PHONE_HEIGHT = 1320
define PHONE_X = (2560 - PHONE_WIDTH) // 2
define PHONE_PAGE_X = 44
define PHONE_PAGE_Y = 112
define PHONE_PAGE_WIDTH = PHONE_WIDTH - 2 * PHONE_PAGE_X
define PHONE_PAGE_HEIGHT = PHONE_HEIGHT - PHONE_PAGE_Y - 64
define PHONE_MODE_FULL = "full"
define PHONE_MODE_CONTENT = "content"
define PHONE_MODE_BOTTOM = "bottom"
define PHONE_MODE_SCALE = {"full": 1.0, "content": 1.16, "bottom": 1.16}
define PHONE_MODE_Y = {
    "full": (1440 - PHONE_HEIGHT) // 2,
    "content": int(1440 * .20),
    "bottom": int(1440 * .80 - PHONE_HEIGHT * PHONE_MODE_SCALE[PHONE_MODE_BOTTOM]),
}
define PHONE_PAGE_MODES = {
    "home": "full", "messages": "content", "phone": "content",
    "weather": "content", "calendar": "content", "clock": "content",
    "album": "content", "notes": "content", "recorder": "content",
    "calculator": "content", "chat": "content", "reply": "content",
    "photo": "content", "schedule_detail": "content",
    "note_edit": "content", "alarm_edit": "content", "dial": "content",
}

init python:
    def phone_page_mode(app, contact=None, story_mode=False):
        page = app
        if app == "messages" and contact:
            page = "chat"
        return PHONE_PAGE_MODES[page]

    def phone_page_top(mode):
        # Keep navigation visible when the enlarged device extends above the scene.
        return max(PHONE_PAGE_Y, int((36 - PHONE_MODE_Y[mode]) / PHONE_MODE_SCALE[mode]))

    def phone_visible_page_height(mode):
        top = phone_page_top(mode)
        return int(min(PHONE_HEIGHT - 64 - top,
                       (1440 - 36 - PHONE_MODE_Y[mode]) / PHONE_MODE_SCALE[mode] - top))

    def phone_shell_motion(mode, entry_y, entry_mode):
        return phone_shell_shift(mode, entry_y)

    def phone_page_motion(mode, entry_mode):
        return phone_page_safe_area(mode)

    def set_phone_mode(mode):
        renpy.set_screen_variable("phone_mode", mode, "phone_panel")

    def phone_panel_enter(app, contact, story_mode):
        renpy.retain_after_load()
        if story_mode:
            phone_begin_story_ami()
        set_phone_mode(phone_page_mode(app, contact, story_mode))

    def phone_navigate(app, contact=None, direction=1):
        if phone_navigation_locked():
            return
        story_mode = renpy.get_screen_variable("story_mode", "phone_panel")
        for name, value in (("phone_app", app), ("chat_contact", contact),
                            ("phone_direction", direction), ("phone_new_index", None),
                            ("phone_follow", None),
                            ("phone_scroll", ui.adjustment())):
            renpy.set_screen_variable(name, value, "phone_panel")
        set_phone_mode(phone_page_mode(app, contact, story_mode))

    def phone_back():
        contact = renpy.get_screen_variable("chat_contact", "phone_panel")
        phone_navigate("messages" if contact else "home", direction=-1)

    def phone_navigation_locked():
        return (renpy.get_screen("phone_panel") is not None
                and renpy.get_screen_variable("reply_session", "phone_panel"))

# Apply presets immediately; app changes never animate the device position or size.
transform phone_shell_shift(mode, entry_y):
    subpixel True
    xpos (PHONE_WIDTH // 2)
    xanchor .5
    yanchor 0.0
    zoom PHONE_MODE_SCALE[mode]
    yoffset (PHONE_MODE_Y[mode] - entry_y)

transform phone_page_safe_area(mode):
    subpixel True
    yoffset (phone_page_top(mode) - PHONE_PAGE_Y)
