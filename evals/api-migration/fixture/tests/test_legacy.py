import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal
from activity.parse import Event, load_events
from activity.report import summarize
from activity.cli import main


class LegacyTests(unittest.TestCase):
    def test_exact_decimal_summary(self):
        self.assertEqual(summarize([Event('b',Decimal('0.1')),Event('b',Decimal('0.2')),Event('a',Decimal('2'))]),
                         {'count':3,'totals':{'a':'2','b':'0.3'}})

    def test_empty(self):
        self.assertEqual(summarize([]), {'count':0,'totals':{}})

    def test_csv_without_timestamps_and_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'events.csv'
            path.write_text('category,amount\nb,0.10\na,2.00\nb,0.20\n')
            self.assertEqual(len(load_events(path)),3)
            stdout=io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main([str(path)]),0)
            self.assertEqual(json.loads(stdout.getvalue()), {'count':3,'totals':{'a':'2.00','b':'0.30'}})

    def test_missing_file_no_json(self):
        stdout,stderr=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            self.assertEqual(main(['/nonexistent/activity-fixture.csv']),2)
        self.assertEqual(stdout.getvalue(),'')
        self.assertTrue(stderr.getvalue())
