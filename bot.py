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
    "جمادى الآخرة": 6, "رجب": 7, "شعبان": 8, "رمضان": 9, "شوال": 10, "ذو القعدة": 11, "ذو الحجة": 12
}

def parse_text_to_gregorian(text):
    for name, number in ARABIC_MONTHS.items():
        if name in text:
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:
                day = int(numbers[0])
                year = int(numbers[1]) if len(numbers) > 2 else datetime.now().year
                return Gregorian(year, number, day)
    raise ValueError("تعذر فهم التاريخ الميلادي بالنص.")

def parse_text_to_hijri(text):
    for name, number in ARABIC_MONTHS.items():
        if name in text:
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:
                day = int(numbers[0])
                year = int(numbers[1]) if len(numbers) > 2 else Hijri.today().year
                return Hijri(year, number, day)
    raise ValueError("تعذر فهم التاريخ الهجري بالنص.")

def detect_and_convert(text):
    text = text.strip().lower()

    # الكلمات الذكية
    if text in ["اليوم", "today"]:
        g = Gregorian.today()
        h = Hijri.from_gregorian(g.year, g.month, g.day)
    elif text in ["غدًا", "غدا", "غداً", "tomorrow"]:
        g = Gregorian.today().to_date() + timedelta(days=1)
        g = Gregorian(g.year, g.month, g.day)
        h = Hijri.from_gregorian(g.year, g.month, g.day)
    elif text in ["أمس", "امس", "yesterday"]:
        g = Gregorian.today().to_date() - timedelta(days=1)
        g = Gregorian(g.year, g.month, g.day)
        h = Hijri.from_gregorian(g.year, g.month, g.day)
    else:
        # محاولة تلقائية
        try:
            g = parse_gregorian(text)
            h = Hijri.from_gregorian(g.year, g.month, g.day)
        except:
            try:
                h = parse_hijri(text)
                g = h.to_gregorian()
            except:
                try:
                    g = parse_text_to_gregorian(text)
                    h = Hijri.from_gregorian(g.year, g.month, g.day)
                except:
                    h = parse_text_to_hijri(text)
                    g = h.to_gregorian()

    weekday = g.to_date().strftime('%A')
    days_ar = {
        "Saturday": "السبت", "Sunday": "الأحد", "Monday": "الاثنين",
        "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
        "Thursday": "الخميس", "Friday": "الجمعة"
    }
    return g, h, days_ar.get(weekday, weekday)

def parse_gregorian(text):
    patterns = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            else:
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
            return Gregorian(year, month, day)
    raise ValueError

def parse_hijri(text):
    patterns = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            else:
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
            return Hijri(year, month, day)
    raise ValueError

@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await message.reply("أهلًا بك! 🗓️
أرسل أي تاريخ هجري أو ميلادي وسأقوم بتحويله فورًا!")

@dp.message_handler()
async def convert(message: types.Message):
    try:
        g, h, weekday = detect_and_convert(message.text)
        await message.reply(
            f"📆 الميلادي: {g.year}-{g.month:02d}-{g.day:02d}
"
            f"🕌 الهجري: {h.year}-{h.month:02d}-{h.day:02d}
"
            f"📅 اليوم: {weekday}"
        )
    except Exception as e:
        await message.reply("❌ عذرًا، لم أتمكن من فهم هذا التاريخ. يرجى استخدام صيغة يوم/شهر/سنة أو كلمات مثل 'اليوم'.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
