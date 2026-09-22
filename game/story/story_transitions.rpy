label story_time_transition(time_text):

    $ story_hud_hidden = True
    $ rm_hud_sync_story_time(time_text)

    scene black
    hide fro
    hide ami
    hide pal

    pause 0.4
    centered "[time_text]"
    pause 0.4

    $ story_hud_hidden = False
    return


label story_masked_centered(message):

    window hide
    show screen story_centered_mask(message)
    pause
    hide screen story_centered_mask
    window auto

    return


screen story_centered_mask(message):
    zorder 80

    add Solid("#000000b8")
    text message:
        xalign 0.5
        yalign 0.5
        xmaximum 2000
        textalign 0.5
        color "#ffffff"
        size 51
