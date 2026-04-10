#!/usr/bin/env python3
"""Build كتاب الطهارة from v4 — proper semantic analysis."""

import json, re, unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def strip_d(text):
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def derive_topic(bab_name):
    """Derive clean masala_topic from bab name — strip only باب prefix."""
    t = bab_name.strip()
    for p in [r'^هَذَا بَابٌ فِي\s+', r'^بَابُ\s+', r'^بَابِ\s+']:
        t_new = re.sub(p, '', t)
        if t_new != t:
            t = t_new
            break
    t = strip_d(t)
    return re.sub(r'\.\s*', ' - ', t).strip(' -')

with open(BASE / 'extracts/muwatta_tahara_db_only_with_hukm.json', 'r') as f:
    v4 = json.load(f)


def classify_entry(text):
    plain = strip_d(text)
    if re.match(r'^(?:و?)?قال يحيى', plain):
        return 'قول مالك'
    if 'رسول الله' in plain[:300] and re.search(r'رسول الله.*?(قال|يقول|أمر|نهى|فعل|صلى|توضأ|أكل|غسل)', plain[:400]):
        return 'حديث'
    return 'أثر'


def extract_narrator_chain(text):
    """Full narrator chain from text (between 'عن مالك' and matn start)."""
    plain = strip_d(text)
    if plain.startswith('قال يحيى'):
        return 'مالك'
    
    # Full chain after عن مالك
    m = re.search(r'عن\s+مالك\S*\s*[،,]?\s*عن\s+(.+?)(?:\s+أن(?:ه|ها)?\s|\s+أن\s+رسول)', plain[:350])
    if m:
        return m.group(1).strip().rstrip('،, ')
    
    # Balagh pattern: عن مالك أنه بلغه أن NAME
    m = re.search(r'عن\s+مالك\S*\s+أنه\s+بلغه[،,]?\s+أن\s+(.+?)(?:\s+كان|\s+قد|\s+دخل)', plain[:300])
    if m:
        return m.group(1).strip().rstrip('،, ')
    
    # عن مالك عن نافع أن...
    m = re.search(r'عن\s+مالك\S*\s*[،,]?\s*عن\s+(\S+(?:\s+\S+){0,4})', plain[:200])
    if m:
        return m.group(1).strip().rstrip('،, ')
    
    return ''


def extract_malik_ruling(text):
    """Extract Malik's actual words from قول مالك entry, stripping يحيى wrapper."""
    plain = strip_d(text)
    
    # Pattern 1: قال يحيى: سمعت مالكاً يقول CONTENT
    m = re.search(r'(?:يقول|مالك\S*\s*[:\s]*«?)(.+)', plain, re.DOTALL)
    if m:
        content = m.group(1).strip().lstrip('«": ')
        # Find this in original diacritized text
        search = content[:30]
        pos = strip_d(text).find(search)
        if pos >= 0:
            # Map to original position
            count = 0
            for i, c in enumerate(text):
                if unicodedata.category(c) != 'Mn':
                    if count == pos:
                        result = text[i:].strip().lstrip('«": ')
                        # Ensure ends at word boundary
                        return result
                    count += 1
    
    # Pattern 2: سئل مالك عن... فقال: «CONTENT»
    m = re.search(r'فقال\s*[:\s]*[«"](.+?)(?:[»"]|$)', plain, re.DOTALL)
    if m:
        return m.group(1).strip()
    
    return plain  # Fallback: return full text


def extract_summary(text, entry_type, max_len=90):
    """Extract meaningful summary from text content."""
    plain = strip_d(text)
    
    if entry_type == 'قول مالك':
        ruling = extract_malik_ruling(text)
        ruling_plain = strip_d(ruling)
        if len(ruling_plain) > max_len:
            sp = ruling_plain[:max_len].rfind(' ')
            return ruling_plain[:sp] if sp > max_len//2 else ruling_plain[:max_len]
        return ruling_plain
    
    # For hadith: find the Prophet's actual statement
    m = re.search(r'ﷺ[^«]*?[«:]\s*(.{15,})', plain)
    if m:
        s = m.group(1).strip().lstrip('«"')
        if len(s) > max_len:
            sp = s[:max_len].rfind(' ')
            return s[:sp] if sp > max_len//2 else s[:max_len]
        return s
    
    # For hadith without «»: Prophet did/said
    m = re.search(r'ﷺ\s+(.{15,100})', plain)
    if m:
        s = m.group(1).strip()
        if len(s) > max_len:
            sp = s[:max_len].rfind(' ')
            return s[:sp] if sp > max_len//2 else s[:max_len]
        return s
    
    # For athar: companion's statement/action
    m = re.search(r'(?:كان|قال)\s*[:\s]*[«"]?(.{15,100})', plain[30:])
    if m:
        s = m.group(1).strip().lstrip('«"')
        if 'حدثني' not in s[:15] and 'عن مالك' not in s[:15]:
            if len(s) > max_len:
                sp = s[:max_len].rfind(' ')
                return s[:sp] if sp > max_len//2 else s[:max_len]
            return s
    
    # Fallback
    mid = len(plain) // 3
    s = plain[mid:mid+max_len]
    sp = s.rfind(' ')
    return s[:sp] if sp > 20 else s[:max_len]


def extract_tags(bab_name, all_text):
    combined = strip_d(bab_name + ' ' + all_text[:600])
    TAG_MAP = {
        'وضوء': 'وضوء', 'الوضوء': 'وضوء', 'توضأ': 'وضوء',
        'طهارة': 'طهارة', 'الطهارة': 'طهارة', 'طهور': 'طهارة',
        'غسل': 'غسل', 'الغسل': 'غسل', 'اغتسل': 'غسل',
        'نجاس': 'نجاسة', 'نجس': 'نجاسة',
        'ماء': 'ماء', 'الماء': 'ماء', 'البحر': 'ماء',
        'استنجاء': 'استنجاء', 'حجار': 'استنجاء',
        'تيمم': 'تيمم', 'صعيد': 'تيمم',
        'حيض': 'حيض', 'مستحاضة': 'حيض', 'استحاضة': 'حيض',
        'جنب': 'جنابة', 'جنابة': 'جنابة',
        'خف': 'مسح الخفين', 'الخفين': 'مسح الخفين',
        'سواك': 'سواك',
        'نوم': 'نواقض', 'رعاف': 'نواقض', 'حدث': 'نواقض',
        'مضمض': 'مضمضة', 'استنثر': 'استنثار',
        'صلاة': 'صلاة', 'الصلاة': 'صلاة',
        'مسح': 'مسح',
    }
    tags = set(['طهارة'])
    for kw, tag in TAG_MAP.items():
        if kw in combined:
            tags.add(tag)
    return sorted(tags)


def build_hukm(all_hadiths, bab_name):
    """Build hukm by collecting ALL Malik rulings found in the bab's texts."""
    rulings = []
    
    for h in all_hadiths:
        plain = strip_d(h['text'])
        
        # 1. Explicit قول مالك entries
        if classify_entry(h['text']) == 'قول مالك':
            ruling = strip_d(extract_malik_ruling(h['text']))
            if ruling and len(ruling) > 10:
                rulings.append(ruling)
            continue
        
        # 2. Embedded "قال مالك:" within hadith/athar texts
        for m in re.finditer(r'قال\s*(?:يحيى\s*[:\s]*)?(?:قال\s*)?مالك\S*\s*[:\s]+[«"]?(.+?)(?:[»"]|$)', plain):
            r = m.group(1).strip()
            if len(r) > 10:
                rulings.append(r)
    
    # 3. If no Malik ruling, extract Prophet's commands from hadiths
    if not rulings:
        for h in all_hadiths:
            plain = strip_d(h['text'])
            # Prophet commands
            for m in re.finditer(r'ﷺ.*?(?:قال|يقول)\s*[:\s]*[«"](.+?)(?:[»"]|$)', plain):
                r = m.group(1).strip()
                if len(r) > 10 and len(r) < 200:
                    rulings.append(r)
                    break
    
    return '\n'.join(rulings[:5])


# === BUILD ===
masail = []

for bab in v4['abwab']:
    bab_name = bab['bab_name']
    hadiths = bab.get('hadiths', [])
    
    dalil_entries = []
    qawl_entries_clean = []
    all_text = ""
    
    for h in hadiths:
        text = h['text']
        pid = h.get('page_id')
        hnum = h.get('hadith_num')
        entry_type = classify_entry(text)
        all_text += strip_d(text) + " "
        
        if entry_type == 'قول مالك':
            ruling = extract_malik_ruling(text)
            qawl_entries_clean.append(ruling)
        else:
            narrator = extract_narrator_chain(text)
            summary = extract_summary(text, entry_type)
            
            dalil_entries.append({
                "type": entry_type,
                "num": hnum,
                "narrator": narrator,
                "summary": summary,
                "full_text": text,
                "page_id": pid,
                "shamela_url": f"https://shamela.ws/book/1699/{pid}" if pid else "",
            })
    
    hukm = build_hukm(hadiths, bab_name)
    tags = extract_tags(bab_name, all_text)
    
    masail.append({
        "masala_id": f"muwatta_tahara_{len(masail)+1:03d}",
        "bab": bab_name,
        "bab_num": len(masail) + 1,
        "masala_topic": derive_topic(bab_name),
        "hukm": hukm,
        "rulings": [{"speaker": "مالك", "text": t} for t in qawl_entries_clean],
        "dalil": dalil_entries,
        "fiqh_tags": tags,
        "sub_masail": [],
    })

output = {
    "kitab": "كتاب الطهارة",
    "kitab_num": 3,
    "book_key": "book_01",
    "source": "الموطأ - رواية يحيى الليثي",
    "extracted_at": "2026-04-10",
    "data_source": "shamela_v4.db",
    "masail": masail,
}

out = BASE / 'data/masail/book_01/extracted/kitab_03_tahara.json'
# SAFEGUARD: This script creates 32 base masail (1 per bab).
# Run split_muwatta_masail.py AFTER this to get the 49-masail golden model.
with open(out, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("⚠ WARNING: Run split_muwatta_masail.py next to restore 49-masail golden model!")

th = sum(1 for m in masail for d in m['dalil'] if d['type'] == 'حديث')
ta = sum(1 for m in masail for d in m['dalil'] if d['type'] == 'أثر')
tr = sum(len(m['rulings']) for m in masail)
wh = sum(1 for m in masail if m['hukm'])
print(f"✓ {len(masail)} masail | {th} حديث | {ta} أثر | {tr} rulings | {wh}/{len(masail)} with hukm")
