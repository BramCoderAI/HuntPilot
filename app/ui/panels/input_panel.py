from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config import DEFAULT_SAMPLE_REQUEST, DEFAULT_SAMPLE_RESPONSE


class InputPanel(QWidget):
    analyze_clicked = pyqtSignal(str, str)
    clear_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.request_label = QLabel("Raw HTTP Request")
        self.request_text_edit = QTextEdit()

        self.response_label = QLabel("Raw HTTP Response")
        self.response_text_edit = QTextEdit()

        self.load_request_button = QPushButton("Load Request From File")
        self.load_response_button = QPushButton("Load Response From File")
        self.load_sample_button = QPushButton("Load Sample")
        self.clear_button = QPushButton("Clear")
        self.analyze_button = QPushButton("Analyze")

        self.load_request_button.clicked.connect(self.load_request_from_file)
        self.load_response_button.clicked.connect(self.load_response_from_file)
        self.load_sample_button.clicked.connect(self.load_sample)
        self.clear_button.clicked.connect(self.clear_text)
        self.analyze_button.clicked.connect(self.on_click)

        button_row = QHBoxLayout()
        button_row.addWidget(self.load_request_button)
        button_row.addWidget(self.load_response_button)
        button_row.addWidget(self.load_sample_button)
        button_row.addWidget(self.clear_button)
        button_row.addWidget(self.analyze_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.request_label)
        main_layout.addWidget(self.request_text_edit)
        main_layout.addWidget(self.response_label)
        main_layout.addWidget(self.response_text_edit)
        main_layout.addLayout(button_row)

        self.setLayout(main_layout)

    def on_click(self):
        request_text = self.request_text_edit.toPlainText()
        response_text = self.response_text_edit.toPlainText()
        self.analyze_clicked.emit(request_text, response_text)

    def clear_text(self):
        self.request_text_edit.clear()
        self.response_text_edit.clear()
        self.clear_clicked.emit()

    def load_sample(self):
        self.request_text_edit.setPlainText(DEFAULT_SAMPLE_REQUEST)
        self.response_text_edit.setPlainText(DEFAULT_SAMPLE_RESPONSE)

    def load_request_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open HTTP Request File",
            "",
            "Text Files (*.txt *.http *.req);;All Files (*)",
        )

        if not file_path:
            return

        self.request_text_edit.setPlainText(self._read_text_file(file_path))

    def load_response_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open HTTP Response File",
            "",
            "Text Files (*.txt *.http *.resp);;All Files (*)",
        )

        if not file_path:
            return

        self.response_text_edit.setPlainText(self._read_text_file(file_path))

    def _read_text_file(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as file:
                return file.read()

    def set_exchange_text(self, request_text: str, response_text: str):
        self.request_text_edit.setPlainText(request_text)
        self.response_text_edit.setPlainText(response_text)

    def get_request_text(self) -> str:
        return self.request_text_edit.toPlainText()

    def get_response_text(self) -> str:
        return self.response_text_edit.toPlainText()