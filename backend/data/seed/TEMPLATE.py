"""Template for comparison seed data. Keep under 100 lines."""

# Each file exports a list like KITAB_DATA = [...]
# Each masala entry:
EXAMPLE = {
    "masala_key": "unique_key",       # unique ID
    "category": "باب الزكاة",         # bab name
    "title_ar": "حكم الزكاة",         # masala title
    "positions": [
        {
            "book": "الرسالة",         # book name
            "hukm": "wajib",           # wajib/mandub/mubah/makruh/haram/None
            "hukm_text_ar": "Arabic text from the matn",
            "dalil_ar": "evidence or empty string",
            "conditions_ar": "conditions or empty string",
        },
        # Repeat for: مختصر خليل, ابن عاشر, أقرب المسالك, المدونة
    ],
    "comparison": {
        "result": "ittifaq",           # ittifaq/ikhtilaf/tafsilat
        "summary_ar": "ملخص في جملة",
        "details_ar": "تفصيل كامل",
    },
}
