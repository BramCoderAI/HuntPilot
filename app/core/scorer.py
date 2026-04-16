from app.models.analysis_models import (
    AnalysisSummary,
    DetectionResult,
    Hypothesis,
    ScoredAnalysisResult,
)


CONFIDENCE_POINTS = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

PRIORITY_POINTS = {
    "low signal": 1,
    "worth checking": 2,
    "test first": 3,
}

IMPACT_POINTS = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

EFFORT_POINTS = {
    "low": 3,
    "medium": 2,
    "high": 1,
}

ISSUE_DEFAULTS = {
    "BOLA / IDOR": {"impact": "high", "effort": "medium"},
    "Privilege Escalation": {"impact": "high", "effort": "medium"},
    "Mass Assignment": {"impact": "high", "effort": "medium"},
    "Missing Server-Side Validation": {"impact": "medium", "effort": "low"},
    "GraphQL Authorization": {"impact": "medium", "effort": "medium"},
    "Upload Validation": {"impact": "medium", "effort": "medium"},
    "Authorization Behavior": {"impact": "medium", "effort": "low"},
    "Validation Surface": {"impact": "low", "effort": "low"},
    "Server Error / Information Leak": {"impact": "medium", "effort": "low"},
    "Object Enumeration / Access Pattern": {"impact": "low", "effort": "low"},
}


def score_detection_result(detection: DetectionResult) -> ScoredAnalysisResult:
    hypotheses = []

    for hypothesis in detection.hypotheses:
        scored = _score_hypothesis(hypothesis)
        hypotheses.append(scored)

    hypotheses.sort(key=_sort_key, reverse=True)

    summary = _build_summary(detection, hypotheses)

    return ScoredAnalysisResult(
        signals=detection.signals,
        hypotheses=hypotheses,
        summary=summary,
    )


def _score_hypothesis(hypothesis: Hypothesis) -> Hypothesis:
    defaults = ISSUE_DEFAULTS.get(
        hypothesis.issue_type,
        {"impact": "medium", "effort": "medium"},
    )

    if not hypothesis.impact:
        hypothesis.impact = defaults["impact"]

    if not hypothesis.effort:
        hypothesis.effort = defaults["effort"]

    confidence_points = CONFIDENCE_POINTS.get(hypothesis.confidence.lower(), 1)
    priority_points = PRIORITY_POINTS.get(hypothesis.priority.lower(), 1)
    impact_points = IMPACT_POINTS.get(hypothesis.impact.lower(), 2)
    effort_points = EFFORT_POINTS.get(hypothesis.effort.lower(), 2)

    evidence_bonus = min(len(hypothesis.evidence), 3)

    hypothesis.score = (
        confidence_points * 30
        + priority_points * 25
        + impact_points * 20
        + effort_points * 10
        + evidence_bonus * 5
    )

    return hypothesis


def _sort_key(hypothesis: Hypothesis):
    return (
        hypothesis.score,
        PRIORITY_POINTS.get(hypothesis.priority.lower(), 1),
        CONFIDENCE_POINTS.get(hypothesis.confidence.lower(), 1),
        IMPACT_POINTS.get(hypothesis.impact.lower(), 1),
    )


def _build_summary(
    detection: DetectionResult,
    hypotheses: list[Hypothesis],
) -> AnalysisSummary:
    total_signals = len(detection.signals)
    total_hypotheses = len(hypotheses)

    high_confidence_count = sum(
        1 for hypothesis in hypotheses if hypothesis.confidence.lower() == "high"
    )

    test_first_count = sum(
        1 for hypothesis in hypotheses if hypothesis.priority.lower() == "test first"
    )

    top_issue_titles = [hypothesis.title for hypothesis in hypotheses[:3]]

    overall_risk = _compute_overall_risk(hypotheses)
    analyst_note = _build_analyst_note(hypotheses, overall_risk)

    return AnalysisSummary(
        total_signals=total_signals,
        total_hypotheses=total_hypotheses,
        high_confidence_count=high_confidence_count,
        test_first_count=test_first_count,
        top_issue_titles=top_issue_titles,
        overall_risk=overall_risk,
        analyst_note=analyst_note,
    )


def _compute_overall_risk(hypotheses: list[Hypothesis]) -> str:
    if not hypotheses:
        return "low"

    top_score = hypotheses[0].score
    high_impact_count = sum(
        1 for hypothesis in hypotheses if hypothesis.impact.lower() == "high"
    )
    test_first_count = sum(
        1 for hypothesis in hypotheses if hypothesis.priority.lower() == "test first"
    )

    if top_score >= 220 or (high_impact_count >= 2 and test_first_count >= 2):
        return "high"

    if top_score >= 150 or test_first_count >= 1:
        return "medium"

    return "low"


def _build_analyst_note(
    hypotheses: list[Hypothesis],
    overall_risk: str,
) -> str:
    if not hypotheses:
        return "No clear issue class was prioritized from the current exchange."

    top = hypotheses[0]

    if overall_risk == "high":
        return (
            f"Focus on '{top.title}' first. The current exchange shows strong indicators "
            f"that justify immediate manual verification."
        )

    if overall_risk == "medium":
        return (
            f"'{top.title}' is the best lead right now. The exchange contains meaningful "
            f"signals, but behavior still needs confirmation through manual testing."
        )

    return (
        f"'{top.title}' is worth a quick check, but the current exchange alone does not "
        f"show a strong concentration of high-risk indicators."
    )