import difflib
from typing import Any, Dict, List, Optional

from app.models.comparison_models import ComparisonResult, ComparisonRow
from app.models.history_models import HistoryEntry
from app.core.parser import parse_http_request, parse_http_response


class ComparisonManager:
    def compare_entries(self, left_entry: HistoryEntry, right_entry: HistoryEntry) -> ComparisonResult:
        rows = []

        rows.append(self._build_row("Created At", left_entry.created_at, right_entry.created_at))
        rows.append(self._build_row("Updated At", left_entry.updated_at, right_entry.updated_at))
        rows.append(self._build_row("Method", left_entry.request_method, right_entry.request_method))
        rows.append(self._build_row("Path", left_entry.request_path, right_entry.request_path))
        rows.append(
            self._build_row(
                "Response Status",
                self._safe_str(left_entry.response_status, "NoResp"),
                self._safe_str(right_entry.response_status, "NoResp"),
            )
        )
        rows.append(self._build_row("Overall Risk", left_entry.overall_risk, right_entry.overall_risk))
        rows.append(self._build_row("Favorite", str(left_entry.is_favorite), str(right_entry.is_favorite)))
        rows.append(self._build_row("Hit Count", str(left_entry.hit_count), str(right_entry.hit_count)))
        rows.append(
            self._build_row(
                "Top Issues",
                " | ".join(left_entry.top_issue_titles) if left_entry.top_issue_titles else "None",
                " | ".join(right_entry.top_issue_titles) if right_entry.top_issue_titles else "None",
            )
        )
        rows.append(
            self._build_row(
                "Analyst Note",
                left_entry.analyst_note if left_entry.analyst_note else "None",
                right_entry.analyst_note if right_entry.analyst_note else "None",
            )
        )
        rows.append(
            self._build_row(
                "Request Raw Length",
                str(len(left_entry.request_raw)),
                str(len(right_entry.request_raw)),
            )
        )
        rows.append(
            self._build_row(
                "Response Raw Length",
                str(len(left_entry.response_raw)),
                str(len(right_entry.response_raw)),
            )
        )

        left_request = parse_http_request(left_entry.request_raw)
        right_request = parse_http_request(right_entry.request_raw)

        left_response = parse_http_response(left_entry.response_raw) if left_entry.response_raw.strip() else None
        right_response = parse_http_response(right_entry.response_raw) if right_entry.response_raw.strip() else None

        request_structured_diffs = self._compare_requests(left_request, right_request)
        response_structured_diffs = self._compare_responses(left_response, right_response)

        request_line_diff = self._build_line_diff(
            left_text=left_entry.request_raw,
            right_text=right_entry.request_raw,
            from_label="left_request",
            to_label="right_request",
        )
        response_line_diff = self._build_line_diff(
            left_text=left_entry.response_raw,
            right_text=right_entry.response_raw,
            from_label="left_response",
            to_label="right_response",
        )

        changed_count = sum(1 for row in rows if row.changed)
        summary = self._build_summary(
            left_entry=left_entry,
            right_entry=right_entry,
            changed_count=changed_count,
            request_diff_count=len(request_structured_diffs),
            response_diff_count=len(response_structured_diffs),
        )

        return ComparisonResult(
            left_entry_id=left_entry.entry_id,
            right_entry_id=right_entry.entry_id,
            rows=rows,
            summary=summary,
            request_structured_diffs=request_structured_diffs,
            response_structured_diffs=response_structured_diffs,
            request_line_diff=request_line_diff,
            response_line_diff=response_line_diff,
        )

    def _compare_requests(self, left_request, right_request) -> List[str]:
        diffs: List[str] = []

        self._append_simple_field_diff(diffs, "Request method", left_request.method, right_request.method)
        self._append_simple_field_diff(diffs, "Request URL", left_request.url, right_request.url)
        self._append_simple_field_diff(diffs, "Request path", left_request.path, right_request.path)
        self._append_simple_field_diff(diffs, "Request host", left_request.host, right_request.host)
        self._append_simple_field_diff(diffs, "Request content-type", left_request.content_type, right_request.content_type)

        diffs.extend(self._compare_dicts("Query Param", left_request.query_params, right_request.query_params))
        diffs.extend(self._compare_dicts("Header", left_request.headers, right_request.headers))
        diffs.extend(self._compare_dicts("Cookie", left_request.cookies, right_request.cookies))

        if left_request.body_json is not None or right_request.body_json is not None:
            diffs.extend(
                self._compare_json_values(
                    path="request.body_json",
                    left_value=left_request.body_json,
                    right_value=right_request.body_json,
                )
            )
        elif left_request.body_form or right_request.body_form:
            diffs.extend(self._compare_dicts("Form Field", left_request.body_form, right_request.body_form))
        else:
            self._append_simple_field_diff(diffs, "Request raw body", left_request.body, right_request.body)

        return diffs

    def _compare_responses(self, left_response, right_response) -> List[str]:
        diffs: List[str] = []

        if left_response is None and right_response is None:
            return diffs

        if left_response is None and right_response is not None:
            diffs.append("Response exists only on right side.")
            return diffs

        if left_response is not None and right_response is None:
            diffs.append("Response exists only on left side.")
            return diffs

        self._append_simple_field_diff(
            diffs,
            "Response status",
            str(left_response.status_code),
            str(right_response.status_code),
        )
        self._append_simple_field_diff(
            diffs,
            "Response reason phrase",
            left_response.reason_phrase,
            right_response.reason_phrase,
        )
        self._append_simple_field_diff(
            diffs,
            "Response content-type",
            left_response.content_type,
            right_response.content_type,
        )
        self._append_simple_field_diff(
            diffs,
            "Response body length",
            str(left_response.body_length),
            str(right_response.body_length),
        )

        diffs.extend(self._compare_dicts("Response Header", left_response.headers, right_response.headers))

        if left_response.body_json is not None or right_response.body_json is not None:
            diffs.extend(
                self._compare_json_values(
                    path="response.body_json",
                    left_value=left_response.body_json,
                    right_value=right_response.body_json,
                )
            )
        else:
            self._append_simple_field_diff(diffs, "Response raw body", left_response.body, right_response.body)

        return diffs

    def _compare_dicts(self, label: str, left_dict: Dict[str, Any], right_dict: Dict[str, Any]) -> List[str]:
        diffs: List[str] = []

        left_keys = set(left_dict.keys())
        right_keys = set(right_dict.keys())

        for key in sorted(left_keys - right_keys):
            diffs.append(f"{label} removed: {key}={left_dict[key]}")

        for key in sorted(right_keys - left_keys):
            diffs.append(f"{label} added: {key}={right_dict[key]}")

        for key in sorted(left_keys & right_keys):
            left_value = str(left_dict.get(key, ""))
            right_value = str(right_dict.get(key, ""))
            if left_value != right_value:
                diffs.append(
                    f"{label} changed: {key} | left={left_value} | right={right_value}"
                )

        return diffs

    def _compare_json_values(self, path: str, left_value: Any, right_value: Any) -> List[str]:
        diffs: List[str] = []

        if left_value is None and right_value is None:
            return diffs

        if left_value is None and right_value is not None:
            diffs.append(f"{path} added on right: {self._short_value(right_value)}")
            return diffs

        if left_value is not None and right_value is None:
            diffs.append(f"{path} removed on right: {self._short_value(left_value)}")
            return diffs

        if type(left_value) != type(right_value):
            diffs.append(
                f"{path} type changed: left={type(left_value).__name__} | right={type(right_value).__name__}"
            )
            return diffs

        if isinstance(left_value, dict):
            left_keys = set(left_value.keys())
            right_keys = set(right_value.keys())

            for key in sorted(left_keys - right_keys):
                diffs.append(
                    f"{path}.{key} removed on right: {self._short_value(left_value[key])}"
                )

            for key in sorted(right_keys - left_keys):
                diffs.append(
                    f"{path}.{key} added on right: {self._short_value(right_value[key])}"
                )

            for key in sorted(left_keys & right_keys):
                diffs.extend(
                    self._compare_json_values(
                        path=f"{path}.{key}",
                        left_value=left_value[key],
                        right_value=right_value[key],
                    )
                )

            return diffs

        if isinstance(left_value, list):
            if left_value == right_value:
                return diffs

            min_len = min(len(left_value), len(right_value))
            for index in range(min_len):
                diffs.extend(
                    self._compare_json_values(
                        path=f"{path}[{index}]",
                        left_value=left_value[index],
                        right_value=right_value[index],
                    )
                )

            if len(left_value) > len(right_value):
                for index in range(len(right_value), len(left_value)):
                    diffs.append(
                        f"{path}[{index}] removed on right: {self._short_value(left_value[index])}"
                    )

            if len(right_value) > len(left_value):
                for index in range(len(left_value), len(right_value)):
                    diffs.append(
                        f"{path}[{index}] added on right: {self._short_value(right_value[index])}"
                    )

            return diffs

        if left_value != right_value:
            diffs.append(
                f"{path} changed: left={self._short_value(left_value)} | right={self._short_value(right_value)}"
            )

        return diffs

    def _append_simple_field_diff(
        self,
        diffs: List[str],
        field_name: str,
        left_value: str,
        right_value: str,
    ) -> None:
        left_text = left_value if left_value not in {None, ""} else "None"
        right_text = right_value if right_value not in {None, ""} else "None"

        if left_text != right_text:
            diffs.append(f"{field_name} changed: left={left_text} | right={right_text}")

    def _build_line_diff(
        self,
        left_text: str,
        right_text: str,
        from_label: str,
        to_label: str,
        max_lines: int = 200,
    ) -> str:
        left_lines = left_text.splitlines()
        right_lines = right_text.splitlines()

        diff_lines = list(
            difflib.unified_diff(
                left_lines,
                right_lines,
                fromfile=from_label,
                tofile=to_label,
                lineterm="",
            )
        )

        if not diff_lines:
            return "No line-level differences detected."

        if len(diff_lines) > max_lines:
            visible_lines = diff_lines[:max_lines]
            visible_lines.append(f"... diff truncated, total lines: {len(diff_lines)}")
            return "\n".join(visible_lines)

        return "\n".join(diff_lines)

    def _build_row(self, field_name: str, left_value: str, right_value: str) -> ComparisonRow:
        return ComparisonRow(
            field_name=field_name,
            left_value=left_value,
            right_value=right_value,
            changed=left_value != right_value,
        )

    def _safe_str(self, value, default: str) -> str:
        return default if value is None else str(value)

    def _short_value(self, value: Any, max_length: int = 80) -> str:
        text = str(value)
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def _build_summary(
        self,
        left_entry: HistoryEntry,
        right_entry: HistoryEntry,
        changed_count: int,
        request_diff_count: int,
        response_diff_count: int,
    ) -> str:
        key_changes = []

        if left_entry.response_status != right_entry.response_status:
            key_changes.append("response status changed")

        if left_entry.overall_risk != right_entry.overall_risk:
            key_changes.append("overall risk changed")

        if left_entry.request_path != right_entry.request_path:
            key_changes.append("path changed")

        if left_entry.request_method != right_entry.request_method:
            key_changes.append("method changed")

        if not key_changes:
            key_changes_text = "No major high-level field changed."
        else:
            key_changes_text = ", ".join(key_changes).capitalize() + "."

        return (
            f"Compared {changed_count} metadata differences, "
            f"{request_diff_count} structured request differences, and "
            f"{response_diff_count} structured response differences. "
            f"{key_changes_text}"
        )