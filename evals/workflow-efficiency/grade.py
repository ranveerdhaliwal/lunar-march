"""Post-run behavior checks; copied into each project only after agents exit."""
import subprocess
import sys
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from activity.parse import Event,parse_timestamp,load_events
from activity.report import summarize


class WindowTests(unittest.TestCase):
    def test_parser_normalizes_offsets(self):
        expected=datetime(2026,10,10,10,tzinfo=timezone.utc)
        for value in ('2026-10-10T10:00:00Z','2026-10-10T12:00:00+02:00','2026-10-10T03:00:00-07:00'):
            self.assertEqual(parse_timestamp(value),expected)
            self.assertEqual(parse_timestamp(value).utcoffset(),timedelta(0))

    def test_parser_rejects_invalid(self):
        for value in ('','2026-10-10','2026-10-10T10:00:00','garbage','2026-13-01T00:00:00Z',
                      '2026-10-10T10:00:00+01:60','2026-10-10T10:00:00+24:00'):
            with self.subTest(value=value),self.assertRaises(ValueError):parse_timestamp(value)

    def test_half_open_window_exact_totals(self):
        rows=[Event('a',Decimal('0.1'),'2026-10-10T10:00:00Z'),
              Event('a',Decimal('0.2'),'2026-10-10T12:30:00+02:00'),
              Event('b',Decimal('7'),'2026-10-10T11:00:00Z'),
              Event('b',Decimal('9'),'2026-10-10T09:59:59Z')]
        self.assertEqual(summarize(rows,since=parse_timestamp('2026-10-10T10:00:00Z'),until=parse_timestamp('2026-10-10T11:00:00Z')),{'count':2,'totals':{'a':'0.3'}})

    def test_one_sided_windows(self):
        rows=[Event('x',Decimal('1'),'2026-10-10T09:00:00Z'),Event('x',Decimal('2'),'2026-10-10T10:00:00Z')]
        bound=parse_timestamp('2026-10-10T10:00:00Z')
        self.assertEqual(summarize(rows,since=bound),{'count':1,'totals':{'x':'2'}})
        self.assertEqual(summarize(rows,until=bound),{'count':1,'totals':{'x':'1'}})

    def test_bad_bounds_even_on_empty_data(self):
        aware=parse_timestamp('2026-10-10T10:00:00Z')
        naive=datetime(2026,10,10)
        for kwargs in ({'since':naive},{'until':naive},{'since':aware,'until':aware},{'since':aware,'until':aware-timedelta(seconds=1)}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):summarize([],**kwargs)

    def test_all_event_timestamps_checked_with_window(self):
        since=parse_timestamp('2026-10-10T10:00:00Z')
        until=parse_timestamp('2026-10-10T11:00:00Z')
        for stamp in (None,'','bad','2026-10-10T09:00:00'):
            with self.subTest(stamp=stamp),self.assertRaises(ValueError):
                summarize([Event('a',Decimal('1'),'2026-10-10T12:00:00Z'),Event('b',Decimal('2'),stamp)],since=since,until=until)

    def test_no_window_preserves_legacy(self):
        rows=[Event('a',Decimal('1'),None),Event('a',Decimal('2'),'bad')]
        self.assertEqual(summarize(rows),{'count':2,'totals':{'a':'3'}})

    def invoke(self,csv,args):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'data.csv';path.write_text(csv)
            result = subprocess.run([sys.executable, '-m', 'activity.cli', str(path), *args],
                                    text=True, capture_output=True, timeout=10)
            return result.returncode, result.stdout, result.stderr

    def test_cli_filtering(self):
        code,stdout,stderr=self.invoke('category,amount,timestamp\na,0.10,2026-10-10T10:00:00Z\na,0.20,2026-10-10T10:30:00Z\nb,9,2026-10-10T11:00:00Z\n',['--since','2026-10-10T10:00:00Z','--until','2026-10-10T11:00:00Z'])
        self.assertEqual(code,0);self.assertEqual(stderr,'');self.assertEqual(json.loads(stdout),{'count':2,'totals':{'a':'0.30'}})

    def test_cli_errors_no_partial_json(self):
        csv='category,amount,timestamp\na,1,2026-10-10T10:00:00Z\nb,2,bad\n'
        for args in (['--since','bad'],['--since','2026-10-10T12:00:00Z','--until','2026-10-10T10:00:00Z'],['--since','2026-10-10T09:00:00Z']):
            code,stdout,stderr=self.invoke(csv,args)
            self.assertEqual(code,2);self.assertEqual(stdout,'');self.assertTrue(stderr)

    def test_cli_missing_timestamp_in_window(self):
        code,stdout,stderr=self.invoke('category,amount\na,1\n',['--until','2026-10-10T11:00:00Z'])
        self.assertEqual(code,2);self.assertEqual(stdout,'');self.assertTrue(stderr)

    def test_cli_short_csv_row_is_data_error(self):
        for row in ('a', 'a,,2026-10-10T10:00:00Z', 'a,not-a-number,2026-10-10T10:00:00Z'):
            with self.subTest(row=row):
                code,stdout,stderr=self.invoke('category,amount,timestamp\n'+row+'\n',[])
                self.assertEqual(code,2);self.assertEqual(stdout,'');self.assertTrue(stderr)
                self.assertNotIn('Traceback',stderr)
