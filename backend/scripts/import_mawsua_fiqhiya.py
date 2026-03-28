#!/usr/bin/env python3
"""
Import the Kuwaiti Fiqh Encyclopedia (الموسوعة الفقهية الكويتية) via the Turath API.

The encyclopedia (45 volumes, ~32000 pages) is available through turath.io's public API:
  - Book info + TOC:  https://api.turath.io/book?id=11430&include=indexes&ver=3
  - Full book JSON:   https://files.turath.io/books/11430.json
  - Single page:      https://api.turath.io/page?book_id=11430&pg={page}&ver=3

The full book JSON (~50-100MB) contains all pages in one file. For large books
we can also fetch page-by-page via the /page endpoint.

Strategy:
  1. Try downloading the full book JSON from files.turath.io (fastest)
  2. Fallback: fetch book info for TOC, then page-by-page via the API
  3. Parse each page's HTML content, extract text and headings
  4. Tag/filter content mentioning Maliki positions
  5. Save structured JSON

Output: data/mawsua_fiqhiya.json
"""

import asyncio
import json
import logging
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# Turath API endpoints
API_BASE = "https://api.turath.io"
FILES_BASE = "https://files.turath.io/books"
BOOK_ID = 11430
API_VERSION = 3

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "mawsua_fiqhiya.json"

# Rate limiting for page-by-page mode
REQUEST_DELAY = 0.5  # Turath API is public and fast, but be respectful
MAX_RETRIES = 3
RETRY_DELAY = 3

# Maliki keywords for filtering
MALIKI_KEYWORDS = [
    "المالكية",
    "المالكيّة",
    "المالكيَّة",
    "مالك",
    "مذهب مالك",
    "عند المالكية",
    "قال المالكية",
    "ذهب المالكية",
    "مذهب المالكيَّة",
    "المدونة",       # Key Maliki reference text
    "ابن القاسم",    # Major Maliki scholar
    "خليل",          # Mukhtasar Khalil
    "الموطأ",        # Malik's Muwatta
]

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "MawsuaFiqhMaliki/1.0 (research project)",
}


class HTMLTextExtractor(HTMLParser):
    """Simple HTML to text converter that also extracts headings."""

    def __init__(self):
        super().__init__()
        self.text_parts: list[str] = []
        self.headings: list[str] = []
        self._in_heading = False
        self._current_heading = ""
        self._heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "b", "strong"}
        self._current_tag = ""
        self._current_classes: list[str] = []

    def handle_starttag(self, tag, attrs):
        self._current_tag = tag
        attr_dict = dict(attrs)
        self._current_classes = attr_dict.get("class", "").split()
        # Detect headings by tag or by Shamela CSS classes (c4, c5)
        if tag in self._heading_tags or any(c in self._current_classes for c in ("c4", "c5")):
            self._in_heading = True
            self._current_heading = ""

    def handle_endtag(self, tag):
        if tag in self._heading_tags or tag == "span":
            if self._in_heading and self._current_heading.strip():
                self.headings.append(self._current_heading.strip())
            self._in_heading = False
        if tag in ("p", "br", "div"):
            self.text_parts.append("\n")

    def handle_data(self, data):
        cleaned = data.strip()
        if cleaned:
            self.text_parts.append(cleaned)
            if self._in_heading:
                self._current_heading += cleaned

    def get_text(self) -> str:
        return " ".join(self.text_parts).strip()

    def get_headings(self) -> list[str]:
        return self.headings


def parse_html_content(html: str) -> dict:
    """Parse HTML content from a Turath page into plain text + headings."""
    extractor = HTMLTextExtractor()
    extractor.feed(html)
    return {
        "text": extractor.get_text(),
        "headings": extractor.get_headings(),
    }


def detect_maliki_content(text: str) -> dict:
    """Analyze text for Maliki fiqh mentions and extract relevant excerpts."""
    keywords_found = []
    excerpts = []

    for kw in MALIKI_KEYWORDS:
        if kw in text:
            keywords_found.append(kw)
            for match in re.finditer(re.escape(kw), text):
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                excerpt = text[start:end].strip()
                excerpts.append(excerpt)

    return {
        "mentions_maliki": len(keywords_found) > 0,
        "maliki_keywords_found": list(set(keywords_found)),
        "maliki_excerpts": excerpts[:10],
    }


def identify_topic(headings: list[str]) -> str:
    """Identify the fiqh topic from headings."""
    topic_patterns = [
        r"(كتاب\s+\S+)",
        r"(باب\s+\S+(?:\s+\S+)?)",
        r"(فصل\s+في\s+\S+(?:\s+\S+)?)",
    ]
    for heading in headings:
        for pattern in topic_patterns:
            match = re.search(pattern, heading)
            if match:
                return match.group(1)
    return headings[0] if headings else ""


async def fetch_json(
    client: httpx.AsyncClient, url: str, params: Optional[dict] = None
) -> Optional[dict]:
    """Fetch JSON from API with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = await client.get(
                url, params=params, headers=HEADERS,
                follow_redirects=True, timeout=60,
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait = RETRY_DELAY * (attempt + 2)
                log.warning("Rate limited, waiting %ds...", wait)
                await asyncio.sleep(wait)
            elif resp.status_code == 404:
                return None
            else:
                log.warning("HTTP %d for %s (attempt %d)", resp.status_code, url, attempt + 1)
                await asyncio.sleep(RETRY_DELAY)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            log.warning("Connection error: %s (attempt %d)", e, attempt + 1)
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    log.error("Failed to fetch %s after %d retries", url, MAX_RETRIES)
    return None


async def fetch_book_info(client: httpx.AsyncClient) -> Optional[dict]:
    """Fetch book metadata and TOC indexes from the API."""
    log.info("Fetching book info from %s/book", API_BASE)
    return await fetch_json(client, f"{API_BASE}/book", {
        "id": BOOK_ID,
        "include": "indexes",
        "ver": API_VERSION,
    })


async def fetch_full_book(client: httpx.AsyncClient) -> Optional[dict]:
    """Download the full book JSON file (can be large, 50-100MB)."""
    url = f"{FILES_BASE}/{BOOK_ID}.json"
    log.info("Downloading full book JSON from %s (this may take a while)...", url)
    try:
        resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=300)
        if resp.status_code == 200:
            log.info("Downloaded full book JSON (%d bytes)", len(resp.content))
            return resp.json()
        else:
            log.warning("Failed to download full book: HTTP %d", resp.status_code)
            return None
    except Exception as e:
        log.warning("Error downloading full book: %s", e)
        return None


async def fetch_page(client: httpx.AsyncClient, page_num: int) -> Optional[dict]:
    """Fetch a single page via the API."""
    return await fetch_json(client, f"{API_BASE}/page", {
        "book_id": BOOK_ID,
        "pg": page_num,
        "ver": API_VERSION,
    })


def process_book_data(book_data: dict) -> list[dict]:
    """Process the full book JSON into structured entries.

    The book JSON has a 'pages' array where each item has:
      - 'text': HTML content of the page
      - 'page': page number (or index)
      - 'vol': volume number
      - 'part': part number
    And an 'indexes' array with TOC entries mapping to pages.
    """
    pages = book_data.get("pages", [])
    indexes = book_data.get("indexes", [])

    # Build a page-to-heading map from indexes
    page_headings = {}
    for idx_entry in indexes:
        pg = idx_entry.get("page", idx_entry.get("pg"))
        title = idx_entry.get("title", idx_entry.get("tit", ""))
        level = idx_entry.get("level", idx_entry.get("lvl", 0))
        if pg is not None and title:
            if pg not in page_headings:
                page_headings[pg] = []
            page_headings[pg].append({"title": title, "level": level})

    entries = []
    for page in pages:
        html_text = page.get("text", "")
        if not html_text or len(html_text) < 20:
            continue

        page_num = page.get("page", page.get("pg", 0))
        vol = page.get("vol", page.get("part", 0))

        # Parse HTML content
        parsed = parse_html_content(html_text)
        text = parsed["text"]
        headings = parsed["headings"]

        # Add TOC headings if available
        toc_headings = page_headings.get(page_num, [])
        all_headings = [h["title"] for h in toc_headings] + headings

        if not text or len(text) < 20:
            continue

        # Analyze for Maliki content
        maliki_info = detect_maliki_content(text)

        entry = {
            "page": page_num,
            "volume": vol,
            "topic": identify_topic(all_headings),
            "headings": all_headings,
            "text": text,
            "source_url": f"https://app.turath.io/book/{BOOK_ID}?page={page_num}",
            **maliki_info,
        }
        entries.append(entry)

    return entries


async def process_page_by_page(
    client: httpx.AsyncClient,
    book_info: dict,
    start_from: int = 1,
    limit: Optional[int] = None,
) -> list[dict]:
    """Fetch and process pages one by one via the API (slower but uses less memory)."""
    # Extract indexes/TOC from book info
    indexes = book_info.get("indexes", {})
    headings = indexes.get("headings", [])
    volume_bounds = indexes.get("volume_bounds", {})

    max_page = max((h.get("page", 0) for h in headings), default=0)
    if max_page == 0:
        max_page = 31949  # Known total for this book

    log.info("Book has ~%d pages, %d TOC headings, starting from page %d", max_page, len(headings), start_from)

    # Build page list from TOC headings (fetch pages that have indexed content)
    toc_pages = sorted(set(
        h.get("page", 0) for h in headings
        if (h.get("page", 0) or 0) >= start_from
    ))

    if not toc_pages:
        # Fallback: generate sequential page numbers
        toc_pages = list(range(start_from, max_page + 1))

    if limit:
        toc_pages = toc_pages[:limit]

    total = len(toc_pages)
    entries = []

    for i, pg in enumerate(toc_pages):
        if i % 100 == 0:
            log.info("[%d/%d] Fetching page %d...", i + 1, total, pg)

        page_data = await fetch_page(client, pg)
        if not page_data:
            continue

        text_html = page_data.get("text", "")
        meta = page_data.get("meta", {})
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {}

        if not text_html or len(text_html) < 20:
            continue

        parsed = parse_html_content(text_html)
        text = parsed["text"]
        headings = parsed["headings"]

        # Add meta headings
        meta_headings = meta.get("headings", []) if isinstance(meta, dict) else []
        all_headings = meta_headings + headings

        vol = meta.get("vol", 0) if isinstance(meta, dict) else 0

        if not text or len(text) < 20:
            continue

        maliki_info = detect_maliki_content(text)

        entry = {
            "page": pg,
            "volume": vol,
            "topic": identify_topic(all_headings),
            "headings": all_headings,
            "text": text,
            "source_url": f"https://app.turath.io/book/{BOOK_ID}?page={pg}",
            **maliki_info,
        }
        entries.append(entry)

        if (i + 1) % 100 == 0:
            maliki_count = sum(1 for e in entries if e["mentions_maliki"])
            log.info("  Progress: %d entries, %d Maliki-relevant", len(entries), maliki_count)

        await asyncio.sleep(REQUEST_DELAY)

    return entries


def save_results(entries: list[dict], output_file: Path):
    """Save entries to JSON with Maliki-only subset."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    maliki_entries = [e for e in entries if e.get("mentions_maliki")]

    result = {
        "source": "turath.io",
        "source_name": "الموسوعة الفقهية الكويتية",
        "book_id": BOOK_ID,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_pages": len(entries),
        "maliki_relevant": len(maliki_entries),
        "entries": entries,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    log.info(
        "Saved %d pages (%d Maliki-relevant) to %s",
        len(entries), len(maliki_entries), output_file,
    )

    # Save Maliki-only subset
    maliki_file = output_file.with_name("mawsua_fiqhiya_maliki.json")
    maliki_result = {
        "source": "turath.io",
        "source_name": "الموسوعة الفقهية الكويتية (المالكية فقط)",
        "book_id": BOOK_ID,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_pages": len(maliki_entries),
        "entries": maliki_entries,
    }
    with open(maliki_file, "w", encoding="utf-8") as f:
        json.dump(maliki_result, f, ensure_ascii=False, indent=2)

    log.info("Saved Maliki-only subset (%d pages) to %s", len(maliki_entries), maliki_file)


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Import Kuwaiti Fiqh Encyclopedia from turath.io API"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "pages", "info"],
        default="full",
        help=(
            "full: download entire book JSON at once (fast, uses ~100MB RAM); "
            "pages: fetch page-by-page (slow, low memory); "
            "info: only fetch book info and TOC"
        ),
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=1,
        help="Start from page number (for page-by-page mode)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of pages to process",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help=f"Output JSON file (default: {OUTPUT_FILE})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last page in existing output file (pages mode only)",
    )
    args = parser.parse_args()

    output_file = Path(args.output)
    start_from = args.start_from

    # Resume support
    existing_entries = []
    if args.resume and output_file.exists():
        with open(output_file, encoding="utf-8") as f:
            existing = json.load(f)
            existing_entries = existing.get("entries", [])
            if existing_entries:
                last_page = max(e["page"] for e in existing_entries)
                start_from = last_page + 1
                log.info(
                    "Resuming from page %d (%d existing entries)",
                    start_from, len(existing_entries),
                )

    async with httpx.AsyncClient() as client:
        if args.mode == "info":
            # Just fetch and display book info
            info = await fetch_book_info(client)
            if info:
                info_file = output_file.with_name("mawsua_fiqhiya_info.json")
                info_file.parent.mkdir(parents=True, exist_ok=True)
                with open(info_file, "w", encoding="utf-8") as f:
                    json.dump(info, f, ensure_ascii=False, indent=2)
                log.info("Saved book info to %s", info_file)

                indexes = info.get("indexes", {})
                headings = indexes.get("headings", [])
                log.info("Book has %d TOC headings", len(headings))
                for h in headings[:20]:
                    log.info("  - Page %s [L%s]: %s", h.get("page"), h.get("level"), h.get("title", ""))
            return

        if args.mode == "full":
            # Download entire book at once
            book_data = await fetch_full_book(client)
            if book_data:
                entries = process_book_data(book_data)
                if args.limit:
                    entries = entries[:args.limit]
                save_results(entries, output_file)
                log.info("Done! Processed %d pages from full book download", len(entries))
                return
            else:
                log.warning("Full book download failed, falling back to page-by-page mode")

        # Page-by-page mode (or fallback from full mode)
        info = await fetch_book_info(client)
        if not info:
            log.error("Failed to fetch book info, exiting")
            return

        # Save TOC
        indexes = info.get("indexes", {})
        headings = indexes.get("headings", [])
        toc_file = output_file.with_name("mawsua_fiqhiya_toc.json")
        toc_file.parent.mkdir(parents=True, exist_ok=True)
        with open(toc_file, "w", encoding="utf-8") as f:
            json.dump({"headings": headings, "total": len(headings)}, f, ensure_ascii=False, indent=2)
        log.info("Saved TOC (%d headings) to %s", len(headings), toc_file)

        new_entries = await process_page_by_page(
            client, info, start_from=start_from, limit=args.limit
        )

        all_entries = existing_entries + new_entries
        save_results(all_entries, output_file)
        log.info("Done! Total: %d pages processed", len(all_entries))


if __name__ == "__main__":
    asyncio.run(main())
