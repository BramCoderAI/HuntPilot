from typing import List

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.history_models import HistoryEntry


class HistoryPanel(QWidget):
    entry_selected = pyqtSignal(str)
    clear_history_clicked = pyqtSignal()
    save_metadata_clicked = pyqtSignal(str, bool, str, list)
    filter_changed = pyqtSignal(str, str, bool, str)
    compare_left_clicked = pyqtSignal(str)
    compare_right_clicked = pyqtSignal(str)
    compare_run_clicked = pyqtSignal()
    apply_suggested_tags_clicked = pyqtSignal(str)
    copy_suggested_tags_clicked = pyqtSignal(str)
    quick_add_tag_clicked = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()

        self.current_entry_id = ""
        self.compare_left_entry_id = ""
        self.compare_right_entry_id = ""
        self.current_manual_tags: list[str] = []
        self.current_suggested_tags: list[str] = []

        self.title = QLabel("History")

        self.search_label = QLabel("Search")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by method, path, issue, note, tag...")

        self.risk_filter_label = QLabel("Risk Filter")
        self.risk_filter_combo = QComboBox()
        self.risk_filter_combo.addItems(["all", "high", "medium", "low"])

        self.favorite_filter_checkbox = QCheckBox("Show Favorites Only")

        self.tag_filter_label = QLabel("Tag Filter")
        self.tag_filter_input = QLineEdit()
        self.tag_filter_input.setPlaceholderText("Filter by a single tag...")

        self.list_widget = QListWidget()

        self.favorite_checkbox = QCheckBox("Favorite")
        self.note_label = QLabel("Analyst Note")
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Add your manual note for this history entry...")

        self.tags_label = QLabel("Manual Tags (comma separated)")
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("idor, authz, graphql, retry")

        self.suggested_tags_label = QLabel("Suggested Tags")
        self.suggested_tags_value = QLabel("None")
        self.suggested_tags_value.setWordWrap(True)

        self.apply_suggested_tags_button = QPushButton("Apply Suggested Tags to Manual Tags")
        self.copy_suggested_tags_button = QPushButton("Copy Suggested Tags")
        self.mark_interesting_button = QPushButton("Mark as Interesting")
        self.mark_retest_button = QPushButton("Mark for Retest")

        self.compare_left_label = QLabel("Compare Left: none")
        self.compare_right_label = QLabel("Compare Right: none")
        self.mark_left_button = QPushButton("Use Selected as Left")
        self.mark_right_button = QPushButton("Use Selected as Right")
        self.run_compare_button = QPushButton("Compare Left vs Right")

        self.save_metadata_button = QPushButton("Save Note / Favorite / Tags")
        self.clear_button = QPushButton("Clear History")

        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.save_metadata_button.clicked.connect(self._on_save_metadata_clicked)
        self.clear_button.clicked.connect(self._on_clear_clicked)

        self.search_input.textChanged.connect(self._emit_filter_changed)
        self.risk_filter_combo.currentTextChanged.connect(self._emit_filter_changed)
        self.favorite_filter_checkbox.toggled.connect(self._emit_filter_changed)
        self.tag_filter_input.textChanged.connect(self._emit_filter_changed)

        self.mark_left_button.clicked.connect(self._on_mark_left_clicked)
        self.mark_right_button.clicked.connect(self._on_mark_right_clicked)
        self.run_compare_button.clicked.connect(self.compare_run_clicked.emit)

        self.apply_suggested_tags_button.clicked.connect(self._on_apply_suggested_tags_clicked)
        self.copy_suggested_tags_button.clicked.connect(self._on_copy_suggested_tags_clicked)
        self.mark_interesting_button.clicked.connect(self._on_mark_interesting_clicked)
        self.mark_retest_button.clicked.connect(self._on_mark_retest_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.risk_filter_label)
        layout.addWidget(self.risk_filter_combo)
        layout.addWidget(self.favorite_filter_checkbox)
        layout.addWidget(self.tag_filter_label)
        layout.addWidget(self.tag_filter_input)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.favorite_checkbox)
        layout.addWidget(self.note_label)
        layout.addWidget(self.note_edit)
        layout.addWidget(self.tags_label)
        layout.addWidget(self.tags_input)
        layout.addWidget(self.suggested_tags_label)
        layout.addWidget(self.suggested_tags_value)
        layout.addWidget(self.apply_suggested_tags_button)
        layout.addWidget(self.copy_suggested_tags_button)
        layout.addWidget(self.mark_interesting_button)
        layout.addWidget(self.mark_retest_button)
        layout.addWidget(self.compare_left_label)
        layout.addWidget(self.compare_right_label)
        layout.addWidget(self.mark_left_button)
        layout.addWidget(self.mark_right_button)
        layout.addWidget(self.run_compare_button)
        layout.addWidget(self.save_metadata_button)
        layout.addWidget(self.clear_button)

        self.setLayout(layout)

    def set_entries(self, entries: List[HistoryEntry]):
        self.list_widget.clear()

        for entry in entries:
            star = "★ " if entry.is_favorite else ""
            response_part = str(entry.response_status) if entry.response_status is not None else "NoResp"
            top_issue = entry.top_issue_titles[0] if entry.top_issue_titles else "No lead"
            hit_count_part = f"x{entry.hit_count}" if entry.hit_count > 1 else "x1"

            merged_tags = self._merge_tags(entry.tags, entry.suggested_tags)
            tag_part = f" | tags: {', '.join(merged_tags)}" if merged_tags else ""

            label = (
                f"{star}[{entry.updated_at}] "
                f"{entry.request_method or 'UNK'} "
                f"{entry.request_path or '/'} "
                f"| {response_part} | {entry.overall_risk.upper()} | {hit_count_part} | {top_issue}{tag_part}"
            )

            item = QListWidgetItem(label)
            item.setData(256, entry.entry_id)
            self.list_widget.addItem(item)

    def load_entry_metadata(self, entry: HistoryEntry):
        self.current_entry_id = entry.entry_id
        self.current_manual_tags = list(entry.tags)
        self.current_suggested_tags = list(entry.suggested_tags)

        self.favorite_checkbox.setChecked(entry.is_favorite)
        self.note_edit.setPlainText(entry.analyst_note)
        self.tags_input.setText(", ".join(entry.tags))
        self.suggested_tags_value.setText(", ".join(entry.suggested_tags) if entry.suggested_tags else "None")

    def clear_metadata_editor(self):
        self.current_entry_id = ""
        self.current_manual_tags = []
        self.current_suggested_tags = []
        self.favorite_checkbox.setChecked(False)
        self.note_edit.clear()
        self.tags_input.clear()
        self.suggested_tags_value.setText("None")

    def get_filter_values(self) -> tuple[str, str, bool, str]:
        return (
            self.search_input.text().strip(),
            self.risk_filter_combo.currentText().strip().lower(),
            self.favorite_filter_checkbox.isChecked(),
            self.tag_filter_input.text().strip().lower(),
        )

    def set_compare_left(self, entry: HistoryEntry):
        self.compare_left_entry_id = entry.entry_id
        self.compare_left_label.setText(
            f"Compare Left: {entry.request_method or 'UNK'} {entry.request_path or '/'}"
        )

    def set_compare_right(self, entry: HistoryEntry):
        self.compare_right_entry_id = entry.entry_id
        self.compare_right_label.setText(
            f"Compare Right: {entry.request_method or 'UNK'} {entry.request_path or '/'}"
        )

    def get_compare_ids(self) -> tuple[str, str]:
        return self.compare_left_entry_id, self.compare_right_entry_id

    def _emit_filter_changed(self):
        search_text, risk_filter, favorites_only, tag_filter = self.get_filter_values()
        self.filter_changed.emit(search_text, risk_filter, favorites_only, tag_filter)

    def _selected_entry_id(self) -> str:
        current_item = self.list_widget.currentItem()
        if current_item is None:
            return ""
        return current_item.data(256) or ""

    def _on_item_clicked(self, item: QListWidgetItem):
        entry_id = item.data(256)
        if entry_id:
            self.entry_selected.emit(entry_id)

    def _on_save_metadata_clicked(self):
        if not self.current_entry_id:
            return

        tags = self._normalized_tags_from_input()

        self.save_metadata_clicked.emit(
            self.current_entry_id,
            self.favorite_checkbox.isChecked(),
            self.note_edit.toPlainText(),
            tags,
        )

    def _on_apply_suggested_tags_clicked(self):
        if not self.current_entry_id:
            return

        self.apply_suggested_tags_clicked.emit(self.current_entry_id)

    def _on_copy_suggested_tags_clicked(self):
        if not self.current_entry_id:
            return

        self.copy_suggested_tags_clicked.emit(self.current_entry_id)

    def _on_mark_interesting_clicked(self):
        if not self.current_entry_id:
            return

        self.quick_add_tag_clicked.emit(self.current_entry_id, "interesting")

    def _on_mark_retest_clicked(self):
        if not self.current_entry_id:
            return

        self.quick_add_tag_clicked.emit(self.current_entry_id, "retest")

    def _on_mark_left_clicked(self):
        entry_id = self._selected_entry_id()
        if entry_id:
            self.compare_left_clicked.emit(entry_id)

    def _on_mark_right_clicked(self):
        entry_id = self._selected_entry_id()
        if entry_id:
            self.compare_right_clicked.emit(entry_id)

    def _on_clear_clicked(self):
        self.clear_history_clicked.emit()

    def clear(self):
        self.list_widget.clear()
        self.clear_metadata_editor()
        self.compare_left_entry_id = ""
        self.compare_right_entry_id = ""
        self.compare_left_label.setText("Compare Left: none")
        self.compare_right_label.setText("Compare Right: none")

    def _merge_tags(self, manual_tags: list[str], suggested_tags: list[str]) -> list[str]:
        merged = []
        seen = set()

        for tag in list(manual_tags) + list(suggested_tags):
            normalized = tag.strip().lower()
            if not normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            merged.append(normalized)

        return merged

    def _normalized_tags_from_input(self) -> list[str]:
        tags = [
            tag.strip().lower()
            for tag in self.tags_input.text().split(",")
            if tag.strip()
        ]

        unique_tags = []
        seen = set()
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags