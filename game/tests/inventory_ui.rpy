# Explicit test fixture only; does not grant items to a player's story/save.
label rm_inventory_visual_preview:
    $ _autosave = False
    $ opening_active = False
    $ story_hud_hidden = False
    $ inventory = ["帕尔的巧克力","药盒","手机","钱包","奇怪的项链","西铁月票","地图"]
    $ rm_inventory_seen = ["药盒","手机","钱包","奇怪的项链","地图"]
    scene bg doctor_office
    "背包测试准备。"
    show screen inventory_panel
    while True:
        "背包界面测试。"

label rm_inventory_save_checkpoint:
    # Save stock at an ordinary story checkpoint, not uncommitted test-runner
    # assignments during the same modal interaction.
    "保存测试准备。"
    show screen inventory_panel
    while True:
        "保存测试就绪。"

testsuite inventory_ui:
    parameter inventory_saved_preferences = [None]
    parameter inventory_saved_window = [None]
    parameter inventory_saved_timeout = [None]
    parameter (inv_width,inv_height) = [(1920,1080),(1280,720),(2560,1440)]
    before testcase:
        python:
            inventory_saved_timeout = _test.timeout
            _test.timeout = 20
            inventory_saved_preferences = (_preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size)
            _preferences.afm_enable = False
            inventory_saved_window = renpy.display.draw.info['max_window_size']
            renpy.display.draw.info['max_window_size'] = (max(inv_width,inventory_saved_window[0]),max(inv_height,inventory_saved_window[1]))
            renpy.set_physical_size((inv_width,inv_height))
    after testcase:
        python:
            _test.timeout = inventory_saved_timeout
            _preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size = inventory_saved_preferences
            renpy.display.draw.info['max_window_size'] = inventory_saved_window
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase inventory_ui.browse:
    run Start("rm_inventory_visual_preview")
    advance until screen "inventory_panel"
    pause .5
    assert screen "inventory_panel"
    assert eval renpy.get_physical_size() == (inv_width,inv_height)
    assert eval not rm_hud_visible()
    assert eval renpy.get_screen_variable('selected_item','inventory_panel') == '帕尔的巧克力'
    assert eval '帕尔的巧克力' in rm_inventory_seen
    assert id "inventory_use"
    python:
        inv_before = list(inventory)
    assert not eval renpy.get_displayable('inventory_panel','inventory_use').is_sensitive()
    screenshot ("../../tmp/inventory_ui/%dx%d/overview.png" % (inv_width,inv_height))
    click id "inventory_item_5"
    assert eval '西铁月票' in rm_inventory_seen
    assert not id "inventory_use"
    click id "inventory_category_food"
    assert eval renpy.get_screen_variable('selected_item','inventory_panel') == '帕尔的巧克力'
    click id "inventory_item_0"
    click id "inventory_item_0"
    assert eval inventory == inv_before
    click id "inventory_preview"
    assert id "inventory_image_viewport"
    assert not id "inventory_grid"
    assert not id "inventory_use"
    click id "inventory_zoom_in"
    assert eval renpy.get_screen_variable('image_zoom','inventory_panel') == 1.25
    click id "inventory_zoom_reset"
    assert eval renpy.get_screen_variable('image_zoom','inventory_panel') == 1.0
    screenshot ("../../tmp/inventory_ui/%dx%d/inspect.png" % (inv_width,inv_height))
    keysym "K_ESCAPE"
    assert id "inventory_grid"
    assert eval renpy.get_screen_variable('current_category','inventory_panel') == 'food'
    click id "inventory_category_medicine"
    assert id "inventory_empty"
    assert not id "inventory_name"
    assert not id "inventory_preview"
    screenshot ("../../tmp/inventory_ui/%dx%d/empty.png" % (inv_width,inv_height))
    click id "inventory_category_important"
    assert eval renpy.get_screen_variable('selected_item','inventory_panel') == '药盒'
    assert not id "inventory_use"
    screenshot ("../../tmp/inventory_ui/%dx%d/container.png" % (inv_width,inv_height))
    click id "inventory_close"
    assert not screen "inventory_panel"
    run Show("medicine_panel")
    assert eval rm_inventory.rows(inventory,'medicine') == []
    keysym "K_ESCAPE"
    assert not screen "medicine_panel"
    assert eval inventory == inv_before

testcase inventory_ui.edges:
    run Start("rm_inventory_visual_preview")
    advance until screen "inventory_panel"
    run SetVariable("inventory",["项链","奇怪的项链","地图","地图","未登记物品"])
    click id "inventory_category_all"
    assert eval len(rm_inventory.rows(inventory)) == 3
    assert eval rm_inventory.rows(inventory)[0]['count'] == 2
    click id "inventory_item_2"
    assert not eval renpy.get_displayable('inventory_panel','inventory_preview').is_sensitive()
    assert not id "inventory_use"
    screenshot ("../../tmp/inventory_ui/%dx%d/unknown.png" % (inv_width,inv_height))
    run SetVariable("inventory",["排版测试物品%02d" % i for i in range(37)])
    click id "inventory_category_all"
    assert id "inventory_scrollbar"
    run Function(renpy.get_screen_variable('grid_scroll','inventory_panel').change,450)
    pause .2
    click id "inventory_item_36"
    assert eval renpy.get_screen_variable('selected_item','inventory_panel') == '排版测试物品36'
    screenshot ("../../tmp/inventory_ui/%dx%d/overflow.png" % (inv_width,inv_height))
    run Hide("inventory_panel")
    run Jump("rm_inventory_save_checkpoint")
    advance until screen "inventory_panel"
    run Function(renpy.save,"inventory-ui-test",include_screenshot=False)
    run SetVariable("inventory",[])
    assert id "inventory_empty"
    run Function(renpy.load,"inventory-ui-test")
    pause .3
    assert eval len(inventory) == 37
    assert eval '排版测试物品36' in rm_inventory_seen
    # Full load starts a new browse session; subview return (above) is preserved.
    assert eval renpy.get_screen_variable('selected_item','inventory_panel') == '排版测试物品00'
    keysym "K_ESCAPE"
    assert not screen "inventory_panel"
