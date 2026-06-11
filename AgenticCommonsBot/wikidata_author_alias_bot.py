#!/usr/bin/env python3
"""
Wikidata-to-OL author alternate_names sync bot.

Deterministic (no LLM) sync. For OL authors that already have a cross-linked
Wikidata Q-id but are missing one or more non-Latin labels Wikidata has, this
bot fetches the Wikidata labels, diffs against OL's current alternate_names,
and PUTs the missing non-Latin forms in a single edit.

Two modes:

  discover   Stream the OL monthly author dump and emit candidate OL keys to
             stdout. Filters to authors that (a) have remote_ids.wikidata
             populated and (b) have no non-Latin form in alternate_names.

  sync       For one OL author key, GET the current OL record + the Wikidata
             entity, compute the diff, and PUT the missing non-Latin forms.
             Defaults to dry-run; pass --live to actually submit.

Pure stdlib. Auth via Internet Archive S3 keys (S3 access + secret from
https://archive.org/account/s3.php — OL is an IA sub-project that shares
the account system).

Required env vars (sync mode only):
  OL_BOT_ACCESS   S3-style access key
  OL_BOT_SECRET   S3-style secret key

Usage:
  # find candidates from monthly dump:
  python3 wikidata_author_alias_bot.py discover --limit 10

  # dry-run a single author:
  python3 wikidata_author_alias_bot.py sync /authors/OL713582A

  # submit for real:
  python3 wikidata_author_alias_bot.py sync /authors/OL713582A --live
"""
from __future__ import annotations

import argparse
import gzip
import http.cookiejar
import json
import os
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

OL_BASE = "https://openlibrary.org"
OL_DUMP_URL = "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz"
WD_BASE = "https://www.wikidata.org"
UA_DEFAULT = "AgenticCommonsBot/0.1 (wiki-bot@agentic-commons.org)"

# Unicode block markers used to classify a label as "non-Latin". A label is
# non-Latin if any character's Unicode name contains one of these tokens.
NON_LATIN_MARKERS = (
    "CJK", "HIRAGANA", "KATAKANA", "HANGUL",
    "ARABIC", "HEBREW", "CYRILLIC", "GREEK",
    "DEVANAGARI", "BENGALI", "TAMIL", "THAI",
    "TELUGU", "GUJARATI", "KANNADA", "MALAYALAM",
    "MYANMAR", "GEORGIAN", "ARMENIAN", "ETHIOPIC",
    "TIBETAN", "KHMER", "LAO", "SINHALA",
)


def is_non_latin(s: str) -> bool:
    for ch in s:
        try:
            name = unicodedata.name(ch)
        except ValueError:
            continue
        if any(m in name for m in NON_LATIN_MARKERS):
            return True
    return False


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s.strip())


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
    """POST /account/login with S3 keys → establishes a write-capable session.

    Minimal field set: adding remember/test fields triggers HTTP 500.
    Matches the auth pattern used by olclient.
    """
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


def fetch_wikidata_labels(qid: str, user_agent: str) -> dict:
    """Return {language_code: label} for the Wikidata entity."""
    url = f"{WD_BASE}/wiki/Special:EntityData/{qid}.json"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    ent = data["entities"].get(qid, {})
    labels = ent.get("labels", {})
    return {code: l["value"] for code, l in labels.items()}


# ── discover mode ────────────────────────────────────────────────────


def discover_candidates(dump_url: str = OL_DUMP_URL,
                        user_agent: str = UA_DEFAULT,
                        limit: int | None = None):
    """Stream the OL author dump, yield (ol_key, record) for candidates.

    A candidate is an author that:
    - has `remote_ids.wikidata` set (the cross-link anchor)
    - has no non-Latin form in `alternate_names`
    """
    req = urllib.request.Request(dump_url, headers={"User-Agent": user_agent})
    yielded = 0
    scanned = 0
    skipped_no_wikidata = 0
    skipped_already_has_non_latin = 0

    with urllib.request.urlopen(req, timeout=120) as resp:
        with gzip.GzipFile(fileobj=resp) as gz:
            for raw in gz:
                scanned += 1
                if limit and yielded >= limit:
                    break
                parts = raw.decode("utf-8", errors="replace").rstrip("\n").split("\t")
                if len(parts) != 5:
                    continue
                if parts[0] != "/type/author":
                    continue
                try:
                    rec = json.loads(parts[4])
                except json.JSONDecodeError:
                    continue
                qid = (rec.get("remote_ids") or {}).get("wikidata")
                if not qid:
                    skipped_no_wikidata += 1
                    continue
                alts = rec.get("alternate_names") or []
                if any(is_non_latin(a) for a in alts):
                    skipped_already_has_non_latin += 1
                    continue
                yielded += 1
                yield rec["key"], rec

    print(
        f"# discover summary: scanned={scanned} yielded={yielded} "
        f"skipped_no_wikidata={skipped_no_wikidata} "
        f"skipped_already_has_non_latin={skipped_already_has_non_latin}",
        file=sys.stderr,
    )


# ── sync mode ────────────────────────────────────────────────────────


def compute_additions(author_record: dict, wd_labels: dict) -> list:
    """Return [(lang_code, label)] of non-Latin Wikidata labels NOT in OL.

    Dedup is value-based (NFC normalized) — multiple Wikidata language codes
    often share the same string (e.g. zh + zh-cn + zh-hans all = '苏童'),
    so we only add the first unique form.
    """
    have = {nfc(author_record.get("name") or "")}
    for a in (author_record.get("alternate_names") or []):
        have.add(nfc(a))
    have.discard("")

    seen = set()
    to_add = []
    for code, val in wd_labels.items():
        if not is_non_latin(val):
            continue
        n = nfc(val)
        if n in have or n in seen:
            continue
        seen.add(n)
        to_add.append((code, val))
    return to_add


def sync_author(ol_key: str, access: str, secret: str,
                user_agent: str = UA_DEFAULT, live: bool = False) -> dict:
    """Sync one OL author. Returns a result dict."""
    opener, _jar = make_opener(user_agent)

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

    qid = (author.get("remote_ids") or {}).get("wikidata")
    print(f"  name: {author.get('name')}", file=sys.stderr)
    print(f"  current alternate_names: {author.get('alternate_names') or []}", file=sys.stderr)
    print(f"  wikidata Q-id: {qid or '(none)'}", file=sys.stderr)

    if not qid:
        return {"status": "skipped", "reason": "no_wikidata_link", "ol_key": ol_key}

    print(f"\n[3] GET Wikidata {qid} labels", file=sys.stderr)
    labels = fetch_wikidata_labels(qid, user_agent)
    print(f"  total labels: {len(labels)}", file=sys.stderr)

    to_add = compute_additions(author, labels)
    print(f"\n[4] Diff — missing non-Latin labels: {len(to_add)}", file=sys.stderr)
    for code, val in to_add:
        print(f"    {code:10}  {val}", file=sys.stderr)

    if not to_add:
        return {
            "status": "skipped",
            "reason": "no_missing_non_latin_labels",
            "ol_key": ol_key,
            "qid": qid,
        }

    additions_only = [val for _, val in to_add]
    new_alt = sorted(set(author.get("alternate_names") or []) | set(additions_only))
    updated = dict(author)
    updated["alternate_names"] = new_alt
    updated["_comment"] = (
        f"Added {len(to_add)} non-Latin label(s) from Wikidata {qid}: "
        + ", ".join(f"'{v}'" for v in additions_only)
    )

    if not live:
        print(f"\n[DRY-RUN] Would PUT {ol_key}.json", file=sys.stderr)
        print(f"  edit comment: {updated['_comment']}", file=sys.stderr)
        print(f"  new alternate_names ({len(new_alt)}): {new_alt}", file=sys.stderr)
        print(f"\n  Re-run with --live to actually submit.", file=sys.stderr)
        return {
            "status": "dry_run",
            "ol_key": ol_key,
            "qid": qid,
            "to_add": to_add,
            "new_alternate_names": new_alt,
            "edit_comment": updated["_comment"],
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
    final = fresh.get("alternate_names") or []
    landed = all(v in final for v in additions_only)
    print(f"  final alternate_names ({len(final)}): {final}", file=sys.stderr)
    print(f"  all additions landed: {landed}", file=sys.stderr)

    return {
        "status": "published" if landed else "published_unverified",
        "ol_key": ol_key,
        "qid": qid,
        "added": to_add,
        "final_alternate_names": final,
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
    p_disc.add_argument("--limit", type=int, default=None, help="Stop after N candidates")
    p_disc.add_argument("--dump-url", default=OL_DUMP_URL)

    p_sync = sub.add_parser("sync", help="Sync a single OL author")
    p_sync.add_argument("ol_key", help="OL author key, e.g. /authors/OL713582A")
    p_sync.add_argument("--live", action="store_true",
                        help="Actually PUT. Default is DRY-RUN (does not write).")

    args = ap.parse_args()

    if args.mode == "discover":
        for ol_key, _rec in discover_candidates(dump_url=args.dump_url, limit=args.limit):
            print(ol_key)
        return

    if args.mode == "sync":
        access = os.environ.get("OL_BOT_ACCESS")
        secret = os.environ.get("OL_BOT_SECRET")
        if not access or not secret:
            print("ERROR: OL_BOT_ACCESS and OL_BOT_SECRET env vars are required.", file=sys.stderr)
            print("  Get them from https://archive.org/account/s3.php", file=sys.stderr)
            sys.exit(2)
        result = sync_author(args.ol_key, access, secret, UA_DEFAULT, live=args.live)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
