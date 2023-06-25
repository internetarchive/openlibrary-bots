import unittest
from typing import ClassVar

from isbnbot import normalize_isbns


class NormalizeISBNJobTestCase(unittest.TestCase):
    single: ClassVar[dict[str, tuple]] = {
        "0-19-852663-6": ("0198526636",),
        "0-9752298-0-X": ("097522980X",),
        "3-444-101-11-2": ("3444101112",),
        "978-1619636071": ("9781619636071",),
        "978-3-16-148410-0": ("9783161484100",),
        "ISBN 979-10-90636-07-1": ("9791090636071",),
        "ISBN: 2-7535-0291-9": ("2753502919",),
        "0 - 934314 - 08 - x": ("093431408X",),
        "I.S.B.N: 978-9947-834-43-5": ("9789947834435",),
        "ISBN: 978-0-620-45358-5": ("9780620453585",),
        "9706544526 (Colección)": ("9706544526",),
        "9071066045 (Stichting Oud-Muiderberg)": ("9071066045",),
        "ISBN9984-725-71-5": ("9984725715",),
        "ISBN   88-8191-235X": ("888191235X",),
        "978 971 92645 3 8": ("9789719264538",),
        "2.902.639.57.0": ("2902639570",),
        "ISBN-978-958-660-120-7": ("9789586601207",),
    }
    double: ClassVar[dict[str, tuple]] = {
        "0-9752298-0-X 0-19-852663-6": ("097522980X", "0198526636"),
        "9789585596689-9789585596672": ("9789585596689", "9789585596672"),
        "9789585596689 - 0-9752298-0-X": ("9789585596689", "097522980X"),
        "28458625552876144972": ("2845862555", "2876144972"),
        "978-84-96785-10-6. 978-84-96785-44-1": ("9788496785106", "9788496785441"),
        "978-608-4501-13-8; 978-608-65045-4-0": ("9786084501138", "9786086504540"),
        "0-380-75964-0 / 978-0-380-75964-4 (USA edition)": (
            "0380759640",
            "9780380759644",
        ),
        "978-0-380-75964-4 (USA edition) /0-380-75964-0 ": (
            "9780380759644",
            "0380759640",
        ),
        "ISBN 2-7535-0291-9ISBN 978-2-296-09310-2  ": ("2753502919", "9782296093102"),
    }
    multi: ClassVar[dict[str, tuple]] = {
        "978-84-96785-10-6. 978-84-96785-44-19789585596689": (
            "9788496785106",
            "9788496785441",
            "9789585596689",
        ),
        "0-9752298-0-X 0-19-852663-6 / 28458625552876144972": (
            "097522980X",
            "0198526636",
            "2845862555",
            "2876144972",
        ),
        "978-84-96785-10-6. 978-84-96785-44-1978-608-4501-13-8; 978-608-65045-4-0": (
            "9788496785106",
            "9788496785441",
            "9786084501138",
            "9786086504540",
        ),
        "978-2-296-09310-2  978-84-96785-10-6. 978-84-96785-44-19789585596689": (
            "9782296093102",
            "9788496785106",
            "9788496785441",
            "9789585596689",
        ),
        "0-9752298-0-X   0 - 934314 - 08 - x ISBN   88-8191-235X": (
            "097522980X",
            "093431408X",
            "888191235X",
        ),
    }
    tricky: ClassVar[dict[str, tuple]] = {
        # same number twice, note dedupe is done after
        "97815420429639781542042963": ("9781542042963", "9781542042963"),
        # tab character
        "\t978-83-8169-344-8": ("9788381693448",),
        # unicode
        "978\xad-85-\xad913035-\xad0-\xad2": ("9788591303502",),
        "\u202c978-3-86850-235-0": ("9783868502350",),
        "0-19-852X663-6": ("0198526636",),
    }
    invalid = (
        "11111111112222222222222" "9881567445145",
        "9771654981684",
        "011249845X",
        "7521245214",
    )
    ignored = (
        "978",
        "-3-",
        "-16-",
        "-14810-0",
        "$10.00",
        "N/A",
        "bought 2001-12-25",
        "",
        "13-978-951-558-248-5",
        "13:978-1478322221",
        "(ISBN13: 9781492993780",
        "1567445144 (ISBN13: 9781567445145)",
        "ISBN # 978-1-4243-0080-8 Registration Number TXu -1 - 333 – 097 Effective Date of Registration 11 Dec 2006",
    )

    def test_single_inputs(self):
        for input_str, expectedoutput in iter(self.single.items()):
            with self.subTest(f"single input:{input_str}"):
                self.assertEqual(normalize_isbns.parse_isbns(input_str), expectedoutput)

    def test_double_inputs(self):
        for input_str, expectedoutput in iter(self.double.items()):
            with self.subTest(f"double input:{input_str}"):
                self.assertEqual(normalize_isbns.parse_isbns(input_str), expectedoutput)

    def test_multi_inputs(self):
        for input_str, expectedoutput in iter(self.multi.items()):
            with self.subTest(f"multi input:{input_str}"):
                self.assertEqual(normalize_isbns.parse_isbns(input_str), expectedoutput)

    def test_tricky_inputs(self):
        for input_str, expectedoutput in iter(self.tricky.items()):
            with self.subTest(f"tricky input:{input_str}"):
                self.assertEqual(normalize_isbns.parse_isbns(input_str), expectedoutput)

    def test_invalid_inputs(self):
        for input_str in self.invalid:
            with self.subTest(f"Invalid input:{input_str}"):
                self.assertFalse(normalize_isbns.parse_isbns(input_str))

    def test_ignored_inputs(self):
        for input_str in self.ignored:
            with self.subTest(f"Should ignore:{input_str}"):
                self.assertFalse(normalize_isbns.parse_isbns(input_str))


if __name__ == "__main__":
    unittest.main()
