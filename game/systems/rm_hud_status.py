"""HUD-only status projection and measured flow layout. Never changes game rules."""
from copy import deepcopy
import re
from . import rm_core


GROUPS = (("treatment", "病程 / 治疗"), ("current", "当前状态"),
          ("injury", "伤病"), ("life", "生活 / 特质"))
GROUP_NAMES = dict(GROUPS)
MANUAL_ORDER = (
    "余烬", "余烬·双相", "电残留", "药物依赖", "文拉法辛", "曲唑酮", "碳酸锂", "阿立哌唑", "拉莫三嗪", "阿普唑仑",
    "喜悦", "悲伤", "镇定", "焦虑", "兴奋", "涣散", "愤怒", "恐惧", "自信", "怀疑",
    "疲劳", "训练负荷", "饥饿", "饱腹", "心悸", "微醺", "醉酒",
    "骨折", "苦痛与伤痕", "深度疲劳", "扭伤", "肌肉酸痛", "营养不良", "消化不良", "中暑", "感冒",
    "健康作息", "精力充沛", "优质睡眠",
)
TREATMENT_NAMES = set(MANUAL_ORDER[:10])
CURRENT_NAMES = set(MANUAL_ORDER[10:27])
INJURY_NAMES = set(MANUAL_ORDER[27:36])
ENVIRONMENT_CATEGORIES = {"weather", "temperature", "location", "environment"}
MOOD_IDS = {"mood_stable", "mood_high", "mood_low", "mood_mania", "mood_depression"}
TEMPERATURE_LABELS = dict(extreme_cold="极寒", cold="寒冷", temperate="适温", hot="炎热", extreme_hot="酷热")
LOCATIONS = dict(doctor_office="医院", nurse_station="医院", bathroom="医院",
                 hospital_corridor="医院", hospital_entrance="医院", train_station="车站",
                 train_platform="站台", train_carriage="列车", home="家", school="学校")


def display_count(row):
    value = row.get("display_count")
    if value is None:
        value = row.get("value_text", "")
    match = re.search(r"[-+]?\d+", str(value))
    return str(abs(int(match.group()))) if match else "1"


def group_for(row, name):
    if row.get("group") in GROUP_NAMES:
        return row["group"]
    for key, title in GROUPS:
        if row.get("group") == title:
            return key
    key, category = row.get("id", ""), row.get("category")
    if name in TREATMENT_NAMES or key.startswith(("pending_", "disease_")):
        return "treatment"
    if name.split("·")[0] in INJURY_NAMES or category in ("injury", "disease"):
        return "injury"
    if name in CURRENT_NAMES or category in ("emotion", "physiological") or key == "intoxication":
        return "current"
    if category == "medication":
        return "treatment"
    return "life"


def normalize(rows):
    result = []
    merged = {}
    for source in rows:
        key = str(source.get("id") or "story_" + source.get("display_name", source.get("label", "")))
        merged.setdefault(key, {}).update(source)
    for key, row in merged.items():
        if not row.get("visible_in_hud", True) or row.get("category") in ENVIRONMENT_CATEGORIES or key in ENVIRONMENT_CATEGORIES | MOOD_IDS:
            continue
        if key.startswith("test_growth_") and row.get("value_text") == "0/6":
            continue
        name = row.get("display_name", row.get("label", ""))
        if not name:
            continue
        if key.startswith("pending_"):
            name = rm_core.MEDICINE_LABELS.get(key[8:], name)
        if key == "hunger" and str(row.get("value_text", "")).startswith("×-"):
            name = "饱腹"
        value = row.get("value_text", "")
        detail = "{}{}\n{}".format(name, " " + value if value else "", row.get("tooltip", "")).strip()
        result.append(dict(id=key, group=group_for(row, name), display_name=name,
                           display_count=display_count(row), visible_in_hud=True,
                           priority=row.get("priority", MANUAL_ORDER.index(name) if name in MANUAL_ORDER else 100),
                           tooltip=detail))
    # IDs break priority ties, not current container width or dictionary insertion order.
    result.sort(key=lambda item: (item["priority"], item["id"]))
    return [dict(id=key, title=title, items=[item for item in result if item["group"] == key])
            for key, title in GROUPS if any(item["group"] == key for item in result)]


def snapshot(character, extra_rows=()):
    # The core summary upgrades legacy save defaults; do that on a copy, not during screen prediction.
    state = deepcopy(character)
    rows = rm_core.status_summary(state)
    if getattr(state, "trazodone_sleep_bonus_day", None) == state.day:
        rows.append(dict(id="trazodone_sleep", label="曲唑酮", category="medication",
                         tooltip="本日仍有睡眠恢复加成；不代表所有服药效果都持续存在。"))
    periods = dict(morning="上午", afternoon="下午", evening="晚上")
    categories = dict(training="训练", study="学习", social="社交", rest="休息", sport="运动")
    for key, active in getattr(state, "time_habits", {}).items():
        if active:
            period, category = key.split(":", 1)
            name = "{}{}习惯".format(periods.get(period, period), categories.get(category, category))
            rows.append(dict(id="time_habit_" + key, label=name, group="life", priority=130,
                             tooltip="在对应时段进行同类日程时，精力消耗减少1（仍至少消耗1）。"))
    rows.extend(extra_rows)
    return normalize(rows)


def environment(character, background=(), location="", extra_rows=()):
    weather = getattr(character, "current_weather", None)
    temperature = getattr(character, "current_temperature", None)
    parts = []
    if weather in rm_core.WEATHER_LABELS:
        parts.append(rm_core.WEATHER_LABELS[weather])
    if temperature is not None:
        parts.append(TEMPERATURE_LABELS[rm_core.temperature_band(temperature)])
    if not parts:
        parts = [row.get("display_name", row.get("label", "")) for row in extra_rows
                 if row.get("category") in ("weather", "temperature") or row.get("id") in ("weather", "temperature")]
    if not location:
        location = next((row.get("display_name", row.get("label", "")) for row in extra_rows
                         if row.get("category") == "location" or row.get("id") == "location"), "")
    if not location:
        location = next((LOCATIONS[attr] for attr in background if attr in LOCATIONS), "")
    return [line for line in (" · ".join(filter(None, parts)), location) if line]


def fit_name(name, available, measure):
    """Ellipsize only a single oversize label; keep the full name in its detail."""
    if measure(name) <= available:
        return name
    low, high = 0, len(name)
    while low < high:
        middle = (low + high + 1) // 2
        if measure(name[:middle] + "…") <= available:
            low = middle
        else:
            high = middle - 1
    return name[:low] + "…"


def flow(groups, width, measure_name, measure_count, height_budget=600):
    """Greedy pixel-width flow. All geometry is QHD; no character-count columns."""
    prepared = []
    for group in groups:
        lines, line, used = [], [], 0
        for item in group["items"]:
            count_width = measure_count(item["display_count"])
            name = fit_name(item["display_name"], width - count_width - 28, measure_name)
            name_width = measure_name(name)
            item_width = name_width + count_width + 28
            if line and used + 8 + item_width > width:
                lines.append(line)
                line, used = [], 0
            x = used + (8 if line else 0)
            line.append(dict(item, text=name, width=item_width, name_width=name_width, x=x))
            used = x + item_width
        if line:
            lines.append(line)
        prepared.append(dict(group, lines=lines))
    # Preserve at least one row per non-empty group before granting extra rows.
    caps = [1] * len(prepared)
    total = 40 + 40 + sum(28 + 36 for _ in prepared) + max(0, len(prepared) - 1) * 12
    for _ in range(2):
        for i, group in enumerate(prepared):
            if caps[i] < len(group["lines"]) and total + 42 <= height_budget:
                caps[i] += 1
                total += 42
    y, hidden, layouts = 40, 0, []
    for group, cap in zip(prepared, caps):
        visible = []
        for row_number, line in enumerate(group["lines"][:cap]):
            visible.extend(dict(item, y=28 + row_number * 42) for item in line)
        overflow = None
        if len(visible) < len(group["items"]):
            marker_width = measure_name("...") + 20
            last_y = 28 + (cap - 1) * 42
            # Reserve the marker inside the last allowed row; displaced states
            # remain part of the stable hidden suffix and its count.
            while visible and visible[-1]["y"] == last_y and visible[-1]["x"] + visible[-1]["width"] + 8 + marker_width > width:
                visible.pop()
            marker_x = visible[-1]["x"] + visible[-1]["width"] + 8 if visible and visible[-1]["y"] == last_y else 0
            overflow = dict(text="...", display_count="", name_width=measure_name("..."),
                            width=marker_width, x=marker_x, y=last_y)
        omitted = len(group["items"]) - len(visible)
        hidden += omitted
        height = 28 + cap * 42 - 6
        layouts.append(dict(id=group["id"], title=group["title"], items=visible, y=y,
                            rows=cap, hidden=omitted, height=height, overflow=overflow))
        y += height + 12
    return dict(groups=layouts, hidden=hidden, footer_y=max(40, y - 4), width=width)
