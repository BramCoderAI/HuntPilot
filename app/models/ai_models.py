from dataclasses import dataclass, field
from typing import List


@dataclass
class AISettings:
    mode: str = "disabled"              # disabled | builtin | ollama
    builtin_profile: str = "rulepack-small"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen3:1.7b"
    auto_suggest_after_analysis: bool = False


@dataclass
class AISuggestionResult:
    enabled: bool = False
    provider: str = ""
    model_name: str = ""
    success: bool = False
    content: str = ""
    error_message: str = ""


@dataclass
class AIPromptContext:
    project_name: str
    request_method: str
    request_path: str
    response_status: str
    overall_risk: str
    top_issue_titles: List[str] = field(default_factory=list)
    suggested_tags: List[str] = field(default_factory=list)


@dataclass
class AIConnectionStatus:
    provider: str = ""
    success: bool = False
    message: str = ""
    available_models: List[str] = field(default_factory=list)