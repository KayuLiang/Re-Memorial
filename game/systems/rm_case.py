"""Case-file presentation only. Rules and their explanations remain in rm_core."""
from copy import deepcopy
from . import rm_core

ATTRIBUTES = ("str", "dex", "con", "int", "pow")
LABELS = dict(zip(ATTRIBUTES, ("力量", "敏捷", "体质", "智力", "意志")))
FILTERS = (("all", "全部"), ("owned", "当前拥有"), ("unlocked", "已解锁"), ("locked", "未解锁"))
MOOD_DESCRIPTIONS = {
    "stable": "没有病程时，Mood 在 −60 至 60 之间显示为平稳。",
    "high": "没有病程时，Mood 高于 60 显示为高涨。",
    "low": "没有病程时，Mood 低于 −60 显示为低落。",
    "mania": "处于躁狂病程。病程状态优先于 Mood 区间显示。",
    "depression": "处于抑郁病程。病程状态优先于 Mood 区间显示。",
}


def snapshot(character, extra_rows=()):
    # The existing summary fills legacy save defaults. Do that on a copy,
    # never on the live character while reading a UI or predicting a screen.
    summary = rm_core.character_summary(deepcopy(character))
    rows = [dict(row) for row in summary["statuses"]
            if not (row["id"].startswith("test_growth_") and row["value_text"] == "0/6")]
    mood = summary["mood"]
    rows.insert(0, dict(id="mood_" + mood["state"], label=mood["label"],
                        value_text="Mood：{}".format(mood["value"]), tooltip=MOOD_DESCRIPTIONS[mood["state"]]))
    disease = summary["disease"]
    if disease["state"] != rm_core.DISEASE_NONE:
        rows.append(dict(id="disease_" + disease["state"], label=disease["label"],
                         value_text="持续 {} 轮".format(disease["turns"]), tooltip=MOOD_DESCRIPTIONS[disease["state"]]))
    for index, row in enumerate(extra_rows):
        item = dict(row)
        item.setdefault("id", "transient_{}".format(index))
        item.setdefault("value_text", "")
        item.setdefault("tooltip", "")
        rows.append(item)
    summary["statuses"] = rows
    return summary


def remember(history, rows):
    result = dict(history)
    for row in rows:
        if not row["id"].startswith("transient_"):
            result[row["id"]] = dict(row)
    return result


def catalog_ids():
    """Only finite effect types already defined by the current game rules."""
    ids = ["mood_" + state for state in rm_core.MOOD_LABELS]
    ids += ["disease_" + state for state in rm_core.DISEASE_LABELS if state != rm_core.DISEASE_NONE]
    for attribute in ATTRIBUTES:
        ids.extend(prefix + attribute for prefix in ("dice_growth_", "growth_reward_pending_", "degradation_", "degradation_penalty_pending_"))
        ids.append("attr_value_{}_1".format(attribute))
    ids.extend("test_growth_" + attribute for attribute in rm_core.TEST_TRAINING_ATTRIBUTES)
    ids.extend("training_fatigue_" + schedule for schedule in rm_core.TEST_TRAINING_SCHEDULE_ATTRIBUTES)
    return ids


def dictionary_rows(current, history, filter_key="all"):
    owned = {row["id"]: row for row in current}
    unlocked = dict(history)
    unlocked.update(owned)
    ids = list(owned) + [key for key in unlocked if key not in owned]
    ids += [key for key in catalog_ids() if key not in unlocked]
    result = []
    for key in ids:
        is_owned, is_unlocked = key in owned, key in unlocked
        if filter_key == "owned" and not is_owned:
            continue
        if filter_key == "unlocked" and not is_unlocked:
            continue
        if filter_key == "locked" and is_unlocked:
            continue
        item = dict(unlocked.get(key, dict(id=key, label="？", value_text="", tooltip="遇到这个状态后，可在这里查阅说明。")))
        item.update(owned=is_owned, unlocked=is_unlocked,
                    badge="当前拥有" if is_owned else "已解锁" if is_unlocked else "未解锁")
        result.append(item)
    return result


def page_rows(rows, page, size=8):
    count = max(1, (len(rows) + size - 1) // size)
    page = max(0, min(page, count - 1))
    return rows[page * size:(page + 1) * size], page, count


def radar_fractions(attributes):
    return [max(0.0, min(1.0, attributes[key]["effective"] / 20.0)) for key in ATTRIBUTES]
