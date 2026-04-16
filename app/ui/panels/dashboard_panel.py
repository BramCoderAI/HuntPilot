from PyQt6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from app.models.dashboard_models import DashboardData


class DashboardPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("Project Dashboard")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.output)

        self.setLayout(layout)

    def display_dashboard(self, dashboard_data: DashboardData, project_name: str):
        lines = []

        lines.append("=== Project Dashboard ===")
        lines.append(f"Project: {project_name}")
        lines.append("")

        lines.append("=== Metrics ===")
        if dashboard_data.metrics:
            for metric in dashboard_data.metrics:
                lines.append(f"- {metric.label}: {metric.value}")
        else:
            lines.append("No metrics available.")
        lines.append("")

        lines.append("=== Risk Distribution ===")
        lines.extend(self._format_count_items(dashboard_data.risk_counts))
        lines.append("")

        lines.append("=== Most Frequent Status Codes ===")
        lines.extend(self._format_count_items(dashboard_data.status_counts))
        lines.append("")

        lines.append("=== Most Frequent Paths ===")
        lines.extend(self._format_count_items(dashboard_data.endpoint_counts))
        lines.append("")

        lines.append("=== Most Frequent Issue Titles ===")
        lines.extend(self._format_count_items(dashboard_data.issue_counts))
        lines.append("")

        lines.append("=== Most Frequent Tags ===")
        lines.extend(self._format_count_items(dashboard_data.tag_counts))
        lines.append("")

        lines.append("=== Recent Activity ===")
        if dashboard_data.recent_items:
            for item in dashboard_data.recent_items:
                tag_text = ", ".join(item.tags) if item.tags else "no-tags"
                lines.append(
                    f"- [{item.updated_at}] {item.method} {item.path} | "
                    f"{item.response_status} | {item.overall_risk} | {item.top_issue} | tags: {tag_text}"
                )
        else:
            lines.append("No recent activity.")

        self.output.setPlainText("\n".join(lines))

    def clear(self):
        self.output.clear()

    def _format_count_items(self, items):
        if not items:
            return ["No data."]

        lines = []
        for item in items:
            lines.append(f"- {item.name}: {item.count}")
        return lines