# utils/cache.py — простий in-memory кеш для популярних запитів

import time
from typing import Any

# Структура: ключ → (значення, час_закінчення)
_cache: dict[str, tuple[Any, float]] = {}

DEFAULT_TTL = 60  # секунд


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL):
    """Зберегти значення у кеш."""
    _cache[key] = (value, time.time() + ttl)


def cache_get(key: str) -> Any | None:
    """Отримати значення з кешу. Повертає None якщо протермінований або відсутній."""
    entry = _cache.get(key)
    if not entry:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        del _cache[key]
        return None
    return value


def cache_delete(key: str):
    """Видалити ключ з кешу."""
    _cache.pop(key, None)


def cache_clear():
    """Очистити весь кеш."""
    _cache.clear()
