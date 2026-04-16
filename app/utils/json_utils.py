import json
from typing import Any, Optional


def try_parse_json(text: str) -> Optional[Any]:
    if not text or not text.strip():
        return None

    try:
        return json.loads(text)
    except Exception:
        return None


def pretty_json(data: Any) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)