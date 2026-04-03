# config.py

BOT_TOKEN = ""  # Заміни!

CHANNEL_ID = "@x0re3"
ADMIN_IDS  = []  # Заміни на свій Telegram ID

MAX_FILE_SIZE       = 50 * 1024 * 1024
ANTISPAM_MAX_ACTIONS = 5
ANTISPAM_WINDOW     = 10

DB_PATH  = "bot_database.db"
LOG_PATH = "logs.txt"

LANGUAGES = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
}
DEFAULT_LANG = "en"

# Типи файлів → авто-підказка категорії (якщо адмін вже її створив)
FILE_TYPE_MAP = {
    "lua": "Lua",
    "cfg": "Config",
    "ini": "Config",
    "exe": "Cheat",
    "dll": "Cheat",
    "zip": "Tool",
    "rar": "Tool",
    "json": "Tool",
    "txt": "Інше",
}
