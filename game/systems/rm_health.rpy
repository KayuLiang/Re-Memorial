# Event authors supply damage/treatment amounts; no hospital prices or schedules here.
init -10 python:
    def rm_damage_health(amount, character=None):
        return rm_core.damage_health(character or rm_ensure_player(), amount)

    def rm_heal_health(amount, character=None):
        return rm_core.heal_health(character or rm_ensure_player(), amount)

    def rm_health_game_over():
        return (not main_menu and not renpy.context()._menu and
                store.rm_player is not None and rm_core.is_dead(store.rm_player))

    config.overlay_screens.append("rm_health_death")

label rm_health_end:
    $ renpy.stop_skipping()
    while True:
        $ renpy.pause(hard=True)

# Always available regardless of HUD unlock or an open functional panel.
# Standard loading and rollback remain available; death is not save deletion.
screen rm_health_death():
    zorder 2000
    modal rm_health_game_over()
    if rm_health_game_over():
        key "dismiss" action NullAction()
        key "game_menu" action ShowMenu("load")
        add Solid("#292923")
        vbox:
            xalign .5
            yalign .5
            spacing 32
            text "角色死亡" id "health_death_title" size 64 color "#f3eee3" xalign .5
            text "生命值已归零。" size 32 color "#f3eee3" xalign .5
            textbutton "读取存档" id "health_load" xalign .5 text_color "#f3eee3" text_hover_color "#b4776e" action ShowMenu("load")
            textbutton "返回主菜单" id "health_main_menu" xalign .5 text_color "#f3eee3" text_hover_color "#b4776e" action MainMenu(confirm=False)
