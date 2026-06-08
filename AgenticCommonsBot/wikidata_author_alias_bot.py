#!/usr/bin/env python3
"""
OpenLibrary alternate-name submission bot.

Reads a proposal JSON (produced by an upstream research worker and validated
by an independent QA gate) and adds one well-evidenced name variant to an
author's ``alternate_names`` array on OpenLibrary.

See README.md for the upstream pipeline, evidence requirements, and rate-limit
posture.

Required env vars:
  OL_BOT_ACCESS   — S3-style access key from https://archive.org/account/s3.php
  OL_BOT_SECRET   — S3-style secret key from same page
  OL_BOT_USERNAME — display username (only used in logs); defaults to
                    "AgenticCommonsBot"

Why S3 keys (not email/password): OL grants two different session privilege
levels — email+password sessions are anti-bot-restricted (PUT returns 403);
access+secret sessions get full API write privileges. The S3 keys live on
Internet Archive (https://archive.org/account/s3.php) because OL is an IA
sub-project sharing accounts.

Usage:
  python3 wikidata_author_alias_bot.py --proposal sample_proposal.json          # dry-run
  python3 wikidata_author_alias_bot.py --proposal sample_proposal.json --live   # submit

Proposal JSON shape: see README.md and sample_proposal.json.

OL auth: POST /account/login with form-encoded access + secret;
session cookie returned, then GET / PUT page .json with the cookie.
"""

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.parse
import urllib.request

BASE = "https://openlibrary.org"

REQUIRED_KEYS = ("ol_key", "task_type", "proposed_addition", "comment")

USER_AGENT = "AgenticCommonsBot/0.1 (wiki-bot@agentic-commons.org)"


def load_proposal(path, item_index):
    with open(path) as f:
        doc = json.load(f)
    if isinstance(doc, dict) and "items" in doc:
        items = doc["items"]
        if not items:
            raise ValueError(f"proposal {path}: 'items' is empty")
        if item_index < 0 or item_index >= len(items):
            raise ValueError(f"--item-index {item_index} out of range (have {len(items)})")
        proposal = items[item_index]
    elif isinstance(doc, dict) and "ol_key" in doc:
        proposal = doc
    else:
        raise ValueError(f"proposal {path}: expected single proposal or {{items:[...]}}")
    for k in REQUIRED_KEYS:
        if k not in proposal:
            raise ValueError(f"proposal missing required field: {k!r}")
    if proposal["task_type"] != "add_alternate_name":
        raise ValueError(
            f"only task_type='add_alternate_name' is supported in this MVP "
            f"(got {proposal['task_type']!r})"
        )
    if not proposal["ol_key"].startswith("/authors/"):
        raise ValueError(
            f"alternate_name task only supports /authors/* pages "
            f"(got {proposal['ol_key']!r})"
        )
    return proposal


def make_opener(user_agent):
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


def login_s3(opener, access, secret):
    """Form-POST to /account/login with S3 access+secret.

    This grants a full-privilege session (writes allowed). The alternative —
    email+password — yields an anti-bot-restricted session (PUT -> 403).
    Matches the auth pattern used by openlibrary-client (olclient).

    On success: HTTP 303 redirect + session cookie set.
    """
    # Minimal field set: adding 'remember'/'test' triggers HTTP 500 on OL.
    body = urllib.parse.urlencode({
        "access": access,
        "secret": secret,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/account/login",
        data=body, method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with opener.open(req, timeout=30) as r:
        body_text = r.read().decode("utf-8", errors="replace")
        return r.status, r.geturl(), body_text


def fetch_author(opener, ol_key):
    """GET /authors/OL...A.json — returns parsed JSON dict."""
    url = f"{BASE}{ol_key}.json"
    req = urllib.request.Request(url)
    with opener.open(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def put_author(opener, ol_key, author_data):
    """PUT /authors/OL...A.json with full updated JSON.

    Returns (status, final_url, body_text).
    """
    url = f"{BASE}{ol_key}.json"
    body = json.dumps(author_data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PUT")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    with opener.open(req, timeout=30) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--proposal", required=True, help="Path to proposal JSON")
    ap.add_argument("--item-index", type=int, default=0)
    ap.add_argument("--live", action="store_true",
                    help="Actually PUT. Default is DRY-RUN (does not write).")
    args = ap.parse_args()

    username = os.environ.get("OL_BOT_USERNAME", "AgenticCommonsBot")
    access = os.environ.get("OL_BOT_ACCESS")
    secret = os.environ.get("OL_BOT_SECRET")
    if not access or not secret:
        print("ERROR: OL_BOT_ACCESS and OL_BOT_SECRET env vars are required.", file=sys.stderr)
        print("       Get them from https://archive.org/account/s3.php (Internet", file=sys.stderr)
        print("       Archive shares OL's account system).", file=sys.stderr)
        sys.exit(2)

    proposal = load_proposal(args.proposal, args.item_index)
    ol_key = proposal["ol_key"]
    addition = proposal["proposed_addition"]
    comment = proposal["comment"]

    print("=" * 72, file=sys.stderr)
    print(f"OL alternate-name bot — {'LIVE' if args.live else 'DRY-RUN'}", file=sys.stderr)
    print(f"Proposal: {args.proposal} (item {args.item_index})", file=sys.stderr)
    print(f"OL key:   {ol_key}", file=sys.stderr)
    print(f"URL:      {BASE}{ol_key}", file=sys.stderr)
    print(f"User:     {username} (login via S3 access key {access[:6]}…)", file=sys.stderr)
    print(f"Adding:   {addition!r}", file=sys.stderr)
    print("=" * 72, file=sys.stderr)

    opener, jar = make_opener(USER_AGENT)

    print("\n[1] POST /account/login (S3 auth) …", file=sys.stderr)
    try:
        status, final_url, body = login_s3(opener, access, secret)
        print(f"  HTTP {status}, landed at {final_url}", file=sys.stderr)
        cookies = [(c.name, c.value[:10] + "…") for c in jar]
        print(f"  cookies set: {cookies}", file=sys.stderr)
    except Exception as e:
        print(f"  login failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)

    print(f"\n[2] GET {ol_key}.json (current author data) …", file=sys.stderr)
    try:
        author = fetch_author(opener, ol_key)
    except Exception as e:
        print(f"  fetch failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(4)

    current_names = author.get("alternate_names") or []
    print(f"  current alternate_names ({len(current_names)}): {current_names}", file=sys.stderr)

    if addition in current_names:
        print(f"\n⚠️  {addition!r} already in alternate_names — skipping", file=sys.stderr)
        return

    # Construct the updated author payload (do not mutate other fields)
    updated = dict(author)
    updated["alternate_names"] = current_names + [addition]
    updated["_comment"] = comment

    print(f"\n[3] Prepared PUT payload:", file=sys.stderr)
    print(f"    alternate_names: {updated['alternate_names']}", file=sys.stderr)
    print(f"    _comment (first 120 chars): {comment[:120]!r}", file=sys.stderr)

    if not args.live:
        print(f"\n[DRY-RUN] Would PUT to {BASE}{ol_key}.json", file=sys.stderr)
        print("[DRY-RUN] Re-run with --live to actually submit.", file=sys.stderr)
        return

    print(f"\n[4] LIVE PUT → {BASE}{ol_key}.json", file=sys.stderr)
    try:
        status, result_url, body = put_author(opener, ol_key, updated)
        print(f"  HTTP {status}", file=sys.stderr)
        print(f"  result url: {result_url}", file=sys.stderr)
        print(f"  body[:300]: {body[:300]!r}", file=sys.stderr)
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}", file=sys.stderr)
        print(f"  body[:500]: {e.read()[:500].decode('utf-8', errors='replace')!r}", file=sys.stderr)
        sys.exit(5)

    print(f"\n[5] Verify via GET {ol_key}.json …", file=sys.stderr)
    fresh = fetch_author(opener, ol_key)
    final_names = fresh.get("alternate_names") or []
    if addition in final_names:
        print(f"\n✅ SUCCESS — {addition!r} now in alternate_names", file=sys.stderr)
        print(f"   final list ({len(final_names)}): {final_names}", file=sys.stderr)
        print(f"   see: {BASE}{ol_key}", file=sys.stderr)
    else:
        print(f"\n❌ NOT YET present in alternate_names — may need cache refresh", file=sys.stderr)
        print(f"   observed list: {final_names}", file=sys.stderr)


if __name__ == "__main__":
    main()
