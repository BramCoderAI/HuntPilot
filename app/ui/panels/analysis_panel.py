from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

from app.models.ai_models import AISuggestionResult
from app.models.analysis_models import ExtractionResult, ScoredAnalysisResult


class AnalysisPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("Analysis Results")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.last_extraction = None
        self.last_scored_result = None
        self.last_ai_result = None

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.output)

        self.setLayout(layout)

    def display_results(
        self,
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        ai_result: AISuggestionResult | None = None,
    ):
        self.last_extraction = extraction
        self.last_scored_result = scored_result
        self.last_ai_result = ai_result
        self._render()

    def update_ai_result(self, ai_result: AISuggestionResult | None):
        self.last_ai_result = ai_result
        self._render()

    def clear(self):
        self.last_extraction = None
        self.last_scored_result = None
        self.last_ai_result = None
        self.output.clear()

    def _render(self):
        if self.last_extraction is None or self.last_scored_result is None:
            self.output.clear()
            return

        extraction = self.last_extraction
        scored_result = self.last_scored_result
        ai_result = self.last_ai_result

        lines = []

        lines.append("=== Summary ===")
        lines.append(f"Overall Risk: {scored_result.summary.overall_risk}")
        lines.append(f"Total Signals: {scored_result.summary.total_signals}")
        lines.append(f"Total Hypotheses: {scored_result.summary.total_hypotheses}")
        lines.append(f"High Confidence Hypotheses: {scored_result.summary.high_confidence_count}")
        lines.append(f"Test First Hypotheses: {scored_result.summary.test_first_count}")
        lines.append("Top Leads:")
        if scored_result.summary.top_issue_titles:
            for title in scored_result.summary.top_issue_titles:
                lines.append(f"  - {title}")
        else:
            lines.append("  - None")
        lines.append(f"Analyst Note: {scored_result.summary.analyst_note}")
        lines.append("")

        lines.append("=== AI Recommended Next Actions ===")
        if ai_result is None:
            lines.append("No AI suggestion generated yet.")
        else:
            lines.append(f"Provider: {ai_result.provider or 'None'}")
            lines.append(f"Model: {ai_result.model_name or 'None'}")
            lines.append(f"Success: {'Yes' if ai_result.success else 'No'}")
            if ai_result.success:
                lines.append("")
                lines.append(ai_result.content if ai_result.content else "No AI content returned.")
            else:
                lines.append(f"Error: {ai_result.error_message or 'Unknown AI error.'}")
        lines.append("")

        lines.append("=== Extracted Findings ===")
        lines.append("")

        lines.append("Detected IDs:")
        lines.extend(self._format_extracted_findings(extraction.ids))
        lines.append("")

        lines.append("Sensitive Fields:")
        lines.extend(self._format_extracted_findings(extraction.sensitive_fields))
        lines.append("")

        lines.append("Auth Markers:")
        lines.extend(self._format_extracted_findings(extraction.auth_markers))
        lines.append("")

        lines.append("Session Markers:")
        lines.extend(self._format_extracted_findings(extraction.session_markers))
        lines.append("")

        lines.append("Endpoint Markers:")
        lines.extend(self._format_extracted_findings(extraction.endpoint_markers))
        lines.append("")

        lines.append("Content Markers:")
        lines.extend(self._format_extracted_findings(extraction.content_markers))
        lines.append("")

        lines.append("Response Markers:")
        lines.extend(self._format_extracted_findings(extraction.response_markers))
        lines.append("")

        lines.append("=== Detected Signals ===")
        lines.append("")
        if scored_result.signals:
            for index, signal in enumerate(scored_result.signals, start=1):
                lines.append(f"{index}. {signal.name}")
                lines.append(f"   Description: {signal.description}")
                lines.append(f"   Severity: {signal.severity}")
                lines.append("   Evidence:")
                if signal.evidence:
                    for item in signal.evidence:
                        lines.append(f"     - {item}")
                else:
                    lines.append("     - None")
                lines.append("")
        else:
            lines.append("No signals detected.")
            lines.append("")

        lines.append("=== Prioritized Hypotheses ===")
        lines.append("")
        if scored_result.hypotheses:
            for index, hypothesis in enumerate(scored_result.hypotheses, start=1):
                lines.append(f"{index}. {hypothesis.title}")
                lines.append(f"   Issue Type: {hypothesis.issue_type}")
                lines.append(f"   Score: {hypothesis.score}")
                lines.append(f"   Confidence: {hypothesis.confidence}")
                lines.append(f"   Priority: {hypothesis.priority}")
                lines.append(f"   Impact: {hypothesis.impact}")
                lines.append(f"   Effort: {hypothesis.effort}")
                lines.append(f"   Description: {hypothesis.description}")
                lines.append(f"   Rationale: {hypothesis.rationale}")
                lines.append("   Evidence:")
                if hypothesis.evidence:
                    for item in hypothesis.evidence:
                        lines.append(f"     - {item}")
                else:
                    lines.append("     - None")
                lines.append("   Recommended Tests:")
                if hypothesis.recommended_tests:
                    for test in hypothesis.recommended_tests:
                        lines.append(f"     - {test}")
                else:
                    lines.append("     - None")
                lines.append("")
        else:
            lines.append("No hypotheses generated.")

        self.output.setPlainText("\n".join(lines))

    def _format_extracted_findings(self, findings):
        if not findings:
            return ["  None"]

        lines = []
        for finding in findings:
            lines.append(
                f"  - name={finding.name} | value={finding.value} | source={finding.source}"
            )
        return lines