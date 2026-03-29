"""
Maliki Fiqh Masail Review Web App
FastAPI backend that auto-discovers and loads ALL seed comparison files.
"""

import importlib
import sys
from pathlib import Path
from collections import defaultdict
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add seed data directory to path
SEED_DIR = Path(__file__).resolve().parent.parent / "backend" / "data" / "seed"
sys.path.insert(0, str(SEED_DIR))

# ---------------------------------------------------------------------------
# Auto-discover all seed_*_comparisons.py and seed_*_part*.py files
# ---------------------------------------------------------------------------
ALL_MASAIL = []
_seen_keys = set()

# Map of kitab keywords to kitab names
KITAB_NAMES = {
    "tahara": "كتاب الطهارة",
    "salat": "كتاب الصلاة",
    "zakat": "كتاب الزكاة",
    "siyam": "كتاب الصيام",
    "hajj": "كتاب الحج",
    "nikah": "كتاب النكاح",
    "talaq": "كتاب الطلاق",
    "buyu": "كتاب البيوع",
    "faraid": "كتاب الفرائض",
    "qada": "كتاب القضاء",
    "hudud": "كتاب الحدود",
    "misc": "كتب متفرقة",
}

# Data list names to look for in each module
DATA_LIST_NAMES = [
    "TAHARA_PART1", "TAHARA_PART2", "TAHARA_DATA",
    "SALAT_DATA", "ZAKAT_DATA", "SIYAM_DATA", "HAJJ_DATA",
    "NIKAH_DATA", "TALAQ_DATA", "BUYU_DATA",
    "FARAID_DATA", "QADA_DATA", "HUDUD_DATA", "MISC_DATA",
]

# Detect which kitab a masala belongs to based on its category or source file
def _detect_kitab(masala, source_file=""):
    cat = masala.get("category", "")
    key = masala.get("masala_key", "")

    for kw, name in KITAB_NAMES.items():
        if kw in source_file:
            return name
        if kw in key:
            return name

    # Fallback: detect from category name
    if "طهارة" in cat or "وضوء" in cat or "غسل" in cat or "تيمم" in cat or "مياه" in cat or "نجاس" in cat or "حيض" in cat or "خفين" in cat or "استنجاء" in cat or "ميت" in cat:
        return "كتاب الطهارة"
    if "صلاة" in cat or "مواقيت" in cat or "أذان" in cat or "سجود" in cat or "إمام" in cat or "جمعة" in cat or "جنازة" in cat or "نوافل" in cat or "كسوف" in cat:
        return "كتاب الصلاة"
    if "زكاة" in cat:
        return "كتاب الزكاة"
    if "صيام" in cat or "صوم" in cat or "اعتكاف" in cat:
        return "كتاب الصيام"
    if "حج" in cat or "عمرة" in cat or "إحرام" in cat or "أضحية" in cat:
        return "كتاب الحج"
    if "نكاح" in cat or "زواج" in cat or "صداق" in cat or "ولاية" in cat:
        return "كتاب النكاح"
    if "طلاق" in cat or "خلع" in cat or "عدة" in cat or "حضانة" in cat or "رضاع" in cat:
        return "كتاب الطلاق"
    if "بيع" in cat or "ربا" in cat or "إجارة" in cat or "شركة" in cat or "رهن" in cat:
        return "كتاب البيوع"
    if "فرائض" in cat or "ميراث" in cat or "وصية" in cat:
        return "كتاب الفرائض"
    if "قضاء" in cat or "شهادة" in cat:
        return "كتاب القضاء"
    if "حد" in cat or "قصاص" in cat or "دية" in cat:
        return "كتاب الحدود"

    return "كتب متفرقة"


# Load all seed files
_loaded_modules = []
_seed_files = set(SEED_DIR.glob("seed_*comparisons*.py")) | set(SEED_DIR.glob("seed_*part*.py"))
for seed_file in sorted(_seed_files):
    module_name = seed_file.stem
    try:
        mod = importlib.import_module(module_name)
        _loaded_modules.append(module_name)

        # Try all known data list names
        for list_name in DATA_LIST_NAMES:
            data_list = getattr(mod, list_name, None)
            if data_list and isinstance(data_list, list):
                for masala in data_list:
                    key = masala.get("masala_key", "")
                    if key and key not in _seen_keys:
                        _seen_keys.add(key)
                        # Tag with kitab
                        masala["_kitab"] = _detect_kitab(masala, module_name)
                        ALL_MASAIL.append(masala)
    except Exception as e:
        print(f"Warning: Failed to load {module_name}: {e}")

# ---------------------------------------------------------------------------
# Build indexes
# ---------------------------------------------------------------------------
MASAIL_BY_KEY = {m["masala_key"]: m for m in ALL_MASAIL}

# kitab -> list of masail
KUTUB = defaultdict(list)
for m in ALL_MASAIL:
    KUTUB[m["_kitab"]].append(m)

# category (bab) -> list of masail
ABWAB = defaultdict(list)
for m in ALL_MASAIL:
    ABWAB[m["category"]].append(m)

# Ordered bab names per kitab
ABWAB_PER_KITAB = defaultdict(list)
_seen_bab_per_kitab = defaultdict(set)
for m in ALL_MASAIL:
    kitab = m["_kitab"]
    bab = m["category"]
    if bab not in _seen_bab_per_kitab[kitab]:
        _seen_bab_per_kitab[kitab].add(bab)
        ABWAB_PER_KITAB[kitab].append(bab)

# Kitab order (preserve insertion order)
KITAB_ORDER = []
_seen_kitab = set()
for m in ALL_MASAIL:
    if m["_kitab"] not in _seen_kitab:
        _seen_kitab.add(m["_kitab"])
        KITAB_ORDER.append(m["_kitab"])


def _count_results(masail_list):
    counts = {"ittifaq": 0, "ikhtilaf": 0, "tafsilat": 0}
    for m in masail_list:
        r = m.get("comparison", {}).get("result", "")
        if r in counts:
            counts[r] += 1
    return counts


def _kitab_key(name):
    for kw, full in KITAB_NAMES.items():
        if full == name:
            return kw
    return name.replace(" ", "_")


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(title="Maliki Fiqh Review", docs_url="/docs")


@app.get("/api/kutub")
def list_kutub():
    result = []
    for kitab_name in KITAB_ORDER:
        masail = KUTUB[kitab_name]
        counts = _count_results(masail)
        result.append({
            "kitab": kitab_name,
            "kitab_key": _kitab_key(kitab_name),
            "masail_count": len(masail),
            "abwab_count": len(ABWAB_PER_KITAB[kitab_name]),
            **counts,
        })
    return result


@app.get("/api/kutub/{kitab_key}/abwab")
def list_abwab(kitab_key: str):
    kitab_name = KITAB_NAMES.get(kitab_key, kitab_key)
    result = []
    for bab_name in ABWAB_PER_KITAB.get(kitab_name, []):
        masail = [m for m in ABWAB[bab_name] if m["_kitab"] == kitab_name]
        counts = _count_results(masail)
        result.append({
            "bab": bab_name,
            "masail_count": len(masail),
            **counts,
        })
    return result


@app.get("/api/kutub/{kitab_key}/masail")
def list_masail(kitab_key: str, bab: Optional[str] = Query(None)):
    kitab_name = KITAB_NAMES.get(kitab_key, kitab_key)
    if bab:
        source = [m for m in ABWAB.get(bab, []) if m["_kitab"] == kitab_name]
    else:
        source = KUTUB.get(kitab_name, [])
    return [
        {
            "masala_key": m["masala_key"],
            "title_ar": m["title_ar"],
            "category": m["category"],
            "result": m.get("comparison", {}).get("result", ""),
            "summary_ar": m.get("comparison", {}).get("summary_ar", ""),
            "positions_count": len(m.get("positions", [])),
        }
        for m in source
    ]


@app.get("/api/masail/{masala_key}")
def get_masala(masala_key: str):
    m = MASAIL_BY_KEY.get(masala_key)
    if not m:
        return {"error": "Not found"}
    return {k: v for k, v in m.items() if k != "_kitab"}


@app.get("/api/search")
def search_masail(q: str = Query("")):
    if not q.strip():
        return []
    results = []
    for m in ALL_MASAIL:
        searchable = " ".join([
            m.get("title_ar", ""),
            m.get("comparison", {}).get("summary_ar", ""),
            m.get("comparison", {}).get("details_ar", ""),
        ] + [p.get("hukm_text_ar", "") for p in m.get("positions", [])])
        if q.strip() in searchable:
            results.append({
                "masala_key": m["masala_key"],
                "title_ar": m["title_ar"],
                "category": m["category"],
                "kitab": m["_kitab"],
                "result": m.get("comparison", {}).get("result", ""),
                "summary_ar": m.get("comparison", {}).get("summary_ar", ""),
                "positions_count": len(m.get("positions", [])),
            })
    return results


@app.get("/api/stats")
def get_stats():
    total_positions = sum(len(m.get("positions", [])) for m in ALL_MASAIL)
    counts = _count_results(ALL_MASAIL)

    bab_stats = {}
    for bab_name, masail in ABWAB.items():
        bab_stats[bab_name] = {"masail_count": len(masail), **_count_results(masail)}

    book_counts = defaultdict(int)
    hukm_counts = defaultdict(int)
    for m in ALL_MASAIL:
        for p in m.get("positions", []):
            book_counts[p.get("book", "غير محدد")] += 1
            h = p.get("hukm") or "غير محدد"
            hukm_counts[h] += 1

    kitab_stats = {}
    for kitab_name in KITAB_ORDER:
        masail = KUTUB[kitab_name]
        kitab_stats[kitab_name] = {"masail_count": len(masail), **_count_results(masail)}

    return {
        "total_masail": len(ALL_MASAIL),
        "total_positions": total_positions,
        "result_counts": counts,
        "kitab_stats": kitab_stats,
        "bab_stats": bab_stats,
        "book_counts": dict(book_counts),
        "hukm_counts": dict(hukm_counts),
    }


# Feedback router
from fiqh_feedback import router as feedback_router
app.include_router(feedback_router)

# Serve static files
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    print(f"Loaded {len(ALL_MASAIL)} masail from {len(_loaded_modules)} seed files")
    print(f"Kutub: {', '.join(f'{k} ({len(v)})' for k, v in KUTUB.items())}")
    print(f"Starting server at http://localhost:8765")
    uvicorn.run(app, host="0.0.0.0", port=8765)
