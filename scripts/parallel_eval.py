#!/usr/bin/env python3
"""Bounded two-lane CPU-only evaluation with independent checkouts."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
import workflow_eval as common
from context_eval import snapshot

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = ('parallel_eval.py', 'workflow_eval.py', 'context_eval.py', 'usage.py', 'isolated_codex.py')


def prepare(output, case, isolated=False, parallel_first=False, pairs=2):
    config = common.read(case / 'case.json')
    lanes = config['lanes']
    if len(lanes) != 2 or set(lanes[0]['owned_paths']) & set(lanes[1]['owned_paths']):
        raise ValueError('exactly two disjoint lanes required')
    if set(config['owned_paths']) != set().union(*(set(l['owned_paths']) for l in lanes)):
        raise ValueError('lane ownership must cover entire task')
    if output.exists():
        raise ValueError('fresh output directory required')
    output.mkdir(parents=True)
    shutil.copytree(case / 'fixture', output / 'frozen', ignore=shutil.ignore_patterns('__pycache__'))
    for name in ('task.md', 'grade.py'):
        shutil.copy(case / name, output / name)
    (output / 'runner').mkdir()
    for name in DEPENDENCIES:
        shutil.copy(ROOT / 'scripts' / name, output / 'runner' / name)
    baseline = common.check(output / 'frozen', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    if baseline['returncode']:
        raise ValueError('baseline failed')
    manifest = dict(config, format='parallel-workflow-v1', prepared_at=datetime.now(timezone.utc).isoformat(),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        cli_version=subprocess.check_output(['codex', '--version'], text=True).strip(),
        isolated_runtime=isolated, parent_model='gpt-6-astra', worker_model='gpt-6-luna', effort='high', service_tier_requested='default',
        metric='weighted_cost', pricing=common.read(common.CASE / 'standard-credit-rates-2026-10-10.json'),
        fixture_hashes=snapshot(output / 'frozen'), task_sha256=common.digest(output / 'task.md'),
        grader_sha256=common.digest(output / 'grade.py'), runner_hashes=snapshot(output / 'runner'),
        order=(['quick', 'direct', 'direct', 'quick'] if parallel_first else ['direct', 'quick', 'quick', 'direct'])[:2*pairs], max_model_calls=4*pairs,
        direct_timeout=240, worker_timeout=180, review_timeout=120,
        success_rule='Two pairs, all quality/scope/acceptance gates and complete telemetry; parallel mean time and cost each <=90% of Direct.',
        stop_rule='Stop immediately on any quality or telemetry failure; stop after first pair on efficiency failure; no retries, repairs or replacement trials.',
        limitations='Exploratory dirty-suite fixture; fresh CLI sessions, not accumulated chat. Setup/test authoring/controller and external approval review excluded. Standard-credit proxy, not subscription-meter usage. Skill remains disabled.')
    common.write(output / 'manifest.json', manifest)
    common.write(output / 'baseline.json', baseline)
    print(json.dumps({'output': str(output), 'baseline': 'passed', 'max_model_calls': 4*pairs}))


def validate(output):
    manifest = common.read(output / 'manifest.json')
    for name, field in (('task.md', 'task_sha256'), ('grade.py', 'grader_sha256')):
        if common.digest(output / name) != manifest[field]:
            raise ValueError('frozen task or grader changed')
    if snapshot(output / 'frozen') != manifest['fixture_hashes'] or snapshot(output / 'runner') != manifest['runner_hashes']:
        raise ValueError('frozen source changed')
    if any(common.digest(ROOT / 'scripts' / name) != manifest['runner_hashes'][name] for name in DEPENDENCIES):
        raise ValueError('runner changed after freeze')
    return manifest


def execute_lane(trial, manifest, lane):
    folder = trial / ('worker-' + lane['id'])
    folder.mkdir()
    project = folder / 'project'
    shutil.copytree(trial.parent / 'frozen', project)
    common.init_project(project)
    prompt = (trial.parent / 'task.md').read_text() + '\nYour assignment is ONLY lane ' + lane['id'] + '.\n'
    prompt += 'Owned paths: ' + ', '.join(lane['owned_paths']) + '. Do not implement or modify the other lane.\n'
    prompt += 'Run these lane checks: ' + json.dumps(lane['commands']) + '. The other formatter may remain unimplemented in your isolated checkout.\n'
    prompt += common.lean_implementation_prompt()
    prompt += '\nNo agents or model calls, coordinator skills, network, GPU operations, dependencies or commits. Stay in this checkout; do not inspect other trials or evaluator files. Return <=150 words of paths, checks and unresolved requirements.\n'
    started_at = datetime.now(timezone.utc).isoformat()
    result = common.invoke(project, folder, manifest['worker_model'], prompt, manifest['worker_timeout'], isolated=manifest.get('isolated_runtime', False))
    result['started_at'] = started_at
    result['finished_at'] = datetime.now(timezone.utc).isoformat()
    evidence = common.collect_evidence(project, manifest['fixture_hashes'], lane['owned_paths'], lane['commands'])
    result['evidence'] = evidence
    result['lane'] = lane['id']
    result['quality_pass'] = result['exit_code'] == 0 and evidence['scope_pass'] and evidence['stable_during_checks'] and all(c['returncode'] == 0 for c in evidence['checks'])
    common.write(folder / 'result.json', result)
    return result


def dispatch(trial, manifest):
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(execute_lane, trial, manifest, lane) for lane in manifest['lanes']]
        # Resolve all attempts so failure never hides the other worker's usage.
        records = []
        for lane, future in zip(manifest['lanes'], futures):
            try:
                records.append(future.result())
            except Exception as error:
                folder = trial / ('worker-' + lane['id'])
                folder.mkdir(exist_ok=True)
                path = folder / 'result.json'
                result = common.read(path) if path.exists() else {
                    'model_requested': manifest['worker_model'],
                    'usage': {field: None for field in common.FIELDS}}
                result.update(lane=lane['id'], exit_code=125, quality_pass=False,
                              infrastructure_error=type(error).__name__ + ': ' + str(error))
                common.write(path, result)
                records.append(result)
        return records


def merge(trial, manifest, records):
    if len(records) != 2 or any(not r['quality_pass'] for r in records):
        return False
    if snapshot(trial / 'project') != manifest['fixture_hashes']:
        raise ValueError('integration checkout changed before merge')
    for lane, record in zip(manifest['lanes'], records):
        source = trial / ('worker-' + lane['id']) / 'project'
        if record['lane'] != lane['id'] or snapshot(source) != record['evidence']['source_hashes']:
            raise ValueError('worker evidence no longer current')
        changed = {name for name in set(record['evidence']['source_hashes']) | set(manifest['fixture_hashes']) if record['evidence']['source_hashes'].get(name) != manifest['fixture_hashes'].get(name)}
        if changed != set(lane['owned_paths']):
            raise ValueError('worker changed protected paths')
        for name in lane['owned_paths']:
            path = source / name
            if not path.is_file() or path.is_symlink():
                raise ValueError('missing or symlinked artifact')
    for lane in manifest['lanes']:
        for name in lane['owned_paths']:
            target = trial / 'project' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(trial / ('worker-' + lane['id']) / 'project' / name, target)
    return True


def run_one(output):
    m = validate(output)
    summary = common.summarize(output)
    if summary['complete'] or summary['early_stop']:
        print(json.dumps(summary, indent=2)); return
    sequence = summary['trials']
    if len(list(output.glob('trial-*'))) != sequence:
        raise ValueError('interrupted trial retained; no replacement')
    arm = m['order'][sequence]
    trial = output / f'trial-{sequence+1:02d}'
    trial.mkdir()
    shutil.copytree(output / 'frozen', trial / 'project')
    common.init_project(trial / 'project')
    (trial / 'root').mkdir()
    task = (output / 'task.md').read_text()
    constraints = '\nCPU only. Do not delegate, launch models, load skills, install dependencies, use network/GPU, or commit. Work inside this checkout; do not inspect evaluator files or other trials.\n'
    workers = []; root = None; evidence = None; parallel_seconds = None
    start = time.monotonic()
    if arm == 'direct':
        root = common.invoke(trial / 'project', trial / 'root', m['parent_model'], task + '\nImplement BOTH lanes yourself; inspect the final diff and run the listed checks.\n' + constraints, m['direct_timeout'], True, isolated=m.get('isolated_runtime', False))
    else:
        lane_start = time.monotonic()
        workers = dispatch(trial, m)
        parallel_seconds = round(time.monotonic() - lane_start, 3)
        if merge(trial, m, workers):
            evidence = common.collect_evidence(trial / 'project', m['fixture_hashes'], m['owned_paths'], m['commands'])
            common.write(trial / 'integration-evidence.json', evidence)
            if evidence['scope_pass'] and evidence['stable_during_checks'] and all(c['returncode'] == 0 for c in evidence['checks']):
                prompt = task + '\nTwo independent workers have completed their lanes. Review the merged result; do not implement or repair. Read ' + str(trial / 'integration-evidence.json') + ' for the full diff, source hashes and protected checks. Reuse passing checks on unchanged source. Probe only concrete uncovered requirements; do not add unrelated validation. Return the required acceptance decision. You may read that named evidence file outside the checkout.\n' + constraints
                root = common.invoke(trial / 'project', trial / 'root', m['parent_model'], prompt, m['review_timeout'], True, isolated=m.get('isolated_runtime', False))
    seconds = round(time.monotonic() - start, 3)
    after = snapshot(trial / 'project')
    changed = sorted(k for k in set(after) | set(m['fixture_hashes']) if after.get(k) != m['fixture_hashes'].get(k))
    scope = set(changed) == set(m['owned_paths'])
    current = bool(evidence and after == evidence['source_hashes'])
    topology = not workers if arm == 'direct' else len(workers) == 2 and all(r['quality_pass'] for r in workers) and current
    checks = evidence['checks'] if current else [common.check(trial / 'project', c) for c in m['commands']]
    shutil.copy(output / 'grade.py', trial / 'project/test_hidden.py')
    checks.append(common.check(trial / 'project', [sys.executable, '-m', 'unittest', 'test_hidden', '-v']))
    roles = ([root] if root else []) + workers
    combined = common.combine_usage([r['usage'] for r in roles])
    cost = common.weighted_cost(roles, m['pricing']['rates'])
    result = dict(sequence=sequence+1, arm=arm, root=root, workers=workers, seconds=seconds,
        parallel_phase_seconds=parallel_seconds, weighted_cost=cost, combined_usage=combined,
        changed_paths=changed, scope_pass=scope, topology_pass=topology, checks=checks,
        final_source_hashes=after, reused_source_bound_checks=current,
        root_skipped_reason='worker or integration checks failed' if root is None else None,
        quality_pass=bool(root and root['exit_code'] == 0 and root.get('semantic_acceptance') is True and scope and topology and all(c['returncode'] == 0 for c in checks)),
        usage_complete=cost is not None and all(combined[f] is not None for f in ('total_tokens', 'uncached_input_plus_output')))
    common.write(trial / 'result.json', result)
    print(json.dumps({k:result[k] for k in ('arm','seconds','parallel_phase_seconds','weighted_cost','quality_pass')} | {'summary':common.summarize(output)}, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare','run-one','summarize'])
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--isolated-runtime', action='store_true')
    p.add_argument('--parallel-first', action='store_true')
    p.add_argument('--pairs', type=int, choices=[1,2], default=2)
    p.add_argument('--case', type=Path, default=ROOT / 'evals/parallel-exporters')
    a = p.parse_args()
    if a.command == 'prepare': prepare(a.output.resolve(), a.case.resolve(), a.isolated_runtime, a.parallel_first, a.pairs)
    elif a.command == 'run-one': run_one(a.output.resolve())
    else: print(json.dumps(common.summarize(a.output.resolve()), indent=2))

if __name__ == '__main__': main()
