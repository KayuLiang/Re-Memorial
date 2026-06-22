# Re: Memorial demo script.

define system = Character("系统提示")
define wind = Character("风中的声音")
define god = Character("“山神”")
define doctor = Character("医生")
define nurse = Character("护士")
define ami = Character("阿弥")
define fro = Character("[player_name]")

default player_name = "弗洛"
default inventory = []
default ami_affection = 0

label start:

    jump story_0_1_0
