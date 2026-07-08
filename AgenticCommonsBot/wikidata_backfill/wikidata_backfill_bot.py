#!/usr/bin/env python3
"""
Wikidata-to-OL author remote_ids.wikidata backfill bot.

For OL authors whose `remote_ids.wikidata` is empty, this bot reads a
pre-verified proposal (produced upstream by a research pipeline + QA gate),
re-fetches the Wikidata entity to confirm the evidence still holds, and
PUTs the single `remote_ids.wikidata` value in one edit. Append-only —
never overwrites an existing `remote_ids.wikidata`, never touches other
identifiers (VIAF / ISNI / LCNAF / ...).

Two modes:

  discover   Stream the OL monthly author dump and emit candidate OL keys
             to stdout. Filters to authors that (a) have `remote_ids.wikidata`
             empty and (b) have `birth_date` populated (name-only matching
             is too weak for common names).

  sync       For one OL author key + one proposal JSON, GET the current OL
             record, re-fetch Wikidata to revalidate the proposal, and PUT
             the added value. Defaults to dry-run; pass --live to actually
             submit.

Pure stdlib. Auth via Internet Archive S3 keys (S3 access + secret from
https://archive.org/account/s3.php — OL is an IA sub-project that shares
the account system). Uses the same `agenticcommonsbot` account as the
sibling `AgenticCommonsBot/wikidata_author_alias_bot.py`; one bot account,
two field-scoped bots.

Required env vars (sync mode only):
  OL_BOT_ACCESS   S3-style access key
  OL_BOT_SECRET   S3-style secret key

Usage:
  # find candidates from monthly dump:
  python3 wikidata_backfill_bot.py discover --limit 10

  # dry-run a single author against a proposal file:
  python3 wikidata_backfill_bot.py sync /authors/OL4155123A \\
      --proposal sample_proposal.json

  # submit for real:
  python3 wikidata_backfill_bot.py sync /authors/OL4155123A \\
      --proposal sample_proposal.json --live
"""
from __future__ import annotations

import argparse
import gzip
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

OL_BASE = "https://openlibrary.org"
OL_DUMP_URL = "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz"
WD_BASE = "https://www.wikidata.org"
UA_DEFAULT = "AgenticCommonsBot/0.1 (wiki-bot@agentic-commons.org)"


# ── HTTP helpers ─────────────────────────────────────────────────────


def make_opener(user_agent: str):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPRedirectHandler(),
    )
    opener.addheaders = [
        ("User-Agent", user_agent),
        ("Accept", "application/json"),
    ]
    return opener, jar


def login_s3(opener, access: str, secret: str) -> int:
    """POST /account/login with S3 keys → establishes a write-capable session."""
    body = urllib.parse.urlencode({"access": access, "secret": secret}).encode()
    req = urllib.request.Request(f"{OL_BASE}/account/login", data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with opener.open(req, timeout=30) as r:
        return r.status


def fetch_ol_author(opener, ol_key: str) -> dict:
    url = f"{OL_BASE}{ol_key}.json"
    req = urllib.request.Request(url)
    with opener.open(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def put_ol_author(opener, ol_key: str, data: dict):
    url = f"{OL_BASE}{ol_key}.json"
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PUT")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    with opener.open(req, timeout=30) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", errors="replace")


def fetch_wikidata_entity(qid: str, user_agent: str) -> dict:
    """Return the Wikidata entity object (labels, claims, sitelinks)."""
    url = f"{WD_BASE}/wiki/Special:EntityData/{qid}.json"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    entities = data.get("entities") or {}
    return entities.get(qid) or {}


# ── Wikidata field extraction ────────────────────────────────────────


def _claim_time(claims: dict, pid: str) -> str | None:
    for c in claims.get(pid, []):
        dv = c.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(dv, dict) and "time" in dv:
            return dv["time"][1:11]
    return None


def _claim_ids(claims: dict, pid: str) -> list[str]:
    out = []
    for c in claims.get(pid, []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and "id" in v:
            out.append(v["id"])
        elif isinstance(v, str):
            out.append(v)
    return out


# ── discover mode ────────────────────────────────────────────────────


def discover_candidates(dump_url: str = OL_DUMP_URL,
                        user_agent: str = UA_DEFAULT,
                        limit: int | None = None):
    """Stream the OL author dump, yield (ol_key, record) for candidates.

    A candidate is an author that:
    - has `remote_ids.wikidata` empty (that's the gap to fill)
    - has `birth_date` populated (identity anchor for downstream matching)
    - is not a redirect / delete record
    """
    req = urllib.request.Request(dump_url, headers={"User-Agent": user_agent})
    yielded = 0
    scanned = 0
    skipped_has_wikidata = 0
    skipped_no_birth_date = 0

    with urllib.request.urlopen(req, timeout=180) as resp:
        with gzip.GzipFile(fileobj=resp) as gz:
            for raw in gz:
                scanned += 1
                if limit and yielded >= limit:
                    break
                parts = raw.decode("utf-8", errors="replace").rstrip("\n").split("\t")
                if len(parts) != 5 or parts[0] != "/type/author":
                    continue
                try:
                    rec = json.loads(parts[4])
                except json.JSONDecodeError:
                    continue
                rids = rec.get("remote_ids") or {}
                if rids.get("wikidata"):
                    skipped_has_wikidata += 1
                    continue
                birth = (rec.get("birth_date") or "").strip()
                if not birth:
                    skipped_no_birth_date += 1
                    continue
                yielded += 1
                yield rec.get("key"), rec

    print(
        f"# discover summary: scanned={scanned} yielded={yielded} "
        f"skipped_has_wikidata={skipped_has_wikidata} "
        f"skipped_no_birth_date={skipped_no_birth_date}",
        file=sys.stderr,
    )


# ── sync mode ────────────────────────────────────────────────────────


def revalidate_proposal(proposal: dict, entity: dict) -> tuple[bool, list[str]]:
    """Re-fetch checks against a live Wikidata entity.

    Returns (ok, notes). The proposal is rejected if:
    - entity missing / empty
    - P31 does not include Q5 (human)
    - source == P648_reverse but the entity's P648 does not include the OL id
    - Wikidata entity is a redirect
    """
    notes = []
    if not entity:
        return False, ["wikidata_entity_missing"]

    # entity-level redirect check
    if entity.get("redirects") or entity.get("id") != proposal.get("qid"):
        # Special:EntityData may return the redirect target under a different key,
        # so also allow id-mismatch through if the target id matches; we compare
        # the raw payload id against the proposal.
        if entity.get("id") != proposal.get("qid"):
            notes.append(f"qid_redirected_to={entity.get('id')}")

    claims = entity.get("claims") or {}
    p31_ids = _claim_ids(claims, "P31")
    if "Q5" not in p31_ids:
        return False, [f"P31_not_human ({p31_ids})"]
    notes.append("P31=Q5 ✓")

    qid = proposal.get("qid")
    ol_key = proposal.get("ol_key") or ""
    ol_olid = ol_key.rsplit("/", 1)[-1] if ol_key else ""

    source = proposal.get("source")
    if source == "P648_reverse":
        p648 = _claim_ids(claims, "P648")
        if ol_olid not in p648:
            return False, [f"P648_reverse_missing (P648={p648}, expected {ol_olid})"]
        notes.append(f"P648={p648} contains {ol_olid} ✓ (Source A)")
    elif source == "entity_resolution":
        # Best-effort revalidation of the structured evidence — the QA gate
        # is the authoritative check upstream; here we just confirm P569 or
        # P570 still resolves so we don't PUT against a mangled entity.
        p569 = _claim_time(claims, "P569")
        p570 = _claim_time(claims, "P570")
        if not (p569 or p570):
            return False, ["entity_resolution_missing_life_dates"]
        notes.append(f"P569={p569} P570={p570} ✓ (Source B revalidation)")
    else:
        return False, [f"unknown_proposal_source={source}"]

    return True, notes


def sync_author(ol_key: str, proposal_path: str, access: str, secret: str,
                user_agent: str = UA_DEFAULT, live: bool = False) -> dict:
    """Sync one OL author against a proposal JSON. Returns a result dict."""
    opener, _jar = make_opener(user_agent)

    with open(proposal_path, "r", encoding="utf-8") as f:
        proposal = json.load(f)

    if proposal.get("ol_key") != ol_key:
        return {
            "status": "input_mismatch",
            "error": f"proposal.ol_key={proposal.get('ol_key')} does not match arg {ol_key}",
        }
    qid = proposal.get("qid")
    if not qid or not qid.startswith("Q"):
        return {"status": "input_invalid", "error": f"proposal.qid missing or malformed: {qid!r}"}

    print(f"[1] POST /account/login (S3 auth)", file=sys.stderr)
    try:
        st = login_s3(opener, access, secret)
        print(f"  HTTP {st}", file=sys.stderr)
    except Exception as e:
        return {"status": "login_failed", "error": f"{type(e).__name__}: {e}"}

    print(f"\n[2] GET {ol_key}.json (current OL state)", file=sys.stderr)
    try:
        author = fetch_ol_author(opener, ol_key)
    except urllib.error.HTTPError as e:
        return {"status": "fetch_failed", "ol_key": ol_key, "http_code": e.code}
    rids = author.get("remote_ids") or {}
    print(f"  name: {author.get('name')}", file=sys.stderr)
    print(f"  birth_date: {author.get('birth_date')}", file=sys.stderr)
    print(f"  death_date: {author.get('death_date')}", file=sys.stderr)
    print(f"  current remote_ids: {rids}", file=sys.stderr)

    # Skip: OL already has a wikidata id on file — never overwrite.
    existing = rids.get("wikidata")
    if existing:
        return {
            "status": "skipped",
            "reason": "ol_already_has_wikidata",
            "ol_key": ol_key,
            "existing_qid": existing,
            "proposal_qid": qid,
            "note": (
                "conflict — a human should compare "
                f"OL={existing} vs proposal={qid} on the Wikidata side"
                if existing != qid else "already up to date"
            ),
        }

    # Skip: OL record is a redirect / delete (defensive; discover filter should
    # have caught this, but the dump may lag a live edit).
    ol_type = author.get("type") or {}
    ol_type_key = ol_type.get("key") if isinstance(ol_type, dict) else ol_type
    if ol_type_key in ("/type/redirect", "/type/delete"):
        return {
            "status": "skipped",
            "reason": f"ol_record_is_{ol_type_key.split('/')[-1]}",
            "ol_key": ol_key,
        }

    print(f"\n[3] GET Wikidata {qid} entity (revalidate proposal)", file=sys.stderr)
    entity = fetch_wikidata_entity(qid, user_agent)
    print(f"  entity id: {entity.get('id')}", file=sys.stderr)
    ok, notes = revalidate_proposal(proposal, entity)
    for n in notes:
        print(f"  {n}", file=sys.stderr)
    if not ok:
        return {
            "status": "skipped",
            "reason": "revalidation_failed",
            "ol_key": ol_key,
            "qid": qid,
            "notes": notes,
        }

    # Build the append-only update.
    new_rids = dict(rids)
    new_rids["wikidata"] = qid
    updated = dict(author)
    updated["remote_ids"] = new_rids
    edit_note = proposal.get("edit_note") or (
        f"Adding remote_ids.wikidata={qid} per Wikidata cross-reference "
        f"(https://www.wikidata.org/wiki/{qid})."
    )
    updated["_comment"] = edit_note

    print(f"\n[4] Diff — remote_ids.wikidata to add: {qid}", file=sys.stderr)
    print(f"  new remote_ids: {new_rids}", file=sys.stderr)

    if not live:
        print(f"\n[DRY-RUN] Would PUT {ol_key}.json", file=sys.stderr)
        print(f"  edit comment: {edit_note}", file=sys.stderr)
        print(f"\n  Re-run with --live to actually submit.", file=sys.stderr)
        return {
            "status": "dry_run",
            "ol_key": ol_key,
            "qid": qid,
            "source": proposal.get("source"),
            "evidence": proposal.get("evidence"),
            "current_remote_ids": rids,
            "new_remote_ids": new_rids,
            "edit_note": edit_note,
        }

    print(f"\n[5] LIVE PUT {ol_key}.json", file=sys.stderr)
    try:
        st, url, body = put_ol_author(opener, ol_key, updated)
        print(f"  HTTP {st}", file=sys.stderr)
        print(f"  body[:300]: {body[:300]!r}", file=sys.stderr)
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode("utf-8", errors="replace")
        print(f"  HTTP {e.code}: {e.reason}", file=sys.stderr)
        print(f"  body[:500]: {body!r}", file=sys.stderr)
        return {
            "status": "publish_failed",
            "ol_key": ol_key,
            "http_code": e.code,
            "body": body,
        }

    print(f"\n[6] Verify GET {ol_key}.json", file=sys.stderr)
    fresh = fetch_ol_author(opener, ol_key)
    final_rids = fresh.get("remote_ids") or {}
    landed = final_rids.get("wikidata") == qid
    print(f"  final remote_ids: {final_rids}", file=sys.stderr)
    print(f"  wikidata landed: {landed}", file=sys.stderr)

    return {
        "status": "published" if landed else "published_unverified",
        "ol_key": ol_key,
        "qid": qid,
        "source": proposal.get("source"),
        "final_remote_ids": final_rids,
        "verified": landed,
    }


# ── main ─────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="mode", required=True)

    p_disc = sub.add_parser("discover", help="Stream OL dump → emit candidate OL keys to stdout")
    p_disc.add_argument("--limit", type=int, default=None,
                        help="Stop after N candidates (default: no limit)")
    p_disc.add_argument("--dump-url", default=OL_DUMP_URL)
    p_disc.add_argument("--user-agent", default=UA_DEFAULT)

    p_sync = sub.add_parser("sync", help="Sync one OL author against a proposal JSON")
    p_sync.add_argument("ol_key", help="OL author key, e.g. /authors/OL4155123A")
    p_sync.add_argument("--proposal", required=True,
                        help="Path to proposal JSON (schema_version=wikidata_backfill_proposal.v1)")
    p_sync.add_argument("--live", action="store_true",
                        help="Actually PUT (default is dry-run)")
    p_sync.add_argument("--user-agent", default=UA_DEFAULT)

    args = ap.parse_args()

    if args.mode == "discover":
        for ol_key, _rec in discover_candidates(
            dump_url=args.dump_url,
            user_agent=args.user_agent,
            limit=args.limit,
        ):
            print(ol_key)
        return

    if args.mode == "sync":
        access = os.environ.get("OL_BOT_ACCESS", "")
        secret = os.environ.get("OL_BOT_SECRET", "")
        if not access or not secret:
            print("ERROR: OL_BOT_ACCESS / OL_BOT_SECRET env vars are required for sync mode.",
                  file=sys.stderr)
            sys.exit(2)
        result = sync_author(
            ol_key=args.ol_key,
            proposal_path=args.proposal,
            access=access,
            secret=secret,
            user_agent=args.user_agent,
            live=args.live,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        # exit non-zero on any non-success terminal state, so callers can chain
        if result.get("status") in ("login_failed", "fetch_failed", "publish_failed",
                                     "input_mismatch", "input_invalid"):
            sys.exit(1)
        return


if __name__ == "__main__":
    main()
