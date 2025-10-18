import re
from typing import Optional, Tuple


def validate_group_link(link: str) -> Tuple[bool, Optional[str]]:
    link = link.strip()

    if link.startswith('@'):
        username = link[1:]
        if re.match(r'^[a-zA-Z0-9_]{5,32}$', username):
            return True, username
        return False, None

    patterns = [
        r't\.me/([a-zA-Z0-9_]{5,32})',
        r'https?://t\.me/([a-zA-Z0-9_]{5,32})',
        r'telegram\.me/([a-zA-Z0-9_]{5,32})',
        r'https?://telegram\.me/([a-zA-Z0-9_]{5,32})'
    ]

    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            username = match.group(1)
            if not username.endswith('bot'):
                return True, username

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
