from typing import Optional

from app.models.analysis_models import (
    DetectedSignal,
    DetectionResult,
    ExtractionResult,
    Hypothesis,
)
from app.models.http_models import HTTPRequest, HTTPResponse


PRIVILEGE_FIELD_NAMES = {
    "role",
    "roles",
    "permission",
    "permissions",
    "is_admin",
    "isadmin",
    "access_level",
}

ACCOUNT_FIELD_NAMES = {
    "user_id",
    "account_id",
    "profile_id",
    "organization_id",
    "owner_id",
    "owner",
    "email",
}

WORKFLOW_FIELD_NAMES = {
    "status",
    "plan",
    "subscription",
}


def run_detectors(
    request: HTTPRequest,
    extraction: ExtractionResult,
    response: Optional[HTTPResponse] = None,
) -> DetectionResult:
    result = DetectionResult()

    _detect_identifier_access_patterns(request, extraction, result)
    _detect_privilege_escalation(request, extraction, result)
    _detect_mass_assignment(request, extraction, result)
    _detect_server_side_validation_gaps(request, extraction, result)
    _detect_graphql_auth_risk(request, extraction, result)
    _detect_upload_validation_risk(request, extraction, result)

    if response is not None:
        _detect_authz_response_patterns(request, extraction, response, result)
        _detect_validation_response_patterns(request, extraction, response, result)
        _detect_server_error_patterns(response, extraction, result)

    return result


def _detect_identifier_access_patterns(
    request: HTTPRequest,
    extraction: ExtractionResult,
    result: DetectionResult,
) -> None:
    has_path_id = any(finding.source == "path" for finding in extraction.ids)
    has_other_account_refs = any(
        finding.name.lower() in ACCOUNT_FIELD_NAMES
        for finding in extraction.ids + extraction.sensitive_fields
    )

    if has_path_id and has_other_account_refs:
        evidence = _collect_evidence_for_names(
            extraction,
            {
                "path_identifier",
                "user_id",
                "account_id",
                "profile_id",
                "organization_id",
                "owner_id",
                "owner",
                "email",
            },
        )

        result.signals.append(
            DetectedSignal(
                name="multiple_user_reference_points",
                description="The request contains both a path identifier and user/account-related references.",
                severity="high",
                evidence=evidence,
            )
        )

        result.hypotheses.append(
            Hypothesis(
                issue_type="BOLA / IDOR",
                title="Potential object-level authorization weakness",
                description="The request appears to act on a resource identified in the path while also carrying user or account references in parameters or body fields.",
                rationale="When a request contains multiple user or object reference points, inconsistent authorization checks can allow access to another user's object.",
                confidence="high",
                priority="test first",
                impact="high",
                effort="medium",
                recommended_tests=[
                    "Change the identifier in the path to another test object you are authorized to use.",
                    "Change the body or query identifier independently from the path identifier and compare behavior.",
                    "Compare status code, response size, and returned fields between authorized and altered requests.",
                    "Check whether read, update, or delete behavior changes across different owned test objects.",
                ],
                evidence=evidence,
            )
        )
    elif len(extraction.ids) >= 2:
        evidence = [f"{finding.source}:{finding.name}={finding.value}" for finding in extraction.ids]

        result.signals.append(
            DetectedSignal(
                name="multiple_identifiers_present",
                description="The request carries multiple object identifiers.",
                severity="medium",
                evidence=evidence,
            )
        )

        result.hypotheses.append(
            Hypothesis(
                issue_type="BOLA / IDOR",
                title="Multiple object references worth checking for authorization drift",
                description="The request includes more than one identifier, which can sometimes expose inconsistent object authorization logic.",
                rationale="Multiple identifiers in one request can produce mismatches between the object being authorized and the object being processed.",
                confidence="medium",
                priority="worth checking",
                impact="high",
                effort="medium",
                recommended_tests=[
                    "Swap one identifier at a time while keeping the others unchanged.",
                    "Check whether the server trusts body identifiers more than path identifiers.",
                    "Review whether the returned object matches the resource you intended to access.",
                ],
                evidence=evidence,
            )
        )


def _detect_privilege_escalation(
    request: HTTPRequest,
    extraction: ExtractionResult,
    result: DetectionResult,
) -> None:
    privilege_fields = [
        finding
        for finding in extraction.sensitive_fields
        if finding.name.lower() in PRIVILEGE_FIELD_NAMES
    ]

    if not privilege_fields:
        return

    evidence = [f"{finding.source}:{finding.name}={finding.value}" for finding in privilege_fields]

    result.signals.append(
        DetectedSignal(
            name="privilege_related_fields_in_request",
            description="The request contains role or permission-related fields.",
            severity="high",
            evidence=evidence,
        )
    )

    confidence = "high" if request.method.upper() in {"PATCH", "PUT", "POST"} else "medium"

    result.hypotheses.append(
        Hypothesis(
            issue_type="Privilege Escalation",
            title="Client-controlled privilege fields detected",
            description="The request includes fields that may influence authorization or privilege level.",
            rationale="If the backend trusts role or permission fields sent by the client, an attacker may be able to raise privileges or alter access level.",
            confidence=confidence,
            priority="test first",
            impact="high",
            effort="medium",
            recommended_tests=[
                "Modify role, permission, or admin-related fields to stronger values and compare the response.",
                "Add privilege-related fields not present in the normal UI and see whether they are accepted.",
                "Check whether the change persists on subsequent reads or affects accessible features.",
                "Compare behavior using different test accounts with different legitimate roles.",
            ],
            evidence=evidence,
        )
    )


def _detect_mass_assignment(
    request: HTTPRequest,
    extraction: ExtractionResult,
    result: DetectionResult,
) -> None:
    json_field_count = 0
    if isinstance(request.body_json, dict):
        json_field_count = _count_json_leaf_fields(request.body_json)

    sensitive_body_fields = [
        finding
        for finding in extraction.sensitive_fields
        if finding.source in {"json_body", "form_body"}
    ]

    if json_field_count >= 5 and len(sensitive_body_fields) >= 1:
        evidence = [f"json_leaf_fields={json_field_count}"]
        evidence.extend(
            f"{finding.source}:{finding.name}={finding.value}" for finding in sensitive_body_fields
        )

        result.signals.append(
            DetectedSignal(
                name="broad_client_supplied_object",
                description="The request body contains many client-controlled fields including sensitive-looking ones.",
                severity="high",
                evidence=evidence,
            )
        )

        result.hypotheses.append(
            Hypothesis(
                issue_type="Mass Assignment",
                title="Request body may allow unsafe field binding",
                description="The request includes a broad object with multiple client-controlled fields and at least one sensitive field.",
                rationale="Backends that bind whole objects directly from client input can accidentally allow protected fields to be modified.",
                confidence="high",
                priority="test first",
                impact="high",
                effort="medium",
                recommended_tests=[
                    "Add fields that are not exposed in the UI, such as role, status, owner_id, or internal flags.",
                    "Remove optional fields one by one and observe which fields the backend truly requires.",
                    "Inject likely server-side model fields and compare whether they are ignored, rejected, or persisted.",
                    "Check whether sensitive fields can be modified even when the frontend normally hides them.",
                ],
                evidence=evidence,
            )
        )
    elif sensitive_body_fields:
        evidence = [f"{finding.source}:{finding.name}={finding.value}" for finding in sensitive_body_fields]

        result.signals.append(
            DetectedSignal(
                name="sensitive_client_supplied_fields",
                description="The request body contains sensitive-looking writable fields.",
                severity="medium",
                evidence=evidence,
            )
        )

        result.hypotheses.append(
            Hypothesis(
                issue_type="Mass Assignment",
                title="Sensitive body fields deserve binding checks",
                description="Sensitive fields are being sent by the client and may be trusted by the backend.",
                rationale="Even small request bodies can expose unsafe object binding when sensitive fields are writable from the client side.",
                confidence="medium",
                priority="worth checking",
                impact="medium",
                effort="medium",
                recommended_tests=[
                    "Try adding adjacent internal-looking fields to the request body.",
                    "Change one sensitive field at a time and verify whether it is persisted.",
                    "Check whether the server silently accepts extra properties.",
                ],
                evidence=evidence,
            )
        )


def _detect_server_side_validation_gaps(
    request: HTTPRequest,
    extraction: ExtractionResult,
    result: DetectionResult,
) -> None:
    workflow_fields = [
        finding
        for finding in extraction.sensitive_fields
        if finding.name.lower() in WORKFLOW_FIELD_NAMES
    ]

    account_fields = [
        finding
        for finding in extraction.sensitive_fields
        if finding.name.lower() in ACCOUNT_FIELD_NAMES
    ]

    if request.method.upper() not in {"POST", "PUT", "PATCH"}:
        return

    if not workflow_fields and not account_fields:
        return

    evidence = [
        f"{finding.source}:{finding.name}={finding.value}"
        for finding in workflow_fields + account_fields
    ]

    result.signals.append(
        DetectedSignal(
            name="client_controls_business_fields",
            description="The request body or parameters contain business-critical fields controlled by the client.",
            severity="medium",
            evidence=evidence,
        )
    )

    result.hypotheses.append(
        Hypothesis(
            issue_type="Missing Server-Side Validation",
            title="Business-critical fields should be validated server-side",
            description="The client appears able to send account, workflow, or lifecycle fields directly.",
            rationale="Fields such as status, owner, plan, account references, or subscription values often require strict backend validation and authorization.",
            confidence="medium",
            priority="worth checking",
            impact="medium",
            effort="low",
            recommended_tests=[
                "Send invalid, unexpected, or out-of-sequence values for workflow fields such as status or plan.",
                "Attempt transitions that should not be allowed at the current step.",
                "Provide another authorized test account reference and verify whether the backend enforces ownership.",
                "Check whether the server rejects invalid enum values or silently normalizes them.",
            ],
            evidence=evidence,
        )
    )


def _detect_graphql_auth_risk(
    request: HTTPRequest,
    extraction: ExtractionResult,
    result: DetectionResult,
) -> None:
    has_graphql_endpoint = any(
        finding.name == "graphql_endpoint" for finding in extraction.endpoint_markers
    )

    if not has_graphql_endpoint:
        return

    evidence = [f"{finding.source}:{finding.name}={finding.value}" for finding in extraction.endpoint_markers]

    result.signals.append(
        DetectedSignal(
            name="graphql_surface_detected",
            description="The request targets a GraphQL endpoint.",
            severity="medium",
            evidence=evidence,
        )
    )

    result.hypotheses.append(
        Hypothesis(
            issue_type="GraphQL Authorization",
            title="GraphQL endpoint deserves field-level authorization checks",
            description="GraphQL often exposes authorization problems at the field, object, or nested query level.",
            rationale="Even when endpoint authentication is correct, GraphQL resolvers may apply inconsistent authorization across fields or related objects.",
            confidence="medium",
            priority="worth checking",
            impact="medium",
            effort="medium",
            recommended_tests=[
                "Check whether introspection is enabled when it should be restricted.",
                "Request fields that look admin-only or unrelated to the current user.",
                "Try nested object queries that cross account boundaries using authorized test data.",
                "Test whether unauthorized fields fail cleanly or leak partial data.",
            ],
            evidence=evidence,
        )
    )


def _detect_upload_validation_risk(
    request: HTTPRequest,
    extraction: ExtractionResult,
    result: DetectionResult,
) -> None:
    has_multipart = any(
        finding.name == "multipart_form_data" for finding in extraction.content_markers
    )
    has_upload_path = any(
        finding.name == "upload_endpoint" for finding in extraction.endpoint_markers
    )

    if not has_multipart and not has_upload_path:
        return

    evidence = [
        f"{finding.source}:{finding.name}={finding.value}"
        for finding in extraction.content_markers + extraction.endpoint_markers
        if finding.name in {"multipart_form_data", "upload_endpoint"}
    ]

    result.signals.append(
        DetectedSignal(
            name="file_upload_surface_detected",
            description="The request appears related to a file upload flow.",
            severity="medium",
            evidence=evidence,
        )
    )

    result.hypotheses.append(
        Hypothesis(
            issue_type="Upload Validation",
            title="Upload flow should be checked for validation and storage controls",
            description="The request looks like a file upload or upload-related endpoint.",
            rationale="Upload handlers often fail on extension checks, MIME validation, filename handling, or post-upload access controls.",
            confidence="medium",
            priority="worth checking",
            impact="medium",
            effort="medium",
            recommended_tests=[
                "Compare server handling of extension, MIME type, and real file content.",
                "Try filenames with unusual characters, double extensions, or long names.",
                "Check whether uploaded files are publicly reachable or executable in downstream flows.",
                "Verify size limits and server behavior on malformed multipart requests.",
            ],
            evidence=evidence,
        )
    )


def _detect_authz_response_patterns(
    request: HTTPRequest,
    extraction: ExtractionResult,
    response: HTTPResponse,
    result: DetectionResult,
) -> None:
    if response.status_code in {401, 403}:
        evidence = [f"response:status_code={response.status_code}"]
        evidence.extend(
            f"{finding.source}:{finding.name}={finding.value}"
            for finding in extraction.response_markers
            if finding.name in {"auth_error", "permission_error", "reason_phrase"}
        )

        result.signals.append(
            DetectedSignal(
                name="authorization_response_detected",
                description="The response clearly indicates an authorization or authentication barrier.",
                severity="medium",
                evidence=evidence,
            )
        )

        result.hypotheses.append(
            Hypothesis(
                issue_type="Authorization Behavior",
                title="Authorization barrier confirmed by response",
                description="The server is explicitly rejecting the request with an authorization-related response.",
                rationale="A 401 or 403 confirms a server-side check exists, which is useful for mapping trust boundaries and testing whether related endpoints enforce the same control consistently.",
                confidence="medium",
                priority="worth checking",
                impact="medium",
                effort="low",
                recommended_tests=[
                    "Compare this endpoint with similar endpoints handling the same object type.",
                    "Change one identifier at a time and verify whether all variants still trigger the same control.",
                    "Check whether read and write operations enforce the same restriction consistently.",
                    "Look for adjacent endpoints where the same authorization rule may be missing.",
                ],
                evidence=evidence,
            )
        )

    if response.status_code == 404 and any(finding.source == "path" for finding in extraction.ids):
        evidence = [f"response:status_code={response.status_code}"]

        result.signals.append(
            DetectedSignal(
                name="not_found_on_object_route",
                description="The request targeted an object route and returned 404.",
                severity="low",
                evidence=evidence,
            )
        )

        result.hypotheses.append(
            Hypothesis(
                issue_type="Object Enumeration / Access Pattern",
                title="404 behavior on object route is worth comparing",
                description="A 404 on an object-specific route can be useful when comparing how the application responds to existing versus non-existing or unauthorized objects.",
                rationale="Different 404, 403, and 200 behaviors can reveal authorization patterns or object existence handling.",
                confidence="low",
                priority="worth checking",
                impact="low",
                effort="low",
                recommended_tests=[
                    "Compare the response for an existing object you control versus a clearly non-existing identifier.",
                    "Check whether response size, timing, or message wording differs across object states.",
                ],
                evidence=evidence,
            )
        )


def _detect_validation_response_patterns(
    request: HTTPRequest,
    extraction: ExtractionResult,
    response: HTTPResponse,
    result: DetectionResult,
) -> None:
    has_validation_marker = any(
        finding.name == "validation_error" for finding in extraction.response_markers
    )

    if response.status_code in {400, 422} or has_validation_marker:
        evidence = [f"response:status_code={response.status_code}"]
        evidence.extend(
            f"{finding.source}:{finding.name}={finding.value}"
            for finding in extraction.response_markers
            if finding.name == "validation_error"
        )

        result.signals.append(
            DetectedSignal(
                name="validation_feedback_detected",
                description="The response contains validation-related feedback.",
                severity="low",
                evidence=evidence,
            )
        )

        result.hypotheses.append(
            Hypothesis(
                issue_type="Validation Surface",
                title="Validation behavior can be mapped more precisely",
                description="The response suggests the backend performs input validation and may reveal how strict or detailed those checks are.",
                rationale="Validation messages often help identify trusted fields, hidden rules, enum constraints, and differences between client-side and server-side enforcement.",
                confidence="medium",
                priority="worth checking",
                impact="low",
                effort="low",
                recommended_tests=[
                    "Send boundary values, wrong data types, and unknown enum values.",
                    "Check whether validation messages reveal internal field names or accepted formats.",
                    "Compare validation behavior across similar endpoints and methods.",
                ],
                evidence=evidence,
            )
        )


def _detect_server_error_patterns(
    response: HTTPResponse,
    extraction: ExtractionResult,
    result: DetectionResult,
) -> None:
    has_server_error_keyword = any(
        finding.name in {"server_error_hint", "debug_leak_hint"}
        for finding in extraction.response_markers
    )

    if response.status_code >= 500 or has_server_error_keyword:
        evidence = [f"response:status_code={response.status_code}"]
        evidence.extend(
            f"{finding.source}:{finding.name}={finding.value}"
            for finding in extraction.response_markers
            if finding.name in {"server_error_hint", "debug_leak_hint"}
        )

        result.signals.append(
            DetectedSignal(
                name="server_error_or_debug_hint",
                description="The response suggests a server-side failure or possible debug information leakage.",
                severity="high",
                evidence=evidence,
            )
        )

        result.hypotheses.append(
            Hypothesis(
                issue_type="Server Error / Information Leak",
                title="Server-side error handling deserves review",
                description="The response indicates either a backend failure or information that may help map internal behavior.",
                rationale="500-level errors, stack traces, and backend technology hints can reveal fragile input handling or useful debugging artifacts.",
                confidence="medium",
                priority="test first",
                impact="medium",
                effort="low",
                recommended_tests=[
                    "Check whether the same error is reproducible with small controlled input changes.",
                    "Look for stack traces, technology names, SQL fragments, or internal field names in the response.",
                    "Compare error behavior across content types and malformed structures.",
                ],
                evidence=evidence,
            )
        )


def _collect_evidence_for_names(extraction: ExtractionResult, names: set[str]) -> list[str]:
    evidence = []

    all_findings = (
        extraction.ids
        + extraction.sensitive_fields
        + extraction.auth_markers
        + extraction.session_markers
        + extraction.endpoint_markers
        + extraction.content_markers
        + extraction.response_markers
    )

    lowered_names = {name.lower() for name in names}

    for finding in all_findings:
        if finding.name.lower() in lowered_names:
            evidence.append(f"{finding.source}:{finding.name}={finding.value}")

    return evidence


def _count_json_leaf_fields(data) -> int:
    if isinstance(data, dict):
        total = 0
        for value in data.values():
            total += _count_json_leaf_fields(value)
        return total
    if isinstance(data, list):
        total = 0
        for item in data:
            total += _count_json_leaf_fields(item)
        return total
    return 1