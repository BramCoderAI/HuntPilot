from dataclasses import dataclass, field
from typing import List


@dataclass
class DashboardMetric:
    label: str
    value: str


@dataclass
class DashboardCountItem:
    name: str
    count: int


@dataclass
class DashboardRecentItem:
    updated_at: str
    method: str
    path: str
    response_status: str
    overall_risk: str
    top_issue: str
    tags: List[str] = field(default_factory=list)


@dataclass
class DashboardData:
    metrics: List[DashboardMetric] = field(default_factory=list)
    risk_counts: List[DashboardCountItem] = field(default_factory=list)
    status_counts: List[DashboardCountItem] = field(default_factory=list)
    endpoint_counts: List[DashboardCountItem] = field(default_factory=list)
    issue_counts: List[DashboardCountItem] = field(default_factory=list)
    tag_counts: List[DashboardCountItem] = field(default_factory=list)
    recent_items: List[DashboardRecentItem] = field(default_factory=list)