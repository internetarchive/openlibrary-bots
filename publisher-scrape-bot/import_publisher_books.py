#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from publishers import PARSERS

if TYPE_CHECKING:
    from publishers.base import ParsedBook


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl publisher site and create books via openlibrary-client."
    )
    parser.add_argument(
        "publisher",
        choices=sorted(PARSERS.keys()),
        help="Publisher parser to use (example: artanuji)",
    )
    parser.add_argument("--start-id", type=int, default=1, help="Start book id")
    parser.add_argument(
        "--end-id", type=int, default=5000, help="End book id (inclusive)"
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.4,
        help="Delay between requests to avoid overloading publisher site",
    )
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=20.0,
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--skip-existing-isbn",
        action="store_true",
        help="Check Open Library by ISBN and skip if a book already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Crawl and parse only; print create payloads without creating",
    )
    parser.add_argument(
        "--max-books",
        type=int,
        default=0,
        help="Stop after creating this many books (0 = unlimited)",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> str | None:
    if args.start_id < 1:
        return "--start-id must be >= 1"
    if args.end_id < args.start_id:
        return "--end-id must be >= --start-id"
    if args.sleep_seconds < 0:
        return "--sleep-seconds must be >= 0"
    if args.request_timeout <= 0:
        return "--request-timeout must be > 0"
    if args.max_books < 0:
        return "--max-books must be >= 0"
    return None


def fetch_html(url: str, timeout: float) -> str | None:
    req = Request(
        url,
        headers={
            "User-Agent": "OpenGeoLibraryBot/0.1 (+https://openlibrary.org)",
            "Accept-Language": "en-US,en;q=0.9,ka;q=0.8",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            content_type = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(content_type, errors="replace")
    except HTTPError as exc:
        if exc.code in (403, 404):
            return None
        raise
    except URLError:
        return None


def load_ol_client() -> tuple[Any, Any]:
    from olclient import common as ol_common
    from olclient.openlibrary import OpenLibrary

    return OpenLibrary, ol_common


def parsed_book_to_ol_book(book: ParsedBook, ol_common: Any) -> Any:
    identifiers = {}
    if book.isbn_13:
        identifiers["isbn_13"] = [book.isbn_13]
    if book.isbn_10:
        identifiers["isbn_10"] = [book.isbn_10]

    return ol_common.Book(
        title=book.title,
        authors=[ol_common.Author(name=book.author)],
        publisher=book.publisher,
        publish_date=book.publish_date,
        identifiers=identifiers,
        number_of_pages=book.number_of_pages,
        description=book.description,
        subject=book.subject,
        cover=book.cover_url,
    )


def run_ol_create(
    ol: Any, ol_common: Any, book: ParsedBook, dry_run: bool
) -> tuple[bool, str]:
    payload_json = json.dumps(book.to_openlibrary_create_payload(), ensure_ascii=False)
    if dry_run:
        return True, f"DRY RUN: {payload_json}"

    try:
        created = ol.create_book(parsed_book_to_ol_book(book, ol_common))
        created_olid = getattr(created, "olid", "")
        if created_olid:
            return True, f"created={created_olid}"
        return True, "created"
    except Exception as exc:
        return False, str(exc)


def ol_book_exists_by_isbn(ol: Any, isbn: str) -> bool:
    try:
        edition = ol.Edition.get(isbn=isbn)
    except Exception:
        return False
    return edition is not None


def process_book(
    book: ParsedBook,
    args: argparse.Namespace,
    ol: Any,
    ol_common: Any,
) -> tuple[str, str]:
    payload = book.to_openlibrary_create_payload()

    identifiers = payload.get("identifiers", {})
    isbn = ""
    if identifiers.get("isbn_13"):
        isbn = identifiers["isbn_13"][0]
    elif identifiers.get("isbn_10"):
        isbn = identifiers["isbn_10"][0]

    if args.skip_existing_isbn and isbn and ol_book_exists_by_isbn(ol, isbn):
        return "skipped", f"id={book.source_id} isbn={isbn} already exists"

    ok, output = run_ol_create(ol, ol_common, book, args.dry_run)
    if ok:
        return "created", f"id={book.source_id} {book.title} -> {output}"
    return "failed", f"id={book.source_id} {book.title} -> {output}"


def main() -> int:
    args = parse_args()
    if arg_error := validate_args(args):
        print(arg_error, file=sys.stderr)
        return 2

    parser = PARSERS[args.publisher]
    ol = None
    ol_common = None

    if not args.dry_run or args.skip_existing_isbn:
        try:
            OpenLibrary, ol_common = load_ol_client()
            ol = OpenLibrary()
        except Exception as exc:
            print(f"Failed to initialize openlibrary-client: {exc}", file=sys.stderr)
            return 2

    created = 0
    skipped = 0
    failed = 0
    misses = 0

    for item_id in range(args.start_id, args.end_id + 1):
        url = parser.page_url(item_id)
        html = fetch_html(url, timeout=args.request_timeout)

        if not html:
            misses += 1
            continue

        parsed = parser.parse(html, item_id)
        if not parsed:
            misses += 1
            time.sleep(args.sleep_seconds)
            continue

        misses = 0

        status, detail = process_book(parsed, args, ol, ol_common)
        if status == "created":
            created += 1
            print(f"OK {detail}")
        elif status == "skipped":
            skipped += 1
            print(f"SKIP {detail}")
        else:
            failed += 1
            print(f"FAIL {detail}", file=sys.stderr)

        if args.max_books and created >= args.max_books:
            print(f"Reached --max-books={args.max_books}; stopping.")
            break

        time.sleep(args.sleep_seconds)

    print(
        "Summary: "
        f"created={created} skipped={skipped} failed={failed} "
        f"range={args.start_id}-{args.end_id} misses={misses}"
    )
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
