from dataclasses import dataclass, field
from typing import List


@dataclass
class ExtractedFinding:
    category: str
    name: str
    value: str
    source: str


@dataclass
class ExtractionResult:
    ids: List[ExtractedFinding] = field(default_factory=list)
    sensitive_fields: List[ExtractedFinding] = field(default_factory=list)
    auth_markers: List[ExtractedFinding] = field(default_factory=list)
    session_markers: List[ExtractedFinding] = field(default_factory=list)
    endpoint_markers: List[ExtractedFinding] = field(default_factory=list)
    content_markers: List[ExtractedFinding] = field(default_factory=list)
    response_markers: List[ExtractedFinding] = field(default_factory=list)


@dataclass
class DetectedSignal:
    name: str
    description: str
    severity: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class Hypothesis:
    issue_type: str
    title: str
    description: str
    rationale: str
    confidence: str
    priority: str
    recommended_tests: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    impact: str = "medium"
    effort: str = "medium"
    score: int = 0


@dataclass
class DetectionResult:
    signals: List[DetectedSignal] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)


@dataclass
class AnalysisSummary:
    total_signals: int = 0
    total_hypotheses: int = 0
    high_confidence_count: int = 0
    test_first_count: int = 0
    top_issue_titles: List[str] = field(default_factory=list)
    overall_risk: str = "low"
    analyst_note: str = ""


@dataclass
class ScoredAnalysisResult:
    signals: List[DetectedSignal] = field(default_factory=list)
    hypotheses: List[Hypothesis] = field(default_factory=list)
    summary: AnalysisSummary = field(default_factory=AnalysisSummary)