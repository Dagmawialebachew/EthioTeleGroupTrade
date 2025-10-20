import re
from typing import Optional, Tuple
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Chat
# Telegram usernames: 5–32 chars, letters, digits, underscores
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{5,32}$')


def validate_group_link(link: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Telegram group link or @username (string-level only).
    Returns (True, normalized_username) if valid, else (False, None).
    Normalized username is returned WITHOUT the '@'.
    """
    if not link:
        return False, None

    link = link.strip()

    # Case 1: @username
    if link.startswith('@'):
        username = link[1:]
        if USERNAME_PATTERN.fullmatch(username):
             return True, username
        return False, None

    # Case 2: t.me / telegram.me links
    patterns = [
        r'^(?:https?://)?t\.me/([a-zA-Z0-9_]{5,32})$',
        r'^(?:https?://)?telegram\.me/([a-zA-Z0-9_]{5,32})$'
    ]

    for pattern in patterns:
        match = re.match(pattern, link)
        if match:
            username = match.group(1)
            if USERNAME_PATTERN.fullmatch(username):
                return True, username

    return False, None


async def resolve_group(bot: Bot, username: str) -> Tuple[bool, Optional[Chat]]:
    """
    Confirm via Telegram API that the username belongs to a group/supergroup.
    Expects a normalized username (without '@').
    Returns (True, Chat) if valid group, else (False, None).
    """
    try:
        chat = await bot.get_chat(f"@{username}")
        if chat.type in ["group", "supergroup"]:
            return True, chat
        return False, None
    except (TelegramBadRequest, TelegramForbiddenError):
        return False, None

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    username = username.strip()

    if not username.startswith('@'):
        return False, None

    username_part = username[1:]

    if re.match(r'^[a-zA-Z0-9_]{5,32}$', username_part):
        return True, username

    return False, None


def validate_image(file_size: int, mime_type: str) -> bool:
    max_size = 5 * 1024 * 1024
    valid_types = ['image/jpeg', 'image/png', 'image/jpg']

    if file_size > max_size:
        return False

    if mime_type not in valid_types:
        return False

    return True
