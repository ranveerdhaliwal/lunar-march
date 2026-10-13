import json
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from workflow_eval import FIELDS, combine_usage, summarize, invoke, init_project, collect_evidence, run_one, CASE, write, weighted_cost
from context_eval import snapshot
from unittest.mock import patch


class WorkflowPilotTests(unittest.TestCase):
    def test_accounting_includes_worker_and_preserves_missing_telemetry(self):
        root = {field: 100 for field in FIELDS}
        worker = {field: 50 for field in FIELDS}
        self.assertEqual(combine_usage([root, worker])['total_tokens'], 150)
        worker['cached_input_tokens'] = None
        combined = combine_usage([root, worker])
        self.assertIsNone(combined['cached_input_tokens'])
        self.assertEqual(combined['output_tokens'], 150)
        worker['total_tokens'] = None
        self.assertIsNone(combine_usage([root, worker])['total_tokens'])

    def result(self, folder, sequence, arm, seconds, usage, quality=True):
        trial = folder / f'trial-{sequence:02d}'
        trial.mkdir()
        (trial / 'result.json').write_text(json.dumps({
            'arm': arm, 'seconds': seconds,
            'combined_usage': {'total_tokens': usage, 'uncached_input_plus_output': usage},
            'quality_pass': quality, 'usage_complete': usage is not None}))

    def test_one_successful_pair_cannot_authorize_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            self.result(folder, 1, 'direct', 100, 1000)
            self.result(folder, 2, 'quick', 80, 800)
            summary = summarize(folder)
            self.assertTrue(summary['thresholds_met'])
            self.assertFalse(summary['successful'])
            self.assertFalse(summary['early_stop'])
            self.result(folder, 3, 'quick', 80, 800)
            self.result(folder, 4, 'direct', 100, 1000)
            self.assertTrue(summarize(folder)['successful'])

    def test_usage_or_quality_failure_stops_without_replacement(self):
        for quick_usage, quality in ((1100, True), (800, False), (None, True)):
            with self.subTest(usage=quick_usage, quality=quality), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                self.result(folder, 1, 'direct', 100, 1000)
                self.result(folder, 2, 'quick', 80, quick_usage, quality)
                summary = summarize(folder)
                self.assertTrue(summary['early_stop'])
                self.assertFalse(summary['successful'])

    def test_parent_rejection_or_invalid_report_is_not_acceptance(self):
        for report, expected in ((json.dumps({'accepted': True, 'reason': 'checked'}), True),
                                 (json.dumps({'accepted': False, 'reason': 'defect'}), False),
                                 ('plain prose', None), ('true', None)):
            with self.subTest(report=report), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                (folder / 'report.md').write_text(report)
                with patch('workflow_eval.subprocess.Popen') as process:
                    process.return_value.communicate.return_value = ('', '')
                    process.return_value.returncode = 0
                    result = invoke(folder, folder, 'model', 'task', 1, require_acceptance=True)
                self.assertIs(result['semantic_acceptance'], expected)
                self.assertIn('--output-schema', result['command'])

    def test_review_evidence_has_real_diff_new_files_and_matching_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'activity').mkdir()
            (project / 'tests').mkdir()
            source = project / 'activity/parse.py'
            source.write_text('value = 1\n')
            before = snapshot(project)
            init_project(project)
            source.write_text('value = 2\n')
            (project / 'tests/test_windows.py').write_text('import unittest\nclass Smoke(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(1 + 1, 2)\n')
            evidence = collect_evidence(project, before)
            self.assertIn('-value = 1', evidence['tracked_diff'])
            self.assertIn('+value = 2', evidence['tracked_diff'])
            self.assertIn('tests/test_windows.py', evidence['untracked_files'])
            self.assertTrue(evidence['stable_during_checks'])
            self.assertEqual(evidence['source_hashes'], snapshot(project))
            self.assertTrue(all(check['returncode'] == 0 for check in evidence['checks']))
            self.assertFalse(evidence['scope_pass'])
            source.write_text('value = 3\n')
            self.assertNotEqual(evidence['source_hashes'], snapshot(project))

    def test_launcher_dispatch_skips_review_on_failure_and_rejects_review_mutation(self):
        for failed, reviewer_writes in ((True, False), (False, False), (False, True)):
            with self.subTest(failed=failed, reviewer_writes=reviewer_writes), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary)
                shutil.copytree(CASE / 'fixture', output / 'frozen')
                (output / 'task.md').write_text('Test assignment')
                (output / 'grade.py').write_text('import unittest\nclass Grade(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n')
                manifest = {'fixture_hashes': snapshot(output / 'frozen'), 'profile': 'lean',
                            'order': ['quick'], 'parent_model': 'test-parent', 'root_timeout': 10}
                calls = []

                def dispatch(trial):
                    calls.append('worker')
                    folder = trial / 'worker'
                    folder.mkdir()
                    result = {'exit_code': 1 if failed else 0, 'usage': {field: None if failed else 10 for field in FIELDS}}
                    write(folder / 'result.json', result)
                    if not failed:
                        project = trial / 'project'
                        for name in ('parse.py', 'report.py', 'cli.py'):
                            path = project / 'activity' / name
                            path.write_text(path.read_text() + '\n# Trial mutation\n')
                        (project / 'tests/test_windows.py').write_text('import unittest\nclass Check(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n')
                        write(folder / 'evidence.json', collect_evidence(project, manifest['fixture_hashes']))
                    return result

                def review(project, *args, **kwargs):
                    calls.append('review')
                    if reviewer_writes:
                        path = project / 'activity/parse.py'
                        path.write_text(path.read_text() + '\n# Unpermitted review repair\n')
                    return {'exit_code': 0, 'semantic_acceptance': True, 'usage': {field: 20 for field in FIELDS}}

                with patch('workflow_eval.validate', return_value=manifest), patch('workflow_eval.run_worker', side_effect=dispatch), patch('workflow_eval.invoke', side_effect=review), contextlib.redirect_stdout(io.StringIO()):
                    run_one(output)
                result = json.loads(next(output.glob('trial-*/result.json')).read_text())
                self.assertEqual(calls, ['worker'] if failed else ['worker', 'review'])
                self.assertEqual(result['quality_pass'], not failed and not reviewer_writes)
                if failed:
                    self.assertIsNone(result['root'])
                    self.assertIsNone(result['combined_usage']['total_tokens'])
                else:
                    self.assertEqual(result['combined_usage']['total_tokens'], 30)
                    self.assertEqual(result['reused_source_bound_checks'], not reviewer_writes)

    def test_weighted_cost_prices_models_separately_and_requires_telemetry(self):
        rates = {'parent': {'uncached_input_tokens': 250, 'cached_input_tokens': 25, 'output_tokens': 1250},
                 'worker': {'uncached_input_tokens': 2.5, 'cached_input_tokens': .25, 'output_tokens': 12.5}}
        usage = {'uncached_input_tokens': 1000, 'cached_input_tokens': 2000, 'output_tokens': 100, 'reasoning_tokens': 50}
        records = [{'model_requested': name, 'usage': dict(usage)} for name in rates]
        self.assertAlmostEqual(weighted_cost(records, rates), .42925)
        for value in (None, -1, float('nan'), True):
            records[1]['usage']['cached_input_tokens'] = value
            self.assertIsNone(weighted_cost(records, rates))
        self.assertIsNone(weighted_cost([], rates))
        self.assertIsNone(weighted_cost([{'model_requested': 'unknown', 'usage': usage}], rates))

    def test_weighted_decision_can_save_cost_with_more_raw_tokens(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            write(folder / 'manifest.json', {'metric': 'weighted_cost'})
            for seq, arm, seconds, tokens, cost in ((1, 'direct', 100, 1000, 10), (2, 'quick', 80, 2000, 5),
                                                   (3, 'quick', 80, 2000, 5), (4, 'direct', 100, 1000, 10)):
                self.result(folder, seq, arm, seconds, tokens)
                path = folder / f'trial-{seq:02d}/result.json'
                result = json.loads(path.read_text())
                result['weighted_cost'] = cost
                write(path, result)
            self.assertTrue(summarize(folder)['successful'])
            path = folder / 'trial-03/result.json'
            result = json.loads(path.read_text())
            result['weighted_cost'] = None
            write(path, result)
            self.assertFalse(summarize(folder)['successful'])

    def test_case_specific_commands_and_protected_acceptance_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'contract.py').write_text('print("protected-check")\n')
            (project / 'module.py').write_text('value = 1\n')
            before = snapshot(project)
            init_project(project)
            (project / 'module.py').write_text('value = 2\n')
            commands = [[sys.executable, 'contract.py']]
            evidence = collect_evidence(project, before, ['module.py'], commands)
            self.assertTrue(evidence['scope_pass'])
            self.assertEqual(len(evidence['checks']), 1)
            self.assertEqual(evidence['checks'][0]['stdout'], 'protected-check\n')
            (project / 'contract.py').write_text('print("tampered")\n')
            self.assertFalse(collect_evidence(project, before, ['module.py'], commands)['scope_pass'])

    def test_one_pair_plan_can_finish_but_cannot_authorize_publication(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            write(folder/'manifest.json',{'order':['quick','direct']})
            self.result(folder,1,'quick',80,800)
            self.result(folder,2,'direct',100,1000)
            summary=summarize(folder)
            self.assertTrue(summary['complete']);self.assertTrue(summary['thresholds_met'])
            self.assertEqual(summary['planned_trials'],2);self.assertFalse(summary['successful'])

    def test_failed_first_trial_blocks_both_launchers(self):
        import parallel_eval
        import workflow_eval
        for module in (workflow_eval, parallel_eval):
            for quality, usage, cost in ((False, 100, 1), (True, None, 1), (True, 100, None)):
                with self.subTest(module=module.__name__, quality=quality, usage=usage, cost=cost), tempfile.TemporaryDirectory() as d:
                    output = Path(d)
                    manifest = {'order': ['quick', 'direct'], 'metric': 'weighted_cost'}
                    write(output / 'manifest.json', manifest)
                    self.result(output, 1, 'quick', 80, usage, quality)
                    path = output / 'trial-01/result.json'
                    result = json.loads(path.read_text())
                    result['weighted_cost'] = cost
                    write(path, result)
                    with patch.object(module, 'validate', return_value=manifest), patch('workflow_eval.invoke') as launch, contextlib.redirect_stdout(io.StringIO()):
                        module.run_one(output)
                    launch.assert_not_called()
                    self.assertEqual(len(list(output.glob('trial-*'))), 1)
                    summary = summarize(output)
                    self.assertTrue(summary['early_stop'])
                    self.assertIn('trial 1', summary['stop_reason'])

    def test_failure_in_reverse_pair_stops_before_fourth_trial(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            self.result(output, 1, 'direct', 100, 1000)
            self.result(output, 2, 'quick', 80, 800)
            self.result(output, 3, 'quick', 80, 800, quality=False)
            summary = summarize(output)
            self.assertTrue(summary['early_stop'])
            self.assertIn('trial 3', summary['stop_reason'])
            self.assertFalse(summary['successful'])
