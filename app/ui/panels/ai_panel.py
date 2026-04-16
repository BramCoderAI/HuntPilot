from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.ai_models import AIConnectionStatus, AISettings, AISuggestionResult


class AIPanel(QWidget):
    save_settings_clicked = pyqtSignal(object)
    generate_clicked = pyqtSignal()
    copy_install_command_clicked = pyqtSignal(str)
    test_connection_clicked = pyqtSignal()
    pull_model_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.title = QLabel("AI Settings")

        self.mode_label = QLabel("Mode")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["disabled", "builtin", "ollama"])

        self.builtin_profile_label = QLabel("Built-in Profile")
        self.builtin_profile_combo = QComboBox()
        self.builtin_profile_combo.addItems(["rulepack-small", "rulepack-extended"])

        self.ollama_host_label = QLabel("Ollama Host")
        self.ollama_host_input = QLineEdit()
        self.ollama_host_input.setPlaceholderText("http://localhost:11434")

        self.ollama_model_label = QLabel("Ollama Model")
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.setEditable(True)

        self.auto_suggest_checkbox = QCheckBox("Auto generate AI suggestions after analysis")

        self.save_settings_button = QPushButton("Save AI Settings")
        self.test_connection_button = QPushButton("Test AI Connection")
        self.pull_model_button = QPushButton("Pull Selected Ollama Model")
        self.generate_button = QPushButton("Generate AI Suggestions")
        self.copy_install_command_button = QPushButton("Copy Ollama Install + Pull Command")

        self.connection_status_label = QLabel("AI Status")
        self.connection_status_value = QLabel("Not tested.")
        self.connection_status_value.setWordWrap(True)

        self.result_label = QLabel("AI Output")
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)

        self.save_settings_button.clicked.connect(self._on_save_settings_clicked)
        self.test_connection_button.clicked.connect(self.test_connection_clicked.emit)
        self.pull_model_button.clicked.connect(self._on_pull_model_clicked)
        self.generate_button.clicked.connect(self.generate_clicked.emit)
        self.copy_install_command_button.clicked.connect(self._on_copy_install_command_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.builtin_profile_label)
        layout.addWidget(self.builtin_profile_combo)
        layout.addWidget(self.ollama_host_label)
        layout.addWidget(self.ollama_host_input)
        layout.addWidget(self.ollama_model_label)
        layout.addWidget(self.ollama_model_combo)
        layout.addWidget(self.auto_suggest_checkbox)
        layout.addWidget(self.save_settings_button)
        layout.addWidget(self.test_connection_button)
        layout.addWidget(self.pull_model_button)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.copy_install_command_button)
        layout.addWidget(self.connection_status_label)
        layout.addWidget(self.connection_status_value)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_output)

        self.setLayout(layout)

    def set_available_ollama_models(self, models: list[str]):
        current_text = self.ollama_model_combo.currentText().strip()

        self.ollama_model_combo.clear()
        self.ollama_model_combo.addItems(models)

        if current_text:
            self.ollama_model_combo.setCurrentText(current_text)

    def load_settings(self, settings: AISettings):
        self.mode_combo.setCurrentText(settings.mode)
        self.builtin_profile_combo.setCurrentText(settings.builtin_profile)
        self.ollama_host_input.setText(settings.ollama_host)
        self.ollama_model_combo.setCurrentText(settings.ollama_model)
        self.auto_suggest_checkbox.setChecked(settings.auto_suggest_after_analysis)

    def collect_settings(self) -> AISettings:
        return AISettings(
            mode=self.mode_combo.currentText().strip(),
            builtin_profile=self.builtin_profile_combo.currentText().strip(),
            ollama_host=self.ollama_host_input.text().strip() or "http://localhost:11434",
            ollama_model=self.ollama_model_combo.currentText().strip() or "qwen3:1.7b",
            auto_suggest_after_analysis=self.auto_suggest_checkbox.isChecked(),
        )

    def display_result(self, result: AISuggestionResult):
        if result.success:
            title = f"Provider: {result.provider} | Model: {result.model_name}"
            body = result.content or "No content returned."
            self.result_output.setPlainText(f"{title}\n\n{body}")
        else:
            title = f"Provider: {result.provider} | Model: {result.model_name}"
            error = result.error_message or "Unknown AI error."
            self.result_output.setPlainText(f"{title}\n\nError:\n{error}")

    def display_connection_status(self, status: AIConnectionStatus):
        text = f"Provider: {status.provider}\nSuccess: {'Yes' if status.success else 'No'}\nMessage: {status.message}"
        if status.available_models:
            text += "\nAvailable Models:\n- " + "\n- ".join(status.available_models)
        self.connection_status_value.setText(text)

    def clear_output(self):
        self.result_output.clear()

    def _on_save_settings_clicked(self):
        settings = self.collect_settings()
        self.save_settings_clicked.emit(settings)

    def _on_copy_install_command_clicked(self):
        model_name = self.ollama_model_combo.currentText().strip()
        self.copy_install_command_clicked.emit(model_name)

    def _on_pull_model_clicked(self):
        model_name = self.ollama_model_combo.currentText().strip()
        self.pull_model_clicked.emit(model_name)