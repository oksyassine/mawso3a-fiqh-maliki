# Mawso3a Fiqh Maliki — موسوعة الفقه المالكي

## Project Overview
A comprehensive Maliki fiqh encyclopedia app. Cross-platform (Flutter) + Backend (FastAPI + PostgreSQL).

## Architecture

### Backend (FastAPI + PostgreSQL)
- **Entry**: `backend/app/main.py`
- **Database**: PostgreSQL via asyncpg, SQLAlchemy 2.0 async
- **Models**: `backend/app/models/base.py` — Authors, Books, Chapters, Passages, Taxonomy, Positions, Comparisons
- **API**: `/api/v1/books`, `/api/v1/taxonomy`, `/api/v1/search`, `/api/v1/comparisons`
- **AI Engine**: `backend/app/services/comparison_engine.py` — Claude-powered ittifaq/ikhtilaf extraction

### Flutter App (`frontend/`)
- **Package**: mawso3a_fiqh
- **Screens**: home, library, book_reader, taxonomy, comparison, search
- **State**: Provider
- **Offline**: SQLite local cache via sqflite

### Data Sources
- **Shamela.ws** — Primary source for all mutoon and shuruh texts (via Lucene index in ISO)
- **الدرر السنية (dorar.net)** — Fiqh rulings and evidence
- **الموسوعة الفقهية الكويتية** — 45-volume fiqh encyclopedia

### Shamela Extraction Pipeline (COMPLETE ✅)
**Goal**: Import 86 Maliki fiqh books from Shamela v1446 ISO into unified SQLite database.

**Flow**:
1. **Lucene extraction** — `LuceneDumper.java` reads Shamela's Lucene 9.0 page index
   - Input: 7.3M documents across all books in ISO
   - Filter by shamela_id: extract only 86 Maliki books
   - Output: `all_maliki_books.jsonl` (163,401 pages)

2. **Split by book** — `scripts/split_by_book.py`
   - Input: `all_maliki_books.jsonl`
   - Output: 86 JSONL files in `lucene-index/books/shamela_*.jsonl`

3. **Build database** — `scripts/build_book_db.py`
   - Parse HTML TOC anchors: `<span data-type="title">` → kitab/bab markers
   - Clean text: strip HTML, normalize whitespace
   - Output: `data/shamela_v4.db` (SQLite)

**Database Schema**:
```sql
CREATE TABLE books (
  book_key    TEXT PRIMARY KEY,      -- book_01 to book_91
  shamela_id  INTEGER,               -- Shamela.ws book ID
  title       TEXT,                  -- Arabic title
  status      TEXT                   -- DIGITAL, PARTIAL, ABSENT_FROM_ISO
);

CREATE TABLE pages (
  book_key    TEXT,
  shamela_id  INTEGER,
  page_id     INTEGER,
  body        TEXT,                  -- Clean page text (harakat preserved)
  foot        TEXT,                  -- Footnotes (tahqiq apparatus, takhrij, variants)
  toc_anchors TEXT,                  -- JSON [{id, text}] for TOC boundaries
  PRIMARY KEY (shamela_id, page_id)
);
```

**Status**: 
- **86 DIGITAL** books: fully extractable
- **2 PARTIAL**: book_07 (الموازية), book_08 (العتبية) — historically lost texts
- **3 ABSENT_FROM_ISO**: book_40/82/84 with IDs that don't exist in v1446

**Notes**:
- 51,746 pages (31.7%) have footnote text — the tahqiq treasure
- Top footnote-rich books: بغية المقتصد (9.5K pages), التبصرة (6.2K), شرح المختصر (2.7K)
- ISO source: mp3quran.net mirror (12 GB, all segments clean including _7d3/_7d4)
- Local extraction: `lucene-index/extracted/database/store/page/` (13 GB Lucene index)

### Extraction Scripts
- **`scripts/dump_shamela_book.sh <book_id>`** — Extract individual book from Lucene (reusable)
  - Usage: `./dump_shamela_book.sh 587` → `lucene-index/book_587.jsonl`
  - ~15-30 min per book (scans full 7.3M doc index)
  
- **`scripts/split_by_book.py`** — Split merged JSONL by shamela_id (~1 min for 163K pages)
  - Sorts pages by page_id numerically
  - Creates per-book JSONL files in `lucene-index/books/`

- **`scripts/build_book_db.py`** — Build SQLite database from per-book JSONL (~5 min)
  - Parses HTML `<span data-type="title">` TOC anchors
  - Cleans text, normalizes whitespace
  - Stores in `data/shamela_v4.db`

### Query Examples
```bash
# How many pages per book?
sqlite3 data/shamela_v4.db "SELECT book_key, COUNT(*) FROM pages GROUP BY book_key ORDER BY book_key;"

# Get first 5 pages of المدونة
sqlite3 data/shamela_v4.db "SELECT page_id, substr(body,1,200) FROM pages WHERE book_key='book_02' LIMIT 5;"

# Which books have the most footnotes?
sqlite3 data/shamela_v4.db "SELECT book_key, COUNT(*) FROM pages WHERE foot != '' GROUP BY book_key ORDER BY COUNT(*) DESC LIMIT 10;"

# Extract all pages from a kitab (using TOC anchors)
sqlite3 data/shamela_v4.db "SELECT page_id, body FROM pages WHERE book_key='book_02' AND page_id BETWEEN 1 AND 100;"
```

### Ittifaq/Ikhtilaf Engine (Option C — Hybrid)
1. AI (Claude) extracts positions from passages per masala
2. AI compares positions across books → ittifaq/ikhtilaf/tafsilat
3. Scholar review interface to verify/correct
4. Confidence levels: ai_generated → scholar_reviewed → verified

## Key Entities
- **Author** — 38 major Maliki scholars (179-1397 AH)
- **Book** — Mutoon, Shuruh, Hawashi, Nazm, Fatawa, Encyclopedias
- **FiqhCategory** — 17 kutub, ~100 abwab
- **Masala** — Specific fiqh questions
- **Position** — A ruling extracted from a passage
- **Comparison** — Ittifaq/ikhtilaf result across positions

## Study Level Hierarchy
1. Beginner: الأخضري, العشماوية, ابن عاشر, الرسالة
2. Intermediate: أقرب المسالك + الشرح الصغير
3. Advanced: مختصر خليل + الشرح الكبير + حاشية الدسوقي
4. Specialist: المدونة, الذخيرة, البيان والتحصيل
