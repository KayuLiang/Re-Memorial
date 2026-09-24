import random
import unittest
from pathlib import Path

from game.systems import rm_core as rm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
SCREENS_PATH = GAME_DIR / "screens.rpy"
STORY_HUD_PATH = GAME_DIR / "screens_story_hud.rpy"
TEST_SCHEDULES_PATH = GAME_DIR / "systems" / "rm_test_schedules.rpy"
TEST_STORY_PATH = GAME_DIR / "story" / "9-9-9-test-flow.rpy"


class SequenceRandom(object):
    def __init__(self, values=None, uniform_values=None):
        self.values = list(values or [])
        self.uniform_values = list(uniform_values or [])

    def random(self):
        if self.values:
            return self.values.pop(0)
        return 0.0

    def uniform(self, low, high):
        if self.uniform_values:
            return self.uniform_values.pop(0)
        return low


class RMTestFlowCoreTests(unittest.TestCase):
    def test_strength_training_requirement_uses_curved_formal_strength_target(self):
        character = rm.create_initial_character({"str": 4, "dex": 2, "int": 2}, rng=random.Random(1))
        character.attribute_values["str"] = 3
        character.attribute_bonuses["str"].append({"value": 2, "source": "test"})

        self.assertEqual(rm.test_strength_training_requirement(character), 5)

    def test_training_requirement_uses_curved_formal_attribute_target(self):
        character = rm.create_initial_character({"str": 2, "dex": 4, "int": 2}, rng=random.Random(101))
        character.attribute_values["dex"] = 3
        character.attribute_bonuses["dex"].append({"value": 2, "source": "test"})

        self.assertEqual(rm.test_training_requirement(character, "str"), 4)
        self.assertEqual(rm.test_training_requirement(character, "dex"), 5)
        self.assertEqual([rm.training_requirement_from_attribute_value(x) for x in (1, 6, 11, 16, 20)], [3, 7, 14, 23, 32])

    def test_strength_training_progress_maps_result_ranks(self):
        expected = {
            rm.RESULT_BIG_FAILURE: 0,
            rm.RESULT_FAILURE: 1,
            rm.RESULT_SUCCESS: 2,
            rm.RESULT_HARD_SUCCESS: 3,
            rm.RESULT_BIG_SUCCESS: 6,
        }

        for rank, progress in expected.items():
            with self.subTest(rank=rank):
                self.assertEqual(rm.test_strength_training_progress_delta(rank), progress)

    def test_rest_converts_six_strength_training_progress_to_attribute_bonus_status(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(2))
        character.test_growth_progress["str"] = 6

        events = rm.resolve_test_rest(character)
        summary = rm.character_summary(character)

        self.assertIn("test_strength_bonus:str", events)
        self.assertEqual(character.test_growth_progress["str"], 0)
        self.assertEqual(character.current_attribute("str"), 4)
        self.assertTrue(any(status["id"] == "attr_bonus_str_test_strength_training" for status in summary["statuses"]))

    def test_rest_converts_six_dex_training_progress_to_attribute_bonus_status(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(102))
        character.test_growth_progress["dex"] = 6

        events = rm.resolve_test_rest(character)
        summary = rm.character_summary(character)

        self.assertIn("test_training_bonus:dex", events)
        self.assertEqual(character.test_growth_progress["dex"], 0)
        self.assertEqual(character.current_attribute("dex"), 4)
        self.assertTrue(any(status["id"] == "attr_bonus_dex_test_dex_training" for status in summary["statuses"]))

    def test_test_small_rest_reports_settlement_and_growth_reward_pending(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(7))
        character.test_growth_progress["str"] = 6
        character.attribute_bonus_gain_counters["str"] = 3

        events = rm.resolve_test_small_rest(character)
        status_ids = {status["id"] for status in rm.status_summary(character)}

        self.assertIn("small_rest", events)
        self.assertIn("test_strength_bonus:str", events)
        self.assertEqual(character.growth_reward_pending["str"], 1)
        self.assertIn("attr_bonus_str_test_strength_training", status_ids)
        self.assertIn("growth_reward_pending_str", status_ids)

    def test_day_rest_rolls_random_usable_con_die_to_restore_energy(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(8))
        character.energy = 1

        result = rm.resolve_test_day_rest(character, rng=random.Random(0))

        self.assertTrue(result["available"])
        self.assertEqual(result["attribute"], "con")
        self.assertIn(result["die_id"], {die.id for die in character.dice_for("con") if not die.is_sealed()})
        self.assertGreaterEqual(result["restored"], 1)
        self.assertEqual(character.energy, min(rm.energy_max(character), 1 + result["restored"]))

    def test_day_rest_does_not_reduce_shared_training_load(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(105))
        rm.add_training_fatigue(character, "test_strength_training", 2)
        rm.add_training_fatigue(character, "test_dex_training", 1)

        result = rm.resolve_test_day_rest(character, rng=random.Random(106))

        self.assertTrue(result["available"])
        self.assertEqual(character.training_load, 3)
        self.assertFalse(any(event.startswith("fatigue_reduced") for event in result["events"]))

    def test_test_sleep_uses_quality_check_and_restores_energy(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(9))
        character.energy = 0
        character.test_growth_progress["str"] = 6
        character.training_load = 3

        result = rm.resolve_test_sleep(character, rng=random.Random(0))

        self.assertTrue(result["available"])
        self.assertEqual(character.energy, rm.energy_max(character))
        self.assertIn("sleep", result["events"])
        self.assertEqual(character.training_load, 0)
        self.assertIn("training_load_cleared", result["events"])

    def test_sleep_converts_training_progress_once_and_enters_small_rest(self):
        for slot in ("sleep_decision", "night_break_1", "forced_sleep"):
            with self.subTest(slot=slot):
                character = rm.create_initial_character(rng=random.Random(9))
                character.test_growth_progress.update(str=6, dex=6)
                character.attribute_bonus_gain_counters.update(str=3, dex=3)
                rm.start_turn(character, slot)
                result = rm.begin_sleep(character, SequenceRandom([.5, .5, .5, .5]))
                for attr in ("str", "dex"):
                    event = "test_training_bonus:" + attr
                    self.assertEqual(result["events"].count(event), 1)
                    self.assertEqual(character.test_growth_progress[attr], 0)
                    self.assertEqual(len(character.attribute_bonuses[attr]), 1)
                    self.assertEqual(character.growth_reward_pending[attr], 1)
                again = rm.begin_sleep(character, SequenceRandom([.5, .5]))
                self.assertFalse(again["available"])
                self.assertEqual(character.growth_reward_pending["str"], 1)

    def test_direct_small_rest_converts_existing_bonus_before_special_progress(self):
        character = rm.create_initial_character(rng=random.Random(8))
        character.test_growth_progress["dex"] = 6
        character.attribute_value_gain_counters["dex"] = 1
        events = rm.process_small_rest(character, SequenceRandom([.9]))
        self.assertEqual(character.test_growth_progress["dex"], 0)
        self.assertEqual(character.attribute_values["dex"], 0)
        self.assertEqual(len(character.attribute_bonuses["dex"]), 1)
        self.assertIn("test_training_bonus:dex", events)

    def test_training_failure_degradation_is_settled_once_before_mood_changes(self):
        for schedule, attr in rm.TEST_TRAINING_SCHEDULE_ATTRIBUTES.items():
            with self.subTest(schedule=schedule):
                character = rm.create_initial_character(rng=random.Random(2))
                character.mood = 61
                character.degradation_progress[attr] = 4
                check = rm.CheckResult(available=True, attribute=attr, rank=rm.RESULT_BIG_FAILURE)
                check.spec = rm.CheckSpec(attr, 10, additional_check=True)
                apply = rm.apply_test_exercise_schedule_result if attr == "con" else rm.apply_test_training_schedule_result
                apply(character, schedule, check, random.Random(3))
                self.assertEqual(character.degradation_progress[attr], 4)
                rm.end_action_round(character, 0, random.Random(4), check=check)
                self.assertEqual(character.mood, 46)
                self.assertEqual(character.degradation_progress[attr], 0)
                self.assertEqual(character.degradation_penalty_pending[attr], 1)

    def test_round_without_available_big_failure_does_not_add_degradation(self):
        for check in (None, rm.CheckResult(available=False, attribute="str", rank=rm.RESULT_BIG_FAILURE),
                      rm.CheckResult(available=True, attribute="str", rank=rm.RESULT_FAILURE)):
            character = rm.create_initial_character(rng=random.Random(3))
            rm.end_action_round(character, check=check, rng=random.Random(4))
            self.assertEqual(character.degradation_progress["str"], 0)
            self.assertEqual(character.degradation_penalty_pending["str"], 0)

    def test_sunday_sleep_runs_small_rest_then_large_rest(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(10))
        character.day = 7
        character.weekday = 7
        character.attribute_values["str"] = 1

        result = rm.resolve_test_sleep(character, rng=random.Random(1))

        self.assertIn("small_rest", result["events"])
        self.assertIn("large_rest", result["events"])
        self.assertIn("value_to_formal:str", result["events"])
        self.assertEqual(character.formal_attributes["str"], 4)
        self.assertEqual(character.attribute_values["str"], 0)

    def test_status_summary_includes_attribute_values_bonuses_and_training_progress(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(3))
        character.attribute_values["str"] = 2
        character.attribute_bonuses["dex"].append({"value": 2, "source": "debug"})
        character.test_growth_progress["str"] = 5
        character.dice_growth_progress["int"] = 4
        character.growth_reward_pending["pow"] = 1

        statuses = rm.status_summary(character)
        status_ids = {status["id"] for status in statuses}

        self.assertNotIn("attr_value_str", status_ids)
        self.assertIn("attr_value_str_1", status_ids)
        self.assertIn("attr_value_str_2", status_ids)
        self.assertIn("attr_bonus_dex_debug", status_ids)
        self.assertIn("test_growth_str", status_ids)
        self.assertIn("dice_growth_int", status_ids)
        self.assertIn("growth_reward_pending_pow", status_ids)
        self.assertTrue(all(status["tooltip"] for status in statuses))

    def test_test_flow_can_apply_exact_mood_delta_without_pow_adjustment(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(4))
        character.formal_attributes["pow"] = 12
        character.mood = 0

        settlement = rm.end_action_round(character, mood_delta_base=10, rng=random.Random(5), exact_mood_delta=True)

        self.assertEqual(settlement["mood_delta"], 10)
        self.assertEqual(character.mood, 10)

    def test_console_helpers_mutate_mood_states_and_attributes(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(6))

        rm.test_console_adjust_mood(character, 10)
        self.assertEqual(character.mood, 10)

        rm.test_console_set_mood_state(character, "high")
        self.assertEqual(character.mood, 80)
        self.assertEqual(character.disease_state, rm.DISEASE_NONE)

        rm.test_console_set_mood_state(character, "low")
        self.assertEqual(character.mood, -80)
        self.assertEqual(character.disease_state, rm.DISEASE_NONE)

        rm.test_console_set_mood_state(character, "stable")
        self.assertEqual(character.mood, 0)
        self.assertEqual(character.disease_state, rm.DISEASE_NONE)

        rm.test_console_set_mood_state(character, "depression")
        self.assertEqual(character.disease_state, rm.DISEASE_DEPRESSION)
        self.assertEqual(character.dep, 80)

        rm.test_console_set_mood_state(character, "mania")
        self.assertEqual(character.disease_state, rm.DISEASE_MANIA)
        self.assertEqual(character.man, 80)

        rm.test_console_adjust_formal_attribute(character, "str", 1)
        rm.test_console_adjust_attribute_value(character, "str", 1)
        rm.test_console_adjust_attribute_bonus(character, "str", 1)

        self.assertEqual(character.formal_attributes["str"], 4)
        self.assertEqual(character.attribute_values["str"], 1)
        self.assertTrue(any(item["source"] == "console" and item["value"] == 1 for item in character.attribute_bonuses["str"]))
        self.assertEqual(character.current_attribute("str"), 6)

    def test_strength_training_check_can_use_one_to_three_selected_dice(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(11))
        character.energy = 20
        character.dice_pool.append(rm.RMDice("str_extra_1", "str", [1, 2, 3, 4, 5, 6]))
        character.dice_pool.append(rm.RMDice("str_extra_2", "str", [1, 2, 3, 4, 5, 6]))
        dice_ids = [die.id for die in character.dice_for("str")[:3]]
        spec = rm.CheckSpec("str", rm.test_strength_training_requirement(character), dice_ids=dice_ids, action_type=rm.ACTION_SCHEDULE)

        result = rm.perform_check(character, spec, rng=random.Random(12))

        self.assertTrue(result.available)
        self.assertEqual(result.dice_ids, dice_ids)
        self.assertEqual(len(result.dice_results), 3)

    def test_dex_training_check_can_use_one_to_three_selected_dice(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(103))
        character.energy = 20
        character.dice_pool.append(rm.RMDice("dex_extra_1", "dex", [1, 2, 3, 4, 5, 6]))
        character.dice_pool.append(rm.RMDice("dex_extra_2", "dex", [1, 2, 3, 4, 5, 6]))
        dice_ids = [die.id for die in character.dice_for("dex")[:3]]
        spec = rm.CheckSpec("dex", rm.test_training_requirement(character, "dex"), dice_ids=dice_ids, action_type=rm.ACTION_SCHEDULE)

        result = rm.perform_check(character, spec, rng=random.Random(104))

        self.assertTrue(result.available)
        self.assertEqual(result.dice_ids, dice_ids)
        self.assertEqual(len(result.dice_results), 3)

    def test_training_schedule_fatigue_increases_requirement_and_big_failure_range(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(107))
        rm.add_training_fatigue(character, "test_dex_training", 2)

        requirement = rm.test_training_requirement_for_schedule(character, "test_strength_training", rng=random.Random(1))
        spec = rm.CheckSpec(
            "str",
            requirement,
            dice_ids=["str_low_1", "str_low_2"],
            action_type=rm.ACTION_SCHEDULE,
            big_failure_slack=rm.training_fatigue_big_failure_slack(character, "test_strength_training"),
        )
        character.dice_pool = [
            rm.RMDice("str_low_1", "str", [1]),
            rm.RMDice("str_low_2", "str", [2]),
        ]
        character.energy = 20

        result = rm.perform_check(character, spec, rng=random.Random(108))

        self.assertEqual(requirement, 5 + 2 + 5)
        self.assertEqual(result.rank, rm.RESULT_BIG_FAILURE)

    def test_training_schedule_result_adds_matching_fatigue_layer(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(109))
        result = rm.CheckResult(available=True, attribute="dex", rank=rm.RESULT_SUCCESS, success=True)

        rm.apply_test_training_schedule_result(character, "test_dex_training", result, rng=random.Random(110))

        self.assertEqual(character.training_load, 1)

    def test_jogging_check_can_use_con_dex_str_but_requires_con_die(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(111))
        character.energy = 20
        character.dice_pool = [
            rm.RMDice("con_jog", "con", [2]),
            rm.RMDice("dex_jog", "dex", [3]),
            rm.RMDice("str_jog", "str", [4]),
        ]

        missing_con = rm.perform_check(
            character,
            rm.CheckSpec(
                "con",
                6,
                dice_ids=["dex_jog", "str_jog"],
                action_type=rm.ACTION_SCHEDULE,
                allowed_dice_attributes=("con", "dex", "str"),
                required_dice_attributes=("con",),
            ),
            rng=random.Random(112),
        )
        with_con = rm.perform_check(
            character,
            rm.CheckSpec(
                "con",
                6,
                dice_ids=["con_jog", "dex_jog", "str_jog"],
                action_type=rm.ACTION_SCHEDULE,
                allowed_dice_attributes=("con", "dex", "str"),
                required_dice_attributes=("con",),
            ),
            rng=random.Random(113),
        )

        self.assertFalse(missing_con.available)
        self.assertEqual(missing_con.reason, "missing_required_die:con")
        self.assertTrue(with_con.available)
        self.assertEqual(with_con.dice_ids, ["con_jog", "dex_jog", "str_jog"])

    def test_jogging_bonus_can_grant_multiple_attributes_from_one_opportunity(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(114))
        character.formal_attributes["con"] = 20
        result = rm.CheckResult(available=True, attribute="con", rank=rm.RESULT_SUCCESS, success=True)

        applied = rm.apply_test_exercise_schedule_result(
            character,
            "test_jogging",
            result,
            rng=SequenceRandom([0.0, 0.1, 0.1, 0.8]),
        )

        self.assertEqual(applied["bonus"]["success_count"], 1)
        self.assertEqual(applied["bonus"]["granted_attributes"], ["con", "dex"])
        self.assertTrue(any(item["source"] == "test_jogging" for item in character.attribute_bonuses["con"]))
        self.assertTrue(any(item["source"] == "test_jogging" for item in character.attribute_bonuses["dex"]))
        self.assertFalse(any(item["source"] == "test_jogging" for item in character.attribute_bonuses["str"]))

    def test_jogging_bonus_guarantees_at_least_one_attribute_when_opportunity_succeeds(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(115))
        character.formal_attributes["con"] = 20
        result = rm.CheckResult(available=True, attribute="con", rank=rm.RESULT_SUCCESS, success=True)

        applied = rm.apply_test_exercise_schedule_result(
            character,
            "test_jogging",
            result,
            rng=SequenceRandom([0.0, 0.9, 0.9, 0.9], uniform_values=[10.0]),
        )

        self.assertEqual(applied["bonus"]["success_count"], 1)
        self.assertEqual(applied["bonus"]["granted_attributes"], ["con"])
        self.assertEqual(sum(1 for attr in ("con", "dex", "str") for item in character.attribute_bonuses[attr] if item.get("source") == "test_jogging"), 1)

    def test_jogging_bonus_decay_uses_con_dex_str_bonus_layers_at_one_sixth_each(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(116))
        character.formal_attributes["con"] = 20
        for attr in ("con", "dex", "str"):
            character.attribute_bonuses[attr].append({"value": 1, "source": "existing"})
        result = rm.CheckResult(available=True, attribute="con", rank=rm.RESULT_SUCCESS, success=True)

        summary = rm.apply_exercise_jogging_bonus(character, result, rng=SequenceRandom([0.9]))

        self.assertEqual(summary["roll_plan"], [0.2894])

    def test_jogging_schedule_result_adds_shared_load(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(117))
        result = rm.CheckResult(available=True, attribute="con", rank=rm.RESULT_FAILURE, success=False)

        rm.apply_test_exercise_schedule_result(character, "test_jogging", result, rng=random.Random(118))

        self.assertEqual(character.training_load, 1)


class RMTestFlowRenpyTests(unittest.TestCase):
    def test_main_menu_has_start_test_button(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")

        self.assertIn('textbutton _("开始测试") action Start("rm_test_flow_start")', source)

    def test_main_menu_exposes_ui_test_entry(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")

        self.assertIn('textbutton _("UI测试") action Start("rm_ui_test_menu")', source)

    def test_ui_test_menu_routes_to_check_and_reward_flows(self):
        source = TEST_STORY_PATH.read_text(encoding="utf-8")

        self.assertIn("label rm_ui_test_menu:", source)
        self.assertIn('"接下来要测试什么呢？"', source)
        self.assertIn('"检定界面":', source)
        self.assertIn("jump rm_test_flow_loop", source)
        self.assertIn('"奖励选择":', source)
        self.assertIn("call rm_ui_test_reward_choice", source)
        self.assertIn('"返回标题菜单":', source)
        self.assertIn("return", source)

    def test_reward_ui_test_flow_prepares_pending_growth_reward(self):
        source = TEST_STORY_PATH.read_text(encoding="utf-8")
        helper_source = TEST_SCHEDULES_PATH.read_text(encoding="utf-8")

        self.assertIn("label rm_ui_test_reward_choice:", source)
        self.assertIn("$ rm_test_reward_request = rm_test_prepare_growth_reward_test()", source)
        self.assertIn("call rm_test_resolve_pending_cards", source)
        self.assertIn('def rm_test_prepare_growth_reward_test(attr="str"):', helper_source)
        self.assertIn("rm_core.add_growth_reward_pending(character, attr, 1)", helper_source)

    def test_modal_test_panels_allow_game_menu_key(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")

        self.assertIn("screen rm_allow_game_menu():", source)
        self.assertIn('key "game_menu" action ShowMenu()', source)

    def test_test_story_uses_core_meals_sleep_and_wake_flow(self):
        source = TEST_STORY_PATH.read_text(encoding="utf-8")

        self.assertIn("label rm_test_flow_start:", source)
        self.assertIn("$ rm_test_start_flow()", source)
        self.assertIn("现在是[rm_test_day_text()][rm_test_turn_text()]时间点。", source)
        self.assertIn("接下来要做什么", source)
        self.assertIn("call screen rm_test_schedule_select", source)
        self.assertIn("jump rm_test_flow_loop", source)
        self.assertIn("rm_test_node in rm_core.MEAL_SLOTS", source)
        self.assertIn("rm_test_node in rm_core.SLEEP_DECISIONS", source)
        self.assertIn('rm_test_node == "forced_sleep"', source)
        self.assertIn("call rm_test_wake_flow", source)

    def test_test_schedules_use_interactive_dice_check_flow(self):
        source = TEST_STORY_PATH.read_text(encoding="utf-8")

        self.assertIn('if rm_test_schedule_uses_check(selected_schedule):', source)
        self.assertIn("label rm_test_schedule_check_flow(schedule_id):", source)
        self.assertIn("$ rm_test_required_stat = rm_test_check_attribute(schedule_id)", source)
        self.assertIn("$ rm_test_allowed_stats = rm_test_allowed_die_attributes(schedule_id)", source)
        self.assertIn("$ rm_test_required_die_stats = rm_test_required_die_attributes(schedule_id)", source)
        self.assertIn("call screen attribute_dice_select(rm_test_required_stat, min_dice=1, max_dice=3, requirement=rm_test_requirement, check_kind=rm_test_check_kind, action_type=rm_core.ACTION_SCHEDULE, allowed_stats=rm_test_allowed_stats, required_die_stats=rm_test_required_die_stats)", source)
        self.assertNotIn("call screen attribute_dice_confirm(rm_test_required_stat, selected_die_ids)", source)
        self.assertIn("$ rm_test_check_result = rm_test_perform_schedule_check(schedule_id, selected_die_ids, rm_test_requirement, rm_bonus_die_ids)", source)
        self.assertIn("call screen attribute_check_roll_animation(rm_test_check_result)", source)
        self.assertIn("call screen attribute_check_result(rm_test_check_result)", source)
        self.assertIn("$ rm_test_outcome = rm_test_finalize_schedule_check(schedule_id, rm_test_check_result)", source)
        self.assertIn("call rm_test_resolve_pending_cards", source)

    def test_attribute_dice_select_uses_dynamic_attribute_label(self):
        source = (GAME_DIR / "screens_attribute_checks.rpy").read_text(encoding="utf-8")

        self.assertIn("rm_check_formula(preview,required_stat)", source)
        self.assertIn("rm_core.ATTRIBUTE_LABELS[attribute]", source)
        self.assertIn("rm_core.ATTRIBUTE_LABELS[a] for a in allowed", source)

    def test_attribute_dice_select_has_tabs_summary_and_inline_confirm(self):
        source = (GAME_DIR / "screens_attribute_checks.rpy").read_text(encoding="utf-8")

        self.assertNotIn("screen attribute_dice_confirm", source)
        self.assertIn("zorder 230", source)
        self.assertIn("use rm_allow_game_menu", source)
        self.assertIn("default selected_tab = \"usable\"", source)
        for tab in ("全部骰子", "可用骰子", "力量骰子", "灵巧骰子", "体质骰子", "智识骰子", "意志骰子"):
            with self.subTest(tab=tab):
                self.assertIn(tab, source)
        self.assertIn("attribute_check_header", source)
        self.assertIn("rm_dice_view.check_selection", source)
        self.assertNotIn("至少还需要投出", source)
        self.assertIn("attribute_dice_selection_error", source)
        self.assertIn("sensitive can_confirm and not confirm_open and not details_open", source)
        self.assertIn('style "attribute_check_confirm_dim"', source)
        self.assertIn('id "check_cancel"', source)
        self.assertIn("action Return(actual_ids)", source)

    def test_roll_animation_is_interactive_and_result_shows_rank(self):
        source = (GAME_DIR / "screens_attribute_checks.rpy").read_text(encoding="utf-8")

        self.assertEqual(source.count("use rm_allow_game_menu"), 4)
        self.assertIn("default roll_table = RMRealtimeDice", source)
        self.assertIn("Function(roll_table.launch)", source)
        self.assertIn("sensitive phase != 'rolling'", source)
        self.assertIn("attribute_check_rank_label", source)

    def test_test_schedule_screen_and_executor_define_three_test_schedules(self):
        source = TEST_SCHEDULES_PATH.read_text(encoding="utf-8")

        for label in ("休息（测试）", "睡觉（测试）", "负重训练（测试）", "协调训练（测试）"):
            with self.subTest(label=label):
                self.assertIn(label, source)
        self.assertIn('screen rm_test_schedule_select():', source)
        self.assertGreaterEqual(source.count("use rm_allow_game_menu"), 4)
        self.assertIn('Return("test_rest")', source)
        self.assertIn('Return("test_sleep")', source)
        self.assertIn('Return("test_strength_training")', source)
        self.assertIn('Return("test_dex_training")', source)
        self.assertIn('Return("test_jogging")', source)
        self.assertIn("rm_core.test_strength_training_requirement(character)", source)
        self.assertIn('return schedule_id in ("test_strength_training", "test_dex_training", "test_jogging")', source)
        self.assertIn('"test_dex_training": "dex"', source)
        self.assertIn('"test_jogging": "con"', source)
        self.assertIn('rm_test_allowed_die_attributes(schedule_id)', source)
        self.assertIn('rm_test_required_die_attributes(schedule_id)', source)
        self.assertIn('for attribute in bonus.get("granted_attributes", [])', source)
        self.assertIn('"test_training_bonus:{}".format(attribute)', source)
        self.assertIn("def rm_test_schedule_available(schedule_id):", source)
        self.assertIn("def rm_test_schedule_uses_check(schedule_id):", source)
        self.assertIn("def rm_test_execute_rest_schedule(schedule_id, character=None, bonus_die_ids=None):", source)
        self.assertIn("rm_core.resolve_test_day_rest(character", source)
        self.assertIn("def rm_test_check_attribute(schedule_id):", source)
        self.assertIn("def rm_test_perform_schedule_check(schedule_id, dice_ids, requirement=None, bonus_die_ids=None):", source)
        self.assertIn("big_failure_slack=rm_core.training_fatigue_big_failure_slack(character, schedule_id)", source)
        self.assertIn("def rm_test_finalize_schedule_check(schedule_id, result_dict, character=None):", source)
        self.assertIn("def rm_test_perform_strength_training_check(die_id):", source)
        self.assertIn("def rm_test_finalize_strength_training(result_dict, character=None):", source)
        self.assertIn("def rm_test_pending_card_request(character=None):", source)
        self.assertIn("def rm_test_card_needs_die_choice(card):", source)
        self.assertIn("def rm_test_card_description(card):", source)
        self.assertIn("def rm_test_apply_card_selection(card, die_id=None, face_index=None):", source)
        self.assertIn("def rm_test_pending_dice_choices(request, card=None, character=None):", source)
        self.assertIn("rm_test_pending_dice_choices(request, card)", source)
        self.assertIn("rm_core.growth_reward_dice_candidates(character, attr, card)", source)
        self.assertIn("screen rm_test_pending_card_choice", source)
        self.assertIn("default selected_card = None", source)
        self.assertIn("rm_test_card_description(card)", source)
        self.assertIn("screen rm_test_pending_die_choice(request, card=None):", source)
        self.assertIn("screen rm_test_pending_face_choice", source)
        self.assertIn("rm_core.apply_test_strength_training_result(character, result", source)
        self.assertIn("rm_core.resolve_test_sleep(character", source)
        self.assertIn("def rm_test_event_text(events):", source)
        self.assertIn("小休结算", source)
        self.assertIn("骰子成长奖励", source)
        self.assertIn("exact_mood_delta=True", source)
        story_source = (GAME_DIR / "story" / "9-9-9-test-flow.rpy").read_text(encoding="utf-8")
        self.assertIn("rm_test_pending_die_choice(rm_test_pending_request, rm_test_pending_card)", story_source)

    def test_unavailable_check_results_do_not_fallback_to_zero_rolls(self):
        schedules = TEST_SCHEDULES_PATH.read_text(encoding="utf-8")
        screens = (GAME_DIR / "screens_attribute_checks.rpy").read_text(encoding="utf-8")

        self.assertNotIn("else (0,)", schedules)
        self.assertNotIn("else 0", schedules)
        self.assertIn("if rows:", screens)
        self.assertIn("rm_check_reason(result.get('reason'))", screens)

    def test_statuses_render_in_character_panel_and_right_story_overlay(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")

        self.assertIn('config.overlay_screens.append("rm_test_status_overlay")', source)
        self.assertIn("summary['statuses']", source)
        self.assertIn("screen rm_test_status_overlay():", source)
        flat = (GAME_DIR / "ui/rm_hud_flat.rpy").read_text(encoding="utf-8")
        status = (GAME_DIR / "ui/rm_status_hud.rpy").read_text(encoding="utf-8")
        self.assertIn("use rm_status_hud", flat)
        self.assertIn("rm_hud_status.snapshot(rm_ensure_player(), story_hud_effects)", status)
        self.assertIn("hovered SetScreenVariable", source)
        self.assertIn("viewport:", source)
        self.assertIn("mousewheel True", source)
        self.assertIn("draggable True", source)
        self.assertIn("vpgrid:", source)
        self.assertIn("use rm_flat_sides", source)
        self.assertIn("RM_HUD_RIGHT - RM_STATUS_WIDE", status)
        self.assertIn('use rm_status_group(group, SetLocalVariable("expanded", True), expanded)', status)
        self.assertNotIn("for effect in effects[:6]:", flat)

    def test_test_console_button_and_screen_expose_required_controls(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")

        flat = (GAME_DIR / "ui/rm_hud_flat.rpy").read_text(encoding="utf-8")
        self.assertIn("if rm_test_flow_active:", flat)
        self.assertIn('textbutton "操作台"', flat)
        self.assertIn('action Show("rm_test_console")', flat)
        self.assertIn("screen rm_test_console():", source)
        for label in (
            "Mood -10",
            "Mood +10",
            "进入高涨情绪",
            "进入低落情绪",
            "正常状态",
            "抑郁状态",
            "躁狂状态",
            "特定属性",
            "特定属性加值",
            "特定属性加成",
        ):
            with self.subTest(label=label):
                self.assertIn(label, source)
        self.assertIn("rm_test_console_adjust_mood", source)
        self.assertIn("rm_test_console_set_mood_state", source)
        self.assertIn("rm_test_console_adjust_formal_attribute", source)
        self.assertIn("rm_test_console_adjust_attribute_value", source)
        self.assertIn("rm_test_console_adjust_attribute_bonus", source)


if __name__ == "__main__":
    unittest.main()
