import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from isolated_codex import isolated_home,access_token

class IsolatedRuntimeTests(unittest.TestCase):
    def source(self,path,expiry):
        payload=base64.urlsafe_b64encode(json.dumps({'exp':expiry}).encode()).decode().rstrip('=')
        value={'auth_mode':'chatgpt','tokens':{'access_token':'header.'+payload+'.signature','id_token':'synthetic-id','account_id':'synthetic-account','refresh_token':'DO-NOT-COPY'},'last_refresh':'old'}
        (path/'auth.json').write_text(json.dumps(value));(path/'config.toml').write_text('shared config sentinel')
    def test_only_private_state_no_refresh_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d);self.source(source,time.time()+4000);before={p.name:p.read_bytes() for p in source.iterdir()}
            with patch.dict(os.environ,{'CODEX_HOME':str(source),'CODEX_SQLITE_HOME':'shared-db','CODEX_FAKE_REMOTE_TOKEN':'synthetic','OPENAI_API_KEY':'synthetic'}):
                with isolated_home() as env:
                    home=Path(env['CODEX_HOME']);auth=json.loads((home/'auth.json').read_text())
                    self.assertNotEqual(home,source);self.assertEqual(auth['tokens']['refresh_token'],'')
                    self.assertNotIn('CODEX_FAKE_REMOTE_TOKEN',env);self.assertNotIn('OPENAI_API_KEY',env)
                    self.assertEqual(home.stat().st_mode & 0o777,0o700);self.assertEqual((home/'auth.json').stat().st_mode & 0o777,0o600)
                    self.assertEqual(Path(env['CODEX_SQLITE_HOME']).parent,home)
                self.assertFalse(home.exists())
            self.assertEqual({p.name:p.read_bytes() for p in source.iterdir()},before)
    def test_short_token_fails_without_refresh_or_secret_error(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d);self.source(source,time.time()+10);before=(source/'auth.json').read_bytes()
            with self.assertRaises(RuntimeError) as error:access_token(source)
            self.assertNotIn('DO-NOT-COPY',str(error.exception));self.assertEqual((source/'auth.json').read_bytes(),before)
    def test_cleanup_on_call_failure(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d);self.source(source,time.time()+4000)
            with self.assertRaises(ValueError):
                with isolated_home(source) as env:
                    home=Path(env['CODEX_HOME']);raise ValueError('test call failed')
            self.assertFalse(home.exists())

    def test_isolated_command_omits_absent_mcp_config_and_uses_private_env(self):
        import workflow_eval
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            with patch('workflow_eval.subprocess.Popen') as process:
                process.return_value.communicate.return_value=('', '')
                process.return_value.returncode=0
                result=workflow_eval._invoke(folder,folder,'model','task',1,launch_env={'CODEX_HOME':'private'},isolated=True)
            command=result['command']
            self.assertIn('--no-daemon',command);self.assertIn('--ignore-user-config',command)
            self.assertFalse(any('MCP_DOCKER' in arg for arg in command))
            self.assertEqual(process.call_args.kwargs['env']['CODEX_HOME'],'private')

    def test_malformed_expiry_and_session_fail_without_shared_mutation(self):
        for expiry in (float('nan'), float('inf'), True, None, 'tomorrow', 10**400):
            with self.subTest(expiry=expiry), tempfile.TemporaryDirectory() as d:
                source = Path(d)
                self.source(source, expiry)
                before = (source / 'auth.json').read_bytes()
                with self.assertRaises(RuntimeError):
                    access_token(source)
                self.assertEqual((source / 'auth.json').read_bytes(), before)
        for value in ([], {'auth_mode': 'apikey'}, {'auth_mode': 'chatgpt', 'tokens': {'access_token': None}}):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as d:
                source = Path(d)
                (source / 'auth.json').write_text(json.dumps(value))
                with self.assertRaises(RuntimeError):
                    access_token(source)
