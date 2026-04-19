import asyncio
import os
import random
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.types import Message
from aiogram.enums import ChatType, ParseMode, ChatMemberStatus
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

TOKEN = os.getenv("BOT_TOKEN")

EXAMPLES = {
    "15 + 27 = ?": "42",
    "12 * 4 = ?": "48",
    "81 / 9 = ?": "9",
    "150 - 65 = ?": "85",
    "744 * 2": "1488",
    "12 ^ 2 = ?": "144",
    "По чему плавает утка?": "По воде",
    "2 + 2 * 2 = ?": "6",
    "√144 = ?": "12",
    "25 * 4 = ?": "100",
    "1000 - 7 = ?": "Я умер прости",
    "7 * 7 + 1 = ?": "50",
    "Как зовут владельца чата?": "Маша"
}

active_examples = {}

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()

# --- ФУНКЦИЯ УДАЛЕНИЯ ЧЕРЕЗ ВРЕМЯ ---
async def delete_after_delay(message: Message, delay: int = 180):
    """Удаляет сообщение через указанное количество секунд (по умолчанию 3 минуты)"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except TelegramBadRequest:
        # Сообщение уже удалено или у бота нет прав
        pass
    except Exception as e:
        logging.error(f"Ошибка при удалении: {e}")

# --- ФУНКЦИЯ ОТПРАВКИ ПРИМЕРА ---
async def send_random_example(bot: Bot, chat_id: int):
    question, answer = random.choice(list(EXAMPLES.items()))

    sent_msg = await bot.send_message(
        chat_id,
        f"🎲 <b>Дайте ответ на вопрос:</b>\n{question}"
    )
    
    # Автоудаление самого вопроса через 3 минуты
    asyncio.create_task(delete_after_delay(sent_msg))

    active_examples[chat_id] = {
        "question": question,
        "answer": answer
    }

async def delayed_example(bot: Bot, chat_id: int, delay: int):
    await asyncio.sleep(delay)
    await send_random_example(bot, chat_id)

# --- КОМАНДЫ ---
@dp.message(Command("example"))
async def cmd_example(message: Message, bot: Bot):
    # Удаляем саму команду /example
    asyncio.create_task(delete_after_delay(message))
    
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await send_random_example(bot, message.chat.id)
    else:
        await message.answer("Эта команда работает только в группах.")

@dp.message(Command("roulette"))
async def cmd_roulette(message: Message):
    # Удаляем команду /roulette
    asyncio.create_task(delete_after_delay(message))
    
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return await message.answer("Рулетка только для групп!")

    text = ""
    if random.randint(0, 100) % 2 == 0:
        if random.randint(0, 100) % 2 == 0:
            text = f"💥 БАХ! Тебе не повезло втройне\n(шанс выпадения этого сообщения очень мал). {message.from_user.first_name} лох."
        else:
            text = "💥 БАХ! Тебе не повезло."
    else:
        text = "🎉 Щелчок... Тебе повезло, патрон не выстрелил!"
    
    sent_msg = await message.reply(text)
    # Удаляем ответ рулетки
    asyncio.create_task(delete_after_delay(sent_msg))

@dp.message()
async def check_answer(message: Message, bot: Bot):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP] or not message.text:
        return

    chat_id = message.chat.id

    if chat_id in active_examples:
        # Проверяем, что это ответ на сообщение бота
        if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
            data = active_examples[chat_id]
            user_answer = message.text.strip().lower()
            correct_answer = data["answer"].lower()

            if user_answer == correct_answer:
                sent_msg = await message.reply(f"✅ <b>Верно, {message.from_user.first_name}!</b>")
                del active_examples[chat_id]

                # Удаляем сообщение пользователя с ответом и поздравление бота
                asyncio.create_task(delete_after_delay(message))
                asyncio.create_task(delete_after_delay(sent_msg))

                # Планируем следующий пример через 10 минут (600 сек)
                asyncio.create_task(delayed_example(bot, chat_id, 600))

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
