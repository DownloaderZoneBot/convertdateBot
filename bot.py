import logging
import os
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from hijri_converter import Hijri, Gregorian

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

ARABIC_MONTHS = {
    "يناير": 1, "فبراير": 2, "مارس": 3, "إبريل": 4, "ابريل": 4,
    "مايو": 5, "يونيو": 6, "يوليو": 7, "أغسطس": 8, "اغسطس": 8,
    "سبتمبر": 9, "أكتوبر": 10, "اكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12,
    "محرم": 1, "صفر": 2, "ربيع الأول": 3, "ربيع الثاني": 4, 
    "جمادى الأولى": 5, "جمادى الآخرة": 6, "رجب": 7, "شعبان": 8, 
    "رمضان": 9, "شوال": 10, "ذو القعدة": 11, "ذو الحجة": 12
}

def extract_date_components(text):
    # دالة جديدة لاستخراج المكونات بشكل أفضل
    text = re.sub(r'[،\-/_]', ' ', text)  # استبدال الفواصل بمسافات
    parts = re.split(r'\s+', text.strip())
    
    day = None
    month = None
    year = None
    
    for part in parts:
        if part.isdigit():
            num = int(part)
            if 1 <= num <= 31:
                if day is None:
                    day = num
                else:
                    year = num
            else:
                year = num
        else:
            for name, num in ARABIC_MONTHS.items():
                if name in part or name.replace(' ', '') in part:
                    month = num
                    break
    
    return day, month, year

def parse_text_to_gregorian(text):
    day, month, year = extract_date_components(text)
    
    if not all([day, month]):
        raise ValueError("مكونات التاريخ ناقصة")
    
    if year is None:
        year = datetime.now().year
        
    return Gregorian(year, month, day)

def parse_text_to_hijri(text):
    day, month, year = extract_date_components(text)
    
    if not all([day, month]):
        raise ValueError("مكونات التاريخ ناقصة")
    
    if year is None:
        year = Hijri.today().year
        
    return Hijri(year, month, day)

def detect_and_convert(text):
    text = text.strip()
    original_text = text
    
    try:
        # محاولة التحليل المباشر للصيغ الرقمية أولاً
        if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', text):
            year, month, day = map(int, text.split('-'))
            g = Gregorian(year, month, day)
            h = Hijri.from_gregorian(year, month, day)
        elif re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', text):
            day, month, year = map(int, text.split('-'))
            g = Gregorian(year, month, day)
            h = Hijri.from_gregorian(year, month, day)
        else:
            # معالجة الحالات النصية
            text_lower = text.lower()
            if text_lower in ["اليوم", "today"]:
                today = datetime.now()
                g = Gregorian(today.year, today.month, today.day)
                h = Hijri.from_gregorian(today.year, today.month, today.day)
            elif text_lower in ["غدًا", "غدا", "غداً", "tomorrow"]:
                tomorrow = datetime.now() + timedelta(days=1)
                g = Gregorian(tomorrow.year, tomorrow.month, tomorrow.day)
                h = Hijri.from_gregorian(g.year, g.month, g.day)
            elif text_lower in ["أمس", "yesterday", "امس"]:
                yesterday = datetime.now() - timedelta(days=1)
                g = Gregorian(yesterday.year, yesterday.month, yesterday.day)
                h = Hijri.from_gregorian(g.year, g.month, g.day)
            else:
                # محاولة التحليل كتاريخ هجري أو ميلادي نصي
                try:
                    g = parse_text_to_gregorian(original_text)
                    h = Hijri.from_gregorian(g.year, g.month, g.day)
                except:
                    h = parse_text_to_hijri(original_text)
                    g = h.to_gregorian()
        
        # التحقق من صحة التاريخ
        g.to_date()  # سيthrow خطأ إذا كان التاريخ غير صالح
        h.to_date()
        
        weekday = g.to_date().strftime('%A')
        days_ar = {
            "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين",
            "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
            "Thursday": "الخميس", "Friday": "الجمعة"
        }
        return g, h, days_ar.get(weekday, weekday)
    
    except Exception as e:
        raise ValueError(f"لا يمكن تحويل التاريخ: {str(e)}")

@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await message.reply(
        "مرحبًا! أرسل تاريخًا هجريًا أو ميلاديًا لتحويله.\n"
        "أمثلة:\n"
        "• 25 رمضان 1445\n"
        "• 2023-10-05\n"
        "• 5 شوال\n"
        "• غدًا"
    )

@dp.message_handler()
async def convert(message: types.Message):
    try:
        g, h, weekday = detect_and_convert(message.text)
        response = (
            f"📅 الميلادي: {g.year}-{g.month:02d}-{g.day:02d}\n"
            f"🕌 الهجري: {h.year}-{h.month:02d}-{h.day:02d}\n"
            f"📆 اليوم: {weekday}"
        )
        await message.reply(response)
    except Exception as e:
        await message.reply(
            f"❌ خطأ في التحويل: {str(e)}\n"
            "الرجاء استخدام إحدى الصيغ التالية:\n"
            "• يوم شهر سنة (مثال: 25 رمضان 1445)\n"
            "• سنة-شهر-يوم (مثال: 2023-10-05)\n"
            "• يوم-شهر-سنة (مثال: 05-10-2023)"
        )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
