from __future__ import annotations

import sys
import unittest
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parents[1]
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from publishers.base import ParsedBook


class ParsedBookPayloadTest(unittest.TestCase):
    def test_payload_includes_optional_fields_when_present(self) -> None:
        book = ParsedBook(
            source="artanuji",
            source_id=1,
            source_url="https://example.org/book/1",
            title="Example",
            author="Jane Doe",
            publisher="Example Publisher",
            publish_date="2024",
            isbn_13="9781234567897",
            number_of_pages=288,
            description="Desc",
            subject="Fiction",
            cover_url="https://example.org/cover.jpg",
        )

        payload = book.to_openlibrary_create_payload()

        self.assertEqual(payload["title"], "Example")
        self.assertEqual(payload["identifiers"]["isbn_13"], ["9781234567897"])
        self.assertEqual(payload["number_of_pages"], 288)
        self.assertEqual(payload["description"], "Desc")
        self.assertEqual(payload["subject"], "Fiction")
        self.assertEqual(payload["cover"], "https://example.org/cover.jpg")

    def test_payload_omits_optional_fields_when_absent(self) -> None:
        book = ParsedBook(
            source="artanuji",
            source_id=2,
            source_url="https://example.org/book/2",
            title="Example 2",
            author="John Smith",
            publisher="Example Publisher",
            publish_date="2023",
        )

        payload = book.to_openlibrary_create_payload()

        self.assertEqual(payload["identifiers"], {})
        self.assertNotIn("number_of_pages", payload)
        self.assertNotIn("description", payload)
        self.assertNotIn("subject", payload)
        self.assertNotIn("cover", payload)


if __name__ == "__main__":
    unittest.main()
