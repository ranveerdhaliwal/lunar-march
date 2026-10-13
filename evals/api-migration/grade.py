"""Independent post-run probes for the same migration contract."""
import unittest
from decimal import Decimal
from unittest.mock import patch
import activity
from activity import report
from activity.parse import Event

class MigrationProbes(unittest.TestCase):
    def test_mixed_values_and_no_mutation(self):
        rows=[Event('second',Decimal('-1.05')),Event('first',Decimal('3.000')),Event('second',Decimal('1.05'))]
        before=repr(rows)
        for fn in (report.summarize_events,report.summarize,activity.summarize_events,activity.summarize):
            self.assertEqual(fn(rows),{'count':3,'totals':{'first':'3.000','second':'0.00'}})
            self.assertEqual(repr(rows),before)

    def test_compatibility_propagates_exception(self):
        for fn in (report.summarize,activity.summarize):
            with patch.object(report,'summarize_events',side_effect=ValueError('sentinel')):
                with self.assertRaisesRegex(ValueError,'sentinel'):fn([])
