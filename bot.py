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
    "محرم": 1, "صفر": 2, "ربيع الأول": 3, "ربيع الثاني": 4, "جمادى الأولى": 5,
    "جمادى الآخرة": 6, "رجب": 7, "شعبان": 8, "رمضان": 9, "شوال": 10, 
    "ذو القعدة": 11, "ذو الحجة": 12
}

def parse_text_to_gregorian(text):
    text_lower = text.lower()
    for name, number in ARABIC_MONTHS.items():
        if name.lower() in text_lower:
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:
                day = int(numbers[0])
                year = int(numbers[-1]) if len(numbers) > 2 else datetime.now().year
                return Gregorian(year, number, day)
    raise ValueError("تاريخ ميلادي غير صالح")

def parse_text_to_hijri(text):
    text_lower = text.lower()
    for name, number in ARABIC_MONTHS.items():
        if name.lower() in text_lower:
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:
                day = int(numbers[0])
                year = int(numbers[-1]) if len(numbers) > 2 else Hijri.today().year
                return Hijri(year, number, day)
    raise ValueError("تاريخ هجري غير صالح")

def detect_and_convert(text):
    text = text.strip().lower()
    
    # معالجة الكلمات المفتاحية
    if text in ["اليوم", "today"]:
        today = datetime.now()
        g = Gregorian(today.year, today.month, today.day)
        h = Hijri.from_gregorian(today.year, today.month, today.day)
    elif text in ["غدًا", "غدا", "غداً", "tomorrow"]:
        tomorrow = datetime.now() + timedelta(days=1)
        g = Gregorian(tomorrow.year, tomorrow.month, tomorrow.day)
        h = Hijri.from_gregorian(g.year, g.month, g.day)
    elif text in ["أمس", "yesterday", "امس"]:
        yesterday = datetime.now() - timedelta(days=1)
        g = Gregorian(yesterday.year, yesterday.month, yesterday.day)
        h = Hijri.from_gregorian(g.year, g.month, g.day)
    else:
        try:  # حاول تحليل كتاريخ ميلادي
            g = parse_text_to_gregorian(text)
            h = Hijri.from_gregorian(g.year, g.month, g.day)
        except:
            try:  # حاول تحليل كتاريخ هجري
                h = parse_text_to_hijri(text)
                g = h.to_gregorian()
            except:
                raise ValueError("صيغة غير معروفة")

    # تحويل اليوم إلى عربي
    weekday = g.to_date().strftime('%A')
    days_ar = {
        "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين",
        "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
        "Thursday": "الخميس", "Friday": "الجمعة"
    }
    return g, h, days_ar.get(weekday, weekday)

@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await message.reply("مرحبًا! أرسل تاريخًا هجريًا أو ميلاديًا لتحويله.\nمثال: 25 رمضان 1445 أو 2023-04-14")

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
        await message.reply(f"❌ خطأ: {str(e)}\nالرجاء استخدام صيغة مثل '25 رمضان 1445' أو '2023-04-14'")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
