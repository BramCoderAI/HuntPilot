from dataclasses import dataclass, field
from typing import List


@dataclass
class ProjectDashboardItem:
    project_name: str
    folder_name: str
    updated_at: str
    total_entries: int
    favorites_count: int
    notes_count: int
    repeated_count: int
    high_count: int
    medium_count: int
    low_count: int


@dataclass
class ProjectDashboardData:
    total_projects: int = 0
    total_entries: int = 0
    total_favorites: int = 0
    total_notes: int = 0
    total_high: int = 0
    total_medium: int = 0
    total_low: int = 0
    projects: List[ProjectDashboardItem] = field(default_factory=list)