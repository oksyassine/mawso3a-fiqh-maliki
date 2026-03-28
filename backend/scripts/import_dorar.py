#!/usr/bin/env python3
"""
Import fiqh content from dorar.net (الدرر السنية - الموسوعة الفقهية).

Scrapes the Dorar Fiqh Encyclopedia, focusing on content relevant to Maliki fiqh.

URL pattern:
  - TOC: https://dorar.net/feqhia  (lists all kutub with their section IDs)
  - Article: https://dorar.net/feqhia/{id}  (server-rendered HTML with fiqh text)

Content structure:
  - Main text is inside <div class="w-100 mt-4"> blocks
  - Footnotes/references are in <a class="dorar-bg-lightGreen"> elements with data-content attrs
  - Madhab positions (Hanafi, Maliki, Shafi'i, Hanbali) are mentioned inline
  - Breadcrumb: kitab > bab > fasl > mabhath > matlab

Output: data/dorar_feqhia.json
"""

import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup, Tag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

BASE_URL = "https://dorar.net"
FEQHIA_URL = f"{BASE_URL}/feqhia"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "dorar_feqhia.json"

# Rate limiting
REQUEST_DELAY = 1.5  # seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Maliki-related keywords to tag content
MALIKI_KEYWORDS = [
    "المالكيَّة",
    "المالكية",
    "المالكيّة",
    "مالك",
    "المذهب المالكي",
    "مذهب مالك",
    "عند المالكية",
    "قول المالكية",
    "مذهب المالكيَّة",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en;q=0.5",
}


async def fetch_page(
    client: httpx.AsyncClient, url: str, retries: int = MAX_RETRIES
) -> Optional[str]:
    """Fetch a page with retry logic and rate limiting."""
    for attempt in range(retries):
        try:
            resp = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=30)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                wait = RETRY_DELAY * (attempt + 2)
                log.warning("Rate limited on %s, waiting %ds...", url, wait)
                await asyncio.sleep(wait)
            elif resp.status_code == 404:
                log.debug("404 for %s, skipping", url)
                return None
            else:
                log.warning("HTTP %d for %s (attempt %d)", resp.status_code, url, attempt + 1)
                await asyncio.sleep(RETRY_DELAY)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            log.warning("Connection error for %s: %s (attempt %d)", url, e, attempt + 1)
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    log.error("Failed to fetch %s after %d retries", url, retries)
    return None


def extract_toc(html: str) -> list[dict]:
    """Extract the table of contents from the main feqhia page.

    Returns a list of {id, title, url} for every topic link found in the sidebar.
    """
    soup = BeautifulSoup(html, "html.parser")
    toc = []
    seen_ids = set()

    for a_tag in soup.find_all("a", href=re.compile(r"/feqhia/\d+")):
        href = a_tag.get("href", "")
        match = re.search(r"/feqhia/(\d+)", href)
        if not match:
            continue
        topic_id = int(match.group(1))
        if topic_id in seen_ids:
            continue

        title = a_tag.get_text(strip=True)
        # Skip empty titles or navigation-only links
        if not title or len(title) < 3:
            continue
        # Skip prev/next navigation links
        if title in ("السابق", "التالي"):
            continue

        seen_ids.add(topic_id)
        toc.append({
            "id": topic_id,
            "title": title,
            "url": f"{FEQHIA_URL}/{topic_id}",
        })

    toc.sort(key=lambda x: x["id"])
    return toc


def extract_breadcrumb(soup: BeautifulSoup) -> list[str]:
    """Extract the breadcrumb path (kitab > bab > fasl > mabhath)."""
    breadcrumb = []
    # Breadcrumb is typically in the page header area
    # Pattern: الرئيسة > الموسوعة الفقهية > كتابُ الطَّهارةِ > الباب الأول > ...
    bc_el = soup.find("div", class_=re.compile(r"breadcrumb|bread"))
    if bc_el:
        for item in bc_el.find_all(["a", "span", "li"]):
            text = item.get_text(strip=True)
            if text and text not in ("الرئيسة", "الموسوعة الفقهية", ">", ""):
                breadcrumb.append(text)
    if not breadcrumb:
        # Fallback: extract from title
        title_el = soup.find("title")
        if title_el:
            parts = title_el.get_text().split(" - ")
            if parts:
                breadcrumb = [parts[0].strip()]
    return breadcrumb


def extract_footnotes(content_el: Tag) -> list[dict]:
    """Extract footnotes from data-content attributes of reference links."""
    footnotes = []
    for a_tag in content_el.find_all("a", class_=re.compile(r"dorar-bg-lightGreen")):
        note_id = a_tag.get("id", "")
        note_text = a_tag.get("data-content", "").strip()
        if note_text:
            footnotes.append({
                "id": note_id,
                "text": note_text,
            })
    return footnotes


def extract_article_content(html: str) -> Optional[dict]:
    """Extract the main fiqh content from an article page.

    Returns: {title, breadcrumb, text, footnotes, mentions_maliki, evidence}
    """
    soup = BeautifulSoup(html, "html.parser")

    # Get page title
    title = ""
    title_el = soup.find("title")
    if title_el:
        title = title_el.get_text(strip=True).split(" - ")[0].strip()

    # Get breadcrumb
    breadcrumb = extract_breadcrumb(soup)

    # Find the main content container
    # Content hierarchy: div#cntnt.card-body > div.w-100.mt-4 (contains text + footnote links)
    # Footnote links have class "dorar-bg-lightGreen" with data-content attributes
    content_div = None

    # Strategy 1: Direct ID selector for the content container
    cntnt = soup.find("div", id="cntnt")
    if cntnt:
        # Look for the w-100 child which has the actual text
        w100 = cntnt.find("div", class_=lambda c: c and "w-100" in c)
        content_div = w100 or cntnt

    # Strategy 2: Look for div with class "w-100" containing footnote links
    if not content_div:
        for div in soup.find_all("div", class_=lambda c: c and "w-100" in c):
            if div.find("a", class_=re.compile(r"dorar-bg-lightGreen|enc-")):
                content_div = div
                break

    # Strategy 3: Look for w-100 divs with substantial Arabic fiqh terms
    if not content_div:
        fiqh_terms = [
            "الأصل", "المذاهب", "الإجماع", "الحكم", "يجب", "يجوز", "لا يجوز",
            "اتفق", "المسلمين", "النبي", "الفقهاء", "القول", "المذهب", "الحنفيَّة",
            "المالكيَّة", "الشافعيَّة", "الحنابلة", "اختلف", "أجمع", "الراجح",
        ]
        for div in soup.find_all("div", class_=lambda c: c and "w-100" in c):
            text = div.get_text(strip=True)
            if len(text) > 100 and any(kw in text for kw in fiqh_terms):
                content_div = div
                break

    # Strategy 4: Look for card-body with amiri font class (article wrapper)
    if not content_div:
        amiri = soup.find("div", class_=re.compile(r"amiri_custom_content"))
        if amiri:
            content_div = amiri

    # Strategy 5: Look in tab-pane active elements
    if not content_div:
        for div in soup.find_all("div", class_=re.compile(r"tab-pane.*active")):
            text = div.get_text(strip=True)
            if len(text) > 200:
                content_div = div
                break

    if not content_div:
        # Last resort: check if page has fiqh content at all
        body = soup.find("body")
        if body:
            full_text = body.get_text()
            has_content = any(
                kw in full_text for kw in ["المذاهب", "الإجماع", "الدليل", "الحنفيَّة", "المالكيَّة"]
            )
            if not has_content:
                return None  # This is likely a section/TOC page, not a content page

    # Extract text content
    raw_text = ""
    footnotes = []
    if content_div:
        footnotes = extract_footnotes(content_div)
        # Remove footnote popover elements for clean text
        for a_tag in content_div.find_all("a", class_=re.compile(r"dorar-bg-lightGreen")):
            a_tag.decompose()
        raw_text = content_div.get_text(separator=" ", strip=True)
        # Clean up excessive whitespace
        raw_text = re.sub(r"\s+", " ", raw_text).strip()
    else:
        # Try extracting from full body, filtering out navigation
        body = soup.find("body")
        if body:
            # Get all text content, removing known non-content elements
            for nav in body.find_all(["nav", "header", "footer", "script", "style"]):
                nav.decompose()
            for sidebar in body.find_all("div", class_=re.compile(r"sidebar|slide-out|modal")):
                sidebar.decompose()

            footnotes = extract_footnotes(body)
            for a_tag in body.find_all("a", class_=re.compile(r"dorar-bg-lightGreen")):
                a_tag.decompose()

            raw_text = body.get_text(separator=" ", strip=True)
            raw_text = re.sub(r"\s+", " ", raw_text).strip()

    if not raw_text or len(raw_text) < 50:
        return None

    # Check if content mentions Maliki madhab
    mentions_maliki = any(kw in raw_text for kw in MALIKI_KEYWORDS)

    # Extract evidence/daleel sections
    evidence = []
    daleel_patterns = [
        r"الدَّليلُ[^:]*:\s*([^\.]{10,300})",
        r"الأدلَّة[^:]*:\s*([^\.]{10,300})",
        r"الدليل[^:]*:\s*([^\.]{10,300})",
    ]
    for pattern in daleel_patterns:
        for match in re.finditer(pattern, raw_text):
            evidence.append(match.group(1).strip())

    return {
        "title": title,
        "breadcrumb": breadcrumb,
        "text": raw_text,
        "footnotes": footnotes,
        "evidence": evidence,
        "mentions_maliki": mentions_maliki,
    }


async def scrape_toc(client: httpx.AsyncClient) -> list[dict]:
    """Fetch and parse the main feqhia TOC page to get all topic IDs."""
    log.info("Fetching main TOC from %s", FEQHIA_URL)
    html = await fetch_page(client, FEQHIA_URL)
    if not html:
        log.error("Failed to fetch TOC page")
        return []

    toc = extract_toc(html)
    log.info("Found %d topics in TOC", len(toc))
    return toc


async def scrape_articles(
    client: httpx.AsyncClient,
    toc: list[dict],
    start_from: int = 0,
    limit: Optional[int] = None,
) -> list[dict]:
    """Scrape individual article pages.

    Args:
        client: httpx async client
        toc: list of {id, title, url} from TOC
        start_from: skip topics with id < start_from (for resuming)
        limit: max number of articles to scrape (None = all)
    """
    articles = []
    filtered = [t for t in toc if t["id"] >= start_from]
    if limit:
        filtered = filtered[:limit]

    total = len(filtered)
    log.info("Scraping %d articles (start_from=%d, limit=%s)", total, start_from, limit)

    for i, topic in enumerate(filtered):
        topic_id = topic["id"]
        url = topic["url"]

        log.info("[%d/%d] Fetching topic %d: %s", i + 1, total, topic_id, topic["title"][:60])

        html = await fetch_page(client, url)
        if not html:
            continue

        article = extract_article_content(html)
        if article:
            article["id"] = topic_id
            article["source_url"] = url
            articles.append(article)
            log.info(
                "  -> Extracted: %d chars, maliki=%s, %d footnotes",
                len(article["text"]),
                article["mentions_maliki"],
                len(article["footnotes"]),
            )
        else:
            log.debug("  -> No content (likely a section/TOC page)")

        # Rate limiting
        await asyncio.sleep(REQUEST_DELAY)

    return articles


def save_results(articles: list[dict], output_file: Path):
    """Save scraped articles to JSON."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Separate Maliki-relevant articles
    maliki_articles = [a for a in articles if a.get("mentions_maliki")]

    result = {
        "source": "dorar.net",
        "source_name": "الدرر السنية - الموسوعة الفقهية",
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_articles": len(articles),
        "maliki_relevant": len(maliki_articles),
        "articles": articles,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    log.info(
        "Saved %d articles (%d Maliki-relevant) to %s",
        len(articles),
        len(maliki_articles),
        output_file,
    )

    # Also save a Maliki-only subset
    maliki_file = output_file.with_name("dorar_feqhia_maliki.json")
    maliki_result = {
        "source": "dorar.net",
        "source_name": "الدرر السنية - الموسوعة الفقهية (المالكية فقط)",
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_articles": len(maliki_articles),
        "articles": maliki_articles,
    }
    with open(maliki_file, "w", encoding="utf-8") as f:
        json.dump(maliki_result, f, ensure_ascii=False, indent=2)

    log.info("Saved Maliki-only subset (%d articles) to %s", len(maliki_articles), maliki_file)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Import fiqh content from dorar.net")
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Start from topic ID (for resuming interrupted scrapes)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of articles to scrape (default: all)",
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
        help="Resume from last scraped ID in existing output file",
    )
    args = parser.parse_args()

    output_file = Path(args.output)
    start_from = args.start_from

    # Resume support: load existing file and find last ID
    existing_articles = []
    if args.resume and output_file.exists():
        with open(output_file, encoding="utf-8") as f:
            existing = json.load(f)
            existing_articles = existing.get("articles", [])
            if existing_articles:
                last_id = max(a["id"] for a in existing_articles)
                start_from = last_id + 1
                log.info("Resuming from ID %d (found %d existing articles)", start_from, len(existing_articles))

    async with httpx.AsyncClient() as client:
        # Step 1: Get TOC
        toc = await scrape_toc(client)
        if not toc:
            log.error("No topics found in TOC, exiting")
            return

        # Step 2: Scrape articles
        new_articles = await scrape_articles(
            client, toc, start_from=start_from, limit=args.limit
        )

        # Merge with existing if resuming
        all_articles = existing_articles + new_articles

        # Step 3: Save
        save_results(all_articles, output_file)

    log.info("Done! Total: %d articles scraped", len(all_articles))


if __name__ == "__main__":
    asyncio.run(main())
