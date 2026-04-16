import json
import os
from dataclasses import asdict
from typing import List

from app.models.history_models import HistoryEntry


def ensure_parent_directory(file_path: str) -> None:
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def save_history_entries(file_path: str, entries: List[HistoryEntry]) -> None:
    ensure_parent_directory(file_path)

    data = [asdict(entry) for entry in entries]

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_history_entries(file_path: str) -> List[HistoryEntry]:
    if not os.path.exists(file_path):
        return []

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    entries: List[HistoryEntry] = []
    for item in data:
        created_at = item.get("created_at", "")
        updated_at = item.get("updated_at", created_at)

        entries.append(
            HistoryEntry(
                entry_id=item.get("entry_id", ""),
                created_at=created_at,
                updated_at=updated_at,
                request_raw=item.get("request_raw", ""),
                response_raw=item.get("response_raw", ""),
                request_method=item.get("request_method", ""),
                request_path=item.get("request_path", ""),
                response_status=item.get("response_status"),
                overall_risk=item.get("overall_risk", "low"),
                top_issue_titles=item.get("top_issue_titles", []),
                is_favorite=item.get("is_favorite", False),
                analyst_note=item.get("analyst_note", ""),
                tags=item.get("tags", []),
                suggested_tags=item.get("suggested_tags", []),
                hit_count=item.get("hit_count", 1),
                extraction_data=item.get("extraction_data"),
                scored_analysis_data=item.get("scored_analysis_data"),
                ai_suggestion_data=item.get("ai_suggestion_data"),
            )
        )

    return entries