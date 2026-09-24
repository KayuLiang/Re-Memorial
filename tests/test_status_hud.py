import unittest
from game.systems import rm_core, rm_hud_status as hud


class StatusHudTests(unittest.TestCase):
    def test_grouping_counts_environment_and_stable_order(self):
        rows = [dict(id="ember", label="余烬", value_text="×180"),
                dict(id="ect_residual", label="电残留", value_text="27日"),
                dict(id="hunger", label="饥饿", value_text="×-1", category="physiological"),
                dict(id="pending_lithium", label="lithium", category="medication"),
                dict(id="intoxication", label="微醺", category="medication"),
                dict(id="injury_fracture", label="骨折", category="injury"),
                dict(id="routine", label="健康作息"),
                dict(id="weather", label="多云", category="weather"),
                dict(id="mood_stable", label="平稳"),
                dict(id="hidden", label="隐藏状态", visible_in_hud=False)]
        groups = hud.normalize(rows)
        self.assertEqual([g["id"] for g in groups], [g[0] for g in hud.GROUPS])
        items = {i["id"]: i for g in groups for i in g["items"]}
        self.assertEqual(items["ember"]["display_count"], "180")
        self.assertEqual(items["ect_residual"]["display_count"], "27")
        self.assertEqual(items["hunger"]["display_name"], "饱腹")
        self.assertEqual(items["hunger"]["display_count"], "1")
        self.assertEqual(items["pending_lithium"]["display_name"], "碳酸锂")
        self.assertEqual(items["intoxication"]["group"], "current")
        self.assertNotIn("weather", items)
        self.assertNotIn("hidden", items)
        self.assertNotIn("mood_stable", items)
        self.assertEqual(groups, hud.normalize(list(reversed(rows))))

    def test_count_sources_and_empty_groups(self):
        for value, expected in [("×2", "2"), ("3/6", "3"), ("+5", "5"), ("再伤2", "2"), ("", "1")]:
            self.assertEqual(hud.display_count(dict(value_text=value)), expected)
        self.assertEqual(hud.display_count(dict(value_text="27日", display_count=3)), "3")
        self.assertEqual(hud.normalize([]), [])
        self.assertEqual([g["id"] for g in hud.normalize([dict(label="剧情长期状态")])], ["life"])

    def test_story_override_merges_duplicate_id_without_duplicate_controls(self):
        groups = hud.normalize([dict(id="emotion_anxiety", label="焦虑", value_text="×2", category="emotion"),
                                dict(id="emotion_anxiety", display_count=3, tooltip="剧情补充")])
        self.assertEqual(len(groups[0]["items"]), 1)
        self.assertEqual(groups[0]["items"][0]["display_count"], "3")
        self.assertEqual(groups[0]["items"][0]["display_name"], "焦虑")
        self.assertIn("剧情补充", groups[0]["items"][0]["tooltip"])

    def test_snapshot_does_not_upgrade_live_state_or_invent_medicine_duration(self):
        player = rm_core.create_initial_character()
        player.ember = 180
        player.medicine_taken_today["venlafaxine"] = 1
        player.pending_bipolar_medications["aripiprazole"] = True
        player.trazodone_sleep_bonus_day = player.day
        player.time_habits["morning:study"] = True
        del player.current_weather
        groups = hud.snapshot(player)
        self.assertFalse(hasattr(player, "current_weather"))
        items = {i["id"]: i for g in groups for i in g["items"]}
        self.assertEqual(items["pending_aripiprazole"]["display_name"], "阿立哌唑")
        self.assertIn("trazodone_sleep", items)
        self.assertIn("time_habit_morning:study", items)
        self.assertNotIn("venlafaxine", items)
        player.day += 1
        self.assertNotIn("trazodone_sleep", [i["id"] for g in hud.snapshot(player) for i in g["items"]])

    def test_environment_is_separate_and_unknown_location_is_not_invented(self):
        player = rm_core.create_initial_character()
        self.assertEqual(hud.environment(player), [])
        player.current_weather = rm_core.WEATHER_CLOUDY
        player.current_temperature = 50
        self.assertEqual(hud.environment(player, ("doctor_office",)), ["多云 · 适温", "医院"])
        self.assertEqual(hud.environment(player, ("train_carriage",)), ["多云 · 适温", "列车"])
        self.assertEqual(hud.environment(player, ("unknown",)), ["多云 · 适温"])

    def test_flow_uses_measured_width_not_character_count(self):
        groups = hud.normalize([dict(id=str(i), label=n, group="current", priority=i)
                                for i, n in enumerate(("WWW", "iii", "短", "长名字"))])
        measure = lambda text: sum(30 if ch == "W" else 5 if ch == "i" else 20 for ch in text)
        layout = hud.flow(groups, 200, measure, lambda _: 10)
        items = layout["groups"][0]["items"]
        self.assertEqual(items[0]["y"], items[1]["y"])
        self.assertNotEqual(items[1]["y"], items[2]["y"])

    def test_dense_flow_limits_rows_bounds_and_counts_without_reordering(self):
        groups = hud.normalize([dict(id=f"{g}-{i:02}", label="状态" + str(i), group=g, priority=i)
                                for g, _ in hud.GROUPS for i in range(30)])
        for width in (312, 416):
            layout = hud.flow(groups, width, lambda t: len(t) * 26, lambda t: len(t) * 10)
            count = 0
            for source, group in zip(groups, layout["groups"]):
                self.assertTrue(1 <= group["rows"] <= 3)
                ids = [i["id"] for i in group["items"]]
                self.assertEqual(ids, [i["id"] for i in source["items"]][:len(ids)])
                count += len(ids)
                for item in group["items"]:
                    self.assertLessEqual(item["x"] + item["width"], width)
                    self.assertLessEqual(item["y"] + 36, group["height"])
                more = group["overflow"]
                self.assertIsNotNone(more)
                self.assertLessEqual(more["x"] + more["width"], width)
                self.assertEqual(more["y"], 28 + (group["rows"] - 1) * 42)
                for item in group["items"]:
                    if item["y"] == more["y"]:
                        self.assertLessEqual(item["x"] + item["width"] + 8, more["x"])
            self.assertEqual(layout["hidden"], 120 - count)
            self.assertLessEqual(layout["footer_y"] + 40, 600)
        narrow = hud.flow(groups, 312, lambda t: len(t) * 26, lambda t: 10)
        wide = hud.flow(groups, 416, lambda t: len(t) * 26, lambda t: 10)
        self.assertLess(wide["hidden"], narrow["hidden"])

    def test_overflow_marker_not_shown_when_everything_fits(self):
        groups = hud.normalize([dict(label="焦虑")])
        layout = hud.flow(groups, 312, lambda t: len(t) * 26, lambda t: 10)
        self.assertIsNone(layout["groups"][0]["overflow"])
        self.assertEqual(layout["hidden"], 0)

    def test_oversize_label_keeps_full_name_for_tooltip(self):
        groups = hud.normalize([dict(label="很长的剧情长期状态" * 8)])
        layout = hud.flow(groups, 312, lambda t: len(t) * 26, lambda t: 10)
        item = layout["groups"][0]["items"][0]
        self.assertTrue(item["text"].endswith("…"))
        self.assertIn(item["display_name"], item["tooltip"])
        self.assertLessEqual(item["width"], 312)


if __name__ == "__main__":
    unittest.main()
