# AgenticCommonsBot

Deterministic Wikidata-to-OpenLibrary sync for author `alternate_names`.

For OpenLibrary authors that already have a cross-linked Wikidata Q-id but
lack one or more non-Latin labels Wikidata has, this bot fetches the
Wikidata labels, diffs against OpenLibrary's current `alternate_names`,
and PUTs the missing non-Latin forms in a single edit.

Closes [internetarchive/openlibrary#12887](https://github.com/internetarchive/openlibrary/issues/12887).

## What this bot does

Two modes, both pure stdlib:

### `discover` — find candidates

Stream the monthly author dump (`ol_dump_authors_latest.txt.gz`), filter to
authors that:
- have `remote_ids.wikidata` populated (cross-linked Q-id, anchors identity)
- have no non-Latin form in `alternate_names` (Unicode-block check)

Emit OL author keys to stdout, one per line.

### `sync` — actually edit one author

For one OL author key:
1. POST `/account/login` with S3 keys → write-capable session
2. GET `/authors/<key>.json` → current `alternate_names`, current Q-id link
3. GET Wikidata `Special:EntityData/<Q-id>.json` → all label translations
4. Diff: non-Latin Wikidata labels MINUS OL's current alternate_names (NFC-normalized, value-level dedup across language codes)
5. If diff is empty → skip; otherwise PUT updated record
6. Verify via re-fetch GET

## What this bot does NOT do

- Does not use an LLM, fuzzy matching, or any model judgment. Identity match is anchored on the OL↔Wikidata cross-link; missing-form detection is set difference over Unicode-block-filtered labels.
- Does not crawl OL. Candidate discovery uses the monthly bulk dump (one HTTP GET per month). Per-author work uses one GET + one PUT + one verify GET.
- Does not edit works, editions, subjects, or any field other than `alternate_names`.
- Does not remove, reorder, or replace existing `alternate_names` entries — it appends only.
- Does not handle author record duplicates (a separate concern; out of scope here).
- Does not invent or transliterate names. Only labels already present on Wikidata are propagated.

## Why this design

Following review feedback on issue #12887:

| Concern | Resolution |
|---|---|
| OL is hammered by crawler traffic | Use monthly bulk dump for candidate discovery, not OL search/list APIs |
| Weak identity matching (matching by name alone) | Require OL record to have `remote_ids.wikidata` populated; identity comes from the existing cross-link, not from heuristics |
| One-addition-per-edit is too conservative | Each edit adds **all** missing non-Latin forms from Wikidata at once |
| Wikidata + Wikipedia aren't really independent sources | Wikidata is the sole authoritative source; the Q-id anchors the match |

## Frequency

Per-day cap of 8 edits initially. Each edit makes 1 GET (Wikidata) + 1 GET
(OL) + 1 PUT (OL) + 1 verify GET (OL) = 4 HTTP calls. Monthly dump fetch is
one streamed download (no local persistence).

`work_count`-descending candidate ordering is a future enhancement — it
requires either an additional OL works-dump pass (~several GB) or batch
queries to OL search, neither of which is in this version.

## Authentication

Internet Archive S3 keys (access + secret) per OL's standard write-API auth
path. Get them from https://archive.org/account/s3.php while signed in to
the bot account.

```bash
export OL_BOT_ACCESS=<access key>
export OL_BOT_SECRET=<secret key>
```

The bot account is `agenticcommonsbot`.

## Usage

```bash
# Find first 10 candidates from the monthly dump:
python3 wikidata_author_alias_bot.py discover --limit 10

# Dry-run a single author (no write):
python3 wikidata_author_alias_bot.py sync /authors/OL713582A

# Actually submit:
python3 wikidata_author_alias_bot.py sync /authors/OL713582A --live
```

## What a sync run looks like

See [`sample_run.txt`](sample_run.txt) for a captured dry-run against the
canonical Su Tong record (`/authors/OL713582A`). Summary of that run:

- 41 Wikidata labels for Q778276
- 19 non-Latin after Unicode-block filter
- 7 net new after dedup against OL's existing 6 `alternate_names`
- Edit would add: Hebrew, Russian, Thai, Arabic + Egyptian Arabic variant, Korean, Assamese (Bulgarian "Су Тун" was deduped against Russian's identical spelling)

## Maintainer

- GitHub: [@agentic-commons-foundation](https://github.com/agentic-commons-foundation)
- Email: wiki-bot@agentic-commons.org
