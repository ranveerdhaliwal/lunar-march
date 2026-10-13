import io
import json
import unittest
from decimal import Decimal
from ledgerfmt.model import Record
from ledgerfmt.formats import jsonl

class JsonlContract(unittest.TestCase):
    def test_roundtrip_scale_unicode(self):
        rows=[Record('café\n"a"',Decimal('0.0100'),('x,y','\n',''))]
        out=io.StringIO();jsonl.dump(iter(rows),out)
        self.assertFalse(out.closed);self.assertEqual(out.getvalue().count('\n'),1)
        self.assertIn('café',out.getvalue());self.assertEqual(jsonl.load(io.StringIO(out.getvalue())),rows)
        self.assertEqual(json.loads(out.getvalue())['amount'],'0.0100')
    def test_empty(self):
        self.assertEqual(jsonl.load(io.StringIO('\n \t\n')),[])
        out=io.StringIO();self.assertIsNone(jsonl.dump([],out));self.assertEqual(out.getvalue(),'')
    def test_exact_keys(self):
        for value in ({'account':'a','amount':'1'}, {'account':'a','amount':'1','tags':[],'extra':0}, [], 7):
            with self.subTest(value=value),self.assertRaises(ValueError):jsonl.load(io.StringIO(json.dumps(value)))
    def test_bad_wire_schema(self):
        for amount,tags in ((1,[]),('NaN',[]),('1e3',[]),('1','x'),('1',[None])):
            with self.assertRaises(ValueError):jsonl.load(io.StringIO(json.dumps({'account':'a','amount':amount,'tags':tags})))
    def test_bad_json_context(self):
        with self.assertRaises(ValueError) as error:jsonl.load(io.StringIO('\n{broken}\n'))
        self.assertRegex(str(error.exception).lower(),r'(line|row).*2')
    def test_atomic_late_error(self):
        for bad in (Record('b',Decimal('NaN')),Record('',Decimal('1')),Record('b',Decimal('2'),('x',None))):
            out=io.StringIO('prefix');out.seek(0,2)
            with self.assertRaises(ValueError):jsonl.dump(iter([Record('a',Decimal('1')),bad]),out)
            self.assertEqual(out.getvalue(),'prefix')
    def test_order_and_sorted_keys(self):
        out=io.StringIO();jsonl.dump([Record('b',Decimal('2')),Record('a',Decimal('1'))],out)
        decoded=[json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual([x['account'] for x in decoded],['b','a'])
        self.assertEqual(list(decoded[0]),['account','amount','tags'])
