init -11 python:
    def apply_fog_to_cards(cards):
        return rm_core.apply_fog_to_cards(cards, rng=renpy.random)

    def resolve_fog_reward(state, attr, reward_card):
        return rm_core.resolve_fog_reward(state, attr, reward_card, rng=renpy.random)

    def resolve_fog_penalty(state, attr, penalty_card):
        return rm_core.resolve_fog_penalty(state, attr, penalty_card, rng=renpy.random)

    def draw_visible_or_fogged_cards(pool, draw_count):
        return rm_core.draw_visible_or_fogged_cards(pool, draw_count, rng=renpy.random)

    def ensure_at_least_one_visible(cards):
        return rm_core.ensure_at_least_one_visible(cards, rng=renpy.random)

    def rm_fog_probability(hidden_count):
        """Return the default fog chance for the next growth or penalty card."""
        if hidden_count <= 0:
            return 0.30
        if hidden_count == 1:
            return 0.25
        return 0.20

    def rm_resolve_mock_fog_card(card_kind="reward"):
        """Skeleton fog resolution for testing later growth-card integrations."""
        roll = renpy.random.random()
        if card_kind == "reward":
            if roll < 0.55:
                return "reward_normal"
            if roll < 0.85:
                return "reward_double"
            if roll < 0.95:
                return "reward_null"
            return "reward_to_penalty"
        if roll < 0.40:
            return "penalty_normal"
        if roll < 0.70:
            return "penalty_null"
        if roll < 0.90:
            return "penalty_to_reward"
        return "penalty_double"
