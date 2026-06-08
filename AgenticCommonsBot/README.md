# AgenticCommonsBot

Adds one well-evidenced entry to an Open Library author's `alternate_names` array, citing Wikidata + a Wikipedia article in another language as independent sources.

Closes #450.

## What this bot does

For a single OL author at a time:

1. GET `/authors/OL...A.json`
2. Verify `alternate_names` is still empty (skip if not — someone else already handled it)
3. Append exactly one proposed addition to `alternate_names`
4. PUT the updated author JSON with an edit comment citing the two evidence URLs

That's it. One author, one addition, one PUT.

## What this bot does NOT do

- Does not generate the alternate name itself. It reads a pre-built proposal JSON. The proposal upstream is produced by a research worker (which may use an LLM) and then validated by an independent QA gate that re-fetches the two evidence URLs and checks they actually contain the proposed value.
- Does not edit works, editions, subjects, or any field other than `alternate_names`.
- Does not remove, reorder, or replace existing `alternate_names` entries.
- Does not bulk-process. Each invocation handles a single proposal item.

## Evidence requirement

Every proposal must include **at least two independent reputable sources** in the `evidence` array. The default pair:

- **Wikidata** — capture the Q-id and the matching multilingual label
- **Wikipedia (other-language article)** — capture the article title in the script being added

Other acceptable corroborators: official publisher page, university faculty page, national library authority record (LoC, BnF, NDL, NLI, etc.).

The bot is strict about the two-source minimum. If a proposal arrives with fewer than two evidence entries, the upstream gate rejects it before it reaches the bot.

## Frequency

Targeting **≤ 8 edits per day** total. Each edit issues 1 GET + 1 PUT + 1 verify GET, paced at 1.5s between requests. Well below polite-bot thresholds.

## Authentication

Uses Internet Archive S3 keys (access + secret) per OL's standard write-API auth path. Get them from https://archive.org/account/s3.php while signed in to the bot account.

```bash
export OL_BOT_ACCESS=<access key>
export OL_BOT_SECRET=<secret key>
```

The bot account is `agenticcommonsbot`.

## How to use

```bash
# Dry-run (default — does not write):
python3 wikidata_author_alias_bot.py --proposal sample_proposal.json

# Live submission:
python3 wikidata_author_alias_bot.py --proposal sample_proposal.json --live

# If proposal contains multiple items, pick one with --item-index:
python3 wikidata_author_alias_bot.py --proposal multi_item.json --item-index 2 --live
```

## Proposal JSON shape

See `sample_proposal.json` in this directory for a real example. The shape is:

```json
{
  "items": [
    {
      "ol_key": "/authors/OL2630047A",
      "task_type": "add_alternate_name",
      "author_name_primary": "Su Tong",
      "current_alternate_names": [],
      "proposed_addition": "苏童",
      "comment": "Adding native-script form per Wikidata Q778276 (zh label '苏童') and Chinese Wikipedia article title '苏童'.",
      "evidence": [
        {"source": "Wikidata Q778276", "url": "https://www.wikidata.org/wiki/Q778276", "value": "苏童"},
        {"source": "Wikipedia (zh)", "url": "https://zh.wikipedia.org/wiki/%E8%8B%8F%E7%AB%A5", "value": "苏童"}
      ],
      "rationale": "Su Tong is a major contemporary Chinese novelist (Wives and Concubines / Raise the Red Lantern). Both Wikidata and zhwiki confirm 苏童 as the canonical native-script form."
    }
  ]
}
```

## Edit comment format

Pure factual citation, with the Wikidata Q-id and Wikipedia article inline. Example:

> Adding native-script form per Wikidata Q778276 (zh label '苏童') and Chinese Wikipedia article title '苏童'.

No project attribution, no slogans.

## What a dry-run looks like

See `sample_dry_run.txt` in this directory for captured output from a real dry-run against `/authors/OL2630047A` (real OL author, real network calls, no PUT issued).

## Maintainer

- GitHub: [@agentic-commons-foundation](https://github.com/agentic-commons-foundation)
- Email: wiki-bot@agentic-commons.org
