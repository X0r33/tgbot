# handlers/start.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import main_menu_kb, subscribe_kb, language_kb, remove_kb
from utils.subscription import check_subscription
from utils.antispam import check_spam, get_remaining_cooldown
from utils.logger import logger
from i18n import t, get_lang
from config import CHANNEL_ID, LANGUAGES

router = Router()


class LangFSM(StatesGroup):
    choosing = State()


def get_user_lang(telegram_id: int) -> str:
    user = db.get_user_by_telegram_id(telegram_id)
    return get_lang(user)


async def subscription_gate(message: Message, bot: Bot) -> bool:
    user = db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    lang = get_lang(user)

    if user.get("is_banned"):
        await message.answer(t("banned", lang))
        return False

    subscribed = await check_subscription(bot, message.from_user.id)
    if not subscribed:
        await message.answer(
            t("subscribe_required", lang),
            reply_markup=subscribe_kb(f"https://t.me/{CHANNEL_ID.lstrip('@')}", lang),
            parse_mode="HTML"
        )
        return False
    return True


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
    tg_id = message.from_user.id
    user  = db.get_or_create_user(
        telegram_id=tg_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    logger.info(f"[/start] user={tg_id}")

    if user.get("is_banned"):
        await message.answer(t("banned", get_lang(user)))
        return

    # Якщо мова ще не вибрана — показуємо вибір
    # БАГ БУВ: t("choose_language", "uk") — "uk" немає в i18n, fallback до DEFAULT_LANG
    if db.is_new_user(tg_id):
        await state.set_state(LangFSM.choosing)
        await message.answer(
            t("choose_language"),   # використовуємо DEFAULT_LANG (en)
            reply_markup=language_kb()
        )
        return

    lang = get_lang(user)
    subscribed = await check_subscription(bot, tg_id)
    if not subscribed:
        await message.answer(
            t("subscribe_required", lang),
            reply_markup=subscribe_kb(f"https://t.me/{CHANNEL_ID.lstrip('@')}", lang),
            parse_mode="HTML"
        )
        return

    name = message.from_user.first_name or "User"
    await message.answer(t("welcome", lang, name=name), reply_markup=main_menu_kb(lang), parse_mode="HTML")


# ── Вибір мови ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("setlang:"))
async def cb_set_language(callback: CallbackQuery, state: FSMContext, bot: Bot):
    lang_code = callback.data.split(":", 1)[1]
    if lang_code not in LANGUAGES:
        await callback.answer("Invalid language", show_alert=True)
        return

    tg_id = callback.from_user.id
    db.get_or_create_user(
        telegram_id=tg_id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name
    )
    db.set_user_language(tg_id, lang_code)
    await state.clear()
    logger.info(f"[lang] user={tg_id} lang={lang_code}")

    await callback.message.edit_text(t("language_set", lang_code), parse_mode="HTML")

    subscribed = await check_subscription(bot, tg_id)
    if not subscribed:
        await callback.message.answer(
            t("subscribe_required", lang_code),
            reply_markup=subscribe_kb(f"https://t.me/{CHANNEL_ID.lstrip('@')}", lang_code),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    name = callback.from_user.first_name or "User"
    await callback.message.answer(
        t("welcome", lang_code, name=name),
        reply_markup=main_menu_kb(lang_code),
        parse_mode="HTML"
    )
    await callback.answer()


# ── Зміна мови з меню (один хендлер для всіх мов)
# БАГ БУВ: два хендлери на однаковий фільтр — другий ніколи не викликався
@router.message(F.text.in_({"🌐 Language", "🌐 Язык"}))
async def cmd_language_menu(message: Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(t("choose_language", lang), reply_markup=language_kb(), parse_mode="HTML")


# ── Підтвердження підписки ────────────────────────────────────────────────────

@router.callback_query(F.data == "check_subscription")
async def cb_check_subscription(callback: CallbackQuery, bot: Bot):
    tg_id = callback.from_user.id
    lang  = get_user_lang(tg_id)

    subscribed = await check_subscription(bot, tg_id)
    if not subscribed:
        await callback.answer(t("not_subscribed", lang), show_alert=True)
        return

    db.get_or_create_user(
        telegram_id=tg_id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name
    )
    await callback.message.edit_text(t("sub_confirmed", lang), parse_mode="HTML")
    name = callback.from_user.first_name or "User"
    await callback.message.answer(
        t("welcome", lang, name=name),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML"
    )
    await callback.answer()


# ── /menu ─────────────────────────────────────────────────────────────────────

@router.message(Command("menu"))
async def cmd_menu(message: Message, bot: Bot):
    if not await subscription_gate(message, bot):
        return
    lang = get_user_lang(message.from_user.id)
    await message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))


# ── /help ─────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message):
    lang = get_user_lang(message.from_user.id)
    await message.answer(t("help_text", lang), parse_mode="HTML")


# ── /stats ────────────────────────────────────────────────────────────────────

@router.message(Command("stats"))
@router.message(F.text.in_({"📊 Statistics", "📊 Статистика"}))
async def cmd_stats(message: Message, bot: Bot):
    if not await subscription_gate(message, bot):
        return
    if check_spam(message.from_user.id):
        lang = get_user_lang(message.from_user.id)
        return await message.answer(t("antispam", lang, sec=int(get_remaining_cooldown(message.from_user.id))))

    lang  = get_user_lang(message.from_user.id)
    stats = db.get_global_stats()
    await message.answer(
        t("stats_title", lang,
          users=stats["users"], files=stats["files"],
          downloads=stats["downloads"], banned=stats["banned"]),
        parse_mode="HTML"
    )
    db.log_action(message.from_user.id, "stats_view")


# ── /promo ────────────────────────────────────────────────────────────────────

@router.message(Command("promo"))
async def cmd_use_promo(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer("❌ Usage: /promo CODE")

    code = parts[1].strip().upper()
    user = db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    lang = get_user_lang(message.from_user.id)

    if user.get("is_banned"):
        return await message.answer(t("banned", lang))

    success, msg = db.use_promocode(code, user["id"])
    db.log_action(user["id"], "promo_activate" if success else "promo_fail", code)
    await message.answer(msg, parse_mode="HTML",
                         reply_markup=main_menu_kb(lang) if success else None)
