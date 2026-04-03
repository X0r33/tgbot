# handlers/admin.py — повна адмін-панель

from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import (
    admin_main_kb, admin_back_kb, confirm_kb,
    main_menu_kb, remove_kb, categories_kb,
    subcategories_kb, file_edit_kb, file_list_kb,
    upload_category_kb
)
from utils.logger import logger
from utils.cache import cache_clear
from config import ADMIN_IDS

router = Router()


# ─────────────────────────────────────────────────────────────────────────────
def is_admin(tg_id: int) -> bool:
    if tg_id in ADMIN_IDS:
        return True
    u = db.get_user_by_telegram_id(tg_id)
    return bool(u and u.get("is_admin"))


def _ensure_admin_flag(tg_id: int, username=None, first_name=None):
    """Автоматично ставить is_admin=1 для ADMIN_IDS."""
    if tg_id in ADMIN_IDS:
        db.get_or_create_user(tg_id, username, first_name)
        conn = db.get_connection()
        cur  = conn.cursor()
        cur.execute("UPDATE users SET is_admin=1 WHERE telegram_id=?", (tg_id,))
        conn.commit()
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# FSM стани
# ─────────────────────────────────────────────────────────────────────────────
class AdminFSM(StatesGroup):
    # Категорії
    new_cat_name    = State()
    rename_cat_id   = State()
    rename_cat_name = State()
    # Підкатегорії
    new_sub_cat_id  = State()
    new_sub_name    = State()
    rename_sub_id   = State()
    rename_sub_name = State()
    # Редагування файлу
    edit_file_id    = State()
    edit_file_field = State()   # name | desc | tags | cat | sub
    edit_file_value = State()
    edit_cat_choose = State()   # вибір категорії для файлу
    edit_sub_choose = State()   # вибір підкатегорії для файлу
    # Розсилка
    broadcast_msg   = State()
    # Промокоди
    promo_code      = State()
    promo_expires   = State()
    promo_uses      = State()


# ─────────────────────────────────────────────────────────────────────────────
# /admin
# ─────────────────────────────────────────────────────────────────────────────
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🚫 Немає доступу.")
    _ensure_admin_flag(message.from_user.id, message.from_user.username, message.from_user.first_name)
    stats = db.get_global_stats()
    await message.answer(
        f"🔧 <b>Адмін панель</b>\n\n"
        f"👥 Юзерів: {stats['users']} | 📁 Файлів: {stats['files']}\n"
        f"⬇️ Завантажень: {stats['downloads']} | 📂 Категорій: {stats['categories']}",
        parse_mode="HTML",
        reply_markup=admin_main_kb()
    )


# ─────────────────────────────────────────────────────────────────────────────
# Головний callback-диспетчер адмін-панелі
# ─────────────────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("adm:"))
async def cb_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫 Немає доступу.", show_alert=True)

    action = callback.data.split(":", 1)[1]

    # ── Назад ────────────────────────────────────────────────────────────────
    if action == "back":
        stats = db.get_global_stats()
        await callback.message.edit_text(
            f"🔧 <b>Адмін панель</b>\n\n"
            f"👥 Юзерів: {stats['users']} | 📁 Файлів: {stats['files']}\n"
            f"⬇️ Завантажень: {stats['downloads']} | 📂 Категорій: {stats['categories']}",
            parse_mode="HTML",
            reply_markup=admin_main_kb()
        )

    # ── Статистика ────────────────────────────────────────────────────────────
    elif action == "stats":
        stats  = db.get_global_stats()
        users  = db.get_all_users()
        today  = datetime.now().strftime("%Y-%m-%d")
        new_td = sum(1 for u in users if (u.get("join_date") or "").startswith(today))
        await callback.message.edit_text(
            f"📊 <b>Статистика</b>\n\n"
            f"👥 Всього юзерів: <b>{stats['users']}</b>  (+{new_td} сьогодні)\n"
            f"🚫 Заблокованих: <b>{stats['banned']}</b>\n\n"
            f"📁 Файлів: <b>{stats['files']}</b>\n"
            f"⬇️ Завантажень: <b>{stats['downloads']}</b>\n"
            f"📂 Категорій: <b>{stats['categories']}</b>",
            parse_mode="HTML",
            reply_markup=admin_back_kb()
        )

    # ── Логи ──────────────────────────────────────────────────────────────────
    elif action == "logs":
        logs = db.get_recent_logs(25)
        if not logs:
            return await callback.message.edit_text("📋 Логів немає.", reply_markup=admin_back_kb())
        lines = []
        for lg in logs:
            name = lg.get("first_name") or lg.get("username") or f"#{lg['user_id']}"
            lines.append(f"• {(lg.get('created_at') or '')[:16]} | {name} | {lg['action']} | {(lg.get('details') or '')[:25]}")
        await callback.message.edit_text(
            "📋 <b>Останні дії:</b>\n\n" + "\n".join(lines),
            parse_mode="HTML", reply_markup=admin_back_kb()
        )

    # ── Файли ─────────────────────────────────────────────────────────────────
    elif action == "files":
        files = db.get_all_files(30)
        if not files:
            return await callback.message.edit_text("📁 Файлів немає.", reply_markup=admin_back_kb())
        lines = []
        for f in files:
            hid  = " 🙈" if f.get("is_hidden") else ""
            cat  = f.get("cat_name") or "—"
            sub  = f"/{f['sub_name']}" if f.get("sub_name") else ""
            lines.append(f"• <code>/fedit_{f['id']}</code> {f['name'][:22]}{hid}  [{cat}{sub}]  ⬇️{f.get('downloads',0)}")
        text = "📁 <b>Файли (останні 30):</b>\n\n" + "\n".join(lines)
        text += "\n\n<i>Натисни /fedit_ID для редагування</i>"
        await callback.message.edit_text(text[:4096], parse_mode="HTML", reply_markup=admin_back_kb())

    # ── Юзери ─────────────────────────────────────────────────────────────────
    elif action == "users":
        users = db.get_all_users()[:30]
        lines = []
        for u in users:
            ban  = " 🚫" if u.get("is_banned") else ""
            adm  = " 👑" if u.get("is_admin")  else ""
            name = u.get("first_name") or u.get("username") or "—"
            lines.append(f"• <code>{u['telegram_id']}</code> {name}{ban}{adm}")
        text = "👥 <b>Юзери:</b>\n\n" + "\n".join(lines)
        text += "\n\n<i>/admin_ban ID [причина]\n/admin_unban ID</i>"
        await callback.message.edit_text(text[:4096], parse_mode="HTML", reply_markup=admin_back_kb())

    # ── Категорії ─────────────────────────────────────────────────────────────
    elif action == "cats":
        await _show_admin_cats(callback.message, edit=True)

    # ── Розсилка ──────────────────────────────────────────────────────────────
    elif action == "broadcast":
        await state.set_state(AdminFSM.broadcast_msg)
        await callback.message.answer("📣 Надішліть повідомлення для розсилки (текст/фото/файл):")

    # ── Промокоди ─────────────────────────────────────────────────────────────
    elif action == "promo":
        promos = db.get_all_promocodes()
        lines  = [
            f"• <code>{p['code']}</code>  {p['used_count']}/{p['max_uses']}  до {(p.get('expires_at') or '∞')[:10]}"
            for p in promos
        ]
        text = "🎟 <b>Промокоди:</b>\n\n" + ("\n".join(lines) if lines else "Немає.")
        text += "\n\n<i>/admin_promo — створити новий</i>"
        await callback.message.edit_text(text[:4096], parse_mode="HTML", reply_markup=admin_back_kb())

    # ── Експорт ───────────────────────────────────────────────────────────────
    elif action == "export":
        data = db.export_db_json().encode("utf-8")
        await callback.message.answer_document(
            BufferedInputFile(data, filename="db_export.json"),
            caption="💾 Експорт БД"
        )

    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# КАТЕГОРІЇ — адмін управління
# ─────────────────────────────────────────────────────────────────────────────

async def _show_admin_cats(message: Message, edit: bool = False):
    cats = db.get_all_categories()
    text = "📂 <b>Керування категоріями</b>\n\n"
    if cats:
        for c in cats:
            subs = db.get_subcategories(c["id"])
            sub_names = ", ".join(s["name"] for s in subs) if subs else "—"
            text += f"• <b>{c['name']}</b> (ID {c['id']})\n  └ {sub_names}\n"
    else:
        text += "Категорій ще немає.\n"
    text += "\n<i>Кнопки нижче для керування</i>"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    b = InlineKeyboardBuilder()
    for c in cats:
        b.row(
            InlineKeyboardButton(text=f"📁 Підкат. {c['name']}", callback_data=f"adm_sublist:{c['id']}"),
            InlineKeyboardButton(text=f"✏️ {c['name']}", callback_data=f"adm_cat:rename:{c['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"adm_cat:del:{c['id']}"),
        )
    b.row(InlineKeyboardButton(text="➕ Нова категорія", callback_data="adm_cat:new"))
    b.row(InlineKeyboardButton(text="🔙 Адмін меню",    callback_data="adm:back"))
    kb = b.as_markup()

    if edit:
        try:
            await message.edit_text(text[:4096], parse_mode="HTML", reply_markup=kb)
        except Exception:
            await message.answer(text[:4096], parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text[:4096], parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("adm_cat:"))
async def cb_adm_cat(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)

    parts = callback.data.split(":")  # adm_cat:new | adm_cat:rename:ID | adm_cat:del:ID
    action = parts[1]

    if action == "new":
        await state.set_state(AdminFSM.new_cat_name)
        await callback.message.answer("✏️ Введіть назву нової категорії:")
        await callback.answer()

    elif action == "rename":
        cat_id = int(parts[2])
        await state.set_state(AdminFSM.rename_cat_id)
        await state.update_data(rename_cat_id=cat_id)
        cat = db.get_category_by_id(cat_id)
        await state.set_state(AdminFSM.rename_cat_name)
        await callback.message.answer(
            f"✏️ Нова назва для категорії <b>{cat['name'] if cat else cat_id}</b>:",
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "del":
        cat_id = int(parts[2])
        cat    = db.get_category_by_id(cat_id)
        await callback.message.answer(
            f"⚠️ Видалити категорію <b>{cat['name'] if cat else cat_id}</b>?\n"
            f"Всі файли в ній втратять категорію.",
            parse_mode="HTML",
            reply_markup=confirm_kb(f"delcat:{cat_id}")
        )
        await callback.answer()


@router.message(AdminFSM.new_cat_name)
async def got_new_cat_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    name = message.text.strip()
    if not name:
        return await message.answer("❌ Порожня назва.")
    user = db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    cat_id = db.create_category(name, user["id"])
    await state.clear()
    cache_clear()
    logger.info(f"[admin] cat created: {name} by {message.from_user.id}")
    await message.answer(f"✅ Категорію <b>{name}</b> (ID {cat_id}) створено!", parse_mode="HTML")
    await _show_admin_cats(message)


@router.message(AdminFSM.rename_cat_name)
async def got_rename_cat(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    cat_id = data.get("rename_cat_id")
    db.rename_category(cat_id, message.text.strip())
    await state.clear()
    cache_clear()
    await message.answer(f"✅ Категорію перейменовано на <b>{message.text.strip()}</b>.", parse_mode="HTML")
    await _show_admin_cats(message)


@router.callback_query(F.data.startswith("confirm:delcat:"))
async def cb_confirm_delcat(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)
    cat_id = int(callback.data.split(":")[-1])
    cat    = db.get_category_by_id(cat_id)
    db.delete_category(cat_id)
    cache_clear()
    logger.info(f"[admin] cat deleted id={cat_id} by {callback.from_user.id}")
    await callback.message.edit_text(f"🗑 Категорію <b>{cat['name'] if cat else cat_id}</b> видалено.", parse_mode="HTML")
    await _show_admin_cats(callback.message)
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# ПІДКАТЕГОРІЇ — адмін управління
# ─────────────────────────────────────────────────────────────────────────────

async def _show_admin_subs(message: Message, cat_id: int, edit: bool = False):
    cat  = db.get_category_by_id(cat_id)
    subs = db.get_subcategories(cat_id)
    cat_name = cat["name"] if cat else str(cat_id)
    text = f"📁 <b>Підкатегорії: {cat_name}</b>\n\n"
    if subs:
        for s in subs:
            text += f"• <b>{s['name']}</b> (ID {s['id']})\n"
    else:
        text += "Підкатегорій немає.\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    b = InlineKeyboardBuilder()
    for s in subs:
        b.row(
            InlineKeyboardButton(text=f"✏️ {s['name']}", callback_data=f"adm_sub:rename:{s['id']}"),
            InlineKeyboardButton(text="🗑",               callback_data=f"adm_sub:del:{s['id']}"),
        )
    b.row(InlineKeyboardButton(text="➕ Нова підкатегорія", callback_data=f"adm_sub:new:{cat_id}"))
    b.row(InlineKeyboardButton(text="🔙 До категорій",      callback_data="adm:cats"))
    kb = b.as_markup()

    if edit:
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await message.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("adm_sublist:"))
async def cb_adm_sublist(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)
    cat_id = int(callback.data.split(":", 1)[1])
    await _show_admin_subs(callback.message, cat_id, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("adm_sub:"))
async def cb_adm_sub(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)

    parts  = callback.data.split(":")  # adm_sub:new:CAT_ID | adm_sub:rename:SUB_ID | adm_sub:del:SUB_ID
    action = parts[1]

    if action == "new":
        cat_id = int(parts[2])
        await state.set_state(AdminFSM.new_sub_name)
        await state.update_data(new_sub_cat_id=cat_id)
        cat = db.get_category_by_id(cat_id)
        await callback.message.answer(
            f"✏️ Нова підкатегорія для <b>{cat['name'] if cat else cat_id}</b>:",
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "rename":
        sub_id = int(parts[2])
        sub    = db.get_subcategory_by_id(sub_id)
        await state.set_state(AdminFSM.rename_sub_name)
        await state.update_data(rename_sub_id=sub_id, rename_sub_cat_id=sub["category_id"] if sub else 0)
        await callback.message.answer(
            f"✏️ Нова назва для <b>{sub['name'] if sub else sub_id}</b>:",
            parse_mode="HTML"
        )
        await callback.answer()

    elif action == "del":
        sub_id = int(parts[2])
        sub    = db.get_subcategory_by_id(sub_id)
        await callback.message.answer(
            f"⚠️ Видалити підкатегорію <b>{sub['name'] if sub else sub_id}</b>?",
            parse_mode="HTML",
            reply_markup=confirm_kb(f"delsub:{sub_id}:{sub['category_id'] if sub else 0}")
        )
        await callback.answer()


@router.message(AdminFSM.new_sub_name)
async def got_new_sub_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data   = await state.get_data()
    cat_id = data.get("new_sub_cat_id", 0)
    user   = db.get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    sub_id = db.create_subcategory(cat_id, message.text.strip(), user["id"])
    await state.clear()
    cache_clear()
    await message.answer(f"✅ Підкатегорію <b>{message.text.strip()}</b> (ID {sub_id}) створено!", parse_mode="HTML")
    await _show_admin_subs(message, cat_id)


@router.message(AdminFSM.rename_sub_name)
async def got_rename_sub(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data   = await state.get_data()
    sub_id = data.get("rename_sub_id")
    cat_id = data.get("rename_sub_cat_id", 0)
    db.rename_subcategory(sub_id, message.text.strip())
    await state.clear()
    cache_clear()
    await message.answer(f"✅ Перейменовано на <b>{message.text.strip()}</b>.", parse_mode="HTML")
    await _show_admin_subs(message, cat_id)


@router.callback_query(F.data.startswith("confirm:delsub:"))
async def cb_confirm_delsub(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)
    _, _, sub_id_s, cat_id_s = callback.data.split(":")
    sub_id = int(sub_id_s)
    cat_id = int(cat_id_s)
    sub    = db.get_subcategory_by_id(sub_id)
    db.delete_subcategory(sub_id)
    cache_clear()
    await callback.message.edit_text(
        f"🗑 Підкатегорію <b>{sub['name'] if sub else sub_id}</b> видалено.", parse_mode="HTML"
    )
    await _show_admin_subs(callback.message, cat_id)
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# РЕДАГУВАННЯ ФАЙЛІВ
# ─────────────────────────────────────────────────────────────────────────────

@router.message(F.text.regexp(r"^/fedit_(\d+)$"))
async def cmd_fedit(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🚫 Немає доступу.")
    file_id = int(message.text.split("_")[1])
    f = db.get_file_by_id(file_id)
    if not f:
        return await message.answer("❌ Файл не знайдено.")
    await _show_file_edit(message, f)


async def _show_file_edit(message: Message, f: dict):
    hidden = "🙈 Прихований" if f.get("is_hidden") else "👁 Видимий"
    cat  = f.get("cat_name") or "—"
    sub  = f.get("sub_name") or "—"
    text = (
        f"✏️ <b>Редагування файлу #{f['id']}</b>\n\n"
        f"📄 Назва: <b>{f['name']}</b>\n"
        f"📝 Опис: {(f.get('description') or '—')[:80]}\n"
        f"🏷 Теги: {f.get('tags') or '—'}\n"
        f"📂 Категорія: {cat}\n"
        f"📁 Підкатегорія: {sub}\n"
        f"👁 Статус: {hidden}\n"
        f"⬇️ Завантажень: {f.get('downloads', 0)}\n"
        f"📅 Додано: {(f.get('created_at') or '')[:10]}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=file_edit_kb(f["id"]))


# Кнопки редагування з file_edit_kb (fedit:field:file_id)
@router.callback_query(F.data.startswith("fedit:"))
async def cb_fedit(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)

    parts   = callback.data.split(":")  # fedit:field:file_id
    field   = parts[1]
    file_id = int(parts[2])

    f = db.get_file_by_id(file_id)
    if not f:
        return await callback.answer("❌ Файл не знайдено.", show_alert=True)

    await state.update_data(edit_file_id=file_id)

    if field == "name":
        await state.set_state(AdminFSM.edit_file_field)
        await state.update_data(edit_field="name")
        await callback.message.answer(
            f"✏️ Поточна назва: <b>{f['name']}</b>\n\nВведіть нову назву:",
            parse_mode="HTML"
        )

    elif field == "desc":
        await state.set_state(AdminFSM.edit_file_field)
        await state.update_data(edit_field="description")
        await callback.message.answer(
            f"✏️ Поточний опис:\n{f.get('description') or '—'}\n\nВведіть новий опис:"
        )

    elif field == "tags":
        await state.set_state(AdminFSM.edit_file_field)
        await state.update_data(edit_field="tags")
        await callback.message.answer(
            f"✏️ Поточні теги: <code>{f.get('tags') or '—'}</code>\n\nВведіть нові теги (через пробіл):",
            parse_mode="HTML"
        )

    elif field == "cat":
        cats = db.get_all_categories()
        await state.set_state(AdminFSM.edit_cat_choose)
        await callback.message.answer(
            "📂 Оберіть нову категорію:",
            reply_markup=upload_category_kb(cats)
        )

    elif field == "sub":
        cat_id = f.get("category_id")
        if not cat_id:
            return await callback.answer("Спочатку встановіть категорію.", show_alert=True)
        subs = db.get_subcategories(cat_id)
        from keyboards import upload_subcategory_kb
        await state.set_state(AdminFSM.edit_sub_choose)
        await callback.message.answer(
            "📁 Оберіть нову підкатегорію:",
            reply_markup=upload_subcategory_kb(subs, cat_id)
        )

    await callback.answer()


# Введення нового текстового значення для поля файлу
@router.message(AdminFSM.edit_file_field)
async def got_edit_file_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data    = await state.get_data()
    file_id = data.get("edit_file_id")
    field   = data.get("edit_field")
    value   = message.text.strip()

    if field == "tags":
        value = " ".join(x.lower() for x in value.replace(",", " ").split() if x)

    db.update_file(file_id, **{field: value})
    cache_clear()
    await state.clear()
    logger.info(f"[admin_edit] file={file_id} field={field} by={message.from_user.id}")
    f = db.get_file_by_id(file_id)
    await message.answer(f"✅ Поле <b>{field}</b> оновлено!", parse_mode="HTML")
    if f:
        await _show_file_edit(message, f)


# Вибір нової категорії для файлу (під час редагування)
@router.callback_query(AdminFSM.edit_cat_choose, F.data.startswith("upl_cat:"))
async def cb_edit_cat_choose(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    data    = await state.get_data()
    file_id = data.get("edit_file_id")
    val     = callback.data.split(":", 1)[1]

    if val == "new":
        await state.set_state(AdminFSM.new_cat_name)
        await callback.message.answer("✏️ Введіть назву нової категорії:")
        await callback.answer()
        return

    cat_id = int(val)
    db.update_file(file_id, category_id=cat_id, subcategory_id=None)
    cache_clear()
    await state.clear()
    f = db.get_file_by_id(file_id)
    await callback.message.answer("✅ Категорію оновлено!")
    if f:
        await _show_file_edit(callback.message, f)
    await callback.answer()


# Вибір нової підкатегорії для файлу (під час редагування)
@router.callback_query(AdminFSM.edit_sub_choose, F.data.startswith("upl_sub:"))
async def cb_edit_sub_choose(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    data    = await state.get_data()
    file_id = data.get("edit_file_id")
    raw     = callback.data[len("upl_sub:"):]

    if raw == "skip":
        db.update_file(file_id, subcategory_id=None)
    elif raw.startswith("new:"):
        cat_id = int(raw.split(":", 1)[1])
        await state.set_state(AdminFSM.new_sub_name)
        await state.update_data(new_sub_cat_id=cat_id)
        await callback.message.answer("✏️ Введіть назву нової підкатегорії:")
        await callback.answer()
        return
    else:
        db.update_file(file_id, subcategory_id=int(raw))

    cache_clear()
    await state.clear()
    f = db.get_file_by_id(file_id)
    await callback.message.answer("✅ Підкатегорію оновлено!")
    if f:
        await _show_file_edit(callback.message, f)
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# Inline кнопки з картки файлу: admin_toggle, admin_del
# ─────────────────────────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("admin_toggle:"))
async def cb_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)
    file_id = int(callback.data.split(":", 1)[1])
    new     = db.toggle_file_hidden(file_id)
    cache_clear()
    status  = "прихований 🙈" if new else "видимий 👁"
    logger.info(f"[admin_toggle] file={file_id} hidden={new} by={callback.from_user.id}")
    await callback.answer(f"Файл тепер {status}", show_alert=True)


@router.callback_query(F.data.startswith("admin_del:"))
async def cb_admin_del(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)
    file_id = int(callback.data.split(":", 1)[1])
    f       = db.get_file_by_id(file_id)
    await callback.message.answer(
        f"⚠️ Видалити файл <b>{f['name'] if f else file_id}</b>?",
        parse_mode="HTML",
        reply_markup=confirm_kb(f"delfile:{file_id}")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm:delfile:"))
async def cb_confirm_delfile(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return await callback.answer("🚫", show_alert=True)
    file_id = int(callback.data.split(":")[-1])
    f       = db.get_file_by_id(file_id)
    name    = f["name"] if f else str(file_id)
    db.delete_file(file_id)
    cache_clear()
    logger.info(f"[admin_del] file={file_id} by={callback.from_user.id}")
    await callback.message.edit_text(f"🗑 Файл <b>{name}</b> видалено.", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "cancel_action")
async def cb_cancel(callback: CallbackQuery):
    await callback.message.edit_text("❌ Скасовано.")
    await callback.answer()


# ─────────────────────────────────────────────────────────────────────────────
# БАН / РОЗБАН
# ─────────────────────────────────────────────────────────────────────────────
@router.message(F.text.regexp(r"^/admin_ban \d+"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id): return
    parts  = message.text.split(maxsplit=2)
    tg_id  = int(parts[1])
    reason = parts[2] if len(parts) > 2 else "—"
    db.ban_user(tg_id, reason)
    logger.info(f"[ban] {tg_id} by {message.from_user.id} reason={reason}")
    await message.answer(f"🚫 Юзера <code>{tg_id}</code> заблоковано.\nПричина: {reason}", parse_mode="HTML")


@router.message(F.text.regexp(r"^/admin_unban \d+"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id): return
    tg_id = int(message.text.split()[1])
    db.unban_user(tg_id)
    await message.answer(f"✅ Юзера <code>{tg_id}</code> розблоковано.", parse_mode="HTML")


# ─────────────────────────────────────────────────────────────────────────────
# РОЗСИЛКА
# ─────────────────────────────────────────────────────────────────────────────
@router.message(AdminFSM.broadcast_msg)
async def got_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await state.clear(); return
    users = db.get_all_users()
    sent = failed = 0
    await message.answer(f"📣 Розсилка для {len(users)} юзерів...")
    for u in users:
        if u.get("is_banned"): continue
        try:
            if message.photo:
                await bot.send_photo(u["telegram_id"], message.photo[-1].file_id, caption=message.caption or "")
            elif message.document:
                await bot.send_document(u["telegram_id"], message.document.file_id, caption=message.caption or "")
            else:
                await bot.send_message(u["telegram_id"], message.text or "", parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
    await state.clear()
    logger.info(f"[broadcast] sent={sent} failed={failed} by={message.from_user.id}")
    await message.answer(f"✅ Надіслано: {sent}  ❌ Помилок: {failed}", reply_markup=main_menu_kb("en"))


# ─────────────────────────────────────────────────────────────────────────────
# ПРОМОКОДИ — РОШИРЕНА ВЕРСІЯ з прив'язкою файлів
# ─────────────────────────────────────────────────────────────────────────────

class PromoFSM(StatesGroup):
    code = State()
    name = State()
    desc = State()
    expires = State()
    max_uses = State()
    add_files = State()


@router.message(Command("admin_promo"))
async def cmd_admin_promo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.set_state(PromoFSM.code)
    await message.answer(
        "🎟 <b>Створення промокоду</b>\n\n"
        "Крок 1/6: Введіть код (літери/цифри/підкреслення):",
        parse_mode="HTML", reply_markup=remove_kb()
    )


@router.message(PromoFSM.code)
async def promo_got_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    if not code.replace("_", "").isalnum():
        return await message.answer("❌ Тільки літери, цифри, підкреслення.")
    await state.update_data(code=code)
    await state.set_state(PromoFSM.name)
    await message.answer("Крок 2/6: Введіть назву промокоду (наприклад: «VIP доступ»):")


@router.message(PromoFSM.name)
async def promo_got_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip()[:100])
    await state.set_state(PromoFSM.desc)
    await message.answer("Крок 3/6: Введіть опис (або 0 для пропуску):")


@router.message(PromoFSM.desc)
async def promo_got_desc(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "0" else message.text.strip()[:200]
    await state.update_data(desc=desc)
    await state.set_state(PromoFSM.expires)
    await message.answer("Крок 4/6: Термін дії <code>YYYY-MM-DD</code> або <code>0</code> для безліміту:", parse_mode="HTML")


@router.message(PromoFSM.expires)
async def promo_got_expires(message: Message, state: FSMContext):
    txt = message.text.strip()
    expires = None if txt == "0" else txt
    await state.update_data(expires=expires)
    await state.set_state(PromoFSM.max_uses)
    await message.answer("Крок 5/6: Макс. кількість використань (число):")


@router.message(PromoFSM.max_uses)
async def promo_got_max_uses(message: Message, state: FSMContext):
    try:
        max_uses = int(message.text.strip())
    except ValueError:
        return await message.answer("❌ Введіть число!")
    await state.update_data(max_uses=max_uses)
    
    data = await state.get_data()
    user = db.get_user_by_telegram_id(message.from_user.id)
    db.create_promocode(
        code=data["code"],
        expires_at=data.get("expires"),
        created_by=user["id"] if user else 0,
        max_uses=max_uses,
        name=data["name"],
        description=data.get("desc", "")
    )
    
    # Показуємо всі файли для вибору
    files = db.get_all_files(100)
    await state.set_state(PromoFSM.add_files)
    await state.update_data(promo_code=data["code"])
    
    if not files:
        await message.answer("⚠️ Немає файлів для прив'язки. Промокод створено без файлів.")
        await state.clear()
        return
    
    text = f"✅ Промокод <b>{data['code']}</b> створено!\n\n"
    text += "Крок 6/6: Виберіть файли для прив'язки (надішліть ID через пробіл)\n\n"
    text += "📁 <b>Доступні файли:</b>\n"
    for f in files[:30]:
        hid = " 🙈" if f.get("is_hidden") else ""
        text += f"• <code>{f['id']}</code> — {f['name'][:30]}{hid}\n"
    text += "\n<i>Наприклад: /add_promo_files КОД 123 456 789</i>\n"
    text += "Або натисніть /skip_promo_files"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("skip_promo_files"))
async def skip_promo_files(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.clear()
    await message.answer("✅ Промокод створено без файлів.", reply_markup=main_menu_kb())


@router.message(Command("add_promo_files"))
async def add_promo_files(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    parts = message.text.split()
    if len(parts) < 3:
        return await message.answer("❌ Використання: /add_promo_files КОД ID1 ID2 ID3 ...")
    
    code = parts[1].upper()
    file_ids = []
    for p in parts[2:]:
        try:
            file_ids.append(int(p))
        except ValueError:
            pass
    
    if not file_ids:
        return await message.answer("❌ Не вказано жодного ID файлу.")
    
    promo = db.get_promo_by_code(code)
    if not promo:
        return await message.answer(f"❌ Промокод <code>{code}</code> не знайдено.", parse_mode="HTML")
    
    db.add_files_to_promo(code, file_ids)
    await state.clear()
    await message.answer(
        f"✅ До промокоду <b>{code}</b> прив'язано {len(file_ids)} файлів.\n"
        f"ID: {', '.join(str(fid) for fid in file_ids)}",
        parse_mode="HTML"
    )



# ─────────────────────────────────────────────────────────────────────────────
# ПЕРЕГЛЯД ФАЙЛІВ КОРИСТУВАЧА (ОТРИМАНИХ ЧЕРЕЗ ПРОМО)
# ─────────────────────────────────────────────────────────────────────────────

@router.message(Command("user_files"))
async def cmd_user_files(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🚫 Немає доступу.")
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("❌ Використання: /user_files USER_ID")
    try:
        tg_id = int(parts[1])
    except ValueError:
        return await message.answer("❌ ID має бути числом.")
    
    user = db.get_user_by_telegram_id(tg_id)
    if not user:
        return await message.answer(f"❌ Користувача {tg_id} не знайдено.")
    
    promo_files = db.get_user_promo_files(user["id"])
    if not promo_files:
        return await message.answer(f"👤 {user.get('first_name')}\n📦 Немає доступу до приватних файлів.")
    
    files = []
    for fid in promo_files:
        f = db.get_file_by_id(fid)
        if f:
            files.append(f)
    
    text = f"👤 <b>{user.get('first_name')}</b>\n📦 Доступ до {len(files)} файлів:\n\n"
    for f in files:
        hidden = " 🙈" if f.get("is_hidden") else ""
        text += f"• <code>{f['id']}</code> — {f['name'][:40]}{hidden}\n"
    
    await message.answer(text[:4096], parse_mode="HTML")
