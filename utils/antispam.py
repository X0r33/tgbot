# utils/antispam.py — захист від спаму

import time
from collections import defaultdict, deque
from config import ANTISPAM_MAX_ACTIONS, ANTISPAM_WINDOW

# Словник: telegram_id → черга часових міток дій
_user_actions: dict[int, deque] = defaultdict(deque)


def check_spam(telegram_id: int) -> bool:
    """
    Повертає True якщо користувач спамить (перевищив ліміт дій).
    Повертає False якщо все ок.
    """
    now = time.time()
    actions = _user_actions[telegram_id]

    # Видаляємо застарілі дії поза вікном
    while actions and now - actions[0] > ANTISPAM_WINDOW:
        actions.popleft()

    if len(actions) >= ANTISPAM_MAX_ACTIONS:
        return True  # спам!

    actions.append(now)
    return False


def get_remaining_cooldown(telegram_id: int) -> float:
    """Повертає скільки секунд лишилось до закінчення блокування."""
    now = time.time()
    actions = _user_actions[telegram_id]
    if not actions:
        return 0.0
    oldest = actions[0]
    remaining = ANTISPAM_WINDOW - (now - oldest)
    return max(0.0, remaining)
