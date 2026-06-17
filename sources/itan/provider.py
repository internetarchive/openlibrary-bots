"""
provider.py
~~~~~~~~~~~

DataProvider for ITAN Global Publishing.

Streams the ITAN catalog JSONL file and yields ITANRecord instances.
Inherits all traversal logic from JSONLProvider — HTTP streaming,
bad-line skipping, and logging are handled upstream.

Usage::

    from sources.itan.provider import ITANProvider

    for record in ITANProvider().iter_ol_records():
        print(record.model_dump(exclude_none=True))
"""

from olclient.imports import JSONLProvider

from sources.itan.record import ITANRecord


class ITANProvider(JSONLProvider):
    SOURCE_SLUG = "itan_technologies"
    TITLE = "ITAN Global Publishing"
    SOURCE_URL = (
        "https://raw.githubusercontent.com/ITANigp/itan-ebook-backend"
        "/refs/heads/feature/open-library/data/itan_catalog.jsonl"
    )
    RECORD_CLASS = ITANRecord
