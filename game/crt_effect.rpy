# Reusable CRT filter. Call with:
# show screen crt_effect
# hide screen crt_effect

define crt_scroll_speed = 6.0
define crt_mode_settings = {
    "subtle": {
        "scanline": 0.22,
        "noise": 0.18,
        "flicker": 0.012,
        "jitter": 0,
    },
    "interference": {
        "scanline": 0.46,
        "noise": 0.42,
        "flicker": 0.045,
        "jitter": 8,
    },
    "shutdown": {
        "scanline": 0.75,
        "noise": 0.78,
        "flicker": 0.18,
        "jitter": 22,
    },
}

image crt_noise_cycle:
    "images/effects/crt_noise_01.png"
    pause 0.09
    "images/effects/crt_noise_02.png"
    pause 0.08
    "images/effects/crt_noise_03.png"
    pause 0.11
    repeat

transform crt_scanline_scroll(speed=6.0):
    subpixel True
    ypos -config.screen_height
    linear speed ypos 0
    repeat

transform crt_flicker(strength=0.025):
    alpha 0.0
    pause 0.70
    linear 0.04 alpha strength
    linear 0.08 alpha 0.0
    pause 1.15
    linear 0.03 alpha strength * 0.6
    linear 0.06 alpha 0.0
    repeat

transform crt_horizontal_jitter(amount=0):
    xoffset 0
    choice:
        pause 0.08
        linear 0.02 xoffset amount
        linear 0.03 xoffset -amount
        linear 0.02 xoffset 0
    choice:
        pause 0.18
    repeat

screen crt_effect(mode="subtle"):
    modal False
    zorder 1000

    $ settings = crt_mode_settings.get(mode, crt_mode_settings["subtle"])

    fixed:
        xsize config.screen_width
        ysize config.screen_height
        clipping True
        at crt_horizontal_jitter(settings["jitter"])

        add "images/effects/crt_scanlines.png":
            alpha settings["scanline"]
            at crt_scanline_scroll(crt_scroll_speed)

        add "crt_noise_cycle":
            xsize config.screen_width
            ysize config.screen_height
            alpha settings["noise"]

        add Solid("#ffffff"):
            at crt_flicker(settings["flicker"])
