import json
import os
import re
import shutil
from dataclasses import asdict

from app.models.project_models import ProjectInfo


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def slugify_project_name(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^\w\s\.-]", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value)
    value = value.strip("._-")
    return value or "project"


def read_json_file(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json_file(file_path: str, data: dict) -> None:
    ensure_directory(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def save_project_info(project_file_path: str, project_info: ProjectInfo) -> None:
    write_json_file(project_file_path, asdict(project_info))


def load_project_info(project_file_path: str) -> ProjectInfo:
    data = read_json_file(project_file_path)
    return ProjectInfo(
        name=data.get("name", ""),
        folder_name=data.get("folder_name", ""),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


def delete_directory(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)