from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.models.analysis_models import ExtractionResult, ScoredAnalysisResult
from app.models.ai_models import AISuggestionResult
from app.models.history_models import HistoryEntry
from app.models.http_models import HTTPRequest, HTTPResponse
from app.utils.ai_serialization import ai_suggestion_result_to_dict
from app.utils.analysis_serialization import (
    extraction_result_to_dict,
    scored_analysis_result_to_dict,
)
from app.utils.history_utils import load_history_entries, save_history_entries


class HistoryManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.entries: List[HistoryEntry] = load_history_entries(self.file_path)

    def get_entries(self) -> List[HistoryEntry]:
        return list(self.entries)

    def get_entry_by_id(self, entry_id: str) -> Optional[HistoryEntry]:
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    def add_entry(
        self,
        request: HTTPRequest,
        response: Optional[HTTPResponse],
        extraction_result: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        request_raw: str,
        response_raw: str,
        suggested_tags: list[str],
        ai_result: AISuggestionResult | None = None,
    ) -> HistoryEntry:
        existing_entry = self._find_duplicate_entry(
            request=request,
            response=response,
            request_raw=request_raw,
            response_raw=response_raw,
        )

        now = datetime.now().isoformat(timespec="seconds")
        extraction_data = extraction_result_to_dict(extraction_result)
        scored_analysis_data = scored_analysis_result_to_dict(scored_result)
        ai_suggestion_data = ai_suggestion_result_to_dict(ai_result)

        if existing_entry is not None:
            existing_entry.updated_at = now
            existing_entry.request_method = request.method
            existing_entry.request_path = request.path
            existing_entry.response_status = response.status_code if response is not None else None
            existing_entry.overall_risk = scored_result.summary.overall_risk
            existing_entry.top_issue_titles = scored_result.summary.top_issue_titles[:3]
            existing_entry.hit_count += 1
            existing_entry.extraction_data = extraction_data
            existing_entry.scored_analysis_data = scored_analysis_data
            existing_entry.suggested_tags = suggested_tags
            existing_entry.ai_suggestion_data = ai_suggestion_data

            self._move_entry_to_top(existing_entry.entry_id)
            self.save()
            return existing_entry

        entry = HistoryEntry(
            entry_id=str(uuid4()),
            created_at=now,
            updated_at=now,
            request_raw=request_raw,
            response_raw=response_raw,
            request_method=request.method,
            request_path=request.path,
            response_status=response.status_code if response is not None else None,
            overall_risk=scored_result.summary.overall_risk,
            top_issue_titles=scored_result.summary.top_issue_titles[:3],
            is_favorite=False,
            analyst_note="",
            tags=[],
            suggested_tags=suggested_tags,
            hit_count=1,
            extraction_data=extraction_data,
            scored_analysis_data=scored_analysis_data,
            ai_suggestion_data=ai_suggestion_data,
        )

        self.entries.insert(0, entry)
        self._trim_entries()
        self.save()

        return entry

    def update_entry_metadata(
        self,
        entry_id: str,
        is_favorite: Optional[bool] = None,
        analyst_note: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Optional[HistoryEntry]:
        entry = self.get_entry_by_id(entry_id)
        if entry is None:
            return None

        if is_favorite is not None:
            entry.is_favorite = is_favorite

        if analyst_note is not None:
            entry.analyst_note = analyst_note

        if tags is not None:
            entry.tags = tags

        self.save()
        return entry

    def update_entry_ai_result(
        self,
        entry_id: str,
        ai_result: AISuggestionResult | None,
    ) -> Optional[HistoryEntry]:
        entry = self.get_entry_by_id(entry_id)
        if entry is None:
            return None

        entry.ai_suggestion_data = ai_suggestion_result_to_dict(ai_result)
        self.save()
        return entry

    def clear(self) -> None:
        self.entries = []
        self.save()

    def save(self) -> None:
        save_history_entries(self.file_path, self.entries)

    def _trim_entries(self) -> None:
        self.entries = self.entries[:200]

    def _find_duplicate_entry(
        self,
        request: HTTPRequest,
        response: Optional[HTTPResponse],
        request_raw: str,
        response_raw: str,
    ) -> Optional[HistoryEntry]:
        response_status = response.status_code if response is not None else None

        for entry in self.entries:
            if (
                entry.request_method == request.method
                and entry.request_path == request.path
                and entry.response_status == response_status
                and entry.request_raw == request_raw
                and entry.response_raw == response_raw
            ):
                return entry

        return None

    def _move_entry_to_top(self, entry_id: str) -> None:
        for index, entry in enumerate(self.entries):
            if entry.entry_id == entry_id:
                selected_entry = self.entries.pop(index)
                self.entries.insert(0, selected_entry)
                return