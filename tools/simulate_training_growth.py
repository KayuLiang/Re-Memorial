"""Controlled full training trajectories; no production schedules or saves changed."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import closing
from functools import lru_cache
from itertools import combinations
import json
from pathlib import Path
import random
import sqlite3
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import simulate_dice_growth as base

rm = base.rm
MAX_TOTAL = 70
SCENARIOS = [('pow', 'pow', 6), ('con', 'con', 6)] + [
    (f'{attr}_{n}', attr, n) for attr in ('str', 'dex') for n in range(1, 7)]


def selected_pools(dice):
    """All outcomes of the core's forced-shackle selection, with equal weights."""
    usable = [d for d in dice if not d.is_sealed()]
    forced = [d for d in usable if d.enchantment == rm.ENCHANT_SHACKLE]
    if len(forced) > 3:
        return list(combinations(forced, 3))
    free = sorted((d for d in usable if d not in forced),
                  key=lambda d: -base.roll_mean(d.faces, d.enchantment))
    return [forced + free[:3-len(forced)]]


@lru_cache(maxsize=16384)
def _pool_mean(key):
    dice = [rm.RMDice(str(i), 'pow', faces, enchant) for i, (faces, enchant) in enumerate(key)]
    pools = selected_pools(dice)
    return sum(sum(base.roll_mean(d.faces, d.enchantment) for d in pool) for pool in pools)/len(pools)


def pool_mean(dice):
    return _pool_mean(tuple((tuple(d.faces), d.enchantment) for d in dice))


def total_pmf(state, attr):
    pools = selected_pools(state.dice_for(attr))
    raw = sum((base.pool_pmf(pool) for pool in pools), np.zeros(61))/len(pools)
    # An entirely sealed pool cannot make a check, even if its modifier is high.
    available = any(pools)
    modifier = rm.attribute_modifier(state, attr, rm.mood_check_profile(rm.MOOD_STABLE))
    total = np.zeros(MAX_TOTAL+1)
    if available:
        total[modifier:modifier+61] = raw
    return total, modifier, available


def target_for(survival, probability):
    attainable = np.flatnonzero(survival >= probability-1e-12)
    return int(attainable[-1]) if len(attainable) else None


def card_options(state, attr, card):
    if not rm.card_needs_die_choice(card):
        return [dict(card)]
    options = []
    for die in rm.growth_reward_dice_candidates(state, attr, card):
        if rm.card_needs_face_choice(card):
            options.extend(dict(card, die_id=die.id, face_index=i)
                           for i in rm.growth_reward_face_indices(die, card))
        else:
            options.append(dict(card, die_id=die.id))
    return options


def card_score(state, attr, card):
    """Exact one-step mean over hidden targets, without drawing settlement RNG."""
    dice = state.dice_for(attr)
    kind = card['type']
    if kind == 'add_new_die':
        # Unenchanted new dice have known mean from the revealed total.
        new = rm.RMDice('new', attr, [card['face_total']/card['die_sides']]*card['die_sides'])
        return pool_mean(dice + [new])
    if kind in ('add_light_enchant', 'add_swift_enchant', 'seal_die', 'shackle_die',
                'add_heavy_enchant', 'add_sluggish_enchant'):
        candidates = [d for d in dice if d.enchantment is None]
    elif kind.startswith('upgrade_') or kind == 'downgrade_die_type':
        candidates = rm.dice_type_change_candidates(state, attr, upgrade=kind != 'downgrade_die_type')
    else:
        candidates = rm.growth_reward_dice_candidates(state, attr, card)
    if card.get('die_id'):
        candidates = [d for d in candidates if d.id == card['die_id']]
    scores = []
    enchants = {'add_light_enchant':rm.ENCHANT_LIGHT, 'add_swift_enchant':rm.ENCHANT_SWIFT,
                'seal_die':rm.ENCHANT_SEAL, 'shackle_die':rm.ENCHANT_SHACKLE,
                'add_heavy_enchant':rm.ENCHANT_HEAVY, 'add_sluggish_enchant':rm.ENCHANT_SLUGGISH}
    for die in candidates:
        variants = []
        if kind.startswith(('replace_', 'increase_', 'decrease_')):
            indices = ([card['face_index']] if 'face_index' in card
                       else rm.growth_reward_face_indices(die, card))
            for i in indices:
                changed = die.copy()
                value = (rm.replacement_face_value(card, die) if kind.startswith('replace_')
                         else die.faces[i] + (card.get('increase_amount', 1) if kind.startswith('increase_') else -1))
                changed.faces[i] = min(len(die.faces), max(1, value))
                variants.append(changed)
        else:
            changed = die.copy()
            if kind.startswith('upgrade_'):
                changed.faces += [min(changed.faces), max(changed.faces)]
            elif kind == 'downgrade_die_type':
                for _ in range(2):
                    changed.faces.remove(min(changed.faces))
                changed.faces = [min(v, len(changed.faces)) for v in changed.faces]
            elif kind == 'convert_negative_enchant':
                for enchant in rm.POSITIVE_ENCHANTMENTS:
                    variant = die.copy()
                    variant.enchantment = enchant
                    variants.append(variant)
            elif kind == 'clear_negative_enchant':
                changed.enchantment = None
            elif kind in enchants:
                changed.enchantment = enchants[kind]
            else:
                raise ValueError(kind)
            if not variants:
                variants.append(changed)
        scores.append(sum(pool_mean([v if d.id == die.id else d for d in dice])
                          for v in variants)/len(variants))
    return sum(scores)/len(scores)


def choose_card(state, attr, cards, policy, rng):
    if policy == 'random':
        return base.random_choice(state, attr, cards, rng)
    options = [option for card in cards for option in card_options(state, attr, card)]
    return max(options, key=lambda card: card_score(state, attr, card))


def settle_cards(state, policy, rng, counts):
    # Same growth-before-degradation priority as the current selection screen.
    for mode, pending, draw, apply in (
        ('reward', state.growth_reward_pending, rm.draw_pending_growth_reward_cards, rm.apply_pending_growth_reward),
        ('penalty', state.degradation_penalty_pending, rm.draw_pending_degradation_penalty_cards, rm.apply_pending_degradation_penalty)):
        for attr in rm.ATTRIBUTES:
            while pending[attr]:
                cards = draw(state, attr, 3, rng)
                if not cards:
                    break  # Leave an unfulfillable pending selection intact.
                card = choose_card(state, attr, cards, policy, rng)
                result = apply(state, attr, card, rng)
                assert result['applied'], (mode, card)
                counts[f'{mode}:{attr}'] += 1
                counts[f'{mode}_type:{card["type"]}'] += 1


def initial_state(attr, initial, seed):
    allocation = None
    if attr in ('str', 'dex'):
        allocation = {attr:initial, ('dex' if attr == 'str' else 'str'):1, 'int':7-initial}
    return rm.create_initial_character(allocation, random.Random(seed))


def training_dice(state, attr):
    allowed = ('con', 'str', 'dex') if attr == 'con' else (attr,)
    dice = rm.usable_dice_for_attributes(state, allowed)
    forced = rm.shackled_dice(dice)
    size = min(3, len(dice))
    options = [pool for pool in combinations(dice, size)
               if (len(forced) > 3 or all(d in pool for d in forced))
               and (attr != 'con' or any(d.attribute == 'con' for d in pool))]
    return max(options, key=lambda pool: sum(base.roll_mean(d.faces, d.enchantment) for d in pool), default=())


def proxy_strength_bonus(state, attr, result, rng):
    """Only POW uses this adapter: STR probabilities, target-attribute counters."""
    plan = rm.build_strength_training_bonus_rolls(rm.current_attribute(state, attr), result.rank)
    for chance in plan:
        if result.rank == rm.RESULT_SUCCESS:
            chance *= (2/3)**rm._count_attribute_bonuses(state, attr)
        if rm.roll_probability(chance, rng):
            rm.add_attribute_bonus(state, attr, 1)


def training_day(state, attr, policy, rng, counts):
    schedule = {'str':'test_strength_training', 'dex':'test_dex_training',
                'con':'test_jogging', 'pow':'test_strength_training'}[attr]
    for slot in rm.TIME_SLOTS[:6]:
        rm.start_turn(state, slot)
        dice = training_dice(state, attr)
        layers = rm.training_fatigue_layers(state, schedule)
        requirement = rm.test_training_requirement(state, attr) + rm.roll_training_fatigue_requirement_penalty(layers, rng)
        spec = rm.CheckSpec(attr, requirement, [d.id for d in dice], big_failure_slack=0,
                            allowed_dice_attributes=('con', 'str', 'dex') if attr == 'con' else (attr,),
                            required_dice_attributes=('con',) if attr == 'con' else ())
        result = rm.perform_check(state, spec, rng) if dice else None
        if result is None or not result.available:
            rm.resolve_test_day_rest(state, rng)
            counts['rest_actions'] += 1
            continue
        counts['training_actions'] += 1
        counts['rank:'+result.rank] += 1
        if attr == 'pow':
            proxy_strength_bonus(state, attr, result, rng)
            state.test_growth_progress[attr] = min(6, state.test_growth_progress.get(attr, 0)
                                                   + rm.test_training_progress_delta(result.rank))
            rm.add_training_fatigue(state, schedule)
        elif attr == 'con':
            rm.apply_test_exercise_schedule_result(state, schedule, result, rng)
        else:
            rm.apply_test_training_schedule_result(state, schedule, result, rng)
        if rm.is_dead(state):
            counts['death_during_training'] += 1
            return False
        rm.apply_big_failure_degradation(state, result)
        settle_cards(state, policy, rng, counts)
    # STR/DEX progress is converted by the core small rest; POW stays a proxy.
    if attr == 'pow' and state.test_growth_progress.get(attr, 0) >= 6:
        state.test_growth_progress[attr] = 0
        rm.add_attribute_bonus(state, attr, 1)
        counts['test_training_bonus:pow'] += 1
    rm.start_turn(state, 'sleep_decision')
    result = rm.begin_sleep(state, rng)
    if not result['available'] or rm.is_dead(state):
        counts['death_before_wake'] += 1
        return False
    assert not result['needs_wake_check']
    counts.update(result['events'])
    # Do NOT drain again after large rest: newly earned formal-point rewards
    # wait for the next small rest, matching the actual end_day ordering.
    settle_cards(state, policy, rng, counts)
    return True


def simulate(scenario, policy, trials, max_attribute, max_days, seed):
    name, attr, initial = scenario
    samples = {value:[] for value in range(initial, max_attribute+1)}
    pmfs = {value:np.zeros(MAX_TOTAL+1) for value in samples}
    squared = {value:np.zeros(MAX_TOTAL+1) for value in samples}
    counts = Counter()
    stopped = Counter()
    for trial in range(trials):
        state = initial_state(attr, initial, seed+trial)
        rng = random.Random(seed+10000000*(1+base.POLICIES.index(policy))+trial)
        local = Counter()
        last = None
        for day in range(max_days+1):
            value = state.formal_attributes[attr]
            if value in samples and value != last:
                pmf, modifier, available = total_pmf(state, attr)
                pmfs[value] += pmf
                squared[value] += np.cumsum(pmf[::-1])[::-1]**2
                samples[value].append(dict(trial=trial, day=day, modifier=modifier,
                    mean=float(pmf @ np.arange(MAX_TOTAL+1)), rewards=local[f'reward:{attr}'],
                    penalties=local[f'penalty:{attr}'], available=available,
                    bonus=len(state.attribute_bonuses[attr]), intermediate=state.attribute_values[attr],
                    owned=len(state.dice_for(attr)), pending_points=state.dice_growth_progress[attr]))
            last = value
            if value >= max_attribute:
                stopped['reached_or_crossed_max'] += 1
                break
            if day == max_days:
                stopped['day_limit'] += 1
                break
            if training_day(state, attr, policy, rng, local) is False:
                stopped['death'] += 1
                break
        counts.update(local)
        if (trial+1) % 100 == 0:
            print(f'{name}/{policy} {trial+1}/{trials}', flush=True)
    rows = []
    for value, observations in samples.items():
        n = len(observations)
        if not n:
            rows.append(dict(formal_attribute=value, n=0))
            continue
        pmf = pmfs[value]/n
        survival = np.cumsum(pmf[::-1])[::-1]
        se = np.sqrt(np.maximum(0, squared[value]/n-survival**2)/max(1, n-1))
        means = [sample['mean'] for sample in observations]
        row = dict(formal_attribute=value, n=n, mean=float(np.mean(means)),
                   p10=float(np.quantile(means,.1)), p90=float(np.quantile(means,.9)),
                   survival=survival.tolist(), pmf=pmf.tolist(), se=se.tolist(),
                   thresholds={str(p):target_for(survival,p) for p in base.PROBABILITIES})
        for field in ('day', 'modifier', 'rewards', 'penalties', 'bonus', 'intermediate', 'owned', 'pending_points', 'available'):
            row['mean_'+field] = float(np.mean([sample[field] for sample in observations]))
        rows.append(row)
    return dict(name=name, attr=attr, initial=initial, policy=policy, trials=trials,
                rows=rows, samples=samples, outcomes=dict(counts), stopped=dict(stopped))


def fit_wake(result):
    # The fixed POW-6 anchor is 72.5%; do not demand 75% from that exception.
    rows = [row for row in result['rows'] if row['n'] >= min(result['trials'], 100)
            and 6 < row['formal_attribute'] <= 20]
    if len(rows) < 3:
        return None
    x = np.array([row['formal_attribute'] for row in rows])
    z = x-6
    survival = np.array([row['survival'] for row in rows])
    best = None
    # Stay at or above 75% on fitted growth points, then minimize excess.
    for a_step in range(-500, 501):
        if a_step == 0:
            continue
        a = a_step / 1000.0
        b = np.arange(801) / 100.0
        b = b[b + 28*a >= -1e-12]
        curves = 15+a*z[None,:]**2+b[:,None]*z[None,:]
        targets = np.floor(curves+.5).astype(int)
        valid = targets.max(axis=1) <= MAX_TOTAL
        curves, targets, b = curves[valid], targets[valid], b[valid]
        if not len(b):
            continue
        rates = survival[np.arange(len(rows))[None,:], targets]
        errors = np.where(np.all(rates >= .75, axis=1),
                          np.mean((rates-.75)**2, axis=1), np.inf)
        i = int(np.argmin(errors))
        if not np.isfinite(errors[i]):
            continue
        key = (float(errors[i]), abs(a), float(b[i]))
        if best is None or key < best[0]:
            best = (key, round(float(a),3), round(float(b[i]),2), targets[i], rates[i])
    if best is None:
        return None
    _, a, b, targets, rates = best
    fitted = []
    for row in result['rows']:
        if not row['n'] or not 6 <= row['formal_attribute'] <= 20:
            continue
        z = row['formal_attribute']-6
        target = int(np.floor(15+a*z*z+b*z+.5))
        rate = row['survival'][target]
        band = np.flatnonzero((np.array(row['survival']) >= .70) & (np.array(row['survival']) <= .75))
        fitted.append(dict(pow=row['formal_attribute'], n=row['n'], target=int(target), success=float(rate),
                           mc_se=row['se'][target], used_for_fit=row['formal_attribute'] > 6 and row['n'] >= min(result['trials'],100),
                           attainable_targets_70_75=band.tolist()))
    return dict(a=a, b=b, anchor=15, domain=[6,20], rows=fitted,
                target_probability=.75, objective='minimum squared excess above 75%; fitted non-anchor points >=75%',
                minimum_success=min(r['success'] for r in fitted), maximum_success=max(r['success'] for r in fitted))


def write_results(directory, results, metadata):
    database = directory/'dice-growth.sqlite'
    with closing(sqlite3.connect(database)) as db, db:
        db.executescript('''
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE growth(scenario TEXT, policy TEXT, formal_attribute INTEGER, n INTEGER,
          mean_total REAL, p10 REAL, p90 REAL, mean_days REAL, mean_rewards REAL,
          mean_penalties REAL, mean_modifier REAL, available_fraction REAL,
          PRIMARY KEY(scenario,policy,formal_attribute));
        CREATE TABLE distribution(scenario TEXT, policy TEXT, formal_attribute INTEGER,
          total_score INTEGER, probability REAL, pass_probability REAL, pass_mc_se REAL,
          PRIMARY KEY(scenario,policy,formal_attribute,total_score));
        CREATE TABLE target_curve(scenario TEXT, policy TEXT, formal_attribute INTEGER,
          requested_probability REAL, target INTEGER, actual_probability REAL,
          probability_at_next_target REAL, pass_mc_se REAL,
          PRIMARY KEY(scenario,policy,formal_attribute,requested_probability));
        CREATE VIEW lookup AS SELECT t.*,g.n FROM target_curve t JOIN growth g
          USING(scenario,policy,formal_attribute);
        CREATE TABLE samples(scenario TEXT,policy TEXT,formal_attribute INTEGER,trial INTEGER,
          day INTEGER,modifier INTEGER,mean_total REAL,rewards INTEGER,penalties INTEGER,
          available INTEGER,bonus INTEGER,intermediate INTEGER,owned INTEGER,pending_points INTEGER,
          PRIMARY KEY(scenario,policy,formal_attribute,trial));
        ''')
        db.executemany('INSERT INTO metadata VALUES (?,?)', [(k,json.dumps(v,ensure_ascii=False)) for k,v in metadata.items()])
        for result in results:
            for row in result['rows']:
                prefix = (result['name'], result['policy'], row['formal_attribute'])
                if not row['n']:
                    continue
                db.execute('INSERT INTO growth VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', prefix+tuple(row[k] for k in (
                    'n','mean','p10','p90','mean_day','mean_rewards','mean_penalties','mean_modifier','mean_available')))
                db.executemany('INSERT INTO distribution VALUES (?,?,?,?,?,?,?)', [prefix+(s,p,row['survival'][s],row['se'][s]) for s,p in enumerate(row['pmf'])])
                for p in base.PROBABILITIES:
                    target = row['thresholds'][str(p)]
                    values = ((None,None,None) if target is None else (row['survival'][target],
                              row['survival'][target+1] if target<MAX_TOTAL else 0.,row['se'][target]))
                    db.execute('INSERT INTO target_curve VALUES (?,?,?,?,?,?,?,?)',prefix+(p,target)+values)
                fields = ('trial','day','modifier','mean','rewards','penalties','available','bonus','intermediate','owned','pending_points')
                db.executemany('INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    [prefix+tuple(sample[f] for f in fields) for sample in result['samples'][row['formal_attribute']]])
    fits = {r['policy']:fit_wake(r) for r in results if r['name']=='pow' and metadata['max_attribute']==20}
    summary = dict(metadata=metadata, scenarios=[{k:v for k,v in r.items() if k!='samples'} for r in results],
                   wake_fits={policy:fit for policy,fit in fits.items() if fit is not None})
    (directory/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trials',type=int,default=1000)
    parser.add_argument('--max-attribute',type=int,default=20)
    parser.add_argument('--max-days',type=int,default=730)
    parser.add_argument('--seed',type=int,default=20260920)
    parser.add_argument('--workers',type=int,choices=(1,2),default=2)
    parser.add_argument('--refit-only',action='store_true',help='Refit saved trajectories without rerunning growth or changing the database.')
    parser.add_argument('--scenarios',nargs='*')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.refit_only:
        path=args.output/'summary.json'
        summary=json.loads(path.read_text(encoding='utf-8'))
        fits={r['policy']:fit_wake(r) for r in summary['scenarios'] if r['name']=='pow'}
        summary['wake_fits']={p:f for p,f in fits.items() if f is not None}
        path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Refitted existing growth results; trajectories and database unchanged.')
        return
    if args.trials<2 or not 6<=args.max_attribute<=20 or args.max_days<1:
        parser.error('Use trials >= 2, 6 <= max attribute <= 20, max days >= 1.')
    args.output.mkdir(parents=True,exist_ok=True)
    if (args.output/'dice-growth.sqlite').exists():
        parser.error('Use a fresh output directory to preserve earlier results.')
    metadata = dict(model='training-growth-provisional-v1',seed=args.seed,trials=args.trials,
        max_attribute=args.max_attribute,max_days=args.max_days,
        x_axis='formal attribute; first exact morning visit; skipped values not interpolated',
        measurement='actual bonus + intermediate + formal modifier; stable mood; full legal same-attribute dice; energy unrestricted ONLY at measurement',
        daily_policy='six ordinary rounds focused on target; rest if all-out dice unavailable or unaffordable; on-time sleep',
        models={'pow':'STR proxy; no production POW schedule', 'str':'strength bonus + test progress',
                'dex':'test progress only', 'con':'jogging mixed CON/STR/DEX rolls and bonuses; initial STR3 DEX3 INT2'},
        implemented_connections=['nightly test-progress-to-bonus conversion in core small rest',
                                 'training big failures accumulate core degradation before mood changes'],
        included=['all three growth counters','small and weekly large rest','degradation and legal card choices',
                  'sealed and forced shackled dice','temporary-enchantment decay','real energy, daytime rest and training fatigue'],
        exclusions=['unconfigured narrative event rewards','late nights and sleep disease by on-time policy',
                    'mood drift: controlled stable throughout','fog: current growth UI does not use it'],
        reward_order='growth before penalties; weekly formal gains wait until following small rest',
        uncertainty='exact conditional PMF; Monte Carlo SE over independently sampled first visits; conditional on reaching exact value')
    results=[]
    started=time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        jobs = {}
        for index,scenario in enumerate(SCENARIOS):
            if args.scenarios and scenario[0] not in args.scenarios:
                continue
            for policy in base.POLICIES:
                job=executor.submit(simulate,scenario,policy,args.trials,args.max_attribute,args.max_days,args.seed+index*100000)
                jobs[job]=(scenario[0],policy)
        for job in as_completed(jobs):
            results.append(job.result())
            print(f'Completed {jobs[job]}; elapsed {time.monotonic()-started:.1f}s',flush=True)
    order={(s[0],p):i for i,(s,p) in enumerate((s,p) for s in SCENARIOS for p in base.POLICIES)}
    results.sort(key=lambda r:order[r['name'],r['policy']])
    write_results(args.output,results,metadata)
    print(f'Done in {time.monotonic()-started:.1f}s: {args.output}',flush=True)


if __name__=='__main__':
    main()
