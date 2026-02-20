from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

BOT_DIR = Path(__file__).resolve().parents[1]
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from import_publisher_books import (
    parsed_book_to_ol_book,
    validate_args,
)
from publishers.base import ParsedBook


class ImportScriptTest(unittest.TestCase):
    def test_validate_args_accepts_valid_values(self) -> None:
        args = argparse.Namespace(
            start_id=1,
            end_id=10,
            sleep_seconds=0.1,
            request_timeout=5.0,
            max_books=0,
        )
        self.assertIsNone(validate_args(args))

    def test_validate_args_rejects_invalid_range(self) -> None:
        args = argparse.Namespace(
            start_id=12,
            end_id=10,
            sleep_seconds=0.1,
            request_timeout=5.0,
            max_books=0,
        )
        self.assertEqual(validate_args(args), "--end-id must be >= --start-id")

    def test_parsed_book_to_ol_book_maps_fields(self) -> None:
        captured = {}

        class FakeAuthor:
            def __init__(self, name: str) -> None:
                self.name = name

        class FakeBook:
            def __init__(self, **kwargs) -> None:
                captured.update(kwargs)

        fake_common = SimpleNamespace(Author=FakeAuthor, Book=FakeBook)
        parsed = ParsedBook(
            source="publisher",
            source_id=5,
            source_url="https://example.org/book/5",
            title="Example Title",
            author="Jane Doe",
            publisher="Example Press",
            publish_date="2025",
            isbn_13="9781234567897",
            number_of_pages=210,
            description="Example description",
            subject="Example subject",
            cover_url="https://example.org/cover.jpg",
        )

        parsed_book_to_ol_book(parsed, fake_common)

        self.assertEqual(captured["title"], "Example Title")
        self.assertEqual(captured["authors"][0].name, "Jane Doe")
        self.assertEqual(captured["publisher"], "Example Press")
        self.assertEqual(captured["publish_date"], "2025")
        self.assertEqual(captured["identifiers"]["isbn_13"], ["9781234567897"])
        self.assertEqual(captured["number_of_pages"], 210)
        self.assertEqual(captured["description"], "Example description")
        self.assertEqual(captured["subject"], "Example subject")
        self.assertEqual(captured["cover"], "https://example.org/cover.jpg")


if __name__ == "__main__":
    unittest.main()
