# handlers/search.py

import hashlib
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import (
    main_menu_kb, categories_kb, subcategories_kb,
    file_view_kb, file_list_kb, cancel_kb
)
from utils.antispam import check_spam, get_remaining_cooldown
from utils.cache import cache_get, cache_set
from utils.logger import logger
from handlers.start import subscription_gate, get_user_lang
from i18n import t

router = Router()


class SearchFSM(StatesGroup):
    waiting_query = State()


def can_access_file(user, file: dict, is_admin: bool) -> bool:
    """
    Перевіряє доступ до файлу.
    БАГ БУВ: user міг бути None → KeyError на user["id"]
    """
    if is_admin:
        return True
    if not file.get("is_hidden"):
        return True
    # Прихований файл — перевіряємо доступ через промокод
    if user is None:
        return False
    return db.has_promo_access(user["id"], file["id"])


def format_file_card(f: dict, lang: str = "en") -> str:
    author_name = f.get("first_name") or f.get("username") or "—"
    author_tg   = f.get("author_telegram_id")
    author_str  = f"<a href='tg://user?id={author_tg}'>{author_name}</a>" if author_tg else author_name

    size = f.get("size", 0) or 0
    size_str = (
        f"{size/1024/1024:.1f} MB" if size >= 1024*1024 else
        f"{size/1024:.1f} KB"      if size >= 1024 else
        f"{size} B"                if size else ""
    )

    tags_raw = f.get("tags", "") or ""
    tags_str = " ".join(f"#{x}" for x in tags_raw.split() if x) or "—"
    hidden   = " 🙈" if f.get("is_hidden") else ""

    cat_name = f.get("cat_name") or "—"
    sub_name = f.get("sub_name") or ""
    cat_line = f"📂 {cat_name}" + (f"  ›  📁 {sub_name}" if sub_name else "")

    lbl = {
        "en": ("⬇️ Downloads:", "📅 Added:",      "📦 Size:", "👤 Author:", "🏷 Tags:"),
        "ru": ("⬇️ Загрузок:", "📅 Добавлено:", "📦 Размер:", "👤 Автор:", "🏷 Теги:"),
    }.get(lang, ("⬇️ Downloads:", "📅 Added:", "📦 Size:", "👤 Author:", "🏷 Tags:"))

    return (
        f"📄 <b>{f['name']}</b>{hidden}\n\n"
        f"📝 {f.get('description') or '—'}\n\n"
        f"{lbl[4]} {tags_str}\n"
        f"{cat_line}\n"
        f"{lbl[3]} {author_str}\n"
        f"{lbl[0]} <b>{f.get('downloads', 0)}</b>\n"
        f"{lbl[1]} {(f.get('created_at') or '')[:10]}\n"
        + (f"{lbl[2]} {size_str}\n" if size_str else "")
    )


async def send_file_card(target, f: dict, is_admin: bool, lang: str):
    card = format_file_card(f, lang)
    kb   = file_view_kb(f["id"], is_admin=is_admin, is_hidden=bool(f.get("is_hidden")), lang=lang)
    msg  = target if isinstance(target, Message) else target.message
    if f.get("preview_photo_id"):
        await msg.answer_photo(photo=f["preview_photo_id"], caption=card,
                               reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(card, reply_markup=kb, parse_mode="HTML")


# ── Пошук ─────────────────────────────────────────────────────────────────────

@router.message(Command("search"))
@router.message(F.text.in_({"🔍 Search", "🔍 Поиск"}))
async def cmd_search(message: Message, state: FSMContext, bot: Bot):
    if not await subscription_gate(message, bot):
        return
    lang  = get_user_lang(message.from_user.id)
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1 and parts[0].startswith("/"):
        return await _do_search(message, parts[1].strip(), message.from_user.id, lang)
    await state.set_state(SearchFSM.waiting_query)
    await state.update_data(lang=lang)
    await message.answer(t("search_ask", lang), reply_markup=cancel_kb(lang))


@router.message(SearchFSM.waiting_query)
async def got_search_query(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "en")
    if message.text == t("btn_cancel", lang):
        await state.clear()
        return await message.answer(t("cancelled", lang), reply_markup=main_menu_kb(lang))
    await state.clear()
    if check_spam(message.from_user.id):
        return await message.answer(
            t("antispam", lang, sec=int(get_remaining_cooldown(message.from_user.id))),
            reply_markup=main_menu_kb(lang)
        )
    await _do_search(message, message.text.strip(), message.from_user.id, lang)


async def _do_search(message: Message, query: str, tg_id: int, lang: str):
    key   = f"search:{query.lower()}"
    files = cache_get(key)
    if files is None:
        files = db.search_files(query)
        cache_set(key, files, ttl=30)
    db.log_action(tg_id, "search", query)
    if not files:
        return await message.answer(
            t("search_not_found", lang, query=query),
            parse_mode="HTML", reply_markup=main_menu_kb(lang)
        )
    await message.answer(
        t("search_results", lang, query=query, count=len(files)),
        parse_mode="HTML", reply_markup=file_list_kb(files)
    )


# ── Категорії ─────────────────────────────────────────────────────────────────

@router.message(F.text.in_({"📂 Categories", "📂 Категории"}))
async def cmd_categories(message: Message, bot: Bot):
    if not await subscription_gate(message, bot):
        return
    lang = get_user_lang(message.from_user.id)
    cats = db.get_all_categories()
    if not cats:
        await message.answer("📭 No categories yet." if lang == "en" else "📭 Категорий пока нет.")
        return
    await message.answer(t("categories_title", lang), reply_markup=categories_kb(cats, lang))


@router.callback_query(F.data == "cats_back")
async def cb_cats_back(callback: CallbackQuery):
    lang = get_user_lang(callback.from_user.id)
    cats = db.get_all_categories()
    try:
        await callback.message.edit_text(
            t("categories_title", lang),
            reply_markup=categories_kb(cats, lang)
        )
    except Exception:
        await callback.message.answer(
            t("categories_title", lang),
            reply_markup=categories_kb(cats, lang)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery):
    cat_id   = int(callback.data.split(":", 1)[1])
    lang     = get_user_lang(callback.from_user.id)
    cat      = db.get_category_by_id(cat_id)
    subs     = db.get_subcategories(cat_id)
    cat_name = cat["name"] if cat else str(cat_id)
    try:
        await callback.message.edit_text(
            t("subcategories_title", lang, category=cat_name),
            reply_markup=subcategories_kb(subs, cat_id, lang),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            t("subcategories_title", lang, category=cat_name),
            reply_markup=subcategories_kb(subs, cat_id, lang),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("subcat:"))
async def cb_subcategory(callback: CallbackQuery):
    _, cat_id_s, sub_id_s = callback.data.split(":")
    cat_id = int(cat_id_s)
    sub_id = int(sub_id_s)
    lang   = get_user_lang(callback.from_user.id)

    key   = f"files:{cat_id}:{sub_id}"
    files = cache_get(key)
    if files is None:
        files = db.get_files_by_category(cat_id, sub_id if sub_id else None)
        cache_set(key, files, ttl=60)

    cat   = db.get_category_by_id(cat_id)
    label = cat["name"] if cat else str(cat_id)
    if sub_id:
        sub   = db.get_subcategory_by_id(sub_id)
        label += f" › {sub['name']}" if sub else ""

    if not files:
        await callback.answer(t("category_empty", lang, name=label), show_alert=True)
        return
    await callback.message.answer(
        f"📂 <b>{label}</b> — {len(files)} file(s):",
        parse_mode="HTML",
        reply_markup=file_list_kb(files)
    )
    await callback.answer()


# ── Популярне ─────────────────────────────────────────────────────────────────

@router.message(F.text.in_({"⭐ Popular", "⭐ Популярное"}))
async def cmd_popular(message: Message, bot: Bot):
    if not await subscription_gate(message, bot):
        return
    lang  = get_user_lang(message.from_user.id)
    files = cache_get("popular:top10")
    if files is None:
        files = db.get_top_files(10)
        cache_set("popular:top10", files, ttl=120)
    if not files:
        return await message.answer(t("no_files", lang))
    await message.answer(t("popular_title", lang), parse_mode="HTML", reply_markup=file_list_kb(files))


# ── Перегляд файлу ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("file:"))
async def cb_view_file(callback: CallbackQuery):
    file_id  = int(callback.data.split(":", 1)[1])
    lang     = get_user_lang(callback.from_user.id)
    # БАГ БУВ: user міг бути None — тепер безпечно
    user     = db.get_user_by_telegram_id(callback.from_user.id)
    is_admin = bool(user and user.get("is_admin"))

    f = db.get_file_by_id(file_id)
    if not f:
        return await callback.answer(t("file_not_found", lang), show_alert=True)
    if not can_access_file(user, f, is_admin):
        return await callback.answer(t("file_hidden", lang), show_alert=True)
    await send_file_card(callback, f, is_admin, lang)
    await callback.answer()


# ── Завантажити файл ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("dl:"))
async def cb_download(callback: CallbackQuery):
    file_id = int(callback.data.split(":", 1)[1])
    lang    = get_user_lang(callback.from_user.id)
    if check_spam(callback.from_user.id):
        return await callback.answer(
            t("antispam", lang, sec=int(get_remaining_cooldown(callback.from_user.id))),
            show_alert=True
        )
    f = db.get_file_by_id(file_id)
    if not f:
        return await callback.answer(t("file_not_found", lang), show_alert=True)

    user     = db.get_user_by_telegram_id(callback.from_user.id)
    is_admin = bool(user and user.get("is_admin"))
    if not can_access_file(user, f, is_admin):
        return await callback.answer(t("file_hidden", lang), show_alert=True)

    sub_line = f"\n📁 {f['sub_name']}" if f.get("sub_name") else ""
    await callback.message.answer_document(
        document=f["file_id"],
        caption=f"📄 <b>{f['name']}</b>{sub_line}\n{f.get('description', '') or ''}",
        parse_mode="HTML"
    )
    u = db.get_or_create_user(
        callback.from_user.id, callback.from_user.username, callback.from_user.first_name
    )
    db.increment_downloads(file_id, u["id"])
    db.log_action(u["id"], "download", f"file_id={file_id}")
    await callback.answer(t("file_downloaded", lang))


# ── Схожі файли ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("similar:"))
async def cb_similar(callback: CallbackQuery):
    file_id = int(callback.data.split(":", 1)[1])
    lang    = get_user_lang(callback.from_user.id)
    f = db.get_file_by_id(file_id)
    if not f:
        return await callback.answer(t("file_not_found", lang), show_alert=True)

    similar = []
    if f.get("subcategory_id"):
        similar = [x for x in db.get_files_by_category(f["category_id"], f["subcategory_id"])
                   if x["id"] != file_id]
    if not similar and f.get("category_id"):
        similar = [x for x in db.get_files_by_category(f["category_id"])
                   if x["id"] != file_id]
    if not similar:
        tags = (f.get("tags") or "").split()
        if tags:
            similar = [x for x in db.search_files(tags[0]) if x["id"] != file_id]

    if not similar:
        return await callback.answer(t("no_similar", lang), show_alert=True)
    await callback.message.answer(
        t("similar_title", lang, count=len(similar[:10])),
        reply_markup=file_list_kb(similar[:10])
    )
    await callback.answer()


# ── Пряме посилання /file_ID ──────────────────────────────────────────────────

@router.message(F.text.regexp(r"^/file_(\d+)$"))
async def cmd_direct_file(message: Message):
    file_id  = int(message.text.split("_")[1])
    lang     = get_user_lang(message.from_user.id)
    user     = db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name
    )
    is_admin = bool(user.get("is_admin"))
    f = db.get_file_by_id(file_id)
    if not f:
        return await message.answer(t("file_not_found", lang))
    if not can_access_file(user, f, is_admin):
        return await message.answer(t("file_hidden", lang))
    await send_file_card(message, f, is_admin, lang)


# ── Inline ────────────────────────────────────────────────────────────────────

@router.inline_query()
async def inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query:
        return await inline_query.answer([], cache_time=1)
    files   = db.search_files(query)[:10]
    results = []
    for f in files:
        desc = (f.get("description") or "")[:100]
        sub  = f" [{f['sub_name']}]" if f.get("sub_name") else ""
        results.append(InlineQueryResultArticle(
            id    = hashlib.md5(str(f["id"]).encode()).hexdigest()[:8],
            title = f"{f['name']}{sub}",
            description=f"{desc} | ⬇️{f.get('downloads', 0)}",
            input_message_content=InputTextMessageContent(
                message_text=f"📄 <b>{f['name']}</b>{sub}\n\n{desc}\n\n👉 /file_{f['id']}",
                parse_mode="HTML"
            )
        ))
    await inline_query.answer(results, cache_time=30)
