from PyQt6.QtWidgets import QMessageBox


def confirm_delete_project(parent, project_name: str) -> bool:
    result = QMessageBox.question(
        parent,
        "Delete Project",
        f"Are you sure you want to delete the project '{project_name}'?\n\nThis will remove its history, favorites, notes, and exports.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes