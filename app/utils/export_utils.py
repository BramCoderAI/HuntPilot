import json
import os
from dataclasses import asdict
from typing import Any


def ensure_parent_directory(file_path: str) -> None:
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_text_file(file_path: str, content: str) -> None:
    ensure_parent_directory(file_path)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def write_json_file(file_path: str, data: Any) -> None:
    ensure_parent_directory(file_path)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def dataclass_to_dict(obj: Any) -> Any:
    try:
        return asdict(obj)
    except TypeError:
        return obj