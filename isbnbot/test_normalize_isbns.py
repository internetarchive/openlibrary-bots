import unittest

import normalize_isbns

class NormalizeISBNJobTestCase(unittest.TestCase):

    single = {
        '0-19-852663-6': ['0198526636'],
        '0-9752298-0-X': ['097522980X'],
        '3-444-101-11-2': ['3444101112'],
        '978-1619636071': ['9781619636071'],
        '978-3-16-148410-0': ['9783161484100'],
        'ISBN 979-10-90636-07-1': ['9791090636071'],
        'ISBN: 2-7535-0291-9': ['2753502919'],
        '0 - 934314 - 08 - x': ['093431408X'],
        'I.S.B.N: 978-9947-834-43-5': ['9789947834435'],
        'ISBN: 978-0-620-45358-5': ['9780620453585'],
        '9706544526 (Colección)': ['9706544526'],
        '9071066045 (Stichting Oud-Muiderberg)': ['9071066045'],
        'ISBN9984-725-71-5': ['9984725715'],
        'ISBN   88-8191-235X': ['888191235X'],
        '978 971 92645 3 8': ['9789719264538'],
        '2.902.639.57.0': ['2902639570'],
        'ISBN-978-958-660-120-7': ['9789586601207'],
    }
    double = {
        '0-9752298-0-X 0-19-852663-6': ['097522980X','0198526636'],
        '9789585596689-9789585596672': ['9789585596689', '9789585596672'],
        '9789585596689 - 0-9752298-0-X': ['9789585596689', '097522980X'],
        '28458625552876144972': ['2845862555', '2876144972'],
        '978-84-96785-10-6. 978-84-96785-44-1': ['9788496785106', '9788496785441'],
        '978-608-4501-13-8; 978-608-65045-4-0': ['9786084501138', '9786086504540'],
        '0-380-75964-0 / 978-0-380-75964-4 (USA edition)': ['0380759640', '9780380759644'],
        '978-0-380-75964-4 (USA edition) /0-380-75964-0 ': ['9780380759644','0380759640'],
        'ISBN 2-7535-0291-9ISBN 978-2-296-09310-2  ': ['2753502919', '9782296093102'],
    }
    multi = { # we 
        '978-84-96785-10-6. 978-84-96785-44-19789585596689': ['9788496785106','9788496785441','9789585596689'],
        '0-9752298-0-X 0-19-852663-6 / 28458625552876144972': ['097522980X','0198526636', '2845862555', '2876144972'],
        '978-84-96785-10-6. 978-84-96785-44-1978-608-4501-13-8; 978-608-65045-4-0': ['9788496785106', '9788496785441','9786084501138','9786086504540'],
        '978-2-296-09310-2  978-84-96785-10-6. 978-84-96785-44-19789585596689': ['9782296093102', '9788496785106','9788496785441','9789585596689'],
    }
    tricky = {
        # same number twice, note dedupe is done after
        '97815420429639781542042963': ['9781542042963', '9781542042963'],
        # tab character
        '\t978-83-8169-344-8': ['9788381693448'],
        # unicode
        '978\xad-85-\xad913035-\xad0-\xad2': ['9788591303502'],
        '\u202c978-3-86850-235-0': ['9783868502350'],
        # isbn13 with 13 somewhere in the string
        '1567445144 (ISBN13: 9781567445145)': ['9781567445145'], # note we ignore the isbn10
        '13-978-951-558-248-5': ['9789515582485'],
        '13:978-1478322221': ['9781478322221'],
        '(ISBN13: 9781492993780': ['9781492993780'],
        # lots of extra numbers
        'ISBN # 978-1-4243-0080-8 Registration Number TXu -1 - 333 – 097 Effective Date of Registration 11 Dec 2006': ['9781424300808'],
    }
    invalid = [
        '11111111112222222222222'
        '9881567445145',
        '0-19-852X663-6',
    ]
    ignored = [
        '978',
        '-3-',
        '-16-',
        '-14810-0',
        # TODO match these common non-isbn entries and blank them
        # check short isbns, blank common ones, levenshtien against existing
        # fill 10 from 13 and vice versa
        # list 10 and 13 char ISBNs that isbnlib doesn't like the look of
        '$10.00',
        'N/A',
        'bought 2001-12-25',
        '',
    ]

    def test_single_inputs(self):
        for input, expectedoutput in iter(self.single.items()):
            with self.subTest('single input:' + input):
                self.assertEqual(normalize_isbns.parse_isbns(input), expectedoutput)

    def test_double_inputs(self):
        for input, expectedoutput in iter(self.double.items()):
            with self.subTest('double input:' + input):
                self.assertEqual(normalize_isbns.parse_isbns(input), expectedoutput)

    def test_multi_inputs(self):
        for input, expectedoutput in iter(self.multi.items()):
            with self.subTest('multi input:' + input):
                self.assertEqual(normalize_isbns.parse_isbns(input), expectedoutput)

    def test_tricky_inputs(self):
        for input, expectedoutput in iter(self.tricky.items()):
            with self.subTest('tricky input:' + input):
                self.assertEqual(normalize_isbns.parse_isbns(input), expectedoutput)

    def test_invalid_inputs(self):
        for input in self.invalid:
            with self.subTest('Invalid input:' + input):
                self.assertFalse(normalize_isbns.parse_isbns(input))

    def test_ignored_inputs(self):
        for input in self.ignored:
            with self.subTest('Should ignore:' + input):
                self.assertFalse(normalize_isbns.parse_isbns(input))

if __name__ == '__main__':
    unittest.main()
