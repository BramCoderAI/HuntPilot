import sys

from PyQt6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.ui.project_selector_window import ProjectSelectorWindow


class HuntPilotApp:
    def __init__(self):
        self.project_selector = None
        self.main_window = None

    def show_project_selector(self):
        if self.main_window is not None:
            self.main_window.close()
            self.main_window = None

        if self.project_selector is None:
            self.project_selector = ProjectSelectorWindow()
            self.project_selector.project_open_requested.connect(self.open_project)
        else:
            self.project_selector.refresh_projects()

        self.project_selector.show()
        self.project_selector.raise_()
        self.project_selector.activateWindow()

    def open_project(self, project_info):
        if self.main_window is not None:
            self.main_window.close()

        self.main_window = MainWindow(project_info)
        self.main_window.back_to_project_selector_requested.connect(self.show_project_selector)
        self.main_window.show()

        if self.project_selector is not None:
            self.project_selector.hide()

    def run(self):
        self.show_project_selector()


def main():
    app = QApplication(sys.argv)

    huntpilot_app = HuntPilotApp()
    huntpilot_app.run()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()