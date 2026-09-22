"""Offline growth reference: actual game rewards, exact per-pool roll PMFs.

Run from the project root. No save files or runtime balance rules are changed.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random
import sqlite3
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from game.systems import rm_core as rm

PROBABILITIES = (.2, .3, .4, .5, .6, .7, .8)
SCENARIOS = [("pow", "pow", 6), ("con", "con", 6)] + [
    ("allocated_" + str(n), "str", n) for n in range(1, 7)]
POLICIES = ("random", "greedy")
MAX_SCORE = 60


def roll_mean(faces, enchantment=None):
    if enchantment == rm.ENCHANT_SWIFT:
        return sum((2*i + 1)*v for i, v in enumerate(sorted(faces))) / len(faces)**2
    if enchantment == rm.ENCHANT_SLUGGISH:
        return sum((2*(len(faces)-i)-1)*v for i, v in enumerate(sorted(faces))) / len(faces)**2
    return sum(faces) / len(faces)


def die_pmf(die):
    p = np.bincount(die.faces, minlength=len(die.faces)+1).astype(float) / len(die.faces)
    cdf = np.cumsum(p)
    if die.enchantment == rm.ENCHANT_SWIFT:
        p = np.diff(np.r_[0., cdf**2])
    elif die.enchantment == rm.ENCHANT_SLUGGISH:
        p = np.diff(np.r_[0., 1-(1-cdf)**2])
    return p


def pool_pmf(dice):
    chosen = sorted(dice, key=lambda d: -roll_mean(d.faces, d.enchantment))[:3]
    p = np.array([1.])
    for die in chosen:
        p = np.convolve(p, die_pmf(die))
    return np.pad(p, (0, MAX_SCORE+1-len(p)))


def top_three(means):
    return sum(sorted(means, reverse=True)[:3])


def choice_targets(state, attr, card):
    return rm.growth_reward_dice_candidates(state, attr, card)


def random_choice(state, attr, cards, rng):
    card = dict(rng.choice(cards))
    if rm.card_needs_die_choice(card):
        die = rng.choice(choice_targets(state, attr, card))
        card['die_id'] = die.id
        if rm.card_needs_face_choice(card):
            card['face_index'] = rng.choice(rm.growth_reward_face_indices(die, card))
    return card


def greedy_choice(state, attr, cards):
    """Exact one-step expected top-three score, before hidden random outcomes.

    Rewards with random die/face targets average over the same candidates as
    the core. Chosen targets maximize over player choices, not random ones.
    """
    dice = state.dice_for(attr)
    means = [roll_mean(d.faces, d.enchantment) for d in dice]

    def changed_score(index, new_mean):
        return top_three(means[:index] + [new_mean] + means[index+1:])

    best_score, best_card = -math.inf, None
    for original in cards:
        card = dict(original)
        kind = card['type']
        if kind == 'add_new_die':
            score = top_three(means + [card['face_total']/card['die_sides']])
        elif kind == 'add_light_enchant':
            score = top_three(means)
        elif kind == 'add_swift_enchant':
            scores = [changed_score(i, roll_mean(d.faces, rm.ENCHANT_SWIFT))
                      for i, d in enumerate(dice) if d.enchantment is None]
            score = sum(scores)/len(scores)
        elif kind.startswith('upgrade_'):
            candidates = rm.dice_type_change_candidates(state, attr)
            outcomes = [(changed_score(i, roll_mean(d.faces + [min(d.faces), max(d.faces)], d.enchantment)), d.id)
                        for i, d in enumerate(dice) if d in candidates]
            if kind == 'upgrade_chosen_die_type':
                score, card['die_id'] = max(outcomes, key=lambda item: item[0])
            else:
                score = sum(value for value, _ in outcomes)/len(outcomes)
        elif kind.startswith(('replace_', 'increase_')):
            chosen_die = rm.card_needs_die_choice(card)
            chosen_face = rm.card_needs_face_choice(card)
            outcomes = []
            candidates = choice_targets(state, attr, card)
            for i, die in enumerate(dice):
                if die not in candidates:
                    continue
                faces = die.faces
                face_scores = []
                indices = rm.growth_reward_face_indices(die, card)
                for j in indices:
                    old = faces[j]
                    value = rm.replacement_face_value(card, die) if kind.startswith('replace_') else old + card['increase_amount']
                    value = min(len(faces), max(1, value))
                    if die.enchantment == rm.ENCHANT_SWIFT:
                        new_mean = roll_mean(faces[:j]+[value]+faces[j+1:], die.enchantment)
                    else:
                        new_mean = means[i] + (value-old)/len(faces)
                    face_scores.append(changed_score(i, new_mean))
                best_index = max(range(len(indices)), key=face_scores.__getitem__) if chosen_face else None
                face_index = indices[best_index] if chosen_face else None
                die_score = face_scores[best_index] if chosen_face else sum(face_scores)/len(indices)
                outcomes.append((die_score, die.id, face_index))
            if chosen_die:
                score, card['die_id'], face_index = max(outcomes, key=lambda item: item[0])
                if chosen_face:
                    card['face_index'] = face_index
            else:
                score = sum(item[0] for item in outcomes)/len(outcomes)
        else:
            raise ValueError('Unexpected reward in growth-only scenario: ' + kind)
        if score > best_score + 1e-12:
            best_score, best_card = score, card
    return best_card, best_score


def initial_state(attr, initial, seed):
    allocation = {'str': initial, 'dex': 1, 'int': 7-initial} if attr == 'str' else None
    return rm.create_initial_character(allocation, random.Random(seed))


def simulate(scenario, policy, trials, max_attribute, seed):
    name, attr, initial = scenario
    rewards = max_attribute - initial
    attributes = np.arange(initial, max_attribute+1)
    modifiers = []
    pmf_sum = np.zeros((rewards+1, MAX_SCORE+1))
    survival_sq = np.zeros_like(pmf_sum)
    expectations = np.zeros((trials, rewards+1))
    dice_count = np.zeros_like(expectations)
    outcomes = Counter()
    for trial in range(trials):
        state = initial_state(attr, initial, seed + trial)
        # Same initial state; independent selection and settlement streams.
        rng = random.Random(seed + 10000000*(1+POLICIES.index(policy)) + trial)
        for step in range(rewards+1):
            assert state.formal_attributes[attr] == attributes[step]
            if trial == 0:
                modifiers.append(rm.attribute_modifier(state, attr, rm.mood_check_profile(rm.get_mood_state(state))))
            dice = state.dice_for(attr)
            pmf = pool_pmf(dice)
            survival = np.cumsum(pmf[::-1])[::-1]
            pmf_sum[step] += pmf
            survival_sq[step] += survival**2
            expectations[trial, step] = pmf @ np.arange(MAX_SCORE+1)
            dice_count[trial, step] = len(dice)
            if step == rewards:
                break
            # Formal-growth-only reference: exercise the game's real counters.
            rm.add_formal_attribute(state, attr, 1)
            rm.process_dice_growth_progress_on_small_rest(state)
            assert state.growth_reward_pending[attr] == 1
            cards = rm.draw_pending_growth_reward_cards(state, attr, 3, rng)
            card = random_choice(state, attr, cards, rng) if policy == 'random' else greedy_choice(state, attr, cards)[0]
            before = [(tuple(d.faces), d.enchantment) for d in dice]
            result = rm.apply_pending_growth_reward(state, attr, card, rng)
            assert result['applied'], card
            assert state.growth_reward_pending[attr] == 0
            after = [(tuple(d.faces), d.enchantment) for d in state.dice_for(attr)]
            outcomes['selected:' + card['type']] += 1
            outcomes['no_change'] += before == after
        if (trial+1) % 500 == 0:
            print(f'{name}/{policy}: {trial+1}/{trials}', flush=True)
    pmf = pmf_sum / trials
    survival = np.cumsum(pmf[:, ::-1], axis=1)[:, ::-1]
    se = np.sqrt(np.maximum(0, survival_sq/trials-survival**2)/max(1, trials-1))
    return dict(name=name, attr=attr, initial=initial, policy=policy, trials=trials,
                attributes=attributes, modifiers=np.array(modifiers),
                pmf=pmf, survival=survival, se=se, expectations=expectations,
                dice_count=dice_count, outcomes=dict(outcomes))


def threshold(survival, probability):
    """Largest integer target with at least the requested mixture success rate."""
    return int(np.flatnonzero(survival >= probability-1e-12)[-1])


def fit_wake(result):
    # Formal growth reference, sampled at actual POW values 6..20.
    x = np.arange(6, 21)
    z = x-6
    survival = result['survival'][z]
    shift = result['modifiers'][z]
    best = None
    # Simple coefficients (a: .001, b: .01), monotone on 6..20.
    b_grid = np.arange(0, 2.001, .01)
    for a in np.arange(-.1, .1001, .001):
        if abs(a) < .0005:
            continue  # User requested a genuine quadratic, not a linear fit.
        allowed = b_grid[(b_grid+28*a >= -1e-12)]
        if not len(allowed):
            continue
        curves = 15 + a*z[None, :]**2 + allowed[:, None]*z[None, :]
        targets = np.floor(curves+.5).astype(int)
        raw = targets-shift
        probabilities = survival[np.arange(len(z))[None, :], np.clip(raw, 0, MAX_SCORE)]
        errors = np.mean((probabilities-.725)**2, axis=1)
        for i in np.flatnonzero(errors <= errors.min()+1e-14):
            # Stable tie-break: probability error, then continuous .725 target fit.
            desired = np.array([np.interp(.725, row[::-1], np.arange(MAX_SCORE, -1, -1)) for row in survival]) + shift
            key = (float(errors[i]), float(np.mean((curves[i]-desired)**2)), abs(a))
            if best is None or key < best[0]:
                best = (key, float(round(a, 3)), float(round(allowed[i], 2)), targets[i], probabilities[i])
    _, a, b, targets, rates = best
    rows = []
    for i, value in enumerate(x):
        s = survival[i]
        in_band = np.flatnonzero((s >= .70-1e-12) & (s <= .75+1e-12)) + shift[i]
        rows.append(dict(pow=int(value), reward_count=int(z[i]), target=int(targets[i]),
                         success=float(rates[i]), mc_se=float(result['se'][z[i], targets[i]-shift[i]]),
                         attainable_targets_70_75=in_band.tolist()))
    return dict(a=a, b=b, anchor=15, domain=[6, 20], reference='reward_count = POW - 6',
                rounding='floor(value + 0.5)', minimum_success=float(min(rates)),
                maximum_success=float(max(rates)), rows=rows)


def write_database(path, results, metadata):
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE growth (scenario TEXT, policy TEXT, formal_attribute INTEGER,
          reward_count INTEGER, attribute_modifier INTEGER,
          trials INTEGER, mean_dice_score REAL, sd_between_builds REAL,
          p10_build_mean REAL, p90_build_mean REAL, mean_owned_dice REAL,
          PRIMARY KEY(scenario, policy, formal_attribute));
        CREATE TABLE distribution (scenario TEXT, policy TEXT, formal_attribute INTEGER,
          raw_score INTEGER, probability REAL, pass_probability REAL, pass_mc_se REAL,
          PRIMARY KEY(scenario, policy, formal_attribute, raw_score));
        CREATE TABLE target_curve (scenario TEXT, policy TEXT, formal_attribute INTEGER,
          requested_probability REAL, raw_target INTEGER, actual_probability REAL,
          probability_at_next_target REAL, pass_mc_se REAL,
          PRIMARY KEY(scenario, policy, formal_attribute, requested_probability));
        CREATE VIEW lookup AS SELECT t.*, g.reward_count, g.attribute_modifier,
          t.raw_target + g.attribute_modifier AS target FROM target_curve t
          JOIN growth g USING(scenario, policy, formal_attribute);
        CREATE VIEW expected_value AS SELECT g.*,
          g.mean_dice_score+g.attribute_modifier AS mean_total_score FROM growth g;
        ''')
        db.executemany('INSERT INTO metadata VALUES (?,?)', [(k, json.dumps(v, ensure_ascii=False)) for k,v in metadata.items()])
        for r in results:
            for k, pmf in enumerate(r['pmf']):
                prefix = (r['name'], r['policy'], int(r['attributes'][k]))
                means = r['expectations'][:, k]
                db.execute('INSERT INTO growth VALUES (?,?,?,?,?,?,?,?,?,?,?)', prefix +
                           (k, int(r['modifiers'][k]), r['trials'], float(means.mean()), float(means.std(ddof=1)),
                            float(np.quantile(means,.1)), float(np.quantile(means,.9)), float(r['dice_count'][:, k].mean())))
                db.executemany('INSERT INTO distribution VALUES (?,?,?,?,?,?,?)',
                               [prefix+(s, float(p), float(r['survival'][k,s]), float(r['se'][k,s])) for s,p in enumerate(pmf)])
                for probability in PROBABILITIES:
                    t = threshold(r['survival'][k], probability)
                    db.execute('INSERT INTO target_curve VALUES (?,?,?,?,?,?,?,?)', prefix +
                               (probability, t, float(r['survival'][k,t]), float(r['survival'][k,t+1]) if t < MAX_SCORE else 0., float(r['se'][k,t])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials', type=int, default=2000)
    parser.add_argument('--max-attribute', type=int, default=20)
    parser.add_argument('--seed', type=int, default=20260920)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenarios', nargs='*')
    args = parser.parse_args()
    if args.trials < 2 or args.max_attribute < 6:
        parser.error('Use at least 2 trials and a maximum attribute of at least 6.')
    args.output.mkdir(parents=True, exist_ok=True)
    database = args.output/'dice-growth.sqlite'
    if database.exists():
        raise SystemExit('Use a fresh output directory to preserve earlier results.')
    results = []
    started = time.monotonic()
    for index, scenario in enumerate(SCENARIOS):
        if args.scenarios and scenario[0] not in args.scenarios:
            continue
        for policy in POLICIES:
            r = simulate(scenario, policy, args.trials, args.max_attribute, args.seed+index*100000)
            results.append(r)
            print(f"Completed {r['name']}/{policy} in {time.monotonic()-started:.1f}s", flush=True)
    metadata = dict(model='formal-attribute-growth-corrected-20260920-v2', seed=args.seed,
                    trials_per_scenario_policy=args.trials, max_attribute=args.max_attribute,
                    x_axis='formal_attribute',
                    growth_reference='only rewards from gained formal attribute points; settled before measurement',
                    baseline='stable mood; no fatigue; top 3 actual-roll-mean dice; energy not limiting',
                    policies={'random':'uniform card slot and player-selectable targets',
                              'greedy':'exact one-step expected top-three sum; first listed choice on ties'},
                    exclusions=['bonus and intermediate attribute gains','schedule growth rewards',
                                'degradation','fog (not used by current growth UI)','schedule event frequencies'],
                    corrections=['capped faces excluded from all increase targets',
                                 'replacement values revealed per target die type',
                                 'low replacement band starts at ceil(0.1 * sides)'],
                    caveats=['formal attribute alone does not determine a full-campaign dice pool'],
                    integer_target='largest T such that P(total >= T) >= requested probability',
                    uncertainty='PMF exact conditional on each pool; MC SE across independent growth trajectories')
    write_database(database, results, metadata)
    summary = dict(metadata=metadata, scenarios=[], wake_fits={})
    for r in results:
        rows = []
        for k, attribute in enumerate(r['attributes']):
            rows.append(dict(formal_attribute=int(attribute), modifier=int(r['modifiers'][k]),
                             rewards=k, mean=float(r['expectations'][:,k].mean()),
                             p10=float(np.quantile(r['expectations'][:,k],.1)),
                             p90=float(np.quantile(r['expectations'][:,k],.9)),
                             mean_owned=float(r['dice_count'][:,k].mean()),
                             thresholds={str(p):threshold(r['survival'][k],p) for p in PROBABILITIES},
                             survival=r['survival'][k].tolist(), se=r['se'][k].tolist()))
        summary['scenarios'].append(dict(name=r['name'], policy=r['policy'], initial=r['initial'],
                                         rows=rows, outcomes=r['outcomes']))
        if r['name']=='pow' and args.max_attribute>=20:
            summary['wake_fits'][r['policy']] = fit_wake(r)
    (args.output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Done: {database}; {time.monotonic()-started:.1f}s', flush=True)


if __name__ == '__main__':
    main()
