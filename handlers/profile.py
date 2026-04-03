# handlers/profile.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import main_menu_kb, file_list_kb, cancel_kb, collection_kb, skip_kb
from utils.antispam import check_spam, get_remaining_cooldown
from handlers.start import subscription_gate, get_user_lang
from i18n import t
from config import LANGUAGES as LANG_MAP

router = Router()


class CollectionFSM(StatesGroup):
    waiting_name = State()
    waiting_desc = State()


# ── Профіль ───────────────────────────────────────────────────────────────────

@router.message(Command("myfiles"))
@router.message(F.text.in_({"👤 My Profile", "👤 Мой профиль"}))
async def cmd_profile(message: Message, bot: Bot):
    if not await subscription_gate(message, bot):
        return
    lang = get_user_lang(message.from_user.id)
    if check_spam(message.from_user.id):
        return await message.answer(
            t("antispam", lang, sec=int(get_remaining_cooldown(message.from_user.id)))
        )

    user     = db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    files    = db.get_user_files(user["id"])
    total_dl = sum(f.get("downloads", 0) for f in files)
    cols     = db.get_user_collections(user["id"])
    lang_lbl = LANG_MAP.get(lang, lang)

    await message.answer(
        t("profile_title", lang,
          name        = user.get("first_name") or "—",
          username    = f"@{user['username']}" if user.get("username") else "—",
          tg_id       = message.from_user.id,
          files       = len(files),
          downloads   = total_dl,
          collections = len(cols),
          joined      = (user.get("join_date") or "")[:10],
          interface_lang = lang_lbl),
        parse_mode="HTML"
    )

    if files:
        await message.answer(
            t("my_files_title", lang, count=len(files)),
            reply_markup=file_list_kb(files)
        )
    db.log_action(user["id"], "profile_view")


# ── Збірки ────────────────────────────────────────────────────────────────────

@router.message(F.text.in_({"🗂 My Collections", "🗂 Мои сборки"}))
async def cmd_collections(message: Message, bot: Bot):
    if not await subscription_gate(message, bot):
        return
    lang = get_user_lang(message.from_user.id)
    user = db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    cols = db.get_user_collections(user["id"])
    await message.answer(
        t("collections_title", lang, count=len(cols)),
        parse_mode="HTML",
        reply_markup=collection_kb(cols, lang)
    )


@router.callback_query(F.data == "col:new")
async def cb_new_col(callback: CallbackQuery, state: FSMContext):
    lang = get_user_lang(callback.from_user.id)
    await state.set_state(CollectionFSM.waiting_name)
    await state.update_data(lang=lang)
    await callback.message.answer(t("collection_ask_name", lang), reply_markup=cancel_kb(lang))
    await callback.answer()


@router.message(CollectionFSM.waiting_name)
async def got_col_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))
    await state.update_data(col_name=message.text.strip()[:64])
    await state.set_state(CollectionFSM.waiting_desc)
    await message.answer(t("collection_ask_desc", lang), reply_markup=skip_kb(lang))


@router.message(CollectionFSM.waiting_desc)
async def got_col_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))
    desc = "" if message.text == t("btn_skip", lang) else message.text.strip()[:256]
    user = db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    cid  = db.create_collection(data["col_name"], desc, user["id"])
    await state.clear()
    await message.answer(
        t("collection_created", lang, name=data["col_name"], id=cid),
        parse_mode="HTML",
        reply_markup=main_menu_kb(lang)
    )


@router.callback_query(F.data.startswith("col:"))
async def cb_view_col(callback: CallbackQuery):
    val = callback.data.split(":", 1)[1]
    if val == "new":
        return
    lang  = get_user_lang(callback.from_user.id)
    files = db.get_collection_files(int(val))
    if not files:
        return await callback.answer(t("collection_empty", lang), show_alert=True)
    await callback.message.answer(
        t("collection_files_title", lang, count=len(files)),
        reply_markup=file_list_kb(files)
    )
    await callback.answer()


@router.message(F.text.regexp(r"^/addtocol (\d+) (\d+)$"))
async def cmd_add_to_col(message: Message):
    lang   = get_user_lang(message.from_user.id)
    parts  = message.text.split()
    col_id = int(parts[1])
    fil_id = int(parts[2])
    user   = db.get_user_by_telegram_id(message.from_user.id)
    if not user:
        return await message.answer("/start")
    if col_id not in [c["id"] for c in db.get_user_collections(user["id"])]:
        return await message.answer(t("collection_not_found", lang))
    f = db.get_file_by_id(fil_id)
    if not f:
        return await message.answer(t("file_not_found", lang))
    db.add_file_to_collection(col_id, fil_id)
    await message.answer(t("collection_added", lang, name=f["name"]), parse_mode="HTML")
