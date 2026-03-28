"""Seed all Maliki authors, mutoon, shuruh, and hawashi."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.base import Base, Author, Book, TextType, StudyLevel

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mawso3a_fiqh"


AUTHORS = [
    # (name_ar, name_en, full_name_ar, death_hijri, death_ce, century, region)
    # === 2nd Century AH — Foundation ===
    ("مالك بن أنس", "Malik ibn Anas", "مالك بن أنس بن مالك بن عامر الأصبحي", 179, 795, 2, "Madinah"),
    ("ابن وهب", "Ibn Wahb", "عبد الله بن وهب بن مسلم القرشي المصري", 197, 812, 2, "Egypt"),
    ("ابن القاسم", "Ibn al-Qasim", "عبد الرحمن بن القاسم العتقي المصري", 191, 806, 2, "Egypt"),
    ("أشهب", "Ashhab", "أشهب بن عبد العزيز القيسي المصري", 204, 819, 3, "Egypt"),
    ("علي بن زياد", "Ali ibn Ziyad", "علي بن زياد العبسي الطرابلسي التونسي", 183, 799, 2, "Tunis"),
    # === 3rd Century AH — Codification ===
    ("ابن عبد الحكم", "Ibn Abd al-Hakam", "عبد الله بن عبد الحكم بن أعين المصري", 214, 829, 3, "Egypt"),
    ("أسد بن الفرات", "Asad ibn al-Furat", "أسد بن الفرات بن سنان التونسي", 213, 828, 3, "Tunis"),
    ("سحنون", "Sahnun", "عبد السلام بن سعيد بن حبيب التنوخي", 240, 854, 3, "Qayrawan"),
    ("ابن حبيب", "Ibn Habib", "عبد الملك بن حبيب بن سليمان السلمي القرطبي", 238, 852, 3, "Andalus"),
    ("العتبي", "al-Utbi", "محمد بن أحمد بن عبد العزيز العتبي القرطبي", 255, 869, 3, "Andalus"),
    ("ابن المواز", "Ibn al-Mawwaz", "محمد بن إبراهيم بن زياد الإسكندري", 269, 882, 3, "Egypt"),
    ("ابن عبدوس", "Ibn Abdus", "محمد بن إبراهيم بن عبدوس", 260, 874, 3, "Qayrawan"),
    ("القاضي إسماعيل", "al-Qadi Isma'il", "إسماعيل بن إسحاق بن حماد الجهضمي البغدادي", 282, 895, 3, "Iraq"),
    ("ابن سحنون", "Ibn Sahnun", "محمد بن سحنون التنوخي", 256, 870, 3, "Qayrawan"),
    ("ابن الماجشون", "Ibn al-Majishun", "عبد الملك بن عبد العزيز بن الماجشون", 212, 827, 3, "Madinah"),
    # === 4th Century AH — Abridgment ===
    ("الأبهري", "al-Abhari", "أبو بكر محمد بن عبد الله الأبهري البغدادي", 375, 985, 4, "Iraq"),
    ("ابن الجلاب", "Ibn al-Jallab", "عبيد الله بن الحسين بن الحسن البصري", 378, 988, 4, "Iraq"),
    ("ابن أبي زيد القيرواني", "Ibn Abi Zayd al-Qayrawani", "أبو محمد عبد الله بن أبي زيد القيرواني", 386, 996, 4, "Qayrawan"),
    ("القابسي", "al-Qabisi", "أبو الحسن علي بن محمد بن خلف المعافري القابسي", 403, 1012, 5, "Qayrawan"),
    ("ابن أبي زمنين", "Ibn Abi Zamnin", "محمد بن عبد الله بن عيسى ابن أبي زمنين الإلبيري", 399, 1008, 4, "Andalus"),
    ("البراذعي", "al-Baradhi'i", "أبو سعيد خلف بن أبي القاسم محمد الأزدي البراذعي", 438, 1046, 5, "Qayrawan"),
    ("أبو عمران الفاسي", "Abu Imran al-Fasi", "موسى بن عيسى الغفجومي الفاسي", 430, 1038, 5, "Fez"),
    # === 5th Century AH — Maturation ===
    ("القاضي عبد الوهاب", "al-Qadi Abd al-Wahhab", "عبد الوهاب بن علي بن نصر البغدادي", 422, 1031, 5, "Iraq"),
    ("ابن يونس", "Ibn Yunus", "أبو بكر محمد بن عبد الله بن يونس التميمي الصقلي", 451, 1059, 5, "Sicily"),
    ("ابن عبد البر", "Ibn Abd al-Barr", "يوسف بن عبد الله بن محمد النمري القرطبي", 463, 1071, 5, "Andalus"),
    ("الباجي", "al-Baji", "أبو الوليد سليمان بن خلف الباجي", 474, 1081, 5, "Andalus"),
    ("اللخمي", "al-Lakhmi", "علي بن محمد الربعي اللخمي", 478, 1085, 5, "Qayrawan"),
    ("ابن بطال", "Ibn Battal", "أبو الحسن علي بن خلف بن عبد الملك ابن بطال القرطبي", 449, 1057, 5, "Andalus"),
    ("ابن التونسي", "Ibn al-Tunisi", "عبد الحميد بن محمد الصائغ التونسي", 443, 1051, 5, "Tunis"),
    # === 6th Century AH — Bridge ===
    ("ابن رشد الجد", "Ibn Rushd al-Jadd", "أبو الوليد محمد بن أحمد بن رشد القرطبي", 520, 1126, 6, "Andalus"),
    ("المازري", "al-Maziri", "أبو عبد الله محمد بن علي بن عمر التميمي المازري", 536, 1141, 6, "Qayrawan"),
    ("ابن العربي", "Ibn al-Arabi", "أبو بكر محمد بن عبد الله ابن العربي المعافري", 543, 1148, 6, "Andalus"),
    ("القاضي عياض", "Qadi Iyad", "أبو الفضل عياض بن موسى اليحصبي السبتي", 544, 1149, 6, "Ceuta"),
    ("ابن رشد الحفيد", "Ibn Rushd al-Hafid", "أبو الوليد محمد بن أحمد بن محمد بن رشد", 595, 1198, 6, "Andalus"),
    # === 7th Century AH ===
    ("ابن شاس", "Ibn Shas", "جلال الدين محمد بن أحمد بن شاس", 616, 1219, 7, "Egypt"),
    ("ابن الحاجب", "Ibn al-Hajib", "جمال الدين عثمان بن عمر بن أبي بكر", 646, 1249, 7, "Egypt"),
    ("القرافي", "al-Qarafi", "شهاب الدين أحمد بن إدريس القرافي", 684, 1285, 7, "Egypt"),
    # === 8th Century AH ===
    ("خليل بن إسحاق", "Khalil ibn Ishaq", "خليل بن إسحاق بن موسى الجندي", 776, 1374, 8, "Egypt"),
    ("ابن عرفة", "Ibn Arafa", "محمد بن محمد بن عرفة الورغمي", 803, 1401, 8, "Tunis"),
    # === 9th Century AH ===
    ("ابن عاصم", "Ibn Asim", "محمد بن محمد بن عاصم الغرناطي", 829, 1426, 9, "Andalus"),
    ("البرزلي", "al-Burzuli", "أبو القاسم بن أحمد بن محمد البرزلي", 841, 1438, 9, "Tunis"),
    ("المواق", "al-Mawwaq", "أبو عبد الله محمد بن يوسف المواق", 897, 1492, 9, "Andalus"),
    ("الرصاع", "al-Rassa'", "محمد الأنصاري الرصاع", 894, 1489, 9, "Tunis"),
    # === 10th Century AH ===
    ("الزقاق", "al-Zaqqaq", "علي بن قاسم الزقاق", 912, 1506, 10, "Fez"),
    ("الونشريسي", "al-Wansharisi", "أحمد بن يحيى الونشريسي", 914, 1508, 10, "Fez"),
    ("السيوطي", "al-Suyuti", "جلال الدين عبد الرحمن السيوطي", 911, 1505, 10, "Egypt"),
    ("أبو الحسن المالكي", "Abu al-Hasan al-Maliki", "علي بن محمد بن عبد الرحمن المنوفي", 939, 1532, 10, "Egypt"),
    ("الحطاب", "al-Hattab", "شمس الدين محمد بن محمد الحطاب الرعيني", 954, 1547, 10, "Maghreb"),
    ("الأخضري", "al-Akhdari", "عبد الرحمن بن محمد الصغير الأخضري", 983, 1575, 10, "Algeria"),
    ("المنجور", "al-Manjur", "أحمد بن علي المنجور", 995, 1587, 10, "Fez"),
    # === 11th Century AH ===
    ("ابن عاشر", "Ibn Ashir", "عبد الواحد بن أحمد بن عاشر الأنصاري", 1040, 1631, 11, "Fez"),
    ("ميارة", "Mayyara", "محمد بن أحمد بن محمد ميارة المالكي", 1072, 1662, 11, "Fez"),
    ("الزرقاني (عبد الباقي)", "al-Zurqani (Abd al-Baqi)", "عبد الباقي بن يوسف الزرقاني", 1099, 1688, 11, "Egypt"),
    ("الخرشي", "al-Kharshi", "أبو عبد الله محمد الخرشي", 1101, 1690, 11, "Egypt"),
    # === 12th Century AH ===
    ("الزرقاني (محمد)", "al-Zurqani (Muhammad)", "محمد بن عبد الباقي الزرقاني", 1122, 1710, 12, "Egypt"),
    ("النفراوي", "al-Nafrawi", "أحمد بن غنيم بن سالم النفراوي", 1126, 1714, 12, "Egypt"),
    ("العدوي", "al-Adawi", "علي بن أحمد الصعيدي العدوي", 1189, 1775, 12, "Egypt"),
    ("البناني", "al-Bannani", "محمد بن الحسن البناني", 1194, 1780, 12, "Egypt"),
    ("الدردير", "al-Dardir", "أبو البركات أحمد بن محمد الدردير", 1201, 1786, 12, "Egypt"),
    ("التاودي", "al-Tawdi", "التاودي بن سودة المري الفاسي", 1209, 1795, 12, "Fez"),
    # === 13th Century AH ===
    ("الدسوقي", "al-Dusuqi", "محمد بن أحمد بن عرفة الدسوقي", 1230, 1815, 13, "Egypt"),
    ("الرهوني", "al-Rahuni", "محمد بن أحمد الرهوني", 1230, 1815, 13, "Fez"),
    ("الصاوي", "al-Sawi", "أحمد بن محمد الصاوي المالكي", 1241, 1825, 13, "Egypt"),
    ("عليش", "Illaysh", "محمد بن أحمد عليش", 1299, 1882, 13, "Egypt"),
    # === 14th Century AH ===
    ("صالح الأزهري", "Salih al-Azhari", "صالح عبد السميع الآبي الأزهري", 1335, 1917, 14, "Egypt"),
    ("الوزاني", "al-Wazzani", "المهدي بن محمد الوزاني", 1342, 1923, 14, "Fez"),
    ("الكشناوي", "al-Kashnawi", "أبو بكر بن حسن الكشناوي", 1397, 1977, 14, "West Africa"),
    # === Additional from deep research ===
    # 6th-9th century
    ("ابن بشير", "Ibn Bashir", "إبراهيم بن عبد الصمد بن بشير التنوخي", 598, 1201, 6, "Tunis"),
    ("ابن بزيزة", "Ibn Baziza", "عبد العزيز بن إبراهيم بن بزيزة التونسي", 662, 1264, 7, "Tunis"),
    ("ابن راشد القفصي", "Ibn Rashid al-Qafsi", "محمد بن عبد الله بن راشد البكري القفصي", 736, 1336, 8, "Tunis"),
    ("ابن جزي", "Ibn Juzayy", "محمد بن أحمد بن جزي الكلبي الغرناطي", 741, 1340, 8, "Andalus"),
    ("ابن الحاج", "Ibn al-Hajj", "محمد بن محمد العبدري الفاسي", 737, 1336, 8, "Fez"),
    ("ابن سلمون", "Ibn Salmun", "سلمون بن علي الكناني الغرناطي", 767, 1365, 8, "Andalus"),
    ("الشاطبي", "al-Shatibi", "إبراهيم بن موسى الشاطبي الغرناطي", 790, 1388, 8, "Andalus"),
    ("ابن فرحون", "Ibn Farhun", "إبراهيم بن علي بن محمد ابن فرحون اليعمري", 799, 1397, 8, "Madinah"),
    ("بهرام", "Bahram", "تاج الدين بهرام بن عبد الله الدميري", 805, 1403, 8, "Egypt"),
    ("ابن ناجي", "Ibn Naji", "قاسم بن عيسى بن ناجي التنوخي القيرواني", 837, 1433, 9, "Qayrawan"),
    ("المازوني", "al-Mazuni", "يحيى بن موسى المغيلي المازوني", 883, 1478, 9, "Algeria"),
    ("ابن هلال السجلماسي", "Ibn Hilal", "إبراهيم بن هلال السجلماسي", 903, 1497, 9, "Sijilmasa"),
    ("ابن غازي", "Ibn Ghazi", "محمد بن أحمد بن غازي العثماني المكناسي", 919, 1513, 10, "Meknes"),
    ("زروق", "Zarruq", "أحمد بن أحمد البرنسي الفاسي زروق", 899, 1493, 9, "Fez"),
    ("ابن مرزوق الحفيد", "Ibn Marzuq al-Hafid", "محمد بن أحمد بن مرزوق التلمساني", 842, 1439, 9, "Tlemcen"),
    ("ابن الشاط", "Ibn al-Shat", "قاسم بن عبد الله الأنصاري السبتي", 723, 1323, 8, "Ceuta"),
    ("ابن عسكر", "Ibn Askar", "عبد الرحمن بن محمد بن عسكر البغدادي", 732, 1332, 8, "Iraq"),
    # 10th-14th century additions
    ("التسولي", "al-Tasuli", "علي بن عبد السلام التسولي", 1258, 1842, 13, "Fez"),
    ("أحمد بابا التنبكتي", "Ahmad Baba al-Timbukti", "أحمد بابا بن أحمد التنبكتي", 1036, 1627, 11, "Timbuktu"),
    ("عثمان بن فودي", "Uthman dan Fodio", "عثمان بن محمد بن عثمان بن فودي", 1232, 1817, 13, "Sokoto"),
    ("عبد الله بن فودي", "Abdullah bin Fodio", "عبد الله بن محمد بن عثمان بن فودي", 1245, 1829, 13, "Sokoto"),
    ("الشنقيطي (مراقي السعود)", "al-Shinqiti", "عبد الله بن الحاج إبراهيم العلوي الشنقيطي", 1230, 1815, 13, "Mauritania"),
    ("ابن عاشور", "Ibn Ashur", "محمد الطاهر بن عاشور", 1393, 1973, 14, "Tunis"),
    ("الغرياني", "al-Gharyani", "الصادق عبد الرحمن الغرياني", None, None, 15, "Libya"),
]


def build_books(author_map: dict[str, int]) -> list[dict]:
    """Build book records referencing author IDs. Returns list of dicts."""
    books = []

    def add(title_ar, title_en, author_key, text_type, level=None,
            parent_key=None, desc_ar="", source="", short=None):
        books.append({
            "title_ar": title_ar,
            "title_en": title_en,
            "short_title_ar": short or title_ar,
            "author_key": author_key,
            "text_type": text_type,
            "study_level": level,
            "parent_key": parent_key,
            "description_ar": desc_ar,
            "source_name": source,
        })

    # ============ 2nd-3rd CENTURY — FOUNDATIONAL TEXTS ============

    add("الموطأ", "Al-Muwatta", "مالك بن أنس", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أول كتاب في الحديث والفقه، أصل المذهب المالكي", source="shamela")

    add("الجامع لابن وهب", "Al-Jami' (Ibn Wahb)", "ابن وهب", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="مجموعة أحاديث وآثار فقهية من أعلم تلاميذ مالك", source="shamela")

    add("الأسدية", "Al-Asadiyya", "أسد بن الفرات", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="مسائل ابن القاسم عن مالك، أصل المدونة، كانت 60 جزءا", source="archive")

    add("المدونة الكبرى", "Al-Mudawwana", "سحنون", TextType.ENCYCLOPEDIA, StudyLevel.SPECIALIST,
        desc_ar="أهم مرجع في الفقه المالكي، جمع فتاوى مالك عن طريق ابن القاسم", source="shamela")

    add("الواضحة في السنن والفقه", "Al-Wadiha", "ابن حبيب", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="مؤلف أندلسي كبير في الفقه المالكي، هيمن على التعليم بالأندلس", source="archive")

    add("المستخرجة (العتبية)", "Al-Mustakhraja (Al-Utbiyya)", "العتبي", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="سماعات من مالك وتلاميذه، من أمهات المذهب", source="shamela")

    add("الموازية", "Al-Muwaziyya", "ابن المواز", TextType.ENCYCLOPEDIA, StudyLevel.SPECIALIST,
        desc_ar="من أمهات المذهب الأربعة، جمع وترجيح بين أقوال المالكية", source="archive")

    add("المجموعة", "Al-Majmu'a", "ابن عبدوس", TextType.ENCYCLOPEDIA, StudyLevel.SPECIALIST,
        desc_ar="مجموعة ضخمة في مذهب مالك وأصحابه، نحو 50 بابا", source="archive")

    add("المختصر الصغير", "Al-Mukhtasar al-Saghir", "ابن عبد الحكم", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أقدم مختصر في المذهب المالكي، نحو 1200 مسألة", source="archive")

    add("المختصر الكبير", "Al-Mukhtasar al-Kabir", "ابن عبد الحكم", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أوسع مختصرات ابن عبد الحكم، نحو 18000 مسألة", source="archive")

    add("المبسوط", "Al-Mabsut (Qadi Isma'il)", "القاضي إسماعيل", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="مؤلف فقهي ضخم لقاضي بغداد المالكي", source="archive")

    add("أحكام القرآن للقاضي إسماعيل", "Ahkam al-Quran (Qadi Isma'il)", "القاضي إسماعيل",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أحكام القرآن من منظور مالكي، من أوائل كتب أحكام القرآن", source="shamela")

    # ============ 4th CENTURY — ABRIDGMENT ERA ============

    add("الرسالة", "Al-Risala", "ابن أبي زيد القيرواني", TextType.MATN, StudyLevel.BEGINNER,
        desc_ar="أشهر متن في المذهب المالكي، يشمل العقيدة والعبادات والمعاملات", source="shamela")

    add("النوادر والزيادات", "Al-Nawadir wal-Ziyadat", "ابن أبي زيد القيرواني",
        TextType.ENCYCLOPEDIA, StudyLevel.SPECIALIST,
        desc_ar="موسوعة ضخمة جمعت أقوال المدونة وزيادات من الأمهات، 15 مجلدا", source="shamela")

    add("الجامع في السنن والآداب", "Al-Jami' fi al-Sunan", "ابن أبي زيد القيرواني",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="جامع في الحديث والأحكام والآداب والسيرة", source="shamela")

    add("التفريع", "Al-Tafri'", "ابن الجلاب", TextType.MATN, StudyLevel.ADVANCED,
        desc_ar="كتاب فقهي منهجي يمثل المدرسة العراقية المالكية", source="shamela")

    add("المغرب في اختصار المدونة", "Al-Mughrib", "ابن أبي زمنين", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أفضل مختصرات المدونة بإجماع، يجمع الاختصار مع الشرح", source="shamela")

    add("منتخب الأحكام", "Muntakhab al-Ahkam", "ابن أبي زمنين", TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="مختارات من الأحكام والنوازل، انتشر في المشرق والمغرب", source="shamela")

    add("التهذيب في اختصار المدونة", "Al-Tahdhib", "البراذعي", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أنجح مختصرات المدونة، حل محلها في التدريس", source="shamela")

    # ============ 5th CENTURY — MATURATION ============

    add("التلقين", "Al-Talqin", "القاضي عبد الوهاب", TextType.MATN, StudyLevel.INTERMEDIATE,
        desc_ar="متن تعليمي في الفقه المالكي، يمثل المدرسة العراقية", source="shamela")

    add("المعونة", "Al-Ma'una", "القاضي عبد الوهاب", TextType.SHARH, StudyLevel.INTERMEDIATE,
        parent_key="الرسالة", desc_ar="شرح على رسالة ابن أبي زيد القيرواني", source="shamela")

    add("الإشراف على نكت مسائل الخلاف", "Al-Ishraf", "القاضي عبد الوهاب",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="بحث في نقاط الخلاف بين المذاهب مع الاستدلال للمالكية", source="shamela")

    add("النكت والفروق لمسائل المدونة", "Al-Nukat wal-Furuq", "القاضي عبد الوهاب",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="المدونة الكبرى", desc_ar="فروق فقهية دقيقة على مسائل المدونة", source="shamela")

    add("عيون المسائل", "Uyun al-Masa'il", "القاضي عبد الوهاب",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="مجموعة مسائل فقهية مهمة", source="shamela")

    add("الجامع لمسائل المدونة", "Al-Jami' li-Masa'il al-Mudawwana", "ابن يونس",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="المدونة الكبرى", desc_ar="سمي مصحف المذهب، من أعظم شروح المدونة", source="shamela")

    add("الكافي في فقه أهل المدينة", "Al-Kafi", "ابن عبد البر",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="كتاب فقهي شامل يمثل مدرسة أهل المدينة، 15 مجلدا", source="shamela")

    add("التبصرة", "Al-Tabsira", "اللخمي", TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="المدونة الكبرى", desc_ar="تعليق نقدي مهم على المدونة، فيه اجتهادات مستقلة", source="shamela")

    # ============ 6th CENTURY — BRIDGE PERIOD ============

    add("البيان والتحصيل", "Al-Bayan wal-Tahsil", "ابن رشد الجد",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="المستخرجة (العتبية)",
        desc_ar="شرح ضخم على العتبية، 20 مجلدا، من أهم مراجع المذهب", source="shamela")

    add("المقدمات الممهدات", "Al-Muqaddimat", "ابن رشد الجد",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="مقدمات أصولية لأبواب الفقه، تأسيس نظري للمدونة", source="shamela")

    add("نوازل ابن رشد", "Nawazil Ibn Rushd", "ابن رشد الجد",
        TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="مجموعة فتاوى ونوازل مهمة", source="shamela")

    add("شرح التلقين", "Sharh al-Talqin (al-Maziri)", "المازري",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="التلقين", desc_ar="شرح مفصل على التلقين، المازري آخر مجتهدي المذهب بإفريقية", source="shamela")

    add("أحكام القرآن لابن العربي", "Ahkam al-Quran (Ibn al-Arabi)", "ابن العربي",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="من أهم كتب أحكام القرآن من منظور مالكي", source="shamela")

    add("القبس شرح الموطأ", "Al-Qabas", "ابن العربي",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="الموطأ", desc_ar="شرح مختصر مهم على الموطأ", source="shamela")

    add("المسالك في شرح الموطأ", "Al-Masalik", "ابن العربي",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="الموطأ", desc_ar="شرح موسع على الموطأ", source="shamela")

    add("التنبيهات المستنبطة", "Al-Tanbihat al-Mustanbata", "القاضي عياض",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="المدونة الكبرى", desc_ar="ملاحظات نقدية على المدونة والمختلطة", source="shamela")

    add("إكمال المعلم بفوائد مسلم", "Ikmal al-Mu'lim", "القاضي عياض",
        TextType.SHARH, StudyLevel.SPECIALIST,
        desc_ar="إتمام شرح المازري على صحيح مسلم، تحفة في الفقه المالكي", source="shamela")

    add("ترتيب المدارك", "Tartib al-Madarik", "القاضي عياض",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أوسع كتاب في تراجم علماء المذهب المالكي", source="shamela")

    # ============ 6th-7th CENTURY — SYSTEMATIC TEXTS ============

    add("بداية المجتهد", "Bidayat al-Mujtahid", "ابن رشد الحفيد", TextType.MATN, StudyLevel.ADVANCED,
        desc_ar="كتاب فقه مقارن يعرض أقوال المذاهب بأدلتها وأسباب اختلافها", source="shamela")

    add("عقد الجواهر الثمينة", "Iqd al-Jawahir al-Thamina", "ابن شاس",
        TextType.MATN, StudyLevel.ADVANCED,
        desc_ar="عرض منظم للفقه المالكي، سبق مختصر خليل", source="shamela")

    add("جامع الأمهات", "Jami' al-Ummahat", "ابن الحاجب", TextType.MATN, StudyLevel.ADVANCED,
        short="مختصر ابن الحاجب",
        desc_ar="مختصر فقهي كان المعتمد قبل مختصر خليل", source="shamela")

    add("الذخيرة", "Al-Dhakhira", "القرافي", TextType.ENCYCLOPEDIA, StudyLevel.SPECIALIST,
        desc_ar="موسوعة فقهية ضخمة من أوسع كتب المذهب", source="shamela")

    add("مختصر خليل", "Mukhtasar Khalil", "خليل بن إسحاق", TextType.MATN, StudyLevel.ADVANCED,
        desc_ar="أهم متن في المذهب المالكي بعد الموطأ، عليه أكثر الشروح", source="shamela")

    add("المختصر الفقهي", "Al-Mukhtasar al-Fiqhi", "ابن عرفة", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="مختصر فقهي مشهور بدقة الحدود والتعريفات", source="shamela")

    add("تحفة الحكام", "Tuhfat al-Hukkam", "ابن عاصم", TextType.NAZM, StudyLevel.ADVANCED,
        desc_ar="نظم في القضاء والعقود والأحكام، حوالي 1680 بيتا", source="shamela")

    add("مختصر الأخضري", "Mukhtasar al-Akhdari", "الأخضري", TextType.MATN, StudyLevel.BEGINNER,
        desc_ar="متن مختصر في الطهارة والصلاة، أول ما يحفظه طالب العلم", source="shamela")

    add("المرشد المعين", "Al-Murshid al-Mu'in", "ابن عاشر", TextType.NAZM, StudyLevel.BEGINNER,
        short="ابن عاشر",
        desc_ar="منظومة في العقيدة والفقه والتصوف، حوالي 317 بيتا", source="shamela")

    add("العشماوية", "Al-Ashmawiyya", "أبو الحسن المالكي", TextType.MATN, StudyLevel.BEGINNER,
        desc_ar="متن مختصر جدا في العبادات للمبتدئين", source="shamela")

    add("أقرب المسالك", "Aqrab al-Masalik", "الدردير", TextType.MATN, StudyLevel.INTERMEDIATE,
        desc_ar="متن مختصر للدردير، أيسر من مختصر خليل", source="shamela")

    add("عقد الجواهر الثمينة", "Iqd al-Jawahir al-Thamina", "ابن شاس",
        TextType.MATN, StudyLevel.ADVANCED,
        desc_ar="عرض منظم للفقه المالكي، سبق مختصر خليل", source="shamela")

    add("لامية الزقاق", "Lamiyyat al-Zaqqaq", "الزقاق", TextType.NAZM, StudyLevel.ADVANCED,
        desc_ar="منظومة في القواعد الفقهية المالكية", source="shamela")

    add("بداية المجتهد", "Bidayat al-Mujtahid", "ابن رشد الحفيد", TextType.MATN, StudyLevel.ADVANCED,
        desc_ar="كتاب فقه مقارن يعرض أقوال المذاهب بأدلتها وأسباب اختلافها", source="shamela")

    # ============ SHURUH on الموطأ ============

    add("التمهيد", "Al-Tamhid", "ابن عبد البر", TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="الموطأ", desc_ar="شرح أسانيد ومعاني أحاديث الموطأ", source="shamela")

    add("الاستذكار", "Al-Istidhkar", "ابن عبد البر", TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="الموطأ", desc_ar="شرح فقهي مقارن على الموطأ", source="shamela")

    add("المنتقى شرح الموطأ", "Al-Muntaqa", "الباجي", TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="الموطأ", desc_ar="شرح حديثي فقهي مهم على الموطأ", source="shamela")

    add("شرح الزرقاني على الموطأ", "Sharh al-Zurqani ala al-Muwatta", "الزرقاني (محمد)",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="الموطأ", desc_ar="أشهر شرح متأخر على الموطأ", source="shamela")

    add("تنوير الحوالك", "Tanwir al-Hawalik", "السيوطي", TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="الموطأ", desc_ar="شرح مختصر على الموطأ", source="shamela")

    # ============ SHURUH on الرسالة ============

    add("كفاية الطالب الرباني", "Kifayat al-Talib al-Rabbani", "أبو الحسن المالكي",
        TextType.SHARH, StudyLevel.BEGINNER,
        parent_key="الرسالة", desc_ar="الشرح المعتمد على الرسالة", source="shamela")

    add("الفواكه الدواني", "Al-Fawākih al-Dawani", "النفراوي", TextType.SHARH, StudyLevel.BEGINNER,
        parent_key="الرسالة", desc_ar="شرح مفصل على الرسالة", source="shamela")

    add("الثمر الداني", "Al-Thamar al-Dani", "صالح الأزهري", TextType.SHARH, StudyLevel.BEGINNER,
        parent_key="الرسالة", desc_ar="شرح متأخر ميسر على الرسالة", source="shamela")

    # ============ HAWASHI on الرسالة ============

    add("حاشية العدوي على كفاية الطالب", "Hashiyat al-Adawi ala Kifayat al-Talib", "العدوي",
        TextType.HASHIYA, StudyLevel.INTERMEDIATE,
        parent_key="كفاية الطالب الرباني", desc_ar="حاشية على شرح أبي الحسن على الرسالة", source="shamela")

    # ============ SHURUH on مختصر خليل ============

    add("مواهب الجليل", "Mawahib al-Jalil", "الحطاب", TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="مختصر خليل", desc_ar="من أعظم وأوسع شروح مختصر خليل", source="shamela")

    add("التاج والإكليل", "Al-Taj wal-Iklil", "المواق", TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="مختصر خليل", desc_ar="شرح يستخرج نصوص المدونة والأمهات", source="shamela")

    add("شرح الزرقاني على مختصر خليل", "Sharh al-Zurqani ala Khalil", "الزرقاني (عبد الباقي)",
        TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="مختصر خليل", desc_ar="شرح واضح ومنظم على مختصر خليل", source="shamela")

    add("شرح الخرشي على مختصر خليل", "Sharh al-Kharshi", "الخرشي", TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="مختصر خليل", desc_ar="أول شرح مصري على مختصر خليل، معتمد بالأزهر", source="shamela")

    add("الشرح الكبير", "Al-Sharh al-Kabir", "الدردير", TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="مختصر خليل", desc_ar="من أهم شروح مختصر خليل، المعتمد للفتوى", source="shamela")

    add("منح الجليل", "Minah al-Jalil", "عليش", TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="مختصر خليل", desc_ar="آخر الشروح الكبرى على مختصر خليل، 9 مجلدات", source="shamela")

    add("جواهر الإكليل", "Jawahir al-Iklil", "صالح الأزهري", TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="مختصر خليل", desc_ar="شرح ملخص ميسر على مختصر خليل", source="shamela")

    # ============ SHURUH on أقرب المسالك ============

    add("الشرح الصغير", "Al-Sharh al-Saghir", "الدردير", TextType.SHARH, StudyLevel.INTERMEDIATE,
        parent_key="أقرب المسالك", desc_ar="شرح الدردير على متنه أقرب المسالك", source="shamela")

    # ============ HAWASHI ============

    add("حاشية الدسوقي على الشرح الكبير", "Hashiyat al-Dusuqi", "الدسوقي",
        TextType.HASHIYA, StudyLevel.ADVANCED,
        parent_key="الشرح الكبير", desc_ar="الحاشية المعتمدة على الشرح الكبير للدردير", source="shamela")

    add("بلغة السالك", "Bulghat al-Salik", "الصاوي", TextType.HASHIYA, StudyLevel.INTERMEDIATE,
        parent_key="الشرح الصغير", desc_ar="حاشية على الشرح الصغير للدردير", source="shamela")

    add("حاشية العدوي على الخرشي", "Hashiyat al-Adawi ala al-Kharshi", "العدوي",
        TextType.HASHIYA, StudyLevel.ADVANCED,
        parent_key="شرح الخرشي على مختصر خليل", desc_ar="حاشية على شرح الخرشي", source="shamela")

    add("حاشية البناني على الزرقاني", "Hashiyat al-Bannani", "البناني",
        TextType.HASHIYA, StudyLevel.ADVANCED,
        parent_key="شرح الزرقاني على مختصر خليل", desc_ar="حاشية على شرح الزرقاني على مختصر خليل", source="shamela")

    # ============ SHURUH on ابن عاشر ============

    add("الدر الثمين والمورد المعين (شرح ميارة الكبير)", "Sharh Mayyara al-Kubra", "ميارة",
        TextType.SHARH, StudyLevel.BEGINNER,
        parent_key="المرشد المعين", desc_ar="أهم شرح على منظومة ابن عاشر", source="shamela")

    # ============ SHURUH on تحفة الحكام ============

    add("شرح ميارة على التحفة", "Sharh Mayyara ala al-Tuhfa", "ميارة",
        TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="تحفة الحكام", desc_ar="شرح على نظم تحفة الحكام لابن عاصم", source="shamela")

    # ============ OTHER IMPORTANT WORKS ============

    add("التبصرة", "Al-Tabsira", "اللخمي", TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="المدونة الكبرى", desc_ar="تعليق نقدي على المدونة", source="shamela")

    add("البيان والتحصيل", "Al-Bayan wal-Tahsil", "ابن رشد الجد",
        TextType.SHARH, StudyLevel.SPECIALIST,
        desc_ar="شرح ضخم على المستخرجة (العتبية)، 20 مجلدا", source="shamela")

    add("المقدمات الممهدات", "Al-Muqaddimat", "ابن رشد الجد",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="مقدمات أصولية لأبواب الفقه", source="shamela")

    add("المعيار المعرب", "Al-Mi'yar al-Mu'rib", "الونشريسي",
        TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="مجموعة فتاوى ضخمة من علماء المغرب والأندلس، 12+ مجلدا", source="shamela")

    add("شرح حدود ابن عرفة", "Sharh Hudud Ibn Arafa", "الرصاع",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="المختصر الفقهي",
        desc_ar="شرح التعريفات الفقهية الدقيقة لابن عرفة", source="shamela")

    add("أسهل المدارك", "Ashal al-Madarik", "الكشناوي", TextType.SHARH, StudyLevel.INTERMEDIATE,
        desc_ar="شرح فقهي مالكي مشهور في غرب أفريقيا", source="shamela")

    # ============ 7th-8th CENTURY — ENCYCLOPEDIAS & METHODOLOGY ============

    add("الذخيرة", "Al-Dhakhira", "القرافي", TextType.ENCYCLOPEDIA, StudyLevel.SPECIALIST,
        desc_ar="موسوعة فقهية ضخمة في 14 مجلدا، من أوسع كتب المذهب", source="shamela")

    add("الفروق", "Al-Furuq", "القرافي", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="548 فرقا و540 قاعدة فقهية، أساسي في القواعد الفقهية", source="shamela")

    add("القوانين الفقهية", "Al-Qawanin al-Fiqhiyya", "ابن جزي", TextType.MATN, StudyLevel.INTERMEDIATE,
        desc_ar="ملخص واضح في الفقه المقارن، أساسا مالكي", source="shamela")

    add("إرشاد السالك", "Irshad al-Salik", "ابن عسكر", TextType.MATN, StudyLevel.INTERMEDIATE,
        desc_ar="دليل موجز في الفقه المالكي", source="shamela")

    add("المدخل", "Al-Madkhal", "ابن الحاج", TextType.MATN, StudyLevel.INTERMEDIATE,
        desc_ar="في آداب العبادات وإصلاح البدع من منظور مالكي", source="shamela")

    add("الموافقات", "Al-Muwafaqat", "الشاطبي", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أول تأسيس منهجي لمقاصد الشريعة، توجه مالكي", source="shamela")

    add("الاعتصام", "Al-I'tisam", "الشاطبي", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أول عمل منهجي في تصنيف البدع", source="shamela")

    add("تبصرة الحكام", "Tabsirat al-Hukkam", "ابن فرحون", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="أصول القضاء والأحكام في الفقه المالكي، مرجع القضاة", source="shamela")

    add("العقد المنظم للحكام", "Al-Iqd al-Munazzam", "ابن سلمون", TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="في الوثائق والعقود والأحكام القضائية المالكية", source="shamela")

    add("التنبيه على مبادئ التوجيه", "Al-Tanbih (Ibn Bashir)", "ابن بشير",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="منهجية الاستدلال وأسباب الخلاف داخل المذهب، اعتمده خليل", source="shamela")

    # ============ 8th CENTURY — SHURUH on مختصر خليل (early) ============

    add("التوضيح شرح مختصر ابن الحاجب", "Al-Tawdih", "خليل بن إسحاق",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="جامع الأمهات", desc_ar="أهم شرح على مختصر ابن الحاجب، 9 مجلدات", source="shamela")

    add("المنزع النبيل شرح مختصر خليل", "Al-Manza' al-Nabil", "ابن مرزوق الحفيد",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="مختصر خليل", desc_ar="أقدم شرح على مختصر خليل، 10 مجلدات", source="shamela")

    add("الشرح الكبير لبهرام", "Sharh Bahram al-Kabir", "بهرام",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="مختصر خليل", desc_ar="أكبر شروح بهرام الثلاثة على مختصر خليل", source="shamela")

    add("شفاء الغليل في حل مقفل خليل", "Shifa' al-Ghalil", "ابن غازي",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="مختصر خليل", desc_ar="حل المشكلات والعبارات الصعبة في مختصر خليل", source="shamela")

    # ============ 9th CENTURY — NAWAZIL & FATAWA ============

    add("نوازل البرزلي", "Nawazil al-Burzuli", "البرزلي", TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="مجموعة فتاوى ونوازل مهمة، تلميذ ابن عرفة 40 سنة", source="shamela")

    add("الدرر المكنونة في نوازل مازونة", "Al-Durar al-Maknuna", "المازوني",
        TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="نوازل علماء تونس والجزائر، مرجع قضائي", source="shamela")

    add("نوازل ابن هلال", "Nawazil Ibn Hilal", "ابن هلال السجلماسي",
        TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="فتاوى مفتي سجلماسة", source="shamela")

    add("إيضاح المسالك إلى قواعد مالك", "Idah al-Masalik", "الونشريسي",
        TextType.MATN, StudyLevel.SPECIALIST,
        desc_ar="118 قاعدة فقهية مالكية", source="shamela")

    add("شرح ابن ناجي على الرسالة", "Sharh Ibn Naji ala al-Risala", "ابن ناجي",
        TextType.SHARH, StudyLevel.INTERMEDIATE,
        parent_key="الرسالة", desc_ar="من أعظم شروح الرسالة", source="shamela")

    add("شرح زروق على الرسالة", "Sharh Zarruq ala al-Risala", "زروق",
        TextType.SHARH, StudyLevel.INTERMEDIATE,
        parent_key="الرسالة", desc_ar="شرح صوفي مالكي مهم على الرسالة", source="shamela")

    # ============ 10th-11th CENTURY ADDITIONS ============

    add("المنهج المنتخب شرح لامية الزقاق", "Sharh al-Manhaj al-Muntakhab", "المنجور",
        TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="لامية الزقاق", desc_ar="أشهر شرح على لامية الزقاق في القواعد الفقهية", source="shamela")

    # ============ 12th-13th CENTURY ADDITIONS ============

    add("حاشية الرهوني على الزرقاني", "Hashiyat al-Rahuni", "الرهوني",
        TextType.HASHIYA, StudyLevel.SPECIALIST,
        parent_key="شرح الزرقاني على مختصر خليل",
        desc_ar="حاشية مغربية مهمة في 8 مجلدات، تصحيحات على الزرقاني", source="shamela")

    add("البهجة في شرح التحفة", "Al-Bahja", "التسولي",
        TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="تحفة الحكام", desc_ar="أوسع شرح على نظم تحفة الحكام لابن عاصم", source="shamela")

    add("حلى المعاصم شرح تحفة ابن عاصم", "Hulal al-Ma'asim", "التاودي",
        TextType.SHARH, StudyLevel.ADVANCED,
        parent_key="تحفة الحكام", desc_ar="شرح مغربي مهم على تحفة الحكام", source="shamela")

    # ============ MAURITANIAN / SHINQITI TEXTS ============

    add("مراقي السعود", "Maraqi al-Su'ud", "الشنقيطي (مراقي السعود)",
        TextType.NAZM, StudyLevel.SPECIALIST,
        desc_ar="1000 بيت في أصول الفقه، المتن المعتمد في موريتانيا", source="shamela")

    add("نشر البنود على مراقي السعود", "Nashr al-Bunud", "الشنقيطي (مراقي السعود)",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="مراقي السعود", desc_ar="شرح المؤلف على نظمه", source="shamela")

    # ============ NAWAZIL COLLECTIONS (late) ============

    add("المعيار الجديد (النوازل الجديدة الكبرى)", "Al-Mi'yar al-Jadid", "الوزاني",
        TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="12 مجلدا، استمرار للمعيار المعرب للونشريسي", source="shamela")

    add("النوازل الصغرى", "Al-Nawazil al-Sughra", "الوزاني",
        TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="مجموعة فتاوى أصغر من المعيار الجديد", source="shamela")

    # ============ MODERN TEXTS ============

    add("كشف المغطى شرح الموطأ", "Kashf al-Mughatta", "ابن عاشور",
        TextType.SHARH, StudyLevel.SPECIALIST,
        parent_key="الموطأ", desc_ar="شرح معاصر مهم على الموطأ", source="shamela")

    add("مدونة الفقه المالكي وأدلته", "Mudawwanat al-Fiqh al-Maliki", "الغرياني",
        TextType.ENCYCLOPEDIA, StudyLevel.ADVANCED,
        desc_ar="موسوعة فقهية مالكية معاصرة بالأدلة، 5 مجلدات", source="archive")

    add("فتح العلي المالك", "Fath al-Ali al-Malik", "عليش",
        TextType.FATAWA, StudyLevel.SPECIALIST,
        desc_ar="فتاوى عليش على مذهب مالك، مجلدان", source="shamela")

    # ============ DATA SOURCES (Encyclopedias) ============

    add("الموسوعة الفقهية الكويتية", "Kuwaiti Fiqh Encyclopedia", "القاضي عبد الوهاب",  # placeholder author
        TextType.ENCYCLOPEDIA, StudyLevel.SPECIALIST,
        desc_ar="موسوعة فقهية شاملة في 45 مجلدا تغطي المذاهب الأربعة", source="mawsua_fiqhiya")

    return books


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_sess = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_sess() as session:
        # Insert authors
        author_map = {}
        for a in AUTHORS:
            author = Author(
                name_ar=a[0], name_en=a[1], full_name_ar=a[2],
                death_hijri=a[3], death_ce=a[4], century_hijri=a[5], region=a[6],
            )
            session.add(author)
            await session.flush()
            author_map[a[0]] = author.id

        # Insert books
        book_records = build_books(author_map)
        book_id_map = {}
        for b in book_records:
            book = Book(
                title_ar=b["title_ar"],
                title_en=b["title_en"],
                short_title_ar=b["short_title_ar"],
                author_id=author_map[b["author_key"]],
                text_type=b["text_type"],
                study_level=b["study_level"],
                parent_book_id=book_id_map.get(b["parent_key"]),
                description_ar=b["description_ar"],
                source_name=b["source_name"],
            )
            session.add(book)
            await session.flush()
            book_id_map[b["title_ar"]] = book.id

        await session.commit()
        print(f"Seeded {len(author_map)} authors and {len(book_records)} books.")


if __name__ == "__main__":
    asyncio.run(seed())
