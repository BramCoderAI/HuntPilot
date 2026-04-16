from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HistoryEntry:
    entry_id: str
    created_at: str
    updated_at: str
    request_raw: str
    response_raw: str
    request_method: str
    request_path: str
    response_status: Optional[int]
    overall_risk: str
    top_issue_titles: List[str] = field(default_factory=list)
    is_favorite: bool = False
    analyst_note: str = ""
    tags: List[str] = field(default_factory=list)
    suggested_tags: List[str] = field(default_factory=list)
    hit_count: int = 1
    extraction_data: Optional[Dict[str, Any]] = None
    scored_analysis_data: Optional[Dict[str, Any]] = None
    ai_suggestion_data: Optional[Dict[str, Any]] = None