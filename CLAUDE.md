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
- **Shamela.ws** — Primary source for all mutoon and shuruh texts
- **الدرر السنية (dorar.net)** — Fiqh rulings and evidence
- **الموسوعة الفقهية الكويتية** — 45-volume fiqh encyclopedia
- **Import scripts**: `backend/scripts/import_shamela.py`, `import_dorar.py`, `import_mawsua_fiqhiya.py`

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
