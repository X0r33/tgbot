# i18n.py — інтернаціоналізація: всі тексти бота (EN/RU)

from config import DEFAULT_LANG

STRINGS: dict[str, dict[str, str]] = {

    "choose_language": {
        "en": "🌐 <b>Choose interface language:</b>",
        "ru": "🌐 <b>Выберите язык интерфейса:</b>",
    },
    "language_set": {
        "en": "✅ Language set: <b>English</b>",
        "ru": "✅ Язык установлен: <b>Русский</b>",
    },
    "welcome": {
        "en": "👋 Hello, <b>{name}</b>!\n\n🗂 <b>FileBOT</b> — store and find files easily.\n\nChoose an action from the menu below:",
        "ru": "👋 Привет, <b>{name}</b>!\n\n🗂 <b>FileBOT</b> — удобное хранение и поиск файлов.\n\nВыберите действие в меню:",
    },
    "subscribe_required": {
        "en": "📢 <b>You need to subscribe to the channel to use this bot!</b>\n\nSubscribe and press «✅ I subscribed»",
        "ru": "📢 <b>Для использования бота нужно подписаться на канал!</b>\n\nПодпишись и нажми «✅ Я подписался»",
    },
    "subscribe_btn": {
        "en": "📢 Subscribe to channel",
        "ru": "📢 Подписаться на канал",
    },
    "subscribed_btn": {
        "en": "✅ I subscribed",
        "ru": "✅ Я подписался",
    },
    "not_subscribed": {
        "en": "❌ You haven't subscribed yet!",
        "ru": "❌ Вы ещё не подписались на канал!",
    },
    "sub_confirmed": {
        "en": "✅ <b>Subscription confirmed!</b>\n\nWelcome to FileBOT 🎉",
        "ru": "✅ <b>Подписка подтверждена!</b>\n\nДобро пожаловать в FileBOT 🎉",
    },
    "banned": {
        "en": "🚫 Your account has been banned.",
        "ru": "🚫 Ваш аккаунт заблокирован.",
    },

    "btn_upload": {
        "en": "📁 Upload",
        "ru": "📁 Загрузить",
    },
    "btn_search": {
        "en": "🔍 Search",
        "ru": "🔍 Поиск",
    },
    "btn_categories": {
        "en": "📂 Categories",
        "ru": "📂 Категории",
    },
    "btn_popular": {
        "en": "⭐ Popular",
        "ru": "⭐ Популярное",
    },
    "btn_profile": {
        "en": "👤 My Profile",
        "ru": "👤 Мой профиль",
    },
    "btn_stats": {
        "en": "📊 Statistics",
        "ru": "📊 Статистика",
    },
    "btn_collections": {
        "en": "🗂 My Collections",
        "ru": "🗂 Мои сборки",
    },
    "btn_language": {
        "en": "🌐 Language",
        "ru": "🌐 Язык",
    },
    "btn_cancel": {
        "en": "❌ Cancel",
        "ru": "❌ Отмена",
    },
    "btn_skip": {
        "en": "⏭ Skip",
        "ru": "⏭ Пропустить",
    },
    "btn_back": {
        "en": "🔙 Back",
        "ru": "🔙 Назад",
    },
    "main_menu": {
        "en": "🏠 Main Menu",
        "ru": "🏠 Главное меню",
    },

    "upload_start": {
        "en": "📁 <b>File Upload</b>\n\nSend a file (up to 50 MB).\nSupported types: <code>.lua .cfg .exe .dll .zip .rar .json .txt</code> and others",
        "ru": "📁 <b>Загрузка файла</b>\n\nОтправьте файл (до 50 MB).\nПоддерживаемые типы: <code>.lua .cfg .exe .dll .zip .rar .json .txt</code> и другие",
    },
    "upload_too_big": {
        "en": "❌ File is too large! Maximum — 50 MB.\nYour file: {size} MB",
        "ru": "❌ Файл слишком большой! Максимум — 50 MB.\nВаш файл: {size} MB",
    },
    "upload_got_file": {
        "en": "✅ File received: <b>{name}</b>\n\n📝 Enter file name or press «Skip»:",
        "ru": "✅ Файл получен: <b>{name}</b>\n\n📝 Введите название файла или нажмите «Пропустить»:",
    },
    "upload_not_file": {
        "en": "⚠️ Please send a file (not a photo, not text).",
        "ru": "⚠️ Пожалуйста, отправьте файл (не фото, не текст).",
    },
    "upload_ask_desc": {
        "en": "📄 Enter file description:",
        "ru": "📄 Введите описание файла:",
    },
    "upload_ask_tags": {
        "en": "🏷 Enter tags separated by space or comma (e.g.: <code>hack lua bypass</code>)\nOr press «Skip»:",
        "ru": "🏷 Введите теги через пробел или запятую (например: <code>hack lua bypass</code>)\nИли нажмите «Пропустить»:",
    },
    "upload_ask_category": {
        "en": "📂 Choose a category (or keep <b>{suggested}</b> — press «Skip»):",
        "ru": "📂 Выберите категорию (или оставьте <b>{suggested}</b> — нажмите «Пропустить»):",
    },
    "upload_ask_subcategory": {
        "en": "📁 Choose a subcategory for <b>{category}</b>:",
        "ru": "📁 Выберите подкатегорию для <b>{category}</b>:",
    },
    "upload_ask_photo": {
        "en": "🖼 Send a preview photo or press «Skip»:",
        "ru": "🖼 Отправьте фото-превью или нажмите «Пропустить»:",
    },
    "upload_done": {
        "en": "✅ <b>File uploaded successfully!</b>\n\n📄 Name: <b>{name}</b>\n📂 Category: <b>{category}</b>\n📁 Subcategory: <b>{subcategory}</b>\n🆔 File ID: <code>{id}</code>\n\nLink: <code>/file_{id}</code>",
        "ru": "✅ <b>Файл успешно загружен!</b>\n\n📄 Название: <b>{name}</b>\n📂 Категория: <b>{category}</b>\n📁 Подкатегория: <b>{subcategory}</b>\n🆔 ID файла: <code>{id}</code>\n\nСсылка: <code>/file_{id}</code>",
    },

    "search_ask": {
        "en": "🔍 Enter search query (name or tag):",
        "ru": "🔍 Введите поисковый запрос (название или тег):",
    },
    "search_not_found": {
        "en": "🔍 Nothing found for «<b>{query}</b>».",
        "ru": "🔍 По запросу «<b>{query}</b>» ничего не найдено.",
    },
    "search_results": {
        "en": "🔍 Results for «<b>{query}</b>»: {count} file(s)",
        "ru": "🔍 Результаты для «<b>{query}</b>»: {count} файл(ов)",
    },
    "categories_title": {
        "en": "📂 Choose a category:",
        "ru": "📂 Выберите категорию:",
    },
    "subcategories_title": {
        "en": "📁 Subcategories of <b>{category}</b>:",
        "ru": "📁 Подкатегории <b>{category}</b>:",
    },
    "category_empty": {
        "en": "No files in category «{name}» yet.",
        "ru": "В категории «{name}» пока нет файлов.",
    },
    "popular_title": {
        "en": "⭐ <b>Top-10 files by downloads:</b>",
        "ru": "⭐ <b>Топ-10 файлов по загрузкам:</b>",
    },
    "no_files": {
        "en": "📭 No files yet.",
        "ru": "📭 Файлов пока нет.",
    },

    "file_hidden": {
        "en": "🔒 This file is hidden.",
        "ru": "🔒 Этот файл скрыт.",
    },
    "file_not_found": {
        "en": "❌ File not found.",
        "ru": "❌ Файл не найден.",
    },
    "file_downloaded": {
        "en": "⬇️ File sent!",
        "ru": "⬇️ Файл отправлен!",
    },
    "btn_download": {
        "en": "⬇️ Download",
        "ru": "⬇️ Скачать",
    },
    "btn_share": {
        "en": "📤 Share",
        "ru": "📤 Поделиться",
    },
    "btn_similar": {
        "en": "📑 Similar files",
        "ru": "📑 Похожие файлы",
    },
    "similar_title": {
        "en": "📑 Similar files ({count}):",
        "ru": "📑 Похожие файлы ({count}):",
    },
    "no_similar": {
        "en": "No similar files found.",
        "ru": "Похожих файлов не найдено.",
    },

    "profile_title": {
        "en": "👤 <b>Profile</b>\n\n🔹 Name: <b>{name}</b>\n🔹 Username: {username}\n🔹 ID: <code>{tg_id}</code>\n\n📁 Files uploaded: <b>{files}</b>\n⬇️ Total downloads: <b>{downloads}</b>\n🗂 Collections: <b>{collections}</b>\n📅 In bot since: {joined}\n🌐 Language: {interface_lang}",
        "ru": "👤 <b>Профиль</b>\n\n🔹 Имя: <b>{name}</b>\n🔹 Username: {username}\n🔹 ID: <code>{tg_id}</code>\n\n📁 Файлов загружено: <b>{files}</b>\n⬇️ Всего загрузок: <b>{downloads}</b>\n🗂 Сборок: <b>{collections}</b>\n📅 В боте с: {joined}\n🌐 Язык: {interface_lang}",
    },
    "my_files_title": {
        "en": "📁 My files ({count}):",
        "ru": "📁 Мои файлы ({count}):",
    },

    "stats_title": {
        "en": "📊 <b>General Statistics</b>\n\n👥 Users: <b>{users}</b>\n📁 Files: <b>{files}</b>\n⬇️ Downloads: <b>{downloads}</b>\n🚫 Banned: <b>{banned}</b>",
        "ru": "📊 <b>Общая статистика</b>\n\n👥 Пользователей: <b>{users}</b>\n📁 Файлов: <b>{files}</b>\n⬇️ Загрузок: <b>{downloads}</b>\n🚫 Заблокированных: <b>{banned}</b>",
    },

    "antispam": {
        "en": "⏳ Wait {sec} seconds before the next action.",
        "ru": "⏳ Подождите {sec} сек перед следующим действием.",
    },
    "cancelled": {
        "en": "❌ Cancelled.",
        "ru": "❌ Отменено.",
    },

    "collections_title": {
        "en": "🗂 <b>My Collections</b> ({count}):",
        "ru": "🗂 <b>Мои сборки</b> ({count}):",
    },
    "collection_empty": {
        "en": "📭 Collection is empty.",
        "ru": "📭 Сборка пуста.",
    },
    "collection_created": {
        "en": "✅ Collection <b>{name}</b> created!\nID: <code>{id}</code>\n\nAdd file: <code>/addtocol {id} FILE_ID</code>",
        "ru": "✅ Сборка <b>{name}</b> создана!\nID: <code>{id}</code>\n\nДобавить файл: <code>/addtocol {id} FILE_ID</code>",
    },
    "collection_ask_name": {
        "en": "📦 Enter name for the new collection:",
        "ru": "📦 Введите название новой сборки:",
    },
    "collection_ask_desc": {
        "en": "📝 Enter collection description or press «Skip»:",
        "ru": "📝 Введите описание сборки или нажмите «Пропустить»:",
    },
    "btn_new_collection": {
        "en": "➕ New Collection",
        "ru": "➕ Новая сборка",
    },
    "collection_files_title": {
        "en": "📦 Files in collection ({count}):",
        "ru": "📦 Файлы в сборке ({count}):",
    },
    "collection_added": {
        "en": "✅ File <b>{name}</b> added to collection!",
        "ru": "✅ Файл <b>{name}</b> добавлен в сборку!",
    },
    "collection_not_found": {
        "en": "❌ Collection not found or doesn't belong to you.",
        "ru": "❌ Сборка не найдена или не принадлежит вам.",
    },

    "help_text": {
        "en": "📖 <b>FileBOT Help</b>\n\n<b>Commands:</b>\n/start — start the bot\n/menu — main menu\n/upload — upload a file\n/search [query] — search\n/myfiles — my files\n/stats — statistics\n/help — this help\n/admin — admin panel\n\n<b>Inline mode:</b>\nType <code>@bot query</code> in any chat",
        "ru": "📖 <b>Справка FileBOT</b>\n\n<b>Команды:</b>\n/start — запуск бота\n/menu — главное меню\n/upload — загрузить файл\n/search [запрос] — поиск\n/myfiles — мои файлы\n/stats — статистика\n/help — эта справка\n/admin — панель администратора\n\n<b>Инлайн режим:</b>\nНапиши <code>@бот запрос</code> в любом чате",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    translations = STRINGS.get(key, {})
    text = translations.get(lang) or translations.get(DEFAULT_LANG, f"[{key}]")
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


def get_lang(user: dict | None) -> str:
    if not user:
        return DEFAULT_LANG
    return user.get("language") or DEFAULT_LANG