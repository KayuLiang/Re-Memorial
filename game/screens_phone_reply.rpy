# Ordinary story choices. Each choice is (story value, authored message).
# Commit only after the choices fade out; the phone keeps its reading position.
init python:
    def phone_present_sent(contact_id, previous_count):
        if len(phone_history(contact_id)) <= previous_count:
            return
        scroll = renpy.get_screen_variable("phone_scroll", "phone_panel")
        follow = scroll.value if scroll.value >= scroll.range - 8 else None
        renpy.set_screen_variable("phone_new_index", len(phone_history(contact_id)) - 1, "phone_panel")
        renpy.set_screen_variable("phone_follow", follow, "phone_panel")
        renpy.restart_interaction()

label phone_story_reply(contact_id, choices, commit, confirm=True):
    $ phone_reply_selection = 0 if len(choices) == 1 else None
    $ phone_reply_sending = False
    show screen phone_panel(start_app="messages", start_chat=contact_id, story_mode=True, reply_session=True)
    call screen story_phone_reply_overlay(contact_id, choices, confirm)
    $ reply_choice = _return
    $ reply_previous_count = len(phone_history(contact_id))
    $ commit(reply_choice)
    $ phone_reply_sending = False
    $ phone_present_sent(contact_id, reply_previous_count)
    $ renpy.pause(.40, modal=False)
    hide screen phone_panel
    return reply_choice

transform phone_reply_appear:
    alpha 0.0
    yoffset 12
    easeout .18 alpha 1.0 yoffset 0

transform phone_reply_disappear:
    linear .16 alpha 0.0 yoffset 8

screen story_phone_reply_overlay(contact_id, choices, confirm=True):
    zorder 220
    style_prefix "choice"
    # The phone remains scrollable; navigation is locked by its reply_session.
    modal False
    on "show" action Function(renpy.retain_after_load)
    key "game_menu" action NullAction()
    use modal_dim_background
    # Keep the former confirm argument for saved calls. All replies now use
    # the normal story-choice interaction: choosing the text sends it.
    vbox:
        align (.5, .5)
        at (phone_reply_disappear if phone_reply_sending else phone_reply_appear)
        for i, option in enumerate(choices):
            textbutton option[1]:
                id ("story_phone_reply_option_" + str(i))
                substitute False
                sensitive not phone_reply_sending
                action [SetVariable("phone_reply_selection", i), SetVariable("phone_reply_sending", True)]
    if phone_reply_sending:
        timer .16 action Return(choices[phone_reply_selection])
