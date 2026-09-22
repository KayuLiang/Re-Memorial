"""Read-only presentation of physical dice. No rolls, rewards or state writes."""
from collections import Counter
from . import rm_core
LABELS = {"str":"力量", "dex":"灵巧", "con":"体质", "int":"智力", "pow":"意志"}
ORDER = ("str","dex","con","int","pow")

def rows(character, attribute="all", order="attribute", enchantment="all"):
    result = []
    totals = Counter(d.attribute for d in character.dice_pool)
    serials = Counter()
    for die in character.dice_pool:
        serials[die.attribute] += 1
        if attribute != "all" and die.attribute != attribute:
            continue
        if enchantment != "all" and bool(die.enchantment) != (enchantment == "enchanted"):
            continue
        row = rm_core.dice_summary(die)
        row.update(label=LABELS[die.attribute], sides=len(die.faces), serial=serials[die.attribute], total=totals[die.attribute])
        result.append(row)
    key = {"attribute": lambda d: (ORDER.index(d["attribute"]), d["serial"]),
           "sides": lambda d: (d["sides"], d["attribute"], d["serial"]),
           "mean": lambda d: (-d["expectation"], d["attribute"], d["serial"])}[order]
    return sorted(result, key=key)

def preview_indices(faces):
    """D4/6: every physical face. Larger dice: five concrete faces + ellipsis."""
    if len(faces) <= 6:
        return list(range(len(faces)))
    ranked = sorted(range(len(faces)), key=lambda i: (faces[i], i))
    return [ranked[round(i*(len(ranked)-1)/4)] for i in range(5)] + [None]

def distribution(faces):
    counts = Counter(faces)
    values = sorted(set(range(1,len(faces)+1)) | set(faces))
    return [(value, counts[value], counts[value]/float(len(faces))) for value in values]

def visible_faces(faces, offset=0):
    count = min(len(faces), 9) if len(faces) > 12 else len(faces)
    offset = max(0, min(offset, len(faces)-count))
    return list(range(offset, offset+count))

def growth(character):
    return [(a, LABELS[a], int(character.dice_growth_progress.get(a, 0)),
             int(character.growth_reward_pending.get(a, 0))) for a in ORDER]
