#!/usr/bin/env python3
"""Bounded CPU-only pilot: direct parent versus parent coordinator + Luna."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from context_eval import snapshot
from usage import extract_usage_jsonl

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'evals/workflow-efficiency'
FIELDS = ('input_tokens', 'cached_input_tokens', 'uncached_input_tokens',
          'output_tokens', 'reasoning_tokens', 'total_tokens', 'uncached_input_plus_output')
OWNED = {'activity/parse.py', 'activity/report.py', 'activity/cli.py', 'tests/test_windows.py'}


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(project, command):
    result = subprocess.run(command, cwd=project, text=True, capture_output=True, timeout=30)
    return {'command': command, 'returncode': result.returncode,
            'stdout': result.stdout[-5000:], 'stderr': result.stderr[-5000:]}


def _invoke(project, folder, model, prompt, timeout, require_acceptance=False, launch_env=None, isolated=False):
    command = [shutil.which('codex'), 'exec', '--ephemeral', '-C', str(project),
               '-m', model, '-c', 'model_reasoning_effort="high"',
               '-c', 'agents.max_depth=0', '-c', 'service_tier="default"',
               '-c', 'mcp_servers.MCP_DOCKER.enabled=false', '--approve-for-me', '--json',
               '--output-last-message', str(folder / 'report.md'), '-']
    if isolated:
        docker_override = command.index('mcp_servers.MCP_DOCKER.enabled=false')
        del command[docker_override-1:docker_override+1]
        command[1:1] = ['--no-daemon']
        command.insert(command.index('exec') + 1, '--ignore-user-config')
    if require_acceptance:
        schema = {'type': 'object', 'properties': {
            'accepted': {'type': 'boolean'}, 'reason': {'type': 'string'}},
            'required': ['accepted', 'reason'], 'additionalProperties': False}
        write(folder / 'acceptance-schema.json', schema)
        command[-1:-1] = ['--output-schema', str(folder / 'acceptance-schema.json')]
        prompt += '\nReturn the required JSON acceptance decision. Set accepted=false for any unresolved material defect; mechanical tests alone do not establish acceptance. In reason, tie each rejection to a stated requirement and concrete evidence (file/location, input, expected versus observed behavior). If verification is blocked, state what could not be checked. Optional improvements beyond the task are advisory and must not expand acceptance requirements. Keep the decision concise.\n'
    (folder / 'prompt.md').write_text(prompt)
    started = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True, env=launch_env)
    try:
        stdout, stderr = process.communicate(prompt, timeout=timeout)
        code = process.returncode
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        code = 124
    elapsed = time.monotonic() - started
    (folder / 'events.jsonl').write_text(stdout)
    (folder / 'stderr.log').write_text(stderr)
    result = {'model_requested': model, 'effort': 'high', 'service_tier_requested': 'default', 'command': command,
              'seconds': round(elapsed, 3), 'exit_code': code,
              'usage': extract_usage_jsonl(stdout), 'prompt_sha256': digest(folder / 'prompt.md')}
    if require_acceptance:
        try:
            decision = read(folder / 'report.md')
        except (OSError, ValueError):
            decision = {}
        if not isinstance(decision, dict):
            decision = {}
        result['semantic_acceptance'] = decision.get('accepted') if isinstance(decision.get('accepted'), bool) else None
        result['semantic_reason'] = decision.get('reason')
    write(folder / 'result.json', result)
    return result


def invoke(project, folder, model, prompt, timeout, require_acceptance=False, isolated=False):
    if not isolated:
        return _invoke(project, folder, model, prompt, timeout, require_acceptance)
    from isolated_codex import isolated_home
    started = time.monotonic()
    try:
        with isolated_home() as env:
            result = _invoke(project, folder, model, prompt, timeout, require_acceptance, env, True)
        result['model_process_seconds'] = result['seconds']
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        result = {'model_requested': model, 'effort': 'high', 'service_tier_requested': 'default',
                  'exit_code': 125, 'usage': {field: None for field in FIELDS},
                  'semantic_acceptance': False, 'infrastructure_error': type(error).__name__}
    result['seconds'] = round(time.monotonic() - started, 3)
    result['runtime_isolation'] = 'temporary home; no daemon; ignore user config; access token only; state removed after call'
    write(folder / 'result.json', result)
    return result


def prepare(output, profile='lean', parent_model='gpt-6.1-sol', worker_model='gpt-5.6-luna', metric='weighted_cost', case=None):
    case = Path(case).resolve() if case else CASE
    specification = read(case / 'case.json') if (case / 'case.json').exists() else {}
    pricing = read(CASE / 'standard-credit-rates-2026-10-10.json')
    if metric == 'weighted_cost' and any(model not in pricing['rates'] for model in (parent_model, worker_model)):
        raise ValueError('requested model has no frozen credit rates')
    if output.exists():
        raise ValueError('output already exists; choose a fresh directory')
    output.mkdir(parents=True)
    frozen = output / 'frozen'
    shutil.copytree(case / 'fixture', frozen)
    shutil.copy(case / 'task.md', output / 'task.md')
    shutil.copy(case / 'grade.py', output / 'grade.py')
    shutil.copy(Path(__file__), output / 'runner.py')
    baseline = check(frozen, [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    if baseline['returncode']:
        raise ValueError('legacy fixture checks must pass before live work')
    manifest = {'format': 'lunarmarch-workflow-pilot-v3', 'prepared_at': datetime.now(timezone.utc).isoformat(),
                'case': str(case), 'owned_paths': specification.get('owned_paths', sorted(OWNED)),
                'acceptance_commands': specification.get('acceptance_commands', default_checks()),
                'review_focus': specification.get('review_focus', ''),
                'profile': profile, 'parent_model': parent_model, 'worker_model': worker_model, 'effort': 'high',
                'metric': metric, 'pricing': pricing, 'service_tier_requested': 'default',
                'local_overrides': ['MCP_DOCKER disabled for these CPU-only fixture calls'],
                'cli_version': subprocess.check_output(['codex', '--version'], text=True).strip(),
                'source_commit': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
                'dirty_suite_override': True, 'publication_scope': 'exploratory pilot, not a general performance claim',
                'fixture_hashes': snapshot(frozen), 'task_sha256': digest(output / 'task.md'),
                'grader_sha256': digest(output / 'grade.py'), 'runner_sha256': digest(output / 'runner.py'),
                'skill_sha256': digest(ROOT / 'SKILL.md'), 'python': sys.version,
                'root_timeout': 360, 'worker_timeout': 180, 'max_model_calls': 6,
                'order': ['direct', 'quick', 'quick', 'direct'],
                'success_rule': 'all quality/scope/acceptance checks pass; complete telemetry; two counterbalanced pairs; Quick mean time and weighted Standard-credit cost each <=90% of Direct' if metric == 'weighted_cost' else 'all quality checks pass; complete telemetry; Quick mean time and both raw-token measures each <=90% of Direct',
                'stop_rule': 'stop immediately on any quality or telemetry failure; stop after first pair if Quick fails any efficiency threshold; no replacement trials',
                'dispatch_policy': 'launcher starts worker, then fresh parent review; no nested CLI' if profile == 'lean' else 'parent starts nested CLI',
                'cost_limits': 'weighted credit proxy only, no subscription-meter or invoice inference; root and worker included, benchmark setup/controller and external approval review excluded'}
    write(output / 'manifest.json', manifest)
    write(output / 'baseline.json', baseline)
    print(json.dumps({'output': str(output), 'legacy_baseline': 'passed', 'order': manifest['order']}))


def validate(output):
    manifest = read(output / 'manifest.json')
    for name, field in [('task.md', 'task_sha256'), ('grade.py', 'grader_sha256'), ('runner.py', 'runner_sha256')]:
        if digest(output / name) != manifest[field]:
            raise ValueError(f'frozen {name} changed')
    if snapshot(output / 'frozen') != manifest['fixture_hashes']:
        raise ValueError('frozen fixture changed')
    if manifest['runner_sha256'] != digest(Path(__file__)):
        raise ValueError('runner changed after planning')
    return manifest


def run_worker(trial):
    job = read(trial / 'job.json')
    if job['arm'] != 'quick':
        raise ValueError('Direct trials may not launch a worker')
    folder = trial / 'worker'
    folder.mkdir(exist_ok=False)  # One dispatch only, including failures.
    prompt = (trial.parent / 'task.md').read_text()
    manifest = validate(trial.parent)
    if manifest.get('profile') == 'lean':
        prompt += lean_implementation_prompt()
        prompt += '\nYou are an already assigned implementation worker. Do not load coordinator skills, select a workflow, or delegate. Return <=150 words with changed paths, check results and unmet requirements.\n'
    else:
        prompt += '\nYou are the single bounded Luna Builder. Implement the feature in this project. Do not delegate or run another model. Return <=200 words.\n'
    result = invoke(trial / 'project', folder, manifest['worker_model'], prompt, manifest['worker_timeout'])
    if manifest.get('profile') == 'lean' and result['exit_code'] == 0:
        write(folder / 'evidence.json', collect_evidence(trial / 'project', manifest['fixture_hashes'], manifest.get('owned_paths'), manifest.get('acceptance_commands')))
    return result


def worker(trial):
    result = run_worker(trial)
    print(json.dumps(result))
    raise SystemExit(0 if result['exit_code'] == 0 else 1)


def lean_implementation_prompt():
    return """
The assignment is complete: inspect the named inputs together, implement, and verify. Use the existing Git baseline to inspect your diff. Check coverage of each requested behavior, including error handling; report any unmet requirement. Batch independent reads/checks where practical. Re-run only after relevant changes or a new finding. Do not load orchestration skills or add workflow artifacts to this project.
"""


def init_project(project):
    # Disposable fixture only; gives both arms the same useful diff baseline.
    subprocess.run(['git', 'init', '-q', str(project)], check=True)
    subprocess.run(['git', '-C', str(project), 'add', '--', *snapshot(project)], check=True)
    subprocess.run(['git', '-C', str(project), '-c', 'user.name=Workflow Evaluation',
                    '-c', 'user.email=eval@example.invalid', '-c', 'commit.gpgsign=false',
                    '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Fixture baseline'], check=True)


def default_checks():
    return [[sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
            [sys.executable, '-m', 'compileall', '-q', 'activity', 'tests']]


def collect_evidence(project, before, owned=None, commands=None):
    # Generate evidence outside the worker session, bound to the files tested.
    initial = snapshot(project)
    checks = [check(project, command) for command in (commands if commands is not None else default_checks())]
    after = snapshot(project)
    changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    diff = subprocess.run(['git', 'diff', '--no-ext-diff', '--no-textconv', 'HEAD', '--'],
                          cwd=project, text=True, capture_output=True, check=True).stdout
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'],
                                        cwd=project).decode().split('\0')
    return {'source_hashes': after, 'stable_during_checks': initial == after,
            'changed_paths': changed, 'scope_pass': set(changed) == set(owned if owned is not None else OWNED), 'checks': checks,
            'tracked_diff': diff,
            'untracked_files': {name: (project / name).read_text() for name in untracked if name and name in after}}


def combine_usage(records):
    return {field: sum(record[field] for record in records)
            if all(record.get(field) is not None for record in records) else None
            for field in FIELDS}


def weighted_cost(records, rates):
    if not records:
        return None
    total = 0.0
    for record in records:
        model_rates = rates.get(record.get('model_requested'))
        if not model_rates:
            return None
        for field in ('uncached_input_tokens', 'cached_input_tokens', 'output_tokens'):
            value = record['usage'].get(field)
            rate = model_rates.get(field)
            if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 for x in (value, rate)):
                return None
            total += value * rate / 1_000_000
    # Reasoning tokens are already included in output tokens, never added twice.
    return round(total, 9)


def summarize(output):
    trials = [read(path) for path in sorted(output.glob('trial-*/result.json'))]
    manifest = read(output / 'manifest.json') if (output / 'manifest.json').exists() else {}
    weighted = manifest.get('metric') == 'weighted_cost'
    groups = {arm: [trial for trial in trials if trial['arm'] == arm] for arm in ('direct', 'quick')}
    metrics = {}
    for arm, values in groups.items():
        metrics[arm] = {'trials': len(values), 'all_quality_pass': bool(values) and all(value['quality_pass'] for value in values)}
        for field in ('seconds', 'total_tokens', 'uncached_input_plus_output', 'weighted_cost'):
            numbers = [value.get(field) if field in ('seconds', 'weighted_cost') else value['combined_usage'][field] for value in values]
            metrics[arm][field] = sum(numbers) / len(numbers) if numbers and all(number is not None for number in numbers) else None
    paired = len(groups['direct']) == len(groups['quick']) and bool(groups['direct'])
    quality = paired and all(value['quality_pass'] and value['usage_complete'] for value in trials)
    measures = ('seconds', 'weighted_cost') if weighted else ('seconds', 'total_tokens', 'uncached_input_plus_output')
    efficient = quality and all(metrics['quick'][field] is not None and metrics['direct'][field] is not None and
                                metrics['quick'][field] <= .9 * metrics['direct'][field]
                                for field in measures)
    planned = len(manifest.get('order', ['direct', 'quick', 'quick', 'direct']))
    failed_trial = next((index + 1 for index, value in enumerate(trials)
                         if not value['quality_pass'] or not value['usage_complete']
                         or (weighted and value.get('weighted_cost') is None)), None)
    stop_reason = (f'trial {failed_trial} failed quality or complete usage accounting' if failed_trial
                   else 'first pair failed efficiency thresholds' if len(trials) == 2 and not efficient
                   else None)
    summary = {'metric': 'weighted_cost' if weighted else 'raw_tokens', 'trials': len(trials), 'planned_trials': planned, 'metrics': metrics,
               'complete': len(trials) == planned, 'thresholds_met': efficient,
               'successful': planned >= 4 and len(trials) == planned and efficient,
               'early_stop': stop_reason is not None, 'stop_reason': stop_reason}
    write(output / 'summary.json', summary)
    return summary


def run_one(output):
    manifest = validate(output)
    summary = summarize(output)
    if summary['successful'] or summary['complete'] or summary['early_stop']:
        print(json.dumps(summary, indent=2))
        return
    sequence = summary['trials']
    # Any abandoned directory is an interrupted trial, never silently replaced.
    existing = list(output.glob('trial-*'))
    if len(existing) != sequence:
        raise ValueError('incomplete trial exists; preserve and classify it rather than retrying')
    arm = manifest['order'][sequence]
    trial = output / f'trial-{sequence+1:02d}-{hashlib.sha256(str(sequence).encode()).hexdigest()[:8]}'
    trial.mkdir()
    project = trial / 'project'
    shutil.copytree(output / 'frozen', project)
    if manifest.get('profile') == 'lean':
        init_project(project)
    else:
        subprocess.run(['git', 'init', '-q', str(project)], check=True)
    write(trial / 'job.json', {'arm': arm})
    (trial / 'root').mkdir()
    task = (output / 'task.md').read_text()
    if arm == 'direct':
        prompt = task + '\nComplete this task yourself in this main agent. Do not delegate, launch other model calls, or use orchestration skills. Implement, check and inspect your final diff.\n'
    else:
        prompt = task + f'''\nUse LunarMarch Quick: coordinate one bounded Luna Builder, then independently inspect its changes and verify the task. Do not implement or repair it yourself. No additional workers, Scouts, Testers, or Reviewers. No retries in this pilot. If defects remain, report failure.
To dispatch the single worker, run exactly:
python3 {Path(__file__).resolve()} worker --trial {trial}
This fixed helper invokes one authenticated Codex CLI call, records worker telemetry outside the project, and caps it at 180 seconds. Request require_escalated for this helper if needed for nested Codex local state or its sandbox; this one dispatch is explicitly authorized. Inspect {trial}/worker/report.md and the actual changed files, then run the acceptance checks and give your own concise acceptance decision. Do not read hidden graders or other trial directories.
'''
    if manifest.get('profile') == 'lean':
        if arm == 'direct':
            prompt += lean_implementation_prompt()
        else:
            prompt = task + f'''\nA single implementation worker has already completed this assignment. You are the independent acceptance reviewer. Do not implement, repair, select a workflow, load coordinator skills, or launch any agents.
Read {trial}/worker/evidence.json and {trial}/worker/report.md. The launcher generated the diff, source hashes and fresh public-check results after the worker exited. Inspect the diff and coverage against the task, independently probing any uncovered or doubtful behavior. Reuse recorded passing checks on unchanged files; do not rerun them merely to repeat the worker. Read additional source only to resolve a concrete review question. Reject any unmet requirement and return the required JSON acceptance decision. Do not read hidden graders or other trials.
'''
    if arm == 'quick' and manifest.get('review_focus'):
        prompt += '\nReview focus: ' + manifest['review_focus'] + '\n'
    prompt += '\nCPU only. Work inside this project. Do not inspect the evaluator source, other projects, or files outside the named worker report and evidence artifact. Do not touch GPU processes or install dependencies.\n'
    workflow_started = time.monotonic()
    # A known dispatch does not need an LLM to launch another CLI in its sandbox.
    # The launcher owns this sequence; failed startup never buys a review call.
    dispatched = run_worker(trial) if manifest.get('profile') == 'lean' and arm == 'quick' else None
    root = None if dispatched and dispatched['exit_code'] != 0 else invoke(
        project, trial / 'root', manifest['parent_model'], prompt, manifest['root_timeout'], require_acceptance=True)
    workflow_seconds = round(time.monotonic() - workflow_started, 3)
    after = snapshot(project)
    before = manifest['fixture_hashes']
    changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    scope = set(changed) == set(manifest.get('owned_paths', OWNED))
    worker_result = read(trial / 'worker/result.json') if (trial / 'worker/result.json').exists() else None
    topology = (worker_result is None) if arm == 'direct' else (worker_result is not None and worker_result['exit_code'] == 0)
    evidence_path = trial / 'worker/evidence.json'
    evidence = read(evidence_path) if manifest.get('profile') == 'lean' and evidence_path.exists() else None
    evidence_current = bool(evidence and evidence['stable_during_checks'] and evidence['source_hashes'] == after)
    if manifest.get('profile') == 'lean' and arm == 'quick':
        topology = topology and evidence_current  # Acceptance context must not become a second writer.
    checks = evidence['checks'] if evidence_current else [
        check(project, command) for command in manifest.get('acceptance_commands', default_checks())]
    shutil.copy(output / 'grade.py', project / 'test_hidden_windows.py')
    checks.append(check(project, [sys.executable, '-m', 'unittest', 'test_hidden_windows', '-v']))
    usage_records = ([root['usage']] if root else []) + ([worker_result['usage']] if worker_result else [])
    combined = combine_usage(usage_records)
    cost = weighted_cost([record for record in (root, worker_result) if record], manifest.get('pricing', {}).get('rates', {}))
    result = {'sequence': sequence+1, 'arm': arm, 'root': root, 'worker': worker_result,
              'seconds': workflow_seconds, 'weighted_cost': cost, 'combined_usage': combined, 'changed_paths': changed,
              'scope_pass': scope, 'topology_pass': topology, 'checks': checks,
              'reused_source_bound_checks': evidence_current,
              'root_skipped_reason': 'worker failed before review' if root is None else None,
              'quality_pass': root is not None and root['exit_code'] == 0 and root.get('semantic_acceptance') is True and topology and scope and all(value['returncode'] == 0 for value in checks),
              'usage_complete': all(combined[field] is not None for field in ('total_tokens', 'uncached_input_plus_output')) and (manifest.get('metric') != 'weighted_cost' or cost is not None),
              'final_source_hashes': after}
    write(trial / 'result.json', result)
    print(json.dumps({'trial': str(trial), 'arm': arm, 'quality_pass': result['quality_pass'],
                      'seconds': workflow_seconds, 'weighted_cost': cost, 'usage': combined, 'summary': summarize(output)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'run-one', 'worker', 'summarize'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--trial', type=Path)
    parser.add_argument('--case', type=Path, help='Fixture, brief, grader and optional case.json directory')
    parser.add_argument('--profile', choices=['original', 'lean'], default='lean')
    parser.add_argument('--parent-model', default='gpt-6.1-sol')
    parser.add_argument('--worker-model', default='gpt-5.6-luna')
    parser.add_argument('--metric', choices=['weighted_cost', 'raw_tokens'], default='weighted_cost')
    args = parser.parse_args()
    if args.command == 'worker':
        worker(args.trial.resolve())
    elif args.command == 'prepare':
        prepare(args.output.resolve(), args.profile, args.parent_model, args.worker_model, args.metric, args.case)
    elif args.command == 'run-one':
        run_one(args.output.resolve())
    else:
        print(json.dumps(summarize(args.output.resolve()), indent=2))


if __name__ == '__main__':
    main()
