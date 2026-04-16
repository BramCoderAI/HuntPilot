from app.core.history_manager import HistoryManager
from app.core.project_manager import ProjectManager
from app.models.project_dashboard_models import ProjectDashboardData, ProjectDashboardItem


class ProjectDashboardManager:
    def __init__(self):
        self.project_manager = ProjectManager()

    def build_global_dashboard(self) -> ProjectDashboardData:
        projects = self.project_manager.list_projects()
        dashboard_items: list[ProjectDashboardItem] = []

        total_entries = 0
        total_favorites = 0
        total_notes = 0
        total_high = 0
        total_medium = 0
        total_low = 0

        for project in projects:
            history_file_path = self.project_manager.get_history_file_path(project.folder_name)
            history_manager = HistoryManager(file_path=history_file_path)
            entries = history_manager.get_entries()

            favorites_count = sum(1 for entry in entries if entry.is_favorite)
            notes_count = sum(1 for entry in entries if entry.analyst_note.strip())
            repeated_count = sum(1 for entry in entries if entry.hit_count > 1)
            high_count = sum(1 for entry in entries if entry.overall_risk.lower() == "high")
            medium_count = sum(1 for entry in entries if entry.overall_risk.lower() == "medium")
            low_count = sum(1 for entry in entries if entry.overall_risk.lower() == "low")

            total_entries += len(entries)
            total_favorites += favorites_count
            total_notes += notes_count
            total_high += high_count
            total_medium += medium_count
            total_low += low_count

            dashboard_items.append(
                ProjectDashboardItem(
                    project_name=project.name,
                    folder_name=project.folder_name,
                    updated_at=project.updated_at,
                    total_entries=len(entries),
                    favorites_count=favorites_count,
                    notes_count=notes_count,
                    repeated_count=repeated_count,
                    high_count=high_count,
                    medium_count=medium_count,
                    low_count=low_count,
                )
            )

        dashboard_items.sort(key=lambda item: item.updated_at, reverse=True)

        return ProjectDashboardData(
            total_projects=len(projects),
            total_entries=total_entries,
            total_favorites=total_favorites,
            total_notes=total_notes,
            total_high=total_high,
            total_medium=total_medium,
            total_low=total_low,
            projects=dashboard_items,
        )