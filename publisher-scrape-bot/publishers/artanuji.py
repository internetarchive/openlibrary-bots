from __future__ import annotations

import html as ihtml
import re
from typing import Optional
from urllib.parse import urljoin

from publishers.base import ParsedBook


class ArtanujiParser:
    name = "artanuji"
    base_url = "https://www.artanuji.ge/book_ge.php?id={id}"

    _STOP_DESCRIPTION_LABELS = (
        "ინგლისურიდან თარგმნა",
        "რუსულიდან თარგმნა",
        "გერმანულიდან თარგმნა",
        "ფრანგულიდან თარგმნა",
        "გაზიარება",
        "ავტორის წიგნები",
        "ამავე კატეგორიაში",
        "ყიდვა",
    )

    def page_url(self, item_id: int) -> str:
        return self.base_url.format(id=item_id)

    def parse(self, html: str, item_id: int) -> Optional[ParsedBook]:
        if "book_ge.php" not in html or "ISBN" not in html:
            return None

        title = self._extract_title(html)
        author = self._extract_author(html)
        isbn_raw = self._extract_field(html, "ISBN")
        publish_date = self._extract_field(html, "გამოცემის თარიღი") or ""
        pages_raw = self._extract_field(html, "გვერდები")
        subject = self._extract_field(html, "კატეგორია")
        description = self._extract_description(html)
        cover_url = self._extract_cover_url(html, item_id)

        if not title or not author or not isbn_raw:
            return None

        isbn_10, isbn_13 = self._classify_isbn(isbn_raw)
        if not (isbn_10 or isbn_13):
            return None

        pages = None
        if pages_raw:
            page_match = re.search(r"\d+", pages_raw)
            pages = int(page_match.group(0)) if page_match else None

        year_match = re.search(r"\b(1[89]\d{2}|20\d{2}|21\d{2})\b", publish_date)
        publish_year = year_match.group(1) if year_match else publish_date.strip()

        return ParsedBook(
            source=self.name,
            source_id=item_id,
            source_url=self.page_url(item_id),
            title=title,
            author=author,
            publisher="არტანუჯი",
            publish_date=publish_year,
            isbn_13=isbn_13,
            isbn_10=isbn_10,
            number_of_pages=pages,
            description=description,
            subject=subject,
            cover_url=cover_url,
        )

    def _extract_title(self, html: str) -> Optional[str]:
        match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return self._clean_text(match.group(1))

    def _extract_author(self, html: str) -> Optional[str]:
        # Most pages place author name in <h4> under the title block.
        match = re.search(r"<h4[^>]*>(.*?)</h4>", html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return self._clean_text(match.group(1))

    def _extract_field(self, html: str, label: str) -> Optional[str]:
        prefix = f"{label}:"
        for line in self._to_text_lines(html):
            if line.startswith(prefix):
                return self._clean_text(line[len(prefix) :])
        return None

    def _extract_description(self, html: str) -> Optional[str]:
        text = self._to_text_lines(html)
        if not text:
            return None

        start_idx = None
        for idx, line in enumerate(text):
            if line.startswith("ყიდვა"):
                start_idx = idx + 1
                break
        if start_idx is None:
            start_idx = 0

        out = []
        for line in text[start_idx:]:
            if any(line.startswith(stop) for stop in self._STOP_DESCRIPTION_LABELS):
                break
            if len(line) >= 35:
                out.append(line)
        if not out:
            return None
        return " ".join(out).strip()

    def _extract_cover_url(self, html: str, item_id: int) -> Optional[str]:
        og = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )
        if og:
            return urljoin(self.page_url(item_id), self._clean_text(og.group(1)))

        # Fallback to the first image on the page.
        image = re.search(
            r'<img[^>]+src=["\']([^"\']+)["\']',
            html,
            flags=re.IGNORECASE,
        )
        if image:
            return urljoin(self.page_url(item_id), self._clean_text(image.group(1)))
        return None

    @staticmethod
    def _classify_isbn(raw: str) -> tuple[Optional[str], Optional[str]]:
        digits = re.sub(r"[^0-9Xx]", "", raw).upper()
        if len(digits) == 13:
            return None, digits
        if len(digits) == 10:
            return digits, None
        # Some pages include both ISBN-10/13 separated by punctuation.
        isbn_13 = None
        isbn_10 = None
        for token in re.findall(r"[0-9Xx-]{10,20}", raw):
            value = re.sub(r"[^0-9Xx]", "", token).upper()
            if len(value) == 13 and not isbn_13:
                isbn_13 = value
            elif len(value) == 10 and not isbn_10:
                isbn_10 = value
        return isbn_10, isbn_13

    @staticmethod
    def _clean_text(value: str) -> str:
        value = re.sub(r"<[^>]+>", " ", value)
        value = ihtml.unescape(value)
        value = re.sub(r"\s+", " ", value)
        return value.strip()

    def _to_text_lines(self, html: str) -> list[str]:
        html = re.sub(
            r"<(script|style)\b[^>]*>.*?</\1>",
            " ",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        html = re.sub(r"</(p|div|h1|h2|h3|h4|li)>", "\n", html, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", html)
        text = ihtml.unescape(text)
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        return [line for line in lines if line]
