"""Eight-slot layout and sessions; medicine effects remain in rm_core."""
import math
from game.systems import rm_core as core

SLOT_COUNT = 8
INITIAL_SLOTS = ("venlafaxine", "trazodone", "alprazolam", None, None, None, None, None)
INITIAL_RECOMMENDATIONS = {"morning": ("venlafaxine",), "evening": ("trazodone",)}


def ensure_state(state):
    # Old saves retain their stock, including assigned but exhausted medicines.
    if not hasattr(state, "pillbox_slots"):
        owned = [drug for drug in INITIAL_SLOTS if drug in state.medicine_counts]
        owned += [drug for drug in core.PSYCHIATRIC_MEDICINES
                  if drug in state.medicine_counts and drug not in owned]
        state.pillbox_slots = core.RevertableList((owned + [None] * 8)[:8])
    elif not isinstance(state.pillbox_slots, core.RevertableList):
        state.pillbox_slots = core.RevertableList(state.pillbox_slots)
    if not hasattr(state, "current_rotation_step"):
        state.current_rotation_step = 0
    if not hasattr(state, "recommended_drugs"):
        state.recommended_drugs = {period: [drug for drug in drugs if drug in state.pillbox_slots]
                                   for period, drugs in INITIAL_RECOMMENDATIONS.items()}
    for name in ("recommended_drugs", "pillbox_node_days", "pillbox_last_session"):
        value = getattr(state, name, {})
        if not isinstance(value, core.RevertableDict):
            value = core.RevertableDict(value)
        setattr(state, name, value)
    for period, drugs in state.recommended_drugs.items():
        if not isinstance(drugs, core.RevertableList):
            state.recommended_drugs[period] = core.RevertableList(drugs)


def set_prescription(state, slots, recommendations):
    if len(slots) != 8 or any(drug is not None and drug not in core.DRUG_DEFINITIONS for drug in slots):
        raise ValueError("A pillbox requires eight known medicine/empty slots")
    if any(period not in ("morning", "evening") or any(drug not in slots for drug in drugs)
           for period, drugs in recommendations.items()):
        raise ValueError("Recommendations must refer to assigned medicines")
    state.pillbox_slots = core.RevertableList(slots)
    state.recommended_drugs = core.RevertableDict(
        (period, core.RevertableList(drugs)) for period, drugs in recommendations.items())
    ensure_state(state)


def selected_slot(step):
    return (-int(step)) % SLOT_COUNT


def shortest_turn(step, slot):
    return ((-int(slot) - int(step) + 4) % SLOT_COUNT) - 4


def slot_position(slot, radius=280):
    angle = math.radians(slot * 45)
    return (round(510 - radius * math.sin(angle)), round(510 + radius * math.cos(angle)))


def selection(state, context):
    slot = selected_slot(state.current_rotation_step)
    drug = state.pillbox_slots[slot]
    definition = core.DRUG_DEFINITIONS.get(drug)
    return dict(slot=slot, drug=drug, definition=definition,
                count=state.medicine_counts.get(drug, 0),
                taken=state.medicine_taken_today.get(drug, 0),
                recommended=drug is not None and drug in state.recommended_drugs.get(context, ()))


def take_selected(state, context, confirm_repeat=False, rng=None):
    item = selection(state, context)
    if not item["definition"] or not item["definition"]["enabled"]:
        return dict(available=False, reason="empty_slot", events=[])
    handler = item["definition"]["repeat_handler" if confirm_repeat else "effect_handler"]
    return handler(state, item["drug"], rng=rng, confirm_repeat=confirm_repeat)


def finish_session(state, context, before):
    taken = {drug: count - before.get(drug, 0) for drug, count in state.medicine_taken_today.items()
             if count > before.get(drug, 0)}
    state.pillbox_last_session = core.RevertableDict(context=context, day=state.day,
                                                   taken=core.RevertableDict(taken))
    if context in ("morning", "evening"):
        state.pillbox_node_days[context] = state.day
    return state.pillbox_last_session


def due_context(state):
    if not any(state.pillbox_slots):
        return None
    slot = state.current_time_slot
    context = ("morning" if slot in ("breakfast", "morning_1", "morning_2", "lunch") else
               "evening" if slot in core.SLEEP_DECISIONS + ("forced_sleep",) else None)
    return context if context and state.pillbox_node_days.get(context) != state.day else None
