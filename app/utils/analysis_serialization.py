from app.models.analysis_models import (
    AnalysisSummary,
    DetectedSignal,
    ExtractedFinding,
    ExtractionResult,
    Hypothesis,
    ScoredAnalysisResult,
)


def extraction_result_to_dict(extraction: ExtractionResult) -> dict:
    return {
        "ids": [finding_to_dict(finding) for finding in extraction.ids],
        "sensitive_fields": [finding_to_dict(finding) for finding in extraction.sensitive_fields],
        "auth_markers": [finding_to_dict(finding) for finding in extraction.auth_markers],
        "session_markers": [finding_to_dict(finding) for finding in extraction.session_markers],
        "endpoint_markers": [finding_to_dict(finding) for finding in extraction.endpoint_markers],
        "content_markers": [finding_to_dict(finding) for finding in extraction.content_markers],
        "response_markers": [finding_to_dict(finding) for finding in extraction.response_markers],
    }


def extraction_result_from_dict(data: dict | None) -> ExtractionResult | None:
    if not data:
        return None

    return ExtractionResult(
        ids=findings_from_list(data.get("ids", [])),
        sensitive_fields=findings_from_list(data.get("sensitive_fields", [])),
        auth_markers=findings_from_list(data.get("auth_markers", [])),
        session_markers=findings_from_list(data.get("session_markers", [])),
        endpoint_markers=findings_from_list(data.get("endpoint_markers", [])),
        content_markers=findings_from_list(data.get("content_markers", [])),
        response_markers=findings_from_list(data.get("response_markers", [])),
    )


def scored_analysis_result_to_dict(scored_result: ScoredAnalysisResult) -> dict:
    return {
        "signals": [
            {
                "name": signal.name,
                "description": signal.description,
                "severity": signal.severity,
                "evidence": list(signal.evidence),
            }
            for signal in scored_result.signals
        ],
        "hypotheses": [
            {
                "issue_type": hypothesis.issue_type,
                "title": hypothesis.title,
                "description": hypothesis.description,
                "rationale": hypothesis.rationale,
                "confidence": hypothesis.confidence,
                "priority": hypothesis.priority,
                "recommended_tests": list(hypothesis.recommended_tests),
                "evidence": list(hypothesis.evidence),
                "impact": hypothesis.impact,
                "effort": hypothesis.effort,
                "score": hypothesis.score,
            }
            for hypothesis in scored_result.hypotheses
        ],
        "summary": {
            "total_signals": scored_result.summary.total_signals,
            "total_hypotheses": scored_result.summary.total_hypotheses,
            "high_confidence_count": scored_result.summary.high_confidence_count,
            "test_first_count": scored_result.summary.test_first_count,
            "top_issue_titles": list(scored_result.summary.top_issue_titles),
            "overall_risk": scored_result.summary.overall_risk,
            "analyst_note": scored_result.summary.analyst_note,
        },
    }


def scored_analysis_result_from_dict(data: dict | None) -> ScoredAnalysisResult | None:
    if not data:
        return None

    summary_data = data.get("summary", {})

    return ScoredAnalysisResult(
        signals=[
            DetectedSignal(
                name=item.get("name", ""),
                description=item.get("description", ""),
                severity=item.get("severity", ""),
                evidence=item.get("evidence", []),
            )
            for item in data.get("signals", [])
        ],
        hypotheses=[
            Hypothesis(
                issue_type=item.get("issue_type", ""),
                title=item.get("title", ""),
                description=item.get("description", ""),
                rationale=item.get("rationale", ""),
                confidence=item.get("confidence", "low"),
                priority=item.get("priority", "low signal"),
                recommended_tests=item.get("recommended_tests", []),
                evidence=item.get("evidence", []),
                impact=item.get("impact", "medium"),
                effort=item.get("effort", "medium"),
                score=item.get("score", 0),
            )
            for item in data.get("hypotheses", [])
        ],
        summary=AnalysisSummary(
            total_signals=summary_data.get("total_signals", 0),
            total_hypotheses=summary_data.get("total_hypotheses", 0),
            high_confidence_count=summary_data.get("high_confidence_count", 0),
            test_first_count=summary_data.get("test_first_count", 0),
            top_issue_titles=summary_data.get("top_issue_titles", []),
            overall_risk=summary_data.get("overall_risk", "low"),
            analyst_note=summary_data.get("analyst_note", ""),
        ),
    )


def finding_to_dict(finding: ExtractedFinding) -> dict:
    return {
        "category": finding.category,
        "name": finding.name,
        "value": finding.value,
        "source": finding.source,
    }


def findings_from_list(items: list[dict]) -> list[ExtractedFinding]:
    return [
        ExtractedFinding(
            category=item.get("category", ""),
            name=item.get("name", ""),
            value=item.get("value", ""),
            source=item.get("source", ""),
        )
        for item in items
    ]