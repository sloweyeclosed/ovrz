import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.markdown import link
import sys
import asyncio

# Настройки
API_TOKEN = "7581495047:AAHk28H3K5nXSpHuLNaFHB3F23I0KDhaZTA"
ADMIN_ID = 6674826114  # Ваш цифровой ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Хранилище данных
ticket_counter = 0
tickets = {}  # {ticket_id: {"user_id": int, "text": str, "answered": bool}}

# Меню для пользователя
user_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📨")]
    ],
    resize_keyboard=True
)

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def get_user_link(user: types.User) -> str:
    """Генерирует ссылку на пользователя"""
    name = user.full_name.replace(">", "").replace("<", "")
    if user.username:
        return f"<a href='https://t.me/{user.username}'>{name}</a>"
    return f"<a href='tg://user?id={user.id}'>{name}</a>"


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Режим администратора. Команды:\n"
                             "/ot [ID] [ответ] - ответить\n"
                             "/ql - список вопросов")
    else:
        await message.answer("press 📨",
                             reply_markup=user_menu)


@dp.message(F.text == "📨")
async def ask_question(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        return

    await message.answer("wrt:",
                         reply_markup=ReplyKeyboardRemove())


@dp.message(F.text & ~F.text.startswith('/'))
async def handle_question(message: types.Message):
    global ticket_counter

    if message.from_user.id == ADMIN_ID:
        return

    # Создаем новый тикет
    ticket_counter += 1
    tickets[ticket_counter] = {
        "user_id": message.from_user.id,
        "text": message.text,
        "answered": False
    }

    # Формируем ссылку на пользователя
    user_link = get_user_link(message.from_user)

    # Уведомляем админа
    await bot.send_message(
        ADMIN_ID,
        f"🆔 Новый вопрос #{ticket_counter}\n"
        f"От: {user_link} (ID: {message.from_user.id})\n"
        f"─────────────────\n"
        f"{message.text}\n"
        f"─────────────────\n"
        f"Ответить: /ot {ticket_counter} [текст ответа]",
        parse_mode="HTML"
    )

    await message.answer(f"✅",
                         reply_markup=user_menu)


@dp.message(Command("ql"))
async def list_tickets(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not tickets:
        await message.answer("📭 Нет активных вопросов")
        return

    response = "📋 Все вопросы:\n\n"
    for ticket_id, ticket in tickets.items():
        status = "✅" if ticket["answered"] else "🔄"
        response += f"{status} #{ticket_id}: {ticket['text'][:50]}...\n"

    await message.answer(response)


@dp.message(Command("ot"))
async def admin_reply(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("❌ Формат: /ot [ID] [ответ]\nПример: /ot 5 Проблема решена")
            return

        ticket_id = int(parts[1])
        answer = parts[2]

        if ticket_id not in tickets:
            await message.answer(f"❌ Вопроса #{ticket_id} не существует")
            return

        ticket = tickets[ticket_id]

        # Формируем ответ пользователю с его исходным вопросом
        await bot.send_message(
            ticket["user_id"],
            f"you: {ticket['text']}\n"
            f"─────────────────\n"
            f"me: {answer}\n",
            reply_markup=user_menu
        )

        tickets[ticket_id]["answered"] = True
        await message.answer(f"✅ Ответ на вопрос #{ticket_id} отправлен")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


async def main():
    while True:
        try:
            await bot.delete_webhook()
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    logging.info("=== Бот запущен ===")
    asyncio.run(main())