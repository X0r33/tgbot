# handlers/upload.py — завантаження файлу з динамічними категоріями/підкатегоріями

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import (
    cancel_kb, skip_kb, main_menu_kb, remove_kb,
    upload_category_kb, upload_subcategory_kb
)
from utils.antispam import check_spam, get_remaining_cooldown
from utils.logger import logger
from config import MAX_FILE_SIZE, FILE_TYPE_MAP
from handlers.start import subscription_gate, get_user_lang
from i18n import t

router = Router()


class UploadFSM(StatesGroup):
    waiting_file        = State()
    waiting_name        = State()
    waiting_description = State()
    waiting_tags        = State()
    waiting_category    = State()   # inline: вибір або ввід нової
    waiting_new_cat     = State()   # ввід назви нової категорії
    waiting_subcategory = State()   # inline: вибір або ввід нової
    waiting_new_sub     = State()   # ввід назви нової підкатегорії
    waiting_photo       = State()


def _ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else "other"


# ── /upload ───────────────────────────────────────────────────────────────────
@router.message(Command("upload"))
@router.message(F.text.in_({"📁 Завантажити", "📁 Upload", "📁 Загрузить"}))
async def start_upload(message: Message, state: FSMContext, bot: Bot):
    if not await subscription_gate(message, bot):
        return

    # Тільки адмін може завантажувати файли
    from config import ADMIN_IDS
    user = db.get_user_by_telegram_id(message.from_user.id)
    is_admin = message.from_user.id in ADMIN_IDS or bool(user and user.get("is_admin"))
    if not is_admin:
        lang = get_user_lang(message.from_user.id)
        no_access = {"en": "🚫 Only admins can upload files.",
                     "ru": "🚫 Загружать файлы могут только администраторы."}
        await message.answer(no_access.get(lang, no_access["en"]))
        return

    if check_spam(message.from_user.id):
        lang = get_user_lang(message.from_user.id)
        await message.answer(t("antispam", lang, sec=int(get_remaining_cooldown(message.from_user.id))))
        return

    lang = get_user_lang(message.from_user.id)
    await state.set_state(UploadFSM.waiting_file)
    await state.update_data(lang=lang)
    await message.answer(t("upload_start", lang), reply_markup=cancel_kb(lang), parse_mode="HTML")


# ── Файл ─────────────────────────────────────────────────────────────────────
@router.message(UploadFSM.waiting_file, F.document)
async def got_file(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    doc  = message.document

    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await message.answer(t("upload_too_big", lang, size=f"{doc.file_size/1024/1024:.1f}"))
        return

    file_type = FILE_TYPE_MAP.get(_ext(doc.file_name or ""), "other")
    await state.update_data(
        tg_file_id=doc.file_id,
        file_name=doc.file_name or "file",
        file_type=file_type,
        file_size=doc.file_size or 0
    )
    await state.set_state(UploadFSM.waiting_name)
    await message.answer(t("upload_got_file", lang, name=doc.file_name),
                         reply_markup=skip_kb(lang), parse_mode="HTML")


@router.message(UploadFSM.waiting_file)
async def file_not_sent(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))
        return
    await message.answer(t("upload_not_file", lang))


# ── Назва ─────────────────────────────────────────────────────────────────────
@router.message(UploadFSM.waiting_name)
async def got_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))

    name = data["file_name"] if message.text == t("btn_skip", lang) else message.text.strip()[:128]
    await state.update_data(name=name)
    await state.set_state(UploadFSM.waiting_description)
    await message.answer(t("upload_ask_desc", lang), reply_markup=cancel_kb(lang))


# ── Опис ──────────────────────────────────────────────────────────────────────
@router.message(UploadFSM.waiting_description)
async def got_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))

    await state.update_data(description=message.text.strip()[:500])
    await state.set_state(UploadFSM.waiting_tags)
    await message.answer(t("upload_ask_tags", lang), reply_markup=skip_kb(lang), parse_mode="HTML")


# ── Теги ──────────────────────────────────────────────────────────────────────
@router.message(UploadFSM.waiting_tags)
async def got_tags(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))

    tags = "" if message.text == t("btn_skip", lang) else \
        " ".join(x.lower() for x in message.text.replace(",", " ").split() if x)[:200]

    await state.update_data(tags=tags)
    await _ask_category(message, state, lang)


async def _ask_category(message: Message, state: FSMContext, lang: str):
    cats = db.get_all_categories()
    await state.set_state(UploadFSM.waiting_category)
    if not cats:
        await message.answer(
            "⚠️ Категорій ще немає. Введіть назву нової категорії:",
            reply_markup=cancel_kb(lang)
        )
        await state.set_state(UploadFSM.waiting_new_cat)
        return
    await message.answer(
        t("upload_ask_category", lang),
        reply_markup=remove_kb(),
        parse_mode="HTML"
    )
    await message.answer("👇", reply_markup=upload_category_kb(cats, lang))


# ── Вибір категорії (callback) ────────────────────────────────────────────────
@router.callback_query(UploadFSM.waiting_category, F.data.startswith("upl_cat:"))
async def cb_upload_cat(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    val  = callback.data.split(":", 1)[1]

    if val == "new":
        await state.set_state(UploadFSM.waiting_new_cat)
        await callback.message.answer("✏️ Введіть назву нової категорії:", reply_markup=cancel_kb(lang))
        await callback.answer()
        return

    cat_id = int(val)
    cat    = db.get_category_by_id(cat_id)
    await state.update_data(category_id=cat_id, category_name=cat["name"] if cat else "?")
    await callback.answer()
    await _ask_subcategory(callback.message, state, cat_id, lang)


# ── Нова категорія (текст) ────────────────────────────────────────────────────
@router.message(UploadFSM.waiting_new_cat)
async def got_new_cat(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))

    user   = db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    cat_id = db.create_category(message.text.strip(), user["id"])
    cat    = db.get_category_by_id(cat_id)
    await state.update_data(category_id=cat_id, category_name=cat["name"] if cat else message.text.strip())
    await message.answer(f"✅ Категорію <b>{message.text.strip()}</b> створено!", parse_mode="HTML")
    await _ask_subcategory(message, state, cat_id, lang)


async def _ask_subcategory(message: Message, state: FSMContext, cat_id: int, lang: str):
    subs = db.get_subcategories(cat_id)
    await state.set_state(UploadFSM.waiting_subcategory)
    await state.update_data(pending_cat_id=cat_id)
    await message.answer(
        t("upload_ask_subcategory", lang, category=""),
        reply_markup=remove_kb(),
        parse_mode="HTML"
    )
    await message.answer("👇", reply_markup=upload_subcategory_kb(subs, cat_id, lang))


# ── Вибір підкатегорії (callback) ─────────────────────────────────────────────
@router.callback_query(UploadFSM.waiting_subcategory, F.data.startswith("upl_sub:"))
async def cb_upload_sub(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    raw  = callback.data[len("upl_sub:"):]   # "skip" | "123" | "new:42"

    if raw == "skip":
        await state.update_data(subcategory_id=0, subcategory_name="")
        await callback.answer()
        await _ask_photo(callback.message, state, lang)
        return

    if raw.startswith("new:"):
        cat_id = int(raw.split(":", 1)[1])
        await state.update_data(pending_cat_id=cat_id)
        await state.set_state(UploadFSM.waiting_new_sub)
        await callback.message.answer("✏️ Введіть назву нової підкатегорії:", reply_markup=cancel_kb(lang))
        await callback.answer()
        return

    sub_id = int(raw)
    sub    = db.get_subcategory_by_id(sub_id)
    await state.update_data(subcategory_id=sub_id, subcategory_name=sub["name"] if sub else "?")
    await callback.answer()
    await _ask_photo(callback.message, state, lang)


# ── Нова підкатегорія (текст) ─────────────────────────────────────────────────
@router.message(UploadFSM.waiting_new_sub)
async def got_new_sub(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))

    user   = db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    cat_id = data.get("pending_cat_id") or data.get("category_id", 0)
    sub_id = db.create_subcategory(cat_id, message.text.strip(), user["id"])
    sub    = db.get_subcategory_by_id(sub_id)
    await state.update_data(subcategory_id=sub_id, subcategory_name=sub["name"] if sub else message.text.strip())
    await message.answer(f"✅ Підкатегорію <b>{message.text.strip()}</b> створено!", parse_mode="HTML")
    await _ask_photo(message, state, lang)


async def _ask_photo(message: Message, state: FSMContext, lang: str):
    await state.set_state(UploadFSM.waiting_photo)
    await message.answer(t("upload_ask_photo", lang), reply_markup=skip_kb(lang))


# ── Фото ──────────────────────────────────────────────────────────────────────
@router.message(UploadFSM.waiting_photo)
async def got_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uk")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))

    photo_id = message.photo[-1].file_id if message.photo else None
    user     = db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    fid = db.add_file(
        file_id          = data["tg_file_id"],
        name             = data["name"],
        description      = data.get("description", ""),
        file_type        = data["file_type"],
        category_id      = data.get("category_id") or 0,
        subcategory_id   = data.get("subcategory_id") or 0,
        size             = data.get("file_size", 0),
        tags             = data.get("tags", ""),
        author_id        = user["id"],
        preview_photo_id = photo_id,
    )

    db.log_action(user["id"], "upload", f"file_id={fid} name={data['name']}")
    logger.info(f"[upload] user={message.from_user.id} file={fid}")

    await state.clear()
    await message.answer(
        t("upload_done", lang,
          name     = data["name"],
          category = data.get("category_name") or "—",
          subcategory = data.get("subcategory_name") or "—",
          id       = fid),
        reply_markup=main_menu_kb(lang),
        parse_mode="HTML"
    )
