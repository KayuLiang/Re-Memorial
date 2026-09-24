import random
import unittest

from game.systems import rm_core as rm


class RMSecondStageTests(unittest.TestCase):
    def test_mood_disease_entry_stable_switch_and_sleep_recovery(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(1))
        character.mood = 100

        self.assertEqual(rm.get_mood_state(character), rm.MOOD_HIGH)
        self.assertAlmostEqual(rm.calculate_k_pow(character), 1.0)
        self.assertGreater(rm.calculate_enter_disease_probability(character), 0)

        rm.apply_disease_entry(character)
        self.assertEqual(character.disease_state, rm.DISEASE_MANIA)
        self.assertEqual(character.man, 100)
        character.mood = 50
        self.assertEqual(rm.get_mood_state(character), rm.DISEASE_MANIA)

        rm.apply_stable_return(character)
        self.assertEqual(character.disease_state, rm.DISEASE_NONE)
        self.assertEqual(character.man, 0)
        self.assertEqual(character.dep, 0)

        character.mood = 100
        rm.apply_sleep_recovery(character)
        self.assertEqual(character.mood, 95)

    def test_attribute_rest_growth_counters_and_large_rest_degradation(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(2))

        for _ in range(4):
            rm.add_attribute_bonus(character, "str", 1)
        self.assertEqual(character.dice_growth_progress["str"], 0)
        self.assertEqual(character.growth_reward_pending["str"], 1)

        character.attribute_bonuses["str"] = [{"value": 1, "source": "a"}]
        rm.process_small_rest(character, rng=random.Random(0))
        self.assertEqual(character.attribute_values["str"], 1)
        self.assertEqual(character.attribute_bonuses["str"], [])

        character.attribute_values["str"] = 1
        rm.process_large_rest(character, rng=random.Random(1))
        self.assertEqual(character.formal_attributes["str"], 4)
        self.assertEqual(character.attribute_values["str"], 0)

    def test_large_rest_does_not_repeat_small_rest(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(12))
        character.attribute_bonuses["str"] = [{"value": 1, "source": "test"}]

        events = rm.process_large_rest(character, rng=random.Random(0))

        self.assertNotIn("bonus_to_value:str", events)
        self.assertNotIn("bonus_lost:str", events)
        self.assertEqual(character.attribute_bonuses["str"], [{"value": 1, "source": "test"}])

    def test_growth_and_degradation_card_backends(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(3))

        rm.add_dice_growth_progress(character, "int", 6)
        events = rm.process_dice_growth_progress_on_small_rest(character)
        self.assertIn("growth_reward_pending:int", events)
        cards = rm.draw_growth_reward_cards(character, "int", draw_count=3, rng=random.Random(4))
        self.assertEqual(len(cards), 3)
        self.assertTrue(all(rm.is_growth_reward_legal(character, "int", card) for card in cards))

        before = len(character.dice_pool)
        rm.apply_growth_reward(character, "int", {"type": "add_new_die"})
        self.assertEqual(len(character.dice_pool), before + 1)

        str_before = len(character.dice_for("str"))
        rm.apply_growth_reward(character, "str", {"type": "add_new_die"})
        self.assertEqual(len(character.dice_for("str")), str_before + 1)
        self.assertGreaterEqual(len(character.dice_for("str")[-1].faces), 6)

        rm.add_degradation_progress(character, "dex", 6)
        self.assertEqual(character.degradation_penalty_pending["dex"], 1)
        penalties = rm.draw_degradation_penalty_cards(character, "dex", draw_count=3, rng=random.Random(5))
        self.assertEqual(len(penalties), 3)
        rm.apply_degradation_penalty(character, "dex", {"type": "seal_die"})
        self.assertTrue(any(die.enchantment == rm.ENCHANT_SEAL for die in character.dice_for("dex")))

    def test_pending_growth_reward_and_degradation_penalty_draws_are_consumed(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(13))
        character.growth_reward_pending["int"] = 1
        character.degradation_penalty_pending["dex"] = 1

        rewards = rm.draw_pending_growth_reward_cards(character, "int", draw_count=3, rng=random.Random(14))
        reward_result = rm.apply_pending_growth_reward(character, "int", rewards[0], rng=random.Random(15))
        penalties = rm.draw_pending_degradation_penalty_cards(character, "dex", draw_count=3, rng=random.Random(16))
        penalty_result = rm.apply_pending_degradation_penalty(character, "dex", penalties[0], rng=random.Random(17))

        self.assertEqual(len(rewards), 3)
        self.assertEqual(len(penalties), 3)
        self.assertTrue(reward_result["applied"])
        self.assertTrue(penalty_result["applied"])
        self.assertEqual(character.growth_reward_pending["int"], 0)
        self.assertEqual(character.degradation_penalty_pending["dex"], 0)

    def test_card_labels_are_chinese(self):
        self.assertEqual(rm.card_label({"type": "increase_chosen_face"}), "提升指定面值")
        self.assertEqual(rm.card_label({"type": "decrease_chosen_face"}), "降低指定面值")
        self.assertEqual(rm.card_label({"type": "seal_die"}), "封印骰子")

    def test_growth_reward_pool_weights_match_manual_distribution(self):
        self.assertEqual(sum(rm.GROWTH_REWARD_WEIGHTS.values()), 150)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["add_new_die"], 10)
        self.assertNotIn("upgrade_die_type", rm.GROWTH_REWARD_TYPES)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["upgrade_random_die_type"], 5)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["upgrade_chosen_die_type"], 5)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["replace_random_face_random_die"], 12)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["replace_random_face_chosen_die"], 12)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["replace_chosen_face_chosen_die"], 12)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["increase_random_face_random_die"], 18)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["increase_random_face_chosen_die"], 18)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["increase_chosen_face"], 18)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["add_light_enchant"], 10)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["add_swift_enchant"], 10)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["clear_negative_enchant"], 15)
        self.assertEqual(rm.GROWTH_REWARD_WEIGHTS["convert_negative_enchant"], 5)

    def test_growth_reward_internal_weights_match_manual_distribution(self):
        self.assertEqual(rm.REPLACEMENT_FACE_BAND_WEIGHTS["replace_random_face_random_die"], {"high": 3, "mid": 2, "low": 1})
        self.assertEqual(rm.REPLACEMENT_FACE_BAND_WEIGHTS["replace_random_face_chosen_die"], {"high": 2, "mid": 2, "low": 2})
        self.assertEqual(rm.REPLACEMENT_FACE_BAND_WEIGHTS["replace_chosen_face_chosen_die"], {"high": 1, "mid": 2, "low": 3})
        self.assertEqual(rm.INCREASE_FACE_AMOUNT_WEIGHTS["increase_random_face_random_die"], {2: 8, 1: 4})
        self.assertEqual(rm.INCREASE_FACE_AMOUNT_WEIGHTS["increase_random_face_chosen_die"], {2: 6, 1: 6})
        self.assertEqual(rm.INCREASE_FACE_AMOUNT_WEIGHTS["increase_chosen_face"], {2: 4, 1: 8})

    def test_new_die_reward_card_records_sides_total_and_description(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(24))
        card = rm.build_growth_reward_card(character, "str", "add_new_die", rng=random.Random(25))

        self.assertIn(card["die_sides"], (6, 8, 10))
        self.assertIn("face_total", card)
        self.assertIn("骰面总和为{}的{}面骰".format(card["face_total"], card["die_sides"]), rm.card_description(card))

    def test_new_die_reward_applies_card_sides_and_face_total(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(26))
        card = {"type": "add_new_die", "die_sides": 6, "face_total": 24}

        rm.apply_growth_reward(character, "str", card, rng=random.Random(27))
        die = character.dice_for("str")[-1]

        self.assertEqual(len(die.faces), 6)
        self.assertEqual(sum(die.faces), 24)
        self.assertTrue(all(1 <= face <= 6 for face in die.faces))

    def test_reward_card_descriptions_include_generated_face_values(self):
        replace_card = {"type": "replace_random_face_chosen_die", "new_face_value": 3}
        increase_card = {"type": "increase_chosen_face", "increase_amount": 2}

        self.assertIn("数值为3", rm.card_description(replace_card))
        self.assertIn("+2", rm.card_description(increase_card))

    def test_capped_faces_are_illegal_at_draw_selection_and_settlement(self):
        for kind in rm.INCREASE_FACE_AMOUNT_WEIGHTS:
            state = rm.create_initial_character(rng=random.Random(80))
            die = state.dice_for("str")[0]
            die.faces = [6] * 6
            capped = rm.RMDice("str_capped", "str", [8] * 8)
            state.dice_pool.append(capped)
            self.assertNotIn(kind, rm.legal_growth_reward_types(state, "str"))
            state.growth_reward_pending["str"] = 1
            card = {"type": kind, "increase_amount": 2}
            self.assertFalse(rm.apply_pending_growth_reward(state, "str", card)["applied"])
            self.assertEqual(state.growth_reward_pending["str"], 1)
            die.faces[2] = 5
            self.assertEqual(rm.growth_reward_dice_candidates(state, "str", card), [die])
            self.assertEqual(rm.growth_reward_face_indices(die, card), [2])
            if rm.card_needs_die_choice(card):
                for bad in (dict(card, die_id=capped.id), dict(card, die_id=die.id, face_index=0)):
                    self.assertFalse(rm.apply_pending_growth_reward(state, "str", bad)["applied"])
                    self.assertEqual(state.growth_reward_pending["str"], 1)
                card["die_id"] = die.id
            if rm.card_needs_face_choice(card):
                card["face_index"] = 2
            self.assertTrue(rm.apply_pending_growth_reward(state, "str", card, random.Random(81))["applied"])
            self.assertEqual(die.faces, [6] * 6)  # +2 overflow is discarded.
            self.assertEqual(capped.faces, [8] * 8)
            self.assertEqual(state.growth_reward_pending["str"], 0)

    def test_replacement_cards_reveal_values_for_each_target_type(self):
        class HighBandLowValue(random.Random):
            def uniform(self, low, high):
                return low
            def randint(self, low, high):
                return low

        state = rm.create_initial_character(rng=random.Random(82))
        small = state.dice_for("str")[0]
        state.dice_pool.append(rm.RMDice("str_d12", "str", [1] * 12))
        for kind in rm.REPLACEMENT_FACE_BAND_WEIGHTS:
            card = rm.build_growth_reward_card(state, "str", kind, HighBandLowValue())
            self.assertEqual(card["new_face_values"], {"6": 5, "12": 9})
            self.assertIn("d6：5", rm.card_description(card))
            self.assertIn("d12：9", rm.card_description(card))
            for die in (small, state.find_die("str_d12")):
                die.faces = [1] * len(die.faces)
                selected = dict(card, type="replace_chosen_face_chosen_die", die_id=die.id, face_index=0)
                self.assertTrue(rm.apply_growth_reward(state, "str", selected)["applied"])
                self.assertEqual(die.faces[0], card["new_face_values"][str(len(die.faces))])
        self.assertEqual(rm._face_value_for_band(20, "low", HighBandLowValue()), 2)
        self.assertEqual(rm._face_value_for_band(12, "low", HighBandLowValue()), 2)

    def test_reward_cards_do_not_mix_chosen_and_random_die_wording(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(30))

        for card_type in rm.GROWTH_REWARD_TYPES:
            card = rm.build_growth_reward_card(character, "str", card_type, rng=random.Random(31))
            self.assertNotIn("选择或随机", rm.card_description(card))

    def test_upgrade_die_type_has_separate_random_and_chosen_cards(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(32))
        character.dice_pool.append(rm.RMDice("str_extra", "str", [9] * 12))
        target = character.dice_for("str")[0]
        other = character.dice_for("str")[1]
        target.faces = [1, 2, 3, 4, 5, 6]
        other.faces = [9] * 12

        self.assertFalse(rm.card_needs_die_choice({"type": "upgrade_random_die_type"}))
        self.assertTrue(rm.card_needs_die_choice({"type": "upgrade_chosen_die_type"}))

        result = rm.apply_growth_reward(
            character,
            "str",
            {"type": "upgrade_chosen_die_type", "die_id": target.id},
            rng=random.Random(33),
        )

        self.assertTrue(result["applied"])
        self.assertEqual(target.faces, [1, 2, 3, 4, 5, 6, 1, 6])
        self.assertEqual(other.faces, [9] * 12)

    def test_fixed_die_types_and_owned_limits_apply_at_draw_and_settlement(self):
        for attr, sides in (("pow", 20), ("con", 4)):
            with self.subTest(attr=attr):
                character = rm.create_initial_character(rng=random.Random(40))
                original = [list(die.faces) for die in character.dice_for(attr)]
                for card_type in ("upgrade_random_die_type", "upgrade_chosen_die_type"):
                    card = {"type": card_type, "die_id": character.dice_for(attr)[0].id}
                    self.assertNotIn(card_type, rm.legal_growth_reward_types(character, attr))
                    self.assertFalse(rm.apply_growth_reward(character, attr, card)["applied"])
                self.assertNotIn("downgrade_die_type", rm.legal_degradation_penalty_types(character, attr))
                self.assertFalse(rm.apply_degradation_penalty(character, attr, {"type": "downgrade_die_type"})["applied"])
                self.assertEqual([die.faces for die in character.dice_for(attr)], original)

                character.growth_reward_pending[attr] = 2
                card = {"type": "add_new_die"}
                self.assertTrue(rm.apply_pending_growth_reward(character, attr, card)["applied"])
                self.assertEqual(character.dice_for(attr)[-1].faces, [1] * sides)
                self.assertFalse(rm.apply_pending_growth_reward(character, attr, card)["applied"])
                self.assertEqual(character.growth_reward_pending[attr], 1)
                self.assertEqual(len(character.dice_for(attr)), 3)
                forbidden = {"add_new_die", "upgrade_random_die_type", "upgrade_chosen_die_type"}
                for seed in range(30):
                    cards = rm.draw_pending_growth_reward_cards(character, attr, rng=random.Random(seed))
                    self.assertEqual(len(cards), 3)
                    self.assertTrue(all(card["type"] not in forbidden for card in cards))

    def test_new_die_card_parameters_cannot_bypass_attribute_type(self):
        character = rm.create_initial_character(rng=random.Random(41))
        character.growth_reward_pending["pow"] = 1
        original = [list(die.faces) for die in character.dice_pool]
        for sides, total in ((21, 21), (6, 20), (20, 400)):
            card = {"type": "add_new_die", "die_sides": sides, "face_total": total}
            self.assertFalse(rm.apply_pending_growth_reward(character, "pow", card)["applied"])
        self.assertEqual([die.faces for die in character.dice_pool], original)
        self.assertEqual(character.growth_reward_pending["pow"], 1)

    def test_other_attributes_stop_at_five_owned_dice(self):
        for attr in rm.ALLOCATED_ATTRIBUTES:
            character = rm.create_initial_character(rng=random.Random(42))
            for _ in range(4):
                self.assertTrue(rm.apply_growth_reward(character, attr, {"type": "add_new_die"})["applied"])
            self.assertNotIn("add_new_die", rm.legal_growth_reward_types(character, attr))
            self.assertFalse(rm.apply_growth_reward(character, attr, {"type": "add_new_die"})["applied"])
            self.assertEqual(len(character.dice_for(attr)), 5)

    def test_upgrade_steps_filter_capped_dice_and_preserve_pending_reward(self):
        for attr in rm.ALLOCATED_ATTRIBUTES:
            character = rm.create_initial_character(rng=random.Random(43))
            die = character.dice_for(attr)[0]
            die.faces = [1, 2, 3, 4, 5, 6]
            capped = rm.RMDice(attr + "_capped", attr, [12] * 12)
            character.dice_pool.append(capped)
            character.growth_reward_pending[attr] = 1
            stale = {"type": "upgrade_chosen_die_type", "die_id": capped.id}
            self.assertFalse(rm.apply_pending_growth_reward(character, attr, stale)["applied"])
            self.assertEqual(character.growth_reward_pending[attr], 1)
            for sides in (8, 10, 12):
                before = list(die.faces)
                self.assertEqual(rm.dice_type_change_candidates(character, attr), [die])
                result = rm.apply_growth_reward(character, attr, {"type": "upgrade_random_die_type"})
                self.assertTrue(result["applied"])
                self.assertEqual(die.faces, before + [min(before), max(before)])
                self.assertEqual(len(die.faces), sides)
                self.assertEqual(capped.faces, [12] * 12)
            self.assertFalse(rm.apply_growth_reward(character, attr, {"type": "upgrade_random_die_type"})["applied"])
            self.assertNotIn("upgrade_chosen_die_type", rm.legal_growth_reward_types(character, attr))

    def test_downgrade_removes_two_lowest_faces_and_clamps_to_new_type(self):
        character = rm.create_initial_character(rng=random.Random(44))
        die = character.dice_for("str")[0]
        die.faces = [12, 1, 9, 2, 10, 3, 8, 4, 11, 5, 6, 7]
        floor_die = rm.RMDice("str_floor", "str", [1, 2, 3, 4, 5, 6])
        character.dice_pool.append(floor_die)
        for sides in (10, 8, 6):
            remaining = list(die.faces)
            for _ in range(2):
                remaining.remove(min(remaining))
            result = rm.apply_degradation_penalty(character, "str", {"type": "downgrade_die_type"})
            self.assertTrue(result["applied"])
            self.assertEqual(die.faces, [min(value, sides) for value in remaining])
            self.assertEqual(floor_die.faces, [1, 2, 3, 4, 5, 6])
        character.degradation_penalty_pending["str"] = 1
        self.assertFalse(rm.apply_pending_degradation_penalty(character, "str", {"type": "downgrade_die_type"})["applied"])
        self.assertEqual(character.degradation_penalty_pending["str"], 1)

    def test_d6_is_not_a_legal_downgrade_target_for_any_allocated_attribute(self):
        character = rm.create_initial_character(rng=random.Random(45))
        for attr in rm.ALLOCATED_ATTRIBUTES:
            before = list(character.dice_for(attr)[0].faces)
            self.assertEqual(rm.dice_type_change_candidates(character, attr, upgrade=False), [])
            self.assertNotIn("downgrade_die_type", rm.legal_degradation_penalty_types(character, attr))
            for seed in range(20):
                cards = rm.draw_degradation_penalty_cards(character, attr, rng=random.Random(seed))
                self.assertTrue(all(card["type"] != "downgrade_die_type" for card in cards))
            result = rm.apply_degradation_penalty(character, attr, {"type": "downgrade_die_type"})
            self.assertFalse(result["applied"])
            self.assertEqual(character.dice_for(attr)[0].faces, before)

    def test_negative_enchant_rewards_require_and_use_chosen_die(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(34))
        character.dice_pool.append(rm.RMDice("str_extra", "str", [9, 9, 9, 9]))
        first = character.dice_for("str")[0]
        second = character.dice_for("str")[1]
        rm.set_die_enchantment(first, rm.ENCHANT_HEAVY)
        rm.set_die_enchantment(second, rm.ENCHANT_SLUGGISH)

        self.assertTrue(rm.card_needs_die_choice({"type": "clear_negative_enchant"}))
        self.assertTrue(rm.card_needs_die_choice({"type": "convert_negative_enchant"}))

        clear_result = rm.apply_growth_reward(
            character,
            "str",
            {"type": "clear_negative_enchant", "die_id": second.id},
            rng=random.Random(35),
        )
        convert_result = rm.apply_growth_reward(
            character,
            "str",
            {"type": "convert_negative_enchant", "die_id": first.id},
            rng=random.Random(36),
        )

        self.assertTrue(clear_result["applied"])
        self.assertTrue(convert_result["applied"])
        self.assertIsNone(second.enchantment)
        self.assertIn(first.enchantment, rm.POSITIVE_ENCHANTMENTS)

    def test_reward_cards_apply_replace_value_and_increase_amount(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(21))
        die = character.dice_for("str")[0]
        die.faces = [1, 2, 3, 4, 5, 6]

        rm.apply_growth_reward(
            character,
            "str",
            {"type": "replace_random_face_chosen_die", "die_id": die.id, "face_index": 1, "new_face_value": 6},
            rng=random.Random(22),
        )
        rm.apply_growth_reward(
            character,
            "str",
            {"type": "increase_chosen_face", "die_id": die.id, "face_index": 2, "increase_amount": 2},
            rng=random.Random(23),
        )

        self.assertEqual(die.faces, [1, 6, 5, 4, 5, 6])

    def test_chosen_die_and_face_cards_use_player_selection(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(18))
        character.dice_pool.append(rm.RMDice("str_extra", "str", [9, 9, 9, 9]))
        target = character.dice_for("str")[0]
        other = character.dice_for("str")[1]
        target.faces = [1, 2, 3, 4]
        other.faces = [9, 9, 9, 9]

        reward = rm.apply_growth_reward(
            character,
            "str",
            {"type": "increase_chosen_face", "die_id": target.id, "face_index": 2},
            rng=random.Random(19),
        )
        penalty = rm.apply_degradation_penalty(
            character,
            "str",
            {"type": "decrease_chosen_face", "die_id": target.id, "face_index": 2},
            rng=random.Random(20),
        )
        missing_choice_penalty = rm.apply_degradation_penalty(
            character,
            "str",
            {"type": "decrease_chosen_face", "face_index": 1},
            rng=random.Random(201),
        )

        self.assertTrue(reward["applied"])
        self.assertTrue(penalty["applied"])
        self.assertFalse(missing_choice_penalty["applied"])
        self.assertEqual(target.faces, [1, 2, 3, 4])
        self.assertEqual(other.faces, [9, 9, 9, 9])

    def test_fog_cards_and_temporary_enchant_decay(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(6))
        cards = [{"type": "add_new_die"}, {"type": "upgrade_random_die_type"}, {"type": "add_light_enchant"}]

        fogged = rm.apply_fog_to_cards(cards, rng=random.Random(7))
        self.assertTrue(any(not card["fogged"] for card in fogged))
        self.assertEqual(len(rm.draw_visible_or_fogged_cards(cards, 3, rng=random.Random(7))), 3)

        outcome = rm.resolve_fog_reward(character, "str", {"type": "add_new_die"}, rng=random.Random(1))
        self.assertIn(outcome["mode"], ("normal", "double", "null", "to_penalty"))

        die = character.dice_for("str")[0]
        rm.set_die_enchantment(die, rm.ENCHANT_LIGHT, temporary=True)
        removed = rm.process_temporary_enchant_decay(character, rng=random.Random(1))
        self.assertIn(die.id, removed)
        self.assertIsNone(die.enchantment)

    def test_full_turn_day_and_week_entry_points(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(8))
        rm.start_turn(character, "morning_1")
        result = rm.resolve_action(character, rm.ScheduleSpec("mock_study", "Mock Study", mood_delta=5))
        settlement = rm.end_turn(character, result, rng=random.Random(9))

        self.assertEqual(character.time_slot_index, 1)
        self.assertIn("mood_delta", settlement)

        character.mood = 100
        day = rm.end_day(character, rng=random.Random(10))
        self.assertIn("sleep_recovery", day["events"])

        character.day = 7
        week = rm.end_week_if_needed(character, rng=random.Random(11))
        self.assertIn("large_rest", week["events"])


if __name__ == "__main__":
    unittest.main()
