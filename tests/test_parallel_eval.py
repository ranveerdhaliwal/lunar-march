import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import parallel_eval as runner
import workflow_eval as common
from context_eval import snapshot

class ParallelRunnerTests(unittest.TestCase):
    def test_dispatch_really_overlaps_two_lanes(self):
        barrier=threading.Barrier(2,timeout=5)
        def execute(trial,manifest,lane):
            barrier.wait();return {'lane':lane['id']}
        with patch.object(runner,'execute_lane',side_effect=execute):
            result=runner.dispatch(Path('/unused'),{'lanes':[{'id':'a'},{'id':'b'}]})
        self.assertEqual([r['lane'] for r in result],['a','b'])

    def test_failed_lane_does_not_discard_other_usage(self):
        with tempfile.TemporaryDirectory() as d:
            def execute(trial,manifest,lane):
                if lane['id']=='a':raise OSError('startup failed')
                return {'lane':'b','usage':{'total_tokens':42}}
            with patch.object(runner,'execute_lane',side_effect=execute):
                result=runner.dispatch(Path(d),{'worker_model':'test','lanes':[{'id':'a'},{'id':'b'}]})
            self.assertFalse(result[0]['quality_pass'])
            self.assertIsNone(result[0]['usage']['total_tokens'])
            self.assertEqual(result[1]['usage']['total_tokens'],42)

    def setup_merge(self,root):
        fixture=root/'frozen';fixture.mkdir();(fixture/'a.py').write_text('a=0\n');(fixture/'b.py').write_text('b=0\n');(fixture/'protected.txt').write_text('untouched')
        trial=root/'trial';trial.mkdir();shutil.copytree(fixture,trial/'project')
        lanes=[{'id':key,'owned_paths':[key+'.py']} for key in ('a','b')]
        records=[]
        for lane in lanes:
            p=trial/('worker-'+lane['id'])/'project';shutil.copytree(fixture,p)
            (p/(lane['id']+'.py')).write_text(lane['id']+'=1\n')
            records.append({'lane':lane['id'],'quality_pass':True,'evidence':{'source_hashes':snapshot(p)}})
        return trial,{'lanes':lanes,'fixture_hashes':snapshot(fixture)},records

    def test_merge_uses_only_owned_paths_and_checks_both_before_copy(self):
        with tempfile.TemporaryDirectory() as d:
            trial,m,records=self.setup_merge(Path(d))
            self.assertTrue(runner.merge(trial,m,records))
            self.assertEqual((trial/'project/a.py').read_text(),'a=1\n')
            self.assertEqual((trial/'project/b.py').read_text(),'b=1\n')
            self.assertEqual((trial/'project/protected.txt').read_text(),'untouched')
        with tempfile.TemporaryDirectory() as d:
            trial,m,records=self.setup_merge(Path(d))
            source=trial/'worker-b/project';(source/'protected.txt').write_text('bad')
            records[1]['evidence']['source_hashes']=snapshot(source)
            with self.assertRaisesRegex(ValueError,'protected'):runner.merge(trial,m,records)
            self.assertEqual(snapshot(trial/'project'),m['fixture_hashes'])

    def test_three_roles_count_and_missing_worker_usage_fails_closed(self):
        rates={'astra':{'uncached_input_tokens':250,'cached_input_tokens':25,'output_tokens':1250},'luna':{'uncached_input_tokens':2.5,'cached_input_tokens':.25,'output_tokens':12.5}}
        records=[{'model_requested':model,'usage':{f:100 for f in common.FIELDS}} for model in ('astra','luna','luna')]
        self.assertAlmostEqual(common.weighted_cost(records,rates),.15555)
        self.assertEqual(common.combine_usage([r['usage'] for r in records])['total_tokens'],300)
        records[2]['usage']['cached_input_tokens']=None
        self.assertIsNone(common.weighted_cost(records,rates))

    def test_review_mutation_rejects_acceptance(self):
        for mutation in (False,True):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                output=Path(d);frozen=output/'frozen';frozen.mkdir();(frozen/'a.py').write_text('x=0\n');(frozen/'b.py').write_text('x=0\n')
                (output/'task.md').write_text('Task');(output/'grade.py').write_text('import unittest\nclass Test(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
                m={'fixture_hashes':snapshot(frozen),'order':['quick'],'parent_model':'astra','worker_model':'luna','worker_timeout':1,'review_timeout':1,'commands':[],'owned_paths':['a.py','b.py'],'lanes':[{'id':k,'owned_paths':[k+'.py']} for k in ('a','b')],'pricing':{'rates':{'astra':{'uncached_input_tokens':1,'cached_input_tokens':1,'output_tokens':1},'luna':{'uncached_input_tokens':1,'cached_input_tokens':1,'output_tokens':1}}}}
                def dispatch(trial,manifest):
                    records=[]
                    for lane in m['lanes']:
                        p=trial/('worker-'+lane['id'])/'project';shutil.copytree(frozen,p);(p/(lane['id']+'.py')).write_text('x=1\n')
                        records.append({'lane':lane['id'],'model_requested':'luna','quality_pass':True,'usage':{f:1 for f in common.FIELDS},'evidence':{'source_hashes':snapshot(p)}})
                    return records
                def invoke(project,*args,**kwargs):
                    if mutation:(project/'a.py').write_text('x=2\n')
                    return {'model_requested':'astra','exit_code':0,'semantic_acceptance':True,'usage':{f:1 for f in common.FIELDS}}
                with patch.object(runner,'validate',return_value=m),patch.object(runner,'dispatch',side_effect=dispatch),patch.object(common,'invoke',side_effect=invoke),contextlib.redirect_stdout(io.StringIO()):runner.run_one(output)
                result=json.loads((output/'trial-01/result.json').read_text())
                self.assertEqual(result['quality_pass'],not mutation)
                self.assertEqual(result['combined_usage']['total_tokens'],3)
