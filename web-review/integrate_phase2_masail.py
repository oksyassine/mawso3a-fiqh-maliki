#!/usr/bin/env python3
"""
Integrate Phase 2 Unified Masail into Web Review App.

1. Load tahara_phase2_cross_reference.json (9 unified masail)
2. Convert to web app format
3. Create seed_tahara_phase2_unified.py
4. Update muwatta seed with new hukm enrichments
5. Sync to web server
"""

import json
from pathlib import Path
from typing import List, Dict

# Paths
PHASE2_FILE = Path(__file__).parent.parent / "extracts" / "tahara_phase2_cross_reference.json"
MUWATTA_HUKM_FILE = Path(__file__).parent.parent / "extracts" / "muwatta_tahara_db_only_with_hukm.json"
SEED_OUTPUT = Path(__file__).parent / "backend" / "data" / "seed" / "seed_tahara_phase2_unified.py"
MUWATTA_SEED_UPDATE = Path(__file__).parent / "backend" / "data" / "seed" / "seed_muwatta_masail.py"

def load_phase2_unified():
    """Load Phase 2 unified masail."""
    with open(PHASE2_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_muwatta_hukm():
    """Load muwatta with hukm enrichments."""
    with open(MUWATTA_HUKM_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_unified_to_seed_format(unified_masail):
    """Convert Phase 2 unified masail to web app format."""
    seed_data = []

    for masala in unified_masail['unified_masail']:
        # Calculate tawafoq and khalif info
        tawafoq = masala['tawafoq_percentage']
        khalif_info = ""
        if masala['khalif']:
            khalif_scholars = []
            for k in masala['khalif']:
                khalif_scholars.append(f"{k['hukm']}: {', '.join(k['scholars'])}")
            khalif_info = " | ".join(khalif_scholars)

        # Build scholar positions text
        positions = []
        for pos in masala['scholar_positions']:
            positions.append({
                'book': pos['book'],
                'speaker': pos['speaker'],
                'hukm': pos['hukm'],
                'hukm_source': pos['hukm_source'],
                'text_preview': pos['text_preview'],
                'shamela_link': pos['shamela_link'],
                'masala_id': pos['full_masala_id'],
                'page_id': pos['page_id']
            })

        # Determine result type
        if tawafoq >= 90:
            result_type = "ittifaq"
            result_text = f"إجماع {tawafoq:.1f}%"
        elif tawafoq >= 70:
            result_type = "tafsilat"
            result_text = f"تفصيل {tawafoq:.1f}%"
        else:
            result_type = "ikhtilaf"
            result_text = f"خلاف {tawafoq:.1f}%"

        seed_entry = {
            'masala_key': masala['unified_masala_id'],
            'title_ar': masala['topic'],
            'category': 'موحد - ' + masala['topic'],
            'comparison': {
                'result': result_type,
                'summary_ar': masala['consensus_text'][:200],
                'details_ar': f"إجماع على {masala['consensus_hukm']} بنسبة {tawafoq:.1f}%" + (f"\nخلاف: {khalif_info}" if khalif_info else ""),
                'tawafoq_percentage': tawafoq,
                'khalif_summary': khalif_info
            },
            'positions': positions,
            'tafsil': masala['tafsil_summary'],
            'source': 'Phase 2 Cross-Reference',
            'entries_count': masala['entries_count']
        }

        seed_data.append(seed_entry)

    return seed_data

def create_seed_file(seed_data):
    """Create seed_tahara_phase2_unified.py file."""
    # Ensure directory exists
    SEED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Generate Python code
    code = '''"""
Phase 2 Unified Cross-Reference Masail for كتاب الطهارة.

Created from fuzzy topic matching with consensus extraction.
Each entry includes:
- Consensus text (ما اتفق عليه العلماء)
- Tawafoq % (agreement percentage)
- Khalif (disagreements with scholar attribution)
- Tafsil (detailed conditions per scholar)
- Scholar positions with Shamela links
"""

TAHARA_PHASE2_DATA = '''

    code += repr(seed_data)
    code += '\n'

    with open(SEED_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"✓ Created: {SEED_OUTPUT}")
    print(f"  Generated {len(seed_data)} unified masail entries")

def create_muwatta_seed_with_hukm(muwatta_data):
    """Create/update muwatta seed file with hukm enrichments."""
    muwatta_seed = Path(__file__).parent / "backend" / "data" / "seed" / "seed_muwatta_masail.py"
    muwatta_seed.parent.mkdir(parents=True, exist_ok=True)

    # Convert muwatta data to seed format
    seed_data = []

    for bab in muwatta_data['abwab']:
        bab_name = bab['bab_name']

        for hadith in bab.get('hadiths', []):
            seed_entry = {
                'masala_key': f"muwatta_hadith_{hadith.get('hadith_num')}",
                'title_ar': f"حديث {hadith.get('hadith_num')} - {bab_name}",
                'category': bab_name,
                'comparison': {
                    'result': 'ittifaq',  # Muwatta is source
                    'summary_ar': hadith['text'][:150],
                    'hukm': hadith.get('hukm', 'jaiz'),
                    'hukm_source': hadith.get('hukm_source', ''),
                },
                'positions': [{
                    'book': 'الموطأ',
                    'speaker': 'مالك',
                    'hukm': hadith.get('hukm', 'jaiz'),
                    'hukm_source': hadith.get('hukm_source', ''),
                    'text_preview': hadith['text'][:100],
                    'page_id': hadith.get('page_id'),
                    'shamela_link': f"shamela.ws/book/1699/{hadith.get('page_id', 0) - 1 if hadith.get('page_id') else 0}"
                }],
                'source': 'الموطأ (Updated with Hukm)',
            }
            seed_data.append(seed_entry)

    # Generate Python code
    code = '''"""
Updated Muwatta Masail with Hukm Enrichments.

Extracted from shamela_v4.db with semantic hukm extraction.
Each hadith now includes:
- Extracted hukm (ruling type)
- Hukm source (how it was determined)
- Full diacritics preserved
"""

MUWATTA_DATA = '''

    code += repr(seed_data)
    code += '\n'

    with open(MUWATTA_SEED_UPDATE, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"✓ Updated: {MUWATTA_SEED_UPDATE}")
    print(f"  Updated {len(seed_data)} muwatta entries with hukm enrichments")

def sync_to_server():
    """Instructions for syncing to server."""
    print("\n" + "=" * 80)
    print("SYNC TO SERVER")
    print("=" * 80)
    print("""
The web review app will auto-discover the new seed files.

To deploy to server (quran.learn.nucleuselmers.org/fiqh/):

1. SSH to server:
   ssh user@quran.learn.nucleuselmers.org

2. Navigate to mawso3a fiqh app:
   cd /home/app/mawso3a-fiqh-maliki/web-review

3. Copy seed files:
   cp backend/data/seed/seed_tahara_phase2_unified.py .
   cp backend/data/seed/seed_muwatta_masail.py .

4. Restart app (or it auto-reloads on next request)

5. Access web UI:
   https://quran.learn.nucleuselmers.org/fiqh/

The unified masail will appear in:
  - "Masail Home" → "كتاب الطهارة" (will show Phase 2 entries)
  - Search will include all new entries
  - Each entry shows: consensus, tawafoq %, khalif, tafsil, scholar positions
""")

def main():
    print("=" * 80)
    print("INTEGRATING PHASE 2 UNIFIED MASAIL INTO WEB REVIEW APP")
    print("=" * 80 + "\n")

    # Load data
    print("Loading Phase 2 unified masail...")
    phase2_data = load_phase2_unified()
    print(f"✓ Loaded {len(phase2_data['unified_masail'])} unified masail\n")

    print("Loading muwatta with hukm enrichments...")
    muwatta_data = load_muwatta_hukm()
    total_hadiths = sum(len(bab.get('hadiths', [])) for bab in muwatta_data['abwab'])
    print(f"✓ Loaded {total_hadiths} muwatta hadiths with hukm\n")

    # Convert and create seed files
    print("Converting Phase 2 unified masail to seed format...")
    seed_format = convert_unified_to_seed_format(phase2_data)

    print("Creating seed file for unified masail...")
    create_seed_file(seed_format)

    print("\nCreating seed file for updated muwatta with hukm...")
    create_muwatta_seed_with_hukm(muwatta_data)

    # Sync instructions
    sync_to_server()

    print("\n" + "=" * 80)
    print("✓ INTEGRATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
