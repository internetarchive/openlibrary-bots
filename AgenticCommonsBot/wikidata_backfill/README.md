# AgenticCommonsBot — wikidata_backfill

Evidence-driven Wikidata Q-id backfill for OpenLibrary author `remote_ids.wikidata`.

Sibling of `AgenticCommonsBot/` (the alternate_names bot). Same OL bot account
(`agenticcommonsbot`), different field scope.

Around 67% of OL author records have no `remote_ids.wikidata`. Filling this
identity anchor also unblocks author-record deduplication downstream — the
Q-id is the strongest cross-source join key for deciding whether two OL
author records are the same person (context in the linked issue).

For OL authors whose `remote_ids.wikidata` is currently empty, this bot reads
a pre-verified proposal, re-fetches the Wikidata entity to confirm the
evidence still holds, and PUTs the single new value in one edit.

## What this bot does

Two modes, both pure stdlib:

### `discover` — find candidates

Stream the monthly author dump (`ol_dump_authors_latest.txt.gz`), filter to
authors that:
- have `remote_ids.wikidata` **empty**
- have `birth_date` present (name-only matching is too weak for common names)
- are not redirects / deletes

Emit OL author keys to stdout, one per line.

### `sync` — actually edit one author

For one OL author key + one candidate Q-id (from a proposal JSON):
1. POST `/account/login` with S3 keys → write-capable session
2. GET `/authors/<key>.json` → current `remote_ids`, confirm `wikidata` still empty
3. GET Wikidata `Special:EntityData/<Q-id>.json` → confirm entity exists, is a Q5 human, and evidence claims (P648 for Source A; P569 / P570 / P106 for Source B) are still present
4. If OL already has `remote_ids.wikidata` populated → skip (conflict, never overwrite)
5. If Wikidata evidence no longer holds → skip (revalidation failure)
6. Otherwise PUT updated record with `remote_ids.wikidata = "Q..."` appended (all other identifiers untouched)
7. Verify via re-fetch GET

## What this bot does NOT do

- Does not decide the identity match at PUT time. Match is decided upstream — Source A: Wikidata's own P648 self-declaration; Source B: research worker + QA gate on structured multi-field evidence.
- Does not crawl OL. Candidate discovery uses the monthly bulk dump. Per-author work uses one GET (OL) + one GET (Wikidata) + one PUT (OL) + one verify GET (OL).
- Does not edit works, editions, subjects, or any field other than `remote_ids.wikidata`.
- Does not remove or overwrite any existing entry in the `remote_ids` map — it only adds the `wikidata` key when it was previously absent.
- Does not handle author record duplicates (a separate concern; this backfill is the anchor that makes dedup tractable).
- Does not invent Q-ids. The QID must resolve to a real Wikidata entity at PUT time; if the entity is missing or has been merged/redirected, the bot skips.

## Why this design

`remote_ids.wikidata` is an identity anchor — writing the wrong Q-id fuses two
authors together, which is worse than leaving the field empty. So the review
bar is deliberately higher than for `alternate_names`:

| Concern | Resolution |
|---|---|
| OL is hammered by crawler traffic | Use monthly bulk dump for candidate discovery, not OL search / list APIs |
| Weak identity matching (name alone) | `birth_date` is required on OL side; Source B requires ≥ 2 structured Wikidata fields to match, with evidence citing specific P-ids |
| LLM hallucination of Q-ids | Every QID is re-fetched from Wikidata at PUT time; entity must exist and be Q5 (human); evidence claims must still be present |
| Overwriting a differently-linked author | Skip any author whose `remote_ids.wikidata` is already populated, even if the on-file Q-id disagrees with the proposal — those go to a human conflict-review queue, never to the bot |

## Frequency

Per-day cap of 8 edits initially. Each edit makes 1 GET (Wikidata) + 1 GET
(OL) + 1 PUT (OL) + 1 verify GET (OL) = 4 HTTP calls. Monthly dump fetch is
one streamed download (no local persistence).

## Authentication

Same `agenticcommonsbot` Internet Archive S3 keys used by the sibling
alternate_names bot at [`../README.md`](../README.md). One bot account,
two field-scoped bots.

```bash
export OL_BOT_ACCESS=<access key>
export OL_BOT_SECRET=<secret key>
```

## Usage

```bash
# Find first 10 candidates from the monthly dump:
python3 wikidata_backfill_bot.py discover --limit 10

# Dry-run a single author against a proposal file (no write):
python3 wikidata_backfill_bot.py sync /authors/OL4155123A --proposal sample_proposal.json

# Actually submit:
python3 wikidata_backfill_bot.py sync /authors/OL4155123A --proposal sample_proposal.json --live
```

## What a sync run looks like

See [`sample_run.txt`](sample_run.txt) for a captured dry-run against
`OL4155123A` (Liu Xiaobo, Wikidata `Q41617`), whose `remote_ids.wikidata`
is currently empty on OL while Wikidata already self-declares
`P648 = OL4155123A`.

## Maintainer

- GitHub: [@agentic-commons-foundation](https://github.com/agentic-commons-foundation)
- Email: wiki-bot@agentic-commons.org
