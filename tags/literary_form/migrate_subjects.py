"""
migrate_subjects.py

Migrates Open Library legacy subject strings to canonical typed tags.

Usage:
    python migrate_subjects.py --work OL82563W
    python migrate_subjects.py --file work.json
    python migrate_subjects.py --batch ol_ids.txt --output output/
    python migrate_subjects.py --work OL82563W --dry-run

See scripts/README.md for full documentation.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
MAPPINGS_DIR = Path(__file__).parent / "mappings"

OL_WORK_URL = "https://openlibrary.org/works/{work_id}.json"


# ---------------------------------------------------------------------------
# Load mappings
# ---------------------------------------------------------------------------

def load_mapping(name: str) -> dict[str, str]:
    """Load a JSON mapping file from scripts/mappings/."""
    path = MAPPINGS_DIR / f"{name}.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def load_set(name: str) -> set[str]:
    """Load a JSON list file as a set (e.g. droppable.json)."""
    path = MAPPINGS_DIR / f"{name}.json"
    if not path.exists():
        return set()
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return {s.lower().strip() for s in data}
    return set(data.keys())


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

READING_LEVEL_RE = re.compile(
    r"reading level.grade\s*\d+|grade\s*\d+|rl\s*\d+", re.IGNORECASE
)
CLASSIFICATION_RE = re.compile(
    r"^[0-9]{3}(\.[0-9]+)?$|^[a-z]{1,3}\s*[0-9]+|^pr[0-9]", re.IGNORECASE
)


def normalize(s: str) -> str:
    """Lowercase and strip a subject string for mapping lookup."""
    return s.lower().strip()


def is_reading_level(s: str) -> bool:
    return bool(READING_LEVEL_RE.search(s))


def is_classification_code(s: str) -> bool:
    return bool(CLASSIFICATION_RE.match(s.strip()))


# ---------------------------------------------------------------------------
# Core classifier
# ---------------------------------------------------------------------------

class SubjectClassifier:
    def __init__(self):
        self.literary_form_map = load_mapping("literary_form")
        self.genres_map = load_mapping("genres")
        self.subgenres_map = load_mapping("subgenres")
        self.formats_map = load_mapping("content_formats")
        self.themes_map = load_mapping("literary_themes")
        self.tropes_map = load_mapping("literary_tropes")
        self.topics_map = load_mapping("main_topics")
        self.audience_map = load_mapping("audience")
        self.droppable = load_set("droppable")
        self.people_overrides = load_mapping("people_overrides")
        self.places_overrides = load_mapping("places_overrides")

    def classify_subject(self, raw: str) -> tuple[str, str | None]:
        """
        Classify a single subject string.

        Returns (type, canonical_value) where type is one of:
          literary_form, genres, subgenres, content_formats, literary_themes,
          literary_tropes, main_topics, audience, reading_level,
          classification_code, drop, unmapped
        """
        key = normalize(raw)

        # Audience strings (before hard drops, since some overlap)
        if key in self.audience_map:
            return ("audience", self.audience_map[key])

        # Hard drops
        if key in self.droppable:
            return ("drop", None)

        # Reading levels
        if is_reading_level(raw):
            return ("reading_level", raw.strip())

        # Classification codes (Dewey, LC call numbers)
        if is_classification_code(raw):
            return ("classification_code", raw.strip())

        # Explicit prefix-typed tags (e.g. "form:novel", "genre:tragedy")
        if ":" in raw:
            prefix, _, value = raw.partition(":")
            prefix = prefix.strip().lower()
            value = value.strip()
            type_map = {
                "form": "literary_form",
                "audience": "audience",
                "genre": "genres",
                "subgenre": "subgenres",
                "format": "content_formats",
                "theme": "literary_themes",
                "trope": "literary_tropes",
                "topic": "main_topics",
                "mood": "moods",
            }
            if prefix in type_map:
                return (type_map[prefix], value.title())

        # Mapping lookups (in priority order)
        if key in self.literary_form_map:
            return ("literary_form", self.literary_form_map[key])
        if key in self.genres_map:
            return ("genres", self.genres_map[key])
        if key in self.subgenres_map:
            return ("subgenres", self.subgenres_map[key])
        if key in self.formats_map:
            return ("content_formats", self.formats_map[key])
        if key in self.themes_map:
            return ("literary_themes", self.themes_map[key])
        if key in self.tropes_map:
            return ("literary_tropes", self.tropes_map[key])
        if key in self.topics_map:
            return ("main_topics", self.topics_map[key])

        return ("unmapped", raw.strip())

    def classify_work(self, work: dict) -> dict:
        """
        Given a work JSON dict (from OL API), produce a structured tag output.
        """
        result: dict[str, list] = {
            "literary_form": [],
            "audience": [],
            "genres": [],
            "subgenres": [],
            "content_formats": [],
            "moods": [],
            "literary_themes": [],
            "literary_tropes": [],
            "main_topics": [],
            "sub_topics": [],
            "people": [],
            "places": [],
            "times": [],
            "things": [],
            "reading_level": [],
            "classification_codes": [],
            "unmapped": [],
        }

        # Classify flat subjects
        for raw in work.get("subjects", []):
            tag_type, value = self.classify_subject(raw)
            if tag_type == "drop" or value is None:
                continue
            if tag_type == "reading_level":
                result["reading_level"].append(value)
            elif tag_type == "classification_code":
                result["classification_codes"].append(value)
            elif tag_type in result:
                if value not in result[tag_type]:
                    result[tag_type].append(value)
            else:
                result["unmapped"].append(raw)

        # Resolve literary_form conflicts
        # Fiction wins unless strong Nonfiction-specific signals are present
        if "Fiction" in result["literary_form"] and "Nonfiction" in result["literary_form"]:
            strong_nonfiction = {
                'biography', 'biographies', 'autobiography', 'autobiographies',
                'memoir', 'memoirs', 'juvenile nonfiction'
            }
            subjects_lower = {s.lower().strip() for s in work.get("subjects", [])}
            if subjects_lower & strong_nonfiction:
                result["literary_form"] = ["Nonfiction"]
            else:
                result["literary_form"] = ["Fiction"]

        # subject_people → canonical names
        for raw in work.get("subject_people", []):
            key = normalize(raw)
            canonical = self.people_overrides.get(key, raw.strip())
            if canonical not in result["people"]:
                result["people"].append(canonical)

        # subject_places → canonical places
        for raw in work.get("subject_places", []):
            key = normalize(raw)
            canonical = self.places_overrides.get(key, raw.strip())
            if canonical not in result["places"]:
                result["places"].append(canonical)

        # subject_times → pass through (times are free-form)
        for raw in work.get("subject_times", []):
            cleaned = raw.strip()
            if cleaned and cleaned not in result["times"]:
                result["times"].append(cleaned)

        return result


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_work(work_id: str) -> dict:
    """Fetch a work JSON from Open Library."""
    work_id = work_id.replace("/works/", "").strip()
    if not work_id.endswith(".json"):
        url = OL_WORK_URL.format(work_id=work_id)
    else:
        url = f"https://openlibrary.org/works/{work_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def load_work_file(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_result(work_id: str, result: dict):
    print(f"\n=== {work_id} ===")
    for key, values in result.items():
        if values:
            print(f"  {key}:")
            for v in values:
                print(f"    - {v}")


def write_result(work_id: str, result: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir) / f"{work_id}.json"
    with open(out_path, "w") as f:
        json.dump({"work_id": work_id, **result}, f, indent=2)
    print(f"Written: {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migrate OL legacy subjects to canonical typed tags."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--work", help="OL Work ID (e.g. OL82563W)")
    group.add_argument("--file", help="Path to a local work JSON file")
    group.add_argument("--batch", help="Path to newline-delimited OL Work IDs file")

    parser.add_argument("--output", default="output", help="Output directory for batch mode")
    parser.add_argument("--dry-run", action="store_true", help="Print results, don't write files")

    args = parser.parse_args()
    classifier = SubjectClassifier()

    if args.work:
        print(f"Fetching {args.work}...")
        work = fetch_work(args.work)
        result = classifier.classify_work(work)
        if args.dry_run:
            print_result(args.work, result)
        else:
            write_result(args.work, result, args.output)

    elif args.file:
        work = load_work_file(args.file)
        work_id = work.get("key", Path(args.file).stem).split("/")[-1]
        result = classifier.classify_work(work)
        if args.dry_run:
            print_result(work_id, result)
        else:
            write_result(work_id, result, args.output)

    elif args.batch:
        with open(args.batch) as f:
            work_ids = [line.strip() for line in f if line.strip()]

        for work_id in work_ids:
            try:
                print(f"Processing {work_id}...")
                work = fetch_work(work_id)
                result = classifier.classify_work(work)
                if args.dry_run:
                    print_result(work_id, result)
                else:
                    write_result(work_id, result, args.output)
            except Exception as e:
                print(f"ERROR processing {work_id}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
