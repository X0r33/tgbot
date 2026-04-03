# main.py — точка входу бота

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from utils.logger import logger

# Підключаємо роутери
from handlers import start, upload, search, profile, admin


async def main():
    # Ініціалізуємо базу даних
    db.init_db()
    logger.info("✅ База даних ініціалізована")

    # Створюємо бот та диспетчер
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Реєструємо всі роутери
    # ВАЖЛИВО: порядок має значення — адмін до загальних
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(upload.router)
    dp.include_router(search.router)
    dp.include_router(profile.router)

    logger.info("🤖 Бот запускається...")

    try:
        # Видаляємо вебхук на випадок якщо був встановлений
        await bot.delete_webhook(drop_pending_updates=True)
        # Запускаємо polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("🛑 Бот зупинений")


if __name__ == "__main__":
    asyncio.run(main())
