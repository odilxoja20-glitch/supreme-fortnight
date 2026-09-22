import logging
from datetime import datetime, timezone, timedelta
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# 1. ВСТАВЬ СЮДА ТОКЕН ИЗ BOTFATHER
TOKEN = "8916979998:AAG6VILIUhL74xkDhUgJIyMC2mdTa8dU3bA"

# Словарь для хранения выбранного класса пользователей: {user_id: "5-B" или "5-G"}
user_classes = {}

# 2. РАСПИСАНИЕ УРОКОВ ПО КЛАССАМ
SCHEDULES = {
    "5-B": {
        "Dushanba": [
            "1. Kelajak soati (08:00 - 08:45)",
            "2. Ona tili (08:50 - 09:35)",
            "3. Adabiyot (09:40 - 10:25)",
            "4. Matematika (10:40 - 11:25)",
            "5. Informatika (11:30 - 12:15)",
            "6. Rus tili (12:20 - 13:05)",
        ],
        "Seshanba": [
            "1. Tarix (08:00 - 08:45)",
            "2. Musiqa (08:50 - 09:35)",
            "3. Tasviriy san'at (09:40 - 10:25)",
            "4. Jismoniy madaniyat (10:40 - 11:25)",
            "5. Matematika (11:30 - 12:15)",
            "6. Ingliz tili (12:20 - 13:05)",
        ],
        "Chorshanba": [
            "1. Matematika (08:00 - 08:45)",
            "2. Ingliz tili (08:50 - 09:35)",
            "3. Ingliz tili (09:40 - 10:25)",
            "4. Ona tili (10:40 - 11:25)",
        ],
        "Payshanba": [
            "1. Tarbiya (08:00 - 08:45)",
            "2. Adabiyot (08:50 - 09:35)",
            "3. Science (09:40 - 10:25)",
            "4. Ingliz tili (10:40 - 11:25)",
        ],
        "Juma": [
            "1. Jismoniy madaniyat (08:00 - 08:45)",
            "2. Ona tili (08:50 - 09:35)",
            "3. Matematika (09:40 - 10:25)",
            "4. Texnologiya (10:40 - 11:25)",
            "5. Texnologiya (11:30 - 12:15)",
            "6. Science (12:20 - 13:05)",
        ],
        "Shanba": [
            "1. Ona tili (08:00 - 08:45)",
            "2. Rus tili (08:50 - 09:35)",
            "3. Matematika (09:40 - 10:25)",
            "4. Tarix (10:40 - 11:25)",
        ],
    },
    "5-G": {
        "Dushanba": [
            "1. Kelajak soati (13:15 - 14:00)",
            "2. Matematika (14:05 - 14:50)",
            "3. Ona tili (14:55 - 15:40)",
            "4. Tabiiy fan (15:45 - 16:30)",
            "5. Ingliz tili (16:35 - 17:20)",
        ],
        "Seshanba": [
            "1. Matematika (13:15 - 14:00)",
            "2. Ingliz tili (14:05 - 14:50)",
            "3. Tarix (14:55 - 15:40)",
            "4. Matematika (15:45 - 16:30)",
            "5. Tasviriy san'at (16:35 - 17:20)",
        ],
        "Chorshanba": [
            "1. Texnologiya (13:15 - 14:00)",
            "2. Texnologiya (14:05 - 14:50)",
            "3. Tarbiya (14:55 - 15:40)",
            "4. Rus tili (15:45 - 16:30)",
            "5. Informatika (16:35 - 17:20)",
        ],
        "Payshanba": [
            "1. Ona tili (13:15 - 14:00)",
            "2. Tarix (14:05 - 14:50)",
            "3. Jismoniy tarbiya (14:55 - 15:40)",
            "4. Adabiyot (15:45 - 16:30)",
            "5. Musiqa (16:35 - 17:20)",
        ],
        "Juma": [
            "1. Ona tili (13:15 - 14:00)",
            "2. Adabiyot (14:05 - 14:50)",
            "3. Matematika (14:55 - 15:40)",
            "4. Tabiiy fan (15:45 - 16:30)",
            "5. Jismoniy tarbiya (16:35 - 17:20)",
        ],
        "Shanba": [
            "1. Ona tili (13:15 - 14:00)",
            "2. Rus tili (14:05 - 14:50)",
            "3. Matematika (14:55 - 15:40)",
            "4. Ingliz tili (15:45 - 16:30)",
            "5. Ingliz tili (16:35 - 17:20)",
        ],
    }
}

# ЗВОНКИ 1 СМЕНЫ (5-B)
LESSONS_TIMES_1_SHIFT = [
    (1, "08:00", "08:45"),
    (2, "08:50", "09:35"),
    (3, "09:40", "10:25"),
    (4, "10:40", "11:25"),
    (5, "11:30", "12:15"),
    (6, "12:20", "13:05"),
]

# ЗВОНКИ 2 СМЕНЫ (5-G)
LESSONS_TIMES_2_SHIFT = [
    (1, "13:15", "14:00"),
    (2, "14:05", "14:50"),
    (3, "14:55", "15:40"),
    (4, "15:45", "16:30"),
    (5, "16:35", "17:20"),
    (6, "17:25", "18:10"),
]

DAYS_TRANSLATE = {
    0: "Dushanba",
    1: "Seshanba",
    2: "Chorshanba",
    3: "Payshanba",
    4: "Juma",
    5: "Shanba",
    6: "Yakshanba"
}

def get_uzbekistan_now():
    """Возвращает точное время в Ташкенте (UTC+5)."""
    tz = timezone(timedelta(hours=5))
    return datetime.now(tz)

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        ["📅 Bugun", "📆 Ertaga"],
        ["📌 Barcha kunlar", "⏰ Какой сейчас урок?"],
        ["🏫 Сменить класс (5-B / 5-G)"]
    ], resize_keyboard=True)

def get_class_select_keyboard():
    return ReplyKeyboardMarkup([
        ["5-B", "5-G"]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_classes:
        await update.message.reply_text(
            "Привет! Выбери свой класс:",
            reply_markup=get_class_select_keyboard()
        )
    else:
        current_class = user_classes[user_id]
        await update.message.reply_text(
            f"Привет! Твой выбранный класс: {current_class} 🚀\nВыбирай нужную кнопку внизу 👇",
            reply_markup=get_main_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    now = get_uzbekistan_now()

    # Обработка выбора класса
    if text in ["5-B", "5-G"]:
        user_classes[user_id] = text
        await update.message.reply_text(
            f"✅ Класс {text} успешно выбран!",
            reply_markup=get_main_keyboard()
        )
        return

    if text == "🏫 Сменить класс (5-B / 5-G)":
        await update.message.reply_text(
            "Выбери класс:",
            reply_markup=get_class_select_keyboard()
        )
        return

    # Проверка, выбран ли класс
    if user_id not in user_classes:
        await update.message.reply_text(
            "Пожалуйста, сначала выбери свой класс:",
            reply_markup=get_class_select_keyboard()
        )
        return

    selected_class = user_classes[user_id]
    schedule = SCHEDULES[selected_class]
    lessons_times = LESSONS_TIMES_1_SHIFT if selected_class == "5-B" else LESSONS_TIMES_2_SHIFT

    if text == "📅 Bugun":
        day_name = DAYS_TRANSLATE[now.weekday()]
        if day_name in schedule:
            lessons = "\n".join(schedule[day_name])
            await update.message.reply_text(f"📌 {day_name} ({selected_class}):\n{lessons}")
        else:
            await update.message.reply_text("🎉 Сегодня воскресенье! Уроков нет.")

    elif text == "📆 Ertaga":
        tomorrow = now + timedelta(days=1)
        day_name = DAYS_TRANSLATE[tomorrow.weekday()]
        if day_name in schedule:
            lessons = "\n".join(schedule[day_name])
            await update.message.reply_text(f"📌 {day_name} ({selected_class}):\n{lessons}")
        else:
            await update.message.reply_text("🎉 Завтра воскресенье! Отдыхай.")

    elif text == "📌 Barcha kunlar":
        all_schedule = f"🏫 Расписание для класса {selected_class}:\n\n"
        for day, lessons in schedule.items():
            all_schedule += f"📌 {day}:\n" + "\n".join(lessons) + "\n\n"
        await update.message.reply_text(all_schedule)

    elif text == "⏰ Какой сейчас урок?":
        if now.weekday() == 6:
            await update.message.reply_text("🎉 Сегодня воскресенье, уроков нет!")
            return

        day_name = DAYS_TRANSLATE[now.weekday()]
        today_lessons = schedule.get(day_name, [])
        
        lesson_found = False
        for i, start_str, end_str in lessons_times:
            if i > len(today_lessons):
                continue

            start_dt = datetime.strptime(start_str, "%H:%M").time()
            end_dt = datetime.strptime(end_str, "%H:%M").time()
            now_time = now.time()

            if start_dt <= now_time <= end_dt:
                lesson_found = True
                lesson_name = today_lessons[i - 1]
                
                end_datetime = datetime.combine(now.date(), end_dt, tzinfo=now.tzinfo)
                minutes_left = int((end_datetime - now).total_seconds() // 60)

                msg = (
                    f"🔔 Класс {selected_class} — сейчас идет урок №{i}:\n"
                    f"{lesson_name}\n\n"
                    f"⏳ До конца урока осталось: {minutes_left} мин."
                )
                await update.message.reply_text(msg)
                break

        if not lesson_found:
            await update.message.reply_text(f"😴 Сейчас уроки для {selected_class} не идут (перемена или учебный день завершен).")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот с поддержкой 5-B и 5-G успешно запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()