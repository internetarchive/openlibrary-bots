"""
record.py
~~~~~~~~~

DataProviderRecord for ITAN Global Publishing.

The ITAN catalog is already structured close to the OL import format, so the
transformation is mostly cleanup:

  - Strip leading/trailing whitespace from subjects (several have " Subject")
  - Filter invalid isbn_13 values — the catalog uses "0" as a placeholder
  - Drop ebook_access, which is not in the OL import schema

Source: https://github.com/ITANigp/itan-ebook-backend
Issue:  https://github.com/internetarchive/openlibrary/issues/12091
"""

from __future__ import annotations

import re
from typing import List, Optional

from olclient.imports import DataProviderRecord, OLAuthor, OLImportRecord

# OL import schema pattern for isbn_13
_ISBN13_RE = re.compile(r'^([0-9][- ]*){13}$')


class ITANRecord(DataProviderRecord):
    """One record from the ITAN catalog JSONL file.

    Field names intentionally match the OL import schema because ITAN pre-formats
    their data that way. extra='allow' (inherited) absorbs ebook_access and any
    other ITAN-specific keys without raising.
    """

    title: str
    authors: List[dict]
    publishers: List[str]
    publish_date: str
    source_records: List[str]
    identifiers: Optional[dict] = None
    languages: Optional[List[str]] = None
    subjects: Optional[List[str]] = None
    subtitle: Optional[str] = None
    number_of_pages: Optional[int] = None
    notes: Optional[str] = None
    isbn_13: Optional[List[str]] = None
    isbn_10: Optional[List[str]] = None
    contributions: Optional[List[str]] = None

    # ebook_access and any future ITAN-specific fields are absorbed by extra='allow'

    def to_ol_import(self) -> Optional[OLImportRecord]:
        if not self.title or not self.authors:
            return None

        authors = [
            OLAuthor(name=a["name"])
            for a in self.authors
            if a.get("name", "").strip()
        ]
        if not authors:
            return None

        subjects = (
            [s.strip() for s in self.subjects if s.strip()]
            if self.subjects
            else None
        )

        # Filter malformed ISBNs — ITAN uses "0" and "978" as placeholders
        isbn_13 = (
            [v for v in self.isbn_13 if _ISBN13_RE.match(v)]
            if self.isbn_13
            else None
        ) or None

        isbn_10 = (
            [v for v in self.isbn_10 if v and v != "0"]
            if self.isbn_10
            else None
        ) or None

        return OLImportRecord(
            title=self.title,
            source_records=self.source_records,
            authors=authors,
            publishers=self.publishers,
            publish_date=self.publish_date,
            subtitle=self.subtitle,
            number_of_pages=self.number_of_pages,
            notes=self.notes,
            languages=self.languages,
            subjects=subjects or None,
            isbn_13=isbn_13,
            isbn_10=isbn_10,
            identifiers=self.identifiers,
            contributions=self.contributions,
        )
