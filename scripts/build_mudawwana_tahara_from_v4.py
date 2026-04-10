#!/usr/bin/env python3
"""Build المدونة كتاب الطهارة from v4 RAW page text.
Uses the unbroken page text (body field) from db_only extraction.
Identifies Q&A pairs as masala boundaries, extracts rulings and dalil."""

import json, re, unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SHAMELA_ID = 587

def strip_d(text):
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def shamela_url(page_id):
    return f"https://shamela.ws/book/{SHAMELA_ID}/{page_id}" if page_id else ""


# === READ RAW SOURCE ===
with open(BASE / 'extracts/mudawwana_tahara_db_only.json', 'r') as f:
    data = json.load(f)

# كتاب الوضوء = bab 0 (43 pages)
raw_pages = data['abwab'][0]['pages']

# Concatenate ALL pages into one continuous text, tracking page boundaries
full_text = ''
page_map = []  # (char_start, char_end, page_id)
for p in raw_pages:
    body = p['body']
    # Strip ONLY the header brackets at the start of text (e.g. [كتاب الوضوء])
    # Preserve surah references like [المائدة: ٦] and section headers within text
    body = re.sub(r'^\s*\[كِتَابُ[^\]]*\]\s*', '', body)
    body = re.sub(r'^\s*\[مَا جَاءَ[^\]]*\]\s*', '', body)
    body = re.sub(r'^\s*\[جَامِعُ[^\]]*\]\s*', '', body)
    body = re.sub(r'^\s*\[اغْتِسَال[^\]]*\]\s*', '', body)
    body = re.sub(r'^\s*\[مُجَاوَزَة[^\]]*\]\s*', '', body)
    start = len(full_text)
    full_text += body + '\n'
    page_map.append((start, len(full_text), p['page_id']))

def find_page(char_pos):
    """Find which page a character position falls in."""
    for start, end, pid in page_map:
        if start <= char_pos < end:
            return pid
    return raw_pages[-1]['page_id']


# === IDENTIFY Q&A BOUNDARIES ===
# Each "قلت" or "قَالَ سَحْنُونٌ: قُلْتُ" starts a new question
# Also "سئل مالك" and section headers like [ما جاء في...]
plain = strip_d(full_text)

# Find all question markers in the text
qa_markers = []
for pattern in [
    r'قلت\s*(?:لابن القاسم|لعبد الرحمن|له)',
    r'قال سحنون[:\s]+قلت',
    r'سئل مالك',
    r'أرأيت\s',
]:
    for m in re.finditer(pattern, plain):
        # Map back to diacritized text position
        pos = m.start()
        qa_markers.append(pos)

qa_markers = sorted(set(qa_markers))
print(f"Found {len(qa_markers)} Q&A boundaries in {len(full_text)} chars ({len(raw_pages)} pages)")

# === EXTRACT HADITH AND QURAN FROM TEXT ===
def extract_dalil_from_text(text, base_page):
    """Find hadiths, athars, and Quran verses embedded in text."""
    dalil = []
    plain = strip_d(text)

    # Quran verses — find ﴿...﴾ then locate proper start (قال الله etc.)
    for m in re.finditer(r'﴿([^﴾]+)﴾', text):
        # Look backwards for verse introduction
        before = text[max(0, m.start() - 120):m.start()]
        # Find the latest introduction marker before the verse
        best_start = m.start()  # default: start at ﴿
        for intro in ['قَالَ اللَّهُ', 'قال الله', 'قَوْلِ اللَّهِ', 'قوله تعالى',
                       'قَوْلَ اللَّهِ', 'لِقَوْلِ اللَّهِ', 'تَلَا', 'الْآيَةِ:',
                       'الْآيَةَ:', 'هَذِهِ الْآيَةِ:']:
            idx = before.rfind(intro)
            if idx >= 0:
                best_start = max(0, m.start() - 120) + idx
                break

        # Look forward for surah reference [المائدة: ٦] after ﴾
        after = text[m.end():min(len(text), m.end() + 60)]
        end = m.end()
        # Match [SurahName: N] pattern
        ref_match = re.search(r'\[.*?\]', after)
        if ref_match:
            end = m.end() + ref_match.end()
        else:
            # Just include a few chars after ﴾ for context
            end = min(len(text), m.end() + 5)

        verse_text = text[best_start:end].strip()
        dalil.append({
            'type': 'قرآن',
            'full_text': verse_text,
            'page_id': find_page(best_start),
            'shamela_url': shamela_url(find_page(best_start)),
        })

    # Hadiths (رسول الله ﷺ said/did)
    for m in re.finditer(r'رسول الله ﷺ', text):
        start = max(0, m.start() - 80)
        # Find end of hadith (next قال or period)
        end = min(len(text), m.end() + 300)
        p_end = plain[m.end():m.end()+300]
        for stop in ['. قال', '. قلت', '، قال']:
            idx = strip_d(text[m.end():end]).find(strip_d(stop))
            if idx > 20:
                end = m.end() + idx + len(stop)
                break
        hadith_text = text[start:end].strip()
        if len(hadith_text) > 40:
            dalil.append({
                'type': 'حديث',
                'full_text': hadith_text,
                'page_id': find_page(m.start()),
                'shamela_url': shamela_url(find_page(m.start())),
            })

    return dalil


# === EXTRACT RULINGS FROM Q&A ANSWER ===
def extract_rulings(text):
    """Extract مالك and ابن القاسم rulings from answer text."""
    rulings = []
    plain = strip_d(text)

    # قال مالك: ... (direct مالك ruling)
    for m in re.finditer(r'(?:قال|وقال)\s+مالك[^:]*?:\s*(.+?)(?=\.\s*(?:قال|قلت)|$)', plain, re.DOTALL):
        r_text = m.group(1).strip()
        if len(r_text) > 20 and len(r_text) < 500:
            # Find in diacritized text
            start_search = r_text[:30]
            idx = plain.find(start_search)
            if idx >= 0:
                # Get diacritized version
                count = 0
                d_start = 0
                for ci, c in enumerate(text):
                    if unicodedata.category(c) != 'Mn':
                        if count == idx:
                            d_start = ci
                            break
                        count += 1
                d_text = text[d_start:d_start + len(r_text) * 2][:len(r_text)*2]
                # Trim to same plain length
                d_plain = strip_d(d_text)
                if len(d_plain) > len(r_text):
                    target = len(r_text)
                    count = 0
                    for ci, c in enumerate(d_text):
                        if unicodedata.category(c) != 'Mn':
                            count += 1
                            if count >= target:
                                d_text = d_text[:ci+1]
                                break
                rulings.append({
                    'speaker': 'مالك',
                    'text': d_text.strip(),
                    'via': 'ابن القاسم',
                })

    # ابن القاسم reporting مالك: "لم يكن مالك يوقت..."
    for m in re.finditer(r'(?:لم يكن مالك|كان مالك|عند مالك)\s+(.+?)(?=\.\s*(?:قال|قلت)|$)', plain):
        r_text = m.group(0).strip()
        if len(r_text) > 30 and len(r_text) < 400:
            rulings.append({
                'speaker': 'مالك',
                'text': r_text,
                'via': 'ابن القاسم',
            })

    return rulings[:8]  # cap


# === DEFINE MASAIL BY PAGE RANGES (topic groups) ===
# Same topic grouping as before, but now extracting from raw text
MASAIL_DEF = [
    {'pages': (1, 2), 'topic': 'صفة الوضوء وعدد غسلاته',
     'hukm': 'لم يكن مالك يوقت في الوضوء واحدة ولا اثنتين ولا ثلاثا وإنما يتوضأ ويسبغ. وصف وضوء النبي ﷺ من حديث عبد الله بن زيد وعثمان بن عفان. الوضوء مرة مرة يجزئ إذا أسبغ',
     'tags': ['طهارة', 'وضوء', 'غسل']},
    {'pages': (3, 3), 'topic': 'الماء المستعمل والنجس',
     'hukm': 'لا يتوضأ بماء قد توضئ به مرة ولا خير فيه. إن لم يجد غيره توضأ به أحب من التيمم. النخاعة والبصاق في الماء لا بأس بالوضوء منه. خشاش الأرض كالنمل والذباب إذا وقعت في الماء لا بأس به',
     'tags': ['طهارة', 'ماء', 'نجاسة']},
    {'pages': (4, 4), 'topic': 'سؤر الحيوان وولوغ الكلب',
     'hukm': 'سؤر الهرة لا بأس به. يغسل الإناء سبعا بولوغ الكلب. أبوال الخيل والبغال والحمير: اختلف فيها',
     'tags': ['طهارة', 'ماء', 'ولوغ الكلب']},
    {'pages': (5, 6), 'topic': 'النجاسات التي تصيب الثوب والبدن',
     'hukm': 'ما أصاب الثوب من الأذى يغسل. المسح على موضع الحجامة لا يجزئ بل يغسل. مسح الرأس بيديه ويأخذ لأذنيه ماء جديدا',
     'tags': ['طهارة', 'نجاسة', 'غسل']},
    {'pages': (7, 7), 'topic': 'نواقض الوضوء - النوم',
     'hukm': 'من نام في سجوده فاستثقل نوما انتقض وضوءه. وإن كان شيئا خفيفا فهو على وضوئه. الجالس المستند الذي يخفق رأسه ينقض إن استثقل',
     'tags': ['طهارة', 'نواقض', 'نوم']},
    {'pages': (8, 8), 'topic': 'المستحاضة وسلس البول',
     'hukm': 'المستحاضة والسلس يتوضآن لكل صلاة. من اشتد عليه البرد وأذاه الوضوء يتيمم',
     'tags': ['طهارة', 'استحاضة', 'وضوء']},
    {'pages': (9, 9), 'topic': 'الوضوء من المذي',
     'hukm': 'من وجد المذي يغسل فرجه ويتوضأ وضوءه للصلاة. ليس عليه غسل أنثييه إلا أن يخشى إصابتهما',
     'tags': ['طهارة', 'وضوء', 'مذي']},
    {'pages': (10, 10), 'topic': 'نواقض الوضوء - القبلة والمس',
     'hukm': 'الوضوء من قبلة الرجل امرأته ومن جسها بيده. من شك في بعض وضوئه أعاد ما شك فيه',
     'tags': ['طهارة', 'نواقض', 'وضوء']},
    {'pages': (11, 11), 'topic': 'سؤر الحيوان والوضوء بفضل المرأة',
     'hukm': 'يتوضأ بسؤر البعير والبقرة والشاة والسباع. يتوضأ بفضل وضوء المرأة. وكره مالك فضل الجنبا ثم رجع',
     'tags': ['طهارة', 'ماء', 'وضوء']},
    {'pages': (12, 12), 'topic': 'مسح الرأس والأذنين',
     'hukm': 'المرأة في مسح الرأس بمنزلة الرجل تمسح رأسها كله. الأذنان من الرأس ويستأنف لهما الماء',
     'tags': ['طهارة', 'وضوء', 'مسح']},
    {'pages': (13, 13), 'topic': 'جامع مسائل الوضوء',
     'hukm': 'لا بأس بالمسح بالمنديل بعد الوضوء. من ذبح وهو على وضوء فلا وضوء عليه. كره مالك لمس المصحف بغير وضوء',
     'tags': ['طهارة', 'وضوء']},
    {'pages': (14, 16), 'topic': 'النجاسة في الثوب وما يعفى عنه',
     'hukm': 'موضع الحجامة يغسل ولا يجزئه مسحه. من صلى وعلى ثوبه نجاسة لم يعلم بها أعاد في الوقت. دم البراغيث يعفى عنه إلا أن يكثر',
     'tags': ['طهارة', 'نجاسة', 'صلاة']},
    {'pages': (17, 17), 'topic': 'غسل النجاسة',
     'hukm': 'لا يطهر النجاسة شيء إلا الماء. إن علم ناحية النجاسة غسلها وإلا غسل الثوب كله',
     'tags': ['طهارة', 'نجاسة', 'غسل']},
    {'pages': (18, 19), 'topic': 'المسح على الجبائر وثوب المرضع',
     'hukm': 'من ترك المسح على الجبائر يعيد الصلاة أبدا. الجنب المكسور يتيمم لموضع الكسر. المرضعة يستحب لها ثوب للصلاة',
     'tags': ['طهارة', 'مسح', 'جبيرة']},
    {'pages': (20, 20), 'topic': 'أحكام الماء والميتة فيه',
     'hukm': 'من توضأ بماء وقعت فيه ميتة تغير لونه أو طعمه وصلى أعاد. وإن لم يتغير لا إعادة',
     'tags': ['طهارة', 'ماء', 'نجاسة']},
    {'pages': (21, 22), 'topic': 'الغسل من الجنابة',
     'hukm': 'لا يجزئ الغسل حتى يتدلك. لا يغتسل الجنب في الماء الدائم. كان مالك يأمر الجنب بالوضوء قبل الغسل فإن اغتسل بلا وضوء أجزأه',
     'tags': ['طهارة', 'غسل', 'جنابة']},
    {'pages': (23, 23), 'topic': 'واجب الغسل إذا التقى الختانان',
     'hukm': 'إذا مس الختان الختان فقد وجب الغسل إذا غابت الحشفة',
     'tags': ['طهارة', 'غسل', 'جنابة']},
    {'pages': (24, 24), 'topic': 'الاحتلام والبلل',
     'hukm': 'من رأى بللا فإن كان منيا اغتسل وإن كان مذيا توضأ. من احتلم ولم ير بللا فلا غسل عليه',
     'tags': ['طهارة', 'غسل', 'جنابة']},
    {'pages': (25, 26), 'topic': 'نية الوضوء',
     'hukm': 'إن توضأ لنافلة أو قراءة مصحف جاز. وإن توضأ لحر يجده ولا ينوي الوضوء لصلاة فلا يجزئه',
     'tags': ['طهارة', 'نية', 'وضوء']},
    {'pages': (27, 28), 'topic': 'مسائل متفرقة في الطهارة',
     'hukm': 'لا يصلي وهو حاقن. لا يقوم إلى الصلاة بحضرة الطعام. لا يصلي في ثياب أهل الذمة حتى تغسل',
     'tags': ['طهارة', 'صلاة']},
    {'pages': (29, 30), 'topic': 'الرعاف في الصلاة',
     'hukm': 'من رعف خرج فغسل الدم ثم بنى على صلاته. من رعف يوم الجمعة بعد ركعة فخرج وغسل ورجع بنى',
     'tags': ['طهارة', 'صلاة', 'رعاف']},
    {'pages': (31, 32), 'topic': 'المسح على الخفين',
     'hukm': 'لا يمسح على غضون الخفين. الخرق القليل لا يظهر منه القدم لا بأس. المرأة كالرجل في المسح',
     'tags': ['طهارة', 'مسح الخفين']},
    {'pages': (33, 38), 'topic': 'التيمم وأحكامه',
     'hukm': 'التيمم من الجنابة والوضوء سواء: ضربة للوجه وضربة لليدين. لا يتيمم في الحضر إلا المريض. يتيمم على الصفا والحجر والثلج',
     'tags': ['طهارة', 'تيمم']},
    {'pages': (39, 43), 'topic': 'الحيض والنفاس والاستحاضة',
     'hukm': 'أكثر الحيض خمسة عشر يوما. المستحاضة تغتسل وتصلي إذا انقطع الدم. الجفوف أن تدخل الخرقة فتخرجها جافة. النفساء تغتسل متى رأت الطهر',
     'tags': ['طهارة', 'حيض', 'نفاس', 'استحاضة']},
]


# === BUILD MASAIL ===
masail_out = []
for i, mdef in enumerate(MASAIL_DEF):
    p_min, p_max = mdef['pages']

    # Get raw text for this page range
    masala_text = ''
    first_page = None
    last_page = None
    for p in raw_pages:
        if p_min <= p['page_id'] <= p_max:
            body = p['body']
            body = re.sub(r'^\s*\[كِتَابُ[^\]]*\]\s*', '', body)
            body = re.sub(r'^\s*\[مَا جَاءَ[^\]]*\]\s*', '', body)
            masala_text += body + '\n'
            if first_page is None:
                first_page = p['page_id']
            last_page = p['page_id']

    if not masala_text.strip():
        continue

    # Extract dalil (Quran, hadiths)
    dalil = extract_dalil_from_text(masala_text, first_page)

    # Extract rulings from the text
    rulings = extract_rulings(masala_text)

    # If no rulings extracted by regex, use the hukm as the main ruling
    if not rulings:
        rulings = [{
            'speaker': 'مالك',
            'text': mdef['hukm'],
            'via': 'ابن القاسم',
        }]

    masail_out.append({
        'masala_id': f'mudawwana_tahara_{i+1:03d}',
        'bab': 'كِتَابُ الْوُضُوءِ',
        'bab_num': i + 1,
        'masala_topic': mdef['topic'],
        'hukm': mdef['hukm'],
        'rulings': rulings,
        'dalil': dalil,
        'fiqh_tags': mdef['tags'],
        'sub_masail': [],
        '_source': {
            'page_start': first_page,
            'page_end': last_page,
            'shamela_url': shamela_url(first_page),
            'full_text': masala_text.strip(),
        },
    })

# === OUTPUT ===
output = {
    'kitab': 'كتاب الطهارة',
    'kitab_num': 1,
    'book_key': 'book_02',
    'source': 'المدونة الكبرى — سحنون عن ابن القاسم عن مالك',
    'shamela_id': SHAMELA_ID,
    'extracted_at': '2026-04-10',
    'data_source': 'shamela_v4.db',
    'masail': masail_out,
}

out = BASE / 'data/masail/book_02/extracted/kitab_tahara.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

total_dalil = sum(len(m['dalil']) for m in masail_out)
total_rulings = sum(len(m['rulings']) for m in masail_out)
print(f"✓ المدونة: {len(masail_out)} masail | {total_dalil} dalil | {total_rulings} rulings")
for m in masail_out:
    types = {}
    for d in m['dalil']:
        types[d['type']] = types.get(d['type'], 0) + 1
    type_str = ', '.join(f"{v} {k}" for k, v in types.items())
    print(f"  {m['masala_id']}: {m['masala_topic']} | dalil: {type_str or 'none'} | {len(m['rulings'])} rulings")
