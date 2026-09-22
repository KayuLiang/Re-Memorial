import random
import unittest
from copy import deepcopy
from game.systems import rm_core, rm_case


class CasePresentationTests(unittest.TestCase):
    def setUp(self):
        self.character = rm_core.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(7))

    def test_snapshot_does_not_migrate_live_character(self):
        del self.character.dice_growth_progress
        before = deepcopy(vars(self.character))
        rm_case.snapshot(self.character)
        self.assertFalse(hasattr(self.character, "dice_growth_progress"))
        self.assertEqual(before.keys(), vars(self.character).keys())
        self.assertEqual(before["test_growth_progress"], self.character.test_growth_progress)

    def test_current_values_and_radar_use_actual_cap(self):
        self.character.attribute_values["str"] = 25
        self.character.attribute_values["dex"] = -10
        data = rm_case.snapshot(self.character)
        self.assertEqual(data["attributes"]["str"]["current"], 28)
        self.assertEqual(data["attributes"]["str"]["effective"], 20)
        self.assertEqual(data["attributes"]["dex"]["current"], -7)
        self.assertEqual(rm_case.radar_fractions(data["attributes"])[:2], [1, 0])

    def test_zero_training_is_not_owned_or_unlocked(self):
        rows = rm_case.snapshot(self.character)["statuses"]
        self.assertFalse(any(row["id"].startswith("test_growth_") for row in rows))
        self.assertNotIn("test_growth_str", rm_case.remember({}, rows))

    def test_disappeared_status_keeps_real_explanation(self):
        self.character.attribute_values["str"] = 1
        rows = rm_case.snapshot(self.character)["statuses"]
        history = rm_case.remember({}, rows)
        self.character.attribute_values["str"] = 0
        current = rm_case.snapshot(self.character)["statuses"]
        unlocked = rm_case.dictionary_rows(current, history, "unlocked")
        previous = next(row for row in unlocked if row["id"] == "attr_value_str_1")
        self.assertFalse(previous["owned"])
        self.assertTrue(previous["unlocked"])
        self.assertIn("属性加值", previous["tooltip"])
        self.assertNotIn(previous["id"], [row["id"] for row in rm_case.dictionary_rows(current, history, "owned")])

    def test_archive_copy_and_unidentified_story_rows(self):
        original = {}
        rows = rm_case.snapshot(self.character, [{"label": "测试", "tooltip": "仅排版"}])["statuses"]
        history = rm_case.remember(original, rows)
        self.assertEqual(original, {})
        self.assertFalse(any(key.startswith("transient_") for key in history))
        self.assertTrue(any(row["label"] == "测试" for row in rm_case.dictionary_rows(rows, history, "owned")))

    def test_unknown_entries_do_not_leak_names_or_effects(self):
        rows = rm_case.dictionary_rows([], {}, "locked")
        self.assertTrue(rows)
        self.assertTrue(all(row["label"] == "？" and not row["unlocked"] for row in rows))
        self.assertTrue(all(not row["value_text"] for row in rows))

    def test_pagination_clamps_after_filtering(self):
        self.assertEqual(rm_case.page_rows([], 99), ([], 0, 1))
        self.assertEqual(rm_case.page_rows(list(range(17)), 3), ([16], 2, 3))

    def test_historical_mood_description_has_no_stale_value(self):
        self.character.mood = 99
        history = rm_case.remember({}, rm_case.snapshot(self.character)["statuses"])
        self.character.mood = 0
        current = rm_case.snapshot(self.character)["statuses"]
        high = next(row for row in rm_case.dictionary_rows(current, history, "unlocked") if row["id"] == "mood_high")
        self.assertFalse(high["owned"])
        self.assertNotIn("99", high["tooltip"])


if __name__ == "__main__":
    unittest.main()
