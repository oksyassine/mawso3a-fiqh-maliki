#!/usr/bin/env python3
"""Split الموطأ 32-masail into 49-masail by splitting multi-topic babs.
Run AFTER build_muwatta_tahara_from_v4.py to restore the golden model."""

import json, unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

def strip_d(text):
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

with open(BASE / 'data/masail/book_01/extracted/kitab_03_tahara.json', 'r') as f:
    data = json.load(f)

# SPLITS: bab_num → list of sub-masail definitions
# Each sub-masala: topic, hukm, dalil indices, ruling indices
SPLITS = {
    1: [  # العمل في الوضوء → 4 masail
        {'topic': 'صفة الوضوء', 'dalil': [0], 'rulings': [],
         'hukm': 'وصف وضوء النبي ﷺ: غسل يديه مرتين ثم تمضمض واستنثر ثلاثاً ثم غسل وجهه ثلاثاً ثم يديه إلى المرفقين ثم مسح رأسه ثم غسل رجليه'},
        {'topic': 'الاستنثار والمضمضة', 'dalil': [1, 2], 'rulings': [0],
         'hukm': 'الأمر بالاستنثار عند الوضوء. المضمضة والاستنثار من غرفة واحدة لا بأس بذلك'},
        {'topic': 'إسباغ الوضوء', 'dalil': [3], 'rulings': [],
         'hukm': 'أسبغ الوضوء: ويل للأعقاب من النار'},
        {'topic': 'ترتيب أعضاء الوضوء', 'dalil': [4], 'rulings': [1, 2],
         'hukm': 'من نسي فغسل وجهه قبل يديه أو نسي المضمضة والاستنثار'},
    ],
    3: [  # الطهور للوضوء → 4 masail
        {'topic': 'الوضوء بماء البحر', 'dalil': [0], 'rulings': [],
         'hukm': 'ماء البحر طهور حلال ميتته. هو الطهور ماؤه الحل ميتته'},
        {'topic': 'سؤر الهرة', 'dalil': [1], 'rulings': [],
         'hukm': 'طهارة سؤر الهرة — إنها ليست بنجس إنها من الطوافين عليكم'},
        {'topic': 'سؤر السباع', 'dalil': [2], 'rulings': [],
         'hukm': 'هل ترد حوضك السباع؟ فقال: لها ما حملت في بطونها ولنا ما بقي'},
        {'topic': 'وضوء الرجال والنساء جميعاً', 'dalil': [3], 'rulings': [],
         'hukm': 'كان الرجال والنساء في زمان رسول الله ﷺ يتوضئون جميعاً'},
    ],
    4: [  # ما لا يجب منه الوضوء → 2 masail
        {'topic': 'المشي في المكان القذر', 'dalil': [0], 'rulings': [],
         'hukm': 'من مشت في مكان قذر يطهره ما بعده'},
        {'topic': 'ترك الوضوء مما مسته النار', 'dalil': [1, 2], 'rulings': [],
         'hukm': 'القلس ليس فيه وضوء. القيء ليس فيه وضوء ولكن ليتمضمض منه'},
    ],
    6: [  # جامع الوضوء → 6 masail
        {'topic': 'الاستطابة بالأحجار', 'dalil': [0], 'rulings': [],
         'hukm': 'أولا يجد أحدكم ثلاثة أحجار — الاستجمار بالأحجار'},
        {'topic': 'فضل الوضوء', 'dalil': [1, 2, 3, 4], 'rulings': [],
         'hukm': 'ما من امرئ يتوضأ فيحسن وضوءه ثم يصلي الصلاة إلا غفر له. إذا توضأ العبد خرجت خطاياه من أعضائه'},
        {'topic': 'نبع الماء من بين أصابع النبي ﷺ', 'dalil': [5], 'rulings': [],
         'hukm': 'رأيت الماء ينبع من تحت أصابعه ﷺ فتوضأ الناس'},
        {'topic': 'الاستنجاء بالماء', 'dalil': [6, 7], 'rulings': [],
         'hukm': 'وضوء النساء والاستنجاء'},
        {'topic': 'غسل إناء الكلب', 'dalil': [8], 'rulings': [],
         'hukm': 'إذا شرب الكلب في إناء أحدكم فليغسله سبع مرات'},
        {'topic': 'المحافظة على الوضوء', 'dalil': [9], 'rulings': [],
         'hukm': 'ولا يحافظ على الوضوء إلا مؤمن'},
    ],
    20: [  # إعادة الجنب الصلاة → 2 masail
        {'topic': 'إعادة الجنب الصلاة إذا نسي الغسل', 'dalil': [0, 1], 'rulings': [],
         'hukm': 'الجنب إذا صلى ولم يذكر اغتسل وأعاد الصلاة'},
        {'topic': 'وجود أثر الاحتلام في الثوب', 'dalil': [2, 3, 4], 'rulings': [],
         'hukm': 'من احتلم اغتسل وغسل ما رأى في ثوبه'},
    ],
    22: [  # جامع غسل الجنابة → 2 masail
        {'topic': 'الاغتسال بفضل المرأة', 'dalil': [0], 'rulings': [],
         'hukm': 'لا بأس أن يغتسل بفضل المرأة ما لم تكن حائضا أو جنبا'},
        {'topic': 'الصلاة في ثوب الجنب', 'dalil': [1, 2], 'rulings': [],
         'hukm': 'كان يعرق في الثوب وهو جنب ثم يصلي فيه'},
    ],
    28: [  # جامع الحيضة → 3 masail
        {'topic': 'الحامل ترى الدم', 'dalil': [0, 1], 'rulings': [],
         'hukm': 'الحامل التي ترى الدم تدع الصلاة'},
        {'topic': 'الحائض ترجّل رأس زوجها', 'dalil': [2], 'rulings': [],
         'hukm': 'كانت عائشة ترجل رأس رسول الله ﷺ وهي حائض'},
        {'topic': 'الدم يصيب الثوب', 'dalil': [3], 'rulings': [],
         'hukm': 'إذا أصاب ثوبها الدم من الحيضة تقرصه بالماء ثم تنضحه ثم تصلي فيه'},
    ],
    32: [  # ما جاء في السواك → 2 masail
        {'topic': 'غسل يوم الجمعة والطيب', 'dalil': [0], 'rulings': [],
         'hukm': 'يا معشر المسلمين إن هذا يوم جعله الله عيدا فاغتسلوا ومن كان عنده طيب فلا يضره'},
        {'topic': 'فضل السواك', 'dalil': [1, 2], 'rulings': [],
         'hukm': 'لولا أن أشق على أمتي لأمرتهم بالسواك'},
    ],
}

# Build the new 49-masail list
new_masail = []
for m in data['masail']:
    bab_num = m['bab_num']
    if bab_num in SPLITS:
        # Split this bab into multiple masail
        for split_def in SPLITS[bab_num]:
            new_m = {
                'masala_id': f"muwatta_tahara_{len(new_masail)+1:03d}",
                'bab': m['bab'],
                'bab_num': bab_num,
                'masala_topic': split_def['topic'],
                'hukm': split_def['hukm'],
                'rulings': [m['rulings'][ri] for ri in split_def['rulings'] if ri < len(m['rulings'])],
                'dalil': [m['dalil'][di] for di in split_def['dalil'] if di < len(m['dalil'])],
                'fiqh_tags': m['fiqh_tags'],
                'sub_masail': [],
            }
            new_masail.append(new_m)
    else:
        # Keep as-is, just renumber
        m_copy = dict(m)
        m_copy['masala_id'] = f"muwatta_tahara_{len(new_masail)+1:03d}"
        new_masail.append(m_copy)

data['masail'] = new_masail

out = BASE / 'data/masail/book_01/extracted/kitab_03_tahara.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✓ الموطأ: {len(new_masail)} masail (was 32)")
# Count splits
from collections import Counter
bab_counts = Counter(m['bab_num'] for m in new_masail)
multi = {k: v for k, v in bab_counts.items() if v > 1}
print(f"  Multi-masail babs: {len(multi)} — {dict(multi)}")
