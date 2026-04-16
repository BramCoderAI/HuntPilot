from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout


class ProjectNameDialog(QDialog):
    def __init__(self, title: str, label_text: str, initial_value: str = "", parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)

        self.label = QLabel(label_text)
        self.line_edit = QLineEdit()
        self.line_edit.setText(initial_value)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_value(self) -> str:
        return self.line_edit.text().strip()