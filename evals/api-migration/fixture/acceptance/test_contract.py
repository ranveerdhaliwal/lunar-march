"""Protected executable migration contract, provided to both implementations."""
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from activity.parse import Event

class MigrationContract(unittest.TestCase):
    def test_canonical_export(self):
        package = importlib.import_module('activity')
        report = importlib.import_module('activity.report')
        self.assertIs(package.summarize_events, report.summarize_events)
        self.assertTrue(callable(package.summarize))

    def test_old_module_and_package_api_forward(self):
        report = importlib.import_module('activity.report')
        package = importlib.import_module('activity')
        rows = [Event('x', Decimal('1'))]
        sentinel = {'count': 99, 'totals': {}}
        for legacy in (report.summarize, package.summarize):
            with patch.object(report, 'summarize_events', return_value=sentinel) as canonical:
                self.assertIs(legacy(rows), sentinel)
                canonical.assert_called_once_with(rows)

    def test_exact_decimal_sorted_categories(self):
        from activity.report import summarize_events
        rows = [Event('z',Decimal('0.10')),Event('a',Decimal('-2.00')),Event('z',Decimal('0.20'))]
        before = list(rows)
        result = summarize_events(rows)
        self.assertEqual(result, {'count':3, 'totals':{'a':'-2.00','z':'0.30'}})
        self.assertEqual(list(result['totals']), ['a','z'])
        self.assertEqual(rows,before)

    def test_empty(self):
        from activity.report import summarize_events
        self.assertEqual(summarize_events([]), {'count':0,'totals':{}})

    def test_service_uses_canonical(self):
        from activity import service
        rows = [Event('x',Decimal('3'))]
        sentinel = {'count':1,'totals':{'x':'3'}}
        with patch.object(service,'load_events',return_value=rows), patch.object(service,'summarize_events',return_value=sentinel) as canonical:
            self.assertIs(service.build_report('input.csv'), sentinel)
            canonical.assert_called_once_with(rows)

    def test_cli_uses_canonical(self):
        from activity import cli
        import contextlib,io
        rows = [Event('x',Decimal('3'))]
        sentinel = {'count':1,'totals':{'x':'3'}}
        with patch.object(cli,'load_events',return_value=rows), patch.object(cli,'summarize_events',return_value=sentinel) as canonical, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(['input.csv']),0)
            self.assertEqual(json.loads(output.getvalue()),sentinel)
            canonical.assert_called_once_with(rows)

    def test_real_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.csv';p.write_text('category,amount\nz,0.10\nz,0.20\na,2.00\n')
            result=subprocess.run([sys.executable,'-m','activity.cli',str(p)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0);self.assertEqual(result.stderr,'')
            self.assertEqual(json.loads(result.stdout),{'count':3,'totals':{'a':'2.00','z':'0.30'}})

    def test_existing_missing_file_behavior(self):
        result=subprocess.run([sys.executable,'-m','activity.cli','/nonexistent/migration-input.csv'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,2);self.assertEqual(result.stdout,'');self.assertTrue(result.stderr)
