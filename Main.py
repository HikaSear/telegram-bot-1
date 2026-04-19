import asyncio
import os
import random
import logging
import time
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.types import Message, ChatMemberUpdated, ChatPermissions
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
    "2 + 2 * 2 = ?": "6",
    "√144 = ?": "12",
    "25 * 4 = ?": "100",
    "1000 - 7 = ?": "Я умер прости",
    "7 * 7 + 1 = ?": "50",
    "Как зовут владельца чата?": "Маша"
}

# Структура: {chat_id: {"question": str, "answer": str, "messages": [id1, id2...]}}
active_examples = {}

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОЧИСТКИ ---
async def clear_old_messages(bot: Bot, chat_id: int):
    if chat_id in active_examples:
        for msg_id in active_examples[chat_id].get("messages", []):
            try:
                await bot.delete_message(chat_id, msg_id)
            except TelegramBadRequest:
                pass  # Сообщение уже удалено или слишком старое
        active_examples[chat_id]["messages"] = []


# --- ФУНКЦИЯ ОТПРАВКИ ПРИМЕРА ---
async def send_random_example(bot: Bot, chat_id: int):
    # Сначала удаляем старое, если есть
    await clear_old_messages(bot, chat_id)

    question, answer = random.choice(list(EXAMPLES.items()))

    sent_msg = await bot.send_message(
        chat_id,
        f"🎲 <b>Решите пример:</b>\n{question}"
    )

    active_examples[chat_id] = {
        "question": question,
        "answer": answer,
        "messages": [sent_msg.message_id]
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


@dp.message(Command("рулетка"))
async def cmd_roulette(message: Message, bot: Bot):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return await message.answer("Рулетка только для групп!")

    # Шанс 1 из 7
    if random.randint(1, 7) == 1:
        try:
            # Мут на 60 секунд
            until_date = int(time.time()) + 60
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            await message.reply("💥 БАХ! Тебе не повезло. Мут на 1 минуту.")
        except TelegramBadRequest:
            await message.reply("Упс! Кажется, у меня нет прав мутить пользователей (или ты админ).")
    else:
        await message.reply("🎉 Щелчок... Тебе повезло, патрон не выстрелил!")


@dp.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(ChatMemberStatus.LEFT, ChatMemberStatus.MEMBER)
    )
)
async def on_bot_added_to_group(event: ChatMemberUpdated, bot: Bot):
    await send_random_example(bot, event.chat.id)


@dp.message()
async def check_answer(message: Message, bot: Bot):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP] or not message.text:
        return

    chat_id = message.chat.id

    # Если есть активный пример в этом чате
    if chat_id in active_examples:
        # Добавляем ID сообщения пользователя в список на удаление
        active_examples[chat_id]["messages"].append(message.message_id)

        # Проверяем, является ли это ответом на сообщение бота
        if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
            data = active_examples[chat_id]
            user_answer = message.text.strip().lower()
            correct_answer = data["answer"].lower()

            if user_answer == correct_answer:
                await message.reply(f"✅ <b>Верно, {message.from_user.first_name}!</b>")
                # Очистим всё через 3 секунды, чтобы люди успели увидеть ответ
                await asyncio.sleep(3)
                await clear_old_messages(bot, chat_id)
                del active_examples[chat_id]

                # Запускаем таймер до следующего примера
                asyncio.create_task(delayed_example(bot, chat_id, 1800))


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
