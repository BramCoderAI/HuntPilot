from typing import Optional

from app.models.analysis_models import ExtractionResult, ScoredAnalysisResult
from app.models.ai_models import AISuggestionResult
from app.models.history_models import HistoryEntry
from app.models.http_models import HTTPRequest, HTTPResponse
from app.utils.ai_serialization import ai_suggestion_result_to_dict
from app.utils.analysis_serialization import (
    extraction_result_to_dict,
    scored_analysis_result_to_dict,
)
from app.utils.export_utils import dataclass_to_dict, write_json_file, write_text_file


class ExportManager:
    def export_current_analysis_to_txt(
        self,
        file_path: str,
        request_raw: str,
        response_raw: str,
        request: HTTPRequest,
        response: Optional[HTTPResponse],
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        ai_result: AISuggestionResult | None = None,
    ) -> None:
        content = self._build_text_report(
            request_raw=request_raw,
            response_raw=response_raw,
            request=request,
            response=response,
            extraction=extraction,
            scored_result=scored_result,
            ai_result=ai_result,
        )
        write_text_file(file_path, content)

    def export_current_analysis_to_json(
        self,
        file_path: str,
        request_raw: str,
        response_raw: str,
        request: HTTPRequest,
        response: Optional[HTTPResponse],
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        ai_result: AISuggestionResult | None = None,
    ) -> None:
        data = {
            "request_raw": request_raw,
            "response_raw": response_raw,
            "parsed_request": dataclass_to_dict(request),
            "parsed_response": dataclass_to_dict(response) if response is not None else None,
            "extraction": extraction_result_to_dict(extraction),
            "analysis": scored_analysis_result_to_dict(scored_result),
            "ai_suggestion": ai_suggestion_result_to_dict(ai_result),
        }
        write_json_file(file_path, data)

    def export_history_to_json(
        self,
        file_path: str,
        history_entries: list[HistoryEntry],
    ) -> None:
        data = [dataclass_to_dict(entry) for entry in history_entries]
        write_json_file(file_path, data)

    def _build_text_report(
        self,
        request_raw: str,
        response_raw: str,
        request: HTTPRequest,
        response: Optional[HTTPResponse],
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        ai_result: AISuggestionResult | None = None,
    ) -> str:
        lines: list[str] = []

        lines.append("HuntPilot Analysis Report")
        lines.append("")

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
            lines.append("No AI suggestion generated.")
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

        lines.append("=== Parsed Request ===")
        lines.append(f"Method: {request.method or 'None'}")
        lines.append(f"URL: {request.url or 'None'}")
        lines.append(f"Host: {request.host or 'None'}")
        lines.append(f"Path: {request.path or 'None'}")
        lines.append("")

        lines.append("=== Parsed Response ===")
        if response is None:
            lines.append("No response provided.")
        else:
            lines.append(f"Status Code: {response.status_code}")
            lines.append(f"Reason Phrase: {response.reason_phrase or 'None'}")
            lines.append(f"Content-Type: {response.content_type or 'None'}")
            lines.append(f"Body Length: {response.body_length}")
        lines.append("")

        lines.append("=== Extracted Findings ===")
        lines.append("Detected IDs:")
        lines.extend(self._format_findings(extraction.ids))
        lines.append("")
        lines.append("Sensitive Fields:")
        lines.extend(self._format_findings(extraction.sensitive_fields))
        lines.append("")
        lines.append("Auth Markers:")
        lines.extend(self._format_findings(extraction.auth_markers))
        lines.append("")
        lines.append("Session Markers:")
        lines.extend(self._format_findings(extraction.session_markers))
        lines.append("")
        lines.append("Endpoint Markers:")
        lines.extend(self._format_findings(extraction.endpoint_markers))
        lines.append("")
        lines.append("Content Markers:")
        lines.extend(self._format_findings(extraction.content_markers))
        lines.append("")
        lines.append("Response Markers:")
        lines.extend(self._format_findings(extraction.response_markers))
        lines.append("")

        lines.append("=== Detected Signals ===")
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
            lines.append("None")
            lines.append("")

        lines.append("=== Prioritized Hypotheses ===")
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
            lines.append("None")
            lines.append("")

        lines.append("=== Raw Request ===")
        lines.append(request_raw if request_raw else "None")
        lines.append("")
        lines.append("=== Raw Response ===")
        lines.append(response_raw if response_raw else "None")

        return "\n".join(lines)

    def _format_findings(self, findings) -> list[str]:
        if not findings:
            return ["  None"]

        lines = []
        for finding in findings:
            lines.append(
                f"  - name={finding.name} | value={finding.value} | source={finding.source}"
            )
        return lines