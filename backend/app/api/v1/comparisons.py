from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.base import (
    Comparison, ComparisonPosition, Position, Masala,
    ComparisonResult, ConfidenceLevel,
)

router = APIRouter()


@router.get("/masala/{masala_id}")
async def get_masala_comparisons(
    masala_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all comparisons for a specific masala (ittifaq/ikhtilaf)."""
    q = (
        select(Comparison)
        .options(
            selectinload(Comparison.position_links)
            .selectinload(ComparisonPosition.position)
            .selectinload(Position.passage),
            selectinload(Comparison.position_links)
            .selectinload(ComparisonPosition.position)
            .selectinload(Position.book),
        )
        .where(Comparison.masala_id == masala_id)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/masala/{masala_id}/positions")
async def get_masala_positions(
    masala_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all positions from different books on a masala."""
    q = (
        select(Position)
        .options(
            selectinload(Position.passage),
            selectinload(Position.book).selectinload("author"),
        )
        .where(Position.masala_id == masala_id)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/browse")
async def browse_comparisons(
    result_type: ComparisonResult | None = None,
    confidence: ConfidenceLevel | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Browse all comparisons with filters."""
    q = (
        select(Comparison)
        .options(selectinload(Comparison.masala))
    )
    if result_type:
        q = q.where(Comparison.result == result_type)
    if confidence:
        q = q.where(Comparison.confidence == confidence)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()
