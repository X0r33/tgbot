# keyboards.py

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import LANGUAGES
from i18n import t


def main_menu_kb(lang: str = "en") -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text=t("btn_upload", lang)),
          KeyboardButton(text=t("btn_search", lang)))
    b.row(KeyboardButton(text=t("btn_categories", lang)),
          KeyboardButton(text=t("btn_popular", lang)))
    b.row(KeyboardButton(text=t("btn_profile", lang)),
          KeyboardButton(text=t("btn_stats", lang)))
    b.row(KeyboardButton(text=t("btn_collections", lang)),
          KeyboardButton(text=t("btn_language", lang)))
    return b.as_markup(resize_keyboard=True)


def language_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for code, label in LANGUAGES.items():
        b.row(InlineKeyboardButton(text=label, callback_data=f"setlang:{code}"))
    return b.as_markup()


def subscribe_kb(channel_url: str, lang: str = "en") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=t("subscribe_btn", lang), url=channel_url))
    b.row(InlineKeyboardButton(text=t("subscribed_btn", lang), callback_data="check_subscription"))
    return b.as_markup()


def cancel_kb(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_cancel", lang))]],
        resize_keyboard=True
    )

def skip_kb(lang: str = "en") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_skip", lang)),
                   KeyboardButton(text=t("btn_cancel", lang))]],
        resize_keyboard=True
    )

def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def categories_kb(categories: list, lang: str = "en",
                  admin_mode: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for cat in categories:
        b.row(InlineKeyboardButton(
            text=f"📂 {cat['name']}",
            callback_data=f"cat:{cat['id']}"
        ))
    if admin_mode:
        b.row(InlineKeyboardButton(text="➕ New category", callback_data="adm_cat:new"))
    return b.as_markup()


def subcategories_kb(subs: list, category_id: int, lang: str = "en",
                     admin_mode: bool = False,
                     show_all_btn: bool = True) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if show_all_btn:
        all_lbl = {"en": "📂 All category files", "ru": "📂 Все файлы категории"}
        b.row(InlineKeyboardButton(
            text=all_lbl.get(lang, all_lbl["en"]),
            callback_data=f"subcat:{category_id}:0"
        ))
    for s in subs:
        b.row(InlineKeyboardButton(
            text=f"📁 {s['name']}",
            callback_data=f"subcat:{category_id}:{s['id']}"
        ))
    if admin_mode:
        b.row(InlineKeyboardButton(
            text="➕ New subcategory",
            callback_data=f"adm_sub:new:{category_id}"
        ))
    b.row(InlineKeyboardButton(text=t("btn_back", lang), callback_data="cats_back"))
    return b.as_markup()


def upload_category_kb(categories: list, lang: str = "en") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for cat in categories:
        b.row(InlineKeyboardButton(
            text=f"📂 {cat['name']}",
            callback_data=f"upl_cat:{cat['id']}"
        ))
    b.row(InlineKeyboardButton(text="➕ New category", callback_data="upl_cat:new"))
    return b.as_markup()


def upload_subcategory_kb(subs: list, category_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in subs:
        b.row(InlineKeyboardButton(
            text=f"📁 {s['name']}",
            callback_data=f"upl_sub:{s['id']}"
        ))
    b.row(InlineKeyboardButton(
        text="➕ New subcategory",
        callback_data=f"upl_sub:new:{category_id}"
    ))
    b.row(InlineKeyboardButton(
        text=t("btn_skip", lang),
        callback_data="upl_sub:skip"
    ))
    return b.as_markup()


def file_view_kb(file_id: int, is_admin: bool = False,
                 is_hidden: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=t("btn_download", lang), callback_data=f"dl:{file_id}"))
    b.row(
        InlineKeyboardButton(text=t("btn_share", lang), switch_inline_query=f"file:{file_id}"),
        InlineKeyboardButton(text=t("btn_similar", lang), callback_data=f"similar:{file_id}"),
    )
    if is_admin:
        b.row(
            InlineKeyboardButton(
                text="👁 Show" if is_hidden else "🙈 Hide",
                callback_data=f"admin_toggle:{file_id}"
            ),
            InlineKeyboardButton(text="🗑 Delete", callback_data=f"admin_del:{file_id}"),
        )
        b.row(InlineKeyboardButton(text="✏️ Edit", callback_data=f"admin_edit:{file_id}"))
    return b.as_markup()


def file_list_kb(files: list, page: int = 0) -> InlineKeyboardMarkup:
    b        = InlineKeyboardBuilder()
    per_page = 5
    start    = page * per_page
    chunk    = files[start: start + per_page]

    for f in chunk:
        name = (f["name"][:26] + "…") if len(f["name"]) > 26 else f["name"]
        sub  = f" · {f['sub_name']}" if f.get("sub_name") else ""
        b.row(InlineKeyboardButton(
            text=f"📄 {name}{sub} ({f.get('downloads',0)}⬇️)",
            callback_data=f"file:{f['id']}"
        ))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"filepage:{page-1}"))
    if start + per_page < len(files):
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"filepage:{page+1}"))
    if nav:
        b.row(*nav)
    return b.as_markup()


def admin_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="📊 Statistics",  callback_data="adm:stats"),
        InlineKeyboardButton(text="📋 Logs",        callback_data="adm:logs"),
    )
    b.row(
        InlineKeyboardButton(text="📁 Files",       callback_data="adm:files"),
        InlineKeyboardButton(text="👥 Users",       callback_data="adm:users"),
    )
    b.row(
        InlineKeyboardButton(text="📂 Categories",   callback_data="adm:cats"),
        InlineKeyboardButton(text="📣 Broadcast",    callback_data="adm:broadcast"),
    )
    b.row(
        InlineKeyboardButton(text="🎟 Promocodes",   callback_data="adm:promo"),
        InlineKeyboardButton(text="💾 Export",     callback_data="adm:export"),
    )
    return b.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🔙 Admin menu", callback_data="adm:back"))
    return b.as_markup()


def confirm_kb(action: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Yes", callback_data=f"confirm:{action}"),
        InlineKeyboardButton(text="❌ No",  callback_data="cancel_action"),
    )
    return b.as_markup()


def file_edit_kb(file_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✏️ Name",       callback_data=f"fedit:name:{file_id}"),
        InlineKeyboardButton(text="✏️ Description", callback_data=f"fedit:desc:{file_id}"),
    )
    b.row(
        InlineKeyboardButton(text="🏷 Tags",        callback_data=f"fedit:tags:{file_id}"),
        InlineKeyboardButton(text="📂 Category",   callback_data=f"fedit:cat:{file_id}"),
    )
    b.row(
        InlineKeyboardButton(text="📁 Subcategory", callback_data=f"fedit:sub:{file_id}"),
        InlineKeyboardButton(text="🙈/👁 Visibility", callback_data=f"admin_toggle:{file_id}"),
    )
    b.row(
        InlineKeyboardButton(text="🗑 Delete file", callback_data=f"admin_del:{file_id}"),
    )
    b.row(InlineKeyboardButton(text="🔙 Admin menu", callback_data="adm:back"))
    return b.as_markup()


def collection_kb(collections: list, lang: str = "en") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for col in collections:
        b.row(InlineKeyboardButton(
            text=f"📦 {col['name']}",
            callback_data=f"col:{col['id']}"
        ))
    b.row(InlineKeyboardButton(text=t("btn_new_collection", lang), callback_data="col:new"))
    return b.as_markup()