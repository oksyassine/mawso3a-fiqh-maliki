from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.base import Passage, Chapter, Book

router = APIRouter()


@router.get("/")
async def search_texts(
    q: str = Query(..., min_length=2, description="Search query in Arabic"),
    book_id: int | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Full-text search across all passages."""
    query = (
        select(Passage)
        .join(Chapter)
        .join(Book)
        .options(
            selectinload(Passage.chapter).selectinload(Chapter.book),
        )
        .where(Passage.text_ar.contains(q))
    )
    if book_id:
        query = query.where(Book.id == book_id)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
