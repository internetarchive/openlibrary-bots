from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ParsedBook:
    source: str
    source_id: int
    source_url: str
    title: str
    author: str
    publisher: str
    publish_date: str
    isbn_13: str | None = None
    isbn_10: str | None = None
    number_of_pages: int | None = None
    description: str | None = None
    subject: str | None = None
    cover_url: str | None = None

    def to_openlibrary_create_payload(self) -> dict:
        identifiers = {}
        if self.isbn_13:
            identifiers["isbn_13"] = [self.isbn_13]
        if self.isbn_10:
            identifiers["isbn_10"] = [self.isbn_10]

        payload = {
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "publish_date": self.publish_date,
            "identifiers": identifiers,
        }
        if self.number_of_pages:
            payload["number_of_pages"] = self.number_of_pages
        if self.description:
            payload["description"] = self.description
        if self.subject:
            payload["subject"] = self.subject
        if self.cover_url:
            payload["cover"] = self.cover_url
        return payload


class PublisherParser(Protocol):
    name: str
    base_url: str

    def page_url(self, item_id: int) -> str: ...

    def parse(self, html: str, item_id: int) -> ParsedBook | None:
        ...
