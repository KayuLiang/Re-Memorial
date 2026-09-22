"""Core numeric backend for Re: Memorial.

The implementation lives in pure Python so the Ren'Py wrappers can stay thin
and the formulas can be tested outside the engine.
"""

from __future__ import division

import math
import random

try:
    from renpy.revertable import RevertableObject, RevertableDict, RevertableList
except ImportError:
    # Keep the numeric backend runnable outside Ren'Py.
    RevertableObject, RevertableDict, RevertableList = object, dict, list


ATTRIBUTES = ("con", "str", "dex", "int", "pow")
ALLOCATED_ATTRIBUTES = ("str", "dex", "int")
TEST_TRAINING_ATTRIBUTES = ("str", "dex")
TEST_TRAINING_SCHEDULE_ATTRIBUTES = {
    "test_strength_training": "str",
    "test_dex_training": "dex",
    "test_jogging": "con",
}
TEST_TRAINING_SCHEDULE_LABELS = {
    "test_strength_training": "力量训练",
    "test_dex_training": "灵巧训练",
    "test_jogging": "慢跑",
}
JOGGING_BONUS_ATTRIBUTES = ("con", "dex", "str")
JOGGING_BONUS_WEIGHTS = (("con", 70), ("dex", 30), ("str", 30))

ACTION_SCHEDULE = "schedule"
ACTION_INSTANT = "instant"
ACTION_FORCED_SCHEDULE = "forced_schedule"
ACTION_WAKE = "wake"
ACTION_SLEEP = "sleep"

MOOD_STABLE = "stable"
MOOD_HIGH = "high"
MOOD_LOW = "low"
DISEASE_NONE = "none"
DISEASE_MANIA = "mania"
DISEASE_DEPRESSION = "depression"

ENCHANT_LIGHT = "light"
ENCHANT_SWIFT = "swift"
ENCHANT_SEAL = "seal"
ENCHANT_SHACKLE = "shackle"
ENCHANT_HEAVY = "heavy"
ENCHANT_SLUGGISH = "sluggish"

RESULT_BIG_FAILURE = "big_failure"
RESULT_FAILURE = "failure"
RESULT_SUCCESS = "success"
RESULT_HARD_SUCCESS = "hard_success"
RESULT_BIG_SUCCESS = "big_success"

EMOTION_JOY = "joy"
EMOTION_CALM = "calm"
EMOTION_EXCITEMENT = "excitement"
EMOTION_SADNESS = "sadness"
EMOTION_ANXIETY = "anxiety"
EMOTION_DISTRACTION = "distraction"

WEATHER_SUNNY = "sunny"
WEATHER_CLOUDY = "cloudy"
WEATHER_LIGHT_RAIN = "light_rain"
WEATHER_HEAVY_RAIN = "heavy_rain"
WEATHER_STORM = "storm"
WEATHER_THUNDERSTORM = "thunderstorm"
WEATHER_FOG = "fog"
WEATHER_LIGHT_SNOW = "light_snow"
WEATHER_HEAVY_SNOW = "heavy_snow"

STRENGTH_TRAINING_STR_BONUS_TOTAL_CHANCE = {
    1: 3.00,
    2: 2.80,
    3: 2.60,
    4: 2.40,
    5: 2.20,
    6: 2.00,
    7: 2.00,
    8: 1.80,
    9: 1.60,
    10: 1.40,
    11: 1.20,
    12: 1.00,
    13: 1.00,
    14: 0.92,
    15: 0.86,
    16: 0.80,
    17: 0.72,
    18: 0.64,
    19: 0.57,
    20: 0.50,
}


ATTRIBUTE_LABELS = {
    "con": "体质",
    "str": "力量",
    "dex": "灵巧",
    "int": "智识",
    "pow": "意志",
}

MOOD_LABELS = {
    MOOD_STABLE: "平稳",
    MOOD_HIGH: "高涨",
    MOOD_LOW: "低落",
    DISEASE_MANIA: "躁狂",
    DISEASE_DEPRESSION: "抑郁",
}

DISEASE_LABELS = {
    DISEASE_NONE: "无病程",
    DISEASE_MANIA: "躁狂病程",
    DISEASE_DEPRESSION: "抑郁病程",
}

ENCHANTMENT_LABELS = {
    None: "无",
    ENCHANT_LIGHT: "轻盈",
    ENCHANT_SWIFT: "奖励骰",
    ENCHANT_SEAL: "封印",
    ENCHANT_SHACKLE: "枷锁",
    ENCHANT_HEAVY: "沉重",
    ENCHANT_SLUGGISH: "迟滞",
}


def clamp(value, low, high):
    return max(low, min(high, value))


def _rng(rng):
    return rng if rng is not None else random


class RMDice(RevertableObject):
    def __init__(self, dice_id, attribute, faces, enchantment=None, temporary=False):
        self.id = dice_id
        self.attribute = attribute
        self.faces = RevertableList(faces)
        self.enchantment = enchantment
        self.temporary = temporary
        self.rest_age = 0

    def expectation(self):
        return sum(self.faces) / float(len(self.faces))

    def minimum(self):
        return min(self.faces)

    def maximum(self):
        return max(self.faces)

    def is_sealed(self):
        return self.enchantment == ENCHANT_SEAL

    def copy(self):
        copied = RMDice(self.id, self.attribute, self.faces, self.enchantment, self.temporary)
        copied.rest_age = self.rest_age
        return copied


class RMCharacterState(RevertableObject):
    def __init__(self, formal_attributes, dice_pool, mood=0, disease_state=DISEASE_NONE):
        self.formal_attributes = RevertableDict(formal_attributes)
        self.health = float(health_max(self))
        self.attribute_values = RevertableDict((name, 0) for name in ATTRIBUTES)
        self.attribute_bonuses = RevertableDict((name, RevertableList()) for name in ATTRIBUTES)
        self.dice_pool = RevertableList(dice_pool)
        self.mood = int(mood)
        self.disease_state = disease_state
        self.man = 0
        self.dep = 0
        self.disease_turns = 0
        self.good_routine = False
        self.good_routine_streak = 0
        self.late_night_energy_schedule_week_count = 0
        self.next_day_energy_cap_penalty = 0  # Legacy save field; fatigue now owns this penalty.
        self.test_growth_progress = RevertableDict((name, 0) for name in TEST_TRAINING_ATTRIBUTES)
        self.training_fatigue = RevertableDict((name, 0) for name in TEST_TRAINING_SCHEDULE_ATTRIBUTES)
        self.dice_growth_progress = RevertableDict((name, 0) for name in ATTRIBUTES)
        self.growth_reward_pending = RevertableDict((name, 0) for name in ATTRIBUTES)
        self.degradation_progress = RevertableDict((name, 0) for name in ATTRIBUTES)
        self.degradation_penalty_pending = RevertableDict((name, 0) for name in ATTRIBUTES)
        self.attribute_bonus_gain_counters = RevertableDict((name, 0) for name in ATTRIBUTES)
        self.attribute_value_gain_counters = RevertableDict((name, 0) for name in ATTRIBUTES)
        self.formal_attribute_gain_counters = RevertableDict((name, 0) for name in ATTRIBUTES)
        self.day = 1
        self.weekday = 1
        self.time_slot_index = 0
        self.current_time_slot = None
        self.night_actions_completed = 0
        self.night_snack_eaten = False
        self.meal_choices = RevertableDict()
        self.sleep_pending = None
        self.sleep_fatigue = RevertableList()
        self.fatigue_layers = 0
        self.fatigue_history = RevertableList()
        self.drowsiness = 0
        self.deep_fatigue = None
        self.next_day_energy_cap_bonus = 0
        self.emotions = RevertableDict()
        self.check_streak = RevertableDict(success=0, failure=0)
        self.long_emotions = RevertableDict(confidence=False, doubt=False)
        self.ember = None
        self.bipolar_ember = None
        self.ect_residual_days = 0
        self.pending_bipolar_medications = RevertableDict()
        self.medicine_counts = RevertableDict()
        self.medicine_taken_today = RevertableDict()
        self.psych_medication_days = RevertableList()
        self.drug_dependence = False
        self.initial_gameplay_statuses_applied = False
        self.current_weather = None
        self.current_temperature = None
        self.weather_override = None
        self.environment_diseases = RevertableDict()
        self.environment_natural_cure_rewards = RevertableDict()
        self.injuries = RevertableDict()
        self.ever_had_pain_and_scars = False
        self.exposure_rounds = RevertableDict(cold=0, heat=0)
        self.hunger_level = 0
        self.meal_satiety_progress = 0
        self.overeating_history = RevertableList()
        self.severe_hunger_history = RevertableList()
        self.digestive_disorder = None
        self.malnutrition = None
        self.palpitations = False
        self.intoxication = 0
        self.coffee_count_today = 0
        self.time_habit_history = RevertableList()
        self.time_habits = RevertableDict()
        self.daytime_sleep_pending = None
        self.energy = energy_max(self)

    def dice_for(self, attribute):
        return [die for die in self.dice_pool if die.attribute == attribute]

    def find_die(self, dice_id):
        for die in self.dice_pool:
            if die.id == dice_id:
                return die
        return None

    def current_attribute(self, attribute):
        return current_attribute(self, attribute)

    def effective_attribute(self, attribute):
        return effective_attribute(self, attribute)


class CheckSpec(object):
    def __init__(
        self,
        attribute,
        requirement,
        dice_ids=None,
        action_type=ACTION_SCHEDULE,
        max_dice=3,
        min_dice=1,
        extra_modifier=0,
        forced=False,
        is_late_night=False,
        big_failure_slack=0,
        allowed_dice_attributes=None,
        required_dice_attributes=None,
        check_context=None,
        schedule_category=None,
        location=None,
        outdoors=False,
        sport=False,
        social=False,
        rest=False,
    ):
        self.attribute = attribute
        self.requirement = requirement
        self.dice_ids = list(dice_ids or [])
        self.action_type = action_type
        self.max_dice = max_dice
        self.min_dice = min_dice
        self.extra_modifier = extra_modifier
        self.forced = forced
        self.is_late_night = is_late_night
        self.big_failure_slack = int(big_failure_slack)
        self.allowed_dice_attributes = tuple(allowed_dice_attributes or (attribute,))
        self.required_dice_attributes = tuple(required_dice_attributes or ())
        self.check_context = check_context or ("schedule" if action_type in (ACTION_SCHEDULE, ACTION_FORCED_SCHEDULE) else "internal")
        self.schedule_category = schedule_category
        self.location = location
        self.outdoors = bool(outdoors)
        self.sport = bool(sport)
        self.social = bool(social)
        self.rest = bool(rest)


class CheckResult(object):
    def __init__(self, **kwargs):
        self.available = kwargs.get("available", True)
        self.reason = kwargs.get("reason", "")
        self.attribute = kwargs.get("attribute")
        self.requirement = kwargs.get("requirement", 0)
        self.base_requirement = kwargs.get("base_requirement", self.requirement)
        self.mood_state = kwargs.get("mood_state", MOOD_STABLE)
        self.attribute_modifier = kwargs.get("attribute_modifier", 0)
        self.dice_multiplier = kwargs.get("dice_multiplier", 1.0)
        self.extra_modifier = kwargs.get("extra_modifier", 0)
        self.dice_total = kwargs.get("dice_total", 0)
        self.total = kwargs.get("total", 0)
        self.rank = kwargs.get("rank", RESULT_FAILURE)
        self.success = kwargs.get("success", False)
        self.energy_cost = kwargs.get("energy_cost", 0)
        self.dice_ids = list(kwargs.get("dice_ids", []))
        self.dice_results = list(kwargs.get("dice_results", []))
        self.dice_count = kwargs.get("dice_count", len(self.dice_ids))
        self.emotion_events = list(kwargs.get("emotion_events", []))

    def as_dict(self):
        return dict(self.__dict__)


class ScheduleSpec(object):
    def __init__(self, schedule_id, name, check_spec=None, mood_delta=0):
        self.id = schedule_id
        self.name = name
        self.check_spec = check_spec
        self.mood_delta = mood_delta


def validate_initial_allocation(allocation):
    values = {name: int(allocation.get(name, 0)) for name in ALLOCATED_ATTRIBUTES}
    if sum(values.values()) != 8:
        raise ValueError("STR, DEX, and INT must total 8.")
    if any(values[name] < 1 for name in ALLOCATED_ATTRIBUTES):
        raise ValueError("STR, DEX, and INT must each be at least 1.")
    return values


def strengthen_faces(faces, points, face_cap, rng=None):
    rng = _rng(rng)
    result = list(faces)
    for _ in range(int(points)):
        candidates = [idx for idx, face in enumerate(result) if face < face_cap]
        if not candidates:
            break
        result[rng.choice(candidates)] += 1
    return result


def create_initial_dice(allocation, rng=None):
    rng = _rng(rng)
    dice = [
        RMDice("con_1", "con", [1, 2, 3, 4]),
        RMDice("con_2", "con", [1, 1, 2, 2]),
        RMDice("pow_1", "pow", list(range(1, 21))),
        RMDice("pow_2", "pow", [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10]),
    ]
    for attribute in ALLOCATED_ATTRIBUTES:
        faces = strengthen_faces([1, 2, 3, 4, 5, 6], allocation[attribute] * 2, 6, rng)
        dice.append(RMDice(attribute + "_1", attribute, faces))
    return dice


def create_initial_character(allocation=None, rng=None):
    allocation = validate_initial_allocation(allocation or {"str": 3, "dex": 3, "int": 2})
    formal = {"con": 6, "pow": 6}
    formal.update(allocation)
    return RMCharacterState(formal, create_initial_dice(allocation, rng))


def create_opening_draft_character(rng=None):
    allocation = {"str": 1, "dex": 1, "int": 1}
    formal = {"con": 6, "pow": 6}
    formal.update(allocation)
    return RMCharacterState(formal, create_initial_dice(allocation, rng))


def initial_allocation_from_character(character):
    return {name: int(character.formal_attributes.get(name, 0)) for name in ALLOCATED_ATTRIBUTES}


def initial_attribute_points_remaining(character):
    allocation = initial_allocation_from_character(character)
    return 8 - sum(allocation.values())


def can_reallocate_initial_attribute(character, attribute, delta):
    if attribute not in ALLOCATED_ATTRIBUTES or delta not in (-1, 1):
        return False
    allocation = initial_allocation_from_character(character)
    next_value = allocation[attribute] + delta
    if next_value < 1:
        return False
    next_total = sum(allocation.values()) + delta
    return 3 <= next_total <= 8


def reallocate_initial_attributes(character, attribute, delta, rng=None):
    allocation = initial_allocation_from_character(character)
    if not can_reallocate_initial_attribute(character, attribute, delta):
        return character
    allocation[attribute] += delta
    formal = {"con": 6, "pow": 6}
    formal.update(allocation)
    return RMCharacterState(formal, create_initial_dice(allocation, rng))


def current_attribute(character, attribute):
    base = int(character.formal_attributes.get(attribute, 0))
    value = int(character.attribute_values.get(attribute, 0))
    bonus = sum(int(item.get("value", 0)) if isinstance(item, dict) else int(item) for item in character.attribute_bonuses.get(attribute, []))
    modifier = sleep_attribute_modifier(character, attribute)
    if attribute == "dex" and getattr(character, "digestive_disorder", None):
        modifier -= int(character.digestive_disorder.get("layers", 0))
    if attribute == "str" and getattr(character, "malnutrition", None):
        modifier -= int(character.malnutrition.get("layers", 0))
    return base + value + bonus + modifier


def sleep_attribute_modifier(character, attribute):
    if attribute == "con":
        return -int((getattr(character, "deep_fatigue", None) or {}).get("layers", 0))
    return 0


def sleep_status_summary(state):
    ensure_second_stage_state(state)
    rows = []
    if state.fatigue_layers:
        rows.append(_status_row("sleep_fatigue", "疲劳", "×{}".format(state.fatigue_layers),
            "生理类：每层精力上限 -1；仅按时夜间睡眠清除，不自动到期。", category="physiological"))
    disease = getattr(state, "deep_fatigue", None)
    if disease:
        rows.append(_status_row("deep_fatigue", "深度疲劳", "×{}".format(disease["layers"]),
            "疾病类：体质临时 -{0}；距结算还有 {1} 晚。患病后再次熬夜，每晚加一层，不延长结算时间。{2}".format(
                disease["layers"], disease["last_night"] - state.day + 1,
                "结算时将永久减少 {} 点体质。".format(disease["layers"]) if disease["relapsed"]
                else "这七晚均按时睡觉可避免永久体质损失；康复不直接获得健康作息。"), "con", "disease"))
    if getattr(state, "good_routine", False):
        rows.append(_status_row("good_routine", "健康作息", "",
            "日程类：提供精力充沛与优质睡眠。熬夜后25%抵消新增疲劳和困意且保留，50%抵消并消耗，25%不抵消并消耗。",
            category="schedule"))
        rows.append(_status_row("energetic", "精力充沛", "", "健康作息提供：精力上限 +25%，向下取整。", category="schedule"))
        rows.append(_status_row("quality_sleep", "优质睡眠", "", "健康作息提供：加强睡眠 Mood 恢复。", category="schedule"))
    return rows


def vnext_status_summary(state):
    ensure_second_stage_state(state)
    rows = []
    if state.current_weather:
        rows.append(_status_row("weather", WEATHER_LABELS[state.current_weather],
            "{}°".format(state.current_temperature), "天气类：{}，气温{}。".format(
                WEATHER_LABELS[state.current_weather], temperature_band(state.current_temperature)), category="weather"))
    if state.ember is not None:
        rows.append(_status_row("ember", "余烬", "×{}".format(state.ember),
            "心情类：每日晨间使 Mood 向负向变化；抑郁病态期间锁定。", category="mood"))
    if state.bipolar_ember is not None:
        rows.append(_status_row("bipolar_ember", "余烬·双相", "×{}".format(state.bipolar_ember),
            "心情类：每日晨间产生随机方向的 Mood 变化。", category="mood"))
    if state.ect_residual_days:
        rows.append(_status_row("ect_residual", "电残留", "{}日".format(state.ect_residual_days),
            "心情类：晨间正向 Mood 效果线性衰减。", category="mood"))
    for emotion in EMOTION_LABELS:
        layers = emotion_layers(state, emotion)
        if layers:
            rows.append(_status_row("emotion_" + emotion, EMOTION_LABELS[emotion], "×{}".format(layers),
                "情绪类：在符合条件的下一次普通日程或剧情属性检定中生效。", category="emotion"))
    if state.long_emotions.get("confidence"):
        rows.append(_status_row("confidence", "自信", "", "情绪类：任意检定获得1个奖励骰；连续3次失败解除。", category="emotion"))
    if state.long_emotions.get("doubt"):
        rows.append(_status_row("doubt", "怀疑", "", "情绪类：任意检定获得1个惩罚骰；连续3次成功解除。", category="emotion"))
    if state.palpitations:
        rows.append(_status_row("palpitations", "心悸", "", "生理类：所有检定最终值 ×0.75，完整睡眠后解除。", category="physiological"))
    if state.intoxication:
        label = "微醺" if state.intoxication <= 2 else "醉酒"
        layers = state.intoxication if state.intoxication <= 2 else state.intoxication - 2
        rows.append(_status_row("intoxication", label, "×{}".format(layers),
            "药物与物质类：影响普通检定与社交检定；完整睡眠后清除。", category="medication"))
    if state.hunger_level:
        rows.append(_status_row("hunger", "饥饿", "×{}".format(state.hunger_level),
            "生理类：每日小休后向无状态移动一级。", category="physiological"))
    if state.drug_dependence:
        rows.append(_status_row("drug_dependence", "药物依赖", "",
            "药物类：药盒节点未服精神科药物时，Mood 沿当前方向严重化5%。", category="medication"))
    for medicine in state.pending_bipolar_medications:
        rows.append(_status_row("pending_" + medicine, medicine, "",
            "药物类：作用于下一次晨间余烬·双相结算，结算后失效。", category="medication"))
    for disease, item in state.environment_diseases.items():
        label = "感冒" if disease == "cold" else "中暑"
        suffix = "·加重" if int(item.get("stage", 1)) >= 2 else ""
        rows.append(_status_row("environment_disease_" + disease, label + suffix, "",
            "伤病类：所有检定获得1个惩罚骰；晨间先判定康复，失败后结算伤害。", category="injury"))
    for injury, item in state.injuries.items():
        labels = {"strain": "肌肉拉伤", "sprain": "扭伤", "fracture": "骨折"}
        rows.append(_status_row("injury_" + injury, labels[injury],
            "再伤{}".format(item.get("reinjury", 0)) if item.get("reinjury", 0) else "",
            "伤病类：运动/战斗类检定最终值受伤病倍率影响。", category="injury"))
    if state.digestive_disorder:
        rows.append(_status_row("digestive_disorder", "消化不良", "×{}".format(state.digestive_disorder["layers"]),
            "伤病类：每层当前灵巧-1。", "dex", "injury"))
    if state.malnutrition:
        rows.append(_status_row("malnutrition", "营养不良", "×{}".format(state.malnutrition["layers"]),
            "伤病类：每层当前力量-1。", "str", "injury"))
    return rows


def effective_attribute(character, attribute):
    return min(current_attribute(character, attribute), 20)


def health_max(character):
    """Only formal CON contributes; temporary modifiers never alter HP."""
    return max(0, int(character.formal_attributes.get("con", 0))) * 5


def ensure_health(character):
    # Old saves have no wound history: initialize once, never refill on load.
    if not hasattr(character, "health"):
        character.health = float(health_max(character))


def is_dead(character):
    ensure_health(character)
    return character.health <= 0


def change_health(character, amount):
    """Signed event effect. Death is terminal; loading/rollback is not healing."""
    ensure_health(character)
    amount = float(amount)
    if not math.isfinite(amount):
        raise ValueError("Health change must be finite")
    before = character.health
    if before > 0:
        character.health = max(0.0, min(float(health_max(character)), before + amount))
    return character.health - before


def damage_health(character, amount):
    if amount < 0:
        raise ValueError("Damage must be nonnegative")
    return -change_health(character, -amount)


def heal_health(character, amount):
    if amount < 0:
        raise ValueError("Healing must be nonnegative")
    return change_health(character, amount)


def health_tooltip(character):
    ensure_health(character)
    return "生命值：{:g} / {:g}\n上限＝正式体质×5；夜间小休恢复上限的2.5%。\n生命值归零即死亡。".format(character.health, health_max(character))


def energy_max(character):
    con_expectation = sum(die.expectation() for die in character.dice_pool if die.attribute == "con")
    cap = int(math.floor(1.5 * con_expectation))
    if getattr(character, "good_routine", False):
        cap = int(math.floor(cap * 1.25))
    cap += int(getattr(character, "next_day_energy_cap_bonus", 0))
    cap -= int(getattr(character, "fatigue_layers", 0))
    return max(0, cap)


def mood_state(character):
    if character.disease_state == DISEASE_MANIA:
        return DISEASE_MANIA
    if character.disease_state == DISEASE_DEPRESSION:
        return DISEASE_DEPRESSION
    if character.mood > 60:
        return MOOD_HIGH
    if character.mood < -60:
        return MOOD_LOW
    return MOOD_STABLE


def mood_label(state):
    return MOOD_LABELS.get(state, str(state))


def disease_label(state):
    return DISEASE_LABELS.get(state, str(state))


def enchantment_label(enchantment):
    return ENCHANTMENT_LABELS.get(enchantment, str(enchantment))


def format_die_faces(faces):
    return "/".join(str(face) for face in faces)


def attribute_summary(character, attribute):
    """Return one UI-ready attribute row without embedding formulas in screens."""
    bonus = sum(int(item.get("value", 0)) if isinstance(item, dict) else int(item) for item in character.attribute_bonuses.get(attribute, []))
    return {
        "id": attribute,
        "label": ATTRIBUTE_LABELS.get(attribute, attribute),
        "formal": int(character.formal_attributes.get(attribute, 0)),
        "value": int(character.attribute_values.get(attribute, 0)),
        "bonus": bonus,
        "status_modifier": sleep_attribute_modifier(character, attribute),
        "current": current_attribute(character, attribute),
        "effective": effective_attribute(character, attribute),
    }


def _status_row(status_id, label, value_text, tooltip, attribute=None, category=None):
    return {
        "id": status_id,
        "label": label,
        "value_text": value_text,
        "tooltip": tooltip,
        "attribute": attribute,
        "category": category,
    }



def second_stage_status_summary(character):
    """Return second-stage growth/degradation rows for status panels."""
    ensure_second_stage_state(character)
    rows = []
    for attribute in ATTRIBUTES:
        label = ATTRIBUTE_LABELS.get(attribute, attribute)
        dice_progress = int(character.dice_growth_progress.get(attribute, 0))
        if dice_progress:
            rows.append(_status_row(
                "dice_growth_{}".format(attribute),
                "{}骰子成长进度".format(label),
                "{}/6".format(dice_progress),
                "骰子成长进度：累计 6 点后，在小休结算为 1 次骰子成长奖励。",
                attribute,
            ))
        reward_pending = int(character.growth_reward_pending.get(attribute, 0))
        if reward_pending:
            rows.append(_status_row(
                "growth_reward_pending_{}".format(attribute),
                "{}骰子成长奖励".format(label),
                "x{}".format(reward_pending),
                "待选择的骰子成长奖励；后续会进入成长奖励抽卡流程。",
                attribute,
            ))
        degradation = int(character.degradation_progress.get(attribute, 0))
        if degradation:
            rows.append(_status_row(
                "degradation_{}".format(attribute),
                "{}退化进度".format(label),
                "{}/6".format(degradation),
                "退化进度：累计 6 点后产生 1 次降级惩罚。",
                attribute,
            ))
        penalty_pending = int(character.degradation_penalty_pending.get(attribute, 0))
        if penalty_pending:
            rows.append(_status_row(
                "degradation_penalty_pending_{}".format(attribute),
                "{}降级惩罚".format(label),
                "x{}".format(penalty_pending),
                "待选择的骰子降级惩罚；后续会进入惩罚抽卡流程。",
                attribute,
            ))
    return rows


def status_summary(character):
    """Return compact status rows shown in the test HUD and character panel."""
    rows = sleep_status_summary(character)
    rows.extend(vnext_status_summary(character))
    for attribute in ATTRIBUTES:
        label = ATTRIBUTE_LABELS.get(attribute, attribute)
        value = int(character.attribute_values.get(attribute, 0))
        if value:
            step = 1 if value > 0 else -1
            for layer in range(abs(value)):
                rows.append(_status_row(
                    "attr_value_{}_{}".format(attribute, layer + 1),
                    "{}加值{}".format(label, layer + 1),
                    "{:+d}".format(step),
                    "属性加值：中期属性变化，每层在状态栏中单独显示，大休结算时也会逐层转化。",
                    attribute,
                ))
        for item in character.attribute_bonuses.get(attribute, []):
            amount = int(item.get("value", 0)) if isinstance(item, dict) else int(item)
            source = item.get("source", "unknown") if isinstance(item, dict) else "unknown"
            if amount:
                rows.append(_status_row(
                    "attr_bonus_{}_{}".format(attribute, source),
                    "{}加成".format(label),
                    "{:+d}".format(amount),
                    "属性加成：临时或来源限定的属性层，会参与当前属性与有效属性计算。来源：{}。".format(source),
                    attribute,
                ))
    progress_map = getattr(character, "test_growth_progress", {})
    for attribute in TEST_TRAINING_ATTRIBUTES:
        label = ATTRIBUTE_LABELS.get(attribute, attribute)
        progress = int(progress_map.get(attribute, 0))
        rows.append(_status_row(
            "test_growth_{}".format(attribute),
            "{}训练进度".format(label),
            "{}/6".format(progress),
            "{}训练（测试）：大失败+0，失败+1，普通成功+2，困难成功+3，大成功+6；达到6后在休息（测试）结算为属性加成。".format(label),
            attribute,
        ))
    fatigue_map = getattr(character, "training_fatigue", {})
    for schedule_id, attribute in TEST_TRAINING_SCHEDULE_ATTRIBUTES.items():
        layers = int(fatigue_map.get(schedule_id, 0))
        if layers:
            label = TEST_TRAINING_SCHEDULE_LABELS.get(schedule_id, schedule_id)
            rows.append(_status_row(
                "training_fatigue_{}".format(schedule_id),
                "训练疲劳：{}".format(label),
                "x{}".format(layers),
                "训练疲劳：每层使下一次相同日程目标提高 1d4，并使可发生大失败时的大失败点数范围 +1；休息减少一层，睡觉清空。与熬夜疲劳、困意分开计算。",
                attribute,
                "schedule",
            ))
    rows.extend(second_stage_status_summary(character))
    return rows
def character_summary(character):
    """Collect the current character status for Ren'Py panels and debug screens."""
    state = mood_state(character)
    disease = getattr(character, "disease_state", DISEASE_NONE)
    return {
        "mood": {
            "value": int(getattr(character, "mood", 0)),
            "state": state,
            "label": mood_label(state),
        },
        "disease": {
            "state": disease,
            "label": disease_label(disease),
            "turns": int(getattr(character, "disease_turns", 0)),
            "man": int(getattr(character, "man", 0)),
            "dep": int(getattr(character, "dep", 0)),
        },
        "energy": {
            "current": int(getattr(character, "energy", 0)),
            "maximum": energy_max(character),
        },
        "attributes": {attribute: attribute_summary(character, attribute) for attribute in ATTRIBUTES},
        "statuses": status_summary(character),
    }


def dice_summary(die):
    """Return one die row for UI lists without exposing object internals."""
    return {
        "id": die.id,
        "attribute": die.attribute,
        "label": ATTRIBUTE_LABELS.get(die.attribute, die.attribute),
        "faces": list(die.faces),
        "faces_text": format_die_faces(die.faces),
        "minimum": die.minimum(),
        "maximum": die.maximum(),
        "expectation": die.expectation(),
        "expectation_text": "{:.1f}".format(die.expectation()),
        "enchantment": die.enchantment,
        "enchantment_label": enchantment_label(die.enchantment),
        "temporary": bool(getattr(die, "temporary", False)),
        "sealed": die.is_sealed(),
    }


def dice_pool_summary(character):
    return [dice_summary(die) for die in character.dice_pool]


def mood_tooltip(character):
    summary = character_summary(character)
    mood = summary["mood"]
    disease = summary["disease"]
    return "Mood：{value}（{label}）；病程：{disease}".format(
        value=mood["value"],
        label=mood["label"],
        disease=disease["label"],
    )


def energy_tooltip(character):
    energy = character_summary(character)["energy"]
    return "精力：{current} / {maximum}".format(**energy)


def test_strength_training_requirement(character):
    """Target for the test strength schedule, based on formal STR."""
    return test_training_requirement(character, "str")


def training_requirement_from_attribute_value(attribute_value):
    """Curved training target: floor(0.055 * x^2 + 0.355 * x + 3.545)."""
    x = int(attribute_value)
    return int(math.floor(0.055 * x * x + 0.355 * x + 3.545))


def test_training_requirement(character, attribute):
    """Target for a test training schedule, based on the formal attribute."""
    return training_requirement_from_attribute_value(character.formal_attributes.get(attribute, 0))


def test_training_schedule_attribute(schedule_id):
    return TEST_TRAINING_SCHEDULE_ATTRIBUTES.get(schedule_id)


def training_fatigue_layers(character, schedule_id):
    ensure_second_stage_state(character)
    return int(character.training_fatigue.get(schedule_id, 0))


def roll_training_fatigue_requirement_penalty(layers, rng=None):
    """Roll the extra target value from fatigue: each layer adds 1d4."""
    rng = _rng(rng)
    return sum(rng.randint(1, 4) for _ in range(max(0, int(layers))))


def training_fatigue_requirement_penalty(character, schedule_id, rng=None):
    return roll_training_fatigue_requirement_penalty(training_fatigue_layers(character, schedule_id), rng)


def training_fatigue_big_failure_slack(character, schedule_id):
    """Each fatigue layer expands the possible big-failure dice-total range by 1."""
    return training_fatigue_layers(character, schedule_id)


def test_training_requirement_for_schedule(character, schedule_id, rng=None):
    attribute = test_training_schedule_attribute(schedule_id)
    if attribute is None:
        raise ValueError("Unknown test training schedule: {!r}".format(schedule_id))
    return test_training_requirement(character, attribute) + training_fatigue_requirement_penalty(character, schedule_id, rng)


def add_training_fatigue(character, schedule_id, amount=1):
    ensure_second_stage_state(character)
    if schedule_id not in TEST_TRAINING_SCHEDULE_ATTRIBUTES:
        return 0
    character.training_fatigue[schedule_id] = max(0, int(character.training_fatigue.get(schedule_id, 0)) + int(amount))
    return character.training_fatigue[schedule_id]


def reduce_training_fatigue_on_rest(character):
    """Daytime rest reduces every training fatigue stack by one layer."""
    ensure_second_stage_state(character)
    events = []
    for schedule_id in TEST_TRAINING_SCHEDULE_ATTRIBUTES:
        before = int(character.training_fatigue.get(schedule_id, 0))
        if before > 0:
            after = max(0, before - 1)
            character.training_fatigue[schedule_id] = after
            events.append("fatigue_reduced:{}:{}".format(schedule_id, after))
    return events


def clear_training_fatigue_on_sleep(character):
    """Sleep clears all accumulated training fatigue stacks."""
    ensure_second_stage_state(character)
    events = []
    for schedule_id in TEST_TRAINING_SCHEDULE_ATTRIBUTES:
        if int(character.training_fatigue.get(schedule_id, 0)) > 0:
            character.training_fatigue[schedule_id] = 0
            events.append("fatigue_cleared:{}".format(schedule_id))
    return events


def test_strength_training_progress_delta(rank):
    return test_training_progress_delta(rank)


def test_training_progress_delta(rank):
    if rank == RESULT_BIG_FAILURE:
        return 0
    if rank == RESULT_FAILURE:
        return 1
    if rank == RESULT_SUCCESS:
        return 2
    if rank == RESULT_HARD_SUCCESS:
        return 3
    if rank == RESULT_BIG_SUCCESS:
        return 6
    return 0


def normalize_strength_training_str(str_value):
    """Clamp the STR value used by strength-training growth to the design table."""
    return int(clamp(int(str_value), 1, 20))


def strength_training_bonus_slot_count(str_value):
    """Return the maximum STR bonus layers available for the current STR segment."""
    str_value = normalize_strength_training_str(str_value)
    if str_value <= 6:
        return 3
    if str_value <= 12:
        return 2
    return 1


def _strength_training_result_level(result_level):
    if hasattr(result_level, "rank"):
        return getattr(result_level, "rank")
    if hasattr(result_level, "result_level"):
        return getattr(result_level, "result_level")
    return result_level


def _bonus_probability(value):
    return float(clamp(float(value), 0.0, 1.0))


def build_strength_training_bonus_rolls(str_value, result_level):
    """Build per-layer STR bonus probabilities for the strength-training schedule."""
    str_value = normalize_strength_training_str(str_value)
    result_level = _strength_training_result_level(result_level)
    if result_level in (RESULT_BIG_FAILURE, RESULT_FAILURE):
        return []
    if result_level in (RESULT_HARD_SUCCESS, RESULT_BIG_SUCCESS, "critical_success"):
        return [1.0 for _ in range(strength_training_bonus_slot_count(str_value))]
    if result_level != RESULT_SUCCESS:
        return []

    total = STRENGTH_TRAINING_STR_BONUS_TOTAL_CHANCE[str_value]
    if str_value <= 6:
        rolls = [1.0, (total - 1.0) / 2.0, (total - 1.0) / 2.0]
    elif str_value <= 12:
        rolls = [1.0, total - 1.0]
    else:
        rolls = [total]
    return [chance for chance in [_bonus_probability(item) for item in rolls] if chance > 0.0]


def calculate_strength_training_bonus_plan(str_value, result_level):
    """Return debug-friendly data for the strength-training STR bonus rule."""
    str_value = normalize_strength_training_str(str_value)
    return {
        "str_value": str_value,
        "result_level": _strength_training_result_level(result_level),
        "total_chance": STRENGTH_TRAINING_STR_BONUS_TOTAL_CHANCE[str_value],
        "roll_plan": build_strength_training_bonus_rolls(str_value, result_level),
        "max_layers": strength_training_bonus_slot_count(str_value),
    }


def strength_training_existing_bonus_decay(character):
    """Existing STR bonus layers reduce strength-training bonus chances multiplicatively."""
    return (2.0 / 3.0) ** _count_attribute_bonuses(character, "str")


def apply_strength_training_str_bonus(character, check_result, rng=None):
    """Apply only the STR attribute-bonus part of the strength-training result."""
    result_level = _strength_training_result_level(check_result)
    str_value = normalize_strength_training_str(current_attribute(character, "str"))
    plan = calculate_strength_training_bonus_plan(str_value, result_level)
    plan["base_roll_plan"] = list(plan["roll_plan"])
    plan["existing_bonus_layers"] = _count_attribute_bonuses(character, "str")
    plan["decay_multiplier"] = strength_training_existing_bonus_decay(character) if result_level == RESULT_SUCCESS else 1.0
    rolls = []
    success_count = 0
    adjusted_plan = []
    for chance in plan["base_roll_plan"]:
        if result_level == RESULT_SUCCESS:
            decay = strength_training_existing_bonus_decay(character)
            chance = _bonus_probability(chance * decay)
        adjusted_plan.append(round(chance, 4))
        success = roll_probability(chance, rng)
        rolls.append({"chance": round(chance, 4), "success": success})
        if success:
            success_count += 1
            add_attribute_bonus(character, "str", 1)
            character.attribute_bonuses["str"][-1]["source"] = "test_strength_training"
    plan["roll_plan"] = adjusted_plan
    plan["rolls"] = rolls
    plan["success_count"] = int(success_count)
    return plan


def exercise_existing_bonus_decay(character):
    """Jogging bonus chances are reduced by CON/DEX/STR bonus layers at 1/6 each."""
    layers = sum(_count_attribute_bonuses(character, attr) for attr in JOGGING_BONUS_ATTRIBUTES)
    return (5.0 / 6.0) ** layers


def _grant_attribute_bonus_with_source(character, attribute, source):
    add_attribute_bonus(character, attribute, 1)
    character.attribute_bonuses[attribute][-1]["source"] = source


def _jogging_bonus_attributes_for_opportunity(rng=None):
    rng = _rng(rng)
    granted = []
    if roll_probability(0.70, rng):
        granted.append("con")
    if roll_probability(0.30, rng):
        granted.append("dex")
    if roll_probability(0.30, rng):
        granted.append("str")
    if not granted:
        granted.append(_weighted_choice(JOGGING_BONUS_WEIGHTS, rng))
    return granted


def apply_exercise_jogging_bonus(character, check_result, rng=None):
    """Apply the jogging multi-attribute bonus rule after a successful check."""
    rng = _rng(rng)
    result_level = _strength_training_result_level(check_result)
    con_value = normalize_strength_training_str(current_attribute(character, "con"))
    plan = calculate_strength_training_bonus_plan(con_value, result_level)
    plan["base_roll_plan"] = list(plan["roll_plan"])
    plan["affected_bonus_layers"] = sum(_count_attribute_bonuses(character, attr) for attr in JOGGING_BONUS_ATTRIBUTES)
    rolls = []
    success_count = 0
    adjusted_plan = []
    granted_attributes = []
    for chance in plan["base_roll_plan"]:
        if result_level == RESULT_SUCCESS:
            chance = _bonus_probability(chance * exercise_existing_bonus_decay(character))
        adjusted_plan.append(round(chance, 4))
        success = roll_probability(chance, rng)
        grant = []
        if success:
            success_count += 1
            grant = _jogging_bonus_attributes_for_opportunity(rng)
            for attribute in grant:
                _grant_attribute_bonus_with_source(character, attribute, "test_jogging")
                granted_attributes.append(attribute)
        rolls.append({"chance": round(chance, 4), "success": success, "granted": list(grant)})
    plan["roll_plan"] = adjusted_plan
    plan["rolls"] = rolls
    plan["success_count"] = int(success_count)
    plan["granted_attributes"] = granted_attributes
    return plan


def apply_test_strength_training_result(character, result, rng=None):
    """Apply strength-training STR growth and accumulate test reward progress."""
    return apply_test_training_result(character, "str", result, rng)


def apply_test_training_result(character, attribute, result, rng=None):
    """Apply a test training result and accumulate dice reward progress."""
    ensure_second_stage_state(character)
    if result is None or not getattr(result, "available", False):
        return {"progress_delta": 0, "bonus": None}
    bonus = apply_strength_training_str_bonus(character, result, rng) if attribute == "str" else None
    delta = test_training_progress_delta(result.rank)
    character.test_growth_progress[attribute] = min(6, int(character.test_growth_progress.get(attribute, 0)) + delta)
    return {"progress_delta": delta, "bonus": bonus}


def apply_test_training_schedule_result(character, schedule_id, result, rng=None):
    """Apply one completed test training schedule, including its fatigue stack."""
    attribute = test_training_schedule_attribute(schedule_id)
    if attribute is None:
        raise ValueError("Unknown test training schedule: {!r}".format(schedule_id))
    applied = apply_test_training_result(character, attribute, result, rng)
    if result is not None and getattr(result, "available", False):
        applied["fatigue_layers"] = add_training_fatigue(character, schedule_id, 1)
    else:
        applied["fatigue_layers"] = training_fatigue_layers(character, schedule_id)
    return applied


def apply_test_exercise_schedule_result(character, schedule_id, result, rng=None):
    """Apply one completed test exercise schedule, including fatigue."""
    if schedule_id != "test_jogging":
        raise ValueError("Unknown test exercise schedule: {!r}".format(schedule_id))
    if result is None or not getattr(result, "available", False):
        bonus = None
    else:
        bonus = apply_exercise_jogging_bonus(character, result, rng) if getattr(result, "success", False) else None
        add_training_fatigue(character, schedule_id, 1)
    return {"bonus": bonus, "fatigue_layers": training_fatigue_layers(character, schedule_id)}


def resolve_test_rest(character):
    """Resolve test-only small-rest rewards without creating formal schedules."""
    ensure_second_stage_state(character)
    events = []
    for attribute in TEST_TRAINING_ATTRIBUTES:
        progress = int(character.test_growth_progress.get(attribute, 0))
        if progress >= 6:
            character.test_growth_progress[attribute] = 0
            add_attribute_bonus(character, attribute, 1)
            source = "test_strength_training" if attribute == "str" else "test_{}_training".format(attribute)
            character.attribute_bonuses[attribute][-1]["source"] = source
            events.append("test_training_bonus:{}".format(attribute))
            if attribute == "str":
                events.append("test_strength_bonus:str")
    return events


def resolve_test_small_rest(character):
    """Resolve the test rest schedule and expose second-stage small-rest events."""
    events = ["small_rest"]
    events.extend(resolve_test_rest(character))
    events.extend(process_dice_growth_progress_on_small_rest(character))
    return events


def resolve_test_day_rest(character, rng=None):
    """Resolve a daytime rest schedule by rolling one random usable CON die."""
    dice = usable_dice(character, "con")
    if not dice:
        return {"available": False, "reason": "no_usable_con_die", "events": ["rest_failed:no_usable_con_die"]}
    die = _rng(rng).choice(dice)
    roll = roll_die(die, rng)
    before = int(character.energy)
    rolled_value = int(roll["value"])
    character.energy = min(energy_max(character), before + rolled_value)
    restored = int(character.energy) - before
    events = ["day_rest", "energy_restored:{}".format(restored)]
    if reduce_drowsiness(character, 1):
        events.append("drowsiness_reduced:1")
    events.extend(reduce_training_fatigue_on_rest(character))
    return {
        "available": True,
        "attribute": "con",
        "die_id": die.id,
        "roll": roll,
        "rolled_value": rolled_value,
        "restored": restored,
        "energy_before": before,
        "energy_after": int(character.energy),
        "events": events,
    }


def resolve_test_sleep(character, rng=None):
    """Test UI and ordinary sleep share one settlement entry point."""
    if character.current_time_slot is None:
        start_turn(character, "sleep_decision")
    return begin_sleep(character, rng)


def _reset_disease_values(character):
    character.disease_state = DISEASE_NONE
    character.man = 0
    character.dep = 0
    character.disease_turns = 0


def test_console_adjust_mood(character, delta):
    character.mood = int(clamp(character.mood + int(delta), -200, 200))
    return character.mood


def test_console_set_mood_state(character, state):
    if state == "high":
        _reset_disease_values(character)
        character.mood = 80
    elif state == "low":
        _reset_disease_values(character)
        character.mood = -80
    elif state == "stable":
        _reset_disease_values(character)
        character.mood = 0
    elif state == "depression":
        character.disease_state = DISEASE_DEPRESSION
        character.mood = -80
        character.dep = 80
        character.man = 0
        character.disease_turns = 0
    elif state == "mania":
        character.disease_state = DISEASE_MANIA
        character.mood = 80
        character.man = 80
        character.dep = 0
        character.disease_turns = 0
    else:
        raise ValueError("Unknown test console mood state: {!r}".format(state))
    return character.mood


def test_console_adjust_formal_attribute(character, attribute, delta):
    ensure_second_stage_state(character)
    before = int(character.formal_attributes.get(attribute, 0))
    character.formal_attributes[attribute] = max(0, int(character.formal_attributes.get(attribute, 0)) + int(delta))
    if attribute == "con":
        change_health(character, (character.formal_attributes[attribute] - before) * 5)
    return character.formal_attributes[attribute]


def test_console_adjust_attribute_value(character, attribute, delta):
    ensure_second_stage_state(character)
    character.attribute_values[attribute] = int(character.attribute_values.get(attribute, 0)) + int(delta)
    return character.attribute_values[attribute]


def _console_bonus_entry(character, attribute):
    ensure_second_stage_state(character)
    for item in character.attribute_bonuses[attribute]:
        if isinstance(item, dict) and item.get("source") == "console":
            return item
    item = RevertableDict(value=0, source="console")
    character.attribute_bonuses[attribute].append(item)
    return item


def test_console_adjust_attribute_bonus(character, attribute, delta):
    ensure_second_stage_state(character)
    item = _console_bonus_entry(character, attribute)
    item["value"] = int(item.get("value", 0)) + int(delta)
    if item["value"] == 0:
        character.attribute_bonuses[attribute] = RevertableList(
            bonus for bonus in character.attribute_bonuses[attribute]
            if not (isinstance(bonus, dict) and bonus.get("source") == "console")
        )
    return item["value"]


def mood_check_profile(state):
    if state == MOOD_LOW:
        return {"attribute_factor": 0.75, "dice_multiplier": 0.75, "requirement_factor": 1.0, "max_dice_delta": 0, "third_die_discount": 0}
    if state == DISEASE_DEPRESSION:
        return {"attribute_factor": 0.9, "dice_multiplier": 0.6, "requirement_factor": 1.0, "max_dice_delta": -1, "third_die_discount": 0}
    if state == MOOD_HIGH:
        return {"attribute_factor": 0.5, "dice_multiplier": 1.0, "requirement_factor": 1.15, "max_dice_delta": 0, "third_die_discount": 1}
    if state == DISEASE_MANIA:
        return {"attribute_factor": 0.5, "dice_multiplier": 1.0, "requirement_factor": 1.25, "max_dice_delta": 0, "third_die_discount": 1}
    return {"attribute_factor": 0.5, "dice_multiplier": 1.0, "requirement_factor": 1.0, "max_dice_delta": 0, "third_die_discount": 0}


def adjusted_requirement(base_requirement, profile):
    return int(math.ceil(base_requirement * profile["requirement_factor"]))


def attribute_modifier(character, attribute, profile):
    return int(math.floor(effective_attribute(character, attribute) * profile["attribute_factor"]))


def max_dice_for_check(spec, profile):
    return max(1, int(spec.max_dice) + int(profile["max_dice_delta"]))


def usable_dice(character, attribute):
    return [die for die in character.dice_for(attribute) if not die.is_sealed()]


def usable_dice_for_attributes(character, attributes):
    allowed = set(attributes or ATTRIBUTES)
    return [die for die in character.dice_pool if die.attribute in allowed and not die.is_sealed()]


def shackled_dice(dice):
    return [die for die in dice if die.enchantment == ENCHANT_SHACKLE]


def absorb_shackled_dice(dice, max_count, rng=None):
    rng = _rng(rng)
    shackled = shackled_dice(dice)
    if len(shackled) <= max_count:
        return list(shackled)
    return rng.sample(shackled, max_count)


def selected_dice(character, spec, max_count, rng=None):
    allowed_attributes = tuple(getattr(spec, "allowed_dice_attributes", (spec.attribute,)))
    legal = usable_dice_for_attributes(character, allowed_attributes)
    if not legal:
        return []
    forced = absorb_shackled_dice(legal, max_count, rng)
    selected = list(forced)
    forced_ids = set(die.id for die in forced)
    for dice_id in spec.dice_ids:
        if len(selected) >= max_count:
            break
        die = character.find_die(dice_id)
        if die and die.attribute in allowed_attributes and not die.is_sealed() and die.id not in forced_ids:
            selected.append(die)
            forced_ids.add(die.id)
    if not selected and legal:
        selected.append(legal[0])
    return selected


def missing_required_dice_attribute(dice, required_attributes):
    selected_attributes = set(die.attribute for die in dice)
    for attribute in required_attributes or ():
        if attribute not in selected_attributes:
            return attribute
    return None


def base_energy_cost(dice_count, action_type, third_die_discount=0):
    if dice_count <= 0:
        return 0
    if action_type == ACTION_INSTANT:
        costs = {1: 0, 2: 1, 3: 3}
    else:
        costs = {1: 1, 2: 2, 3: 4}
    cost = costs.get(dice_count, costs[3] + (dice_count - 3) * 2)
    if dice_count >= 3:
        cost -= int(third_die_discount)
    return max(0, cost)


def enchantment_energy_cost(dice):
    cost = 0
    for die in dice:
        if die.enchantment == ENCHANT_LIGHT:
            cost -= 1
        elif die.enchantment == ENCHANT_HEAVY:
            cost += 1
    return cost


def total_energy_cost(dice, spec, profile):
    # Waking is entirely free, including additional dice and heavy enchantments.
    if spec.action_type == ACTION_WAKE:
        return 0
    cost = base_energy_cost(len(dice), spec.action_type, profile["third_die_discount"])
    cost += enchantment_energy_cost(dice)
    if spec.is_late_night and spec.action_type in (ACTION_SCHEDULE, ACTION_FORCED_SCHEDULE) and cost > 0:
        cost += 1
    return max(0, cost)


def roll_single_face(die, rng=None):
    rng = _rng(rng)
    faces = list(die.faces)
    if hasattr(rng, "choice"):
        return rng.choice(faces)
    return faces[min(len(faces) - 1, int(rng.random() * len(faces)))]


def roll_die(die, rng=None, force_mode=None):
    rng = _rng(rng)
    bonus = die.enchantment == ENCHANT_SWIFT
    penalty = die.enchantment == ENCHANT_SLUGGISH
    if force_mode == "bonus":
        bonus = True
    elif force_mode == "penalty":
        penalty = True
    if bonus and penalty:
        bonus = False
        penalty = False
    if bonus or penalty:
        rolls = [roll_single_face(die, rng), roll_single_face(die, rng)]
        value = max(rolls) if bonus else min(rolls)
        return {"die_id": die.id, "attribute": die.attribute, "rolls": rolls, "value": value, "mode": "bonus" if bonus else "penalty", "enchantment": die.enchantment}
    value = roll_single_face(die, rng)
    return {"die_id": die.id, "attribute": die.attribute, "rolls": [value], "value": value, "mode": "normal", "enchantment": die.enchantment}


def roll_dice(dice, rng=None, force_mode=None):
    # Until multi-source placement is configured, one net source affects the first invested die.
    return [roll_die(die, rng, force_mode if index == 0 else None) for index, die in enumerate(dice)]


def dice_min_total(dice):
    return sum(die.minimum() for die in dice)


def dice_max_total(dice):
    return sum(die.maximum() for die in dice)


def result_rank(total, requirement, dice_total, dice, big_failure_slack=0):
    if total >= requirement * 2:
        if len(dice) >= 2 and dice_total == dice_max_total(dice):
            return RESULT_BIG_SUCCESS
        return RESULT_HARD_SUCCESS
    if total >= requirement:
        return RESULT_SUCCESS
    if len(dice) >= 2 and dice_total <= dice_min_total(dice) + int(big_failure_slack):
        return RESULT_BIG_FAILURE
    return RESULT_FAILURE


def apply_mania_big_failure(rank, total, requirement, state):
    if state == DISEASE_MANIA and total < requirement / 3.0:
        return RESULT_BIG_FAILURE
    return rank


def unavailable_result(spec, reason):
    return CheckResult(available=False, reason=reason, attribute=spec.attribute, requirement=spec.requirement, base_requirement=spec.requirement)


def forced_energy_failure(character, spec, dice, cost, state, profile):
    requirement = adjusted_requirement(spec.requirement, profile)
    modifier = attribute_modifier(character, spec.attribute, profile)
    return CheckResult(
        available=True,
        reason="forced_energy_shortage",
        attribute=spec.attribute,
        requirement=requirement,
        base_requirement=spec.requirement,
        mood_state=state,
        attribute_modifier=modifier,
        dice_multiplier=profile["dice_multiplier"],
        extra_modifier=spec.extra_modifier + drowsiness_check_modifier(character, spec.attribute),
        total=modifier + spec.extra_modifier + drowsiness_check_modifier(character, spec.attribute),
        rank=RESULT_FAILURE,
        success=False,
        energy_cost=cost,
        dice_ids=[die.id for die in dice],
    )


def perform_check(character, spec, rng=None):
    ensure_second_stage_state(character)
    rng = _rng(rng)
    state = mood_state(character)
    profile = mood_check_profile(state)
    dice = selected_dice(character, spec, max_dice_for_check(spec, profile), rng)
    if not dice:
        return unavailable_result(spec, "no_usable_dice")
    missing_attribute = missing_required_dice_attribute(dice, getattr(spec, "required_dice_attributes", ()))
    if missing_attribute:
        return unavailable_result(spec, "missing_required_die:{}".format(missing_attribute))
    weather = weather_check_effects(character, spec)
    if not weather["available"]:
        return unavailable_result(spec, weather.get("reason", "weather_blocked"))
    cost = total_energy_cost(dice, spec, profile)
    if cost > 0:
        cost = max(1, cost - time_habit_energy_discount(character, spec))
    if cost > character.energy and spec.forced:
        return forced_energy_failure(character, spec, dice, cost, state, profile)
    if cost > character.energy:
        return unavailable_result(spec, "energy_shortage")
    advantage_count = int(weather["advantage_count"])
    disadvantage_count = int(weather["disadvantage_count"])
    if check_generates_emotion(spec):
        advantage_count += 1 if emotion_layers(character, EMOTION_JOY) else 0
        disadvantage_count += 1 if emotion_layers(character, EMOTION_SADNESS) else 0
    advantage_count += 1 if character.long_emotions.get("confidence") else 0
    disadvantage_count += 1 if character.long_emotions.get("doubt") else 0
    disadvantage_count += len(character.environment_diseases)
    net_advantage = advantage_count - disadvantage_count
    rolls = roll_dice(dice, rng, "bonus" if net_advantage > 0 else "penalty" if net_advantage < 0 else None)
    dice_total = sum(item["value"] for item in rolls)
    requirement = adjusted_requirement(spec.requirement, profile)
    modifier = attribute_modifier(character, spec.attribute, profile)
    extra = spec.extra_modifier + drowsiness_check_modifier(character, spec.attribute)
    total = modifier + dice_total * profile["dice_multiplier"] + extra
    final_multiplier = float(weather["final_multiplier"])
    final_multiplier *= injury_check_multiplier(character, spec)
    final_multiplier *= alcohol_check_multiplier(character, spec)
    participating = check_generates_emotion(spec)
    if participating and emotion_layers(character, EMOTION_CALM):
        final_multiplier *= 1.15
    if participating and emotion_layers(character, EMOTION_ANXIETY):
        final_multiplier *= .85
    if participating and len(dice) >= 2 and emotion_layers(character, EMOTION_EXCITEMENT):
        final_multiplier *= 1.25
    if participating and len(dice) >= 2 and emotion_layers(character, EMOTION_DISTRACTION):
        final_multiplier *= .75
    if character.palpitations:
        final_multiplier *= .75
    total *= final_multiplier
    rank = result_rank(total, requirement, dice_total, dice, getattr(spec, "big_failure_slack", 0))
    rank = apply_mania_big_failure(rank, total, requirement, state)
    character.energy = max(0, character.energy - cost)
    result = CheckResult(
        available=True,
        attribute=spec.attribute,
        requirement=requirement,
        base_requirement=spec.requirement,
        mood_state=state,
        attribute_modifier=modifier,
        dice_multiplier=profile["dice_multiplier"],
        extra_modifier=extra,
        dice_total=dice_total,
        total=total,
        rank=rank,
        success=rank in (RESULT_SUCCESS, RESULT_HARD_SUCCESS, RESULT_BIG_SUCCESS),
        energy_cost=cost,
        dice_ids=[die.id for die in dice],
        dice_results=rolls,
        dice_count=len(dice),
    )
    result.advantage_count = advantage_count
    result.disadvantage_count = disadvantage_count
    result.final_multiplier = final_multiplier
    result.spec = spec
    result.weather_mood_delta_base = int(weather["mood_delta_base"])
    if participating:
        if emotion_layers(character, EMOTION_JOY):
            remove_emotion(character, EMOTION_JOY, 1)
        if emotion_layers(character, EMOTION_CALM):
            remove_emotion(character, EMOTION_CALM, 1)
        if emotion_layers(character, EMOTION_SADNESS) and result.success:
            remove_emotion(character, EMOTION_SADNESS)
        if emotion_layers(character, EMOTION_ANXIETY) and result.success:
            remove_emotion(character, EMOTION_ANXIETY)
        if len(dice) >= 2 and emotion_layers(character, EMOTION_EXCITEMENT):
            remove_emotion(character, EMOTION_EXCITEMENT, 1)
        if len(dice) >= 2 and emotion_layers(character, EMOTION_DISTRACTION) and result.success:
            remove_emotion(character, EMOTION_DISTRACTION, 1)
    return result


def pow_effective(character):
    return effective_attribute(character, "pow")


def pow_k(character):
    d = pow_effective(character) - 6
    return 1 + 2.92e-2 * d - 6.94e-4 * (d ** 2)


def mood_delta_ratio(current_mood, base_delta, k_pow):
    if base_delta == 0:
        return 1.0
    positive = base_delta > 0
    mood = current_mood
    if positive:
        if mood < 30:
            return k_pow
        if mood < 45:
            return 1 + (k_pow - 1) * (45 - mood) / 15.0
        if mood < 60:
            return 1 - (1 - 1 / k_pow) * (mood - 45) / 15.0
        return 1 / k_pow
    if mood < 30:
        return 1 / k_pow
    if mood < 45:
        return 1 - (1 - 1 / k_pow) * (45 - mood) / 15.0
    if mood < 60:
        return 1 + (k_pow - 1) * (mood - 45) / 15.0
    return k_pow


def adjusted_mood_delta(character, base_delta):
    if base_delta == 0:
        return 0
    raw = abs(base_delta * mood_delta_ratio(character.mood, base_delta, pow_k(character)))
    value = max(1, int(math.floor(raw)))
    return value if base_delta > 0 else -value


def disease_enter_base_probability(abs_mood):
    x = abs_mood
    if x <= 60:
        return 0.0
    if x <= 120:
        return 6.37e-6 * ((x - 60) ** 2)
    return 2.29e-2 + 7.65e-4 * (x - 120) + 5.87e-5 * ((x - 120) ** 2)


def disease_enter_probability(character):
    base = disease_enter_base_probability(abs(character.mood))
    return 1 - ((1 - base) ** (1 / pow_k(character)))


def stable_base_probability(abs_mood):
    x = abs_mood
    if x > 120:
        return 0.0
    if x > 80:
        return 7.30e-3 + 1.56e-2 * (((120 - x) / 40.0) ** 2)
    if x > 60:
        return 2.29e-2 + 7.13e-2 * (((80 - x) / 20.0) ** 2)
    if x > 40:
        return 9.43e-2 + 1.86e-1 * (((60 - x) / 20.0) ** 2)
    return 2.80e-1


def stable_probability(character):
    base = stable_base_probability(abs(character.mood))
    return 1 - ((1 - base) ** pow_k(character))


def switch_base_probability(turns):
    return 9.69e-3 * ((max(0, turns) / 210.0) ** 1.96)


def switch_probability(character):
    base = switch_base_probability(character.disease_turns)
    return 1 - ((1 - base) ** (1 / pow_k(character)))


def try_enter_disease(character, rng=None):
    rng = _rng(rng)
    if character.disease_state != DISEASE_NONE or abs(character.mood) <= 60:
        return None
    if rng.random() >= disease_enter_probability(character):
        return None
    if character.mood > 0:
        character.disease_state = DISEASE_MANIA
        character.man = abs(character.mood)
        character.dep = 0
        character.disease_turns = 0
        if getattr(character, "bipolar_ember", None) is not None:
            character.bipolar_ember = 180
        return "enter_mania"
    character.disease_state = DISEASE_DEPRESSION
    character.dep = abs(character.mood)
    character.man = 0
    character.disease_turns = 0
    if getattr(character, "bipolar_ember", None) is not None:
        character.bipolar_ember = 180
    elif hasattr(character, "ember"):
        character.ember = 180
    return "enter_depression"


def try_return_stable(character, rng=None):
    rng = _rng(rng)
    if character.disease_state == DISEASE_NONE:
        return None
    if rng.random() >= stable_probability(character):
        return None
    character.disease_state = DISEASE_NONE
    character.disease_turns = 0
    return "return_stable"


def try_switch_disease(character, rng=None):
    rng = _rng(rng)
    if character.disease_state == DISEASE_NONE:
        return None
    character.disease_turns += 1
    if rng.random() >= switch_probability(character):
        return None
    old_value = character.man if character.disease_state == DISEASE_MANIA else character.dep
    new_intensity = old_value * 0.6 + abs(character.mood)
    if character.disease_state == DISEASE_MANIA:
        character.disease_state = DISEASE_DEPRESSION
        character.mood = int(clamp(-new_intensity, -200, 200))
        character.dep = abs(character.mood)
        character.man = 0
        event = "switch_to_depression"
    else:
        character.disease_state = DISEASE_MANIA
        character.mood = int(clamp(new_intensity, -200, 200))
        character.man = abs(character.mood)
        character.dep = 0
        event = "switch_to_mania"
    character.disease_turns = 0
    return event


def end_action_round(character, mood_delta_base=0, rng=None, exact_mood_delta=False, check=None):
    events = []
    if check is not None and check.available:
        apply_big_failure_degradation(character, check)
        spec = getattr(check, "spec", None)
        if spec is not None:
            mood_delta_base += int(getattr(check, "weather_mood_delta_base", 0))
            events.extend(settle_check_emotions(character, spec, check, rng))
            if spec.outdoors:
                events.extend(process_environment_exposure(character, rng))
            events.extend(record_time_habit_action(character, spec.schedule_category))
    delta = int(mood_delta_base) if exact_mood_delta else adjusted_mood_delta(character, mood_delta_base)
    character.mood = int(clamp(character.mood + delta, -200, 200))
    if character.disease_state == DISEASE_NONE:
        event = try_enter_disease(character, rng)
        if event:
            events.append(event)
    else:
        event = try_return_stable(character, rng)
        if event:
            events.append(event)
        else:
            event = try_switch_disease(character, rng)
            if event:
                events.append(event)
    return {
        "mood_delta": delta,
        "mood": character.mood,
        "disease_state": character.disease_state,
        "events": events,
    }


def mock_schedule_specs():
    return [
        ScheduleSpec("mock_dex_check", "Mock DEX Check", CheckSpec("dex", 5, action_type=ACTION_SCHEDULE), mood_delta=2),
        ScheduleSpec("mock_pow_instant", "Mock POW Instant", CheckSpec("pow", 8, action_type=ACTION_INSTANT), mood_delta=-2),
    ]


# Second-stage backend helpers. These functions intentionally stay UI-agnostic
# and keep formal schedule/event pools as mock-only placeholders.

TIME_SLOTS = ("morning_1", "morning_2", "afternoon_1", "afternoon_2", "evening_1", "evening_2",
              "late_night_1", "late_night_2", "late_night_3")
MEAL_SLOTS = ("breakfast", "lunch", "dinner")
SLEEP_DECISIONS = ("sleep_decision", "night_break_1", "night_break_2")
TIME_SLOT_LABELS = dict(zip(TIME_SLOTS, ("上午1", "上午2", "下午1", "下午2", "晚上1", "晚上2",
                                      "深夜1", "深夜2", "深夜3")))
TIME_SLOT_LABELS.update(breakfast="早餐", lunch="午饭", dinner="晚饭", sleep_decision="就寝时间",
                        night_break_1="深夜1之后", night_break_2="深夜2之后",
                        forced_sleep="昏迷", wake_check="起床")
NEXT_TIME_SLOT = {
    "breakfast": "morning_1", "morning_1": "morning_2", "morning_2": "lunch",
    "lunch": "afternoon_1", "afternoon_1": "afternoon_2", "afternoon_2": "dinner",
    "dinner": "evening_1", "evening_1": "evening_2", "evening_2": "sleep_decision",
    "late_night_1": "night_break_1", "late_night_2": "night_break_2", "late_night_3": "forced_sleep",
}
STATUS_CATEGORIES = {"weather": "天气类", "mood": "心情类", "emotion": "情绪类",
                     "physiological": "生理类", "medication": "药物类",
                     "injury": "伤病类", "disease": "疾病类", "schedule": "日程类"}
WAKE_REQUIREMENT = 15  # POW 6, stable mood, both starting dice: 72.5%; no extra modifier.
SLEEP_QUALITY_POOR = "poor"
SLEEP_QUALITY_GOOD = "good"
SLEEP_QUALITY_EXCELLENT = "excellent"
SEASONS = ("spring", "summer", "autumn", "winter")
WEATHERS = (WEATHER_SUNNY, WEATHER_CLOUDY, WEATHER_LIGHT_RAIN, WEATHER_HEAVY_RAIN,
            WEATHER_STORM, WEATHER_THUNDERSTORM, WEATHER_FOG, WEATHER_LIGHT_SNOW, WEATHER_HEAVY_SNOW)
WEATHER_LABELS = {
    WEATHER_SUNNY: "晴天", WEATHER_CLOUDY: "多云", WEATHER_LIGHT_RAIN: "小雨",
    WEATHER_HEAVY_RAIN: "大雨", WEATHER_STORM: "暴雨", WEATHER_THUNDERSTORM: "雷雨",
    WEATHER_FOG: "雾天", WEATHER_LIGHT_SNOW: "小雪", WEATHER_HEAVY_SNOW: "大雪",
}
WEATHER_WEIGHTS = {
    "spring": (30, 30, 20, 10, 0, 5, 5, 0, 0),
    "summer": (35, 20, 10, 10, 5, 15, 5, 0, 0),
    "autumn": (35, 35, 10, 5, 0, 5, 10, 0, 0),
    "winter": (25, 40, 5, 3, 1, 1, 10, 10, 5),
}
SEASON_TEMPERATURE_OFFSETS = {"spring": 0, "summer": 15, "autumn": 0, "winter": -15}
WEATHER_TEMPERATURE_OFFSETS = {
    WEATHER_SUNNY: 25, WEATHER_CLOUDY: 15, WEATHER_LIGHT_RAIN: -15,
    WEATHER_HEAVY_RAIN: -25, WEATHER_STORM: -25, WEATHER_THUNDERSTORM: -25,
    WEATHER_FOG: 0, WEATHER_LIGHT_SNOW: -25, WEATHER_HEAVY_SNOW: -50,
}
PSYCHIATRIC_MEDICINES = ("lithium", "aripiprazole", "lamotrigine", "venlafaxine", "trazodone", "alprazolam")
MEDICINE_LABELS = {"lithium": "碳酸锂", "aripiprazole": "阿立哌唑", "lamotrigine": "拉莫三嗪",
                   "venlafaxine": "文拉法辛", "trazodone": "曲唑酮", "alprazolam": "阿普唑仑"}
BIPOLAR_MEDICINE_MULTIPLIERS = {
    "lithium": (0.85, 0.85),
    "aripiprazole": (0.75, 1.15),
    "lamotrigine": (1.15, 0.75),
}
POSITIVE_ENCHANTMENTS = (ENCHANT_LIGHT, ENCHANT_SWIFT)
NEGATIVE_ENCHANTMENTS = (ENCHANT_SEAL, ENCHANT_SHACKLE, ENCHANT_HEAVY, ENCHANT_SLUGGISH)
GROWTH_REWARD_TYPES = (
    "add_new_die",
    "upgrade_random_die_type",
    "upgrade_chosen_die_type",
    "replace_random_face_random_die",
    "replace_random_face_chosen_die",
    "replace_chosen_face_chosen_die",
    "increase_random_face_random_die",
    "increase_random_face_chosen_die",
    "increase_chosen_face",
    "add_light_enchant",
    "add_swift_enchant",
    "clear_negative_enchant",
    "convert_negative_enchant",
)

GROWTH_REWARD_WEIGHTS = {
    "add_new_die": 10,
    "upgrade_random_die_type": 5,
    "upgrade_chosen_die_type": 5,
    "replace_random_face_random_die": 12,
    "replace_random_face_chosen_die": 12,
    "replace_chosen_face_chosen_die": 12,
    "increase_random_face_random_die": 18,
    "increase_random_face_chosen_die": 18,
    "increase_chosen_face": 18,
    "add_light_enchant": 10,
    "add_swift_enchant": 10,
    "clear_negative_enchant": 15,
    "convert_negative_enchant": 5,
}

NEW_DIE_SPECS = {
    "str": ((6, 12, 30, 6), (8, 20, 44, 3), (10, 30, 60, 1)),
    "dex": ((6, 12, 30, 6), (8, 20, 44, 3), (10, 30, 60, 1)),
    "int": ((6, 12, 30, 6), (8, 20, 44, 3), (10, 30, 60, 1)),
    "con": ((4, 4, 4, 1),),
    "pow": ((20, 20, 20, 1),),
}
DICE_POOL_LIMITS = {"con": 3, "pow": 3, "str": 5, "dex": 5, "int": 5}

REPLACEMENT_FACE_BAND_WEIGHTS = {
    "replace_random_face_random_die": {"high": 3, "mid": 2, "low": 1},
    "replace_random_face_chosen_die": {"high": 2, "mid": 2, "low": 2},
    "replace_chosen_face_chosen_die": {"high": 1, "mid": 2, "low": 3},
}

INCREASE_FACE_AMOUNT_WEIGHTS = {
    "increase_random_face_random_die": {2: 8, 1: 4},
    "increase_random_face_chosen_die": {2: 6, 1: 6},
    "increase_chosen_face": {2: 4, 1: 8},
}
DEGRADATION_PENALTY_TYPES = (
    "seal_die",
    "shackle_die",
    "add_heavy_enchant",
    "add_sluggish_enchant",
    "downgrade_die_type",
    "decrease_random_face",
    "decrease_chosen_face",
)

CARD_TYPE_LABELS = {
    "add_new_die": "新增骰子",
    "upgrade_random_die_type": "随机提升骰型",
    "upgrade_chosen_die_type": "指定提升骰型",
    "replace_random_face_random_die": "随机骰子替换随机面值",
    "replace_random_face_chosen_die": "指定骰子替换随机面值",
    "replace_chosen_face_chosen_die": "指定骰子替换指定面值",
    "increase_random_face_random_die": "随机骰子提升随机面值",
    "increase_random_face_chosen_die": "指定骰子提升随机面值",
    "increase_chosen_face": "提升指定面值",
    "add_light_enchant": "添加轻盈",
    "add_swift_enchant": "添加轻捷",
    "clear_negative_enchant": "清除负面附魔",
    "convert_negative_enchant": "转化负面附魔",
    "seal_die": "封印骰子",
    "shackle_die": "枷锁骰子",
    "add_heavy_enchant": "添加沉重",
    "add_sluggish_enchant": "添加迟滞",
    "downgrade_die_type": "降低骰型",
    "decrease_random_face": "降低随机面值",
    "decrease_chosen_face": "降低指定面值",
}


def ensure_second_stage_state(character):
    ensure_health(character)
    if not isinstance(character.formal_attributes, RevertableDict):
        character.formal_attributes = RevertableDict(character.formal_attributes)
    if not isinstance(character.attribute_values, RevertableDict):
        character.attribute_values = RevertableDict(character.attribute_values)
    if not isinstance(character.attribute_bonuses, RevertableDict):
        character.attribute_bonuses = RevertableDict(character.attribute_bonuses)
    for name in ATTRIBUTES:
        bonuses = character.attribute_bonuses.get(name)
        if bonuses is None:
            character.attribute_bonuses[name] = RevertableList()
            continue
        if not isinstance(bonuses, RevertableList):
            bonuses = RevertableList(bonuses)
            character.attribute_bonuses[name] = bonuses
        for index, item in enumerate(bonuses):
            if isinstance(item, dict) and not isinstance(item, RevertableDict):
                bonuses[index] = RevertableDict(item)
    if not isinstance(character.dice_pool, RevertableList):
        character.dice_pool = RevertableList(character.dice_pool)
    for die in character.dice_pool:
        if not isinstance(die.faces, RevertableList):
            die.faces = RevertableList(die.faces)
    defaults = {
        "good_routine_streak": 0,
        "late_night_energy_schedule_week_count": 0,
        "day": 1,
        "weekday": 1,
        "time_slot_index": 0,
        "current_time_slot": None,
        "night_actions_completed": 0,
        "night_snack_eaten": False,
        "sleep_pending": None,
        "deep_fatigue": None,
        "next_day_energy_cap_bonus": 0,
        "ember": None,
        "bipolar_ember": None,
        "ect_residual_days": 0,
        "drug_dependence": False,
        "initial_gameplay_statuses_applied": False,
        "ever_had_pain_and_scars": False,
        "current_weather": None,
        "current_temperature": None,
        "weather_override": None,
        "hunger_level": 0,
        "meal_satiety_progress": 0,
        "digestive_disorder": None,
        "malnutrition": None,
        "palpitations": False,
        "intoxication": 0,
        "coffee_count_today": 0,
        "daytime_sleep_pending": None,
    }
    for key, value in defaults.items():
        if not hasattr(character, key):
            setattr(character, key, value)
    if not hasattr(character, "meal_choices"):
        character.meal_choices = RevertableDict()
    elif not isinstance(character.meal_choices, RevertableDict):
        character.meal_choices = RevertableDict(character.meal_choices)
    if not hasattr(character, "sleep_fatigue"):
        character.sleep_fatigue = RevertableList()
    elif not isinstance(character.sleep_fatigue, RevertableList):
        character.sleep_fatigue = RevertableList(character.sleep_fatigue)
    if not hasattr(character, "fatigue_history"):
        # Old saves recorded missing-sleep POW penalties, not nightly fatigue receipts.
        legacy_drowsiness = sum(expiry > character.day for expiry in character.sleep_fatigue)
        character.sleep_fatigue = RevertableList()
        character.fatigue_layers = 0
        character.fatigue_history = RevertableList()
        if character.deep_fatigue is not None:
            character.good_routine = False
            character.good_routine_streak = 0
    elif not isinstance(character.fatigue_history, RevertableList):
        character.fatigue_history = RevertableList(character.fatigue_history)
        legacy_drowsiness = int(getattr(character, "drowsiness", 0))
    else:
        legacy_drowsiness = int(getattr(character, "drowsiness", 0))
    mapping_defaults = {
        "emotions": {},
        "check_streak": {"success": 0, "failure": 0},
        "long_emotions": {"confidence": False, "doubt": False},
        "pending_bipolar_medications": {},
        "medicine_counts": {},
        "medicine_taken_today": {},
        "environment_diseases": {},
        "environment_natural_cure_rewards": {},
        "injuries": {},
        "exposure_rounds": {"cold": 0, "heat": 0},
        "time_habits": {},
    }
    for key, value in mapping_defaults.items():
        current = getattr(character, key, value)
        if not isinstance(current, RevertableDict):
            current = RevertableDict(current)
        setattr(character, key, current)
    if legacy_drowsiness:
        character.emotions[EMOTION_DISTRACTION] = int(character.emotions.get(EMOTION_DISTRACTION, 0)) + legacy_drowsiness
    character.drowsiness = 0  # Compatibility field only; vNext uses the emotion pool.
    for key, default in (("success", 0), ("failure", 0)):
        if key not in character.check_streak:
            character.check_streak[key] = default
    for key in ("confidence", "doubt"):
        if key not in character.long_emotions:
            character.long_emotions[key] = False
    for key in ("cold", "heat"):
        if key not in character.exposure_rounds:
            character.exposure_rounds[key] = 0
    for key in ("psych_medication_days", "time_habit_history", "overeating_history", "severe_hunger_history"):
        current = getattr(character, key, RevertableList())
        if not isinstance(current, RevertableList):
            current = RevertableList(current)
        setattr(character, key, current)
    if character.sleep_pending is not None and not isinstance(character.sleep_pending, RevertableDict):
        character.sleep_pending = RevertableDict(character.sleep_pending)
    if character.deep_fatigue is not None and not isinstance(character.deep_fatigue, RevertableDict):
        character.deep_fatigue = RevertableDict(character.deep_fatigue)
    # The old single deep-night action becomes the first of three, not a new day.
    if character.current_time_slot == "late_night":
        character.current_time_slot = "late_night_1"
    dict_defaults = (
        "dice_growth_progress",
        "growth_reward_pending",
        "degradation_progress",
        "degradation_penalty_pending",
        "attribute_bonus_gain_counters",
        "attribute_value_gain_counters",
        "formal_attribute_gain_counters",
    )
    for key in dict_defaults:
        if not hasattr(character, key):
            setattr(character, key, RevertableDict((name, 0) for name in ATTRIBUTES))
        else:
            if not isinstance(getattr(character, key), RevertableDict):
                setattr(character, key, RevertableDict(getattr(character, key)))
            mapping = getattr(character, key)
            for name in ATTRIBUTES:
                if name not in mapping:
                    mapping[name] = 0
    if not hasattr(character, "test_growth_progress"):
        character.test_growth_progress = RevertableDict((name, 0) for name in TEST_TRAINING_ATTRIBUTES)
    else:
        if not isinstance(character.test_growth_progress, RevertableDict):
            character.test_growth_progress = RevertableDict(character.test_growth_progress)
        for name in TEST_TRAINING_ATTRIBUTES:
            if name not in character.test_growth_progress:
                character.test_growth_progress[name] = 0
    if not hasattr(character, "training_fatigue"):
        character.training_fatigue = RevertableDict((name, 0) for name in TEST_TRAINING_SCHEDULE_ATTRIBUTES)
    else:
        if not isinstance(character.training_fatigue, RevertableDict):
            character.training_fatigue = RevertableDict(character.training_fatigue)
        for name in TEST_TRAINING_SCHEDULE_ATTRIBUTES:
            if name not in character.training_fatigue:
                character.training_fatigue[name] = 0
    return character


EMOTION_LABELS = {
    EMOTION_JOY: "喜悦", EMOTION_CALM: "镇定", EMOTION_EXCITEMENT: "兴奋",
    EMOTION_SADNESS: "悲伤", EMOTION_ANXIETY: "焦虑", EMOTION_DISTRACTION: "涣散",
}
EMOTION_OPPOSITES = {
    EMOTION_JOY: EMOTION_SADNESS, EMOTION_SADNESS: EMOTION_JOY,
    EMOTION_CALM: EMOTION_ANXIETY, EMOTION_ANXIETY: EMOTION_CALM,
    EMOTION_EXCITEMENT: EMOTION_DISTRACTION, EMOTION_DISTRACTION: EMOTION_EXCITEMENT,
}
STACKABLE_EMOTIONS = (EMOTION_JOY, EMOTION_CALM, EMOTION_EXCITEMENT, EMOTION_DISTRACTION)


def emotion_layers(state, emotion):
    ensure_second_stage_state(state)
    return int(state.emotions.get(emotion, 0))


def add_emotion(state, emotion, layers=1, force=False):
    """Add emotion layers after 1:1 opposite cancellation."""
    ensure_second_stage_state(state)
    if emotion not in EMOTION_LABELS:
        raise ValueError("Unknown emotion: {}".format(emotion))
    added = 0
    for _ in range(max(0, int(layers))):
        opposite = EMOTION_OPPOSITES[emotion]
        if not force and emotion_layers(state, opposite):
            state.emotions[opposite] -= 1
            if state.emotions[opposite] <= 0:
                state.emotions.pop(opposite, None)
            continue
        if emotion in STACKABLE_EMOTIONS:
            state.emotions[emotion] = emotion_layers(state, emotion) + 1
            added += 1
        elif not emotion_layers(state, emotion):
            state.emotions[emotion] = 1
            added += 1
    return added


def remove_emotion(state, emotion, layers=None):
    ensure_second_stage_state(state)
    current = emotion_layers(state, emotion)
    removed = current if layers is None else min(current, max(0, int(layers)))
    if removed:
        remaining = current - removed
        if remaining:
            state.emotions[emotion] = remaining
        else:
            state.emotions.pop(emotion, None)
    return removed


def clear_sleep_emotions(state, night_main=False):
    events = []
    emotions = tuple(EMOTION_LABELS) if night_main else (EMOTION_EXCITEMENT, EMOTION_DISTRACTION)
    for emotion in emotions:
        if remove_emotion(state, emotion):
            events.append("emotion_cleared:{}".format(emotion))
    if state.palpitations:
        state.palpitations = False
        events.append("palpitations_cleared")
    if state.intoxication:
        state.intoxication = 0
        events.append("intoxication_cleared")
    return events


def _draw_emotion(state, positive, rng=None):
    weighted = ((EMOTION_JOY, 2), (EMOTION_CALM, 2), (EMOTION_EXCITEMENT, 1)) if positive else (
        (EMOTION_SADNESS, 2), (EMOTION_ANXIETY, 2), (EMOTION_DISTRACTION, 1))
    emotion = _weighted_choice(weighted, rng)
    return emotion, add_emotion(state, emotion, 1)


def check_generates_emotion(spec):
    return getattr(spec, "check_context", None) in ("schedule", "story") and spec.action_type not in (ACTION_WAKE, ACTION_SLEEP)


def settle_check_emotions(state, spec, result, rng=None):
    """One final action result settles emotions once; retries must not call this."""
    if not check_generates_emotion(spec) or result is None or not result.available:
        return []
    rng = _rng(rng)
    events = []
    if result.success:
        state.check_streak["success"] += 1
        state.check_streak["failure"] = 0
    else:
        state.check_streak["failure"] += 1
        state.check_streak["success"] = 0
    removed_opposite = False
    if state.long_emotions.get("confidence") and state.check_streak["failure"] >= 3:
        state.long_emotions["confidence"] = False
        state.check_streak["failure"] = 0
        removed_opposite = True
        events.append("confidence_cleared")
    elif state.long_emotions.get("doubt") and state.check_streak["success"] >= 3:
        state.long_emotions["doubt"] = False
        state.check_streak["success"] = 0
        removed_opposite = True
        events.append("doubt_cleared")
    if not removed_opposite and result.success and state.check_streak["success"] >= 3:
        state.check_streak["success"] = 0
        if not state.long_emotions.get("confidence") and rng.random() < .15:
            state.long_emotions["confidence"] = True
            state.long_emotions["doubt"] = False
            events.append("confidence_gained")
    elif not removed_opposite and not result.success and state.check_streak["failure"] >= 3:
        state.check_streak["failure"] = 0
        if not state.long_emotions.get("doubt") and rng.random() < .15:
            state.long_emotions["doubt"] = True
            state.long_emotions["confidence"] = False
            events.append("doubt_gained")
    if result.rank == RESULT_BIG_SUCCESS:
        attempts = (True, True, True)
        guaranteed = 1
    elif result.rank == RESULT_HARD_SUCCESS:
        attempts = (True, True)
        guaranteed = 0
    elif result.rank == RESULT_SUCCESS:
        attempts = (True,)
        guaranteed = 0
    elif result.rank == RESULT_BIG_FAILURE:
        attempts = (False,)
        guaranteed = 1
    else:
        attempts = (False,)
        guaranteed = 0
    for index, positive in enumerate(attempts):
        chance = (1.0 / 3.0) if result.rank == RESULT_FAILURE else .5
        if index < guaranteed or rng.random() < chance:
            emotion, added = _draw_emotion(state, positive, rng)
            events.append("emotion:{}:{}".format(emotion, added))
    return events


def apply_initial_gameplay_statuses(state, rng=None):
    """Explicit story hook for Flo's first controllable HUD appearance."""
    ensure_second_stage_state(state)
    if state.initial_gameplay_statuses_applied:
        return []
    state.ember = 180
    state.ect_residual_days = 30
    state.drug_dependence = True
    state.initial_gameplay_statuses_applied = True
    if state.current_weather is None:
        generate_weather(state, rng=rng or daily_weather_rng(state))
    return ["ember:180", "ect_residual:30", "drug_dependence"]


def diagnose_bipolar(state):
    ensure_second_stage_state(state)
    state.ember = None
    state.bipolar_ember = 180
    return ["bipolar_ember:180"]


def bipolar_ember_delta(state, rng=None):
    ensure_second_stage_state(state)
    if state.bipolar_ember is None:
        return 0
    rng = _rng(rng)
    layer = int(clamp(state.bipolar_ember, 0, 180))
    magnitude_factor = .5 + layer / 360.0
    magnitude = rng.uniform(15 * magnitude_factor, 45 * magnitude_factor)
    if state.mood > 0:
        sign = 1 if rng.random() < .75 else -1
    elif state.mood < 0:
        sign = -1 if rng.random() < .75 else 1
    else:
        sign = 1 if rng.random() < .5 else -1
    for medicine in tuple(state.pending_bipolar_medications):
        positive, negative = BIPOLAR_MEDICINE_MULTIPLIERS[medicine]
        magnitude *= positive if sign > 0 else negative
    state.pending_bipolar_medications.clear()
    return int(math.floor(magnitude)) * sign


def settle_morning_mood(state, rng=None):
    """Morning order: ember, ECT residual, then pending bipolar medicine is consumed."""
    ensure_second_stage_state(state)
    events = []
    if state.ember is not None:
        delta = apply_mood_delta(state, -(15 + state.ember / 12.0))
        events.append("ember_mood:{:+d}".format(delta))
    if state.bipolar_ember is not None:
        delta = apply_mood_delta(state, bipolar_ember_delta(state, rng))
        events.append("bipolar_ember_mood:{:+d}".format(delta))
    if state.ect_residual_days > 0:
        age = 30 - state.ect_residual_days
        base = 15 * max(0.0, 1 - age / 30.0)
        delta = apply_mood_delta(state, base)
        state.ect_residual_days -= 1
        events.append("ect_residual_mood:{:+d}".format(delta))
    return events


def add_medicine_stock(state, medicine, amount):
    ensure_second_stage_state(state)
    state.medicine_counts[medicine] = max(0, int(state.medicine_counts.get(medicine, 0)) + int(amount))
    return state.medicine_counts[medicine]


def _record_psychiatric_medication_day(state):
    days = sorted(set(int(day) for day in state.psych_medication_days if int(day) >= state.day - 6) | {state.day})
    state.psych_medication_days = RevertableList(days)
    if len(days) >= 5:
        state.drug_dependence = True


def take_medicine(state, medicine, rng=None, confirm_repeat=False):
    ensure_second_stage_state(state)
    rng = _rng(rng)
    if medicine not in PSYCHIATRIC_MEDICINES:
        raise ValueError("Unknown medicine: {}".format(medicine))
    if int(state.medicine_counts.get(medicine, 0)) <= 0:
        return {"available": False, "reason": "out_of_stock", "events": []}
    today_key = "medicine_taken_today"
    taken_today = getattr(state, today_key, RevertableDict())
    if not isinstance(taken_today, RevertableDict):
        taken_today = RevertableDict(taken_today)
    setattr(state, today_key, taken_today)
    repeat = int(taken_today.get(medicine, 0))
    if repeat and not confirm_repeat:
        return {"available": False, "reason": "repeat_confirmation_required", "repeat": True, "events": []}
    state.medicine_counts[medicine] -= 1
    taken_today[medicine] = repeat + 1
    _record_psychiatric_medication_day(state)
    events = ["medicine:{}".format(medicine)]
    if repeat:
        events.append("repeat_medicine_event_hook:{}".format(medicine))
    if medicine in BIPOLAR_MEDICINE_MULTIPLIERS:
        if medicine not in state.pending_bipolar_medications:
            state.pending_bipolar_medications[medicine] = True
            if medicine == "aripiprazole" and rng.random() < .5:
                add_emotion(state, EMOTION_EXCITEMENT)
                events.append("emotion:excitement")
            if medicine == "lamotrigine" and rng.random() < .5:
                add_emotion(state, EMOTION_DISTRACTION)
                events.append("emotion:distraction")
        return {"available": True, "repeat": bool(repeat), "events": events}
    bases = {"venlafaxine": 10, "trazodone": 5, "alprazolam": 15}
    base = bases[medicine] * (0.5 ** repeat)
    delta = apply_mood_delta(state, base)
    events.append("medicine_mood:{:+d}".format(delta))
    if medicine == "trazodone":
        state.trazodone_sleep_bonus_day = state.day
    elif medicine == "alprazolam":
        if remove_emotion(state, EMOTION_ANXIETY):
            events.append("anxiety_cleared")
    return {"available": True, "repeat": bool(repeat), "mood_delta": delta, "events": events}


def close_medicine_node(state, took_psychiatric_medicine):
    ensure_second_stage_state(state)
    if state.drug_dependence and not took_psychiatric_medicine:
        before = state.mood
        state.mood = int(clamp(state.mood * 1.05, -200, 200))
        return ["drug_dependence_mood:{}:{}".format(before, state.mood)]
    return []


def update_drug_dependence_day(state):
    ensure_second_stage_state(state)
    state.psych_medication_days = RevertableList(day for day in state.psych_medication_days if day >= state.day - 6)
    last = max(state.psych_medication_days) if state.psych_medication_days else None
    if state.drug_dependence and (last is None or state.day - last >= 21):
        state.drug_dependence = False
        return ["drug_dependence_cleared"]
    if len(set(state.psych_medication_days)) >= 5:
        state.drug_dependence = True
    return []


def season_for_day(day):
    return SEASONS[((max(1, int(day)) - 1) // 90) % 4]


def daily_weather_rng(state):
    """A day-stable stream keeps weather rollback-safe without consuming action RNG."""
    return random.Random(20260922 + int(state.day) * 7919)


def generate_weather(state, season=None, override=None, rng=None):
    ensure_second_stage_state(state)
    rng = _rng(rng)
    season = season or season_for_day(state.day)
    if season not in SEASONS:
        raise ValueError("Unknown season: {}".format(season))
    weather = override or state.weather_override
    if weather is None:
        weather = _weighted_choice(list(zip(WEATHERS, WEATHER_WEIGHTS[season])), rng)
    if weather not in WEATHERS:
        raise ValueError("Unknown weather: {}".format(weather))
    temperature = int(clamp(round(50 + 15 * rng.gauss(0, 1) + SEASON_TEMPERATURE_OFFSETS[season]
                                  + WEATHER_TEMPERATURE_OFFSETS[weather]), 0, 100))
    state.current_weather = weather
    state.current_temperature = temperature
    return {"weather": weather, "temperature": temperature, "band": temperature_band(temperature)}


def temperature_band(temperature):
    value = int(temperature)
    if value <= 9:
        return "extreme_cold"
    if value <= 29:
        return "cold"
    if value <= 69:
        return "temperate"
    if value <= 89:
        return "hot"
    return "extreme_hot"


def environment_disease_probability(state):
    con = float(clamp(effective_attribute(state, "con"), 1, 20))
    return 1 - ((1 - .109) ** (6.0 / con))


def environment_recovery_probability(state):
    con = float(clamp(effective_attribute(state, "con"), 1, 20))
    return 1 - ((1 - .308) ** (con / 6.0))


def _roll_damage(dice, rng=None):
    rng = _rng(rng)
    return sum(rng.randint(1, sides) for sides in dice)


def trigger_environment_disease(state, disease, rng=None):
    ensure_second_stage_state(state)
    current = state.environment_diseases.get(disease)
    if current is None:
        damage = _roll_damage((4,), rng)
        state.environment_diseases[disease] = RevertableDict(stage=1, acquired_day=state.day,
            stage_day=state.day, required_hospital=False, natural_reward_claimed=False)
        damage_health(state, damage)
        return ["environment_disease:{}:1".format(disease), "health_damage:{}".format(damage)]
    if int(current.get("stage", 1)) == 1:
        current["stage"] = 2
        current["stage_day"] = state.day
        return ["environment_disease_aggravated:{}".format(disease)]
    current["required_hospital"] = True
    return ["hospital_required_hook:{}".format(disease)]


def process_environment_exposure(state, rng=None):
    ensure_second_stage_state(state)
    band = temperature_band(state.current_temperature if state.current_temperature is not None else 50)
    disease = "cold" if band in ("extreme_cold", "cold") else "heat" if band in ("hot", "extreme_hot") else None
    if disease is None:
        return []
    rolls = 2 if band in ("extreme_cold", "extreme_hot") else 1
    state.exposure_rounds[disease] += 1
    triggered = state.exposure_rounds[disease] >= 30
    for _ in range(rolls):
        if triggered or roll_probability(environment_disease_probability(state), rng):
            triggered = True
            break
    if not triggered:
        return ["environment_exposure:{}:{}".format(disease, state.exposure_rounds[disease])]
    state.exposure_rounds[disease] = 0
    return trigger_environment_disease(state, disease, rng)


def settle_environment_diseases_morning(state, rng=None):
    ensure_second_stage_state(state)
    events = []
    for disease in list(state.environment_diseases):
        item = state.environment_diseases[disease]
        if state.day <= int(item.get("acquired_day", state.day)):
            continue
        age = state.day - int(item.get("stage_day", state.day)) + 1
        cured = age >= 7 or roll_probability(environment_recovery_probability(state), rng)
        if cured:
            reward = not bool(state.environment_natural_cure_rewards.get(disease, False))
            state.environment_diseases.pop(disease, None)
            if reward:
                state.environment_natural_cure_rewards[disease] = True
                add_formal_attribute(state, "con", 1)
                events.append("environment_disease_first_natural_cure:{}".format(disease))
            events.append("environment_disease_cured:{}".format(disease))
            continue
        damage = _roll_damage((2, 3) if int(item.get("stage", 1)) >= 2 else (2,), rng)
        damage_health(state, damage)
        events.append("environment_disease_damage:{}:{}".format(disease, damage))
    return events


def weather_check_effects(state, spec):
    """Return counts/factors only; multi-source reroll placement remains configurable."""
    weather = getattr(state, "current_weather", None)
    effects = {"available": True, "advantage_count": 0, "disadvantage_count": 0,
               "final_multiplier": 1.0, "mood_delta_base": 0}
    if weather == WEATHER_STORM and spec.outdoors:
        effects.update(available=False, reason="storm_blocks_outdoors")
        return effects
    if weather in (WEATHER_HEAVY_RAIN, WEATHER_THUNDERSTORM) and spec.outdoors and spec.sport:
        effects.update(available=False, reason="rain_blocks_outdoor_sport")
        return effects
    if weather in (WEATHER_LIGHT_RAIN, WEATHER_HEAVY_RAIN, WEATHER_THUNDERSTORM, WEATHER_STORM):
        if spec.rest or spec.action_type == ACTION_SLEEP:
            effects["advantage_count"] += 1
        if weather != WEATHER_STORM or not spec.outdoors:
            effects["mood_delta_base"] += -5 if spec.outdoors else 5
    if weather == WEATHER_LIGHT_RAIN and spec.outdoors and spec.sport:
        effects["disadvantage_count"] += 1
    if weather == WEATHER_FOG and spec.outdoors:
        effects["final_multiplier"] *= .75
    if weather in (WEATHER_LIGHT_SNOW, WEATHER_HEAVY_SNOW) and spec.social:
        effects["final_multiplier"] *= 1.25
    return effects


def space_reward_multiplier(location, reward_tag, positive=True, rest=False):
    """Apply one most-specific rule to a positive output; never change costs/failures."""
    if not positive:
        return 1.0
    if location == "gym" and reward_tag == "training":
        return 1.25
    if location in ("school", "library") and reward_tag == "study":
        return 1.25
    if location == "park" and reward_tag == "mood":
        return 1.25
    if location == "home":
        if reward_tag == "mood":
            return 1.15
        return 1.0 if rest or reward_tag == "energy" else .85
    if location == "cafe" and reward_tag in ("study", "social"):
        return 1.15
    if location == "bar" and reward_tag == "social":
        return 1.25
    return 1.0


def apply_space_reward(value, location, reward_tag, rest=False):
    if value <= 0:
        return value
    return int(math.floor(value * space_reward_multiplier(location, reward_tag, True, rest)))


def broad_time_period(slot):
    if slot in ("morning_1", "morning_2"):
        return "morning"
    if slot in ("afternoon_1", "afternoon_2"):
        return "afternoon"
    if slot in ("evening_1", "evening_2", "late_night_1", "late_night_2", "late_night_3"):
        return "evening"
    return None


def record_time_habit_action(state, category, slot=None):
    ensure_second_stage_state(state)
    period = broad_time_period(slot or state.current_time_slot)
    if not period or not category:
        return []
    state.time_habit_history.append(RevertableDict(day=state.day, period=period, category=category))
    return refresh_time_habits(state)


def refresh_time_habits(state):
    ensure_second_stage_state(state)
    state.time_habit_history = RevertableList(item for item in state.time_habit_history if int(item["day"]) >= state.day - 6)
    counts = {}
    for item in state.time_habit_history:
        key = "{}:{}".format(item["period"], item["category"])
        counts[key] = counts.get(key, 0) + 1
    events = []
    for key in list(state.time_habits):
        if counts.get(key, 0) < 5:
            state.time_habits.pop(key, None)
            events.append("time_habit_lost:{}".format(key))
    for key, count in sorted(counts.items()):
        if count >= 5 and key not in state.time_habits and len(state.time_habits) < 3:
            state.time_habits[key] = True
            events.append("time_habit_gained:{}".format(key))
    return events


def time_habit_energy_discount(state, spec):
    category = getattr(spec, "schedule_category", None)
    period = broad_time_period(getattr(state, "current_time_slot", None))
    return 1 if period and category and state.time_habits.get("{}:{}".format(period, category)) else 0


FOOD_SATIETY = {"meal": 5, "appetizer": 3, "dessert": 2, "drink": 1}


def begin_meal_node(state):
    ensure_second_stage_state(state)
    state.meal_satiety_progress = 0
    if state.hunger_level < 0:
        state.hunger_level = 0
    else:
        state.hunger_level += 1
    return state.hunger_level


def consume_food(state, food_type, rng=None):
    ensure_second_stage_state(state)
    if food_type not in FOOD_SATIETY:
        raise ValueError("Unknown food type: {}".format(food_type))
    events = []
    if state.hunger_level < 0:
        if state.digestive_disorder is not None:
            state.digestive_disorder["layers"] += 1
            state.digestive_disorder["last_trigger_day"] = state.day
            damage = _roll_damage((4,), rng)
            damage_health(state, damage)
            events.extend(("digestive_disorder_aggravated", "health_damage:{}".format(damage)))
        else:
            state.overeating_history.append(state.day)
            events.append("overeating_record")
    elif state.hunger_level > 0:
        state.hunger_level -= 1
        events.append("hunger_reduced")
    else:
        state.meal_satiety_progress += FOOD_SATIETY[food_type]
        if state.meal_satiety_progress >= 5:
            state.hunger_level = -1
            events.append("full")
    return events


def finish_meal_node(state, rng=None):
    ensure_second_stage_state(state)
    events = []
    if state.hunger_level >= 3:
        if state.malnutrition is not None:
            state.malnutrition["layers"] += 1
            state.malnutrition["last_trigger_day"] = state.day
            damage = _roll_damage((4,), rng)
            damage_health(state, damage)
            events.extend(("malnutrition_aggravated", "health_damage:{}".format(damage)))
        else:
            state.severe_hunger_history.append(state.day)
            events.append("severe_hunger_record")
    state.meal_satiety_progress = 0
    state.overeating_history = RevertableList(day for day in state.overeating_history if day >= state.day - 6)
    state.severe_hunger_history = RevertableList(day for day in state.severe_hunger_history if day >= state.day - 6)
    if len(state.overeating_history) >= 3 and state.digestive_disorder is None:
        state.digestive_disorder = RevertableDict(layers=1, last_trigger_day=state.day)
        state.overeating_history = RevertableList()
        damage = _roll_damage((4,), rng)
        damage_health(state, damage)
        events.extend(("digestive_disorder", "health_damage:{}".format(damage)))
    if len(state.severe_hunger_history) >= 3 and state.malnutrition is None:
        state.malnutrition = RevertableDict(layers=1, last_trigger_day=state.day)
        state.severe_hunger_history = RevertableList()
        damage = _roll_damage((4,), rng)
        damage_health(state, damage)
        events.extend(("malnutrition", "health_damage:{}".format(damage)))
    return events


def settle_nutrition_diseases(state):
    ensure_second_stage_state(state)
    events = []
    if state.digestive_disorder is not None and state.day - int(state.digestive_disorder["last_trigger_day"]) >= 7:
        state.digestive_disorder = None
        events.append("digestive_disorder_natural_cure")
    if state.malnutrition is not None and state.day - int(state.malnutrition["last_trigger_day"]) >= 7:
        state.malnutrition = None
        events.append("malnutrition_natural_cure")
    return events


def treat_nutrition_disease(state, disease, method):
    ensure_second_stage_state(state)
    field = "digestive_disorder" if disease == "digestive" else "malnutrition" if disease == "malnutrition" else None
    if field is None:
        raise ValueError("Unknown nutrition disease: {}".format(disease))
    item = getattr(state, field)
    if item is None:
        return []
    layers = int(item["layers"])
    if method == "medicine":
        add_formal_attribute(state, "dex" if disease == "digestive" else "str", -layers)
    elif method != "hospital":
        raise ValueError("Unknown treatment method: {}".format(method))
    setattr(state, field, None)
    return ["{}_cured:{}".format(disease, method)]


INJURY_RULES = {
    "strain": {"dice": ((4,), (4, 6), (4, 6, 8)), "multiplier": .85, "q6": .50, "forced_day": 3},
    "sprain": {"dice": ((6,), (6, 8), (6, 8, 10)), "multiplier": .75, "q6": .308, "forced_day": 7},
    "fracture": {"dice": ((4, 6), (4, 6, 8), (4, 6, 8, 10)), "multiplier": .50, "q6": .10, "forced_day": 21},
}


def acquire_injury(state, injury, rng=None):
    ensure_second_stage_state(state)
    if injury not in INJURY_RULES:
        raise ValueError("Unknown injury: {}".format(injury))
    current = state.injuries.get(injury)
    reinjury = min(2, int(current.get("reinjury", 0)) + 1) if current else 0
    beyond_cap = bool(current and int(current.get("reinjury", 0)) >= 2)
    damage = _roll_damage(INJURY_RULES[injury]["dice"][reinjury], rng)
    damage_health(state, damage)
    state.injuries[injury] = RevertableDict(reinjury=reinjury, acquired_day=state.day,
        stage_day=state.day, severe_reinjury_hook=beyond_cap)
    events = ["injury:{}:{}".format(injury, reinjury), "health_damage:{}".format(damage)]
    if beyond_cap:
        events.append("severe_reinjury_event_hook:{}".format(injury))
    return events


def injury_check_multiplier(state, spec):
    if not (getattr(spec, "sport", False) or getattr(spec, "check_context", None) in ("combat", "attack", "flee")):
        return 1.0
    multiplier = 1.0
    for injury in state.injuries:
        multiplier *= INJURY_RULES[injury]["multiplier"]
    return multiplier


def settle_injuries_morning(state, rng=None):
    ensure_second_stage_state(state)
    events = []
    con = float(clamp(effective_attribute(state, "con"), 1, 20))
    for injury in list(state.injuries):
        item = state.injuries[injury]
        if state.day <= int(item.get("acquired_day", state.day)):
            continue
        rules = INJURY_RULES[injury]
        age = state.day - int(item.get("stage_day", state.day)) + 1
        chance = 1 - ((1 - rules["q6"]) ** (con / 6.0))
        if age >= rules["forced_day"] or roll_probability(chance, rng):
            state.injuries.pop(injury, None)
            events.append("injury_cured:{}".format(injury))
    return events


def get_mood_state(state):
    return mood_state(state)


def calculate_k_pow(state):
    return pow_k(state)


def update_man_dep_after_mood_delta(state, final_delta):
    ensure_second_stage_state(state)
    if state.disease_state == DISEASE_NONE:
        return
    if final_delta > 0:
        state.man = int(clamp(state.man + abs(final_delta), 0, 200))
    elif final_delta < 0:
        state.dep = int(clamp(state.dep + abs(final_delta), 0, 200))


def apply_mood_delta(state, delta_base):
    ensure_second_stage_state(state)
    delta = adjusted_mood_delta(state, delta_base)
    state.mood = int(clamp(state.mood + delta, -200, 200))
    update_man_dep_after_mood_delta(state, delta)
    return delta


def calculate_enter_disease_probability(state):
    return disease_enter_probability(state)


def roll_probability(probability, rng=None):
    return _rng(rng).random() < probability


def roll_enter_disease(state, rng=None):
    return state.disease_state == DISEASE_NONE and abs(state.mood) > 60 and roll_probability(calculate_enter_disease_probability(state), rng)


def calculate_stable_probability(state):
    return stable_probability(state)


def roll_stabilize(state, rng=None):
    return state.disease_state != DISEASE_NONE and roll_probability(calculate_stable_probability(state), rng)


def calculate_switch_probability(state):
    return switch_probability(state)


def roll_switch_disease(state, rng=None):
    return state.disease_state != DISEASE_NONE and roll_probability(calculate_switch_probability(state), rng)


def apply_disease_entry(state):
    if state.disease_state != DISEASE_NONE or abs(state.mood) <= 60:
        return None
    if state.mood > 0:
        state.disease_state = DISEASE_MANIA
        state.man = int(clamp(abs(state.mood), 0, 200))
        state.dep = 0
        state.disease_turns = 0
        if state.bipolar_ember is not None:
            state.bipolar_ember = 180
        return "enter_mania"
    state.disease_state = DISEASE_DEPRESSION
    state.dep = int(clamp(abs(state.mood), 0, 200))
    state.man = 0
    state.disease_turns = 0
    if state.bipolar_ember is not None:
        state.bipolar_ember = 180
    else:
        state.ember = 180
    return "enter_depression"


def apply_stable_return(state):
    previous = state.disease_state
    if previous == DISEASE_NONE:
        return None
    residual = abs(int(state.man) - int(state.dep)) / 2.0
    state.mood = int(clamp(residual if previous == DISEASE_MANIA else -residual, -200, 200))
    state.man = 0
    state.dep = 0
    state.disease_state = DISEASE_NONE
    state.disease_turns = 0
    return "return_stable"


def apply_disease_switch(state):
    if state.disease_state == DISEASE_NONE:
        return None
    old_value = state.man if state.disease_state == DISEASE_MANIA else state.dep
    new_value = state.dep if state.disease_state == DISEASE_MANIA else state.man
    intensity = old_value * 0.6 + new_value
    if state.disease_state == DISEASE_MANIA:
        state.disease_state = DISEASE_DEPRESSION
        state.mood = int(clamp(-intensity, -200, 200))
        state.dep = abs(state.mood)
        state.man = 0
        event = "switch_to_depression"
    else:
        state.disease_state = DISEASE_MANIA
        state.mood = int(clamp(intensity, -200, 200))
        state.man = abs(state.mood)
        state.dep = 0
        event = "switch_to_mania"
    state.disease_turns = 0
    return event


def sleep_factor(state, quality=SLEEP_QUALITY_GOOD):
    pow_value = effective_attribute(state, "pow")
    if pow_value <= 6:
        factor = 0.95
    elif pow_value <= 12:
        factor = 0.95 + (0.90 - 0.95) * ((pow_value - 6) / 6.0)
    elif pow_value <= 18:
        factor = 0.90 + (0.875 - 0.90) * ((pow_value - 12) / 6.0)
    else:
        factor = 0.875 + (0.867 - 0.875) * ((pow_value - 18) / 2.0)
    if getattr(state, "good_routine", False):
        factor = max(0.85, factor - 0.025)
    if quality == SLEEP_QUALITY_POOR:
        factor += .025
    elif quality == SLEEP_QUALITY_EXCELLENT:
        factor -= .025
    if emotion_layers(state, EMOTION_DISTRACTION):
        factor = 1 - (1 - factor) * 1.25
    if emotion_layers(state, EMOTION_EXCITEMENT):
        factor = 1 - (1 - factor) * .75
    factor = max(.85, factor)
    return factor


def apply_sleep_recovery(state, quality=SLEEP_QUALITY_GOOD):
    before = state.mood
    factor = sleep_factor(state, quality)
    state.mood = int(math.floor(abs(state.mood) * factor))
    if before < 0:
        state.mood *= -1
    return {"before": before, "after": state.mood, "factor": factor}


def process_disease_end_turn_checks(state, rng=None):
    events = []
    if state.disease_state == DISEASE_NONE:
        if roll_enter_disease(state, rng):
            events.append(apply_disease_entry(state))
    else:
        if roll_stabilize(state, rng):
            events.append(apply_stable_return(state))
        else:
            state.disease_turns += 1
            if roll_switch_disease(state, rng):
                events.append(apply_disease_switch(state))
    return [event for event in events if event]


def maybe_trigger_disease_random_event(state, rng=None):
    if state.disease_state == DISEASE_NONE:
        return None
    intensity = max(abs(state.mood), state.man, state.dep)
    chance = 0.05 if intensity < 120 else 0.10
    if not roll_probability(chance, rng):
        return None
    return {"type": "mock_disease_event", "disease_state": state.disease_state, "intensity": intensity}


def _counter_step(counter_dict, attr, threshold):
    rewards = counter_dict[attr] // threshold
    counter_dict[attr] = counter_dict[attr] % threshold
    return rewards


def add_dice_growth_progress(state, attr, amount):
    ensure_second_stage_state(state)
    state.dice_growth_progress[attr] += int(amount)
    return state.dice_growth_progress[attr]


def add_growth_reward_pending(state, attr, count=1):
    ensure_second_stage_state(state)
    state.growth_reward_pending[attr] += int(count)
    return state.growth_reward_pending[attr]


def add_degradation_progress(state, attr, amount):
    ensure_second_stage_state(state)
    state.degradation_progress[attr] += int(amount)
    return process_degradation_threshold(state, attr)


def process_degradation_threshold(state, attr):
    ensure_second_stage_state(state)
    gained = state.degradation_progress[attr] // 6
    state.degradation_progress[attr] %= 6
    state.degradation_penalty_pending[attr] += gained
    return gained


def _count_attribute_bonuses(state, attr):
    return len([item for item in state.attribute_bonuses[attr] if int(item.get("value", item if not isinstance(item, dict) else 0)) != 0])


def add_attribute_bonus(state, attr, amount):
    ensure_second_stage_state(state)
    for _ in range(abs(int(amount))):
        state.attribute_bonuses[attr].append(RevertableDict(value=1 if amount >= 0 else -1, source="second_stage"))
        state.attribute_bonus_gain_counters[attr] += 1
        rewards = _counter_step(state.attribute_bonus_gain_counters, attr, 4)
        if rewards:
            add_dice_growth_progress(state, attr, rewards * 6)
    return current_attribute(state, attr)


def gain_attribute_bonus(state, attr, base_probability, rng=None):
    probability = base_probability * (0.5 ** _count_attribute_bonuses(state, attr))
    if roll_probability(probability, rng):
        add_attribute_bonus(state, attr, 1)
        return True
    return False


def add_attribute_value(state, attr, amount):
    ensure_second_stage_state(state)
    state.attribute_values[attr] += int(amount)
    if amount > 0:
        state.attribute_value_gain_counters[attr] += int(amount)
        rewards = _counter_step(state.attribute_value_gain_counters, attr, 2)
        if rewards:
            add_dice_growth_progress(state, attr, rewards * 6)
    return current_attribute(state, attr)


def add_formal_attribute(state, attr, amount):
    ensure_second_stage_state(state)
    before = int(state.formal_attributes.get(attr, 0))
    state.formal_attributes[attr] = max(0, int(state.formal_attributes.get(attr, 0)) + int(amount))
    if attr == "con":
        change_health(state, (state.formal_attributes[attr] - before) * 5)
    if amount > 0:
        state.formal_attribute_gain_counters[attr] += int(amount)
        rewards = _counter_step(state.formal_attribute_gain_counters, attr, 1)
        if rewards:
            add_dice_growth_progress(state, attr, rewards * 6)
    elif amount < 0:
        # Manual 5.10: each actually lost formal point gives 6 degradation points.
        lost = before - state.formal_attributes[attr]
        if lost:
            add_degradation_progress(state, attr, lost * 6)
    return current_attribute(state, attr)


def process_small_rest(state, rng=None):
    rng = _rng(rng)
    ensure_second_stage_state(state)
    events = resolve_test_rest(state)
    for attr in ATTRIBUTES:
        remaining = []
        for bonus in state.attribute_bonuses[attr]:
            roll = rng.random()
            if roll < 0.25:
                events.append("bonus_lost:{}".format(attr))
            elif roll < 0.75:
                remaining.append(bonus)
            else:
                add_attribute_value(state, attr, 1)
                events.append("bonus_to_value:{}".format(attr))
        state.attribute_bonuses[attr] = RevertableList(remaining)
    events.extend(process_dice_growth_progress_on_small_rest(state))
    return events


def process_large_rest(state, rng=None):
    rng = _rng(rng)
    ensure_second_stage_state(state)
    events = []
    for attr in ATTRIBUTES:
        values = int(state.attribute_values[attr])
        kept = 0
        for _ in range(values):
            roll = rng.random()
            if roll < (1.0 / 3.0):
                add_formal_attribute(state, attr, 1)
                events.append("value_to_formal:{}".format(attr))
            elif roll < (5.0 / 6.0):
                kept += 1
            else:
                add_degradation_progress(state, attr, 1)
                events.append("value_lost:{}".format(attr))
        state.attribute_values[attr] = kept
    events.extend(process_temporary_enchant_decay(state, rng))
    return events


def process_dice_growth_progress_on_small_rest(state):
    ensure_second_stage_state(state)
    events = []
    for attr in ATTRIBUTES:
        gained = state.dice_growth_progress[attr] // 6
        state.dice_growth_progress[attr] %= 6
        if gained:
            add_growth_reward_pending(state, attr, gained)
            events.append("growth_reward_pending:{}".format(attr))
    return events


def _weighted_choice(weighted_items, rng=None):
    rng = _rng(rng)
    total = sum(weight for _, weight in weighted_items)
    if total <= 0:
        return weighted_items[0][0] if weighted_items else None
    roll = rng.uniform(0, total)
    running = 0
    for item, weight in weighted_items:
        running += weight
        if roll <= running:
            return item
    return weighted_items[-1][0]


def _random_new_die_spec(attr, rng=None):
    specs = NEW_DIE_SPECS.get(attr, NEW_DIE_SPECS["str"])
    sides, low, high, _weight = _weighted_choice([(spec, spec[3]) for spec in specs], rng)
    return sides, _rng(rng).randint(low, high)


def _face_value_for_band(cap, band, rng=None):
    rng = _rng(rng)
    cap = max(1, int(cap))
    if band == "high":
        low = int(math.ceil(cap * 0.7))
        high = cap
    elif band == "mid":
        low = int(math.ceil(cap * 0.4))
        high = int(math.floor(cap * 0.7))
    else:
        low = int(math.ceil(cap * 0.1))
        high = int(math.floor(cap * 0.4))
    low = int(clamp(low, 1, cap))
    high = int(clamp(high, low, cap))
    return rng.randint(low, high)


def _replacement_face_value(card_type, sides, rng=None):
    weights = REPLACEMENT_FACE_BAND_WEIGHTS[card_type]
    band = _weighted_choice(list(weights.items()), rng)
    return _face_value_for_band(sides, band, rng)


def replacement_face_value(card, die):
    """Read the revealed value for the target type; retain explicit event cards."""
    values = card.get("new_face_values")
    if values is not None:
        return values[str(len(die.faces))]
    return card["new_face_value"]


def _increase_face_amount(card_type, rng=None):
    weights = INCREASE_FACE_AMOUNT_WEIGHTS[card_type]
    return _weighted_choice(list(weights.items()), rng)


def _card_parameter(card_type, rng=None, attr=None, state=None):
    rng = _rng(rng)
    if card_type == "add_new_die":
        sides, face_total = _random_new_die_spec(attr or "str", rng)
        return {"die_sides": sides, "face_total": face_total}
    if card_type in ("replace_random_face_random_die", "replace_random_face_chosen_die", "replace_chosen_face_chosen_die"):
        sides = sorted({len(die.faces) for die in state.dice_for(attr)})
        return {"new_face_values": {str(n): _replacement_face_value(card_type, n, rng) for n in sides}}
    if card_type in ("increase_random_face_random_die", "increase_random_face_chosen_die", "increase_chosen_face"):
        return {"increase_amount": _increase_face_amount(card_type, rng)}
    return {}


def _card(card_type, rng=None, attr=None, state=None):
    card = {"type": card_type}
    card.update(_card_parameter(card_type, rng, attr, state))
    return card


def legal_growth_reward_types(state, attr):
    return [card_type for card_type in GROWTH_REWARD_TYPES if is_growth_reward_legal(state, attr, {"type": card_type})]


def legal_degradation_penalty_types(state, attr):
    return [card_type for card_type in DEGRADATION_PENALTY_TYPES if is_degradation_penalty_legal(state, attr, {"type": card_type})]


def build_growth_reward_card(state, attr, card_type, rng=None):
    return _card(card_type, rng, attr, state)


def build_degradation_penalty_card(state, attr, card_type, rng=None):
    return _card(card_type, rng, attr, state)


def draw_cards_from_types(types, draw_count, rng=None, weights=None, state=None, attr=None):
    rng = _rng(rng)
    if not types:
        return []
    if weights:
        weighted = [(card_type, int(weights.get(card_type, 0))) for card_type in types if int(weights.get(card_type, 0)) > 0]
        if weighted:
            return [_card(_weighted_choice(weighted, rng), rng, attr, state) for _ in range(draw_count)]
    return [_card(rng.choice(types), rng, attr, state) for _ in range(draw_count)]


def draw_growth_reward_cards(state, attr, draw_count=3, rng=None):
    return draw_cards_from_types(legal_growth_reward_types(state, attr), draw_count, rng, GROWTH_REWARD_WEIGHTS, state, attr)


def draw_degradation_penalty_cards(state, attr, draw_count=3, rng=None):
    return draw_cards_from_types(legal_degradation_penalty_types(state, attr), draw_count, rng)


def card_label(card):
    return CARD_TYPE_LABELS.get(card.get("type"), str(card.get("type", "")))



def card_description(card):
    card_type = card.get("type")
    if card_type == "add_new_die":
        sides = int(card.get("die_sides", 0))
        face_total = int(card.get("face_total", 0))
        if sides and face_total:
            return "获得一个骰面总和为{}的{}面骰。".format(face_total, sides)
        return "获得一颗新的属性骰；奖励结算时会确定骰型和骰面总和。"
    if card_type == "upgrade_random_die_type":
        return "随机一颗可升级的属性骰提升至下一骰型，新增两面分别取原骰的最小值和最大值。"
    if card_type == "upgrade_chosen_die_type":
        return "选择一颗可升级的属性骰提升至下一骰型，新增两面分别取原骰的最小值和最大值。"
    if card_type in ("replace_random_face_random_die", "replace_random_face_chosen_die", "replace_chosen_face_chosen_die"):
        values = card.get("new_face_values", {})
        if len(values) > 1:
            preview = "；".join("d{}：{}".format(sides, values[sides]) for sides in sorted(values, key=int))
        else:
            preview = "数值为{}".format(next(iter(values.values())) if values else card.get("new_face_value", 1))
        if card_type == "replace_random_face_random_die":
            target = "一颗随机骰子的随机骰面"
        if card_type == "replace_random_face_chosen_die":
            target = "一个选定骰子的随机骰面"
        if card_type == "replace_chosen_face_chosen_die":
            target = "一个选定骰子的选定骰面"
        return "新骰面（{}），替换{}。".format(preview, target)
    if card_type in ("increase_random_face_random_die", "increase_random_face_chosen_die", "increase_chosen_face"):
        amount = int(card.get("increase_amount", 1))
        if card_type == "increase_random_face_random_die":
            target = "随机骰子的随机骰面"
        elif card_type == "increase_random_face_chosen_die":
            target = "选定骰子的随机骰面"
        else:
            target = "选定骰子的选定骰面"
        return "使{} +{}。".format(target, amount)
    if card_type == "add_light_enchant":
        return "随机为一颗可用骰子添加轻盈。"
    if card_type == "add_swift_enchant":
        return "随机为一颗可用骰子添加奖励骰状态。"
    if card_type == "clear_negative_enchant":
        return "清除一颗选定骰子的负面状态。"
    if card_type == "convert_negative_enchant":
        return "将一颗选定骰子的负面状态转化为正面状态。"
    if card_type == "seal_die":
        return "封印一颗骰子，使其暂时不可用于检定。"
    if card_type == "shackle_die":
        return "为一颗骰子添加枷锁；检定时会优先被吸入骰组。"
    if card_type == "add_heavy_enchant":
        return "为一颗骰子添加沉重，提高使用成本。"
    if card_type == "add_sluggish_enchant":
        return "为一颗骰子添加迟滞，投掷时取较低结果。"
    if card_type == "downgrade_die_type":
        return "随机一颗可降级的属性骰降低至下一骰型，移除两个最低骰面，其余面值不超过新骰型上限。"
    if card_type in ("decrease_random_face", "decrease_chosen_face"):
        target = "随机骰面" if card_type == "decrease_random_face" else "选定骰面"
        return "使一颗骰子的{} -1，最低不低于 1。".format(target)
    return card_label(card)


def card_needs_die_choice(card):
    return card.get("type") in (
        "upgrade_chosen_die_type",
        "replace_random_face_chosen_die",
        "replace_chosen_face_chosen_die",
        "increase_random_face_chosen_die",
        "increase_chosen_face",
        "clear_negative_enchant",
        "convert_negative_enchant",
        "decrease_chosen_face",
    )


def card_needs_face_choice(card):
    return card.get("type") in ("replace_chosen_face_chosen_die", "increase_chosen_face", "decrease_chosen_face")


def pending_growth_reward_attrs(state):
    ensure_second_stage_state(state)
    return [
        attr
        for attr in ATTRIBUTES
        if int(state.growth_reward_pending.get(attr, 0)) > 0 and legal_growth_reward_types(state, attr)
    ]


def pending_degradation_penalty_attrs(state):
    ensure_second_stage_state(state)
    return [
        attr
        for attr in ATTRIBUTES
        if int(state.degradation_penalty_pending.get(attr, 0)) > 0 and legal_degradation_penalty_types(state, attr)
    ]


def draw_pending_growth_reward_cards(state, attr, draw_count=3, rng=None):
    """Draw choices for one pending dice growth reward without consuming it."""
    if int(state.growth_reward_pending.get(attr, 0)) <= 0:
        return []
    return draw_growth_reward_cards(state, attr, draw_count, rng)


def draw_pending_degradation_penalty_cards(state, attr, draw_count=3, rng=None):
    """Draw choices for one pending degradation penalty without consuming it."""
    if int(state.degradation_penalty_pending.get(attr, 0)) <= 0:
        return []
    return draw_degradation_penalty_cards(state, attr, draw_count, rng)


def dice_type_change_candidates(state, attr, upgrade=True):
    """CON/POW have fixed types; only documented STR/DEX/INT steps apply."""
    if attr not in ALLOCATED_ATTRIBUTES:
        return []
    sides = (6, 8, 10) if upgrade else (8, 10, 12)
    return [die for die in state.dice_for(attr) if len(die.faces) in sides]


def growth_reward_face_indices(die, card):
    if card.get("type") in INCREASE_FACE_AMOUNT_WEIGHTS:
        return [i for i, value in enumerate(die.faces) if value < len(die.faces)]
    return list(range(len(die.faces)))


def growth_reward_dice_candidates(state, attr, card):
    kind = card.get("type")
    if kind in ("upgrade_random_die_type", "upgrade_chosen_die_type"):
        return dice_type_change_candidates(state, attr)
    dice = state.dice_for(attr)
    if kind in INCREASE_FACE_AMOUNT_WEIGHTS:
        return [die for die in dice if growth_reward_face_indices(die, card)]
    if kind in ("clear_negative_enchant", "convert_negative_enchant"):
        return [die for die in dice if die.enchantment in NEGATIVE_ENCHANTMENTS]
    return dice


def is_growth_reward_legal(state, attr, reward_card):
    dice = state.dice_for(attr)
    card_type = reward_card.get("type")
    if card_type == "add_new_die":
        if len(dice) >= DICE_POOL_LIMITS.get(attr, 0):
            return False
        if "die_sides" in reward_card and "face_total" in reward_card:
            return any(reward_card["die_sides"] == sides and low <= reward_card["face_total"] <= high
                       for sides, low, high, weight in NEW_DIE_SPECS[attr])
        return True
    if card_type in ("upgrade_random_die_type", "upgrade_chosen_die_type"):
        candidates = dice_type_change_candidates(state, attr)
        if card_type == "upgrade_chosen_die_type" and reward_card.get("die_id"):
            return _chosen_die(state, attr, reward_card) in candidates
        return bool(candidates)
    if card_type in INCREASE_FACE_AMOUNT_WEIGHTS:
        candidates = growth_reward_dice_candidates(state, attr, reward_card)
        if card_needs_die_choice(reward_card) and reward_card.get("die_id"):
            die = _chosen_die(state, attr, reward_card)
            if die not in candidates:
                return False
            if "face_index" in reward_card:
                return reward_card["face_index"] in growth_reward_face_indices(die, reward_card)
        return bool(candidates)
    if card_type in ("replace_random_face_random_die", "replace_random_face_chosen_die", "replace_chosen_face_chosen_die"):
        return bool(dice)
    if card_type in ("add_light_enchant", "add_swift_enchant"):
        return any(die.enchantment is None for die in dice)
    if card_type in ("clear_negative_enchant", "convert_negative_enchant"):
        chosen = _chosen_die(state, attr, reward_card)
        if reward_card.get("die_id"):
            return chosen is not None and chosen.enchantment in NEGATIVE_ENCHANTMENTS
        return any(die.enchantment in NEGATIVE_ENCHANTMENTS for die in dice)
    return False


def is_degradation_penalty_legal(state, attr, penalty_card):
    dice = state.dice_for(attr)
    card_type = penalty_card.get("type")
    if card_type in ("seal_die", "shackle_die", "add_heavy_enchant", "add_sluggish_enchant"):
        return any(die.enchantment is None for die in dice)
    if card_type == "downgrade_die_type":
        return bool(dice_type_change_candidates(state, attr, upgrade=False))
    if card_type in ("decrease_random_face", "decrease_chosen_face"):
        return bool(dice)
    return False


def _random_die(state, attr, rng=None):
    dice = state.dice_for(attr)
    return _rng(rng).choice(dice) if dice else None


def _random_unenchanted_die(state, attr, rng=None):
    dice = [die for die in state.dice_for(attr) if die.enchantment is None]
    return _rng(rng).choice(dice) if dice else None


def _chosen_die(state, attr, card):
    die_id = card.get("die_id")
    if not die_id:
        return None
    die = state.find_die(die_id)
    if die is not None and die.attribute == attr:
        return die
    return None


def _chosen_or_random_die(state, attr, card, rng=None):
    die = _chosen_die(state, attr, card)
    if die is not None:
        return die
    return _random_die(state, attr, rng)


def _chosen_or_random_face_index(die, card, rng=None):
    if die is None or not die.faces:
        return None
    if "face_index" in card:
        index = int(card.get("face_index"))
        if 0 <= index < len(die.faces):
            return index
    return _rng(rng).randrange(len(die.faces))


def _next_die_id(state, attr):
    return "{}_{}".format(attr, len(state.dice_for(attr)) + 1)


def generate_die_faces_with_total(sides, face_total, rng=None):
    rng = _rng(rng)
    sides = int(sides)
    cap = sides
    face_total = int(clamp(int(face_total), sides, sides * cap))
    faces = [1 for _ in range(sides)]
    remaining = face_total - sides
    while remaining > 0:
        candidates = [index for index, value in enumerate(faces) if value < cap]
        if not candidates:
            break
        index = rng.choice(candidates)
        faces[index] += 1
        remaining -= 1
    return faces


def new_die_faces_for_attribute(attr, reward_card=None, rng=None):
    reward_card = reward_card or {}
    if "die_sides" in reward_card and "face_total" in reward_card:
        return generate_die_faces_with_total(reward_card["die_sides"], reward_card["face_total"], rng)
    sides, face_total = _random_new_die_spec(attr, rng)
    return generate_die_faces_with_total(sides, face_total, rng)


def apply_growth_reward(state, attr, reward_card, rng=None):
    ensure_second_stage_state(state)
    rng = _rng(rng)
    card_type = reward_card.get("type")
    if not is_growth_reward_legal(state, attr, reward_card):
        return {"applied": False, "type": card_type}
    if card_type == "add_new_die":
        state.dice_pool.append(RMDice(_next_die_id(state, attr), attr, new_die_faces_for_attribute(attr, reward_card, rng)))
    elif card_type in ("upgrade_random_die_type", "upgrade_chosen_die_type"):
        die = (rng.choice(dice_type_change_candidates(state, attr))
               if card_type == "upgrade_random_die_type" else _chosen_die(state, attr, reward_card))
        if die is None:
            return {"applied": False, "type": card_type, "reason": "missing_die_choice"}
        die.faces.extend((min(die.faces), max(die.faces)))
    elif card_type in ("replace_random_face_random_die", "replace_random_face_chosen_die", "replace_chosen_face_chosen_die"):
        if card_type == "replace_random_face_random_die":
            die = _random_die(state, attr, rng)
        else:
            die = _chosen_die(state, attr, reward_card)
            if die is None:
                return {"applied": False, "type": card_type, "reason": "missing_die_choice"}
        idx = _chosen_or_random_face_index(die, reward_card, rng)
        if idx is None:
            return {"applied": False, "type": card_type}
        die.faces[idx] = int(clamp(int(replacement_face_value(reward_card, die)), 1, len(die.faces)))
    elif card_type in ("increase_random_face_random_die", "increase_random_face_chosen_die", "increase_chosen_face"):
        if card_type == "increase_random_face_random_die":
            die = rng.choice(growth_reward_dice_candidates(state, attr, reward_card))
        else:
            die = _chosen_die(state, attr, reward_card)
            if die is None:
                return {"applied": False, "type": card_type, "reason": "missing_die_choice"}
        indices = growth_reward_face_indices(die, reward_card)
        idx = reward_card.get("face_index")
        if idx is None and card_type != "increase_chosen_face":
            idx = rng.choice(indices)
        if idx not in indices:
            return {"applied": False, "type": card_type}
        die.faces[idx] = int(clamp(die.faces[idx] + int(reward_card.get("increase_amount", 1)), 1, len(die.faces)))
    elif card_type == "add_light_enchant":
        die = _random_unenchanted_die(state, attr, rng)
        if die is None:
            return {"applied": False, "type": card_type}
        set_die_enchantment(die, ENCHANT_LIGHT)
    elif card_type == "add_swift_enchant":
        die = _random_unenchanted_die(state, attr, rng)
        if die is None:
            return {"applied": False, "type": card_type}
        set_die_enchantment(die, ENCHANT_SWIFT)
    elif card_type == "clear_negative_enchant":
        die = _chosen_die(state, attr, reward_card)
        if die is None or die.enchantment not in NEGATIVE_ENCHANTMENTS:
            return {"applied": False, "type": card_type, "reason": "missing_die_choice"}
        clear_die_enchantment(die)
    elif card_type == "convert_negative_enchant":
        die = _chosen_die(state, attr, reward_card)
        if die is None or die.enchantment not in NEGATIVE_ENCHANTMENTS:
            return {"applied": False, "type": card_type, "reason": "missing_die_choice"}
        set_die_enchantment(die, rng.choice(POSITIVE_ENCHANTMENTS), replace=True)
    return {"applied": True, "type": card_type}


def apply_pending_growth_reward(state, attr, reward_card, rng=None):
    """Apply one selected pending growth reward card and consume one pending count."""
    ensure_second_stage_state(state)
    if int(state.growth_reward_pending.get(attr, 0)) <= 0:
        return {"applied": False, "type": reward_card.get("type"), "attr": attr, "reason": "no_pending_reward"}
    result = apply_growth_reward(state, attr, reward_card, rng)
    result["attr"] = attr
    if result.get("applied"):
        state.growth_reward_pending[attr] = max(0, int(state.growth_reward_pending[attr]) - 1)
    return result


def apply_degradation_penalty(state, attr, penalty_card, rng=None):
    ensure_second_stage_state(state)
    rng = _rng(rng)
    card_type = penalty_card.get("type")
    if not is_degradation_penalty_legal(state, attr, penalty_card):
        return {"applied": False, "type": card_type}
    die = None
    if card_type in ("seal_die", "shackle_die", "add_heavy_enchant", "add_sluggish_enchant"):
        die = _random_unenchanted_die(state, attr, rng)
    elif card_type == "downgrade_die_type":
        die = rng.choice(dice_type_change_candidates(state, attr, upgrade=False))
    elif card_type == "decrease_random_face":
        die = _random_die(state, attr, rng)
    elif card_type == "decrease_chosen_face":
        die = _chosen_die(state, attr, penalty_card)
        if die is None:
            return {"applied": False, "type": card_type, "reason": "missing_die_choice"}
    if die is None:
        return {"applied": False, "type": card_type}
    if card_type == "seal_die":
        set_die_enchantment(die, ENCHANT_SEAL)
    elif card_type == "shackle_die":
        set_die_enchantment(die, ENCHANT_SHACKLE)
    elif card_type == "add_heavy_enchant":
        set_die_enchantment(die, ENCHANT_HEAVY)
    elif card_type == "add_sluggish_enchant":
        set_die_enchantment(die, ENCHANT_SLUGGISH)
    elif card_type == "downgrade_die_type":
        for _ in range(2):
            die.faces.remove(min(die.faces))
        die.faces = RevertableList(min(value, len(die.faces)) for value in die.faces)
    elif card_type in ("decrease_random_face", "decrease_chosen_face"):
        idx = _chosen_or_random_face_index(die, penalty_card, rng)
        if idx is None:
            return {"applied": False, "type": card_type}
        die.faces[idx] = max(1, die.faces[idx] - 1)
    return {"applied": True, "type": card_type}


def apply_pending_degradation_penalty(state, attr, penalty_card, rng=None):
    """Apply one selected pending degradation penalty card and consume one pending count."""
    ensure_second_stage_state(state)
    if int(state.degradation_penalty_pending.get(attr, 0)) <= 0:
        return {"applied": False, "type": penalty_card.get("type"), "attr": attr, "reason": "no_pending_penalty"}
    result = apply_degradation_penalty(state, attr, penalty_card, rng)
    result["attr"] = attr
    if result.get("applied"):
        state.degradation_penalty_pending[attr] = max(0, int(state.degradation_penalty_pending[attr]) - 1)
    return result


def set_die_enchantment(die, enchantment, temporary=False, replace=False):
    if die is None:
        return None
    if die.enchantment is not None and not replace:
        return None
    die.enchantment = enchantment
    die.temporary = bool(temporary)
    die.rest_age = 0
    return die


def clear_die_enchantment(die):
    die.enchantment = None
    die.temporary = False
    die.rest_age = 0
    return die


def process_temporary_enchant_decay(state, rng=None):
    ensure_second_stage_state(state)
    rng = _rng(rng)
    removed = []
    chances = {0: 0.30, 1: 0.60, 2: 0.90}
    for die in state.dice_pool:
        if not getattr(die, "temporary", False) or die.enchantment is None:
            continue
        chance = chances.get(getattr(die, "rest_age", 0), 1.0)
        if rng.random() < chance:
            removed.append(die.id)
            clear_die_enchantment(die)
        else:
            die.rest_age += 1
    return removed


def apply_big_failure_degradation(state, result):
    if result.rank != RESULT_BIG_FAILURE or not result.attribute:
        return 0
    amount = 1
    state_name = mood_state(state)
    if state_name in (DISEASE_MANIA, DISEASE_DEPRESSION):
        amount += 1
    if state_name in (MOOD_HIGH, DISEASE_MANIA):
        amount += 1
    return add_degradation_progress(state, result.attribute, amount)


def fog_probability(hidden_count):
    if hidden_count <= 0:
        return 0.30
    if hidden_count == 1:
        return 0.25
    return 0.20


def apply_fog_to_cards(cards, rng=None):
    rng = _rng(rng)
    result = []
    hidden = 0
    for card in cards:
        copied = dict(card)
        copied["fogged"] = rng.random() < fog_probability(hidden)
        if copied["fogged"]:
            hidden += 1
        result.append(copied)
    return ensure_at_least_one_visible(result, rng)


def ensure_at_least_one_visible(cards, rng=None):
    if cards and all(card.get("fogged") for card in cards):
        _rng(rng).choice(cards)["fogged"] = False
    return cards


def draw_visible_or_fogged_cards(pool, draw_count, rng=None):
    rng = _rng(rng)
    source = list(pool)
    if not source:
        return []
    drawn = [dict(rng.choice(source)) for _ in range(draw_count)]
    return apply_fog_to_cards(drawn, rng)


def resolve_fog_reward(state, attr, reward_card, rng=None):
    rng = _rng(rng)
    roll = rng.random()
    if roll < 0.55:
        return {"mode": "normal", "result": apply_growth_reward(state, attr, reward_card, rng)}
    if roll < 0.85:
        first = apply_growth_reward(state, attr, reward_card, rng)
        extra = None
        cards = draw_growth_reward_cards(state, attr, 1, rng)
        if cards:
            extra = apply_growth_reward(state, attr, cards[0], rng)
        return {"mode": "double", "result": first, "extra": extra}
    if roll < 0.95:
        return {"mode": "null", "result": None}
    cards = draw_degradation_penalty_cards(state, attr, 1, rng)
    penalty = apply_degradation_penalty(state, attr, cards[0], rng) if cards else None
    return {"mode": "to_penalty", "result": penalty}


def resolve_fog_penalty(state, attr, penalty_card, rng=None):
    rng = _rng(rng)
    roll = rng.random()
    if roll < 0.40:
        return {"mode": "normal", "result": apply_degradation_penalty(state, attr, penalty_card, rng)}
    if roll < 0.70:
        return {"mode": "null", "result": None}
    if roll < 0.90:
        cards = draw_growth_reward_cards(state, attr, 1, rng)
        reward = apply_growth_reward(state, attr, cards[0], rng) if cards else None
        return {"mode": "to_reward", "result": reward}
    first = apply_degradation_penalty(state, attr, penalty_card, rng)
    cards = draw_degradation_penalty_cards(state, attr, 1, rng)
    extra = apply_degradation_penalty(state, attr, cards[0], rng) if cards else None
    return {"mode": "double", "result": first, "extra": extra}


def start_turn(state, time_slot):
    ensure_second_stage_state(state)
    if time_slot == "late_night":
        time_slot = "late_night_1"
    if time_slot not in TIME_SLOT_LABELS:
        raise ValueError("Unknown time slot: {}".format(time_slot))
    state.current_time_slot = time_slot
    if time_slot in TIME_SLOTS:
        state.time_slot_index = TIME_SLOTS.index(time_slot)
    return {"time_slot": time_slot}


def resolve_action(state, schedule_spec):
    if state.current_time_slot not in TIME_SLOTS:
        return {"available": False, "reason": "not_action_round", "events": []}
    result = {"schedule": schedule_spec, "mood_delta": getattr(schedule_spec, "mood_delta", 0), "events": []}
    if getattr(schedule_spec, "check_spec", None) is not None:
        result["check"] = perform_check(state, schedule_spec.check_spec)
    return result


def end_turn(state, turn_result, rng=None):
    ensure_second_stage_state(state)
    if state.current_time_slot not in TIME_SLOTS or turn_result.get("available") is False:
        return {"available": False, "events": []}
    events = list(turn_result.get("events", []))
    check = turn_result.get("check")
    if check is not None and not check.available:
        return {"available": False, "events": []}
    if check is not None:
        apply_big_failure_degradation(state, check)
        spec = getattr(check, "spec", None)
        if spec is not None:
            events.extend(settle_check_emotions(state, spec, check, rng))
            if spec.outdoors:
                events.extend(process_environment_exposure(state, rng))
            events.extend(record_time_habit_action(state, spec.schedule_category))
    weather_delta = int(getattr(check, "weather_mood_delta_base", 0)) if check is not None else 0
    delta = apply_mood_delta(state, turn_result.get("mood_delta", 0) + weather_delta)
    events.extend(process_disease_end_turn_checks(state, rng))
    disease_event = maybe_trigger_disease_random_event(state, rng)
    if disease_event:
        events.append(disease_event)
    advance_time_slot(state)
    return {"mood_delta": delta, "mood": state.mood, "disease_state": state.disease_state, "events": events}


def advance_time_slot(state):
    """Finish one action; meals and sleep decisions require explicit choices."""
    ensure_second_stage_state(state)
    if state.current_time_slot not in TIME_SLOTS:
        raise ValueError("Only an action round can be advanced.")
    if state.current_time_slot.startswith("late_night_"):
        state.night_actions_completed = int(state.current_time_slot.rsplit("_", 1)[1])
    state.time_slot_index = TIME_SLOTS.index(state.current_time_slot) + 1
    start_turn(state, NEXT_TIME_SLOT[state.current_time_slot])
    return state.current_time_slot


def start_day(state):
    """Start the first day. Subsequent days must pass through sleep settlement."""
    ensure_second_stage_state(state)
    if state.current_time_slot is not None:
        raise ValueError("A day is already in progress.")
    state.time_slot_index = 0
    return start_turn(state, "breakfast")


def action_clock_progress(state):
    """Six regular holes; reveal optional night rounds only when entered."""
    ensure_second_stage_state(state)
    night_rounds = state.night_actions_completed
    if state.current_time_slot in TIME_SLOTS[6:]:
        night_rounds = max(night_rounds, TIME_SLOTS.index(state.current_time_slot) - 5)
    return (6 + night_rounds, state.time_slot_index)


def choose_meal(state, eat, special_event=None):
    """A meal has only eat/skip choices; authored events may hook into either."""
    ensure_second_stage_state(state)
    slot = state.current_time_slot
    if slot not in MEAL_SLOTS or not isinstance(eat, bool):
        raise ValueError("A meal requires an eat/skip choice at a meal node.")
    begin_meal_node(state)
    state.meal_choices[slot] = eat
    events = ["meal:{}:{}".format(slot, "eat" if eat else "skip")]
    if eat:
        events.extend(consume_food(state, "meal"))
    events.extend(finish_meal_node(state))
    if special_event is not None:
        events.extend(special_event(state, slot, eat) or [])
    start_turn(state, NEXT_TIME_SLOT[slot])
    return {"events": events, "time_slot": state.current_time_slot}


def choose_night_snack(state, special_event=None):
    ensure_second_stage_state(state)
    if state.current_time_slot not in SLEEP_DECISIONS:
        return {"available": False, "reason": "snack_unavailable", "events": []}
    consumed_round = state.night_actions_completed + 1
    state.night_actions_completed = consumed_round
    state.meal_choices["night_snack_{}".format(consumed_round)] = True
    events = ["meal:night_snack:eat"]
    state.meal_satiety_progress = 0
    events.extend(consume_food(state, "meal"))
    state.meal_satiety_progress = 0
    if special_event is not None:
        events.extend(special_event(state, "night_snack", True) or [])
    next_slot = "forced_sleep" if consumed_round >= 3 else "night_break_{}".format(consumed_round)
    start_turn(state, next_slot)
    return {"available": True, "events": events, "time_slot": next_slot}


def continue_night(state):
    ensure_second_stage_state(state)
    if state.current_time_slot not in SLEEP_DECISIONS:
        raise ValueError("Continuing the night requires a sleep decision.")
    slot = "late_night_{}".format(state.night_actions_completed + 1)
    return start_turn(state, slot)


def start_deep_fatigue(state):
    ensure_second_stage_state(state)
    if state.deep_fatigue is None:
        state.fatigue_history = RevertableList()
        state.good_routine = False
        state.good_routine_streak = 0
        # Acquired day's night is night one; settle after its seventh night's sleep.
        state.deep_fatigue = RevertableDict(layers=1, first_day=state.day, last_night=state.day + 6,
                                            last_late_day=None, relapsed=False)
        return ["deep_fatigue_started"]
    return []


def wake_outcome(rank, forced_coma=False):
    """Determine skipped rounds and early waking before rolling new sleep effects."""
    if rank not in (RESULT_BIG_FAILURE, RESULT_FAILURE, RESULT_SUCCESS, RESULT_HARD_SUCCESS, RESULT_BIG_SUCCESS):
        raise ValueError("A wake check result is required.")
    if forced_coma:
        if rank == RESULT_BIG_SUCCESS:
            return {"skip_morning": 0, "early": True}
        if rank == RESULT_HARD_SUCCESS:
            return {"skip_morning": 1, "early": True}
        return {"skip_morning": 2, "early": False}
    if rank in (RESULT_SUCCESS, RESULT_HARD_SUCCESS, RESULT_BIG_SUCCESS):
        return {"skip_morning": 0, "early": True}
    return {"skip_morning": 1, "early": False}


def wake_requirement(state):
    """Approved formal-POW curve; hold boundary targets outside fitted POW 6–20."""
    z = int(clamp(state.formal_attributes["pow"], 6, 20)) - 6
    # Exact half-up rounding of 15 + 1.88*z - 0.063*z*z.
    return (WAKE_REQUIREMENT * 1000 + 1880 * z - 63 * z * z + 500) // 1000


def perform_wake_check(state, requirement=None, dice_ids=None, rng=None):
    if requirement is None:
        requirement = wake_requirement(state)
    return perform_check(state, CheckSpec("pow", requirement, dice_ids, action_type=ACTION_WAKE), rng)


def drowsiness_check_modifier(state, attribute):
    """Legacy compatibility: vNext replaced drowsiness with the distraction emotion."""
    return 0


def reduce_drowsiness(state, layers=1):
    return remove_emotion(state, EMOTION_DISTRACTION, layers)


def consume_coffee(state, rng=None):
    """Coffee grants excitement after 1:1 emotion cancellation; it restores no energy."""
    ensure_second_stage_state(state)
    state.coffee_count_today = int(getattr(state, "coffee_count_today", 0)) + 1
    added = add_emotion(state, EMOTION_EXCITEMENT, 1)
    risks = (0.0, .25, .50, 1.0)
    risk = risks[min(state.coffee_count_today - 1, 3)]
    events = ["coffee", "emotion:excitement:{}".format(added)]
    if roll_probability(risk, rng):
        state.palpitations = True
        events.append("palpitations")
        if roll_probability(.5, rng):
            add_emotion(state, EMOTION_ANXIETY)
            events.append("emotion:anxiety")
    return events


def consume_alcohol(state, rng=None):
    ensure_second_stage_state(state)
    rng = _rng(rng)
    state.intoxication = min(5, int(state.intoxication) + 1)
    count = state.intoxication
    if count <= 3:
        add_emotion(state, EMOTION_CALM, 1)
    events = ["alcohol:{}".format(count)]
    if count >= 3 and rng.random() < .5:
        add_emotion(state, EMOTION_DISTRACTION, 1)
        events.append("emotion:distraction")
    factor = 1.05 if count <= 3 else 1.10
    state.mood = int(clamp(state.mood * factor, -200, 200))
    if count == 5:
        events.extend(("forced_drunk_sleep", "drunk_hospital_event_hook"))
    return events


def alcohol_check_multiplier(state, spec):
    count = int(getattr(state, "intoxication", 0))
    if count <= 0:
        return 1.0
    general = (0, -.05, -.10, -.15, -.40, -.65)[min(count, 5)]
    social = (0, .15, .30, .55, .55, .55)[min(count, 5)] if getattr(spec, "social", False) else 0
    return max(0.0, 1 + general + social)


def gain_sleep_fatigue(state):
    """Record one actual nightly receipt, after healthy-routine protection."""
    ensure_second_stage_state(state)
    state.fatigue_layers += 1
    state.fatigue_history = RevertableList(expiry for expiry in state.fatigue_history if expiry > state.day)
    events = ["sleep_fatigue_added:1"]
    if state.deep_fatigue is not None:
        state.deep_fatigue["layers"] += 1
        state.deep_fatigue["relapsed"] = True
        state.deep_fatigue["last_late_day"] = state.day - 1
        events.append("deep_fatigue_added:{}".format(state.deep_fatigue["layers"]))
    else:
        state.fatigue_history.append(state.day + 7)
        if len(state.fatigue_history) >= 3:
            events.extend(start_deep_fatigue(state))
    state.energy = min(state.energy, energy_max(state))
    return events


def settle_deep_fatigue(state, slept_day):
    disease = state.deep_fatigue
    if disease is None or slept_day < disease["last_night"]:
        return []
    state.deep_fatigue = None
    if disease["relapsed"]:
        before = state.formal_attributes["con"]
        add_formal_attribute(state, "con", -disease["layers"])
        return ["deep_fatigue_permanent_loss:{}".format(before - state.formal_attributes["con"])]
    return ["deep_fatigue_recovered"]


def finish_wake(state, result, rng=None):
    """Settle the pending wake once; ordinary action/rest counters do not advance."""
    ensure_second_stage_state(state)
    if state.current_time_slot != "wake_check" or state.sleep_pending is None:
        raise ValueError("No wake settlement is pending.")
    if isinstance(result, CheckResult):
        if not result.available:
            raise ValueError("An unavailable check cannot settle waking.")
        rank = result.rank
    else:
        rank = result
    rng = _rng(rng)
    pending = state.sleep_pending
    outcome = wake_outcome(rank, pending["forced_coma"])
    # Older saves at the waking node did not preserve the voluntary night count.
    nights = pending.get("night_actions", 3 if pending["forced_coma"] else 1)
    distraction = sum(rng.random() < .5 for _ in range(nights)) if outcome["early"] else 0
    if outcome["early"] and nights == 3:
        distraction = max(1, distraction)
    outcome.update(fatigue=1, distraction=distraction, events=[])
    if state.good_routine:
        shield = rng.random()
        if shield < .75:
            outcome.update(fatigue=0, distraction=0)
            outcome["events"].append("healthy_routine_blocked")
        if shield >= .25:
            state.good_routine = False
            state.good_routine_streak = 0
            outcome["events"].append("good_routine_spent")
    if outcome["fatigue"]:
        outcome["events"].extend(gain_sleep_fatigue(state))
    if outcome["distraction"]:
        add_emotion(state, EMOTION_DISTRACTION, outcome["distraction"])
        outcome["events"].append("emotion:distraction:{}".format(outcome["distraction"]))
    # The final late night belongs to the existing disease before it expires.
    outcome["events"].extend(settle_deep_fatigue(state, pending.get("slept_day", state.day - 1)))
    if is_dead(state):
        state.sleep_pending = None
        outcome["events"].append("death")
        return outcome
    state.energy = min(state.energy, energy_max(state))
    if isinstance(result, CheckResult) and result.rank == RESULT_BIG_FAILURE:
        apply_big_failure_degradation(state, result)
        outcome["events"].append("wake_big_failure")
    state.sleep_pending = None
    skip = outcome["skip_morning"]
    if skip:
        state.meal_choices["breakfast"] = False
    state.time_slot_index = skip
    outcome["events"].extend(settle_morning_mood(state, rng))
    outcome["events"].extend(settle_environment_diseases_morning(state, rng))
    outcome["events"].extend(settle_injuries_morning(state, rng))
    outcome["events"].extend(update_drug_dependence_day(state))
    generate_weather(state, rng=daily_weather_rng(state))
    start_turn(state, ("breakfast", "morning_2", "lunch")[skip])
    return outcome


def perform_sleep_quality_check(state, rng=None):
    """Special CON check: all usable dice, no attribute modifier and no energy cost."""
    ensure_second_stage_state(state)
    dice = usable_dice(state, "con")
    if not dice:
        return CheckResult(available=False, reason="no_usable_con_die", attribute="con")
    rng = _rng(rng)
    rainy = state.current_weather in (WEATHER_LIGHT_RAIN, WEATHER_HEAVY_RAIN, WEATHER_THUNDERSTORM, WEATHER_STORM)
    advantage_count = 1 if rainy else 0
    disadvantage_count = len(state.environment_diseases)
    net = advantage_count - disadvantage_count
    rolls = roll_dice(dice, rng, "bonus" if net > 0 else "penalty" if net < 0 else None)
    dice_total = sum(item["value"] for item in rolls)
    multiplier = 1.0 + .15 * emotion_layers(state, EMOTION_DISTRACTION) - .15 * emotion_layers(state, EMOTION_EXCITEMENT)
    if int(getattr(state, "trazodone_sleep_bonus_day", -1)) == state.day:
        multiplier += .15
    if state.current_weather in (WEATHER_THUNDERSTORM, WEATHER_STORM):
        multiplier -= .25
    total = dice_total * max(0.0, multiplier)
    requirement = int(math.floor(dice_max_total(dice) / 2.0))
    rank = result_rank(total, requirement, dice_total, dice)
    if rank in (RESULT_BIG_FAILURE, RESULT_FAILURE):
        quality = SLEEP_QUALITY_POOR
    elif rank == RESULT_SUCCESS:
        quality = SLEEP_QUALITY_GOOD
    else:
        quality = SLEEP_QUALITY_EXCELLENT
    result = CheckResult(available=True, attribute="con", requirement=requirement,
        base_requirement=requirement, attribute_modifier=0, dice_multiplier=multiplier,
        dice_total=dice_total, total=total, rank=rank, success=quality != SLEEP_QUALITY_POOR,
        energy_cost=0, dice_ids=[die.id for die in dice], dice_results=rolls, dice_count=len(dice))
    result.quality = quality
    result.advantage_count = advantage_count
    result.disadvantage_count = disadvantage_count
    return result


def restore_sleep_energy(state, quality, night_main):
    before = int(state.energy)
    if night_main:
        state.next_day_energy_cap_bonus = 1 if quality == SLEEP_QUALITY_EXCELLENT else 0
    maximum = energy_max(state)
    if quality == SLEEP_QUALITY_POOR:
        state.energy = min(maximum, before + int(math.floor(maximum * .5)))
    else:
        state.energy = maximum
    return {"before": before, "after": int(state.energy), "maximum": maximum}


def _downgrade_sleep_quality(quality):
    if quality == SLEEP_QUALITY_EXCELLENT:
        return SLEEP_QUALITY_GOOD
    return SLEEP_QUALITY_POOR


def begin_daytime_drunk_sleep(state, rng=None):
    """Complete daytime sleep; night-only settlement is deliberately excluded."""
    ensure_second_stage_state(state)
    if state.intoxication < 2 or state.current_time_slot not in TIME_SLOTS[:6]:
        return {"available": False, "reason": "daytime_drunk_sleep_unavailable", "events": []}
    result = perform_sleep_quality_check(state, rng)
    if not result.available:
        return {"available": False, "reason": result.reason, "events": []}
    quality = _downgrade_sleep_quality(result.quality)
    recovery = restore_sleep_energy(state, quality, night_main=False)
    events = ["daytime_drunk_sleep", "sleep_quality:{}".format(quality)]
    events.extend(clear_sleep_emotions(state))
    events.extend(clear_training_fatigue_on_sleep(state))
    remaining = 3
    while remaining > 0 and state.current_time_slot in TIME_SLOTS[:6]:
        remaining -= 1
        next_slot = NEXT_TIME_SLOT[state.current_time_slot]
        while next_slot in MEAL_SLOTS:
            state.current_time_slot = next_slot
            begin_meal_node(state)
            state.meal_choices[next_slot] = False
            events.append("meal:{}:skip".format(next_slot))
            events.extend(finish_meal_node(state))
            next_slot = NEXT_TIME_SLOT[next_slot]
        start_turn(state, next_slot)
    state.daytime_sleep_pending = RevertableDict(quality=quality) if state.current_time_slot in SLEEP_DECISIONS + ("forced_sleep",) else None
    return {"available": True, "sleep_quality": quality, "quality_check": result,
            "energy_before": recovery["before"], "energy_after": recovery["after"],
            "can_continue_to_next_day": state.daytime_sleep_pending is not None, "events": events}


def continue_daytime_sleep_to_next_day(state, rng=None):
    """Finish the same sleep at night without rolling quality a second time."""
    ensure_second_stage_state(state)
    if state.daytime_sleep_pending is None:
        return {"available": False, "reason": "no_daytime_sleep_pending", "events": []}
    quality = state.daytime_sleep_pending["quality"]
    state.daytime_sleep_pending = None
    events = end_day(state, rng, on_time=False, quality=quality)["events"]
    state.next_day_energy_cap_bonus = 1 if quality == SLEEP_QUALITY_EXCELLENT else 0
    events.extend(clear_sleep_emotions(state, night_main=True))
    state.day += 1
    state.weekday = 1 + (state.weekday % 7)
    state.meal_choices = RevertableDict()
    state.medicine_taken_today = RevertableDict()
    state.coffee_count_today = 0
    events.extend(settle_morning_mood(state, rng))
    events.extend(settle_environment_diseases_morning(state, rng))
    events.extend(settle_injuries_morning(state, rng))
    events.extend(update_drug_dependence_day(state))
    generate_weather(state, rng=daily_weather_rng(state))
    start_turn(state, "breakfast")
    return {"available": True, "events": events}


def begin_sleep(state, rng=None):
    """Settle the old night's rest once, then wait for a free wake check if late."""
    ensure_second_stage_state(state)
    if is_dead(state):
        return {"available": False, "reason": "dead", "events": ["death"]}
    if state.current_time_slot not in SLEEP_DECISIONS + ("forced_sleep",):
        return {"available": False, "reason": "not_sleep_time", "events": []}
    on_time = state.current_time_slot == "sleep_decision"
    forced_coma = state.current_time_slot == "forced_sleep"
    night_actions = state.night_actions_completed
    slept_day = state.day
    quality_result = perform_sleep_quality_check(state, rng)
    if not quality_result.available:
        return {"available": False, "reason": quality_result.reason, "events": []}
    quality = quality_result.quality
    events = ["sleep", "sleep_quality:{}".format(quality)]
    events.extend(end_day(state, rng, on_time=on_time, quality=quality)["events"])
    recovery = restore_sleep_energy(state, quality, night_main=True)
    events.extend(clear_sleep_emotions(state, night_main=True))
    if is_dead(state):
        return {"available": True, "needs_wake_check": False, "events": events + ["death"]}
    events.extend(clear_training_fatigue_on_sleep(state))
    state.day += 1
    state.weekday = 1 + (state.weekday % 7)
    state.fatigue_history = RevertableList(expiry for expiry in state.fatigue_history if expiry > state.day)
    state.meal_choices = RevertableDict()
    state.medicine_taken_today = RevertableDict()
    state.coffee_count_today = 0
    state.night_actions_completed = 0
    state.night_snack_eaten = False
    state.time_slot_index = 0
    if on_time:
        events.extend(settle_morning_mood(state, rng))
        events.extend(settle_environment_diseases_morning(state, rng))
        events.extend(settle_injuries_morning(state, rng))
        events.extend(update_drug_dependence_day(state))
        generate_weather(state, rng=daily_weather_rng(state))
        start_turn(state, "breakfast")
    else:
        state.sleep_pending = RevertableDict(forced_coma=forced_coma, night_actions=night_actions, slept_day=slept_day)
        start_turn(state, "wake_check")
    events.append("energy_restored:{}:{}".format(recovery["before"], recovery["after"]))
    return {"available": True, "needs_wake_check": not on_time,
            "sleep_quality": quality, "quality_check": quality_result,
            "energy_before": recovery["before"], "energy_after": state.energy, "events": events}


def end_day(state, rng=None, on_time=None, quality=SLEEP_QUALITY_GOOD):
    ensure_second_stage_state(state)
    if is_dead(state):
        return {"events": ["death"]}
    events = ["sleep_recovery", "small_rest"]
    apply_sleep_recovery(state, quality)
    events.extend(process_small_rest(state, rng))
    # Night-only recovery: daytime rest and standalone growth settlement do not heal.
    restored = heal_health(state, health_max(state) / 40.0)
    if restored:
        events.append("health_restored:{:g}".format(restored))
    if on_time is None:
        on_time = state.current_time_slot == "sleep_decision"
    recovering = state.deep_fatigue is not None
    if on_time:
        if state.fatigue_layers:
            events.append("sleep_fatigue_cleared")
        state.fatigue_layers = 0
        state.good_routine_streak = 0 if recovering else state.good_routine_streak + 1
    else:
        state.good_routine_streak = 0
    if state.ember is not None and state.disease_state != DISEASE_DEPRESSION:
        state.ember = max(0, state.ember - 1)
        events.append("ember_decay:{}".format(state.ember))
    if state.bipolar_ember is not None:
        if state.disease_state in (DISEASE_MANIA, DISEASE_DEPRESSION):
            state.bipolar_ember = 180
        else:
            state.bipolar_ember = max(0, state.bipolar_ember - 1)
        events.append("bipolar_ember_decay:{}".format(state.bipolar_ember))
    if state.hunger_level > 0:
        state.hunger_level -= 1
    elif state.hunger_level < 0:
        state.hunger_level = 0
    events.extend(refresh_time_habits(state))
    events.extend(settle_nutrition_diseases(state))
    # Sunday large rest follows the complete daily small rest.
    events.extend(end_week_if_needed(state, rng)["events"])
    if on_time:
        events.extend(settle_deep_fatigue(state, state.day))
    # Late-night disease expiry waits for fatigue/protection at the waking node.
    if state.good_routine_streak >= 7:
        state.good_routine = True
    return {"events": events}


def end_week_if_needed(state, rng=None):
    ensure_second_stage_state(state)
    events = []
    if state.day % 7 == 0 or state.weekday == 7:
        events.append("large_rest")
        events.extend(process_large_rest(state, rng))
        state.late_night_energy_schedule_week_count = 0
    return {"events": events}
