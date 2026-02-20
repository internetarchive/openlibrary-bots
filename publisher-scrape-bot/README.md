# Publisher Scraper Bot

This bot crawls configured publisher websites and creates Open Library records
using the Open Library Python client (`openlibrary-client` / `olclient`).

## Repository Layout

- `import_publisher_books.py`: crawl + parse + import entrypoint
- `publishers/base.py`: parser contract and parsed-book model
- `publishers/__init__.py`: parser registry
- `publishers/artanuji.py`: `artanuji` publisher scraper/parser
- `tests/`: unit tests for payload generation, parser extraction, and CLI guards

## Supported Publishers

- `artanuji`

Additional publishers can be added by creating a new parser module in
`publishers/` and registering it in `publishers/__init__.py`.

## What The Bot Does

1. Visits publisher book pages by numeric ID.
2. Extracts metadata (title, author, ISBN, date, pages, category, description,
   cover URL when available).
3. Converts extracted metadata into an Open Library create payload.
4. Calls `olclient` Python APIs to create the record on Open Library.
5. Optionally skips books that already exist in Open Library by ISBN.

The crawler framework supports multiple publishers via the parser registry in
`publishers/__init__.py`.

## Prerequisites

- Python 3.10+ (standard library only for this repo)
- Open Library Python client installed (`openlibrary-client`)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The bot requires `openlibrary-client` to upload/check books.

Install dependencies from repo root (or install `openlibrary-client`) before
running non-dry imports.

Run tests:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Usage

Dry run (recommended first):

```bash
python3 import_publisher_books.py \
  artanuji \
  --start-id 650 \
  --end-id 730 \
  --dry-run
```

Create records:

```bash
python3 import_publisher_books.py \
  artanuji \
  --start-id 650 \
  --end-id 730 \
  --skip-existing-isbn
```

## Useful Flags

- `--sleep-seconds`: request throttling delay
- `--request-timeout`: HTTP timeout
- `--max-books`: cap created records in one run
- `--skip-existing-isbn`: skip records already present in Open Library
- `--dry-run`: print create commands without writing to Open Library

## Adding A Publisher

1. Add `publishers/<name>.py`.
2. Implement `parse()` with publisher-specific field extraction.
3. Register it in `publishers/__init__.py` under `PARSERS`.
4. Add parser tests in `tests/test_<name>.py`.
5. Run a small ID range with `--dry-run` to validate parsing/output.

`publishers/<name>.py` should implement the `PublisherParser` protocol:
   - `page_url(item_id: int) -> str`
   - `parse(html: str, item_id: int) -> ParsedBook | None`

## PR Checklist

- Run `python3 -m py_compile import_publisher_books.py publishers/*.py`.
- Run `python3 -m unittest discover -s tests -p 'test_*.py'`.
- Run at least one dry-run import command for the target publisher.
- Confirm README examples and flags match the actual CLI behavior.
