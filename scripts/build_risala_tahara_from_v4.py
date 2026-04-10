#!/usr/bin/env python3
"""Build الرسالة كتاب الطهارة from v4 — proper masail extraction.
Speaker: ابن أبي زيد القيرواني. Only babs 1-5 are طهارة.
Pages within each bab are concatenated then split into masail at topic boundaries."""

import json, re, unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SHAMELA_ID = 11373

def strip_d(text):
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def shamela_url(page_id):
    return f"https://shamela.ws/book/{SHAMELA_ID}/{page_id}" if page_id else ""

def find_page_at(entries, char_pos):
    """Find which page a character position falls in."""
    offset = 0
    for e in entries:
        end = offset + len(e['text']) + 1  # +1 for \n
        if char_pos < end:
            return e['page_id']
        offset = end
    return entries[-1]['page_id']

with open(BASE / 'extracts/risala_tahara_db_only_with_hukm.json', 'r') as f:
    data = json.load(f)

tahara_abwab = data['abwab'][:5]

# Concatenate each bab into one full text
bab_texts = []
for bab in tahara_abwab:
    full = '\n'.join(m['text'] for m in bab['masail'])
    bab_texts.append(full)

# === SPLIT MARKERS ===
# Bab 0 split: أقسام المياه → طهارة البقعة
BAB0_SPLIT = 'وطهارة البقعة للصلاة واجبة'

# Bab 1 splits: الاستنجاء → صفة الوضوء → فضل الوضوء
BAB1_SPLIT1 = 'ومن لم يخرج منه بول ولا غائط'  # end of istinja section
BAB1_SPLIT2 = 'رسول الله ﷺ من توضأ فأحسن الوضوء'  # start of du'a section

# Bab 3 splits: أسباب التيمم → صفة التيمم → تيمم الجنب
BAB3_SPLIT1 = 'والتيمم بالصعيد الطاهر'
BAB3_SPLIT2 = 'وإذا لم يجد الجنب أو الحائض'

def split_text(full, marker):
    """Split text at marker, returning (before, from_marker_onwards)."""
    idx = full.find(marker)
    if idx == -1:
        # Try without diacritics
        plain = strip_d(full)
        plain_marker = strip_d(marker)
        idx_p = plain.find(plain_marker)
        if idx_p == -1:
            return full, ''
        # Map back to original position
        count = 0
        for i, c in enumerate(full):
            if unicodedata.category(c) != 'Mn':
                if count == idx_p:
                    idx = i
                    break
                count += 1
    return full[:idx].rstrip(), full[idx:]


# === BUILD MASAIL ===
masail_out = []

def extract_dalil_from_risala(text, page_start):
    """Extract hadiths and Quran references embedded in الرسالة text."""
    dalil = []
    # Quran verses — find ﴿...﴾ then locate proper start
    for m in re.finditer(r'﴿([^﴾]+)﴾', text):
        before = text[max(0, m.start() - 120):m.start()]
        best_start = m.start()
        for intro in ['قَالَ اللَّهُ', 'قال الله', 'قَوْلِ اللَّهِ', 'قوله تعالى',
                       'لِقَوْلِ اللَّهِ', 'تَلَا', 'الْآيَةِ:']:
            idx = before.rfind(intro)
            if idx >= 0:
                best_start = max(0, m.start() - 120) + idx
                break
        after = text[m.end():min(len(text), m.end() + 60)]
        end = m.end()
        ref_match = re.search(r'\[.*?\]', after)
        if ref_match:
            end = m.end() + ref_match.end()
        else:
            end = min(len(text), m.end() + 5)
        verse_text = text[best_start:end].strip()
        dalil.append({'type': 'قرآن', 'full_text': verse_text, 'page_id': page_start, 'shamela_url': shamela_url(page_start)})

    # Hadith references (رسول الله ﷺ or النبي ﷺ)
    for m in re.finditer(r'(?:رسول الله ﷺ|النبي ﷺ|النبي ﵇)', text):
        start = max(0, m.start() - 40)
        end = min(len(text), m.end() + 200)
        # Find sentence end
        for stop in ['. ', '.\n', ' و']:
            idx = text[m.end():end].find(stop)
            if idx > 10:
                end = m.end() + idx + 1
                break
        hadith = text[start:end].strip()
        if len(hadith) > 30:
            dalil.append({'type': 'حديث', 'full_text': hadith, 'page_id': page_start, 'shamela_url': shamela_url(page_start)})

    # Athar - "جاء الأثر" or specific companion mentions
    for m in re.finditer(r'(?:جاء الأثر|فإنه جاء)', strip_d(text)):
        start = max(0, m.start() - 20)
        end = min(len(strip_d(text)), m.end() + 100)
        dalil.append({'type': 'أثر', 'full_text': text[start:end].strip(), 'page_id': page_start, 'shamela_url': shamela_url(page_start)})

    return dalil


def add_masala(bab_idx, text, topic, hukm, ruling, tags, dalil=None):
    bab = tahara_abwab[bab_idx]
    page_start = find_page_at(bab['masail'], bab_texts[bab_idx].find(text[:50]))
    text_end_pos = bab_texts[bab_idx].find(text[:50]) + len(text)
    page_end = find_page_at(bab['masail'], min(text_end_pos, len(bab_texts[bab_idx])-1))

    # Use manually-defined dalil if provided, otherwise empty
    if dalil is None:
        dalil = []

    masail_out.append({
        'masala_id': f'risala_tahara_{len(masail_out)+1:03d}',
        'bab': bab['bab_name'],
        'bab_num': bab_idx + 1,
        'masala_topic': topic,
        'hukm': hukm,
        'rulings': [{
            'speaker': 'ابن أبي زيد القيرواني',
            'text': ruling,
        }],
        'dalil': dalil,
        'fiqh_tags': tags,
        'sub_masail': [],
        '_source': {
            'page_start': page_start,
            'page_end': page_end,
            'shamela_url': shamela_url(page_start),
            'full_text': text,
        },
    })

# --- Bab 0: طهارة الماء والثوب والبقعة (split into 2) ---
t0 = bab_texts[0]
t0a, t0b = split_text(t0, BAB0_SPLIT)

add_masala(0, t0a,
    topic='أقسام المياه وأحكامها',
    hukm='ماء السماء والعيون والآبار والبحر طاهر مطهر. ما تغير لونه بطاهر حل فيه فهو طاهر غير مطهر. ما غيرته النجاسة فليس بطاهر ولا مطهر. قليل الماء ينجسه قليل النجاسة وإن لم تغيره. قلة الماء مع إحكام الغسل سنة والسرف غلو وبدعة. توضأ رسول الله ﷺ بمد وتطهر بصاع',
    ruling='يكون ذلك بماء طاهر غير مشوب بنجاسة ولا بماء قد تغير لونه لشيء خالطه من شيء نجس أو طاهر إلا ما غيرت لونه الأرض التي هو بها من سبخة أو حمأة',
    tags=['طهارة', 'ماء', 'نجاسة'],
    dalil=[{
        'type': 'حديث',
        'full_text': 'توضأ رسول الله ﷺ بمد وهو وزن رطل وثلث وتطهر بصاع وهو أربعة أمداد بمده ﷺ',
        'summary': 'مقدار ماء الوضوء والغسل',
        'page_id': 11,
        'shamela_url': shamela_url(11),
    }],
)

add_masala(0, t0b,
    topic='طهارة البقعة والثوب ولباس الصلاة',
    hukm='طهارة البقعة للصلاة واجبة وكذلك طهارة الثوب. ينهى عن الصلاة في معاطن الإبل ومحجة الطريق والحمام والمزبلة والمجزرة ومقبرة المشركين. أقل لباس الرجل ثوب ساتر. أقل لباس المرأة درع حصيف سابغ يستر ظهور قدميها وخمار',
    ruling='طهارة البقعة للصلاة واجبة وكذلك طهارة الثوب فقيل إن ذلك فيهما واجب وجوب الفرائض وقيل وجوب السنن المؤكدة',
    tags=['طهارة', 'لباس الصلاة', 'نجاسة'],
)

# --- Bab 1: صفة الوضوء (split into 3) ---
t1 = bab_texts[1]
t1a, t1_rest = split_text(t1, BAB1_SPLIT1)
t1b, t1c = split_text(t1_rest, BAB1_SPLIT2)

add_masala(1, t1a,
    topic='الاستنجاء والاستجمار',
    hukm='الاستنجاء ليس من سنن الوضوء ولا فرائضه وإنما من إيجاب زوال النجاسة. يجزئ فعله بغير نية. صفته: يبدأ بغسل مخرج البول ثم يمسح الأذى بمدر ثم يستنجي بالماء ويجيد العرك. لا يستنجى من ريح. من استجمر بثلاثة أحجار يخرج آخرهن نقيا أجزأه والماء أطهر وأطيب',
    ruling='ليس الاستنجاء مما يجب أن يوصل به الوضوء لا في سنن الوضوء ولا في فرائضه وهو من إيجاب زوال النجاسة به أو بالاستجمار',
    tags=['طهارة', 'استنجاء'],
)

add_masala(1, t1b,
    topic='صفة الوضوء وفرائضه وسننه',
    hukm='من سنة الوضوء غسل اليدين قبل الإناء والمضمضة والاستنشاق والاستنثار ومسح الأذنين وباقيه فريضة. يبدأ بالتسمية ثم غسل يديه ثلاثا ثم المضمضة والاستنشاق ثم غسل الوجه من منابت الشعر إلى الذقن ثلاثا ثم اليدين إلى المرفقين ثم مسح الرأس من المقدم إلى القفا ثم الرد ثم الأذنين ثم غسل الرجلين مع عرك العقبين. ليس عليه تخليل اللحية في الوضوء في قول مالك',
    ruling='من سنة الوضوء غسل اليدين قبل دخولهما في الإناء والمضمضة والاستنشاق والاستنثار ومسح الأذنين سنة وباقيه فريضة',
    tags=['طهارة', 'وضوء', 'مضمضة', 'استنثار', 'مسح', 'غسل'],
    dalil=[
        {
            'type': 'حديث',
            'full_text': 'ويل للأعقاب من النار',
            'summary': 'الحث على إسباغ غسل الرجلين في الوضوء',
            'page_id': 15,
            'shamela_url': shamela_url(15),
        },
        {
            'type': 'قول مالك',
            'full_text': 'ليس عليه تخليلها في الوضوء في قول مالك',
            'summary': 'عدم وجوب تخليل اللحية في الوضوء',
            'page_id': 14,
            'shamela_url': shamela_url(14),
        },
    ],
)

add_masala(1, t1c,
    topic='فضل الوضوء والنية',
    hukm='قال رسول الله ﷺ من توضأ فأحسن الوضوء ثم شهد الشهادتين فتحت له أبواب الجنة الثمانية. يجب أن يعمل الوضوء احتسابا لله يرجو تقبله وثوابه وتطهيره من الذنوب. تمام كل عمل بحسن النية فيه',
    ruling='يجب عليه أن يعمل عمل الوضوء احتسابا لله تعالى لما أمره به يرجو تقبله وثوابه وتطهيره من الذنوب به',
    tags=['طهارة', 'وضوء', 'نية'],
    dalil=[{
        'type': 'حديث',
        'full_text': 'من توضأ فأحسن الوضوء ثم رفع طرفه إلى السماء فقال أشهد أن لا إله إلا الله وحده لا شريك له وأشهد أن محمدا عبده ورسوله فتحت له أبواب الجنة الثمانية يدخل من أيها شاء',
        'summary': 'فضل الدعاء بعد الوضوء — فتحت له أبواب الجنة الثمانية',
        'page_id': 16,
        'shamela_url': shamela_url(16),
    }],
)

# --- Bab 2: الغسل (1 masala — continuous topic) ---
add_masala(2, bab_texts[2],
    topic='صفة الغسل من الجنابة والحيض',
    hukm='الطهر من الجنابة والحيض والنفاس سواء. إن اقتصر على الغسل دون الوضوء أجزأه وأفضل أن يتوضأ أولا. يبدأ بغسل الأذى ثم يتوضأ ثم يخلل شعر رأسه ويغرف على رأسه ثلاثا ثم يفيض على شقه الأيمن ثم الأيسر ويتدلك حتى يعم جسده. ليس على المرأة حل عقاصها. إن مس ذكره بباطن كفه بعد تمام طهره أعاد الوضوء',
    ruling='إن اقتصر المتطهر على الغسل دون الوضوء أجزأه وأفضل له أن يتوضأ بعد أن يبدأ بغسل ما بفرجه أو جسده من الأذى',
    tags=['طهارة', 'غسل', 'جنابة', 'حيض'],
)

# --- Bab 3: التيمم (split into 3) ---
t3 = bab_texts[3]
t3a, t3_rest = split_text(t3, BAB3_SPLIT1)
t3b, t3c = split_text(t3_rest, BAB3_SPLIT2)

add_masala(3, t3a,
    topic='أسباب التيمم ووقته',
    hukm='يجب التيمم لعدم الماء في السفر أو عند عدم القدرة على مسه لمرض. وكذلك المسافر الذي يمنعه خوف لصوص أو سباع. الآيس يتيمم أول الوقت ومن لم يكن عنده علم تيمم في وسطه. من تيمم ثم أصاب الماء: المريض والخائف يعيدان وغيرهم لا يعيد. لا يصلي صلاتين بتيمم واحد إلا المريض المقيم',
    ruling='التيمم يجب لعدم الماء في السفر إذا يئس أن يجده في الوقت وقد يجب مع وجوده إذا لم يقدر على مسه في سفر أو حضر لمرض مانع',
    tags=['طهارة', 'تيمم'],
)

add_masala(3, t3b,
    topic='صفة التيمم',
    hukm='التيمم بالصعيد الطاهر وهو ما ظهر على وجه الأرض من تراب أو رمل أو حجارة أو سبخة. يضرب بيديه الأرض وينفضهما ثم يمسح وجهه كله ثم يضرب ثانية ويمسح يمناه بيسراه من أطراف الأصابع إلى المرفقين ثم يمسح اليسرى باليمنى كذلك',
    ruling='التيمم بالصعيد الطاهر وهو ما ظهر على وجه الأرض منها من تراب أو رمل أو حجارة أو سبخة يضرب بيديه الأرض فإن تعلق بهما شيء نفضهما نفضا خفيفا',
    tags=['طهارة', 'تيمم'],
)

add_masala(3, t3c,
    topic='تيمم الجنب والحائض',
    hukm='إذا لم يجد الجنب أو الحائض الماء تيمما وصليا فإذا وجدا الماء تطهرا ولم يعيدا ما صليا. لا يطأ الرجل امرأته التي انقطع عنها دم حيض أو نفاس بالتيمم حتى يجد الماء',
    ruling='إذا لم يجد الجنب أو الحائض الماء للطهر تيمما وصليا فإذا وجدا الماء تطهرا ولم يعيدا ما صليا',
    tags=['طهارة', 'تيمم', 'جنابة', 'حيض'],
)

# --- Bab 4: المسح على الخفين (1 masala) ---
add_masala(4, bab_texts[4],
    topic='المسح على الخفين',
    hukm='يجوز المسح على الخفين في الحضر والسفر ما لم ينزعهما بشرط أن يدخل فيهما رجليه بعد وضوء تام. صفته: يجعل اليمنى فوق الخف من طرف الأصابع واليسرى من تحت ويذهب بهما إلى الكعبين. لا يمسح على طين في أسفل خفه حتى يزيله',
    ruling='له أن يمسح على الخفين في الحضر والسفر ما لم ينزعهما وذلك إذا أدخل فيهما رجليه بعد أن غسلهما في وضوء تحل به الصلاة',
    tags=['طهارة', 'مسح الخفين'],
)


# === OUTPUT ===
output = {
    'kitab': 'كتاب الطهارة',
    'kitab_num': 1,
    'book_key': 'book_15',
    'source': 'الرسالة — ابن أبي زيد القيرواني',
    'shamela_id': SHAMELA_ID,
    'extracted_at': '2026-04-10',
    'data_source': 'shamela_v4.db',
    'masail': masail_out,
}

out = BASE / 'data/masail/book_15/extracted/kitab_tahara.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✓ الرسالة: {len(masail_out)} masail")
for m in masail_out:
    src = m.get('_source', {})
    types = {}
    for d in m['dalil']:
        types[d['type']] = types.get(d['type'], 0) + 1
    type_str = ', '.join(f"{v} {k}" for k, v in types.items()) or 'none'
    print(f"  {m['masala_id']}: {m['masala_topic']} (pp {src.get('page_start')}-{src.get('page_end')}) dalil: {type_str}")
