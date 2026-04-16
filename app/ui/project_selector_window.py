from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.project_dashboard_manager import ProjectDashboardManager
from app.core.project_manager import ProjectManager
from app.models.project_models import ProjectInfo
from app.ui.dialogs.confirm_dialog import confirm_delete_project
from app.ui.dialogs.project_name_dialog import ProjectNameDialog
from app.ui.panels.project_dashboard_panel import ProjectDashboardPanel


class ProjectSelectorWindow(QWidget):
    project_open_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("HuntPilot - Project Selector")
        self.resize(900, 700)

        self.project_manager = ProjectManager()
        self.project_dashboard_manager = ProjectDashboardManager()
        self.projects: list[ProjectInfo] = []

        self.title = QLabel("Bug Bounty Projects")
        self.project_list = QListWidget()
        self.global_dashboard_panel = ProjectDashboardPanel()

        self.open_button = QPushButton("Open Project")
        self.create_button = QPushButton("Create Project")
        self.rename_button = QPushButton("Rename Project")
        self.delete_button = QPushButton("Delete Project")
        self.refresh_button = QPushButton("Refresh")

        self.open_button.clicked.connect(self.open_selected_project)
        self.create_button.clicked.connect(self.create_project)
        self.rename_button.clicked.connect(self.rename_project)
        self.delete_button.clicked.connect(self.delete_project)
        self.refresh_button.clicked.connect(self.refresh_projects)
        self.project_list.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.project_list)
        layout.addWidget(self.open_button)
        layout.addWidget(self.create_button)
        layout.addWidget(self.rename_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.global_dashboard_panel)

        self.setLayout(layout)

        self.refresh_projects()

    def refresh_projects(self):
        self.projects = self.project_manager.list_projects()
        self.project_list.clear()

        for project in self.projects:
            item_text = (
                f"{project.name} "
                f"({project.folder_name}) "
                f"| updated: {project.updated_at}"
            )
            item = QListWidgetItem(item_text)
            item.setData(256, project.folder_name)
            self.project_list.addItem(item)

        global_dashboard = self.project_dashboard_manager.build_global_dashboard()
        self.global_dashboard_panel.display_dashboard(global_dashboard)

    def get_selected_project(self) -> ProjectInfo | None:
        item = self.project_list.currentItem()
        if item is None:
            return None

        folder_name = item.data(256)
        for project in self.projects:
            if project.folder_name == folder_name:
                return project

        return None

    def open_selected_project(self):
        project = self.get_selected_project()
        if project is None:
            QMessageBox.information(self, "Open Project", "Select a project first.")
            return

        self.project_manager.touch_project(project.folder_name)
        refreshed = self._reload_project(project.folder_name)
        if refreshed is not None:
            self.project_open_requested.emit(refreshed)

    def create_project(self):
        dialog = ProjectNameDialog(
            title="Create Project",
            label_text="Project name / target name:",
            parent=self,
        )
        if dialog.exec() == dialog.DialogCode.Accepted:
            name = dialog.get_value()
            if not name:
                QMessageBox.warning(self, "Create Project", "Project name cannot be empty.")
                return

            try:
                project = self.project_manager.create_project(name)
                self.refresh_projects()
                self.project_open_requested.emit(project)
            except Exception as exc:
                QMessageBox.critical(self, "Create Project", str(exc))

    def rename_project(self):
        project = self.get_selected_project()
        if project is None:
            QMessageBox.information(self, "Rename Project", "Select a project first.")
            return

        dialog = ProjectNameDialog(
            title="Rename Project",
            label_text="New project name:",
            initial_value=project.name,
            parent=self,
        )
        if dialog.exec() == dialog.DialogCode.Accepted:
            new_name = dialog.get_value()
            if not new_name:
                QMessageBox.warning(self, "Rename Project", "Project name cannot be empty.")
                return

            try:
                updated_project = self.project_manager.rename_project(project.folder_name, new_name)
                self.refresh_projects()
                self.project_open_requested.emit(updated_project)
            except Exception as exc:
                QMessageBox.critical(self, "Rename Project", str(exc))

    def delete_project(self):
        project = self.get_selected_project()
        if project is None:
            QMessageBox.information(self, "Delete Project", "Select a project first.")
            return

        if not confirm_delete_project(self, project.name):
            return

        try:
            self.project_manager.delete_project(project.folder_name)
            self.refresh_projects()
        except Exception as exc:
            QMessageBox.critical(self, "Delete Project", str(exc))

    def _on_item_double_clicked(self, item):
        self.open_selected_project()

    def _reload_project(self, folder_name: str) -> ProjectInfo | None:
        for project in self.project_manager.list_projects():
            if project.folder_name == folder_name:
                return project
        return None