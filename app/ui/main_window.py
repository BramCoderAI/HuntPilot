from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QPushButton, QSplitter, QTabWidget, QVBoxLayout, QWidget

from app.config import APP_NAME, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from app.core.ai_manager import AIManager
from app.core.comparison_manager import ComparisonManager
from app.core.dashboard_manager import DashboardManager
from app.core.detectors import run_detectors
from app.core.export_manager import ExportManager
from app.core.extractor import extract_request_findings
from app.core.history_manager import HistoryManager
from app.core.parser import parse_http_request, parse_http_response
from app.core.project_manager import ProjectManager
from app.core.scorer import score_detection_result
from app.core.tag_suggester import TagSuggester
from app.models.ai_models import AISettings
from app.models.history_models import HistoryEntry
from app.models.project_models import ProjectInfo
from app.ui.panels.ai_panel import AIPanel
from app.ui.panels.analysis_panel import AnalysisPanel
from app.ui.panels.comparison_panel import ComparisonPanel
from app.ui.panels.dashboard_panel import DashboardPanel
from app.ui.panels.export_panel import ExportPanel
from app.ui.panels.history_panel import HistoryPanel
from app.ui.panels.input_panel import InputPanel
from app.ui.panels.request_viewer import RequestViewer
from app.ui.panels.status_panel import StatusPanel
from app.utils.ai_serialization import ai_suggestion_result_from_dict
from app.utils.analysis_serialization import (
    extraction_result_from_dict,
    scored_analysis_result_from_dict,
)


class MainWindow(QMainWindow):
    back_to_project_selector_requested = pyqtSignal()

    def __init__(self, project_info: ProjectInfo):
        super().__init__()

        self.project_info = project_info
        self.project_manager = ProjectManager()

        history_file_path = self.project_manager.get_history_file_path(self.project_info.folder_name)
        self.exports_dir = self.project_manager.get_exports_dir(self.project_info.folder_name)
        ai_settings_file_path = self.project_manager.get_ai_settings_file_path(self.project_info.folder_name)

        self.setWindowTitle(f"{APP_NAME} - {self.project_info.name}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self.history_manager = HistoryManager(file_path=history_file_path)
        self.export_manager = ExportManager()
        self.comparison_manager = ComparisonManager()
        self.dashboard_manager = DashboardManager()
        self.tag_suggester = TagSuggester()
        self.ai_manager = AIManager(settings_file_path=ai_settings_file_path)

        self.last_request_raw = ""
        self.last_response_raw = ""
        self.last_parsed_request = None
        self.last_parsed_response = None
        self.last_extraction_result = None
        self.last_scored_result = None
        self.last_suggested_tags: list[str] = []
        self.last_ai_result = None
        self.last_history_entry_id = ""

        self.back_button = QPushButton("Back to Project Selector")
        self.back_button.clicked.connect(self.back_to_project_selector_requested.emit)

        self.input_panel = InputPanel()
        self.request_viewer = RequestViewer()
        self.analysis_panel = AnalysisPanel()
        self.comparison_panel = ComparisonPanel()
        self.dashboard_panel = DashboardPanel()
        self.ai_panel = AIPanel()
        self.status_panel = StatusPanel()
        self.history_panel = HistoryPanel()
        self.export_panel = ExportPanel()

        self.ai_panel.set_available_ollama_models(self.ai_manager.get_recommended_ollama_models())
        self.ai_panel.load_settings(self.ai_manager.get_settings())

        self.input_panel.analyze_clicked.connect(self.handle_analyze)
        self.input_panel.clear_clicked.connect(self.handle_input_clear)

        self.ai_panel.save_settings_clicked.connect(self.handle_save_ai_settings)
        self.ai_panel.generate_clicked.connect(self.handle_generate_ai_suggestions)
        self.ai_panel.copy_install_command_clicked.connect(self.handle_copy_ollama_install_command)
        self.ai_panel.test_connection_clicked.connect(self.handle_test_ai_connection)
        self.ai_panel.pull_model_clicked.connect(self.handle_pull_ollama_model)

        self.history_panel.entry_selected.connect(self.handle_history_selected)
        self.history_panel.clear_history_clicked.connect(self.handle_clear_history)
        self.history_panel.save_metadata_clicked.connect(self.handle_save_history_metadata)
        self.history_panel.filter_changed.connect(self.handle_history_filter_changed)
        self.history_panel.compare_left_clicked.connect(self.handle_compare_left_selected)
        self.history_panel.compare_right_clicked.connect(self.handle_compare_right_selected)
        self.history_panel.compare_run_clicked.connect(self.handle_run_comparison)
        self.history_panel.apply_suggested_tags_clicked.connect(self.handle_apply_suggested_tags)
        self.history_panel.copy_suggested_tags_clicked.connect(self.handle_copy_suggested_tags)
        self.history_panel.quick_add_tag_clicked.connect(self.handle_quick_add_tag)

        self.export_panel.export_current_txt_clicked.connect(self.handle_export_current_txt)
        self.export_panel.export_current_json_clicked.connect(self.handle_export_current_json)
        self.export_panel.export_history_json_clicked.connect(self.handle_export_history_json)

        self.center_tabs = QTabWidget()
        self.center_tabs.addTab(self.request_viewer, "Parsed Exchange")
        self.center_tabs.addTab(self.analysis_panel, "Analysis")
        self.center_tabs.addTab(self.comparison_panel, "Comparison")
        self.center_tabs.addTab(self.dashboard_panel, "Dashboard")
        self.center_tabs.addTab(self.ai_panel, "AI")

        self.right_tabs = QTabWidget()
        self.right_tabs.addTab(self.status_panel, "Status")
        self.right_tabs.addTab(self.history_panel, "History")
        self.right_tabs.addTab(self.export_panel, "Export")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.input_panel)
        splitter.addWidget(self.center_tabs)
        splitter.addWidget(self.right_tabs)
        splitter.setSizes([520, 820, 420])

        root_layout = QVBoxLayout()
        root_layout.addWidget(self.back_button)
        root_layout.addWidget(splitter)

        root_widget = QWidget()
        root_widget.setLayout(root_layout)

        self.setCentralWidget(root_widget)

        self.refresh_history_panel()
        self.refresh_dashboard()
        self.status_panel.set_message(
            f"Project loaded: {self.project_info.name}. Paste a Burp request and optional response, load files, or load the sample exchange."
        )

    def handle_analyze(self, raw_request: str, raw_response: str):
        if not raw_request.strip():
            self.status_panel.set_message("No request provided. Paste a request or load one from a file.")
            return

        parsed_request = parse_http_request(raw_request)
        parsed_response = parse_http_response(raw_response) if raw_response.strip() else None

        extraction_result = extract_request_findings(parsed_request, parsed_response)
        detection_result = run_detectors(parsed_request, extraction_result, parsed_response)
        scored_result = score_detection_result(detection_result)

        suggested_tags = self.tag_suggester.suggest_tags(
            request=parsed_request,
            response=parsed_response,
            extraction=extraction_result,
            scored_result=scored_result,
        )

        self.last_request_raw = raw_request
        self.last_response_raw = raw_response
        self.last_parsed_request = parsed_request
        self.last_parsed_response = parsed_response
        self.last_extraction_result = extraction_result
        self.last_scored_result = scored_result
        self.last_suggested_tags = suggested_tags
        self.last_ai_result = None

        self.request_viewer.display_exchange(parsed_request, parsed_response)
        self.analysis_panel.display_results(extraction_result, scored_result, ai_result=None)
        self.ai_panel.clear_output()
        self.center_tabs.setCurrentWidget(self.analysis_panel)

        history_entry = self.history_manager.add_entry(
            request=parsed_request,
            response=parsed_response,
            extraction_result=extraction_result,
            scored_result=scored_result,
            request_raw=raw_request,
            response_raw=raw_response,
            suggested_tags=suggested_tags,
            ai_result=None,
        )
        self.last_history_entry_id = history_entry.entry_id

        self.refresh_history_panel()
        self.refresh_dashboard()
        self.project_manager.touch_project(self.project_info.folder_name)

        response_note = "with response" if parsed_response is not None else "without response"
        dedupe_note = (
            f" Existing history entry updated (hit count: {history_entry.hit_count})."
            if history_entry.hit_count > 1
            else " New history entry added."
        )

        suggested_tag_note = f" Suggested tags: {', '.join(suggested_tags)}." if suggested_tags else ""

        self.status_panel.set_message(
            f"Analysis complete {response_note}. "
            f"{scored_result.summary.total_hypotheses} hypotheses generated. "
            f"Overall risk: {scored_result.summary.overall_risk}.{dedupe_note}{suggested_tag_note}"
        )

        if self.ai_manager.get_settings().auto_suggest_after_analysis:
            self.handle_generate_ai_suggestions()

    def handle_save_ai_settings(self, settings: AISettings):
        self.ai_manager.save_settings(settings)
        self.status_panel.set_message(f"AI settings saved. Mode: {settings.mode}.")

    def handle_test_ai_connection(self):
        status = self.ai_manager.test_connection()
        self.ai_panel.display_connection_status(status)
        self.status_panel.set_message(status.message)

    def handle_pull_ollama_model(self, model_name: str):
        settings = self.ai_manager.get_settings()
        if settings.mode != "ollama":
            self.status_panel.set_message("Switch AI mode to 'ollama' before pulling a model.")
            return

        success, message = self.ai_manager.pull_ollama_model(model_name)
        self.status_panel.set_message(message)

        status = self.ai_manager.test_connection()
        self.ai_panel.display_connection_status(status)

    def handle_generate_ai_suggestions(self):
        if (
            self.last_parsed_request is None
            or self.last_extraction_result is None
            or self.last_scored_result is None
        ):
            self.status_panel.set_message("No current analysis available for AI suggestions.")
            return

        result = self.ai_manager.generate_suggestions(
            project_name=self.project_info.name,
            request=self.last_parsed_request,
            response=self.last_parsed_response,
            extraction=self.last_extraction_result,
            scored_result=self.last_scored_result,
            suggested_tags=self.last_suggested_tags,
        )

        self.last_ai_result = result

        if self.last_history_entry_id:
            self.history_manager.update_entry_ai_result(
                entry_id=self.last_history_entry_id,
                ai_result=result,
            )

        self.ai_panel.display_result(result)
        self.analysis_panel.update_ai_result(result)
        self.center_tabs.setCurrentWidget(self.analysis_panel)

        if result.success:
            self.status_panel.set_message(
                f"AI suggestions generated with {result.provider} ({result.model_name})."
            )
        else:
            self.status_panel.set_message(
                f"AI suggestion failed with {result.provider} ({result.model_name})."
            )

    def handle_copy_ollama_install_command(self, model_name: str):
        command = self.ai_manager.get_ollama_install_command(model_name)
        QGuiApplication.clipboard().setText(command)
        self.status_panel.set_message("Ollama install + pull command copied to clipboard.")

    def handle_input_clear(self):
        self.last_request_raw = ""
        self.last_response_raw = ""
        self.last_parsed_request = None
        self.last_parsed_response = None
        self.last_extraction_result = None
        self.last_scored_result = None
        self.last_suggested_tags = []
        self.last_ai_result = None
        self.last_history_entry_id = ""

        self.request_viewer.clear()
        self.analysis_panel.clear()
        self.comparison_panel.clear()
        self.ai_panel.clear_output()
        self.status_panel.set_message("Cleared input. Ready for a new request/response pair.")

    def handle_history_selected(self, entry_id: str):
        entry = self.history_manager.get_entry_by_id(entry_id)
        if entry is None:
            self.status_panel.set_message("Could not load the selected history entry.")
            return

        self.input_panel.set_exchange_text(entry.request_raw, entry.response_raw)
        self.history_panel.load_entry_metadata(entry)

        parsed_request = parse_http_request(entry.request_raw)
        parsed_response = parse_http_response(entry.response_raw) if entry.response_raw.strip() else None

        self.request_viewer.display_exchange(parsed_request, parsed_response)

        restored_extraction = extraction_result_from_dict(entry.extraction_data)
        restored_scored_result = scored_analysis_result_from_dict(entry.scored_analysis_data)
        restored_ai_result = ai_suggestion_result_from_dict(entry.ai_suggestion_data)

        if restored_extraction is not None and restored_scored_result is not None:
            self.analysis_panel.display_results(restored_extraction, restored_scored_result, ai_result=restored_ai_result)

            if restored_ai_result is not None:
                self.ai_panel.display_result(restored_ai_result)
            else:
                self.ai_panel.clear_output()

            self.center_tabs.setCurrentWidget(self.analysis_panel)

            self.last_request_raw = entry.request_raw
            self.last_response_raw = entry.response_raw
            self.last_parsed_request = parsed_request
            self.last_parsed_response = parsed_response
            self.last_extraction_result = restored_extraction
            self.last_scored_result = restored_scored_result
            self.last_suggested_tags = list(entry.suggested_tags)
            self.last_ai_result = restored_ai_result
            self.last_history_entry_id = entry.entry_id

            self.status_panel.set_message(
                f"Loaded history entry from {entry.updated_at} with saved analysis."
            )
        else:
            self.status_panel.set_message(
                f"Loaded history entry from {entry.updated_at}. Saved analysis missing, re-run Analyze if needed."
            )

    def handle_compare_left_selected(self, entry_id: str):
        entry = self.history_manager.get_entry_by_id(entry_id)
        if entry is None:
            self.status_panel.set_message("Could not set left comparison entry.")
            return

        self.history_panel.set_compare_left(entry)
        self.status_panel.set_message("Left comparison entry selected.")

    def handle_compare_right_selected(self, entry_id: str):
        entry = self.history_manager.get_entry_by_id(entry_id)
        if entry is None:
            self.status_panel.set_message("Could not set right comparison entry.")
            return

        self.history_panel.set_compare_right(entry)
        self.status_panel.set_message("Right comparison entry selected.")

    def handle_run_comparison(self):
        left_id, right_id = self.history_panel.get_compare_ids()

        if not left_id or not right_id:
            self.status_panel.set_message("Select both left and right history entries before comparing.")
            return

        left_entry = self.history_manager.get_entry_by_id(left_id)
        right_entry = self.history_manager.get_entry_by_id(right_id)

        if left_entry is None or right_entry is None:
            self.status_panel.set_message("Could not load one of the comparison entries.")
            return

        comparison_result = self.comparison_manager.compare_entries(left_entry, right_entry)
        self.comparison_panel.display_comparison(comparison_result)
        self.center_tabs.setCurrentWidget(self.comparison_panel)
        self.status_panel.set_message("Comparison complete.")

    def handle_save_history_metadata(self, entry_id: str, is_favorite: bool, analyst_note: str, tags: list):
        entry = self.history_manager.update_entry_metadata(
            entry_id=entry_id,
            is_favorite=is_favorite,
            analyst_note=analyst_note,
            tags=tags,
        )

        if entry is None:
            self.status_panel.set_message("Could not save note/favorite/tags for the selected history entry.")
            return

        self.refresh_history_panel()
        self.refresh_dashboard()
        self.history_panel.load_entry_metadata(entry)
        self.status_panel.set_message("History entry metadata saved.")

    def handle_apply_suggested_tags(self, entry_id: str):
        entry = self.history_manager.get_entry_by_id(entry_id)
        if entry is None:
            self.status_panel.set_message("Could not apply suggested tags.")
            return

        merged_tags = self._merge_tags(entry.tags, entry.suggested_tags)
        updated_entry = self.history_manager.update_entry_metadata(
            entry_id=entry_id,
            tags=merged_tags,
        )

        if updated_entry is None:
            self.status_panel.set_message("Could not apply suggested tags.")
            return

        self.refresh_history_panel()
        self.refresh_dashboard()
        self.history_panel.load_entry_metadata(updated_entry)
        self.status_panel.set_message("Suggested tags applied to manual tags.")

    def handle_copy_suggested_tags(self, entry_id: str):
        entry = self.history_manager.get_entry_by_id(entry_id)
        if entry is None:
            self.status_panel.set_message("Could not copy suggested tags.")
            return

        text = ", ".join(entry.suggested_tags)
        QGuiApplication.clipboard().setText(text)
        self.status_panel.set_message("Suggested tags copied to clipboard.")

    def handle_quick_add_tag(self, entry_id: str, quick_tag: str):
        entry = self.history_manager.get_entry_by_id(entry_id)
        if entry is None:
            self.status_panel.set_message("Could not add quick tag.")
            return

        merged_tags = self._merge_tags(entry.tags, [quick_tag])
        updated_entry = self.history_manager.update_entry_metadata(
            entry_id=entry_id,
            tags=merged_tags,
        )

        if updated_entry is None:
            self.status_panel.set_message("Could not add quick tag.")
            return

        self.refresh_history_panel()
        self.refresh_dashboard()
        self.history_panel.load_entry_metadata(updated_entry)
        self.status_panel.set_message(f"Quick tag '{quick_tag}' added.")

    def handle_clear_history(self):
        self.history_manager.clear()
        self.refresh_history_panel()
        self.refresh_dashboard()
        self.history_panel.clear_metadata_editor()
        self.comparison_panel.clear()
        self.ai_panel.clear_output()
        self.status_panel.set_message("History cleared.")

    def handle_history_filter_changed(
        self,
        search_text: str,
        risk_filter: str,
        favorites_only: bool,
        tag_filter: str,
    ):
        self.refresh_history_panel(search_text, risk_filter, favorites_only, tag_filter)
        self.status_panel.set_message("History filters updated.")

    def refresh_history_panel(
        self,
        search_text: str | None = None,
        risk_filter: str | None = None,
        favorites_only: bool | None = None,
        tag_filter: str | None = None,
    ):
        if (
            search_text is None
            or risk_filter is None
            or favorites_only is None
            or tag_filter is None
        ):
            search_text, risk_filter, favorites_only, tag_filter = self.history_panel.get_filter_values()

        entries = self.history_manager.get_entries()
        filtered_entries = self._filter_history_entries(
            entries,
            search_text,
            risk_filter,
            favorites_only,
            tag_filter,
        )
        self.history_panel.set_entries(filtered_entries)

    def refresh_dashboard(self):
        entries = self.history_manager.get_entries()
        dashboard_data = self.dashboard_manager.build_dashboard_data(entries)
        self.dashboard_panel.display_dashboard(dashboard_data, self.project_info.name)

    def handle_export_current_txt(self):
        if not self._has_current_analysis():
            self.status_panel.set_message("No current analysis to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Current Analysis as Text",
            f"{self.exports_dir}/huntpilot_analysis.txt",
            "Text Files (*.txt)",
        )

        if not file_path:
            return

        self.export_manager.export_current_analysis_to_txt(
            file_path=file_path,
            request_raw=self.last_request_raw,
            response_raw=self.last_response_raw,
            request=self.last_parsed_request,
            response=self.last_parsed_response,
            extraction=self.last_extraction_result,
            scored_result=self.last_scored_result,
            ai_result=self.last_ai_result,
        )

        self.status_panel.set_message(f"Current analysis exported to: {file_path}")

    def handle_export_current_json(self):
        if not self._has_current_analysis():
            self.status_panel.set_message("No current analysis to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Current Analysis as JSON",
            f"{self.exports_dir}/huntpilot_analysis.json",
            "JSON Files (*.json)",
        )

        if not file_path:
            return

        self.export_manager.export_current_analysis_to_json(
            file_path=file_path,
            request_raw=self.last_request_raw,
            response_raw=self.last_response_raw,
            request=self.last_parsed_request,
            response=self.last_parsed_response,
            extraction=self.last_extraction_result,
            scored_result=self.last_scored_result,
            ai_result=self.last_ai_result,
        )

        self.status_panel.set_message(f"Current analysis exported to: {file_path}")

    def handle_export_history_json(self):
        entries = self.history_manager.get_entries()
        if not entries:
            self.status_panel.set_message("No history entries to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export History as JSON",
            f"{self.exports_dir}/huntpilot_history.json",
            "JSON Files (*.json)",
        )

        if not file_path:
            return

        self.export_manager.export_history_to_json(
            file_path=file_path,
            history_entries=entries,
        )

        self.status_panel.set_message(f"History exported to: {file_path}")

    def _has_current_analysis(self) -> bool:
        return (
            self.last_parsed_request is not None
            and self.last_extraction_result is not None
            and self.last_scored_result is not None
        )

    def _filter_history_entries(
        self,
        entries: list[HistoryEntry],
        search_text: str,
        risk_filter: str,
        favorites_only: bool,
        tag_filter: str,
    ) -> list[HistoryEntry]:
        filtered = []

        search_text_lower = search_text.lower().strip()
        tag_filter_lower = tag_filter.lower().strip()

        for entry in entries:
            if favorites_only and not entry.is_favorite:
                continue

            if risk_filter != "all" and entry.overall_risk.lower() != risk_filter:
                continue

            merged_tags = self._merge_tags(entry.tags, entry.suggested_tags)

            if tag_filter_lower:
                if tag_filter_lower not in merged_tags:
                    continue

            searchable_parts = [
                entry.created_at,
                entry.updated_at,
                entry.request_method,
                entry.request_path,
                entry.overall_risk,
                " ".join(entry.top_issue_titles),
                entry.analyst_note,
                " ".join(merged_tags),
                str(entry.response_status) if entry.response_status is not None else "",
                str(entry.hit_count),
            ]
            searchable_text = " ".join(searchable_parts).lower()

            if search_text_lower and search_text_lower not in searchable_text:
                continue

            filtered.append(entry)

        return filtered

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