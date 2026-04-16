from dataclasses import dataclass, field
from typing import List


@dataclass
class ComparisonRow:
    field_name: str
    left_value: str
    right_value: str
    changed: bool


@dataclass
class ComparisonResult:
    left_entry_id: str
    right_entry_id: str
    rows: List[ComparisonRow] = field(default_factory=list)
    summary: str = ""
    request_structured_diffs: List[str] = field(default_factory=list)
    response_structured_diffs: List[str] = field(default_factory=list)
    request_line_diff: str = ""
    response_line_diff: str = ""