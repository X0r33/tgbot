# database.py

import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT, first_name TEXT,
            language TEXT DEFAULT 'en',
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            join_date TEXT DEFAULT (datetime('now')),
            last_active TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_by INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_by INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(category_id, name)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL, name TEXT NOT NULL,
            description TEXT, file_type TEXT DEFAULT 'other',
            category_id INTEGER, subcategory_id INTEGER,
            size INTEGER DEFAULT 0, tags TEXT DEFAULT '',
            preview_photo_id TEXT, author_id INTEGER,
            downloads INTEGER DEFAULT 0, is_hidden INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS downloads_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, file_id INTEGER,
            download_date TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id INTEGER PRIMARY KEY, reason TEXT,
            banned_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            expires_at TEXT, created_by INTEGER,
            max_uses INTEGER DEFAULT 1, used_count INTEGER DEFAULT 0,
            name TEXT DEFAULT '', description TEXT DEFAULT ''
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS promo_files (
            promo_code TEXT, file_id INTEGER,
            PRIMARY KEY (promo_code, file_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_promo_files (
            user_id INTEGER, file_id INTEGER, promo_code TEXT,
            activated_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, file_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, description TEXT,
            author_id INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS collection_files (
            collection_id INTEGER, file_id INTEGER,
            PRIMARY KEY (collection_id, file_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, action TEXT, details TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


# ── USERS ─────────────────────────────────────────────────────────────────────

def get_or_create_user(telegram_id: int, username=None, first_name=None) -> dict:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    user = cur.fetchone()
    if not user:
        cur.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (?,?,?)",
            (telegram_id, username, first_name)
        )
        conn.commit()
        cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
        user = cur.fetchone()
    else:
        cur.execute(
            "UPDATE users SET username=?, first_name=?, last_active=datetime('now') WHERE telegram_id=?",
            (username, first_name, telegram_id)
        )
        conn.commit()
    result = dict(user)
    conn.close()
    return result


def get_user_by_telegram_id(telegram_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def set_user_language(telegram_id: int, lang: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET language=? WHERE telegram_id=?", (lang, telegram_id))
    conn.commit()
    conn.close()


def is_new_user(telegram_id: int) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT language FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return not row or not row["language"]


def is_banned(telegram_id: int) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT is_banned FROM users WHERE telegram_id=?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row["is_banned"]) if row else False


def ban_user(telegram_id: int, reason: str = "—"):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET is_banned=1 WHERE telegram_id=?", (telegram_id,))
    user = get_user_by_telegram_id(telegram_id)
    if user:
        cur.execute("INSERT OR REPLACE INTO bans (user_id, reason) VALUES (?,?)", (user["id"], reason))
    conn.commit()
    conn.close()


def unban_user(telegram_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET is_banned=0 WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()


def get_all_users() -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY join_date DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ── CATEGORIES ────────────────────────────────────────────────────────────────

def get_all_categories() -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_category_by_id(cat_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM categories WHERE id=?", (cat_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_category(name: str, created_by: int) -> int:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO categories (name, created_by) VALUES (?,?)", (name.strip(), created_by))
    conn.commit()
    cur.execute("SELECT id FROM categories WHERE name=?", (name.strip(),))
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else 0


def delete_category(cat_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM subcategories WHERE category_id=?", (cat_id,))
    cur.execute("UPDATE files SET category_id=NULL WHERE category_id=?", (cat_id,))
    cur.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


def rename_category(cat_id: int, new_name: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE categories SET name=? WHERE id=?", (new_name.strip(), cat_id))
    conn.commit()
    conn.close()


# ── SUBCATEGORIES ─────────────────────────────────────────────────────────────

def get_subcategories(category_id: int) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM subcategories WHERE category_id=? ORDER BY name", (category_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_subcategory_by_id(sub_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM subcategories WHERE id=?", (sub_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_subcategory(category_id: int, name: str, created_by: int) -> int:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO subcategories (category_id, name, created_by) VALUES (?,?,?)",
        (category_id, name.strip(), created_by)
    )
    conn.commit()
    cur.execute("SELECT id FROM subcategories WHERE category_id=? AND name=?", (category_id, name.strip()))
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else 0


def delete_subcategory(sub_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE files SET subcategory_id=NULL WHERE subcategory_id=?", (sub_id,))
    cur.execute("DELETE FROM subcategories WHERE id=?", (sub_id,))
    conn.commit()
    conn.close()


def rename_subcategory(sub_id: int, new_name: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE subcategories SET name=? WHERE id=?", (new_name.strip(), sub_id))
    conn.commit()
    conn.close()


# ── FILES ─────────────────────────────────────────────────────────────────────

def add_file(file_id: str, name: str, description: str, file_type: str,
             category_id: int, subcategory_id: int, size: int, tags: str,
             author_id: int, preview_photo_id: str = None) -> int:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO files (file_id, name, description, file_type, category_id, subcategory_id,
             size, tags, author_id, preview_photo_id)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (file_id, name, description, file_type,
          category_id or None, subcategory_id or None,
          size, tags, author_id, preview_photo_id))
    fid = cur.lastrowid
    conn.commit()
    conn.close()
    return fid


def get_file_by_id(file_db_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT f.*, u.username, u.first_name, u.telegram_id AS author_telegram_id,
               c.name AS cat_name, s.name AS sub_name
        FROM files f
        LEFT JOIN users         u ON f.author_id      = u.id
        LEFT JOIN categories    c ON f.category_id    = c.id
        LEFT JOIN subcategories s ON f.subcategory_id = s.id
        WHERE f.id=?
    """, (file_db_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def search_files(query: str, include_hidden: bool = False) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    hf   = "" if include_hidden else "AND f.is_hidden=0"
    q    = f"%{query.lower()}%"
    cur.execute(f"""
        SELECT f.*, u.username, u.first_name, u.telegram_id AS author_telegram_id,
               c.name AS cat_name, s.name AS sub_name
        FROM files f
        LEFT JOIN users         u ON f.author_id      = u.id
        LEFT JOIN categories    c ON f.category_id    = c.id
        LEFT JOIN subcategories s ON f.subcategory_id = s.id
        WHERE (LOWER(f.name) LIKE ? OR LOWER(f.tags) LIKE ?) {hf}
        ORDER BY f.downloads DESC LIMIT 30
    """, (q, q))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_files_by_category(category_id: int, subcategory_id: int = None,
                           include_hidden: bool = False) -> list:
    conn   = get_connection()
    cur    = conn.cursor()
    hf     = "" if include_hidden else "AND f.is_hidden=0"
    sf     = "AND f.subcategory_id=?" if subcategory_id else ""
    params = [category_id]
    if subcategory_id:
        params.append(subcategory_id)
    cur.execute(f"""
        SELECT f.*, u.username, u.first_name, u.telegram_id AS author_telegram_id,
               c.name AS cat_name, s.name AS sub_name
        FROM files f
        LEFT JOIN users         u ON f.author_id      = u.id
        LEFT JOIN categories    c ON f.category_id    = c.id
        LEFT JOIN subcategories s ON f.subcategory_id = s.id
        WHERE f.category_id=? {sf} {hf}
        ORDER BY f.created_at DESC LIMIT 50
    """, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_top_files(limit: int = 10) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT f.*, u.username, u.first_name, u.telegram_id AS author_telegram_id,
               c.name AS cat_name, s.name AS sub_name
        FROM files f
        LEFT JOIN users         u ON f.author_id      = u.id
        LEFT JOIN categories    c ON f.category_id    = c.id
        LEFT JOIN subcategories s ON f.subcategory_id = s.id
        WHERE f.is_hidden=0
        ORDER BY f.downloads DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_user_files(user_db_id: int) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT f.*, c.name AS cat_name, s.name AS sub_name
        FROM files f
        LEFT JOIN categories    c ON f.category_id    = c.id
        LEFT JOIN subcategories s ON f.subcategory_id = s.id
        WHERE f.author_id=?
        ORDER BY f.created_at DESC
    """, (user_db_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_all_files(limit: int = 50) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT f.*, c.name AS cat_name, s.name AS sub_name, u.username, u.first_name
        FROM files f
        LEFT JOIN categories    c ON f.category_id    = c.id
        LEFT JOIN subcategories s ON f.subcategory_id = s.id
        LEFT JOIN users         u ON f.author_id      = u.id
        ORDER BY f.created_at DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def increment_downloads(file_db_id: int, user_db_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE files SET downloads=downloads+1 WHERE id=?", (file_db_id,))
    cur.execute("INSERT INTO downloads_log (user_id, file_id) VALUES (?,?)", (user_db_id, file_db_id))
    conn.commit()
    conn.close()


def delete_file(file_db_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM downloads_log    WHERE file_id=?", (file_db_id,))
    cur.execute("DELETE FROM collection_files WHERE file_id=?", (file_db_id,))
    cur.execute("DELETE FROM user_promo_files WHERE file_id=?", (file_db_id,))
    cur.execute("DELETE FROM promo_files      WHERE file_id=?", (file_db_id,))
    cur.execute("DELETE FROM files            WHERE id=?",      (file_db_id,))
    conn.commit()
    conn.close()


def toggle_file_hidden(file_db_id: int) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT is_hidden FROM files WHERE id=?", (file_db_id,))
    row = cur.fetchone()
    new = 0 if (row and row["is_hidden"]) else 1
    cur.execute("UPDATE files SET is_hidden=? WHERE id=?", (new, file_db_id))
    conn.commit()
    conn.close()
    return bool(new)


def update_file(file_db_id: int, **kwargs):
    allowed = {"name", "description", "tags", "category_id", "subcategory_id"}
    fields  = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    conn = get_connection()
    cur  = conn.cursor()
    set_clause = ", ".join(f"{k}=?" for k in fields)
    values     = list(fields.values()) + [file_db_id]
    cur.execute(f"UPDATE files SET {set_clause}, updated_at=datetime('now') WHERE id=?", values)
    conn.commit()
    conn.close()


# ── STATS ─────────────────────────────────────────────────────────────────────

def get_global_stats() -> dict:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users");                    users  = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM files WHERE is_hidden=0");  files  = cur.fetchone()["c"]
    cur.execute("SELECT COALESCE(SUM(downloads),0) AS c FROM files");  dl     = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE is_banned=1");  banned = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM categories");               cats   = cur.fetchone()["c"]
    conn.close()
    return {"users": users, "files": files, "downloads": dl, "banned": banned, "categories": cats}


# ── PROMOCODES ────────────────────────────────────────────────────────────────

def create_promocode(code: str, expires_at, created_by: int,
                     max_uses: int = 1, name: str = "", description: str = ""):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO promocodes "
        "(code, expires_at, created_by, max_uses, name, description) VALUES (?,?,?,?,?,?)",
        (code, expires_at, created_by, max_uses, name, description)
    )
    conn.commit()
    conn.close()


def add_files_to_promo(code: str, file_ids: list):
    conn = get_connection()
    cur  = conn.cursor()
    for fid in file_ids:
        cur.execute(
            "INSERT OR IGNORE INTO promo_files (promo_code, file_id) VALUES (?,?)",
            (code, fid)
        )
    conn.commit()
    conn.close()


def get_promo_files(code: str) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT file_id FROM promo_files WHERE promo_code=?", (code,))
    rows = [r["file_id"] for r in cur.fetchall()]
    conn.close()
    return rows


def get_promo_by_code(code: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM promocodes WHERE code=?", (code,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_promocodes() -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM promocodes ORDER BY rowid DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def has_promo_access(user_db_id: int, file_id: int) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT 1 FROM user_promo_files WHERE user_id=? AND file_id=?",
        (user_db_id, file_id)
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def get_user_promo_files(user_db_id: int) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT file_id FROM user_promo_files WHERE user_id=?", (user_db_id,))
    rows = [r["file_id"] for r in cur.fetchall()]
    conn.close()
    return rows


def use_promocode(code: str, user_db_id: int) -> tuple:
    """
    Активує промокод для юзера.
    Повертає (True, msg) або (False, msg).
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM promocodes WHERE code=?", (code,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return False, "❌ Промокод не знайдено."

    if row["used_count"] >= row["max_uses"]:
        conn.close()
        return False, "❌ Промокод вже використано максимальну кількість разів."

    if row["expires_at"]:
        try:
            if datetime.fromisoformat(row["expires_at"]) < datetime.now():
                conn.close()
                return False, "❌ Термін дії промокоду закінчився."
        except ValueError:
            pass

    # Перевіряємо чи юзер вже використовував цей промокод
    cur.execute(
        "SELECT 1 FROM user_promo_files WHERE user_id=? AND promo_code=?",
        (user_db_id, code)
    )
    if cur.fetchone():
        conn.close()
        return False, "❌ Ви вже активували цей промокод."

    cur.execute("UPDATE promocodes SET used_count=used_count+1 WHERE code=?", (code,))

    # Прив'язуємо файли промокоду до юзера
    promo_file_ids = get_promo_files(code)
    for fid in promo_file_ids:
        cur.execute(
            "INSERT OR IGNORE INTO user_promo_files (user_id, file_id, promo_code) VALUES (?,?,?)",
            (user_db_id, fid, code)
        )

    conn.commit()
    conn.close()

    promo_name = row["name"] or code
    file_count = len(promo_file_ids)

    if file_count > 0:
        return True, (
            f"✅ Промокод <b>{promo_name}</b> активовано!\n"
            f"📦 Отримано доступ до {file_count} файл(ів)."
        )
    return True, f"✅ Промокод <b>{promo_name}</b> активовано!"


# ── COLLECTIONS ───────────────────────────────────────────────────────────────

def create_collection(name: str, description: str, author_id: int) -> int:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO collections (name, description, author_id) VALUES (?,?,?)",
        (name, description, author_id)
    )
    cid = cur.lastrowid
    conn.commit()
    conn.close()
    return cid


def add_file_to_collection(collection_id: int, file_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO collection_files (collection_id, file_id) VALUES (?,?)",
        (collection_id, file_id)
    )
    conn.commit()
    conn.close()


def get_user_collections(author_id: int) -> list:
    """Повертає список збірок користувача."""
    conn = get_connection()
    cur  = conn.cursor()
    # БАГ БУВ: SELECT з неіснуючою колонкою file_count — виправлено
    cur.execute(
        "SELECT * FROM collections WHERE author_id=? ORDER BY created_at DESC",
        (author_id,)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_collection_files(collection_id: int) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT f.*, c.name AS cat_name, s.name AS sub_name
        FROM files f
        JOIN collection_files cf ON f.id = cf.file_id
        LEFT JOIN categories    c ON f.category_id    = c.id
        LEFT JOIN subcategories s ON f.subcategory_id = s.id
        WHERE cf.collection_id=?
    """, (collection_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ── ACTION LOGS ───────────────────────────────────────────────────────────────

def log_action(user_id: int, action: str, details: str = ""):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO action_logs (user_id, action, details) VALUES (?,?,?)",
        (user_id, action, details)
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 50) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT al.*, u.username, u.first_name
        FROM action_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ── EXPORT ────────────────────────────────────────────────────────────────────

def export_db_json() -> str:
    conn = get_connection()
    cur  = conn.cursor()
    data = {}
    for tbl in ["users", "categories", "subcategories", "files",
                "downloads_log", "bans", "promocodes", "promo_files"]:
        cur.execute(f"SELECT * FROM {tbl}")
        data[tbl] = [dict(r) for r in cur.fetchall()]
    conn.close()
    return json.dumps(data, ensure_ascii=False, indent=2)
