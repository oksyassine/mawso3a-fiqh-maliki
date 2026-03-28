from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.base import FiqhCategory, Masala

router = APIRouter()


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """List top-level fiqh categories (kutub al-fiqh)."""
    q = (
        select(FiqhCategory)
        .where(FiqhCategory.parent_id.is_(None))
        .options(selectinload(FiqhCategory.subcategories))
        .order_by(FiqhCategory.order)
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/categories/{category_id}")
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Get a category with its subcategories and masail."""
    q = (
        select(FiqhCategory)
        .options(
            selectinload(FiqhCategory.subcategories),
            selectinload(FiqhCategory.masail),
        )
        .where(FiqhCategory.id == category_id)
    )
    result = await db.execute(q)
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(404, "Category not found")
    return cat


@router.get("/masail")
async def list_masail(
    category_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List masail, optionally filtered by category."""
    q = select(Masala).options(selectinload(Masala.category))
    if category_id:
        q = q.where(Masala.category_id == category_id)
    q = q.order_by(Masala.order)
    result = await db.execute(q)
    return result.scalars().all()
