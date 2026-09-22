from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RMTestFlowStaticTests(unittest.TestCase):
    def test_only_check_schedules_use_dice_check_flow(self):
        story = (ROOT / "game" / "story" / "9-9-9-test-flow.rpy").read_text(encoding="utf-8")
        schedules = (ROOT / "game" / "systems" / "rm_test_schedules.rpy").read_text(encoding="utf-8")

        self.assertIn("if rm_test_schedule_uses_check(selected_schedule):", story)
        self.assertIn("call rm_test_schedule_check_flow(selected_schedule)", story)
        self.assertIn("$ rm_test_outcome = rm_test_execute_rest_schedule(selected_schedule)", story)
        self.assertIn("label rm_test_schedule_check_flow(schedule_id):", story)
        self.assertIn('return schedule_id in ("test_strength_training", "test_dex_training", "test_jogging")', schedules)
        self.assertIn("$ rm_test_allowed_stats = rm_test_allowed_die_attributes(schedule_id)", story)
        self.assertIn("$ rm_test_required_die_stats = rm_test_required_die_attributes(schedule_id)", story)
        self.assertIn("allowed_stats=rm_test_allowed_stats, required_die_stats=rm_test_required_die_stats", story)
        self.assertIn('sensitive rm_test_schedule_available("test_rest")', schedules)
        self.assertIn('sensitive rm_test_schedule_available("test_sleep")', schedules)
        self.assertIn('return not rm_test_is_deep_night_turn()', schedules)
        self.assertIn('return "休息（测试）只能在深夜以外使用。"', schedules)
        self.assertIn("def rm_test_check_attribute(schedule_id):", schedules)
        self.assertIn("def rm_test_perform_schedule_check(schedule_id, dice_ids, requirement=None):", schedules)


if __name__ == "__main__":
    unittest.main()
