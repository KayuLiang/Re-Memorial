import sys
import unittest
from pathlib import Path


GAME_DIR = Path(__file__).resolve().parents[1] / "game"
sys.path.insert(0, str(GAME_DIR))

from opening_stats_logic import (
    ADJUSTABLE_STATS,
    STAT_MAX,
    STAT_MIN,
    TOTAL_ALLOCATABLE_POINTS,
    adjust_stat,
    attribute_check_unavailable,
    can_adjust_stat,
    get_attribute_dice,
    points_spent,
    remaining_points,
    stats_complete,
)


class OpeningStatsTests(unittest.TestCase):
    def setUp(self):
        self.base = {"str": 1, "dex": 1, "int": 1, "pow": 1}

    def test_constants_match_design(self):
        self.assertEqual(("str", "dex", "int", "pow"), ADJUSTABLE_STATS)
        self.assertEqual(1, STAT_MIN)
        self.assertEqual(20, STAT_MAX)
        self.assertEqual(17, TOTAL_ALLOCATABLE_POINTS)

    def test_initial_pool_is_seventeen(self):
        self.assertEqual(0, points_spent(self.base))
        self.assertEqual(17, remaining_points(self.base))

    def test_adjustment_spends_and_refunds_points_without_mutating_input(self):
        raised = adjust_stat(self.base, "str", 1)

        self.assertEqual(self.base, {"str": 1, "dex": 1, "int": 1, "pow": 1})
        self.assertIsNot(raised, self.base)
        self.assertEqual(2, raised["str"])
        self.assertEqual(1, points_spent(raised))
        self.assertEqual(16, remaining_points(raised))

        lowered = adjust_stat(raised, "str", -1)
        self.assertEqual(self.base, lowered)
        self.assertIsNot(lowered, raised)

    def test_missing_values_are_normalized_to_one(self):
        adjusted = adjust_stat({}, "dex", 1)

        self.assertEqual({"str": 1, "dex": 2, "int": 1, "pow": 1}, adjusted)

    def test_cannot_drop_below_one(self):
        self.assertFalse(can_adjust_stat(self.base, "str", -1))
        self.assertEqual(self.base, adjust_stat(self.base, "str", -1))

    def test_cannot_exceed_twenty(self):
        values = dict(self.base, str=20)

        self.assertFalse(can_adjust_stat(values, "str", 1))
        self.assertEqual(values, adjust_stat(values, "str", 1))

    def test_cannot_spend_more_than_pool(self):
        values = {"str": 18, "dex": 1, "int": 1, "pow": 1}

        self.assertFalse(can_adjust_stat(values, "dex", 1))
        self.assertEqual(values, adjust_stat(values, "dex", 1))

    def test_constitution_and_unknown_stats_are_rejected(self):
        for stat_name in ("con", "luck"):
            with self.subTest(stat_name=stat_name):
                self.assertFalse(can_adjust_stat(self.base, stat_name, 1))
                rejected = adjust_stat(self.base, stat_name, 1)
                self.assertEqual(self.base, rejected)
                self.assertIsNot(self.base, rejected)

    def test_only_single_point_adjustments_are_accepted(self):
        for delta in (-2, 0, 2):
            with self.subTest(delta=delta):
                self.assertFalse(can_adjust_stat(self.base, "str", delta))
                self.assertEqual(self.base, adjust_stat(self.base, "str", delta))

    def test_complete_requires_exactly_seventeen_spent(self):
        self.assertFalse(stats_complete(self.base))
        self.assertTrue(
            stats_complete({"str": 18, "dex": 1, "int": 1, "pow": 1})
        )
        self.assertFalse(
            stats_complete({"str": 19, "dex": 1, "int": 1, "pow": 1})
        )

    def test_complete_rejects_out_of_range_values_that_cancel_out(self):
        below_minimum = {"str": 19, "dex": 0, "int": 1, "pow": 1}
        above_maximum = {"str": 21, "dex": 0, "int": 0, "pow": 0}

        self.assertEqual(0, remaining_points(below_minimum))
        self.assertEqual(0, remaining_points(above_maximum))
        self.assertFalse(stats_complete(below_minimum))
        self.assertFalse(stats_complete(above_maximum))

    def test_complete_rejects_non_integer_values(self):
        values = {"str": 18.0, "dex": 1, "int": 1, "pow": 1}

        self.assertEqual(0, remaining_points(values))
        self.assertFalse(stats_complete(values))

    def test_attribute_dice_are_unconfigured(self):
        self.assertEqual((), get_attribute_dice("int"))

    def test_unavailable_check_is_structured_and_non_random(self):
        self.assertEqual(
            {
                "available": False,
                "stat": "int",
                "reason": "attribute_dice_not_configured",
                "rolls": (),
            },
            attribute_check_unavailable("int"),
        )


if __name__ == "__main__":
    unittest.main()
