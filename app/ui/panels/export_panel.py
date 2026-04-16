from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ExportPanel(QWidget):
    export_current_txt_clicked = pyqtSignal()
    export_current_json_clicked = pyqtSignal()
    export_history_json_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.title = QLabel("Export")

        self.export_current_txt_button = QPushButton("Export Current Analysis (.txt)")
        self.export_current_json_button = QPushButton("Export Current Analysis (.json)")
        self.export_history_json_button = QPushButton("Export History (.json)")

        self.export_current_txt_button.clicked.connect(self.export_current_txt_clicked.emit)
        self.export_current_json_button.clicked.connect(self.export_current_json_clicked.emit)
        self.export_history_json_button.clicked.connect(self.export_history_json_clicked.emit)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.export_current_txt_button)
        layout.addWidget(self.export_current_json_button)
        layout.addWidget(self.export_history_json_button)
        layout.addStretch()

        self.setLayout(layout)