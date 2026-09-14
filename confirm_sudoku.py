"""Controlled Step 5 replay and frozen reserved-family confirmation.

The pilot chooses a protocol; this runner reproduces that exact paired protocol
from pre-Undo Step 3 memory and runs controls with matched teaching opportunities.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

import numpy as np

ROOT = Path.cwd().resolve()
if not (ROOT / 'sudokufly.py').is_file():
    raise RuntimeError('Run this script from the sudokufly repository root')
sys.path.insert(0, str(ROOT))
from constraint_transfer import render_partial
from joint_sudoku import encode_occupancy
from learn_undo import encode_undo, play_with_undo, render_undo
from one_blank import classification_metrics
from sequence_sudoku import SOURCE, encode_sequence, probe_metrics
from sudokufly import UPSTREAM, UPSTREAM_COMMIT, memory_state

ARMS = ('paired', 'frozen', 'no_feedback', 'inconsistent')
VIEWS = ('base', 'shift', 'small')
CONDITIONS = ((20260919, 0), (20260919, 1), (20260920, 0), (20260920, 1))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def records(path):
    path = Path(path)
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt') as stream:
        for line in stream:
            if not line.endswith('\n'):
                raise RuntimeError(f'Incomplete record in {path}')
            yield json.loads(line)


def verify_run(path):
    summary = json.loads((path / 'summary.json').read_text())
    for name, expected in summary['files_sha256'].items():
        if sha(path / name) != expected:
            raise RuntimeError(f'Artifact hash differs: {path / name}')
    return summary, json.loads((path / 'protocol.json').read_text())


def require_committed(paths):
    """Every requested file must exist in HEAD with identical committed bytes."""
    for path in paths:
        name = str(Path(path).resolve().relative_to(ROOT))
        content = subprocess.check_output(['git', 'show', f'HEAD:{name}'], cwd=ROOT)
        if hashlib.sha256(content).hexdigest() != sha(path):
            raise RuntimeError(f'Commit this exact file before proceeding: {name}')


def check_measure(actual, expected, trace=False):
    fields = ('output_hz', 'score_hz', 'action', 'spikes_sha256', 'memory_before',
              'memory_after', 'KC_spikes', 'DAN_spikes')
    if not all(k in actual and k in expected for k in fields):
        raise RuntimeError('Recorded response lacks a required reproduction field')
    fields += tuple(k for k in ('duration_ms', 'pulse', 'learning', 'frozen') if k in expected)
    if trace:
        fields += ('trace',)
    if not all(k in actual and k in expected and actual[k] == expected[k] for k in fields):
        differing = [k for k in fields if k not in actual or k not in expected or actual[k] != expected[k]]
        raise RuntimeError(f'Exact recorded response reproduction failed: {differing}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--split', choices=('development', 'heldout'), default='development')
    parser.add_argument('--development', type=Path)
    args = parser.parse_args()
    if (args.split == 'heldout') != (args.development is not None):
        parser.error('--development is required only for heldout confirmation')
    started = time.perf_counter()
    args.pilot, args.out = args.pilot.resolve(), args.out.resolve()
    if args.development is not None:
        args.development = args.development.resolve()
    runner = Path(__file__).resolve()
    if runner.parent != ROOT:
        raise RuntimeError('Copy the candidate into the repository, review, and commit before running')
    pilot_summary, pp = verify_run(args.pilot)
    if not pilot_summary['pilot_gate'] or not pp['separate_occupancies']:
        raise RuntimeError('Require a completed passing pilot with separate occupancy banks')
    if tuple((r['seed'], r['mapping']) for r in pilot_summary['runs']) != CONDITIONS:
        raise RuntimeError('Unexpected pilot source conditions')
    prefix = ROOT / pp['memory_source']
    prefix_summary, prefix_protocol = verify_run(prefix)
    if prefix_protocol.get('epochs') != 2 or prefix_protocol['memory_source'] != str(SOURCE.relative_to(ROOT)):
        raise RuntimeError('Expected the two-epoch Undo continuation of original paired Step 3 memories')
    source_summary, source_protocol = verify_run(SOURCE)
    prior = ROOT / pp['prior_assay']
    prior_summary, prior_protocol = verify_run(prior)
    assert source_summary['gate_passed']
    assert pp['memory_summary_sha256'] == sha(prefix / 'summary.json')
    assert pp['prior_summary_sha256'] == sha(prior / 'summary.json')
    assert pp['cases_sha256'] == sha(prior / 'cases.json')
    for path, protocol in ((args.pilot, pp), (prefix, prefix_protocol)):
        for name, digest in protocol['source_sha256'].items():
            historical = subprocess.check_output(['git', 'show', f"{protocol['git_head']}:{name}"], cwd=ROOT)
            assert hashlib.sha256(historical).hexdigest() == digest, (path, name)
    source_paths = [runner] + [ROOT / name for name in pp['source_sha256']]
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    assert all(hashes[name] == digest for name, digest in pp['source_sha256'].items()), 'Selected pilot source changed'
    require_committed(source_paths)
    upstream = subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(UPSTREAM), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    assert upstream == UPSTREAM_COMMIT and not dirty

    development_summary = development_protocol = None
    if args.development is not None:
        development_summary, development_protocol = verify_run(args.development)
        assert development_summary['gate_passed'] and development_summary['split'] == 'development'
        assert development_protocol['source_sha256'] == hashes
        assert development_protocol['pilot_summary_sha256'] == sha(args.pilot / 'summary.json')
        require_committed([args.development / 'summary.json'] +
                          [args.development / name for name in development_summary['files_sha256']])
    else:
        require_committed([args.pilot / 'summary.json'] +
                          [args.pilot / name for name in pilot_summary['files_sha256']])
        require_committed([prefix / 'summary.json'] +
                          [prefix / name for name in prefix_summary['files_sha256']])

    selected = {}
    for run in pilot_summary['runs']:
        epoch = run['selected_epoch']
        chosen = [h for h in run['history'] if h['epoch'] == epoch]
        assert epoch is not None and len(chosen) == 1 and chosen[0]['pilot_gate']
        selected[(run['seed'], run['mapping'])] = chosen[0]
    undo_contexts = json.loads((prefix / 'undo-contexts.json').read_text())
    place_contexts = json.loads((args.pilot / 'contexts.json').read_text())
    joint_contexts = json.loads((args.pilot / 'training-contexts.json').read_text())
    primary_policy = pp['primary_policy']
    primary_contexts = [r for r in place_contexts if r['policy'] == primary_policy]
    new_contexts = [r for r in primary_contexts if r['distinct_peers'] in (1, 2, 4)]
    familiar = {r['input']: r['label'] for r in primary_contexts if r['distinct_peers'] == 3}
    assert len(primary_contexts) == 64 and len(new_contexts) == 44 and len(familiar) == 16
    assert len(joint_contexts) == 76 and len(undo_contexts) == 16
    cases = json.loads((prior / 'cases.json').read_text())
    assert sum(c['split'] == args.split for c in cases) == 160

    # The schedule is chosen entirely from committed paired logs. Control
    # responses cannot alter which input receives an update, its duration, or
    # the selected stopping epoch. Raw reference records remain in dependencies.
    reference_trials = {}
    schedules = {f'{seed}-{mapping}': [] for seed, mapping in CONDITIONS}
    for stage, path in (('undo_prefix', prefix / 'training.jsonl'), ('joint', args.pilot / 'training.jsonl')):
        for source_index, row in enumerate(records(path)):
            if stage == 'undo_prefix' and row.get('arm') != 'paired':
                continue
            condition = (row['seed'], row['mapping'])
            if condition not in selected:
                raise RuntimeError('Unknown recorded source condition')
            if stage == 'joint' and row['epoch'] > selected[condition]['epoch']:
                continue
            entries = schedules[f'{condition[0]}-{condition[1]}']
            context = undo_contexts[row['context']] if stage == 'undo_prefix' else joint_contexts[row['context']]
            label = context['label']
            target = row['taught_raw_target'] if stage == 'undo_prefix' else row['target']
            assert target == label ^ condition[1] and context['input'] == row['input']
            phases = len(row['phases'])
            assert phases in (0, 2, 5)
            assert phases == 5 if stage == 'undo_prefix' else bool(phases) == row['teach']
            entry = {'stage': stage, 'source_record': source_index,
                     'source_epoch': row['epoch'], 'source_trial': row['trial'],
                     'input': row['input'], 'semantic_target': label,
                     'teach': bool(phases), 'phase_count': phases,
                     'operation': 'undo' if stage == 'undo_prefix' else context['operation'],
                     'teaching_rule': row.get('teaching_rule', 'bidirectional' if phases == 5 else 'none'),
                     'update_window_ms': 1200 if phases == 5 else 450 if phases == 2 else 0}
            reference_trials[(condition[0], condition[1], len(entries))] = row
            entries.append(entry)
    control_balance = {}
    for seed, mapping in CONDITIONS:
        name = f'{seed}-{mapping}'
        entries = schedules[name]
        assert len([e for e in entries if e['stage'] == 'undo_prefix']) == 60
        joint = [e for e in entries if e['stage'] == 'joint']
        assert len(joint) == selected[(seed, mapping)]['epoch'] * 76
        assert [e['source_trial'] for e in entries[:60]] == list(range(60))
        for epoch in range(1, selected[(seed, mapping)]['epoch'] + 1):
            assert [e['source_trial'] for e in joint if e['source_epoch'] == epoch] == list(range(76))
        active = defaultdict(list)
        for i, entry in enumerate(entries):
            entry['inconsistent_semantic_target'] = None
            if entry['teach']:
                active[entry['input']].append(i)
        balance = {}
        for key, indices in sorted(active.items()):
            seed_bytes = hashlib.sha256(f'step5-warm-controls-v1:{seed}:{key}'.encode()).digest()
            control_seed = int.from_bytes(seed_bytes[:8], 'little')
            rng = random.Random(control_seed)
            odd_extra = rng.randrange(2) if len(indices) % 2 else None
            labels = [0, 1] * (len(indices) // 2)
            if odd_extra is not None:
                labels.append(odd_extra)
            rng.shuffle(labels)
            for index, label in zip(indices, labels):
                entries[index]['inconsistent_semantic_target'] = label
            balance[key] = {'teaching_events': len(indices), 'zero_targets': labels.count(0),
                            'one_targets': labels.count(1), 'odd_extra': odd_extra, 'seed': control_seed}
        control_balance[name] = balance
    if args.development is not None:
        assert json.loads((args.development / 'schedules.json').read_text()) == schedules
        assert json.loads((args.development / 'control-balance.json').read_text()) == control_balance

    args.out.mkdir(parents=True, exist_ok=False)
    os.environ['STONKFLY_DATA'] = str(ROOT / 'data')
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.brain import MemoryBrain
    from stonkfly.neural.common import annotations

    graph = verify()
    parameters = pp['parameters']
    brain = MemoryBrain(eta=parameters['eta'])
    circuit = brain.circuit
    annotation = annotations(brain.ids)
    outputs = {name: np.flatnonzero(annotation.type.eq(name)) for name in ('MBON07', 'MBON11')}
    for indices in outputs.values():
        brain.tonic[indices] = parameters['MBON_current']
    initial_hash = hashlib.sha256(brain.weight.tobytes()).hexdigest()
    assert initial_hash == pp['initial_weights_sha256'] == source_protocol['initial_weights_sha256']
    assert len(circuit['edges']) == 7835
    positions = {int(cell): i for i, cell in enumerate(brain.ids)}
    sp_path = ROOT / source_protocol['memory_source'] / 'protocol.json'
    assert sha(sp_path) == source_protocol['memory_protocol_sha256']
    sp = json.loads((sp_path).read_text())
    templates = np.asarray(sp['templates'], dtype=np.float64)
    groups = np.asarray([positions[int(cell)] for cell in np.asarray(sp['group_KC_ids']).ravel()], dtype=np.int32).reshape(16, 2, 8)
    undo_groups = np.asarray([positions[int(cell)] for cell in np.asarray(pp['undo_KC_ids']).ravel()], dtype=np.int32).reshape(16, 16)
    occupancy_groups = {int(n): np.asarray([positions[int(cell)] for cell in np.asarray(bank).ravel()], dtype=np.int32).reshape(16, 2, 8)
                        for n, bank in pp['occupancy_KC_ids'].items()}
    assert set(occupancy_groups) == {1, 2, 4}
    inputs_manifest = json.loads((args.pilot / 'inputs.json').read_text())
    inputs = {key: np.asarray([positions[int(cell)] for cell in row['KC_ids']], dtype=np.int32)
              for key, row in inputs_manifest.items()}
    assert len(inputs) == 165
    assert all(hashlib.sha256(ix.tobytes()).hexdigest() == key and np.array_equal(ix, np.unique(ix))
               for key, ix in inputs.items())
    placement_encoder = lambda frame, bank, cells, policy: encode_occupancy(frame, bank, cells, occupancy_groups)
    for context in place_contexts:
        board = [0] * 16
        for position, digit in zip((1, 2, 4, 5), context['peers']):
            board[position] = digit
        for view in VIEWS:
            frame = render_partial(board, 0, context['candidate'], view)
            encoder = placement_encoder if context['policy'] == primary_policy else encode_sequence
            indices, diagnostic = encoder(frame, templates, groups, context['policy'])
            assert hashlib.sha256(indices.tobytes()).hexdigest() == context['input']
            assert diagnostic['distinct_peers'] == context['distinct_peers']
    for context in undo_contexts:
        board = [0] * 16
        for position, digit in zip((1, 2, 4, 5), context['peers']):
            board[position] = digit
        for view in VIEWS:
            indices, diagnostic = encode_undo(render_undo(board, 0, view), templates, undo_groups)
            assert hashlib.sha256(indices.tobytes()).hexdigest() == context['input']
            assert diagnostic['presence_code'] == context['pattern']
    for name, value in (('schedules.json', schedules), ('control-balance.json', control_balance),
                        ('inputs.json', inputs_manifest), ('contexts.json', place_contexts),
                        ('undo-contexts.json', undo_contexts)):
        (args.out / name).write_text(json.dumps(value, indent=2) + '\n')
    protocol = {
        'task': 'Controlled Step5 reproduction and frozen board-family confirmation',
        'split': args.split, 'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'source_sha256': hashes, 'upstream': upstream, 'graph': graph, 'initial_weights_sha256': initial_hash,
        'pilot': str(args.pilot.relative_to(ROOT)), 'pilot_summary_sha256': sha(args.pilot / 'summary.json'),
        'prefix': str(prefix.relative_to(ROOT)), 'prefix_summary_sha256': sha(prefix / 'summary.json'),
        'memory_source': str(SOURCE.relative_to(ROOT)), 'memory_summary_sha256': sha(SOURCE / 'summary.json'),
        'cases_source': str((prior / 'cases.json').relative_to(ROOT)), 'cases_sha256': sha(prior / 'cases.json'),
        'development': None if args.development is None else str(args.development.relative_to(ROOT)),
        'development_summary_sha256': None if args.development is None else sha(args.development / 'summary.json'),
        'parameters': parameters, 'decoder': pp['decoder'], 'primary_policy': primary_policy,
        'selected_epochs': {f'{s}-{m}': selected[(s, m)]['epoch'] for s, m in CONDITIONS},
        'undo_KC_ids': pp['undo_KC_ids'], 'occupancy_KC_ids': pp['occupancy_KC_ids'],
        'views': list(VIEWS), 'training_enabled': args.split == 'development',
        'physical_inputs': 165, 'new_contexts': 44, 'nonempty_contexts': 60, 'familiar_contexts': 16,
        'warm_controls': 'Every arm starts the original paired Step3 memory before Undo. Replay the complete two-epoch003 prefix and selected pilot chronology, including its exact update mask. Frozen keeps W/u/w fixed; no-feedback omits DAN pulses with update/passive windows retained. Inconsistent targets are near-balanced separately over all enabled occurrences of each physical input; odd extras and seeds are saved before training.',
        'dose_limit': 'Bidirectional events stimulate both compartments once. Depression-only events stimulate one compartment; inconsistent target changes may change compartment-specific dose. Actual durations are reported; no equality of those doses is assumed. Total update-window exposure is matched across all nonfrozen arms.',
        'reproduction': 'Every paired decision/teaching phase, every003/pilot epoch checkpoint, and all165 final frozen responses must reproduce the selected source records exactly. This controlled replay uses selected deterministic histories; it is not an independent learning replication.',
        'evaluation': 'Electrical reset per input and fully frozen W/u/w. All165 inputs evaluated at baseline, original inheritance, final recall, source erasure and full erasure. Source erasure restores common initial Step3 W/u/w, not post003 memory. Full-network hashes checked before/after batches and at erasures.',
        'gates': {'placement_balanced_accuracy': .90, 'placement_each_present_class_recall': .85,
                  'whole60_gain_over_every_warm_control': .25, 'new44_balanced_accuracy': .90,
                  'new44_gain_over_every_warm_control': .25, 'undo_balanced_accuracy': .90,
                  'undo_class_recall': .85, 'undo_gain_over_every_warm_control': .25,
                  'familiar_correct': 16, 'sequence_each_stratum_each_view': .90},
        'sequence': '160 distinct split-specific puzzles, each in base/shift/small. Unchanged fixed menu and stack driver with selected occupancy encoder. Every action reuses an exact measured frozen-input response; no solver filtering, repaired moves or teacher metadata selects an action.',
        'limits': 'Empty contexts remain silent and outside the nonempty gate. Engineered recognition, attention, occupancy banks, Undo context codes, menu and stack remain supplied. New44 is fixed by routing, not baseline mistakes. Prior failures remain failed. Reserved coverage aliases trained finite neural inputs. Full stage can pass only after committed controlled development and frozen heldout confirmation.'}
    if development_protocol is not None:
        for name in ('parameters', 'decoder', 'primary_policy', 'selected_epochs', 'undo_KC_ids', 'occupancy_KC_ids', 'views', 'gates'):
            assert protocol[name] == development_protocol[name]
    (args.out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')

    expected_baseline = {}
    expected_selected = {}
    for row in records(args.pilot / 'neural.jsonl'):
        if row['phase'] == 'baseline':
            expected_baseline[row['input']] = row
        elif row['phase'] == 'recall' and row['epoch'] == selected[(row['seed'], row['mapping'])]['epoch']:
            expected_selected[(row['seed'], row['mapping'], row['input'])] = row
    assert set(expected_baseline) == set(inputs)
    assert set(expected_selected) == {(seed, mapping, key) for seed, mapping in CONDITIONS for key in inputs}
    expected_heldout = {}
    if args.development is not None:
        for row in records(args.development / 'neural.jsonl.gz'):
            if row['phase'] == 'recall':
                expected_heldout[(row['seed'], row['mapping'], row['arm'], row['input'])] = row
        assert len(expected_heldout) == 16 * 165
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    offset, threshold = (pp['decoder'][k] for k in ('offset_hz', 'threshold_hz'))
    neural_log = gzip.open(args.out / 'neural.jsonl.gz', 'xt', compresslevel=6)
    training_log = gzip.open(args.out / 'training.jsonl.gz', 'xt', compresslevel=6)
    weight_checks, references, reproduction = [], [], []
    measured = training_trials = 0

    def measure(indices=None, duration=500, pulse=None, learning=False, frozen=True, traced=False):
        brain.weights_frozen = frozen
        before = memory_state(brain)
        stimulation = [] if indices is None else [(indices, parameters['KC_current'])]
        if pulse is not None:
            stimulation.append((circuit[pulse], parameters['DAN_current']))
        boundaries = list(range(0, 101, 4)) + list(range(110, 501, 10)) if traced else [0, duration]
        counts = np.zeros(brain.n, dtype=np.int32)
        trace = []
        for start, end in zip(boundaries, boundaries[1:]):
            chunk, _ = brain.step(dark, end - start, stimulation=stimulation, learning=learning, lamina_bias=0)
            counts += chunk
            if traced:
                trace.append({'start_ms': start, 'end_ms': end, 'selected_KC_counts': chunk[indices].tolist(),
                              'output_counts': {name: chunk[ix].tolist() for name, ix in outputs.items()}})
        hz = {name: float(counts[ix].mean() * 1000 / duration) for name, ix in outputs.items()}
        score = hz['MBON11'] - hz['MBON07'] - offset
        after = memory_state(brain)
        if frozen:
            assert before == after
        return {'duration_ms': duration, 'pulse': pulse, 'learning': learning, 'frozen': frozen,
                'output_hz': hz, 'score_hz': score,
                'action': 1 if score >= threshold else 0 if score <= -threshold else -1,
                'spikes_sha256': hashlib.sha256(counts.tobytes()).hexdigest(),
                'memory_before': before, 'memory_after': after, 'trace': trace,
                'KC_spikes': int(counts[circuit['kc']].sum()),
                'DAN_spikes': {name: int(counts[circuit[name]].sum()) for name in ('reward', 'aversive')}}

    def evaluate(context, expected=None):
        nonlocal measured
        before = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        result = {}
        for key, indices in inputs.items():
            brain.reset(keep_memory=True)
            row = measure(indices, traced=True)
            if expected is not None:
                check_measure(row, expected[key], trace=True)
            result[key] = row
            neural_log.write(json.dumps({**context, 'input': key, **row}, allow_nan=False) + '\n')
            measured += 1
        neural_log.flush()
        after = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        assert before == after
        weight_checks.append({**context, 'inputs': len(result), 'before_sha256': before, 'after_sha256': after})
        return result

    def load_memory(path):
        brain.reset(keep_memory=False)
        with np.load(path, allow_pickle=False) as saved:
            assert np.array_equal(saved['edge_indices'], circuit['edges'])
            brain.weight[circuit['edges']] = saved['weights']
            brain.memory_u[:] = saved['u']
            brain.memory_w[:] = saved['w']
        references.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})

    def compare_checkpoint(path, context):
        with np.load(path, allow_pickle=False) as expected:
            assert np.array_equal(expected['edge_indices'], circuit['edges'])
            assert np.array_equal(brain.weight[circuit['edges']], expected['weights'])
            assert np.array_equal(brain.memory_u, expected['u'])
            assert np.array_equal(brain.memory_w, expected['w'])
        reproduction.append({**context, 'checkpoint': str(path.relative_to(ROOT)), 'sha256': sha(path), 'W_u_w_exact': True})

    def score(responses, mapping):
        def semantic(contexts):
            raw = [responses[r['input']]['action'] for r in contexts]
            return np.asarray([a if a == -1 else a ^ mapping for a in raw])
        placement = probe_metrics(primary_contexts, semantic(primary_contexts))
        new = classification_metrics(np.asarray([r['label'] for r in new_contexts]), semantic(new_contexts))
        undo = classification_metrics(np.asarray([r['label'] for r in undo_contexts]), semantic(undo_contexts))
        undo['minimum_target_margin_hz'] = min((1 if r['label'] ^ mapping else -1) * responses[r['input']]['score_hz'] - threshold for r in undo_contexts)
        retained = sum(responses[key]['action'] == (label ^ mapping) for key, label in familiar.items())
        return {'placement': placement, 'new44': new, 'undo': undo, 'familiar_correct': retained}

    brain.reset(keep_memory=False)
    baseline = evaluate({'phase': 'baseline'}, expected_baseline)
    results = []
    with gzip.open(args.out / 'episodes.jsonl.gz', 'xt', compresslevel=6) as episodes:
        for seed, mapping in CONDITIONS:
            initial_path = SOURCE / f'{seed}-{mapping}-paired-memory.npz'
            load_memory(initial_path)
            source_run = next(r for r in source_summary['runs'] if (r['seed'], r['mapping']) == (seed, mapping))
            inherited_state = memory_state(brain)
            assert inherited_state == source_run['arms']['paired']['memory']
            inherited_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
            inherited = evaluate({'seed': seed, 'mapping': mapping, 'phase': 'inherited'})
            arms = {}
            entries = schedules[f'{seed}-{mapping}']
            for arm in ARMS:
                load_memory(initial_path)
                assert memory_state(brain) == inherited_state
                actual_update_ms = 0
                doses = Counter()
                if args.split == 'development':
                    for trial, entry in enumerate(entries):
                        expected = reference_trials[(seed, mapping, trial)]
                        target = entry['semantic_target'] if arm != 'inconsistent' or not entry['teach'] else entry['inconsistent_semantic_target']
                        raw_target = target ^ mapping
                        pulse = None if arm == 'no_feedback' else 'reward' if raw_target else 'aversive'
                        brain.reset(keep_memory=True)
                        decision = measure(inputs[entry['input']])
                        phases = []
                        if entry['teach']:
                            phases.extend([measure(duration=200, pulse=pulse, learning=arm != 'frozen', frozen=arm == 'frozen'),
                                           measure(duration=250, frozen=arm == 'frozen')])
                            if entry['phase_count'] == 5:
                                brain.reset(keep_memory=True)
                                opposite = None if pulse is None else 'aversive' if pulse == 'reward' else 'reward'
                                phases.extend([measure(duration=200, pulse=opposite),
                                               measure(inputs[entry['input']], learning=arm != 'frozen', frozen=arm == 'frozen'),
                                               measure(duration=250, frozen=arm == 'frozen')])
                        assert len(phases) == entry['phase_count']
                        if arm == 'paired':
                            check_measure(decision, expected['decision'])
                            for actual_phase, reference_phase in zip(phases, expected['phases']):
                                check_measure(actual_phase, reference_phase)
                        for phase in phases:
                            if not phase['frozen']:
                                actual_update_ms += phase['duration_ms']
                            if phase['pulse'] is not None:
                                doses[phase['pulse']] += phase['duration_ms']
                        training_log.write(json.dumps({'seed': seed, 'mapping': mapping, 'arm': arm, 'trial': trial,
                            **entry, 'taught_raw_target': raw_target if entry['teach'] else None,
                            'decision': decision, 'phases': phases}, allow_nan=False) + '\n')
                        training_trials += 1
                        if entry['stage'] == 'undo_prefix' and entry['source_trial'] == 59:
                            if arm == 'paired':
                                compare_checkpoint(prefix / f'{seed}-{mapping}-paired-memory.npz', {'seed': seed, 'mapping': mapping, 'stage': 'prefix'})
                            training_log.flush()
                            print(json.dumps({'seed': seed, 'mapping': mapping, 'arm': arm, 'prefix_complete': True}), flush=True)
                        if entry['stage'] == 'joint' and entry['source_trial'] == 75:
                            if arm == 'paired':
                                history = next(r for r in pilot_summary['runs'] if (r['seed'], r['mapping']) == (seed, mapping))['history']
                                epoch_checkpoint = next(h['checkpoint'] for h in history if h['epoch'] == entry['source_epoch'])
                                compare_checkpoint(args.pilot / epoch_checkpoint, {'seed': seed, 'mapping': mapping, 'stage': 'joint', 'epoch': entry['source_epoch']})
                            training_log.flush()
                            print(json.dumps({'seed': seed, 'mapping': mapping, 'arm': arm, 'epoch_complete': entry['source_epoch']}), flush=True)
                    expected_update = 0 if arm == 'frozen' else sum(e['update_window_ms'] for e in entries)
                    assert actual_update_ms == expected_update
                    np.savez_compressed(args.out / f'{seed}-{mapping}-{arm}-memory.npz', edge_indices=circuit['edges'],
                        weights=brain.weight[circuit['edges']], u=brain.memory_u, w=brain.memory_w)
                    if arm == 'paired':
                        compare_checkpoint(args.pilot / selected[(seed, mapping)]['checkpoint'], {'seed': seed, 'mapping': mapping, 'stage': 'selected_final'})
                else:
                    load_memory(args.development / f'{seed}-{mapping}-{arm}-memory.npz')
                state = memory_state(brain)
                expected = ({key: expected_heldout[(seed, mapping, arm, key)] for key in inputs}
                            if args.split == 'heldout' else
                            {key: expected_selected[(seed, mapping, key)] for key in inputs}
                            if arm == 'paired' else inherited if arm == 'frozen' else None)
                responses = evaluate({'seed': seed, 'mapping': mapping, 'arm': arm, 'phase': 'recall'}, expected)
                scored = score(responses, mapping)
                sequence = defaultdict(lambda: {'puzzles': 0, 'solved': 0, 'undo_count': 0, 'timeouts': 0, 'repeated_state': 0})
                for case in cases:
                    if case['split'] != args.split:
                        continue
                    for view in VIEWS:
                        result = play_with_undo(case, responses, templates, groups, undo_groups, primary_policy, mapping,
                                                view=view, placement_encoder=placement_encoder)
                        episodes.write(json.dumps({'seed': seed, 'mapping': mapping, 'arm': arm,
                            'policy': primary_policy, 'view': view, **result}, allow_nan=False) + '\n')
                        key = f"{case['blank_count']}-{case['stratum']}-{view}"
                        sequence[key]['puzzles'] += 1
                        sequence[key]['solved'] += result['solved']
                        sequence[key]['undo_count'] += result['undo_count']
                        sequence[key]['timeouts'] += result['timeouts']
                        sequence[key]['repeated_state'] += result['end'] == 'repeated_state'
                assert len(sequence) == 15 and all(v['puzzles'] == 32 for v in sequence.values())
                for value in sequence.values():
                    value['solve_rate'] = value['solved'] / value['puzzles']
                brain.weight[circuit['edges']] = brain.baseline_plastic
                assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
                load_memory(initial_path)
                assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == inherited_full
                evaluate({'seed': seed, 'mapping': mapping, 'arm': arm, 'phase': 'source_erased'}, inherited)
                brain.reset(keep_memory=False)
                assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
                evaluate({'seed': seed, 'mapping': mapping, 'arm': arm, 'phase': 'erased'}, baseline)
                if arm == 'frozen':
                    assert state == inherited_state
                    assert all(responses[k]['spikes_sha256'] == inherited[k]['spikes_sha256'] for k in inputs)
                arms[arm] = {'scores': scored, 'sequence': dict(sequence), 'memory': state,
                    'training_trials': len(entries) if args.split == 'development' else 0,
                    'update_window_ms': actual_update_ms, 'DAN_pulse_duration_ms': dict(doses),
                    'source_erasure_exact': True, 'full_erasure_exact': True, 'nonplastic_unchanged': True}
                print(json.dumps({'seed': seed, 'mapping': mapping, 'arm': arm,
                    'whole60': scored['placement']['nonempty']['balanced_accuracy'], 'new44': scored['new44']['balanced_accuracy'],
                    'undo': scored['undo']['balanced_accuracy'], 'familiar': scored['familiar_correct'],
                    'minimum_stratum_view_solve': min(v['solve_rate'] for v in sequence.values())}), flush=True)
            paired = arms['paired']['scores']
            gaps = {arm: {'whole60': paired['placement']['nonempty']['balanced_accuracy'] - arms[arm]['scores']['placement']['nonempty']['balanced_accuracy'],
                          'new44': paired['new44']['balanced_accuracy'] - arms[arm]['scores']['new44']['balanced_accuracy'],
                          'undo': paired['undo']['balanced_accuracy'] - arms[arm]['scores']['undo']['balanced_accuracy']}
                    for arm in ARMS[1:]}
            gates = {
                'placement_absolute': paired['placement']['nonempty']['balanced_accuracy'] >= .90 and
                    all(recall >= .85 for n, row in paired['placement']['by_distinct_peers'].items() if n != '0' for recall in row['class_recall'].values()),
                'whole60_control_gain': all(row['whole60'] >= .25 for row in gaps.values()),
                'new44_absolute': paired['new44']['balanced_accuracy'] >= .90,
                'new44_control_gain': all(row['new44'] >= .25 for row in gaps.values()),
                'undo_absolute': paired['undo']['balanced_accuracy'] >= .90 and min(paired['undo']['class_recall'].values()) >= .85,
                'undo_control_gain': all(row['undo'] >= .25 for row in gaps.values()),
                'familiar_retention': paired['familiar_correct'] == 16,
                'sequence_each_stratum_view': all(v['solve_rate'] >= .90 for v in arms['paired']['sequence'].values())}
            results.append({'seed': seed, 'mapping': mapping, 'arms': arms, 'control_gaps': gaps,
                            'gates': gates, 'gate_passed': all(gates.values())})
            (args.out / 'partial-results.json').write_text(json.dumps(results, indent=2) + '\n')
    neural_log.close()
    training_log.close()
    for name, value in (('full-weight-checks.json', weight_checks), ('memory-references.json', references),
                        ('paired-reproduction.json', reproduction)):
        (args.out / name).write_text(json.dumps(value, indent=2) + '\n')
    assert measured == 165 * 53
    if args.split == 'development':
        assert training_trials == 4 * sum(len(s) for s in schedules.values())
        assert len(reproduction) == sum(selected[c]['epoch'] + 2 for c in CONDITIONS)
    else:
        assert training_trials == 0 and not reproduction
    passed = all(r['gate_passed'] for r in results)
    summary = {'split': args.split, 'gate_passed': passed, 'stage5_complete': args.split == 'heldout' and passed,
        'no_new_learning': args.split == 'heldout', 'controls_evaluated': True,
        'pilot_summary_sha256': sha(args.pilot / 'summary.json'),
        'development_summary_sha256': None if args.development is None else sha(args.development / 'summary.json'),
        'runs': results, 'measured_neural_evaluations': measured, 'training_trials': training_trials,
        'physical_inputs': len(inputs), 'distinct_puzzles': 160, 'views': list(VIEWS), 'episodes': 16 * 160 * len(VIEWS),
        'elapsed_seconds': time.perf_counter() - started,
        'files_sha256': {path.name: sha(path) for path in sorted(args.out.iterdir()) if path.is_file()}}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: summary[key] for key in ('split', 'gate_passed', 'stage5_complete', 'training_trials', 'elapsed_seconds')}), flush=True)


if __name__ == '__main__':
    main()
