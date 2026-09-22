# Re: Memorial demo script.

define system = Character("系统提示")
define mystery = Character("？？？")
define god = Character("“山神”")
define doctor = Character("医生")
define nurse = Character("护士")
define ami = Character("阿弥")
define fro = Character("[player_name]")
define anxious_passenger = Character("焦急的路人")
define thief = Character("小偷")
define lost_owner = Character("失主")
define transit_police = Character("乘警")
define gray_wolf = Character("灰狼")
define pal = Character("帕尔")

default player_name = "弗洛"
default inventory = []
default ami_affection = 0

label start:

    jump story_0_1_0
