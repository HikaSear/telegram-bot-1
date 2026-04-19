import asyncio
import os
import random
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.types import Message, ChatMemberUpdated
from aiogram.enums import ChatType, ParseMode, ChatMemberStatus
from aiogram.client.default import DefaultBotProperties

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


# --- ФУНКЦИЯ ОТПРАВКИ ПРИМЕРА ---
async def send_random_example(bot: Bot, chat_id: int):
    question, answer = random.choice(list(EXAMPLES.items()))

    await bot.send_message(
        chat_id,
        f"🎲 <b>Дайте ответ на вопрос:</b>\n{question}"
    )

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
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await send_random_example(bot, message.chat.id)
    else:
        await message.answer("Эта команда работает только в группах.")


@dp.message(Command("roulette"))
async def cmd_roulette(message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return await message.answer("Рулетка только для групп!")

    if random.randint(1, 2) == 1:
        if random.randint(0, 100) == 0:
            await message.reply(f"💥 БАХ! Тебе не повезло втройне\n(шанс выпадения этого сообщения 0.5%). {message.from_user.first_name} лох")
        else:
            await message.reply("💥 БАХ! Тебе не повезло.")
    else:
        await message.reply("🎉 Щелчок... Тебе повезло, патрон не выстрелил!")


@dp.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(ChatMemberStatus.LEFT, ChatMemberStatus.MEMBER)
    )
)

@dp.message()
async def check_answer(message: Message, bot: Bot):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP] or not message.text:
        return

    chat_id = message.chat.id

    if chat_id in active_examples:
        if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
            data = active_examples[chat_id]
            user_answer = message.text.strip().lower()
            correct_answer = data["answer"].lower()

            if user_answer == correct_answer:
                await message.reply(f"✅ <b>Верно, {message.from_user.first_name}!</b>")
                del active_examples[chat_id]

                asyncio.create_task(delayed_example(bot, chat_id, 600))


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
