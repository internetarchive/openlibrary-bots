"""
Tests for sources/itan/record.py and sources/itan/provider.py

Coverage:
- ITANRecord: field parsing, to_ol_import() transformation
- Cleanup logic: bad ISBNs filtered, subjects stripped, ebook_access dropped
- Skip logic: missing title, missing/empty authors
- ITANProvider: end-to-end over real ITAN data (live HTTP, 67 records)
- Cross-validation: every output record passes import.schema.json
"""

from __future__ import annotations

import json
import os
from nturl2path import pathname2url

import jsonschema
import pytest

from olclient.imports import OLImportRecord
from sources.itan.provider import ITANProvider
from sources.itan.record import ITANRecord

# ---------------------------------------------------------------------------
# Schema validator (reuse olclient's copy of import.schema.json)
# ---------------------------------------------------------------------------

_SCHEMA_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '..', '..', '..', 'openlibrary-client-imports',  # local worktree
        'olclient', 'schemata', 'import.schema.json',
    )
)

# Fall back to installed package location if worktree path doesn't exist
if not os.path.exists(_SCHEMA_PATH):
    import olclient
    _SCHEMA_PATH = os.path.join(
        os.path.dirname(olclient.__file__), 'schemata', 'import.schema.json'
    )

with open(_SCHEMA_PATH) as _f:
    _SCHEMA = json.load(_f)

_RESOLVER = jsonschema.RefResolver(
    'file:' + pathname2url(os.path.abspath(_SCHEMA_PATH)), _SCHEMA
)
_VALIDATOR = jsonschema.Draft4Validator(_SCHEMA, resolver=_RESOLVER)


def assert_valid_schema(record: OLImportRecord) -> None:
    data = record.model_dump(exclude_none=True)
    errors = list(_VALIDATOR.iter_errors(data))
    assert not errors, f"Schema errors: {errors}\nRecord: {data}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_RAW = {
    "title": "Shadows Of The Continent",
    "authors": [{"name": "Tolulope Taiwo"}],
    "publishers": ["Itan Technologies"],
    "publish_date": "2026",
    "languages": ["eng"],
    "subjects": ["African Literature & Fiction", " Contemporary Fiction", "romance"],
    "source_records": ["itan_technologies:BOO1109"],
    "identifiers": {"itan_technologies": ["BOO1109"]},
    "ebook_access": "borrowable",          # NOT in OL schema — must be dropped
    "subtitle": "A Pan-African Romance Suspense Novel",
    "number_of_pages": 189,
    "notes": "A gripping Pan-African romantic thriller.",
    "isbn_13": ["0"],                      # placeholder — must be filtered
    "contributions": ["Editor: Jane Doe"],
}

MINIMAL_RAW = {
    "title": "Minimal Book",
    "authors": [{"name": "Author One"}],
    "publishers": ["Pub"],
    "publish_date": "2024",
    "source_records": ["itan_technologies:BOO0001"],
}


# ---------------------------------------------------------------------------
# ITANRecord unit tests
# ---------------------------------------------------------------------------

class TestITANRecord:
    def test_parses_full_record(self):
        rec = ITANRecord.model_validate(FULL_RAW)
        assert rec.title == "Shadows Of The Continent"
        assert rec.number_of_pages == 189

    def test_absorbs_ebook_access_without_error(self):
        rec = ITANRecord.model_validate(FULL_RAW)
        # ebook_access is accepted via extra='allow' but not surfaced as a typed field
        assert rec.model_extra.get("ebook_access") == "borrowable"

    def test_to_ol_import_returns_record(self):
        rec = ITANRecord.model_validate(MINIMAL_RAW)
        result = rec.to_ol_import()
        assert isinstance(result, OLImportRecord)
        assert result.title == "Minimal Book"
        assert result.source_records == ["itan_technologies:BOO0001"]

    def test_strips_whitespace_from_subjects(self):
        rec = ITANRecord.model_validate(FULL_RAW)
        result = rec.to_ol_import()
        assert " Contemporary Fiction" not in result.subjects
        assert "Contemporary Fiction" in result.subjects

    def test_filters_placeholder_isbn(self):
        rec = ITANRecord.model_validate(FULL_RAW)
        result = rec.to_ol_import()
        # isbn_13 was ["0"] — should be removed entirely
        assert result.isbn_13 is None

    def test_keeps_real_isbn(self):
        # Both "0" and "978" are ITAN placeholders; real 13-digit ISBNs survive
        raw = {**MINIMAL_RAW, "isbn_13": ["9780441569595", "0", "978"]}
        rec = ITANRecord.model_validate(raw)
        result = rec.to_ol_import()
        assert result.isbn_13 == ["9780441569595"]

    def test_drops_ebook_access_from_output(self):
        rec = ITANRecord.model_validate(FULL_RAW)
        result = rec.to_ol_import()
        dumped = result.model_dump(exclude_none=True)
        assert "ebook_access" not in dumped

    def test_skips_record_with_no_title(self):
        raw = {**MINIMAL_RAW, "title": ""}
        rec = ITANRecord.model_validate(raw)
        assert rec.to_ol_import() is None

    def test_skips_record_with_empty_authors_list(self):
        raw = {**MINIMAL_RAW, "authors": []}
        rec = ITANRecord.model_validate(raw)
        assert rec.to_ol_import() is None

    def test_skips_record_with_blank_author_names(self):
        raw = {**MINIMAL_RAW, "authors": [{"name": "  "}]}
        rec = ITANRecord.model_validate(raw)
        assert rec.to_ol_import() is None

    def test_preserves_identifiers(self):
        rec = ITANRecord.model_validate(FULL_RAW)
        result = rec.to_ol_import()
        assert result.identifiers == {"itan_technologies": ["BOO1109"]}

    def test_output_passes_schema(self):
        rec = ITANRecord.model_validate(FULL_RAW)
        assert_valid_schema(rec.to_ol_import())

    def test_minimal_output_passes_schema(self):
        rec = ITANRecord.model_validate(MINIMAL_RAW)
        assert_valid_schema(rec.to_ol_import())

    def test_all_subjects_stripped(self):
        raw = {**MINIMAL_RAW, "subjects": ["  Sci-Fi  ", " Horror", "Fantasy "]}
        rec = ITANRecord.model_validate(raw)
        result = rec.to_ol_import()
        assert result.subjects == ["Sci-Fi", "Horror", "Fantasy"]

    def test_empty_subjects_list_becomes_none(self):
        raw = {**MINIMAL_RAW, "subjects": ["  ", ""]}
        rec = ITANRecord.model_validate(raw)
        result = rec.to_ol_import()
        assert result.subjects is None


# ---------------------------------------------------------------------------
# ITANProvider — live end-to-end over real data
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def live_records():
    """Fetch all ITAN records once for the module; skip if network unavailable."""
    try:
        return list(ITANProvider().iter_ol_records())
    except Exception as exc:
        pytest.skip(f"Could not reach ITAN source: {exc}")


class TestITANProviderLive:
    def test_yields_expected_count(self, live_records):
        # 67 records in the catalog; all should yield (none are missing required fields)
        assert len(live_records) == 67

    def test_all_records_are_ol_import_records(self, live_records):
        assert all(isinstance(r, OLImportRecord) for r in live_records)

    def test_no_placeholder_isbns_in_output(self, live_records):
        for r in live_records:
            if r.isbn_13:
                assert "0" not in r.isbn_13, f"Placeholder ISBN in {r.source_records}"

    def test_no_ebook_access_in_output(self, live_records):
        for r in live_records:
            dumped = r.model_dump(exclude_none=True)
            assert "ebook_access" not in dumped

    def test_no_whitespace_leading_subjects(self, live_records):
        for r in live_records:
            if r.subjects:
                for s in r.subjects:
                    assert s == s.strip(), f"Unstripped subject {s!r} in {r.source_records}"

    def test_all_records_have_source_records_prefix(self, live_records):
        for r in live_records:
            assert any(
                sr.startswith("itan_technologies:") for sr in r.source_records
            ), f"Unexpected source_records format: {r.source_records}"

    def test_all_records_pass_json_schema(self, live_records):
        failures = []
        for r in live_records:
            errors = list(_VALIDATOR.iter_errors(r.model_dump(exclude_none=True)))
            if errors:
                failures.append((r.source_records, errors))
        assert not failures, f"{len(failures)} records failed schema validation: {failures[:3]}"
