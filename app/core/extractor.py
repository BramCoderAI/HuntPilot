from typing import Any, Dict, Optional

from app.models.analysis_models import ExtractedFinding, ExtractionResult
from app.models.http_models import HTTPRequest, HTTPResponse
from app.utils.text_utils import looks_like_numeric_id, looks_like_uuid


SENSITIVE_FIELD_NAMES = {
    "id",
    "user_id",
    "account_id",
    "profile_id",
    "organization_id",
    "owner_id",
    "role",
    "roles",
    "permission",
    "permissions",
    "is_admin",
    "isAdmin",
    "access_level",
    "status",
    "email",
    "password",
    "plan",
    "subscription",
    "owner",
}

SESSION_COOKIE_HINTS = {
    "session",
    "sessionid",
    "phpsessid",
    "connect.sid",
    "sid",
    "token",
    "auth_token",
    "access_token",
    "refresh_token",
    "jwt",
}


def extract_request_findings(
    request: HTTPRequest,
    response: Optional[HTTPResponse] = None,
) -> ExtractionResult:
    result = ExtractionResult()

    _extract_ids_from_path(request, result)
    _extract_ids_from_query_params(request, result)
    _extract_body_markers(request, result)
    _extract_auth_markers(request, result)
    _extract_session_markers(request, result)
    _extract_endpoint_markers(request, result)
    _extract_content_markers(request, result)

    if response is not None:
        _extract_response_markers(response, result)

    return result


def _extract_ids_from_path(request: HTTPRequest, result: ExtractionResult) -> None:
    parts = [part for part in request.path.split("/") if part.strip()]
    for part in parts:
        if looks_like_numeric_id(part) or looks_like_uuid(part):
            result.ids.append(
                ExtractedFinding(
                    category="id",
                    name="path_identifier",
                    value=part,
                    source="path",
                )
            )


def _extract_ids_from_query_params(request: HTTPRequest, result: ExtractionResult) -> None:
    sensitive_names_lower = {name.lower() for name in SENSITIVE_FIELD_NAMES}

    for key, value in request.query_params.items():
        normalized_key = key.lower()

        if normalized_key.endswith("id") or normalized_key.endswith("_id"):
            result.ids.append(
                ExtractedFinding(
                    category="id",
                    name=key,
                    value=value,
                    source="query_param",
                )
            )

        if normalized_key in sensitive_names_lower:
            result.sensitive_fields.append(
                ExtractedFinding(
                    category="sensitive_field",
                    name=key,
                    value=value,
                    source="query_param",
                )
            )


def _extract_body_markers(request: HTTPRequest, result: ExtractionResult) -> None:
    if isinstance(request.body_json, dict):
        _walk_dict(request.body_json, "json_body", result)

    for key, value in request.body_form.items():
        _handle_key_value(key, value, "form_body", result)


def _walk_dict(data: Dict[str, Any], source: str, result: ExtractionResult) -> None:
    for key, value in data.items():
        if isinstance(value, dict):
            _walk_dict(value, source, result)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _walk_dict(item, source, result)
                else:
                    _handle_key_value(key, item, source, result)
        else:
            _handle_key_value(key, value, source, result)


def _handle_key_value(key: str, value: Any, source: str, result: ExtractionResult) -> None:
    value_str = str(value)
    normalized_key = key.lower()
    sensitive_names_lower = {name.lower() for name in SENSITIVE_FIELD_NAMES}

    if normalized_key.endswith("id") or normalized_key.endswith("_id"):
        result.ids.append(
            ExtractedFinding(
                category="id",
                name=key,
                value=value_str,
                source=source,
            )
        )

    if normalized_key in sensitive_names_lower:
        result.sensitive_fields.append(
            ExtractedFinding(
                category="sensitive_field",
                name=key,
                value=value_str,
                source=source,
            )
        )


def _extract_auth_markers(request: HTTPRequest, result: ExtractionResult) -> None:
    authorization = request.headers.get("Authorization", "")
    if authorization:
        result.auth_markers.append(
            ExtractedFinding(
                category="auth",
                name="Authorization",
                value=authorization,
                source="header",
            )
        )

    for header_name, header_value in request.headers.items():
        normalized = header_name.lower()
        if normalized in {"x-api-key", "api-key", "x-auth-token", "x-csrf-token", "csrf-token"}:
            result.auth_markers.append(
                ExtractedFinding(
                    category="auth",
                    name=header_name,
                    value=header_value,
                    source="header",
                )
            )


def _extract_session_markers(request: HTTPRequest, result: ExtractionResult) -> None:
    for cookie_name, cookie_value in request.cookies.items():
        cookie_name_lower = cookie_name.lower()
        if cookie_name_lower in SESSION_COOKIE_HINTS or "session" in cookie_name_lower or "token" in cookie_name_lower:
            result.session_markers.append(
                ExtractedFinding(
                    category="session",
                    name=cookie_name,
                    value=cookie_value,
                    source="cookie",
                )
            )


def _extract_endpoint_markers(request: HTTPRequest, result: ExtractionResult) -> None:
    path_lower = request.path.lower()

    endpoint_patterns = [
        ("graphql_endpoint", "/graphql"),
        ("admin_endpoint", "/admin"),
        ("internal_endpoint", "/internal"),
        ("api_endpoint", "/api/"),
        ("upload_endpoint", "/upload"),
        ("auth_endpoint", "/login"),
        ("auth_endpoint", "/signin"),
        ("auth_endpoint", "/signup"),
        ("auth_endpoint", "/reset"),
        ("auth_endpoint", "/password"),
    ]

    for name, pattern in endpoint_patterns:
        if pattern in path_lower:
            result.endpoint_markers.append(
                ExtractedFinding(
                    category="endpoint",
                    name=name,
                    value=pattern,
                    source="path",
                )
            )


def _extract_content_markers(request: HTTPRequest, result: ExtractionResult) -> None:
    content_type_lower = request.content_type.lower()

    if request.body_json is not None:
        result.content_markers.append(
            ExtractedFinding(
                category="content",
                name="json_body",
                value="true",
                source="request_body",
            )
        )

    if "application/x-www-form-urlencoded" in content_type_lower:
        result.content_markers.append(
            ExtractedFinding(
                category="content",
                name="form_urlencoded",
                value="true",
                source="request_body",
            )
        )

    if "multipart/form-data" in content_type_lower:
        result.content_markers.append(
            ExtractedFinding(
                category="content",
                name="multipart_form_data",
                value="true",
                source="request_body",
            )
        )


def _extract_response_markers(response: HTTPResponse, result: ExtractionResult) -> None:
    if response.status_code:
        result.response_markers.append(
            ExtractedFinding(
                category="response",
                name="status_code",
                value=str(response.status_code),
                source="response",
            )
        )

    if response.reason_phrase:
        result.response_markers.append(
            ExtractedFinding(
                category="response",
                name="reason_phrase",
                value=response.reason_phrase,
                source="response",
            )
        )

    if response.body_json is not None:
        result.response_markers.append(
            ExtractedFinding(
                category="response",
                name="json_response",
                value="true",
                source="response",
            )
        )

    if response.content_type:
        result.response_markers.append(
            ExtractedFinding(
                category="response",
                name="response_content_type",
                value=response.content_type,
                source="response",
            )
        )

    if response.body_length > 0:
        result.response_markers.append(
            ExtractedFinding(
                category="response",
                name="response_body_length",
                value=str(response.body_length),
                source="response",
            )
        )

    body_lower = response.body.lower()

    response_keywords = [
        ("auth_error", "forbidden"),
        ("auth_error", "unauthorized"),
        ("validation_error", "validation"),
        ("validation_error", "invalid"),
        ("permission_error", "not allowed"),
        ("permission_error", "permission"),
        ("server_error_hint", "exception"),
        ("server_error_hint", "traceback"),
        ("server_error_hint", "stack trace"),
        ("debug_leak_hint", "sql"),
        ("debug_leak_hint", "database"),
    ]

    for name, keyword in response_keywords:
        if keyword in body_lower:
            result.response_markers.append(
                ExtractedFinding(
                    category="response",
                    name=name,
                    value=keyword,
                    source="response_body",
                )
            )