import io
import csv as standard_csv
import unittest
from decimal import Decimal
from ledgerfmt.model import Record
from ledgerfmt.formats import csv

class CsvContract(unittest.TestCase):
    def test_roundtrip_and_scale(self):
        rows=[Record('café,\n"q"',Decimal('-2.000'),('one,two','"','\n'))]
        out=io.StringIO();self.assertIsNone(csv.dump(iter(rows),out))
        self.assertFalse(out.closed);self.assertTrue(out.getvalue().startswith('account,amount,tags\n'))
        self.assertEqual(csv.load(io.StringIO(out.getvalue())),rows)
        self.assertEqual(list(standard_csv.reader(io.StringIO(out.getvalue())))[1][1],'-2.000')
    def test_empty_header(self):
        out=io.StringIO();csv.dump([],out);self.assertEqual(out.getvalue(),'account,amount,tags\n')
        self.assertEqual(csv.load(io.StringIO(out.getvalue())),[])
    def test_reject_headers(self):
        for text in ('','amount,account,tags\n','account,amount,amount\n','account,amount,tags,extra\n'):
            with self.subTest(text=text),self.assertRaises(ValueError):csv.load(io.StringIO(text))
    def test_bad_rows(self):
        for row in ('a,1','a,1,[],extra','\n','a,NaN,[]','a,1,garbage','a,1,{}'):
            with self.subTest(row=row),self.assertRaises(ValueError):csv.load(io.StringIO('account,amount,tags\n'+row+'\n'))
    def test_quoted_error_context(self):
        with self.assertRaises(ValueError) as error:csv.load(io.StringIO('account,amount,tags\n"unterminated'))
        self.assertRegex(str(error.exception).lower(),r'(line|row)')
    def test_atomic_error_before_header(self):
        for bad in (Record('b',Decimal('Infinity')),Record('',Decimal('1'))):
            out=io.StringIO('prefix');out.seek(0,2)
            with self.assertRaises(ValueError):csv.dump(iter([Record('a',Decimal('1')),bad]),out)
            self.assertEqual(out.getvalue(),'prefix')
    def test_crlf(self):
        self.assertEqual(csv.load(io.StringIO('account,amount,tags\r\na,1.00,[]\r\n')),[Record('a',Decimal('1.00'))])

    def test_json_numeric_limit_has_row_context(self):
        # CPython can raise plain ValueError, not JSONDecodeError, for this input.
        # Also invalid under the tags schema when a runtime has no integer limit.
        text = 'account,amount,tags\na,1,[' + '9' * 5000 + ']\n'
        with self.assertRaises(ValueError) as error:
            csv.load(io.StringIO(text))
        self.assertRegex(str(error.exception).lower(), r'(line|row)\s*:?\s*2\b')
