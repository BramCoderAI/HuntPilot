import re
from typing import Dict


def parse_cookie_header(cookie_header: str) -> Dict[str, str]:
    cookies: Dict[str, str] = {}

    if not cookie_header:
        return cookies

    parts = cookie_header.split(";")
    for part in parts:
        part = part.strip()
        if not part or "=" not in part:
            continue

        key, value = part.split("=", 1)
        cookies[key.strip()] = value.strip()

    return cookies


def looks_like_numeric_id(value: str) -> bool:
    return bool(re.fullmatch(r"\d{1,20}", value.strip()))


def looks_like_uuid(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"[0-9a-fA-F]{8}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{12}",
            value.strip(),
        )
    )