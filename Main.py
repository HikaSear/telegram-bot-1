import asyncio
import os
import random
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.types import Message, ChatMemberUpdated
from aiogram.enums import ChatType, ParseMode, ChatMemberStatus
from aiogram.client.default import DefaultBotProperties
# --- НАСТРОЙКИ ---
TOKEN = os.getenv("BOT_TOKEN")

# --- МАТЕМАТИЧЕСКИЕ ПРИМЕРЫ ---
EXAMPLES = {
    "15 + 27 = ?": "42",
    "12 * 4 = ?": "48",
    "81 / 9 = ?": "9",
    "150 - 65 = ?": "85",
    "744 * 2": "1488",
    "12 ^ 2 = ?": "144",
    "2 + 2 * 2 = ?": "6",
    "√144 = ?": "12",
    "25 * 4 = ?": "100",
    "1000 - 7 = ?": "Я умер прости",
    "7 * 7 + 1 = ?": "50",
    "Как зовут владельца чата?": "Маша"
}

active_examples = {}

logging.basicConfig(level=logging.INFO)


# --- ФУНКЦИЯ ОТПРАВКИ ПРИМЕРА ---
async def send_random_example(bot: Bot, chat_id: int):
    question, answer = random.choice(list(EXAMPLES.items()))
    active_examples[chat_id] = {"question": question, "answer": answer}

    await bot.send_message(
        chat_id,
        f"🎲 <b>Решите пример:</b>\n\n<code>{question}</code>\n\n<i>Напишите ответ в ответ на это сообщение!</i>"
    )


# --- ФОНОВАЯ ЗАДАЧА ДЛЯ ЗАДЕРЖКИ ---
async def delayed_example(bot: Bot, chat_id: int, delay: int):
    await asyncio.sleep(delay)
    await send_random_example(bot, chat_id)


# --- ИНИЦИАЛИЗАЦИЯ ДИСПЕТЧЕРА ---
dp = Dispatcher()


@dp.message(Command("example"))
async def cmd_example(message: Message, bot: Bot):
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await send_random_example(bot, message.chat.id)
    else:
        await message.answer("Эта команда работает только в группах.")


@dp.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(ChatMemberStatus.LEFT, ChatMemberStatus.MEMBER)
    )
)
async def on_bot_added_to_group(event: ChatMemberUpdated, bot: Bot):
    await send_random_example(bot, event.chat.id)
    logging.info(f"Бот добавлен в чат {event.chat.id}, отправлен пример.")


@dp.message()
async def check_answer(message: Message, bot: Bot):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP] or not message.text:
        return

    if not message.reply_to_message or message.reply_to_message.from_user.id != bot.id:
        return

    chat_id = message.chat.id

    if chat_id in active_examples:
        data = active_examples[chat_id]
        user_answer = message.text.strip().lower()
        correct_answer = data["answer"].lower()

        if user_answer == correct_answer:
            await message.reply(
                f"✅ <b>Верно, {message.from_user.first_name}!</b>\n"
                f"Следующий пример появится через 30 минут.\n\n"
                f"<i>Используйте /example, чтобы не ждать.</i>"
            )
            del active_examples[chat_id]
            asyncio.create_task(delayed_example(bot, chat_id, 1800))


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass