# Art asset labels.

transform fro_left:
    xalign 0.08
    yalign 1.0
    yoffset 350
    zoom 0.62

transform fro_underwear_left:
    xalign 0.08
    yalign 1.0
    yoffset 350
    zoom 0.27

transform fro_casual_left:
    xalign 0.08
    yalign 1.0
    yoffset 180

transform ami_casual_right:
    xalign 0.92
    yalign 1.0
    yoffset 180

image fro underwear default = "images/sprites/fro/spr_fro_underwear_default.png"
image fro hospital_pajamas default = "images/sprites/fro/spr_fro_hospital_pajamas_default.png"
image fro casual default = Composite(
    (420, 760),
    (0, 0), Solid("#354760dd"),
    (74, 350), Text("\u5f17\u6d1b\u4fbf\u670d\u7acb\u7ed8\u5360\u4f4d", size=30, color="#ffffff")
)
image ami casual default = Composite(
    (420, 760),
    (0, 0), Solid("#6b3d42dd"),
    (88, 350), Text("\u963f\u5f25\u4fbf\u670d\u7acb\u7ed8\u5360\u4f4d", size=30, color="#ffffff")
)
