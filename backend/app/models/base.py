"""Database models for Mawso3a Fiqh Maliki."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Boolean,
    DateTime, Float, Enum as SAEnum, Table, UniqueConstraint
)
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


# --- Enums ---

class TextType(str, enum.Enum):
    MATN = "matn"
    SHARH = "sharh"
    HASHIYA = "hashiya"
    NAZM = "nazm"  # didactic poem
    FATAWA = "fatawa"
    ENCYCLOPEDIA = "encyclopedia"


class HukmType(str, enum.Enum):
    WAJIB = "wajib"
    MANDUB = "mandub"
    MUBAH = "mubah"
    MAKRUH = "makruh"
    HARAM = "haram"
    SAHIH = "sahih"
    FASID = "fasid"
    BATIL = "batil"


class ComparisonResult(str, enum.Enum):
    ITTIFAQ = "ittifaq"        # agreement
    IKHTILAF = "ikhtilaf"      # disagreement
    TAFSILAT = "tafsilat"      # partial agreement with conditions


class StudyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    SPECIALIST = "specialist"


class ConfidenceLevel(str, enum.Enum):
    AI_GENERATED = "ai_generated"
    SCHOLAR_REVIEWED = "scholar_reviewed"
    VERIFIED = "verified"


# --- Authors ---

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name_ar = Column(String(500), nullable=False)
    name_en = Column(String(500))
    full_name_ar = Column(Text)
    death_hijri = Column(Integer)  # year of death in Hijri
    death_ce = Column(Integer)     # year of death in CE
    century_hijri = Column(Integer)
    bio_ar = Column(Text)
    bio_en = Column(Text)
    region = Column(String(200))  # e.g., "Maghreb", "Egypt", "Iraq"

    books = relationship("Book", back_populates="author")
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Books (Mutoon + Shuruh + Hawashi) ---

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title_ar = Column(String(500), nullable=False)
    title_en = Column(String(500))
    short_title_ar = Column(String(200))
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    text_type = Column(SAEnum(TextType), nullable=False)
    study_level = Column(SAEnum(StudyLevel))
    parent_book_id = Column(Integer, ForeignKey("books.id"), nullable=True)  # sharh → matn
    description_ar = Column(Text)
    description_en = Column(Text)
    volume_count = Column(Integer, default=1)
    source_url = Column(Text)  # where we got the digital text
    source_name = Column(String(200))  # e.g., "shamela", "dorar", "mawsua_fiqhiya"

    author = relationship("Author", back_populates="books")
    parent_book = relationship("Book", remote_side=[id], backref="commentaries")
    chapters = relationship("Chapter", back_populates="book", order_by="Chapter.order")
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Fiqh Topic Taxonomy ---

class FiqhCategory(Base):
    """Top-level fiqh categories (kutub): tahara, salat, zakat, etc."""
    __tablename__ = "fiqh_categories"

    id = Column(Integer, primary_key=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300))
    parent_id = Column(Integer, ForeignKey("fiqh_categories.id"), nullable=True)
    order = Column(Integer, default=0)

    parent = relationship("FiqhCategory", remote_side=[id], backref="subcategories")
    masail = relationship("Masala", back_populates="category")


class Masala(Base):
    """A specific fiqh question/issue within a category."""
    __tablename__ = "masail"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("fiqh_categories.id"), nullable=False)
    title_ar = Column(String(500), nullable=False)
    title_en = Column(String(500))
    description_ar = Column(Text)
    order = Column(Integer, default=0)

    category = relationship("FiqhCategory", back_populates="masail")
    positions = relationship("Position", back_populates="masala")
    comparisons = relationship("Comparison", back_populates="masala")


# --- Book Content ---

class Chapter(Base):
    """Chapters/sections within a book (abwab)."""
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    title_ar = Column(String(500), nullable=False)
    title_en = Column(String(500))
    volume = Column(Integer, default=1)
    order = Column(Integer, default=0)
    parent_chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    fiqh_category_id = Column(Integer, ForeignKey("fiqh_categories.id"), nullable=True)

    book = relationship("Book", back_populates="chapters")
    parent_chapter = relationship("Chapter", remote_side=[id], backref="subchapters")
    fiqh_category = relationship("FiqhCategory")
    passages = relationship("Passage", back_populates="chapter", order_by="Passage.order")


class Passage(Base):
    """Individual text passages within a chapter."""
    __tablename__ = "passages"

    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    text_ar = Column(Text, nullable=False)
    order = Column(Integer, default=0)
    page_number = Column(Integer)
    volume = Column(Integer)

    chapter = relationship("Chapter", back_populates="passages")
    positions = relationship("Position", back_populates="passage")


# --- Ittifaq / Ikhtilaf Engine ---

class Position(Base):
    """A specific position/ruling extracted from a passage on a masala."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    masala_id = Column(Integer, ForeignKey("masail.id"), nullable=False)
    passage_id = Column(Integer, ForeignKey("passages.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    hukm = Column(SAEnum(HukmType), nullable=True)
    hukm_text_ar = Column(Text)  # the ruling in the author's words
    dalil_ar = Column(Text)      # evidence cited
    conditions_ar = Column(Text)  # conditions/restrictions
    confidence = Column(SAEnum(ConfidenceLevel), default=ConfidenceLevel.AI_GENERATED)
    reviewed_by = Column(String(200))
    reviewed_at = Column(DateTime)

    masala = relationship("Masala", back_populates="positions")
    passage = relationship("Passage", back_populates="positions")
    book = relationship("Book")


class Comparison(Base):
    """Comparison result between positions on the same masala."""
    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True)
    masala_id = Column(Integer, ForeignKey("masail.id"), nullable=False)
    result = Column(SAEnum(ComparisonResult), nullable=False)
    summary_ar = Column(Text)  # human-readable summary
    details_ar = Column(Text)  # detailed explanation
    confidence = Column(SAEnum(ConfidenceLevel), default=ConfidenceLevel.AI_GENERATED)
    reviewed_by = Column(String(200))
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    masala = relationship("Masala", back_populates="comparisons")
    position_links = relationship("ComparisonPosition", back_populates="comparison")


class ComparisonPosition(Base):
    """Links positions to a comparison."""
    __tablename__ = "comparison_positions"

    id = Column(Integer, primary_key=True)
    comparison_id = Column(Integer, ForeignKey("comparisons.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)

    comparison = relationship("Comparison", back_populates="position_links")
    position = relationship("Position")
