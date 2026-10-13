"""Independent post-run probes using the published contract."""
import io
import unittest
from decimal import Decimal
from ledgerfmt.model import Record
from ledgerfmt.formats import csv,jsonl

class ExportProbes(unittest.TestCase):
    def test_cross_format_generator_roundtrip(self):
        rows=[Record(str(i)+'\n,"雪',Decimal(str(i)+'.00100'),('a','a','\r\n')) for i in range(-3,4)]
        for first,second in ((csv,jsonl),(jsonl,csv)):
            a=io.StringIO();first.dump((r for r in rows),a)
            b=io.StringIO();second.dump(first.load(io.StringIO(a.getvalue())),b)
            actual=second.load(io.StringIO(b.getvalue()))
            self.assertEqual(actual,rows)
            self.assertEqual([r.amount.as_tuple() for r in actual],[r.amount.as_tuple() for r in rows])
    def test_atomic_schema_error_preserves_cursor(self):
        for module in (csv,jsonl):
            out=io.StringIO('untouched');out.seek(3)
            with self.assertRaises(ValueError):module.dump([Record('a',Decimal('1')),Record('b',Decimal('2'),('ok',4))],out)
            self.assertEqual(out.getvalue(),'untouched');self.assertEqual(out.tell(),3)
    def test_finite_exponent_and_negative_zero(self):
        rows=[Record('big',Decimal('1E+6')),Record('zero',Decimal('-0.000'))]
        for module in (csv,jsonl):
            out=io.StringIO();module.dump(rows,out);actual=module.load(io.StringIO(out.getvalue()))
            self.assertEqual(actual,rows);self.assertEqual(actual[1].amount.as_tuple(),rows[1].amount.as_tuple())
