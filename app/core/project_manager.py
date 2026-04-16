import os
from datetime import datetime
from typing import List

from app.config import PROJECTS_ROOT_DIR
from app.models.project_models import ProjectInfo
from app.utils.project_utils import (
    delete_directory,
    ensure_directory,
    load_project_info,
    save_project_info,
    slugify_project_name,
)


class ProjectManager:
    def __init__(self, projects_root: str = PROJECTS_ROOT_DIR):
        self.projects_root = projects_root
        ensure_directory(self.projects_root)

    def list_projects(self) -> List[ProjectInfo]:
        projects: List[ProjectInfo] = []

        for entry_name in os.listdir(self.projects_root):
            project_dir = os.path.join(self.projects_root, entry_name)
            project_file = os.path.join(project_dir, "project.json")

            if not os.path.isdir(project_dir):
                continue

            if not os.path.exists(project_file):
                continue

            try:
                project_info = load_project_info(project_file)
                projects.append(project_info)
            except Exception:
                continue

        projects.sort(key=lambda item: item.updated_at, reverse=True)
        return projects

    def create_project(self, display_name: str) -> ProjectInfo:
        display_name = display_name.strip()
        if not display_name:
            raise ValueError("Project name cannot be empty.")

        base_folder_name = slugify_project_name(display_name)
        folder_name = self._make_unique_folder_name(base_folder_name)

        now = datetime.now().isoformat(timespec="seconds")
        project_info = ProjectInfo(
            name=display_name,
            folder_name=folder_name,
            created_at=now,
            updated_at=now,
        )

        project_dir = self.get_project_dir(folder_name)
        ensure_directory(project_dir)
        ensure_directory(os.path.join(project_dir, "history"))
        ensure_directory(os.path.join(project_dir, "exports"))
        ensure_directory(os.path.join(project_dir, "config"))

        project_file = os.path.join(project_dir, "project.json")
        save_project_info(project_file, project_info)

        history_file = os.path.join(project_dir, "history", "history.json")
        if not os.path.exists(history_file):
            with open(history_file, "w", encoding="utf-8") as file:
                file.write("[]")

        return project_info

    def rename_project(self, old_folder_name: str, new_display_name: str) -> ProjectInfo:
        new_display_name = new_display_name.strip()
        if not new_display_name:
            raise ValueError("Project name cannot be empty.")

        old_project_dir = self.get_project_dir(old_folder_name)
        old_project_file = os.path.join(old_project_dir, "project.json")

        if not os.path.exists(old_project_file):
            raise FileNotFoundError("Project does not exist.")

        old_project = load_project_info(old_project_file)

        base_new_folder_name = slugify_project_name(new_display_name)
        new_folder_name = base_new_folder_name

        if base_new_folder_name != old_folder_name:
            new_folder_name = self._make_unique_folder_name(base_new_folder_name)

        new_project_dir = self.get_project_dir(new_folder_name)

        if old_project_dir != new_project_dir:
            os.rename(old_project_dir, new_project_dir)

        updated_at = datetime.now().isoformat(timespec="seconds")
        updated_project = ProjectInfo(
            name=new_display_name,
            folder_name=new_folder_name,
            created_at=old_project.created_at,
            updated_at=updated_at,
        )

        new_project_file = os.path.join(new_project_dir, "project.json")
        save_project_info(new_project_file, updated_project)

        return updated_project

    def delete_project(self, folder_name: str) -> None:
        project_dir = self.get_project_dir(folder_name)
        delete_directory(project_dir)

    def touch_project(self, folder_name: str) -> None:
        project_dir = self.get_project_dir(folder_name)
        project_file = os.path.join(project_dir, "project.json")

        if not os.path.exists(project_file):
            return

        project = load_project_info(project_file)
        updated_project = ProjectInfo(
            name=project.name,
            folder_name=project.folder_name,
            created_at=project.created_at,
            updated_at=datetime.now().isoformat(timespec="seconds"),
        )
        save_project_info(project_file, updated_project)

    def get_project_dir(self, folder_name: str) -> str:
        return os.path.join(self.projects_root, folder_name)

    def get_history_file_path(self, folder_name: str) -> str:
        return os.path.join(self.get_project_dir(folder_name), "history", "history.json")

    def get_exports_dir(self, folder_name: str) -> str:
        return os.path.join(self.get_project_dir(folder_name), "exports")

    def get_ai_settings_file_path(self, folder_name: str) -> str:
        return os.path.join(self.get_project_dir(folder_name), "config", "ai_settings.json")

    def _make_unique_folder_name(self, base_name: str) -> str:
        candidate = base_name
        index = 2

        while os.path.exists(self.get_project_dir(candidate)):
            candidate = f"{base_name}_{index}"
            index += 1

        return candidate