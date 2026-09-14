"""Frozen selective Undo-memory erasure within the trained placement policy.

A contribution to this paired policy is distinct from necessity for Sudoku:
all original warm-control completion results remain visible in the summary.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

ROOT = Path.cwd().resolve()
if not (ROOT / 'sudokufly.py').is_file():
    raise RuntimeError('Run from the sudokufly repository root')
sys.path.insert(0, str(ROOT))
from confirm_sudoku import CONDITIONS, VIEWS, check_measure, records, require_committed, sha, verify_run
from joint_sudoku import encode_occupancy
from learn_undo import play_with_undo
from one_blank import classification_metrics
from sudokufly import UPSTREAM, UPSTREAM_COMMIT, memory_state


def behavior_differences(actual, expected):
    """Compare neural behavior while deliberately excluding global memory hashes."""
    fields = ('duration_ms', 'pulse', 'learning', 'frozen', 'output_hz', 'score_hz',
              'action', 'spikes_sha256', 'KC_spikes', 'DAN_spikes', 'trace')
    if not all(k in actual and k in expected for k in fields):
        raise RuntimeError('Missing a required neural behavior comparison field')
    return [k for k in fields if actual[k] != expected[k]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Passing 007 result directory for this split')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--split', choices=('development', 'heldout'), default='development')
    parser.add_argument('--development', type=Path, help='Committed passing 008 development, required for heldout')
    args = parser.parse_args()
    if (args.split == 'heldout') != (args.development is not None):
        parser.error('--development is required only for heldout')
    started = time.perf_counter()
    args.source, args.out = args.source.resolve(), args.out.resolve()
    if args.development is not None:
        args.development = args.development.resolve()
    runner = Path(__file__).resolve()
    if runner.parent != ROOT:
        raise RuntimeError('Copy the candidate into the repository, review, and commit before running')
    summary007, protocol007 = verify_run(args.source)
    assert summary007['gate_passed'] and summary007['split'] == args.split
    assert protocol007['split'] == args.split and protocol007['primary_policy'] == 'separate-occupancy'
    assert tuple((r['seed'], r['mapping']) for r in summary007['runs']) == CONDITIONS
    assert tuple(protocol007['views']) == VIEWS
    assert all(r['gate_passed'] and all(r['gates'].values()) for r in summary007['runs'])
    require_committed([args.source / 'summary.json'] +
                      [args.source / name for name in summary007['files_sha256']])
    source_paths = [runner] + [ROOT / name for name in protocol007['source_sha256']]
    source_hashes = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    for name, digest in protocol007['source_sha256'].items():
        assert source_hashes[name] == digest, ('007 source changed', name)
        committed = subprocess.check_output(['git', 'show', f"{protocol007['git_head']}:{name}"], cwd=ROOT)
        assert hashlib.sha256(committed).hexdigest() == digest
    require_committed(source_paths)
    source007dev = args.source if args.split == 'development' else ROOT / protocol007['development']
    if args.split == 'heldout':
        assert summary007['stage5_complete'] and summary007['no_new_learning']
        summary007dev, protocol007dev = verify_run(source007dev)
        assert summary007dev['gate_passed'] and summary007dev['split'] == 'development'
        assert protocol007['development_summary_sha256'] == sha(source007dev / 'summary.json')
        assert protocol007['source_sha256'] == protocol007dev['source_sha256']
        require_committed([source007dev / 'summary.json'] +
                          [source007dev / name for name in summary007dev['files_sha256']])
    original = ROOT / protocol007['memory_source']
    original_summary, original_protocol = verify_run(original)
    assert original_summary['gate_passed']
    assert sha(original / 'summary.json') == protocol007['memory_summary_sha256']
    cases_path = ROOT / protocol007['cases_source']
    assert sha(cases_path) == protocol007['cases_sha256']
    cases = [c for c in json.loads(cases_path.read_text()) if c['split'] == args.split]
    assert len(cases) == 160 and len({c['id'] for c in cases}) == 160
    assert sum(c['stratum'] == 'trap' for c in cases) == 64
    inputs_manifest = json.loads((args.source / 'inputs.json').read_text())
    undo_contexts = json.loads((args.source / 'undo-contexts.json').read_text())
    undo_keys = {r['input'] for r in undo_contexts}
    assert len(inputs_manifest) == 165 and len(undo_contexts) == len(undo_keys) == 16
    assert undo_keys <= inputs_manifest.keys()
    development_summary = development_protocol = None
    expected008 = {}
    if args.development is not None:
        development_summary, development_protocol = verify_run(args.development)
        assert development_summary['gate_passed'] and development_summary['split'] == 'development'
        assert development_protocol['source_sha256'] == source_hashes
        assert development_protocol['source007'] == str(source007dev.relative_to(ROOT))
        assert development_protocol['source007_summary_sha256'] == sha(source007dev / 'summary.json')
        require_committed([args.development / 'summary.json'] +
                          [args.development / name for name in development_summary['files_sha256']])
        for row in records(args.development / 'neural.jsonl.gz'):
            expected008[(row['seed'], row['mapping'], row['phase'], row['input'])] = row
        assert set(expected008) == {(s, m, phase, key) for s, m in CONDITIONS
                                   for phase in ('intact', 'undo_erased', 'restored') for key in inputs_manifest}
    expected007, inherited007 = {}, {}
    for row in records(args.source / 'neural.jsonl.gz'):
        if row['phase'] == 'recall' and row['arm'] == 'paired':
            expected007[(row['seed'], row['mapping'], row['input'])] = row
        elif row['phase'] == 'inherited':
            inherited007[(row['seed'], row['mapping'], row['input'])] = row
    expected_keys = {(s, m, key) for s, m in CONDITIONS for key in inputs_manifest}
    assert set(expected007) == set(inherited007) == expected_keys
    expected_full = {(r['seed'], r['mapping']): r['before_sha256']
                     for r in json.loads((args.source / 'full-weight-checks.json').read_text())
                     if r['phase'] == 'recall' and r['arm'] == 'paired'}
    assert set(expected_full) == set(CONDITIONS)
    expected_episodes = (r for r in records(args.source / 'episodes.jsonl.gz') if r['arm'] == 'paired')
    upstream = subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(UPSTREAM), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    assert upstream == UPSTREAM_COMMIT and not dirty

    args.out.mkdir(parents=True, exist_ok=False)
    os.environ['STONKFLY_DATA'] = str(ROOT / 'data')
    sys.path.insert(0, str(UPSTREAM))
    from stonkfly.data import verify
    from stonkfly.neural.brain import MemoryBrain
    from stonkfly.neural.common import annotations
    graph = verify()
    parameters = protocol007['parameters']
    brain = MemoryBrain(eta=parameters['eta'])
    circuit = brain.circuit
    assert len(circuit['edges']) == 7835
    annotation = annotations(brain.ids)
    outputs = {name: np.flatnonzero(annotation.type.eq(name)) for name in ('MBON07', 'MBON11')}
    for indices in outputs.values():
        brain.tonic[indices] = parameters['MBON_current']
    initial_hash = hashlib.sha256(brain.weight.tobytes()).hexdigest()
    assert initial_hash == protocol007['initial_weights_sha256']
    positions = {int(cell): i for i, cell in enumerate(brain.ids)}
    sensory_path = ROOT / original_protocol['memory_source'] / 'protocol.json'
    assert sha(sensory_path) == original_protocol['memory_protocol_sha256']
    sensory = json.loads(sensory_path.read_text())
    templates = np.asarray(sensory['templates'], dtype=np.float64)
    groups = np.asarray([positions[int(c)] for c in np.asarray(sensory['group_KC_ids']).ravel()], dtype=np.int32).reshape(16, 2, 8)
    undo_groups = np.asarray([positions[int(c)] for c in np.asarray(protocol007['undo_KC_ids']).ravel()], dtype=np.int32).reshape(16, 16)
    occupancy_groups = {int(n): np.asarray([positions[int(c)] for c in np.asarray(bank).ravel()], dtype=np.int32).reshape(16, 2, 8)
                        for n, bank in protocol007['occupancy_KC_ids'].items()}
    assert set(occupancy_groups) == {1, 2, 4}
    all_placement = np.concatenate([groups.ravel()] + [bank.ravel() for bank in occupancy_groups.values()])
    assert len(np.unique(all_placement)) == 1024 and len(np.unique(undo_groups)) == 256
    assert not np.any(np.isin(undo_groups, all_placement))
    inputs = {key: np.asarray([positions[int(cell)] for cell in row['KC_ids']], dtype=np.int32)
              for key, row in inputs_manifest.items()}
    for key, indices in inputs.items():
        assert np.array_equal(indices, np.unique(indices)) and hashlib.sha256(indices.tobytes()).hexdigest() == key
        is_undo = np.isin(indices, undo_groups)
        assert (len(indices) == 16 and np.all(is_undo)) if key in undo_keys else not np.any(is_undo)
    mask = np.isin(circuit['pre'], undo_groups)
    assert mask.shape == circuit['edges'].shape and int(mask.sum()) == 892
    assert np.array_equal(circuit['pre'], (np.searchsorted(brain.ptr, circuit['edges'], side='right') - 1).astype(np.int32))
    assert np.all(np.isin(brain.post[circuit['edges'][mask]], np.concatenate(list(outputs.values()))))
    mask_report = {'plastic_edges': 7835, 'undo_edges': int(mask.sum()),
                   'undo_KC_ids': protocol007['undo_KC_ids'], 'selected_slots': np.flatnonzero(mask).tolist(),
                   'selected_edge_indices': circuit['edges'][mask].tolist(),
                   'selected_presynaptic_KC_ids': brain.ids[circuit['pre'][mask]].tolist(),
                   'selected_edges_sha256': hashlib.sha256(circuit['edges'][mask].tobytes()).hexdigest(),
                   'mask_sha256': hashlib.sha256(mask.tobytes()).hexdigest(),
                   'non_undo_inputs': 149, 'direct_input_banks_disjoint': True}
    gates_protocol = {'intact_undo_balanced_accuracy': .90, 'undo_accuracy_loss': .25,
                      'each_condition_view_all64trap_solve_loss': .25,
                      'intact_each_stratum_view_solve_rate': .90,
                      'non_undo_behavior_exact': True, 'erased_undo_behavior_matches_original': True,
                      'source007_all_gates_required': True}
    protocol = {'task': 'Selective Undo-memory ablation within the fixed paired placement policy',
                'split': args.split, 'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'source_sha256': source_hashes, 'upstream': upstream, 'graph': graph,
                'initial_weights_sha256': initial_hash, 'parameters': parameters, 'decoder': protocol007['decoder'],
                'source007': str(args.source.relative_to(ROOT)), 'source007_summary_sha256': sha(args.source / 'summary.json'),
                'source007_development': str(source007dev.relative_to(ROOT)),
                'source007_development_summary_sha256': sha(source007dev / 'summary.json'),
                'original_memory_source': str(original.relative_to(ROOT)), 'original_memory_summary_sha256': sha(original / 'summary.json'),
                'cases_source': str(cases_path.relative_to(ROOT)), 'cases_sha256': sha(cases_path),
                'development': None if args.development is None else str(args.development.relative_to(ROOT)),
                'development_summary_sha256': None if args.development is None else sha(args.development / 'summary.json'),
                'primary_policy': protocol007['primary_policy'], 'views': list(VIEWS), 'gates': gates_protocol,
                'undo_KC_ids': protocol007['undo_KC_ids'], 'occupancy_KC_ids': protocol007['occupancy_KC_ids'],
                'mask_sha256': mask_report['mask_sha256'], 'physical_inputs': 165,
                'intervention': 'All892 existing plastic edges with an Undo-bank presynaptic KC receive that condition original paired Step3 W/u/w. All remaining plastic/nonplastic weights and latent memory retain final paired007 values. No training, DAN pulses, additional warm-control training or action overrides.',
                'evaluation': 'All165 inputs in intact, Undo-erased and restored states, electrically reset per input and fully frozen. Intact/restored reproduce007 exactly. All149 non-Undo inputs must retain exact full spike hashes, outputs and traces after erasure; all16 Undo inputs must match original007 inheritance behavior. Global memory hashes are checked within each state, not equated across different memories.',
                'episodes': 'Same160 split-specific boards and three views, both intact and erased, allfour conditions. Intact episodes reproduce007 exactly. Primary denominator is all64 predefined trap boards in each view; no selection by solved status or Undo use.',
                'interpretation': 'An effect identifies a contribution of newly learned Undo within this trained placement policy. It cannot show learning is necessary for Sudoku completion or that this policy beats warm controls; original control completion results remain reported. Views reuse finite neural inputs and are not independent learning replications.',
                'training_trials': 0}
    if development_protocol is not None:
        for name in ('source_sha256', 'parameters', 'decoder', 'primary_policy', 'views', 'gates',
                     'undo_KC_ids', 'occupancy_KC_ids', 'mask_sha256', 'cases_sha256', 'original_memory_summary_sha256'):
            assert protocol[name] == development_protocol[name]
    for name, value in (('protocol.json', protocol), ('ablation-mask.json', mask_report),
                        ('inputs.json', inputs_manifest), ('undo-contexts.json', undo_contexts)):
        (args.out / name).write_text(json.dumps(value, indent=2) + '\n')
    placement_encoder = lambda frame, bank, cells, policy: encode_occupancy(frame, bank, cells, occupancy_groups)
    dark = np.zeros(len(brain.retina), dtype=np.float32)
    offset, threshold = (protocol007['decoder'][k] for k in ('offset_hz', 'threshold_hz'))
    weight_checks, interventions, references, results = [], [], [], []
    measured = episode_count = 0

    def evaluate(context, expected, compare_behavior=False):
        nonlocal measured
        before_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        before_memory = memory_state(brain)
        responses, differences = {}, {}
        for key, indices in inputs.items():
            brain.reset(keep_memory=True)
            brain.weights_frozen = True
            before = memory_state(brain)
            assert before == before_memory
            counts = np.zeros(brain.n, dtype=np.int32)
            trace = []
            boundaries = list(range(0, 101, 4)) + list(range(110, 501, 10))
            for start, end in zip(boundaries, boundaries[1:]):
                chunk, _ = brain.step(dark, end - start, stimulation=[(indices, parameters['KC_current'])], learning=False, lamina_bias=0)
                counts += chunk
                trace.append({'start_ms': start, 'end_ms': end, 'selected_KC_counts': chunk[indices].tolist(),
                              'output_counts': {name: chunk[ix].tolist() for name, ix in outputs.items()}})
            hz = {name: float(counts[ix].mean() * 1000 / 500) for name, ix in outputs.items()}
            score = hz['MBON11'] - hz['MBON07'] - offset
            after = memory_state(brain)
            assert before == after
            row = {'duration_ms': 500, 'pulse': None, 'learning': False, 'frozen': True,
                   'output_hz': hz, 'score_hz': score,
                   'action': 1 if score >= threshold else 0 if score <= -threshold else -1,
                   'spikes_sha256': hashlib.sha256(counts.tobytes()).hexdigest(),
                   'memory_before': before, 'memory_after': after, 'trace': trace,
                   'KC_spikes': int(counts[circuit['kc']].sum()),
                   'DAN_spikes': {name: int(counts[circuit[name]].sum()) for name in ('reward', 'aversive')}}
            if compare_behavior:
                differing = behavior_differences(row, expected[key])
                if differing:
                    differences[key] = differing
            else:
                check_measure(row, expected[key], trace=True)
            if expected008:
                check_measure(row, expected008[(context['seed'], context['mapping'], context['phase'], key)], trace=True)
            neural_log.write(json.dumps({**context, 'input': key, **row}, allow_nan=False) + '\n')
            responses[key] = row
            measured += 1
        neural_log.flush()
        after_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
        assert before_full == after_full and memory_state(brain) == before_memory
        weight_checks.append({**context, 'inputs': 165, 'before_sha256': before_full,
                              'after_sha256': after_full, 'memory_before': before_memory, 'memory_after': memory_state(brain)})
        return responses, differences

    with gzip.open(args.out / 'neural.jsonl.gz', 'xt', compresslevel=6) as neural_log, \
            gzip.open(args.out / 'episodes.jsonl.gz', 'xt', compresslevel=6) as episode_log:
        for seed, mapping in CONDITIONS:
            checkpoint = source007dev / f'{seed}-{mapping}-paired-memory.npz'
            original_checkpoint = original / f'{seed}-{mapping}-paired-memory.npz'
            references.extend({'path': str(p.relative_to(ROOT)), 'sha256': sha(p)} for p in (checkpoint, original_checkpoint))
            with np.load(checkpoint, allow_pickle=False) as saved, np.load(original_checkpoint, allow_pickle=False) as inherited:
                assert np.array_equal(saved['edge_indices'], circuit['edges'])
                assert np.array_equal(inherited['edge_indices'], circuit['edges'])
                paired = {k: saved[k].copy() for k in ('weights', 'u', 'w')}
                original_values = {k: inherited[k].copy() for k in ('weights', 'u', 'w')}
            assert all(a.shape == mask.shape for a in (*paired.values(), *original_values.values()))
            assert np.array_equal(original_values['weights'][mask], brain.baseline_plastic[mask])
            assert not np.any(original_values['u'][mask]) and not np.any(original_values['w'][mask])
            brain.reset(keep_memory=False)
            brain.weight[circuit['edges']] = paired['weights']
            brain.memory_u[:], brain.memory_w[:] = paired['u'], paired['w']
            intact_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
            assert intact_full == expected_full[(seed, mapping)]
            intact_state = memory_state(brain)
            intact, _ = evaluate({'seed': seed, 'mapping': mapping, 'phase': 'intact'},
                                 {key: expected007[(seed, mapping, key)] for key in inputs})
            hybrid = {k: v.copy() for k, v in paired.items()}
            for key in hybrid:
                hybrid[key][mask] = original_values[key][mask]
                assert np.array_equal(hybrid[key][~mask], paired[key][~mask])
                assert np.array_equal(hybrid[key][mask], original_values[key][mask])
            brain.weight[circuit['edges']] = hybrid['weights']
            brain.memory_u[:], brain.memory_w[:] = hybrid['u'], hybrid['w']
            erased_full = hashlib.sha256(brain.weight.tobytes()).hexdigest()
            erased_state = memory_state(brain)
            np.savez_compressed(args.out / f'{seed}-{mapping}-undo-erased-memory.npz', edge_indices=circuit['edges'], **hybrid)
            if args.development is not None:
                saved_path = args.development / f'{seed}-{mapping}-undo-erased-memory.npz'
                with np.load(saved_path, allow_pickle=False) as prior_hybrid:
                    assert np.array_equal(prior_hybrid['edge_indices'], circuit['edges'])
                    assert all(np.array_equal(prior_hybrid[k], hybrid[k]) for k in hybrid)
                references.append({'path': str(saved_path.relative_to(ROOT)), 'sha256': sha(saved_path)})
            erased, differences = evaluate({'seed': seed, 'mapping': mapping, 'phase': 'undo_erased'},
                {key: inherited007[(seed, mapping, key)] if key in undo_keys else intact[key] for key in inputs}, True)
            brain.weight[circuit['edges']] = paired['weights']
            brain.memory_u[:], brain.memory_w[:] = paired['u'], paired['w']
            assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == intact_full and memory_state(brain) == intact_state
            evaluate({'seed': seed, 'mapping': mapping, 'phase': 'restored'}, intact)
            # Verify that the original full graph is recovered by replacing only
            # its declared plastic slots; nonplastic changes cannot hide here.
            brain.weight[circuit['edges']] = brain.baseline_plastic
            assert hashlib.sha256(brain.weight.tobytes()).hexdigest() == initial_hash
            interventions.append({'seed': seed, 'mapping': mapping, 'intact_full_sha256': intact_full,
                'erased_full_sha256': erased_full, 'restored_full_sha256': intact_full,
                'intact_memory': intact_state, 'erased_memory': erased_state, 'restoration_exact': True,
                'nonplastic_unchanged': True, 'outside_mask_exact': True, 'selected_equals_original': True,
                'changed_entries': {k: int(np.count_nonzero(paired[k] != hybrid[k])) for k in paired},
                'array_sha256': {state: {k: hashlib.sha256(v.tobytes()).hexdigest() for k, v in arrays.items()}
                                 for state, arrays in (('paired', paired), ('original', original_values), ('erased', hybrid))},
                'behavior_differences': differences})
            states, solved = {}, {}
            for state, responses in (('intact', intact), ('undo_erased', erased)):
                action = np.asarray([responses[r['input']]['action'] for r in undo_contexts])
                semantic = np.asarray([a if a == -1 else int(a) ^ mapping for a in action])
                undo = classification_metrics(np.asarray([r['label'] for r in undo_contexts]), semantic)
                undo['minimum_target_margin_hz'] = min(
                    (1 if r['label'] ^ mapping else -1) * responses[r['input']]['score_hz'] - threshold
                    for r in undo_contexts)
                sequence = defaultdict(lambda: {'puzzles': 0, 'solved': 0, 'undo_count': 0, 'timeouts': 0})
                solved[state] = {}
                for case in cases:
                    for view in VIEWS:
                        result = play_with_undo(case, responses, templates, groups, undo_groups,
                            protocol007['primary_policy'], mapping, view=view, placement_encoder=placement_encoder)
                        if state == 'intact':
                            reference = next(expected_episodes)
                            actual = {'seed': seed, 'mapping': mapping, 'arm': 'paired',
                                      'policy': protocol007['primary_policy'], 'view': view, **result}
                            assert actual == reference, ('007 episode reproduction', seed, mapping, case['id'], view)
                        episode_log.write(json.dumps({'seed': seed, 'mapping': mapping, 'state': state,
                            'policy': protocol007['primary_policy'], 'view': view, **result}, allow_nan=False) + '\n')
                        episode_count += 1
                        key = f"{case['blank_count']}-{case['stratum']}-{view}"
                        sequence[key]['puzzles'] += 1
                        sequence[key]['solved'] += result['solved']
                        sequence[key]['undo_count'] += result['undo_count']
                        sequence[key]['timeouts'] += result['timeouts']
                        solved[state][(case['id'], view)] = result['solved']
                assert len(sequence) == 15 and all(r['puzzles'] == 32 for r in sequence.values())
                for row in sequence.values():
                    row['solve_rate'] = row['solved'] / row['puzzles']
                states[state] = {'undo': undo, 'sequence': dict(sequence)}
            trap_effects = {}
            for view in VIEWS:
                keys = [(c['id'], view) for c in cases if c['stratum'] == 'trap']
                assert len(keys) == 64
                intact_count = sum(solved['intact'][k] for k in keys)
                erased_count = sum(solved['undo_erased'][k] for k in keys)
                trap_effects[view] = {'puzzles': 64, 'intact_solved': intact_count, 'erased_solved': erased_count,
                    'intact_solve_rate': intact_count / 64, 'erased_solve_rate': erased_count / 64,
                    'solve_rate_loss': (intact_count - erased_count) / 64,
                    'solved_to_failed': sum(solved['intact'][k] and not solved['undo_erased'][k] for k in keys),
                    'failed_to_solved': sum(not solved['intact'][k] and solved['undo_erased'][k] for k in keys)}
            undo_loss = states['intact']['undo']['balanced_accuracy'] - states['undo_erased']['undo']['balanced_accuracy']
            undo_changed_actions = [
                {'context': i, 'pattern': r['pattern'], 'input': r['input'],
                 'intact_raw_action': intact[r['input']]['action'],
                 'erased_raw_action': erased[r['input']]['action']}
                for i, r in enumerate(undo_contexts)
                if intact[r['input']]['action'] != erased[r['input']]['action']]
            gates = {'source007_all_gates': True, 'non_undo_behavior_exact': not any(k not in undo_keys for k in differences),
                     'erased_undo_behavior_matches_original': not any(k in undo_keys for k in differences),
                     'intact_undo_accuracy': states['intact']['undo']['balanced_accuracy'] >= .90,
                     'undo_accuracy_loss': undo_loss >= .25,
                     'each_view_trap_loss': all(r['solve_rate_loss'] >= .25 for r in trap_effects.values()),
                     'intact_each_stratum_view_recovery': all(r['solve_rate'] >= .90 for r in states['intact']['sequence'].values()),
                     'restoration_exact': True}
            source_run = next(r for r in summary007['runs'] if (r['seed'], r['mapping']) == (seed, mapping))
            results.append({'seed': seed, 'mapping': mapping, 'states': states, 'trap_effects': trap_effects,
                'undo_balanced_accuracy_loss': undo_loss,
                'undo_changed_action_count': len(undo_changed_actions), 'undo_changed_actions': undo_changed_actions,
                'gates': gates, 'gate_passed': all(gates.values()),
                'original_warm_controls': {arm: {'scores': row['scores'], 'sequence': row['sequence']}
                                           for arm, row in source_run['arms'].items() if arm != 'paired'}})
            (args.out / 'partial-results.json').write_text(json.dumps(results, indent=2) + '\n')
            print(json.dumps({'seed': seed, 'mapping': mapping, 'gate_passed': all(gates.values()),
                'undo_accuracy_loss': undo_loss, 'trap_loss_by_view': {v: r['solve_rate_loss'] for v, r in trap_effects.items()}}), flush=True)
    assert next(expected_episodes, None) is None
    assert measured == 4 * 3 * 165 and len(weight_checks) == 12
    assert episode_count == 4 * 2 * 160 * 3
    for name, value in (('full-weight-checks.json', weight_checks), ('interventions.json', interventions),
                        ('memory-references.json', references)):
        (args.out / name).write_text(json.dumps(value, indent=2) + '\n')
    passed = all(r['gate_passed'] for r in results)
    summary = {'split': args.split, 'gate_passed': passed, 'causal_recovery_confirmed': args.split == 'heldout' and passed,
        'stage5_complete': args.split == 'heldout' and passed, 'no_new_learning': True, 'training_trials': 0,
        'source007_summary_sha256': sha(args.source / 'summary.json'),
        'development_summary_sha256': None if args.development is None else sha(args.development / 'summary.json'),
        'runs': results, 'measured_neural_evaluations': measured, 'physical_inputs': 165,
        'episodes': episode_count, 'distinct_puzzles': 160, 'views': list(VIEWS),
        'claim_scope': 'Conditional Undo contribution within the paired placement policy; not necessity for Sudoku completion or superiority over original warm controls.',
        'elapsed_seconds': time.perf_counter() - started,
        'files_sha256': {p.name: sha(p) for p in sorted(args.out.iterdir()) if p.is_file()}}
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('split', 'gate_passed', 'causal_recovery_confirmed', 'elapsed_seconds')}), flush=True)


if __name__ == '__main__':
    main()
