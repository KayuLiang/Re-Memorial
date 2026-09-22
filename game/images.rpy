# Art asset labels.

image bg doctor_office = im.Scale("images/bg/bg_doctor_office.jpg", 2560, 1440)
image bg nurse_station = im.Scale("images/bg/bg_nurse_station.jpg", 2560, 1440)
image bg bathroom = im.Scale("images/bg/bg_bathroom.jpg", 2560, 1440)
image bg hospital_corridor = im.Scale("images/bg/bg_hospital_corridor.png", 2560, 1440)
image bg hospital_entrance = im.Scale("images/bg/bg_hospital_entrance.png", 2560, 1440)
image bg train_station = im.Scale("images/bg/bg_train_station.jpg", 2560, 1440)
image bg train_platform = im.Scale("images/bg/bg_train_platform.jpg", 2560, 1440)
image bg train_carriage = im.Scale("images/bg/bg_train_carriage.png", 2560, 1440)
image bg mountain_station_placeholder = Composite(
    (2560, 1440),
    (0, 0), Solid("#2f3b46"),
    (1013, 667), Text("神山山脚车站 背景占位", size=75, color="#ffffff")
)
image bg mountain_inn_placeholder = Composite(
    (2560, 1440),
    (0, 0), Solid("#44372f"),
    (1040, 667), Text("山腰旅店 背景占位", size=75, color="#ffffff")
)
image bg snow_forest_placeholder = Composite(
    (2560, 1440),
    (0, 0), Solid("#d8e2ea"),
    (1040, 667), Text("雪山林道 背景占位", size=75, color="#1d2730")
)
image bg mountain_shrine_placeholder = Composite(
    (2560, 1440),
    (0, 0), Solid("#c8d2dd"),
    (1013, 667), Text("山神庙雪原 背景占位", size=75, color="#1d2730")
)

transform fro_left:
    xalign 0.08
    yalign 1.0
    yoffset 800
    zoom 0.56

transform fro_underwear_left:
    xalign 0.08
    yalign 1.0
    yoffset 800
    zoom 0.56

transform fro_casual_left:
    xalign 0.08
    yalign 1.0
    yoffset 800
    zoom 0.56

transform ami_casual_right:
    xalign 0.92
    yalign 1.0
    yoffset 800
    zoom 0.56

transform pal_casual_right:
    xalign 0.92
    yalign 1.0
    yoffset 653
    zoom (37.0 / 15.0)

image fro underwear default = "images/sprites/fro/spr_fro_underwear_default.png"
image fro hospital_pajamas default = "images/sprites/fro/spr_fro_hospital_pajamas_default.png"
image fro casual default = "images/sprites/fro/spr_fro_casual_default.png"
image ami underwear default = "images/sprites/ami/spr_ami_underwear_default.png"
image ami casual default = "images/sprites/ami/spr_ami_casual_default.png"
image pal casual default = Composite(
    (420, 760),
    (0, 0), Solid("#4b4f58dd"),
    (88, 350), Text("\u5e15\u5c14\u4fbf\u670d\u7acb\u7ed8\u5360\u4f4d", size=30, color="#ffffff")
)
