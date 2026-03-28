from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.base import Book, Author, Chapter, Passage, TextType, StudyLevel

router = APIRouter()


@router.get("/")
async def list_books(
    text_type: TextType | None = None,
    study_level: StudyLevel | None = None,
    author_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all books with optional filters."""
    q = select(Book).options(selectinload(Book.author))
    if text_type:
        q = q.where(Book.text_type == text_type)
    if study_level:
        q = q.where(Book.study_level == study_level)
    if author_id:
        q = q.where(Book.author_id == author_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/mutoon")
async def list_mutoon(db: AsyncSession = Depends(get_db)):
    """List all mutoon (primary texts) with their shuruh count."""
    q = (
        select(Book)
        .options(selectinload(Book.author), selectinload(Book.commentaries))
        .where(Book.text_type == TextType.MATN)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{book_id}")
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """Get a book with its chapters."""
    q = (
        select(Book)
        .options(
            selectinload(Book.author),
            selectinload(Book.chapters),
            selectinload(Book.commentaries).selectinload(Book.author),
            selectinload(Book.parent_book),
        )
        .where(Book.id == book_id)
    )
    result = await db.execute(q)
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(404, "Book not found")
    return book


@router.get("/{book_id}/chapters")
async def get_chapters(book_id: int, db: AsyncSession = Depends(get_db)):
    """Get all chapters of a book."""
    q = (
        select(Chapter)
        .where(Chapter.book_id == book_id)
        .order_by(Chapter.order)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{book_id}/chapters/{chapter_id}/passages")
async def get_passages(
    book_id: int,
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all passages in a chapter."""
    q = (
        select(Passage)
        .join(Chapter)
        .where(Chapter.book_id == book_id, Passage.chapter_id == chapter_id)
        .order_by(Passage.order)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/authors/")
async def list_authors(db: AsyncSession = Depends(get_db)):
    """List all authors."""
    q = select(Author).order_by(Author.death_hijri)
    result = await db.execute(q)
    return result.scalars().all()
