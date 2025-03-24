# bot.py

import logging
import os
import re
import tempfile
from aiogram import Bot, Dispatcher, executor, types
from hijri_converter import Hijri, Gregorian

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def parse_gregorian_date(text):
    """
    يحاول تفسير النص كتاريخ ميلادي بصيغ مختلفة: dd/mm/yyyy أو yyyy-mm-dd.
    يعيد كائن Gregorian أو يرمي استثناء.
    """
    patterns = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # yyyy-mm-dd
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # dd-mm-yyyy
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            groups = match.groups()
            # لو كانت الصيغة yyyy-mm-dd
            if len(groups[0]) == 4:
                year = int(groups[0])
                month = int(groups[1])
                day = int(groups[2])
            else:
                day = int(groups[0])
                month = int(groups[1])
                year = int(groups[2])

            return Gregorian(year, month, day)

    raise ValueError("Not a valid Gregorian date format")

def parse_hijri_date(text):
    """
    يحاول تفسير النص كتاريخ هجري بصيغ مختلفة: dd/mm/yyyy أو yyyy-mm-dd.
    يعيد كائن Hijri أو يرمي استثناء.
    """
    patterns = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', 
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})'
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:
                year = int(groups[0])
                month = int(groups[1])
                day = int(groups[2])
            else:
                day = int(groups[0])
                month = int(groups[1])
                year = int(groups[2])
            return Hijri(year, month, day)

    raise ValueError("Not a valid Hijri date format")

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(
        "أهلاً بك في بوت تحويل التاريخ!\n"
        "أرسل لي تاريخاً هجرياً أو ميلادياً بأي صيغة (مثل: 25/3/2025 أو 1445-09-15).\n"
        "وسأحاول اكتشاف نوع التاريخ تلقائياً."
    )

@dp.message_handler()
async def convert_date(message: types.Message):
    text = message.text.strip()

    # أولاً نجرّب التفسير كتاريخ ميلادي
    try:
        g = parse_gregorian_date(text)
        h = Hijri.from_gregorian(g.year, g.month, g.day)
        await message.reply(
            f"📅 التاريخ الميلادي: {g.year}-{g.month:02d}-{g.day:02d}\n"
            f"⇒ التاريخ الهجري: {h.year}-{h.month:02d}-{h.day:02d}"
        )
        return
    except:
        pass

    # إذا فشل التفسير الميلادي، نجرب التفسير الهجري
    try:
        h = parse_hijri_date(text)
        g = h.to_gregorian()
        await message.reply(
            f"📅 التاريخ الهجري: {h.year}-{h.month:02d}-{h.day:02d}\n"
            f"⇒ التاريخ الميلادي: {g.year}-{g.month:02d}-{g.day:02d}"
        )
    except:
        await message.reply("عذراً، لم أفهم هذا التاريخ. يرجى استخدام صيغة يوم/شهر/سنة.")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

