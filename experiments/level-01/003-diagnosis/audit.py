"""Recheck experiment 003 records at its committed source version."""

import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[3]
out = root / 'experiments/level-01/003-diagnosis'
checks = []

def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)

original_source = subprocess.check_output(['git', 'show', 'e8df3db:diagnose_step1.py'], cwd=root)
source_hash = hashlib.sha256(original_source).hexdigest()
current_hash = hashlib.sha256((root / 'diagnose_step1.py').read_bytes()).hexdigest()
runner_hash = hashlib.sha256((root / 'sudokufly.py').read_bytes()).hexdigest()
suites = {}
for suite, n in [('phases', 36), ('snapshots', 48), ('training', 120), ('transition', 24)]:
    data = json.loads((out / f'{suite}.json').read_text())
    suites[suite] = data
    check(f'{suite}: record count', len(data['rows']) == n)
    check(f'{suite}: progress agrees', data['rows'] == [json.loads(s) for s in (out / f'{suite}-progress.jsonl').read_text().splitlines()])
    check(f'{suite}: exact source', data['provenance']['source_sha256'] == (current_hash if suite == 'transition' else source_hash))
    check(f'{suite}: unchanged pilot source', data['provenance']['runner_sha256'] == runner_hash)
    check(f'{suite}: verified graph', data['provenance']['verified_graph'] == {'release':'MaleCNS v1.0','neurons':166700,'directed_edges':25582938,'arrays_verified':True})
    check(f'{suite}: pinned upstream', data['provenance']['upstream_head'] == '78ef3e05ab0fa086032098558d893667068944a0')
    for i, r in enumerate(data['rows']):
        if 'bins' not in r:
            continue
        check(f'{suite}/{i}: bin count', len(r['bins']) * 10 == r['duration_ms'])
        check(f'{suite}/{i}: KC counts', sum(v['KC'] for v in r['bins']) == r['KC_spikes'] == sum(v[1] for v in r['KC_ids_counts']))
        check(f'{suite}/{i}: KC identities', len(r['KC_ids_counts']) == r['active_KCs'] == len(set(v[0] for v in r['KC_ids_counts'])))
        check(f'{suite}/{i}: dopamine counts', sum(v['PAM'] for v in r['bins']) == r['PAM_spikes'] and sum(v['PPL'] for v in r['bins']) == r['PPL_spikes'])
        check(f'{suite}/{i}: motor rates', all(sum(v[side] for v in r['bins']) * 1000 / r['duration_ms'] == r[f'{side}_hz'] for side in ('left','right')))
        d = r['right_hz'] - r['left_hz']
        check(f'{suite}/{i}: decoder', d == r['difference_hz'] and r['action'] == ('accept' if d >= 2 else 'reject' if d <= -2 else 'timeout'))
        if not r['learning']:
            check(f'{suite}/{i}: frozen weights', r['changed_edges_in_phase'] == r['weight_L1_change'] == r['weight_signed_change'] == 0)

old = root / 'experiments/level-01/002-expanded-memory'
original = [json.loads(s) for s in (old / 'trials.jsonl').read_text().splitlines()]
for i, r in enumerate(suites['snapshots']['rows']):
    if r['variant'] != 'nominal':
        continue
    mapping, phase = {'untrained':(0,'baseline'),'learned_map0':(0,'learned_eval'),'learned_map1':(1,'learned_eval'),'shuffled_map1':(1,'shuffled_eval')}[r['profile']]
    previous = [v for v in original if v['mapping'] == mapping and v['phase'] == phase and v['cue'] == r['cue']]
    check(f'snapshot/{i}: reproduces both original evaluations', len(previous) == 2 and all(v['observation_spikes_sha256'] == r['spikes_sha256'] for v in previous))

training = suites['training']['rows']
summary = []
for order in (0,1):
    for mapping in (0,1):
        for condition in ('normal','no_external_feedback','freeze_settle'):
            rows = [r for r in training if (r['order'],r['mapping'],r['condition']) == (order,mapping,condition)]
            tr = [r for r in rows if r['phase'] == 'train']
            ev = [r for r in rows if r['phase'] == 'eval']
            expected_order = json.loads((old / 'summary.json').read_text())['runs'][order]['cue_order']
            check(f'training/{order}/{mapping}/{condition}: schedule', len(tr) == 8 and [r['cue'] for r in tr] == expected_order and len(ev) == 2)
            if condition == 'normal' and order == mapping:
                orig_train = [r for r in original if r['mapping'] == mapping and r['phase'] == 'learned_train']
                check(f'training/{order}/{mapping}: original train actions', [r['action'] for r in tr] == [r['action'] for r in orig_train])
                for r in ev:
                    previous = [v for v in original if v['mapping'] == mapping and v['phase'] == 'learned_eval' and v['cue'] == r['cue']]
                    check(f'training/{order}/{mapping}/{r["cue"]}: original eval hashes', len(previous)==2 and all(v['observation_spikes_sha256'] == r['spikes_sha256'] for v in previous))
            if condition == 'no_external_feedback':
                check(f'training/{order}/{mapping}: no imposed pulses', all(r['pulse'] is None for r in tr))
            summary.append({'order':order,'mapping':mapping,'condition':condition,'accuracy':sum(r['correct'] for r in ev)/2,'difference_hz':{r['cue']:r['difference_hz'] for r in ev},'changed_edges':ev[0]['total_changed_edges']})
    for cue in ('vertical','horizontal'):
        pair = [r for r in training if r['order']==order and r['condition']=='no_external_feedback' and r['phase']=='eval' and r['cue']==cue]
        check(f'no-feedback/{order}/{cue}: label independent', len(pair)==2 and pair[0]['spikes_sha256']==pair[1]['spikes_sha256'])

for variant in ('001-visual-cues','002-expanded-memory'):
    p = root / 'experiments/level-01' / variant
    for file, sha in json.loads((p/'summary.json').read_text())['files_sha256'].items():
        check(f'{variant}/{file}: preserved', hashlib.sha256((p/file).read_bytes()).hexdigest() == sha)

for cue in ('vertical','horizontal'):
    for plasticity in ('normal','frozen'):
        before = [r for r in suites['transition']['rows'] if r['cue']==cue and r['plasticity']==plasticity and r['phase']!='settle']
        for phase in ('observation','feedback_without_pulse'):
            pair = [r for r in before if r['phase']==phase]
            check(f'transition/{cue}/{plasticity}/{phase}: matched prehistory', len(pair)==2 and pair[0]['spikes_sha256']==pair[1]['spikes_sha256'])

result = {'experiment':'003-diagnosis','level':1,'status':'incomplete; diagnosis does not pass the learning gate','post_hoc':True,'exact_initial_diagnostic_source_commit':'e8df3db','training_summary':summary,'suite_elapsed_seconds':{k:v['elapsed_seconds'] for k,v in suites.items()},'checks':checks,'all_checks_passed':all(c['passed'] for c in checks),'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name != 'summary.json'},'diagnostic_source_sha256':current_hash}
(out / 'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'passed':result['all_checks_passed'],'training_summary':summary},indent=2))
