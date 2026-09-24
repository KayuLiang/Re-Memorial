import random
import unittest

from game.systems import rm_core as rm


class RMCoreTests(unittest.TestCase):
    def test_throw_faces_are_snapshotted_without_extra_gameplay_randomness(self):
        original = (3,3,3,5,5,6)
        for mode in ("normal", "bonus", "penalty"):
            die = rm.RMDice("mutable", "str", list(original))
            rng, expected = random.Random(7), random.Random(7)
            draws = [expected.choice(original) for _ in range(1 if mode == "normal" else 2)]
            result = rm.roll_die(die, rng, force_mode=mode)
            self.assertEqual(result["faces"], original)
            self.assertEqual(result["rolls"], draws)
            self.assertEqual(rng.getstate(), expected.getstate())
            die.faces[:] = [16]*8
            self.assertEqual(result["faces"], original)
            self.assertIn(result["value"], original)
            next_result = rm.roll_die(die, rng)
            self.assertEqual(next_result["faces"], (16,)*8)
            self.assertEqual(next_result["value"], 16)

    def test_create_initial_character_and_energy_cap(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(1))

        self.assertEqual(character.formal_attributes["con"], 6)
        self.assertEqual(character.formal_attributes["pow"], 6)
        self.assertEqual(character.formal_attributes["str"], 3)
        self.assertEqual(character.current_attribute("dex"), 3)
        self.assertEqual(character.effective_attribute("int"), 2)
        self.assertEqual(rm.energy_max(character), 6)
        self.assertEqual(character.energy, 6)
        self.assertEqual(len(character.dice_for("con")), 2)
        self.assertEqual(len(character.dice_for("pow")), 2)

    def test_dice_enchantments_and_costs(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(2))
        dex_die = character.dice_for("dex")[0]
        dex_die.enchantment = rm.ENCHANT_LIGHT

        spec = rm.CheckSpec(attribute="dex", requirement=5, dice_ids=[dex_die.id], action_type=rm.ACTION_SCHEDULE)
        result = rm.perform_check(character, spec, rng=random.Random(3))

        self.assertTrue(result.available)
        self.assertEqual(result.energy_cost, 0)
        self.assertEqual(result.dice_results[0]["enchantment"], rm.ENCHANT_LIGHT)

    def test_bonus_penalty_seal_shackle_heavy_sluggish(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(4))
        str_die = character.dice_for("str")[0]
        str_die.faces = [1, 6]
        str_die.enchantment = rm.ENCHANT_SWIFT
        spec = rm.CheckSpec(attribute="str", requirement=4, dice_ids=[str_die.id],
                            action_type=rm.ACTION_INSTANT, bonus_die_ids=[str_die.id])
        swift = rm.perform_check(character, spec, rng=random.Random(1))
        self.assertEqual(swift.dice_results[0]["mode"], "bonus")

        str_die.enchantment = rm.ENCHANT_SLUGGISH
        sluggish = rm.perform_check(character, spec, rng=random.Random(1))
        self.assertEqual(sluggish.dice_results[0]["mode"], "penalty")

        str_die.enchantment = rm.ENCHANT_HEAVY
        heavy = rm.perform_check(character, spec, rng=random.Random(1))
        self.assertEqual(heavy.energy_cost, 1)

        str_die.enchantment = rm.ENCHANT_SEAL
        sealed = rm.perform_check(character, spec, rng=random.Random(1))
        self.assertFalse(sealed.available)
        self.assertEqual(sealed.reason, "no_usable_dice")

        str_die.enchantment = rm.ENCHANT_SHACKLE
        shackled = rm.perform_check(
            character,
            rm.CheckSpec(attribute="str", requirement=4, dice_ids=[], action_type=rm.ACTION_INSTANT),
            rng=random.Random(1),
        )
        self.assertTrue(shackled.available)
        self.assertEqual(shackled.dice_ids, [str_die.id])

    def test_mood_modifies_check_structure_and_result(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(5))
        character.mood = -80
        dex_die = character.dice_for("dex")[0]
        dex_die.faces = [4]

        result = rm.perform_check(
            character,
            rm.CheckSpec(attribute="dex", requirement=5, dice_ids=[dex_die.id]),
            rng=random.Random(1),
        )

        self.assertEqual(result.mood_state, rm.MOOD_LOW)
        self.assertEqual(result.attribute_modifier, 2)
        self.assertEqual(result.dice_multiplier, 0.75)
        self.assertEqual(result.total, 5.0)
        self.assertEqual(result.rank, rm.RESULT_SUCCESS)

    def test_result_grades_include_big_success_and_big_failure(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(6))
        die_a = character.dice_for("con")[0]
        die_b = character.dice_for("con")[1]
        die_a.faces = [4]
        die_b.faces = [2]
        success = rm.perform_check(
            character,
            rm.CheckSpec(attribute="con", requirement=4, dice_ids=[die_a.id, die_b.id]),
            rng=random.Random(1),
        )
        self.assertEqual(success.rank, rm.RESULT_BIG_SUCCESS)

        die_a.faces = [1]
        die_b.faces = [1]
        failure = rm.perform_check(
            character,
            rm.CheckSpec(attribute="con", requirement=12, dice_ids=[die_a.id, die_b.id]),
            rng=random.Random(1),
        )
        self.assertEqual(failure.rank, rm.RESULT_BIG_FAILURE)

    def test_turn_end_can_enter_disease_state(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(7))
        character.mood = 200

        settlement = rm.end_action_round(character, mood_delta_base=0, rng=random.Random(1))

        self.assertEqual(settlement["mood"], 200)
        self.assertEqual(character.disease_state, rm.DISEASE_MANIA)
        self.assertIn("enter_mania", settlement["events"])

    def test_reallocate_initial_attributes_rebuilds_new_character_state(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(8))

        reallocated = rm.reallocate_initial_attributes(character, "str", -1, rng=random.Random(8))
        reallocated = rm.reallocate_initial_attributes(reallocated, "int", 1, rng=random.Random(8))

        self.assertEqual(reallocated.formal_attributes["con"], 6)
        self.assertEqual(reallocated.formal_attributes["pow"], 6)
        self.assertEqual(reallocated.formal_attributes["str"], 2)
        self.assertEqual(reallocated.formal_attributes["dex"], 3)
        self.assertEqual(reallocated.formal_attributes["int"], 3)
        self.assertEqual(rm.initial_attribute_points_remaining(reallocated), 0)
        self.assertEqual(reallocated.energy, 6)

    def test_opening_draft_character_starts_incomplete(self):
        character = rm.create_opening_draft_character(rng=random.Random(9))

        self.assertEqual(character.formal_attributes["con"], 6)
        self.assertEqual(character.formal_attributes["pow"], 6)
        self.assertEqual(character.formal_attributes["str"], 1)
        self.assertEqual(character.formal_attributes["dex"], 1)
        self.assertEqual(character.formal_attributes["int"], 1)
        self.assertEqual(rm.initial_attribute_points_remaining(character), 5)
        self.assertTrue(rm.can_reallocate_initial_attribute(character, "str", 1))
        self.assertFalse(rm.can_reallocate_initial_attribute(character, "str", -1))
        self.assertEqual(len(character.dice_pool), 7)

    def test_character_summary_reports_current_status_attributes_and_dice(self):
        character = rm.create_initial_character({"str": 3, "dex": 2, "int": 3}, rng=random.Random(10))
        character.mood = -70
        character.energy = 4
        character.dice_for("dex")[0].enchantment = rm.ENCHANT_SWIFT

        summary = rm.character_summary(character)
        dice = rm.dice_pool_summary(character)

        self.assertEqual(summary["mood"]["value"], -70)
        self.assertEqual(summary["mood"]["state"], rm.MOOD_LOW)
        self.assertEqual(summary["mood"]["label"], "低落")
        self.assertEqual(summary["disease"]["state"], rm.DISEASE_NONE)
        self.assertEqual(summary["energy"], {"current": 4, "maximum": rm.energy_max(character)})
        self.assertEqual(summary["attributes"]["dex"]["formal"], 2)
        self.assertEqual(summary["attributes"]["dex"]["current"], 2)
        self.assertEqual(summary["attributes"]["dex"]["effective"], 2)
        self.assertGreaterEqual(len(dice), 7)
        self.assertEqual(dice[0]["label"], rm.ATTRIBUTE_LABELS[dice[0]["attribute"]])
        self.assertIn("faces_text", dice[0])
        self.assertTrue(any(item["enchantment_label"] == "奖励骰" for item in dice))

    def test_status_tooltips_include_numeric_values(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(11))
        character.mood = 80
        character.energy = 2

        self.assertIn("80", rm.mood_tooltip(character))
        self.assertIn("高涨", rm.mood_tooltip(character))
        self.assertIn("2 / {}".format(rm.energy_max(character)), rm.energy_tooltip(character))


if __name__ == "__main__":
    unittest.main()
