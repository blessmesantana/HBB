import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import json
import os
import datetime
import pytz

API_TOKEN = "6866417541:AAGt08D0gZ7JdUypgFBuQU1D35SnwBKnhOI"
BIRTHDAYS_FILE = "birthdays.json"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить день рождения")],
        [KeyboardButton(text="Изменить дату")],
        [KeyboardButton(text="Удалить дату")],
        [KeyboardButton(text="Список дней рождения")],
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "👋 <b>Привет!</b>\n"
        "Я бот для поздравлений с днём рождения.\n"
        "\n<b>Выбери действие с помощью меню ниже:</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu)

@dp.message(lambda m: m.text == "Добавить день рождения")
async def menu_add(message: types.Message):
    await message.answer("Напиши дату в формате ДД.ММ, например: 01.06")
    dp.data = getattr(dp, 'data', {})
    dp.data[message.from_user.id] = 'add'

@dp.message(lambda m: m.text == "Изменить дату")
async def menu_edit(message: types.Message):
    await message.answer("Напиши новую дату в формате ДД.ММ, например: 01.06")
    dp.data = getattr(dp, 'data', {})
    dp.data[message.from_user.id] = 'edit'

@dp.message(lambda m: m.text == "Удалить дату")
async def menu_remove(message: types.Message):
    # Используем уже существующую функцию
    await cmd_remove(message)

@dp.message(lambda m: m.text == "Список дней рождения")
async def menu_list(message: types.Message):
    await cmd_list(message)

@dp.message(Command("see_all"))
async def cmd_see_all(message: types.Message):
    print("Вызвана команда /see_all")  # временно для отладки
    # Только для администратора
    if message.from_user.username != "bless_santana":
        await message.answer("<i>Команда доступна только администратору.</i>", parse_mode="HTML")
        return
    chat_id = -1001698289619
    if not os.path.exists(BIRTHDAYS_FILE):
        await message.answer("<i>Список дней рождения пуст.</i>", parse_mode="HTML")
        return
    with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Будет отправлено сообщений: {len(data)}")  # временно для отладки
    for key, info in data.items():
        name = info.get("name", "Друг")
        test_text = f"<b>{name}</b>, я знаю, что ты здесь! (тестовое сообщение)"
        print(f"Отправка: {test_text}")  # временно для отладки
        await bot.send_message(chat_id, test_text, parse_mode="HTML")
    await message.answer("<b>Тестовые сообщения отправлены для всех участников.</b>", parse_mode="HTML")

@dp.message()
async def handle_text(message: types.Message):
    dp.data = getattr(dp, 'data', {})
    action = dp.data.get(message.from_user.id)
    if action == 'add':
        message.text = f"/add {message.text.strip()}"
        await cmd_add(message)
        dp.data[message.from_user.id] = None
    elif action == 'edit':
        message.text = f"/edit {message.text.strip()}"
        await cmd_edit(message)
        dp.data[message.from_user.id] = None

def save_birthday(user_id, date):
    if os.path.exists(BIRTHDAYS_FILE):
        with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data[str(user_id)] = date
    with open(BIRTHDAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

@dp.message(Command("add"))
async def cmd_add(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("<b>Пожалуйста, укажи дату в формате</b>\n<code>/add ДД.ММ</code>\nНапример: <code>/add 01.06</code>", parse_mode="HTML")
        return
    date = parts[1]
    # Простая проверка формата
    if len(date) != 5 or date[2] != "." or not date.replace(".", "").isdigit():
        await message.answer("<b>Неверный формат даты.</b>\nИспользуй <code>ДД.ММ</code>, например: <code>01.06</code>", parse_mode="HTML")
        return
    save_birthday(message.from_user.id, date)
    await message.answer(f"<b>Твой день рождения {date} сохранён!</b>", parse_mode="HTML")

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    if not os.path.exists(BIRTHDAYS_FILE):
        await message.answer("<i>Список дней рождения пуст.</i>", parse_mode="HTML")
        return
    with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        await message.answer("<i>Список дней рождения пуст.</i>", parse_mode="HTML")
        return
    text = "<b>🎂 Список дней рождения:</b>"
    for user_id, date in data.items():
        name = "<b>(Вы)</b>" if str(user_id) == str(message.from_user.id) else ""
        # Получаем имя пользователя, если это не вы
        if not name:
            try:
                user = await bot.get_chat(user_id)
                name = f"<b>{user.first_name}</b>"
            except Exception:
                name = f"Пользователь {user_id}"
        text += f"\n{name}: <code>{date}</code>"
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("remove"))
async def cmd_remove(message: types.Message):
    if not os.path.exists(BIRTHDAYS_FILE):
        await message.answer("<i>У вас не сохранён день рождения.</i>", parse_mode="HTML")
        return
    with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if str(message.from_user.id) in data:
        del data[str(message.from_user.id)]
        with open(BIRTHDAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        await message.answer("<b>Ваш день рождения удалён.</b>", parse_mode="HTML")
    else:
        await message.answer("<i>У вас не сохранён день рождения.</i>", parse_mode="HTML")

@dp.message(Command("edit"))
async def cmd_edit(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("<b>Пожалуйста, укажи новую дату в формате</b>\n<code>/edit ДД.ММ</code>", parse_mode="HTML")
        return
    date = parts[1]
    if len(date) != 5 or date[2] != "." or not date.replace(".", "").isdigit():
        await message.answer("<b>Неверный формат даты.</b>\nИспользуй <code>ДД.ММ</code>, например: <code>01.06</code>", parse_mode="HTML")
        return
    if not os.path.exists(BIRTHDAYS_FILE):
        await message.answer("<i>У вас не сохранён день рождения.</i>", parse_mode="HTML")
        return
    with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if str(message.from_user.id) in data:
        data[str(message.from_user.id)] = date
        with open(BIRTHDAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        await message.answer(f"<b>Ваша дата дня рождения изменена на {date}.</b>", parse_mode="HTML")
    else:
        await message.answer("<i>У вас не сохранён день рождения.</i>", parse_mode="HTML")

# Новый birthday_checker для работы с кастомной структурой
async def birthday_checker():
    chat_id = -1001698289619  # chat_id вашей группы
    wishes = {
        "Кальянный мастер": "Пусть угли всегда будут жаркими, а кальян — вкусным!",
        "Бассейндон": "Пусть твой бассейн будет всегда полон веселья и друзей!",
        "Ашкудишка": "Пусть каждый день будет таким же ярким, как ты!",
        "Винодел": "Пусть вино льётся рекой, а жизнь будет сладкой!",
        "Чупик": "Пусть в жизни будет столько же радости, сколько в твоих чупа-чупсах!",
        "Работяга": "Пусть работа приносит только удовольствие и большие успехи!",
        "Пивопоглотитель": "Пусть пиво всегда будет холодным, а компания — весёлой!",
        "Ляля": "Пусть каждый день будет наполнен нежностью и заботой! Гугу-гага!",
        "Стриптизерша": "Пусть танцы будут страстными, а аплодисменты — громкими!",
        "Черный русский": "Пусть коктейли будут крепкими, а вечера — незабываемыми!"
    }
    sent_today = set()
    while True:
        now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
        today = now.strftime("%d.%m")
        hour = now.hour
        minute = now.minute
        if hour == 17 and minute == 15 and today not in sent_today:
            if os.path.exists(BIRTHDAYS_FILE):
                with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, info in data.items():
                    if info.get("date") == today:
                        name = info.get("name", "Друг")
                        nickname = info.get("nickname", "")
                        gender = info.get("gender", "male")
                        wish = wishes.get(nickname, "Пусть сбудется всё задуманное!")
                        if gender == "female":
                            text = (
                                f"🥳 Сегодня свой День Рождения празднует дорогая 🎉 <b>{name}</b>, "
                                f"также известная как <b>{nickname}</b>! 🥂{wish} 🎁"
                            )
                        else:
                            text = (
                                f"🥳 Сегодня свой День Рождения празднует дорогой 🎉 <b>{name}</b>, "
                                f"также известный как <b>{nickname}</b>! 🥂{wish} 🎁"
                            )
                        await bot.send_message(chat_id, text, parse_mode="HTML")
            sent_today.add(today)
        elif hour != 17 or minute != 15:
            sent_today.discard(today)
        await asyncio.sleep(30)  # Проверять каждые 30 секунд

async def main():
    asyncio.create_task(birthday_checker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Тест: проверить поздравления для всех дат
    with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Тест поздравлений для всех:")
    for key, info in data.items():
        name = info.get("name", "Друг")
        nickname = info.get("nickname", "")
        gender = info.get("gender", "male")
        if gender == "female":
            text = f"Сегодня празднует свой День Рождения дорогая {name}, так же известная как {nickname}!"
        else:
            text = f"Сегодня празднует свой День Рождения дорогой {name}, так же известный как {nickname}!"
        print(text)
    asyncio.run(main())
