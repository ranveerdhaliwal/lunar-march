import unittest
from decimal import Decimal
from ledgerfmt.model import Record, record_to_wire, record_from_wire
class ModelTests(unittest.TestCase):
    def test_roundtrip(self):
        row=Record('a',Decimal('1.00'),('x','x'))
        self.assertEqual(record_from_wire(**record_to_wire(row)),row)
    def test_plain_decimal(self):
        self.assertEqual(record_to_wire(Record('a',Decimal('1E+3')))['amount'],'1000')
    def test_invalid_wire(self):
        for amount in ('nan','1e2',1,None):
            with self.assertRaises(ValueError):record_from_wire('a',amount,[])
    def test_invalid_record(self):
        with self.assertRaises(ValueError):record_to_wire(Record('a',Decimal('NaN')))
