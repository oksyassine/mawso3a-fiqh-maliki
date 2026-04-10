#!/usr/bin/env python3
"""
Integrate Phase 2 & Phase 1 Data into Web Review App.

1. Load Phase 2 unified masail from tahara_phase2_cross_reference.json
2. Load updated muwatta with hukm enrichments
3. Create JSON files in static/ for web app to load
4. Update app.js to display consensus, tawafoq %, khalif, tafsil
"""

import json
from pathlib import Path

# Paths
PHASE2_FILE = Path(__file__).parent.parent / "extracts" / "tahara_phase2_cross_reference.json"
MUWATTA_HUKM_FILE = Path(__file__).parent.parent / "extracts" / "muwatta_tahara_db_only_with_hukm.json"
STATIC_DIR = Path(__file__).parent / "static"

def load_phase2_unified():
    """Load Phase 2 unified masail."""
    with open(PHASE2_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_muwatta_hukm():
    """Load muwatta with hukm enrichments."""
    with open(MUWATTA_HUKM_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_unified_to_web_format(unified_data):
    """Convert Phase 2 unified masail to web app display format."""
    masail_list = []

    for masala in unified_data['unified_masail']:
        # Determine consensus/agreement/disagreement type
        tawafoq = masala['tawafoq_percentage']
        if tawafoq >= 90:
            agreement_type = "إجماع"
        elif tawafoq >= 70:
            agreement_type = "تفصيل"
        else:
            agreement_type = "خلاف"

        # Build khalif summary
        khalif_text = ""
        if masala['khalif']:
            khalif_points = []
            for k in masala['khalif']:
                scholars = ", ".join(k['scholars'])
                khalif_points.append(f"{k['hukm']}: {scholars}")
            khalif_text = " | ".join(khalif_points)

        # Build tafsil summary
        tafsil_text = ""
        if masala['tafsil_summary']:
            tafsil_points = []
            for t in masala['tafsil_summary']:
                tafsil_points.append(f"{t['speaker']} ({t['book']}): {', '.join(t.get('conditions', []))[:100]}")
            tafsil_text = " | ".join(tafsil_points[:3])  # First 3 only

        masail_list.append({
            'id': masala['unified_masala_id'],
            'topic': masala['topic'],
            'books': masala['books_covered'],
            'consensus_text': masala['consensus_text'],
            'consensus_hukm': masala['consensus_hukm'],
            'tawafoq_percentage': tawafoq,
            'agreement_type': agreement_type,
            'khalif_summary': khalif_text,
            'tafsil_summary': tafsil_text,
            'scholar_positions': masala['scholar_positions'],
            'full_data': masala  # Include full data for detailed view
        })

    return masail_list

def convert_muwatta_to_web_format(muwatta_data):
    """Convert muwatta with hukm to web display format."""
    masail_list = []

    for bab_idx, bab in enumerate(muwatta_data['abwab']):
        for hadith_idx, hadith in enumerate(bab.get('hadiths', [])):
            masail_list.append({
                'id': f"muwatta_{bab_idx}_{hadith_idx}",
                'hadith_num': hadith.get('hadith_num'),
                'bab': bab['bab_name'],
                'narrator': hadith.get('narrator', ''),
                'text': hadith['text'],
                'hukm': hadith.get('hukm', 'jaiz'),
                'hukm_source': hadith.get('hukm_source', ''),
                'page_id': hadith.get('page_id'),
                'shamela_link': f"shamela.ws/book/1699/{hadith.get('page_id', 1) - 1 if hadith.get('page_id') else 0}"
            })

    return masail_list

def create_web_files():
    """Create JSON files for web app."""
    print("Converting Phase 2 unified masail...")
    phase2_data = load_phase2_unified()
    unified_web = convert_unified_to_web_format(phase2_data)

    print("Converting muwatta with hukm enrichments...")
    muwatta_data = load_muwatta_hukm()
    muwatta_web = convert_muwatta_to_web_format(muwatta_data)

    # Save files
    STATIC_DIR.mkdir(exist_ok=True)

    unified_file = STATIC_DIR / "tahara-unified-masail.json"
    with open(unified_file, 'w', encoding='utf-8') as f:
        json.dump(unified_web, f, ensure_ascii=False, indent=2)
    print(f"✓ Created: {unified_file}")
    print(f"  {len(unified_web)} unified masail entries")

    muwatta_file = STATIC_DIR / "muwatta-masail-updated.json"
    with open(muwatta_file, 'w', encoding='utf-8') as f:
        json.dump(muwatta_web, f, ensure_ascii=False, indent=2)
    print(f"✓ Created: {muwatta_file}")
    print(f"  {len(muwatta_web)} muwatta hadiths with hukm")

    # Create index for all tahara masail
    all_tahara_masail = {
        'unified': unified_web,
        'muwatta': muwatta_web,
        'total_unified': len(unified_web),
        'total_muwatta': len(muwatta_web),
        'average_tawafoq': phase2_data['average_tawafoq_percentage']
    }

    tahara_index = STATIC_DIR / "tahara-masail-index.json"
    with open(tahara_index, 'w', encoding='utf-8') as f:
        json.dump(all_tahara_masail, f, ensure_ascii=False, indent=2)
    print(f"✓ Created: {tahara_index}")

def create_web_ui_update():
    """Create JavaScript snippet for web UI to display new fields."""
    js_code = '''
// Phase 2 Web UI Update
// Add to app.js to display consensus, tawafoq %, khalif, tafsil

function displayUnifiedMasala(masala) {
    const html = `
        <div class="unified-masala">
            <h3>${masala.topic}</h3>
            <div class="agreement-badge ${masala.agreement_type}">
                ${masala.agreement_type} ${masala.tawafoq_percentage.toFixed(1)}%
            </div>

            <section class="consensus">
                <h4>ما اتفق عليه العلماء</h4>
                <p>${masala.consensus_text}</p>
                <strong>الحكم الموحد:</strong> ${masala.consensus_hukm}
            </section>

            ${masala.khalif_summary ? `
                <section class="khalif">
                    <h4>نقاط الخلاف</h4>
                    <p>${masala.khalif_summary}</p>
                </section>
            ` : ''}

            ${masala.tafsil_summary ? `
                <section class="tafsil">
                    <h4>التفصيلات</h4>
                    <p>${masala.tafsil_summary}</p>
                </section>
            ` : ''}

            <section class="scholar-positions">
                <h4>مواقف العلماء</h4>
                <table>
                    <thead>
                        <tr>
                            <th>الكتاب</th>
                            <th>الحكم</th>
                            <th>المصدر</th>
                            <th>الرابط</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${masala.scholar_positions.map(pos => `
                            <tr>
                                <td>${pos.book}</td>
                                <td>${pos.hukm}</td>
                                <td>${pos.hukm_source}</td>
                                <td>
                                    <a href="${pos.shamela_link}" target="_blank">
                                        Shamela ↗
                                    </a>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </section>
        </div>
    `;
    return html;
}

// CSS for unified masala display
const styles = `
.unified-masala {
    border: 2px solid #4CAF50;
    padding: 1.5rem;
    margin: 1rem 0;
    border-radius: 8px;
    background: #f9f9f9;
}

.agreement-badge {
    display: inline-block;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-weight: bold;
    margin: 0.5rem 0;
}

.agreement-badge.إجماع {
    background: #4CAF50;
    color: white;
}

.agreement-badge.تفصيل {
    background: #FF9800;
    color: white;
}

.agreement-badge.خلاف {
    background: #f44336;
    color: white;
}

.unified-masala section {
    margin: 1rem 0;
    padding: 1rem;
    background: white;
    border-radius: 4px;
}

.unified-masala table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.unified-masala th, .unified-masala td {
    padding: 0.5rem;
    text-align: right;
    border-bottom: 1px solid #ddd;
}

.unified-masala th {
    background: #f5f5f5;
    font-weight: bold;
}
`;
'''

    ui_file = Path(__file__).parent / "static" / "phase2-ui-update.js"
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(js_code)
    print(f"\n✓ Created: {ui_file}")
    print("  Include this in app.html for Phase 2 UI support")

def main():
    print("=" * 80)
    print("INTEGRATING PHASE 2 DATA INTO WEB REVIEW APP")
    print("=" * 80 + "\n")

    create_web_files()
    create_web_ui_update()

    print("\n" + "=" * 80)
    print("INTEGRATION COMPLETE")
    print("=" * 80)
    print("""
Next steps:

1. Update app.html to load new JSON files:
   - tahara-unified-masail.json (Phase 2 cross-reference)
   - muwatta-masail-updated.json (Muwatta with hukm)
   - tahara-masail-index.json (Combined index)

2. Add Phase 2 UI elements:
   - Display consensus text
   - Show tawafoq % with color-coded badge
   - Display khalif (disagreements)
   - Show tafsil (detailed conditions)
   - Create scholar positions table with Shamela links

3. Update search to include all new fields

4. Deploy to server:
   cp static/*.json /home/app/mawso3a-fiqh-maliki/web-review/static/
   cp static/phase2-ui-update.js /home/app/mawso3a-fiqh-maliki/web-review/static/

5. Access at:
   https://quran.learn.nucleuselmers.org/fiqh/
""")

if __name__ == '__main__':
    main()
