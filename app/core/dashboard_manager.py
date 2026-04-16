from collections import Counter

from app.models.dashboard_models import (
    DashboardCountItem,
    DashboardData,
    DashboardMetric,
    DashboardRecentItem,
)
from app.models.history_models import HistoryEntry


class DashboardManager:
    def build_dashboard_data(self, entries: list[HistoryEntry]) -> DashboardData:
        total_analyses = len(entries)
        total_favorites = sum(1 for entry in entries if entry.is_favorite)
        unique_paths = len({entry.request_path for entry in entries if entry.request_path})
        duplicated_entries = sum(1 for entry in entries if entry.hit_count > 1)
        notes_count = sum(1 for entry in entries if entry.analyst_note.strip())
        tagged_entries = sum(1 for entry in entries if entry.tags)

        risk_counter = Counter(entry.overall_risk.lower() for entry in entries if entry.overall_risk)
        status_counter = Counter(
            str(entry.response_status) if entry.response_status is not None else "NoResp"
            for entry in entries
        )
        endpoint_counter = Counter(entry.request_path for entry in entries if entry.request_path)
        issue_counter = Counter()
        tag_counter = Counter()

        for entry in entries:
            for issue in entry.top_issue_titles:
                if issue:
                    issue_counter[issue] += 1

            for tag in entry.tags:
                normalized_tag = tag.strip()
                if normalized_tag:
                    tag_counter[normalized_tag] += 1

        metrics = [
            DashboardMetric(label="Total Analyses", value=str(total_analyses)),
            DashboardMetric(label="Favorites", value=str(total_favorites)),
            DashboardMetric(label="Unique Paths", value=str(unique_paths)),
            DashboardMetric(label="Entries With Notes", value=str(notes_count)),
            DashboardMetric(label="Tagged Entries", value=str(tagged_entries)),
            DashboardMetric(label="Repeated Entries", value=str(duplicated_entries)),
        ]

        risk_counts = self._counter_to_items(
            risk_counter,
            preferred_order=["high", "medium", "low"],
        )
        status_counts = self._counter_to_items(status_counter)
        endpoint_counts = self._counter_to_items(endpoint_counter)
        issue_counts = self._counter_to_items(issue_counter)
        tag_counts = self._counter_to_items(tag_counter)

        recent_items = [
            DashboardRecentItem(
                updated_at=entry.updated_at,
                method=entry.request_method or "UNK",
                path=entry.request_path or "/",
                response_status=str(entry.response_status) if entry.response_status is not None else "NoResp",
                overall_risk=entry.overall_risk.upper(),
                top_issue=entry.top_issue_titles[0] if entry.top_issue_titles else "No lead",
                tags=list(entry.tags),
            )
            for entry in entries[:10]
        ]

        return DashboardData(
            metrics=metrics,
            risk_counts=risk_counts,
            status_counts=status_counts[:10],
            endpoint_counts=endpoint_counts[:10],
            issue_counts=issue_counts[:10],
            tag_counts=tag_counts[:15],
            recent_items=recent_items,
        )

    def _counter_to_items(
        self,
        counter: Counter,
        preferred_order: list[str] | None = None,
    ) -> list[DashboardCountItem]:
        items = [DashboardCountItem(name=name, count=count) for name, count in counter.items()]

        if preferred_order:
            order_map = {name: index for index, name in enumerate(preferred_order)}
            items.sort(
                key=lambda item: (
                    order_map.get(item.name.lower(), 999),
                    -item.count,
                    item.name.lower(),
                )
            )
        else:
            items.sort(key=lambda item: (-item.count, item.name.lower()))

        return items