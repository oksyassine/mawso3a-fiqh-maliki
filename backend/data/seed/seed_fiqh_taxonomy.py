"""Seed the standard fiqh taxonomy (abwab al-fiqh) used across all Maliki texts."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.base import Base, FiqhCategory

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/mawso3a_fiqh"

# Standard Maliki fiqh chapters — matches the order in Mukhtasar Khalil and most mutoon
TAXONOMY = [
    ("كتاب الطهارة", "Tahara (Purification)", [
        ("باب المياه", "Types of Water"),
        ("باب الوضوء", "Wudu"),
        ("باب فرائض الوضوء", "Obligations of Wudu"),
        ("باب سنن الوضوء", "Sunnahs of Wudu"),
        ("باب نواقض الوضوء", "Nullifiers of Wudu"),
        ("باب الغسل", "Ghusl"),
        ("باب التيمم", "Tayammum"),
        ("باب المسح على الخفين", "Wiping over Khuffs"),
        ("باب إزالة النجاسة", "Removing Impurity"),
        ("باب الحيض والنفاس", "Menstruation and Postpartum"),
    ]),
    ("كتاب الصلاة", "Salat (Prayer)", [
        ("باب المواقيت", "Prayer Times"),
        ("باب الأذان والإقامة", "Adhan and Iqama"),
        ("باب شروط الصلاة", "Conditions of Prayer"),
        ("باب فرائض الصلاة", "Obligations of Prayer"),
        ("باب سنن الصلاة", "Sunnahs of Prayer"),
        ("باب سجود السهو", "Prostration of Forgetfulness"),
        ("باب صلاة الجماعة", "Congregational Prayer"),
        ("باب الإمامة", "Leading Prayer"),
        ("باب صلاة المسافر", "Traveler's Prayer"),
        ("باب صلاة الجمعة", "Friday Prayer"),
        ("باب صلاة العيدين", "Eid Prayers"),
        ("باب صلاة الكسوف", "Eclipse Prayer"),
        ("باب صلاة الاستسقاء", "Rain Prayer"),
        ("باب صلاة الجنازة", "Funeral Prayer"),
        ("باب صلاة النوافل", "Voluntary Prayers"),
    ]),
    ("كتاب الزكاة", "Zakat", [
        ("باب زكاة النقدين", "Zakat on Gold and Silver"),
        ("باب زكاة الأنعام", "Zakat on Livestock"),
        ("باب زكاة الحبوب والثمار", "Zakat on Crops"),
        ("باب زكاة التجارة", "Zakat on Trade Goods"),
        ("باب زكاة الفطر", "Zakat al-Fitr"),
        ("باب مصارف الزكاة", "Recipients of Zakat"),
    ]),
    ("كتاب الصيام", "Siyam (Fasting)", [
        ("باب وجوب الصوم", "Obligation of Fasting"),
        ("باب فرائض الصوم", "Obligations of Fasting"),
        ("باب مفسدات الصوم", "Nullifiers of Fasting"),
        ("باب الكفارة", "Expiation"),
        ("باب صوم التطوع", "Voluntary Fasting"),
        ("باب الاعتكاف", "I'tikaf"),
    ]),
    ("كتاب الحج", "Hajj (Pilgrimage)", [
        ("باب وجوب الحج", "Obligation of Hajj"),
        ("باب المواقيت", "Miqat"),
        ("باب الإحرام", "Ihram"),
        ("باب أركان الحج", "Pillars of Hajj"),
        ("باب واجبات الحج", "Obligations of Hajj"),
        ("باب محظورات الإحرام", "Prohibitions of Ihram"),
        ("باب العمرة", "Umra"),
        ("باب الهدي والأضحية", "Sacrifice"),
    ]),
    ("كتاب الجهاد", "Jihad", [
        ("باب أحكام الجهاد", "Rulings of Jihad"),
        ("باب الأمان والعهد", "Treaty and Safety"),
        ("باب الغنائم", "War Spoils"),
    ]),
    ("كتاب الأيمان والنذور", "Oaths and Vows", [
        ("باب اليمين", "Oaths"),
        ("باب النذر", "Vows"),
        ("باب الكفارات", "Expiations"),
    ]),
    ("كتاب الأطعمة والأشربة", "Food and Drink", [
        ("باب الذبائح", "Slaughter"),
        ("باب الصيد", "Hunting"),
        ("باب المحرمات", "Prohibited Foods"),
    ]),
    ("كتاب النكاح", "Nikah (Marriage)", [
        ("باب أركان النكاح", "Pillars of Marriage"),
        ("باب شروط النكاح", "Conditions of Marriage"),
        ("باب الولاية", "Guardianship"),
        ("باب الصداق", "Dowry"),
        ("باب الكفاءة", "Compatibility"),
        ("باب العيوب", "Defects"),
        ("باب نكاح المتعة وغيره", "Types of Marriage"),
    ]),
    ("كتاب الطلاق", "Talaq (Divorce)", [
        ("باب أنواع الطلاق", "Types of Divorce"),
        ("باب الخلع", "Khul'"),
        ("باب الإيلاء", "Ila'"),
        ("باب الظهار", "Zihar"),
        ("باب اللعان", "Li'an"),
        ("باب العدة", "Waiting Period"),
        ("باب الرجعة", "Taking Back"),
        ("باب النفقة", "Maintenance"),
        ("باب الحضانة", "Custody"),
        ("باب الرضاع", "Breastfeeding"),
    ]),
    ("كتاب البيوع", "Buyu' (Transactions)", [
        ("باب شروط البيع", "Conditions of Sale"),
        ("باب البيوع المنهي عنها", "Prohibited Sales"),
        ("باب الخيار", "Option"),
        ("باب الربا", "Usury"),
        ("باب السلم", "Advance Payment"),
        ("باب القرض", "Loan"),
        ("باب الرهن", "Pledge"),
        ("باب الحوالة", "Transfer of Debt"),
        ("باب الضمان", "Guarantee"),
        ("باب الكفالة", "Surety"),
        ("باب الشركة", "Partnership"),
        ("باب المضاربة", "Silent Partnership"),
        ("باب المساقاة", "Crop Sharing"),
        ("باب الإجارة", "Lease/Hire"),
        ("باب الجعالة", "Reward"),
        ("باب الوكالة", "Agency"),
    ]),
    ("كتاب الفرائض", "Fara'id (Inheritance)", [
        ("باب أسباب الإرث", "Causes of Inheritance"),
        ("باب الحجب", "Exclusion"),
        ("باب الفروض", "Fixed Shares"),
        ("باب التعصيب", "Residuary Heirs"),
        ("باب الوصية", "Will/Bequest"),
    ]),
    ("كتاب القضاء", "Qada' (Judiciary)", [
        ("باب آداب القاضي", "Etiquette of the Judge"),
        ("باب الشهادة", "Testimony"),
        ("باب الدعوى", "Claims"),
        ("باب البينة", "Evidence"),
    ]),
    ("كتاب الحدود", "Hudud (Penal Law)", [
        ("باب حد الزنا", "Punishment for Adultery"),
        ("باب حد القذف", "Punishment for Slander"),
        ("باب حد السرقة", "Punishment for Theft"),
        ("باب حد الحرابة", "Punishment for Brigandage"),
        ("باب حد الشرب", "Punishment for Drinking"),
        ("باب حد الردة", "Punishment for Apostasy"),
    ]),
    ("كتاب الجنايات", "Jinayat (Criminal Law)", [
        ("باب القصاص", "Retaliation"),
        ("باب الدية", "Blood Money"),
        ("باب القسامة", "Compurgation"),
    ]),
    ("كتاب الوقف", "Waqf (Endowment)", [
        ("باب أحكام الوقف", "Rulings of Waqf"),
        ("باب شروط الوقف", "Conditions of Waqf"),
    ]),
    ("كتاب العتق", "Itq (Manumission)", [
        ("باب العتق", "Freeing Slaves"),
        ("باب التدبير", "Conditional Manumission"),
        ("باب المكاتبة", "Contracted Manumission"),
    ]),
]


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_sess = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_sess() as session:
        order = 0
        for kitab_ar, kitab_en, abwab in TAXONOMY:
            order += 1
            cat = FiqhCategory(name_ar=kitab_ar, name_en=kitab_en, order=order)
            session.add(cat)
            await session.flush()

            sub_order = 0
            for bab_ar, bab_en in abwab:
                sub_order += 1
                sub = FiqhCategory(
                    name_ar=bab_ar, name_en=bab_en,
                    parent_id=cat.id, order=sub_order,
                )
                session.add(sub)

        await session.commit()
        print(f"Seeded {order} categories with subcategories.")


if __name__ == "__main__":
    asyncio.run(seed())
