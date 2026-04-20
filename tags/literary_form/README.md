# literary_form Migration Bot

Migrates Open Library Work records to populate the `literary_form` field
based on existing subject strings.

## What this does

Classifies works as Fiction or Nonfiction by matching their existing subject
strings against a mapping table. Only adds the `literary_form` field, never
removes or modifies existing subject strings.

## Files

- `migrate_subjects.py` — main migration script
- `mappings/literary_form.json` — subject string to literary_form mappings
- `mappings/droppable.json` — strings to strip before classification
- `literary_form_dry_run.jsonl` — dry-run output on 100 works (awaiting mentor review)

## Design decisions

**Fiction wins on conflict:** when a work has subjects matching both Fiction
and Nonfiction signals, Fiction is assigned by default. Nonfiction is only
assigned if strong unambiguous markers are present (biography, memoir,
autobiography). Topic subdivisions like "History" appear on both fiction and
nonfiction works and are not reliable Nonfiction signals.

**droppable.json fix:** `fiction`, `nonfiction`, `non-fiction`, and
`fiction, general` were previously in droppable.json and being silently
discarded before classification. Moved to literary_form.json as direct
mappings, unblocking ~673,756 works.

## Coverage

Full corpus scan (40.79M works, 2026-03-31 dump):
- Works covered: 11,933,832 (29.26%)
- Nonfiction: 8,638,073 (21.18%)
- Fiction: 2,238,600 (5.49%)
- Both (conflict resolved): 1,057,159 (2.59%)

Subject-string matching ceiling is approximately 30-32%.

## Bot account

Uses `OpenLibraryTagsBot`. Bulk writes (>100 records) require @hornc
review before execution.