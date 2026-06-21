# Reusable hue-separation filter.
# Start with:
# $ hue_separation_start("steady", scope="scene")
# $ hue_separation_start("glitch", scope="fullscreen")
# Stop with:
# $ hue_separation_stop()

define hue_separation_baseline_pixels = 3.0
define hue_separation_peak_pixels_min = 8.0
define hue_separation_peak_pixels_max = 18.0
define hue_separation_wait_min = 6.0
define hue_separation_wait_max = 12.0
define hue_separation_peak_duration_min = 0.1
define hue_separation_peak_duration_max = 0.5

default hue_separation_active = False
default hue_separation_mode = "steady"
default hue_separation_scope = "scene"
default hue_separation_pixels = 0.0
default hue_separation_peak_active = False
default hue_separation_next_delay = 0.0
default hue_separation_peak_duration = 0.0

init python:
    renpy.register_shader("rememorial.hue_separation",
        variables="""
            uniform sampler2D tex0;
            uniform vec2 u_model_size;
            uniform float u_hue_separation_pixels;
            varying vec2 v_tex_coord;
            attribute vec2 a_tex_coord;
        """,
        vertex_300="""
            v_tex_coord = a_tex_coord;
        """,
        fragment_300="""
            vec2 offset = vec2(
                u_hue_separation_pixels / u_model_size.x,
                0.0
            );
            vec4 red_sample = texture2D(tex0, v_tex_coord - offset);
            vec4 center_sample = texture2D(tex0, v_tex_coord);
            vec4 cyan_sample = texture2D(tex0, v_tex_coord + offset);

            gl_FragColor = vec4(
                red_sample.r,
                center_sample.g,
                cyan_sample.b,
                max(center_sample.a, max(red_sample.a, cyan_sample.a))
            );
        """,
    )

    def hue_separation_camera_update(trans, st, at):
        trans.u_hue_separation_pixels = hue_separation_pixels

    def _hue_separation_apply_camera(layer_name):
        renpy.show_layer_at(
            [hue_separation_camera],
            layer=layer_name,
            reset=True,
            camera=True,
        )

    def _hue_separation_clear_camera(layer_name):
        renpy.show_layer_at(
            [],
            layer=layer_name,
            reset=True,
            camera=True,
        )

    def _hue_separation_refresh_cameras():
        if not hue_separation_active:
            return

        _hue_separation_apply_camera("master")
        if hue_separation_scope == "fullscreen":
            _hue_separation_apply_camera("screens")

    def _hue_separation_schedule_next():
        global hue_separation_next_delay

        hue_separation_next_delay = renpy.random.uniform(
            hue_separation_wait_min,
            hue_separation_wait_max,
        )

    def _hue_separation_begin_peak():
        global hue_separation_peak_active
        global hue_separation_peak_duration
        global hue_separation_pixels

        if not hue_separation_active or hue_separation_mode != "glitch":
            return

        hue_separation_pixels = renpy.random.uniform(
            hue_separation_peak_pixels_min,
            hue_separation_peak_pixels_max,
        )
        hue_separation_peak_duration = renpy.random.uniform(
            hue_separation_peak_duration_min,
            hue_separation_peak_duration_max,
        )
        hue_separation_peak_active = True
        _hue_separation_refresh_cameras()
        renpy.restart_interaction()

    def _hue_separation_end_peak():
        global hue_separation_peak_active
        global hue_separation_pixels

        if not hue_separation_active or hue_separation_mode != "glitch":
            return

        hue_separation_pixels = hue_separation_baseline_pixels
        hue_separation_peak_active = False
        _hue_separation_schedule_next()
        _hue_separation_refresh_cameras()
        renpy.restart_interaction()

    def hue_separation_start(mode="steady", scope="scene"):
        global hue_separation_active
        global hue_separation_mode
        global hue_separation_scope
        global hue_separation_pixels
        global hue_separation_peak_active
        global hue_separation_peak_duration

        if mode not in ("steady", "glitch"):
            renpy.log(
                "Unknown hue-separation mode {!r}; using 'steady'.".format(mode)
            )
            mode = "steady"

        if scope not in ("scene", "fullscreen"):
            renpy.log(
                "Unknown hue-separation scope {!r}; using 'scene'.".format(scope)
            )
            scope = "scene"

        renpy.hide_screen("hue_separation_glitch_controller")
        _hue_separation_clear_camera("master")
        _hue_separation_clear_camera("screens")

        hue_separation_active = True
        hue_separation_mode = mode
        hue_separation_scope = scope
        hue_separation_pixels = hue_separation_baseline_pixels
        hue_separation_peak_active = False
        hue_separation_peak_duration = 0.0

        _hue_separation_apply_camera("master")
        if scope == "fullscreen":
            _hue_separation_apply_camera("screens")

        if mode == "glitch":
            _hue_separation_schedule_next()
            renpy.show_screen("hue_separation_glitch_controller")

        renpy.restart_interaction()

    def hue_separation_stop():
        global hue_separation_active
        global hue_separation_mode
        global hue_separation_scope
        global hue_separation_pixels
        global hue_separation_peak_active
        global hue_separation_next_delay
        global hue_separation_peak_duration

        renpy.hide_screen("hue_separation_glitch_controller")
        _hue_separation_clear_camera("master")
        _hue_separation_clear_camera("screens")

        hue_separation_active = False
        hue_separation_mode = "steady"
        hue_separation_scope = "scene"
        hue_separation_pixels = 0.0
        hue_separation_peak_active = False
        hue_separation_next_delay = 0.0
        hue_separation_peak_duration = 0.0
        renpy.restart_interaction()


transform hue_separation_camera:
    mesh True
    shader "rememorial.hue_separation"
    function hue_separation_camera_update


screen hue_separation_glitch_controller():
    modal False

    if hue_separation_active and hue_separation_mode == "glitch":
        if hue_separation_peak_active:
            timer hue_separation_peak_duration action Function(_hue_separation_end_peak)
        else:
            timer hue_separation_next_delay action Function(_hue_separation_begin_peak)
