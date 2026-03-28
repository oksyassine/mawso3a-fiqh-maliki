#!/usr/bin/env python3
"""
Batch extraction of ittifaq/ikhtilaf comparisons.

ONE-TIME batch script that:
1. Reads all imported passages from the DB
2. Uses Claude to extract positions (ahkam) per masala
3. Compares positions across books
4. Stores everything as static data in the DB

After this runs, the app serves pre-computed results — no runtime AI calls needed.

Usage:
    # Process all masail
    python batch_extract_comparisons.py

    # Process a specific category
    python batch_extract_comparisons.py --category-id 1

    # Process a single masala
    python batch_extract_comparisons.py --masala-id 42

    # Dry run (print what would be processed)
    python batch_extract_comparisons.py --dry-run

    # Limit API calls (for testing)
    python batch_extract_comparisons.py --limit 10
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import anthropic
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.models.base import (
    Base, Passage, Chapter, Book, Author, Masala, FiqhCategory,
    Position, Comparison, ComparisonPosition,
    HukmType, ComparisonResult, ConfidenceLevel,
)
from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("batch_extract")

settings = get_settings()
client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# Rate limiting
DELAY_BETWEEN_CALLS = 1.0  # seconds


# --- Prompts ---

EXTRACTION_PROMPT = """أنت عالم متخصص في الفقه المالكي. استخرج الحكم الفقهي من هذا النص.

المسألة: {masala_title}
الكتاب: {book_title}
المؤلف: {author_name}

النص:
{passage_text}

أجب بصيغة JSON فقط (بدون أي نص آخر):
{{
    "hukm": "واجب|مندوب|مباح|مكروه|حرام|صحيح|فاسد|باطل|null",
    "hukm_text": "نص الحكم بكلمات المؤلف",
    "dalil": "الدليل المذكور إن وجد أو null",
    "conditions": "الشروط والقيود إن وجدت أو null",
    "is_mu3tamad": true
}}"""

COMPARISON_PROMPT = """أنت عالم متخصص في الفقه المقارن داخل المذهب المالكي.
قارن بين الأحكام التالية المستخرجة من كتب مالكية مختلفة:

المسألة: {masala_title}

{positions_text}

أجب بصيغة JSON فقط (بدون أي نص آخر):
{{
    "result": "ittifaq|ikhtilaf|tafsilat",
    "summary_ar": "ملخص المقارنة في جملتين",
    "details_ar": "تفصيل الاتفاق أو الاختلاف مع ذكر كل قول ومن قال به",
    "mu3tamad": "القول المعتمد في المذهب"
}}"""


# --- Hukm mapping ---

HUKM_MAP = {
    "واجب": HukmType.WAJIB,
    "مندوب": HukmType.MANDUB,
    "مباح": HukmType.MUBAH,
    "مكروه": HukmType.MAKRUH,
    "حرام": HukmType.HARAM,
    "صحيح": HukmType.SAHIH,
    "فاسد": HukmType.FASID,
    "باطل": HukmType.BATIL,
}

RESULT_MAP = {
    "ittifaq": ComparisonResult.ITTIFAQ,
    "ikhtilaf": ComparisonResult.IKHTILAF,
    "tafsilat": ComparisonResult.TAFSILAT,
}


def call_claude(prompt: str, system: str = "") -> dict | None:
    """Synchronous Claude call with JSON extraction."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=system or "أجب بصيغة JSON فقط.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        log.error(f"Claude API error: {e}")
    return None


async def extract_positions_for_masala(
    db: AsyncSession,
    masala: Masala,
    dry_run: bool = False,
) -> list[Position]:
    """Extract positions from all relevant passages for a masala."""

    # Find passages tagged to this masala's category
    q = (
        select(Passage)
        .join(Chapter)
        .join(Book)
        .options(
            selectinload(Passage.chapter)
            .selectinload(Chapter.book)
            .selectinload(Book.author),
        )
        .where(Chapter.fiqh_category_id == masala.category_id)
    )
    result = await db.execute(q)
    passages = result.scalars().all()

    if not passages:
        log.info(f"  No passages found for masala: {masala.title_ar}")
        return []

    log.info(f"  Found {len(passages)} passages for: {masala.title_ar}")

    if dry_run:
        return []

    positions = []
    for passage in passages:
        book = passage.chapter.book
        author = book.author

        prompt = EXTRACTION_PROMPT.format(
            masala_title=masala.title_ar,
            book_title=book.title_ar,
            author_name=author.name_ar,
            passage_text=passage.text_ar[:3000],  # Limit text length
        )

        extraction = call_claude(prompt)
        time.sleep(DELAY_BETWEEN_CALLS)

        if not extraction or "hukm" not in extraction:
            log.warning(f"    Failed extraction for passage {passage.id} in {book.short_title_ar}")
            continue

        hukm_enum = HUKM_MAP.get(extraction.get("hukm"))

        pos = Position(
            masala_id=masala.id,
            passage_id=passage.id,
            book_id=book.id,
            hukm=hukm_enum,
            hukm_text_ar=extraction.get("hukm_text", ""),
            dalil_ar=extraction.get("dalil") or "",
            conditions_ar=extraction.get("conditions") or "",
            confidence=ConfidenceLevel.AI_GENERATED,
        )
        db.add(pos)
        positions.append(pos)
        log.info(f"    ✓ {book.short_title_ar}: {extraction.get('hukm', '?')}")

    await db.flush()
    return positions


async def compare_positions_for_masala(
    db: AsyncSession,
    masala: Masala,
    positions: list[Position],
    dry_run: bool = False,
) -> Comparison | None:
    """Compare extracted positions and store the comparison result."""

    if len(positions) < 2:
        return None

    if dry_run:
        return None

    # Build positions text for Claude
    positions_data = []
    for pos in positions:
        await db.refresh(pos, ["passage"])
        book = await db.get(Book, pos.book_id, options=[selectinload(Book.author)])
        positions_data.append(
            f"📖 {book.title_ar} ({book.author.name_ar}):\n"
            f"الحكم: {pos.hukm_text_ar}\n"
            f"الدليل: {pos.dalil_ar or 'غير مذكور'}\n"
            f"الشروط: {pos.conditions_ar or 'لا يوجد'}"
        )

    prompt = COMPARISON_PROMPT.format(
        masala_title=masala.title_ar,
        positions_text="\n\n".join(positions_data),
    )

    comparison_data = call_claude(prompt)
    time.sleep(DELAY_BETWEEN_CALLS)

    if not comparison_data or "result" not in comparison_data:
        log.warning(f"  Failed comparison for masala: {masala.title_ar}")
        return None

    comp = Comparison(
        masala_id=masala.id,
        result=RESULT_MAP.get(comparison_data["result"], ComparisonResult.TAFSILAT),
        summary_ar=comparison_data.get("summary_ar", ""),
        details_ar=comparison_data.get("details_ar", ""),
        confidence=ConfidenceLevel.AI_GENERATED,
    )
    db.add(comp)
    await db.flush()

    # Link positions
    for pos in positions:
        db.add(ComparisonPosition(comparison_id=comp.id, position_id=pos.id))

    result_emoji = {"ittifaq": "✅", "ikhtilaf": "⚠️", "tafsilat": "📋"}.get(
        comparison_data["result"], "❓"
    )
    log.info(f"  {result_emoji} {comparison_data['result']}: {comparison_data.get('summary_ar', '')[:80]}")

    return comp


async def main():
    parser = argparse.ArgumentParser(description="Batch extract ittifaq/ikhtilaf comparisons")
    parser.add_argument("--category-id", type=int, help="Process only this fiqh category")
    parser.add_argument("--masala-id", type=int, help="Process only this masala")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--limit", type=int, help="Limit number of masail to process")
    args = parser.parse_args()

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_sess = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_sess() as db:
        # Get masail to process
        q = select(Masala).options(selectinload(Masala.category))

        if args.masala_id:
            q = q.where(Masala.id == args.masala_id)
        elif args.category_id:
            q = q.where(Masala.category_id == args.category_id)

        q = q.order_by(Masala.category_id, Masala.order)

        if args.limit:
            q = q.limit(args.limit)

        result = await db.execute(q)
        masail = result.scalars().all()

        log.info(f"Processing {len(masail)} masail {'(DRY RUN)' if args.dry_run else ''}")
        log.info("=" * 60)

        stats = {"total": 0, "positions": 0, "ittifaq": 0, "ikhtilaf": 0, "tafsilat": 0, "skipped": 0}

        for masala in masail:
            stats["total"] += 1
            cat_name = masala.category.name_ar if masala.category else "?"
            log.info(f"\n[{stats['total']}/{len(masail)}] {cat_name} > {masala.title_ar}")

            # Extract positions
            positions = await extract_positions_for_masala(db, masala, dry_run=args.dry_run)
            stats["positions"] += len(positions)

            if len(positions) < 2:
                stats["skipped"] += 1
                continue

            # Compare
            comp = await compare_positions_for_masala(db, masala, positions, dry_run=args.dry_run)
            if comp:
                key = comp.result.value if comp.result else "skipped"
                stats[key] = stats.get(key, 0) + 1

        if not args.dry_run:
            await db.commit()

        log.info("\n" + "=" * 60)
        log.info("DONE!")
        log.info(f"  Masail processed: {stats['total']}")
        log.info(f"  Positions extracted: {stats['positions']}")
        log.info(f"  Ittifaq (agreement): {stats['ittifaq']}")
        log.info(f"  Ikhtilaf (disagreement): {stats['ikhtilaf']}")
        log.info(f"  Tafsilat (partial): {stats['tafsilat']}")
        log.info(f"  Skipped (< 2 positions): {stats['skipped']}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
