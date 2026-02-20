from __future__ import annotations

import sys
import unittest
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parents[1]
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from publishers.artanuji import ArtanujiParser


class ArtanujiParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = ArtanujiParser()

    def test_parse_extracts_expected_fields(self) -> None:
        html = """
        <html>
          <head>
            <meta property="og:image" content="/images/book-1.jpg" />
          </head>
          <body>
            <h1>ზღვის წიგნი</h1>
            <h4>Nino Beridze</h4>
            <div>ISBN: 978-9941-11-222-3</div>
            <div>გამოცემის თარიღი: 2021</div>
            <div>გვერდები: 304</div>
            <div>კატეგორია: პროზა</div>
            <p>ყიდვა</p>
            <p>ეს არის ტესტური აღწერა, რომელიც საკმარისად გრძელია ველის შესავსებად.</p>
            <p>გაზიარება</p>
            book_ge.php
          </body>
        </html>
        """

        parsed = self.parser.parse(html, item_id=123)

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.title, "ზღვის წიგნი")
        self.assertEqual(parsed.author, "Nino Beridze")
        self.assertEqual(parsed.isbn_13, "9789941112223")
        self.assertEqual(parsed.publish_date, "2021")
        self.assertEqual(parsed.number_of_pages, 304)
        self.assertEqual(parsed.subject, "პროზა")
        self.assertTrue(parsed.description and "ტესტური აღწერა" in parsed.description)
        self.assertEqual(parsed.cover_url, "https://www.artanuji.ge/images/book-1.jpg")

    def test_parse_returns_none_for_non_book_page(self) -> None:
        html = "<html><body><h1>Home</h1></body></html>"
        parsed = self.parser.parse(html, item_id=7)
        self.assertIsNone(parsed)


if __name__ == "__main__":
    unittest.main()
