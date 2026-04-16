from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatusPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("Status")
        self.message_label = QLabel("Ready. Load a request or paste one into the input panel.")
        self.message_label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.message_label)
        layout.addStretch()

        self.setLayout(layout)

    def set_message(self, message: str):
        self.message_label.setText(message)