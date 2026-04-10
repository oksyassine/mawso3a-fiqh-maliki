#!/usr/bin/env python3
"""
Create web JSON files for all مصنفات from extracted masail.
Reads from data/masail/{book_key}/extracted/ and outputs to web-review/static/.
"""

import json
from pathlib import Path
from collections import OrderedDict

BASE = Path(__file__).resolve().parent.parent
MASAIL_DIR = BASE / "data" / "masail"
STATIC = BASE / "web-review" / "static"
STATIC.mkdir(parents=True, exist_ok=True)

BOOK_CONFIG = {
    'book_01': {
        'file': 'kitab_03_tahara.json',
        'output': 'muwatta-masail.json',
        'source': 'الموطأ - رواية يحيى الليثي',
        'author': 'الإمام مالك بن أنس',
        'shamela_id': 1699,
    },
    'book_02': {
        'file': 'kitab_tahara.json',
        'output': 'mudawwana-masail.json',
        'source': 'المدونة الكبرى',
        'author': 'سحنون (عن ابن القاسم عن مالك)',
        'shamela_id': 587,
    },
    'book_15': {
        'file': 'kitab_tahara.json',
        'output': 'risala-masail.json',
        'source': 'الرسالة',
        'author': 'ابن أبي زيد القيرواني (310-386هـ)',
        'shamela_id': 11373,
    },
    'book_45': {
        'file': 'kitab_tahara.json',
        'output': 'khalil-masail.json',
        'source': 'مختصر خليل',
        'author': 'خليل بن إسحاق الجندي (ت 776هـ)',
        'shamela_id': 11355,
    },
}


def build_web_json(book_key, config):
    """Read extracted masail and produce web-ready JSON."""
    src = MASAIL_DIR / book_key / "extracted" / config['file']
    if not src.exists():
        print(f"⚠ {src} not found, skipping")
        return

    with open(src, 'r', encoding='utf-8') as f:
        data = json.load(f)

    masail = data.get('masail', [])

    # Group masail by bab
    bab_groups = OrderedDict()
    for m in masail:
        bab_key = (m.get('bab_num', 0), m.get('bab', ''))
        if bab_key not in bab_groups:
            bab_groups[bab_key] = []
        bab_groups[bab_key].append(m)

    abwab = []
    for (bab_num, bab_name), bab_masail in bab_groups.items():
        abwab.append({
            'bab_num': bab_num,
            'bab_name': bab_name,
            'masail': bab_masail,
        })

    output = {
        'source': config['source'],
        'author': config['author'],
        'edition': 'نص المكتبة الشاملة — مستخرج من shamela_v4.db',
        'book_key': book_key,
        'shamela_id': config['shamela_id'],
        'extracted_at': data.get('extracted_at', '2026-04-10'),
        'kutub': [{
            'kitab_num': data.get('kitab_num', 1),
            'kitab_name': data.get('kitab', 'كتاب الطهارة'),
            'masail_count': len(masail),
            'sub_masail_count': sum(len(m.get('sub_masail', [])) for m in masail),
            'abwab': abwab,
        }],
    }

    out = STATIC / config['output']
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total_dalil = sum(len(m.get('dalil', [])) for m in masail)
    total_rulings = sum(len(m.get('rulings', [])) for m in masail)
    print(f"✓ {out.name}: {len(masail)} masail | {len(abwab)} أبواب | {total_dalil} dalil | {total_rulings} rulings")


if __name__ == '__main__':
    print("إنشاء ملفات البيانات...\n")
    for book_key, config in BOOK_CONFIG.items():
        build_web_json(book_key, config)
    print("\nتم!")
