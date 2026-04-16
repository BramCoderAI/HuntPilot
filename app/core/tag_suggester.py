from app.models.analysis_models import ExtractionResult, ScoredAnalysisResult
from app.models.http_models import HTTPRequest, HTTPResponse


class TagSuggester:
    def suggest_tags(
        self,
        request: HTTPRequest,
        response: HTTPResponse | None,
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
    ) -> list[str]:
        suggested_tags: list[str] = []

        issue_type_to_tag = {
            "BOLA / IDOR": "idor",
            "Privilege Escalation": "authz",
            "Mass Assignment": "mass-assignment",
            "Missing Server-Side Validation": "validation",
            "GraphQL Authorization": "graphql",
            "Upload Validation": "upload",
            "Authorization Behavior": "authz-check",
            "Validation Surface": "validation-surface",
            "Server Error / Information Leak": "error-leak",
            "Object Enumeration / Access Pattern": "enumeration",
        }

        for hypothesis in scored_result.hypotheses:
            tag = issue_type_to_tag.get(hypothesis.issue_type)
            if tag:
                suggested_tags.append(tag)

            priority = hypothesis.priority.lower().strip()
            if priority == "test first":
                suggested_tags.append("test-first")

            confidence = hypothesis.confidence.lower().strip()
            if confidence == "high":
                suggested_tags.append("high-confidence")

        for endpoint_marker in extraction.endpoint_markers:
            marker_name = endpoint_marker.name.lower().strip()

            if marker_name == "graphql_endpoint":
                suggested_tags.append("graphql")
            elif marker_name == "admin_endpoint":
                suggested_tags.append("admin")
            elif marker_name == "internal_endpoint":
                suggested_tags.append("internal")
            elif marker_name == "upload_endpoint":
                suggested_tags.append("upload")
            elif marker_name == "auth_endpoint":
                suggested_tags.append("auth-flow")
            elif marker_name == "api_endpoint":
                suggested_tags.append("api")

        for content_marker in extraction.content_markers:
            marker_name = content_marker.name.lower().strip()

            if marker_name == "json_body":
                suggested_tags.append("json")
            elif marker_name == "multipart_form_data":
                suggested_tags.append("multipart")
            elif marker_name == "form_urlencoded":
                suggested_tags.append("form")

        if extraction.auth_markers:
            suggested_tags.append("authenticated")

        if extraction.session_markers:
            suggested_tags.append("session")

        if any(finding.name.lower() in {"role", "roles", "permission", "permissions", "is_admin", "access_level"} for finding in extraction.sensitive_fields):
            suggested_tags.append("privilege-field")

        if any(finding.name.lower() in {"user_id", "account_id", "profile_id", "organization_id", "owner_id"} for finding in extraction.ids + extraction.sensitive_fields):
            suggested_tags.append("object-reference")

        if response is not None:
            if response.status_code:
                suggested_tags.append(str(response.status_code))

            if response.status_code == 403:
                suggested_tags.append("forbidden")
            elif response.status_code == 401:
                suggested_tags.append("unauthorized")
            elif response.status_code == 404:
                suggested_tags.append("not-found")
            elif response.status_code >= 500:
                suggested_tags.append("server-error")

        if request.method:
            suggested_tags.append(request.method.lower())

        risk = scored_result.summary.overall_risk.lower().strip()
        if risk:
            suggested_tags.append(f"risk-{risk}")

        if request.path:
            path_lower = request.path.lower()
            if "/admin" in path_lower:
                suggested_tags.append("admin")
            if "/graphql" in path_lower:
                suggested_tags.append("graphql")
            if "/upload" in path_lower:
                suggested_tags.append("upload")
            if "/api/" in path_lower:
                suggested_tags.append("api")

        normalized_unique_tags: list[str] = []
        seen = set()

        for tag in suggested_tags:
            normalized = tag.strip().lower()
            if not normalized:
                continue
            if normalized not in seen:
                seen.add(normalized)
                normalized_unique_tags.append(normalized)

        return normalized_unique_tags