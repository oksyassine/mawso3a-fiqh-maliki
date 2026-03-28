#!/usr/bin/env python3
"""
Shamela.ws Book Importer
=========================
Downloads full text of books from shamela.ws (المكتبة الشاملة) and saves
them as structured JSON ready for DB import.

Usage:
    # Download a single book by Shamela ID
    python import_shamela.py 587

    # Download a book with custom output directory
    python import_shamela.py 587 --output ./data/books

    # Download all mapped Maliki books
    python import_shamela.py --all-maliki

    # Resume a previously interrupted download
    python import_shamela.py 587 --resume

    # List all mapped Maliki books
    python import_shamela.py --list

Requirements:
    pip install httpx beautifulsoup4 lxml tqdm tenacity
"""

import argparse
import json
import logging
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup, Tag
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("shamela")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SHAMELA_BASE = "https://shamela.ws"
BOOK_URL = f"{SHAMELA_BASE}/book/{{book_id}}"
PAGE_URL = f"{SHAMELA_BASE}/book/{{book_id}}/{{page}}"

# Respectful rate-limiting
REQUEST_DELAY = 1.0  # seconds between requests
REQUEST_TIMEOUT = 30.0  # seconds

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en;q=0.9",
}

# URL pattern: /book/{id}/{page}#{paragraph}
BOOK_URL_RE = re.compile(
    r"(?:https?://)?shamela\.ws/book/(?P<book_id>\d+)/?(?P<page>\d+)?(?:#(?P<para>p\d+))?"
)

# ---------------------------------------------------------------------------
# Maliki Fiqh Books — Shamela IDs
# ---------------------------------------------------------------------------
# Verified via shamela.ws search. IDs may change if Shamela re-indexes.
MALIKI_BOOKS: dict[int, dict[str, str]] = {
    # ===== Primary Sources (أمهات المذهب) =====
    1699: {
        "title": "موطأ مالك",
        "title_ar": "موطأ الإمام مالك - رواية يحيى بن يحيى - ت عبد الباقي",
        "author": "مالك بن أنس",
        "category": "حديث / أصول",
    },
    587: {
        "title": "المدونة الكبرى",
        "title_ar": "المدونة",
        "author": "مالك بن أنس (رواية سحنون عن ابن القاسم)",
        "category": "فقه",
    },
    # ===== Core Mutun (متون) =====
    11373: {
        "title": "الرسالة",
        "title_ar": "الرسالة لابن أبي زيد القيرواني",
        "author": "ابن أبي زيد القيرواني",
        "category": "فقه / متن",
    },
    11355: {
        "title": "مختصر خليل",
        "title_ar": "مختصر العلامة خليل",
        "author": "خليل بن إسحاق الجندي",
        "category": "فقه / متن",
    },
    # ===== Major Commentaries (شروح) =====
    21604: {
        "title": "الشرح الكبير وحاشية الدسوقي",
        "title_ar": "الشرح الكبير للشيخ الدردير وحاشية الدسوقي",
        "author": "الدردير / الدسوقي",
        "category": "فقه / شرح",
    },
    569: {
        "title": "مواهب الجليل",
        "title_ar": "مواهب الجليل في شرح مختصر خليل",
        "author": "الحطاب الرُّعيني",
        "category": "فقه / شرح",
    },
    21589: {
        "title": "الفواكه الدواني",
        "title_ar": "الفواكه الدواني على رسالة ابن أبي زيد القيرواني",
        "author": "أحمد بن غنيم النفراوي",
        "category": "فقه / شرح",
    },
    21597: {
        "title": "حاشية العدوي على كفاية الطالب الرباني",
        "title_ar": "حاشية العدوي على كفاية الطالب الرباني",
        "author": "علي الصعيدي العدوي",
        "category": "فقه / حاشية",
    },
    21607: {
        "title": "بلغة السالك (حاشية الصاوي على الشرح الصغير)",
        "title_ar": "حاشية الصاوي على الشرح الصغير = بلغة السالك لأقرب المسالك",
        "author": "الصاوي",
        "category": "فقه / حاشية",
    },
    14297: {
        "title": "شرح الزرقاني على مختصر خليل",
        "title_ar": "شرح الزرقاني على مختصر خليل وحاشية البناني",
        "author": "الزرقاني / البناني",
        "category": "فقه / شرح",
    },
    # ===== More Shuruh on Mukhtasar Khalil =====
    21611: {
        "title": "التاج والإكليل",
        "title_ar": "التاج والإكليل لمختصر خليل",
        "author": "المواق",
        "category": "فقه / شرح",
    },
    91: {
        "title": "شرح الخرشي وحاشية العدوي",
        "title_ar": "شرح الخرشي على مختصر خليل ومعه حاشية العدوي",
        "author": "الخرشي / العدوي",
        "category": "فقه / شرح",
    },
    21614: {
        "title": "منح الجليل",
        "title_ar": "منح الجليل شرح مختصر خليل",
        "author": "محمد عليش",
        "category": "فقه / شرح",
    },
    14605: {
        "title": "مختصر خليل مع شفاء الغليل",
        "title_ar": "مختصر خليل ومعه شفاء الغليل",
        "author": "خليل بن إسحاق",
        "category": "فقه / متن",
    },
    # ===== Mutoon & Teaching Texts =====
    7262: {
        "title": "التلقين",
        "title_ar": "التلقين في الفقه المالكي",
        "author": "القاضي عبد الوهاب",
        "category": "فقه / متن",
    },
    14590: {
        "title": "التفريع",
        "title_ar": "التفريع في فقه الإمام مالك بن أنس",
        "author": "ابن الجلاب",
        "category": "فقه / متن",
    },
    9548: {
        "title": "متن الأخضري",
        "title_ar": "متن الأخضري في العبادات",
        "author": "الأخضري",
        "category": "فقه / متن",
    },
    37326: {
        "title": "متن العشماوية",
        "title_ar": "متن العشماوية",
        "author": "عبد الباري العشماوي",
        "category": "فقه / متن",
    },
    6532: {
        "title": "تحفة الحكام",
        "title_ar": "تحفة الحكام في نكت العقود والأحكام",
        "author": "ابن عاصم الغرناطي",
        "category": "فقه / نظم",
    },
    # ===== Shuruh on other texts =====
    14249: {
        "title": "شرح ميارة على ابن عاشر",
        "title_ar": "الدر الثمين والمورد المعين - شرح ميارة على ابن عاشر",
        "author": "ميارة المالكي",
        "category": "فقه / شرح",
    },
    121376: {
        "title": "شرح التلقين للمازري",
        "title_ar": "شرح التلقين للمازري",
        "author": "المازري",
        "category": "فقه / شرح",
    },
    1430: {
        "title": "الرسالة - نسخة التتائي",
        "title_ar": "الرسالة لابن أبي زيد القيرواني - نسخة التتائي",
        "author": "ابن أبي زيد القيرواني",
        "category": "فقه / متن",
    },
    18279: {
        "title": "شرح المنهج المنتخب (لامية الزقاق)",
        "title_ar": "شرح المنهج المنتخب إلى قواعد المذهب",
        "author": "المنجور",
        "category": "فقه / قواعد",
    },
    150969: {
        "title": "بلغة السالك - ط الحلبي",
        "title_ar": "حاشية الصاوي على الشرح الصغير - ط الحلبي",
        "author": "الصاوي",
        "category": "فقه / حاشية",
    },
    # ===== القاضي عبد الوهاب =====
    9627: {
        "title": "المعونة",
        "title_ar": "المعونة على مذهب عالم المدينة",
        "author": "القاضي عبد الوهاب",
        "category": "فقه / شرح",
    },
    14245: {
        "title": "الإشراف على نكت مسائل الخلاف",
        "title_ar": "الإشراف على نكت مسائل الخلاف",
        "author": "القاضي عبد الوهاب",
        "category": "فقه / خلاف",
    },
    14467: {
        "title": "عيون المسائل",
        "title_ar": "عيون المسائل للقاضي عبد الوهاب",
        "author": "القاضي عبد الوهاب",
        "category": "فقه",
    },
    18609: {
        "title": "شرح الرسالة للقاضي عبد الوهاب",
        "title_ar": "شرح الرسالة للقاضي عبد الوهاب",
        "author": "القاضي عبد الوهاب",
        "category": "فقه / شرح",
    },
    # ===== شروح الموطأ =====
    551: {
        "title": "شرح الزرقاني على الموطأ",
        "title_ar": "شرح الزرقاني على الموطأ",
        "author": "الزرقاني",
        "category": "حديث / شرح",
    },
    6684: {
        "title": "المنتقى شرح الموطأ",
        "title_ar": "المنتقى شرح الموطأ",
        "author": "الباجي",
        "category": "حديث / شرح",
    },
    1719: {
        "title": "التمهيد - ط المغربية",
        "title_ar": "التمهيد لما في الموطأ من المعاني والأسانيد - ط المغربية",
        "author": "ابن عبد البر",
        "category": "حديث / شرح",
    },
    236: {
        "title": "التمهيد - ت بشار",
        "title_ar": "التمهيد لابن عبد البر - تحقيق بشار عواد",
        "author": "ابن عبد البر",
        "category": "حديث / شرح",
    },
    1722: {
        "title": "الاستذكار",
        "title_ar": "الاستذكار",
        "author": "ابن عبد البر",
        "category": "حديث / شرح",
    },
    # ===== Encyclopedias & Major References =====
    21739: {
        "title": "بداية المجتهد",
        "title_ar": "بداية المجتهد ونهاية المقتصد",
        "author": "ابن رشد الحفيد",
        "category": "فقه مقارن",
    },
    1717: {
        "title": "الذخيرة",
        "title_ar": "الذخيرة",
        "author": "القرافي",
        "category": "فقه / موسوعة",
    },
    21751: {
        "title": "البيان والتحصيل",
        "title_ar": "البيان والتحصيل",
        "author": "ابن رشد الجد",
        "category": "فقه / شرح",
    },
    96257: {
        "title": "النوادر والزيادات",
        "title_ar": "النوادر والزيادات على ما في المدونة من غيرها من الأمهات",
        "author": "ابن أبي زيد القيرواني",
        "category": "فقه / موسوعة",
    },
    8487: {
        "title": "التهذيب في اختصار المدونة",
        "title_ar": "التهذيب في اختصار المدونة",
        "author": "البراذعي",
        "category": "فقه / مختصر",
    },
    # ===== Supplementary =====
    7441: {
        "title": "الثمر الداني",
        "title_ar": "الثمر الداني شرح رسالة ابن أبي زيد القيرواني",
        "author": "صالح الآبي الأزهري",
        "category": "فقه / شرح",
    },
    784: {
        "title": "مواهب الجليل من أدلة خليل",
        "title_ar": "مواهب الجليل من أدلة خليل",
        "author": "محمد بن محمد المغربي",
        "category": "فقه / أدلة",
    },
    17682: {
        "title": "أسهل المدارك",
        "title_ar": "أسهل المدارك شرح إرشاد السالك",
        "author": "الكشناوي",
        "category": "فقه / شرح",
    },
    21688: {
        "title": "فتح العلي المالك",
        "title_ar": "فتح العلي المالك في الفتوى على مذهب الإمام مالك",
        "author": "محمد عليش",
        "category": "فقه / فتاوى",
    },
    150934: {
        "title": "اصطلاح المذهب عند المالكية",
        "title_ar": "اصطلاح المذهب عند المالكية",
        "author": "محمد إبراهيم أحمد علي",
        "category": "فقه / مصطلح",
    },
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclass
class PageData:
    """One page from a Shamela book."""

    page_number: int  # sequential page index on shamela (1-based)
    print_page: str  # printed page number shown on the page
    part: str  # volume/part (جزء)
    text: str  # cleaned Arabic text
    html: str  # original HTML of the content
    chapter_titles: list[str] = field(default_factory=list)  # chapter(s) starting on this page
    footnotes: str = ""  # hamesh / footnotes text


@dataclass
class ChapterEntry:
    """A chapter/section in the book's TOC."""

    title: str
    page: int  # shamela page number
    level: int = 0  # nesting level (0 = top, 1 = sub, ...)


@dataclass
class BookData:
    """Complete downloaded book."""

    book_id: int
    title: str
    author: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chapters: list[ChapterEntry] = field(default_factory=list)
    pages: list[PageData] = field(default_factory=list)
    total_pages: int = 0


# ---------------------------------------------------------------------------
# Shamela Scraper
# ---------------------------------------------------------------------------
class ShamelaScraper:
    """Downloads and parses book content from shamela.ws."""

    def __init__(
        self,
        delay: float = REQUEST_DELAY,
        timeout: float = REQUEST_TIMEOUT,
    ):
        self.delay = delay
        self.timeout = timeout
        self.client = httpx.Client(
            headers=HEADERS,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
            http2=True,
        )

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ----- HTTP with retry ---------------------------------------------------

    @retry(
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.HTTPStatusError, httpx.ConnectError)
        ),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        before_sleep=lambda retry_state: log.warning(
            "Retry %d after error: %s",
            retry_state.attempt_number,
            retry_state.outcome.exception() if retry_state.outcome else "unknown",
        ),
    )
    def _get(self, url: str) -> httpx.Response:
        resp = self.client.get(url)
        # Handle rate-limiting
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "30"))
            log.warning("Rate limited — sleeping %ds", retry_after)
            time.sleep(retry_after)
            raise httpx.HTTPStatusError(
                "Rate limited", request=resp.request, response=resp
            )
        resp.raise_for_status()
        return resp

    def _fetch_page(self, url: str) -> BeautifulSoup:
        time.sleep(self.delay)
        resp = self._get(url)
        return BeautifulSoup(resp.text, "lxml")

    # ----- Book info page ----------------------------------------------------

    def fetch_book_info(self, book_id: int) -> dict[str, Any]:
        """Fetch book metadata from the info/betaka page."""
        url = BOOK_URL.format(book_id=book_id)
        soup = self._fetch_page(url)

        info: dict[str, Any] = {"book_id": book_id, "url": url}

        # Title: <h1><a>...</a></h1>
        h1 = soup.select_one("h1 a")
        info["title"] = h1.get_text(strip=True) if h1 else ""

        # Author: <h1> + <div><a>...</a></div>
        author_el = soup.select_one("h1 + div a")
        info["author"] = author_el.get_text(strip=True) if author_el else ""

        # Betaka (index / card)
        betaka = soup.select_one(".betaka-index")
        if betaka:
            info["betaka_text"] = betaka.get_text("\n", strip=True)

        # Nass content on info page (publisher, pages count, etc.)
        nass = soup.select_one(".nass")
        if nass:
            info["info_text"] = nass.get_text("\n", strip=True)

        return info

    # ----- Single page parsing -----------------------------------------------

    def _parse_page(self, soup: BeautifulSoup, book_id: int) -> dict[str, Any]:
        """Parse a single book page and extract structured data."""
        result: dict[str, Any] = {}

        # Page number (printed)
        page_input = soup.select_one("input#fld_goto_bottom")
        result["print_page"] = page_input["value"] if page_input else ""

        # Part / volume
        part_btn = soup.select_one("#fld_part_top ~ div button")
        result["part"] = part_btn.get_text(strip=True) if part_btn else ""

        # Navigation
        next_link = soup.select_one("input#fld_goto_bottom + a")
        last_link = soup.select_one("input#fld_goto_bottom + a + a")

        if next_link:
            m = BOOK_URL_RE.search(next_link.get("href", ""))
            result["next_page"] = int(m.group("page")) if m and m.group("page") else None
        else:
            result["next_page"] = None

        if last_link:
            m = BOOK_URL_RE.search(last_link.get("href", ""))
            result["last_page"] = int(m.group("page")) if m and m.group("page") else None
        else:
            result["last_page"] = None

        # Content (.nass)
        nass = soup.select_one(".nass")
        if nass:
            # Separate footnotes
            hamesh = nass.select_one(".hamesh")
            footnotes = ""
            if hamesh:
                footnotes = hamesh.get_text("\n", strip=True)
                hamesh.decompose()

            result["html"] = str(nass)
            result["text"] = nass.get_text("\n", strip=True)
            result["footnotes"] = footnotes
        else:
            result["html"] = ""
            result["text"] = ""
            result["footnotes"] = ""

        return result

    def _extract_chapters_from_first_page(
        self, soup: BeautifulSoup, book_id: int
    ) -> list[ChapterEntry]:
        """
        Extract the full table of contents from the sidebar navigation.
        The TOC is available on every page, but we only parse it once
        from the first page.
        """
        chapters: list[ChapterEntry] = []
        selector = f'div.s-nav-head ~ ul a[href*="/book/"]'
        links = soup.select(selector)

        for link in links:
            href = link.get("href", "")
            title = link.get_text(strip=True)
            if not title:
                continue

            m = BOOK_URL_RE.search(href)
            page_num = int(m.group("page")) if m and m.group("page") else 0

            # Determine nesting level by counting parent <ul> elements
            level = 0
            parent = link.parent
            while parent:
                if isinstance(parent, Tag) and parent.name == "ul":
                    level += 1
                parent = parent.parent
            # Subtract 1 because the outermost <ul> is level 0
            level = max(0, level - 1)

            chapters.append(ChapterEntry(title=title, page=page_num, level=level))

        return chapters

    def _build_chapters_page_map(
        self, chapters: list[ChapterEntry]
    ) -> dict[int, list[str]]:
        """Map page numbers to chapter titles that start on that page."""
        page_map: dict[int, list[str]] = {}
        for ch in chapters:
            page_map.setdefault(ch.page, []).append(ch.title)
        return page_map

    # ----- Full book download ------------------------------------------------

    def download_book(
        self,
        book_id: int,
        resume_from: int = 1,
        existing_pages: list[PageData] | None = None,
    ) -> BookData:
        """Download all pages of a book."""
        log.info("=== Downloading book %d from shamela.ws ===", book_id)

        # Step 1: Fetch book info
        info = self.fetch_book_info(book_id)
        log.info("Book: %s by %s", info.get("title"), info.get("author"))

        book = BookData(
            book_id=book_id,
            title=info.get("title", ""),
            author=info.get("author", ""),
            metadata=info,
            pages=existing_pages or [],
        )

        # Step 2: Fetch first content page to get total pages and TOC
        first_url = PAGE_URL.format(book_id=book_id, page=1)
        first_soup = self._fetch_page(first_url)
        first_parsed = self._parse_page(first_soup, book_id)

        total = first_parsed.get("last_page")
        if not total:
            # Fallback: single page book or issue
            total = 1
            log.warning("Could not determine total pages; defaulting to 1")

        book.total_pages = total
        log.info("Total pages: %d", total)

        # Step 3: Extract TOC from first page
        book.chapters = self._extract_chapters_from_first_page(first_soup, book_id)
        log.info("Extracted %d chapter entries from TOC", len(book.chapters))
        chapters_map = self._build_chapters_page_map(book.chapters)

        # Step 4: Process first page (if not resuming past it)
        if resume_from <= 1:
            page_data = PageData(
                page_number=1,
                print_page=first_parsed["print_page"],
                part=first_parsed["part"],
                text=first_parsed["text"],
                html=first_parsed["html"],
                footnotes=first_parsed["footnotes"],
                chapter_titles=chapters_map.get(1, []),
            )
            book.pages.append(page_data)

        # Step 5: Download remaining pages
        start = max(2, resume_from)
        pbar = tqdm(
            range(start, total + 1),
            initial=start - 1,
            total=total,
            desc=f"Book {book_id}",
            unit="pg",
        )

        for page_num in pbar:
            try:
                url = PAGE_URL.format(book_id=book_id, page=page_num)
                soup = self._fetch_page(url)
                parsed = self._parse_page(soup, book_id)

                page_data = PageData(
                    page_number=page_num,
                    print_page=parsed["print_page"],
                    part=parsed["part"],
                    text=parsed["text"],
                    html=parsed["html"],
                    footnotes=parsed["footnotes"],
                    chapter_titles=chapters_map.get(page_num, []),
                )
                book.pages.append(page_data)

                pbar.set_postfix(
                    page=parsed["print_page"],
                    part=parsed["part"],
                )

            except Exception as e:
                log.error("Failed on page %d: %s", page_num, e)
                # Save progress so far and note where we stopped
                log.info(
                    "Saving partial progress (%d pages downloaded). "
                    "Resume with --resume flag.",
                    len(book.pages),
                )
                break

        return book


# ---------------------------------------------------------------------------
# JSON Output
# ---------------------------------------------------------------------------
def save_book_json(book: BookData, output_dir: Path) -> Path:
    """Save book data as structured JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"shamela_{book.book_id}_{_safe_filename(book.title)}.json"
    filepath = output_dir / filename

    data = {
        "book_id": book.book_id,
        "title": book.title,
        "author": book.author,
        "total_pages": book.total_pages,
        "downloaded_pages": len(book.pages),
        "complete": len(book.pages) >= book.total_pages,
        "metadata": book.metadata,
        "chapters": [asdict(ch) for ch in book.chapters],
        "pages": [asdict(p) for p in book.pages],
    }

    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Saved to %s (%.1f MB)", filepath, filepath.stat().st_size / 1e6)
    return filepath


def _safe_filename(s: str) -> str:
    """Create a filesystem-safe name from Arabic text."""
    # Keep Arabic letters, digits, spaces
    s = re.sub(r"[^\w\s\u0600-\u06FF]", "", s)
    s = s.strip().replace(" ", "_")[:60]
    return s or "book"


def load_partial(filepath: Path) -> tuple[int, list[PageData]]:
    """Load a partial download and return (resume_page, existing_pages)."""
    data = json.loads(filepath.read_text(encoding="utf-8"))
    pages = []
    for p in data.get("pages", []):
        pages.append(
            PageData(
                page_number=p["page_number"],
                print_page=p["print_page"],
                part=p["part"],
                text=p["text"],
                html=p["html"],
                chapter_titles=p.get("chapter_titles", []),
                footnotes=p.get("footnotes", ""),
            )
        )
    if pages:
        resume_from = pages[-1].page_number + 1
    else:
        resume_from = 1
    return resume_from, pages


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def list_maliki_books():
    """Print all mapped Maliki books."""
    print(f"\n{'ID':>8}  {'Title':<55} {'Author':<30} {'Category'}")
    print("-" * 130)
    for bid, info in sorted(MALIKI_BOOKS.items()):
        print(
            f"{bid:>8}  {info['title']:<55} {info['author']:<30} {info['category']}"
        )
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Download books from shamela.ws (المكتبة الشاملة)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "book_id",
        nargs="?",
        type=int,
        help="Shamela book ID (e.g., 587 for المدونة)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "shamela_books",
        help="Output directory for JSON files",
    )
    parser.add_argument(
        "--all-maliki",
        action="store_true",
        help="Download all mapped Maliki fiqh books",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all mapped Maliki books and their IDs",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a previously interrupted download",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=REQUEST_DELAY,
        help=f"Delay between requests in seconds (default: {REQUEST_DELAY})",
    )
    parser.add_argument(
        "--info-only",
        action="store_true",
        help="Only fetch book info/metadata, do not download pages",
    )

    args = parser.parse_args()

    if args.list:
        list_maliki_books()
        return

    if args.all_maliki:
        book_ids = list(MALIKI_BOOKS.keys())
    elif args.book_id:
        book_ids = [args.book_id]
    else:
        parser.print_help()
        sys.exit(1)

    with ShamelaScraper(delay=args.delay) as scraper:
        for book_id in book_ids:
            try:
                if args.info_only:
                    info = scraper.fetch_book_info(book_id)
                    print(json.dumps(info, ensure_ascii=False, indent=2))
                    continue

                resume_from = 1
                existing_pages: list[PageData] | None = None

                if args.resume:
                    # Find existing partial file
                    pattern = f"shamela_{book_id}_*.json"
                    existing = list(args.output.glob(pattern))
                    if existing:
                        partial_path = existing[0]
                        resume_from, existing_pages = load_partial(partial_path)
                        log.info(
                            "Resuming book %d from page %d (%d pages already downloaded)",
                            book_id,
                            resume_from,
                            len(existing_pages),
                        )

                book = scraper.download_book(
                    book_id,
                    resume_from=resume_from,
                    existing_pages=existing_pages,
                )
                save_book_json(book, args.output)

            except KeyboardInterrupt:
                log.info("Interrupted by user")
                if "book" in dir():
                    save_book_json(book, args.output)
                sys.exit(0)
            except Exception as e:
                log.error("Failed to download book %d: %s", book_id, e)
                if args.all_maliki:
                    continue  # Move to next book
                raise


if __name__ == "__main__":
    main()
