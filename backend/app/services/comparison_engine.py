"""
Ittifaq/Ikhtilaf comparison service.

Serves PRE-COMPUTED comparison data from the database.
All AI extraction is done offline via scripts/batch_extract_comparisons.py.
No runtime AI calls — everything is static data.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.base import (
    Position, Comparison, ComparisonPosition, Masala,
    FiqhCategory, ComparisonResult, ConfidenceLevel,
)


async def get_masala_summary(db: AsyncSession, masala_id: int) -> dict | None:
    """Get pre-computed comparison summary for a masala."""
    masala = await db.get(Masala, masala_id, options=[selectinload(Masala.category)])
    if not masala:
        return None

    # Get comparisons
    q = (
        select(Comparison)
        .options(
            selectinload(Comparison.position_links)
            .selectinload(ComparisonPosition.position)
            .selectinload(Position.book),
        )
        .where(Comparison.masala_id == masala_id)
    )
    result = await db.execute(q)
    comparisons = result.scalars().all()

    # Get all positions
    q_pos = (
        select(Position)
        .options(
            selectinload(Position.book).selectinload("author"),
            selectinload(Position.passage),
        )
        .where(Position.masala_id == masala_id)
    )
    result_pos = await db.execute(q_pos)
    positions = result_pos.scalars().all()

    return {
        "masala": masala,
        "comparisons": comparisons,
        "positions": positions,
        "position_count": len(positions),
        "has_ikhtilaf": any(c.result == ComparisonResult.IKHTILAF for c in comparisons),
    }


async def get_category_stats(db: AsyncSession, category_id: int) -> dict:
    """Get ittifaq/ikhtilaf statistics for a fiqh category."""
    # Count comparisons by result type
    q = (
        select(
            Comparison.result,
            func.count(Comparison.id),
        )
        .join(Masala)
        .where(Masala.category_id == category_id)
        .group_by(Comparison.result)
    )
    result = await db.execute(q)
    counts = {row[0].value: row[1] for row in result.all()}

    return {
        "category_id": category_id,
        "ittifaq_count": counts.get("ittifaq", 0),
        "ikhtilaf_count": counts.get("ikhtilaf", 0),
        "tafsilat_count": counts.get("tafsilat", 0),
        "total": sum(counts.values()),
    }


async def get_all_ikhtilafat(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[Comparison]:
    """Get all disagreements across the entire corpus."""
    q = (
        select(Comparison)
        .options(
            selectinload(Comparison.masala).selectinload(Masala.category),
            selectinload(Comparison.position_links)
            .selectinload(ComparisonPosition.position)
            .selectinload(Position.book),
        )
        .where(Comparison.result == ComparisonResult.IKHTILAF)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    return result.scalars().all()
