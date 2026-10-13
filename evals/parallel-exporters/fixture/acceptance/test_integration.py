import json
import subprocess
import sys
import unittest

class IntegrationContract(unittest.TestCase):
    def convert(self,source,target,text):
        return subprocess.run([sys.executable,'-m','ledgerfmt.cli',source,target],input=text,text=True,capture_output=True,timeout=10)
    def test_both_directions(self):
        original={'account':'a,雪','amount':'0.0200','tags':['x','x','']}
        result=self.convert('jsonl','csv',json.dumps(original)+'\n');self.assertEqual(result.returncode,0,result.stderr)
        back=self.convert('csv','jsonl',result.stdout);self.assertEqual(back.returncode,0,back.stderr)
        self.assertEqual(json.loads(back.stdout),original)
    def test_invalid_late_input_no_stdout(self):
        for source,target,text in (('jsonl','csv','{"account":"a","amount":"1","tags":[]}\n{bad}\n'),('csv','jsonl','account,amount,tags\na,1,[]\nb,2\n')):
            result=self.convert(source,target,text);self.assertEqual(result.returncode,2);self.assertEqual(result.stdout,'');self.assertTrue(result.stderr)
