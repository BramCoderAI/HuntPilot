import json
import os

from app.models.ai_models import AISettings


def ensure_parent_directory(file_path: str) -> None:
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def save_ai_settings(file_path: str, settings: AISettings) -> None:
    ensure_parent_directory(file_path)

    data = {
        "mode": settings.mode,
        "builtin_profile": settings.builtin_profile,
        "ollama_host": settings.ollama_host,
        "ollama_model": settings.ollama_model,
        "auto_suggest_after_analysis": settings.auto_suggest_after_analysis,
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_ai_settings(file_path: str) -> AISettings:
    if not os.path.exists(file_path):
        return AISettings()

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return AISettings(
        mode=data.get("mode", "disabled"),
        builtin_profile=data.get("builtin_profile", "rulepack-small"),
        ollama_host=data.get("ollama_host", "http://localhost:11434"),
        ollama_model=data.get("ollama_model", "qwen3:1.7b"),
        auto_suggest_after_analysis=data.get("auto_suggest_after_analysis", False),
    )