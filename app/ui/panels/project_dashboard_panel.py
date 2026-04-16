from PyQt6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from app.models.project_dashboard_models import ProjectDashboardData


class ProjectDashboardPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("Projects Dashboard")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.output)

        self.setLayout(layout)

    def display_dashboard(self, dashboard_data: ProjectDashboardData):
        lines = []

        lines.append("=== Global Projects Dashboard ===")
        lines.append(f"Total Projects: {dashboard_data.total_projects}")
        lines.append(f"Total Entries: {dashboard_data.total_entries}")
        lines.append(f"Total Favorites: {dashboard_data.total_favorites}")
        lines.append(f"Total Notes: {dashboard_data.total_notes}")
        lines.append(f"Total High Risk Entries: {dashboard_data.total_high}")
        lines.append(f"Total Medium Risk Entries: {dashboard_data.total_medium}")
        lines.append(f"Total Low Risk Entries: {dashboard_data.total_low}")
        lines.append("")

        lines.append("=== Projects ===")
        if dashboard_data.projects:
            for project in dashboard_data.projects:
                lines.append(
                    f"- {project.project_name} ({project.folder_name}) | "
                    f"updated: {project.updated_at} | "
                    f"entries: {project.total_entries} | "
                    f"favorites: {project.favorites_count} | "
                    f"notes: {project.notes_count} | "
                    f"repeated: {project.repeated_count} | "
                    f"high: {project.high_count} | medium: {project.medium_count} | low: {project.low_count}"
                )
        else:
            lines.append("No projects found.")

        self.output.setPlainText("\n".join(lines))

    def clear(self):
        self.output.clear()