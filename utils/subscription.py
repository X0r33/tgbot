# utils/subscription.py — перевірка підписки на канал

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from config import CHANNEL_ID
from utils.logger import logger


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """
    Перевіряє чи підписаний користувач на канал.
    Повертає True якщо підписаний або якщо перевірку не вдалось зробити.
    """
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Статуси що означають участь у каналі
        return member.status in ("member", "administrator", "creator")
    except TelegramBadRequest as e:
        logger.warning(f"Не вдалось перевірити підписку для {user_id}: {e}")
        # Якщо бот не адмін каналу — пропускаємо перевірку
        return True
    except Exception as e:
        logger.error(f"Помилка перевірки підписки: {e}")
        return True
