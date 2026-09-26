# Developer fixture: exercise the game adapter through real Ren'Py store state.
label rm_cooking_runtime_fixture:
    $ rm_reset_player()
    $ rm_cooking_stock = []
    $ rm_cooking_pending = None
    $ rm_cooking_mastery = {}
    $ rm_cooking_xp_deltas = []
    $ rm_cooking_add_ingredient("米饭")
    $ rm_cooking_add_ingredient("蛋")
    $ rm_cooking_start(["米饭", "蛋"])
    $ rm_cooking_test_die = rm_player.dice_for("dex")[0].id
    $ rm_cooking_test_result = rm_cooking_commit([rm_cooking_test_die], cooking_level=0)
    "烹饪适配层测试完成。"
    return

testsuite cooking_core:
    after testcase:
        run MainMenu(confirm=False)

testcase cooking_core.renpy_adapter:
    run Start("rm_cooking_runtime_fixture")
    pause until screen "say" timeout 5
    assert eval rm_cooking_test_result["status"] == "cooked"
    assert eval rm_cooking_test_result["name"] == "蛋炒饭"
    assert eval len(rm_cooking_stock) == 0
    assert eval rm_cooking_pending["applied"]
    assert eval len(rm_cooking_xp_deltas) == 1
