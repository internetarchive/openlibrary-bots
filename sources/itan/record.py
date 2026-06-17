"""
record.py
~~~~~~~~~

DataProviderRecord for ITAN Global Publishing.

The ITAN catalog is already structured close to the OL import format, so the
transformation is mostly cleanup:

  - Strip leading/trailing whitespace from subjects (several have " Subject")
  - Filter invalid isbn_13 values — the catalog uses "0" as a placeholder
  - Drop ebook_access, which is not in the OL import schema

Source: https://github.com/ITANigp/itan-ebook-backend
Issue:  https://github.com/internetarchive/openlibrary/issues/12091
"""

from __future__ import annotations

import re
from typing import List, Optional

from olclient.imports import DataProviderRecord, OLAuthor, OLImportRecord

# OL import schema pattern for isbn_13
_ISBN13_RE = re.compile(r"^([0-9][- ]*){13}$")

# Scraped from https://itan.app/bookstore?search=<BOO_ID>.
# Stored as the itan_technologies identifier so OL builds a direct deep link via
# url template: https://itan.app/bookstore/@@@
_SLUG_MAP = {
    "BOO1017": "book-clouds-and-mercy-BOO1017",
    "BOO1019": "afrocentric-science-fiction-fantasy-titan-race-edentu-oroso-boo1019",
    "BOO1021": "africa-children-books-amanda-the-smart-safety-girl-elizabeth-uwalaka-boo1021",
    "BOO1022": "african-children-books-the-king-s-daughter-mopelola-adeniyi-boo1022",
    "BOO1023": "african-romance-travails-of-eve-s-daughters-mopelola-adeniyi-boo1023",
    "BOO1024": "african-children-books-kubi-the-lion-prince-mopelola-adeniyi-boo1024",
    "BOO1025": "african-children-books-the-lying-bird-mopelola-adeniyi-boo1025",
    "BOO1026": "african-literature-fiction-dairy-of-a-whiz-kid-eny-awevia-boo1026",
    "BOO1027": "african-literature-fiction-in-bed-with-her-guy-mopelola-adeniyi-boo1027",
    "BOO1028": "african-literature-fiction-juliet-matthew-simpa-boo1028",
    "BOO1029": "african-religious-fiction-soul-reapers-mopelola-adeniyi-boo1029",
    "BOO1030": "african-religious-fiction-a-rough-diamond-mopelola-adeniyi-boo1030",
    "BOO1031": "african-children-books-african-tales-for-modern-times-mopelola-adeniyi-boo1031",
    "BOO1032": "african-children-books-talking-doll-mopelola-adeniyi-boo1032",
    "BOO1033": "african-children-books-african-tales-for-modern-times-vol-2-mopelola-adeniyi-boo1033",
    "BOO1034": "african-children-books-asoro-s-visit-to-the-dentist-mopelola-adeniyi-boo1034",
    "BOO1035": "african-literature-fiction-we-belong-to-nobody-edentu-oroso-boo1035",
    "BOO1037": "african-literature-fiction-revamping-me-mopelola-adeniyi-boo1037",
    "BOO1038": "african-literature-fiction-enemies-within-me-anthony-uyaebo-boo1038",
    "BOO1039": "african-romance-heart-webs-mopelola-adeniyi-boo1039",
    "BOO1040": "african-literature-fiction-the-grief-gallery-john-chizoba-vincent-boo1040",
    "BOO1041": "african-literature-fiction-how-we-chose-who-dies-igoche-john-igoche-boo1041",
    "BOO1042": "african-science-fiction-fantasy-something-strange-elvis-chidiebube-boo1042",
    "BOO1043": "african-science-fiction-fantasy-the-mask-of-oshun-ode-sylvia-boo1043",
    "BOO1044": "african-literature-fiction-the-quiet-general-other-stories-matthew-simpa-boo1044",
    "BOO1045": "african-mystery-thriller-and-suspense-nyanya14-amaechi-praise-boo1045",
    "BOO1046": "african-religious-fiction-on-eagle-s-wings-emmanuel-olaoluwa-boo1046",
    "BOO1047": "african-religious-fiction-the-wind-and-the-fire-emmanuel-olaoluwa-boo1047",
    "BOO1048": "african-religious-fiction-the-throne-and-the-city-emmanuel-olaoluwa-boo1048",
    "BOO1049": "african-mystery-thriller-and-suspense-the-first-whisper-chimdinma-anagor-boo1049",
    "BOO1050": "african-mystery-thriller-and-suspense-the-fairy-s-magic-wand-joshua-okoromodeke-boo1050",
    "BOO1051": "african-mystery-thriller-and-suspense-the-field-of-gold-joshua-okoromodeke-boo1051",
    "BOO1053": "african-mystery-thriller-and-suspense-prototype-lyra-jennifer-okafor-boo1053",
    "BOO1054": "african-literature-fiction-aminu-s-diary-usman-inuwa-boo1054",
    "BOO1055": "african-religious-fiction-marked-mopelola-adeniyi-boo1055",
    "BOO1056": "african-mystery-thriller-and-suspense-the-mambila-mirage-sa-idu-sulaiman-boo1056",
    "BOO1057": "african-mystery-thriller-and-suspense-veins-of-deception-amina-sa-id-sulaiman-boo1057",
    "BOO1058": "african-literature-fiction-my-mother-s-tears-chimbuikem-obiajunwa-boo1058",
    "BOO1059": "african-literature-fiction-echoes-behind-the-wall-ahmad-abubakar-mustafa-boo1059",
    "BOO1065": "african-children-books-it-is-in-you-mopelola-adeniyi-boo1065",
    "BOO1066": "african-children-books-the-wise-princess-mopelola-adeniyi-boo1066",
    "BOO1067": "african-children-books-financial-savvy-kids-mopelola-adeniyi-boo1067",
    "BOO1068": "african-romance-better-than-chocolate-and-other-stories-buka-chiro-kafor-boo1068",
    "BOO1073": "african-literature-fiction-emancipation-atamgbo-raymond-otogwung-boo1073",
    "BOO1077": "african-romance-love-in-lagos-s-dirt-prince-atanda-boo1077",
    "BOO1079": "african-children-books-the-activity-kindergarten-of-wonderful-stories-ahmad-abubakar-mustafa-boo1079",
    "BOO1081": "african-science-fiction-fantasy-the-cube-that-birthed-gods-chukwuebuka-akadile-boo1081",
    "BOO1085": "african-mystery-thriller-and-suspense-two-fronts-buka-chiro-kafor-boo1085",
    "BOO1086": "african-literature-fiction-lifted-by-forex-aondaver-james-yange-boo1086",
    "BOO1088": "african-literature-fiction-the-republic-of-wazimba-isaac-ogbadu-achimugu-boo1088",
    "BOO1089": "african-literature-fiction-a-future-that-remembers-isaac-ogbadu-achimugu-boo1089",
    "BOO1090": "african-science-fiction-fantasy-still-ours-lily-baby-girl-boo1090",
    "BOO1091": "african-romance-the-road-to-uncertainty-obinna-godswill-chinegwu-boo1091",
    "BOO1092": "african-mystery-thriller-and-suspense-the-killer-and-the-saint-obinna-godswill-chinegwu-boo1092",
    "BOO1093": "african-romance-home-calling-obinna-godswill-chinegwu-boo1093",
    "BOO1095": "african-religious-fiction-the-journey-beyond-life-death-eternity-james-yange-boo1095",
    "BOO1097": "african-literature-fiction-the-iron-fist-obinna-godswill-chinegwu-boo1097",
    "BOO1098": "african-literature-fiction-the-chief-who-walked-back-isaac-achimugu-boo1098",
    "BOO1099": "african-romance-mrs-senator-carissa-chiagozie-boo1099",
    "BOO1100": "african-literature-fiction-the-beauty-of-scars-oluwadamilola-loise-anjorin-boo1100",
    "BOO1109": "african-literature-fiction-shadows-of-the-continent-urunna-ikemefuna-boo1109",
    "BOO1110": "african-romance-sworn-strangers-urunna-ikemefuna-boo1110",
    "BOO1111": "african-literature-fiction-born-different-yetunde-anyanwun-boo1111",
    "BOO1112": "african-mystery-thriller-and-suspense-dancing-with-the-enemy-obinna-godswill-chinegwu-boo1112",
    "BOO1113": "african-science-fiction-fantasy-kanran-earth-scavengers-prince-atanda-boo1113",
    "BOO1116": "african-mystery-thriller-and-suspense-ember-s-and-halo-s-david-uchenna-ejiegbu-boo1116",
    "BOO1117": "african-literature-fiction-the-tortoise-that-carried-iron-isaac-achimugu-boo1117",
}


class ITANRecord(DataProviderRecord):
    """One record from the ITAN catalog JSONL file.

    Field names intentionally match the OL import schema because ITAN pre-formats
    their data that way. extra='allow' (inherited) absorbs ebook_access and any
    other ITAN-specific keys without raising.
    """

    title: str
    authors: List[dict]
    publishers: List[str]
    publish_date: str
    source_records: List[str]
    identifiers: Optional[dict] = None
    languages: Optional[List[str]] = None
    subjects: Optional[List[str]] = None
    subtitle: Optional[str] = None
    number_of_pages: Optional[int] = None
    notes: Optional[str] = None
    isbn_13: Optional[List[str]] = None
    isbn_10: Optional[List[str]] = None
    contributions: Optional[List[str]] = None

    # ebook_access and any future ITAN-specific fields are absorbed by extra='allow'

    def to_ol_import(self) -> Optional[OLImportRecord]:
        if not self.title or not self.authors:
            return None

        authors = [
            OLAuthor(name=a["name"]) for a in self.authors if a.get("name", "").strip()
        ]
        if not authors:
            return None

        subjects = (
            [s.strip() for s in self.subjects if s.strip()] if self.subjects else None
        )

        # Filter malformed ISBNs — ITAN uses "0" and "978" as placeholders
        isbn_13 = (
            [v for v in self.isbn_13 if _ISBN13_RE.match(v)] if self.isbn_13 else None
        ) or None

        isbn_10 = (
            [v for v in self.isbn_10 if v and v != "0"] if self.isbn_10 else None
        ) or None

        # Use the bookstore slug as the identifier value so OL builds a direct deep link.
        # source_records keeps the stable BOO ID for deduplication.
        boo_id = next(
            (sr.split(":", 1)[1] for sr in self.source_records if ":" in sr), None
        )
        slug = _SLUG_MAP.get(boo_id) if boo_id else None
        identifiers = {"itan_technologies": [slug or boo_id]} if (slug or boo_id) else self.identifiers

        return OLImportRecord(
            title=self.title,
            source_records=self.source_records,
            authors=authors,
            publishers=self.publishers,
            publish_date=self.publish_date,
            subtitle=self.subtitle,
            number_of_pages=self.number_of_pages,
            notes=self.notes,
            languages=self.languages,
            subjects=subjects or None,
            isbn_13=isbn_13,
            isbn_10=isbn_10,
            identifiers=identifiers,
            contributions=self.contributions,
        )
