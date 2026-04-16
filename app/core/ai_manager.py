import json
import subprocess
import urllib.error
import urllib.request

from app.models.ai_models import AIConnectionStatus, AISettings, AISuggestionResult
from app.models.analysis_models import ExtractionResult, ScoredAnalysisResult
from app.models.http_models import HTTPRequest, HTTPResponse
from app.utils.ai_utils import load_ai_settings, save_ai_settings


class AIManager:
    def __init__(self, settings_file_path: str):
        self.settings_file_path = settings_file_path
        self.settings = load_ai_settings(settings_file_path)

    def get_settings(self) -> AISettings:
        return self.settings

    def save_settings(self, settings: AISettings) -> None:
        self.settings = settings
        save_ai_settings(self.settings_file_path, settings)

    def generate_suggestions(
        self,
        project_name: str,
        request: HTTPRequest,
        response: HTTPResponse | None,
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        suggested_tags: list[str],
    ) -> AISuggestionResult:
        if self.settings.mode == "disabled":
            return AISuggestionResult(
                enabled=False,
                provider="disabled",
                model_name="",
                success=False,
                content="AI is disabled.",
                error_message="",
            )

        if self.settings.mode == "builtin":
            content = self._generate_builtin_suggestions(
                project_name=project_name,
                request=request,
                response=response,
                extraction=extraction,
                scored_result=scored_result,
                suggested_tags=suggested_tags,
            )
            return AISuggestionResult(
                enabled=True,
                provider="builtin",
                model_name=self.settings.builtin_profile,
                success=True,
                content=content,
                error_message="",
            )

        if self.settings.mode == "ollama":
            return self._generate_ollama_suggestions(
                project_name=project_name,
                request=request,
                response=response,
                extraction=extraction,
                scored_result=scored_result,
                suggested_tags=suggested_tags,
            )

        return AISuggestionResult(
            enabled=False,
            provider="unknown",
            model_name="",
            success=False,
            content="",
            error_message=f"Unsupported AI mode: {self.settings.mode}",
        )

    def get_recommended_ollama_models(self) -> list[str]:
        return [
            "qwen3:0.6b",
            "qwen3:1.7b",
            "qwen3:4b",
            "qwen3:8b",
            "qwen2.5:0.5b",
            "qwen2.5:1.5b",
            "qwen2.5:3b",
            "qwen2.5:7b",
            "qwen2.5-coder:0.5b",
            "qwen2.5-coder:1.5b",
            "qwen2.5-coder:3b",
            "qwen2.5-coder:7b",
            "gemma3:1b",
            "gemma3:4b",
            "gemma3:12b",
        ]

    def get_ollama_install_command(self, model_name: str) -> str:
        model_name = model_name.strip() or self.settings.ollama_model
        return f"curl -fsSL https://ollama.com/install.sh | sh && ollama pull {model_name}"

    def test_connection(self) -> AIConnectionStatus:
        if self.settings.mode == "disabled":
            return AIConnectionStatus(
                provider="disabled",
                success=False,
                message="AI is disabled.",
                available_models=[],
            )

        if self.settings.mode == "builtin":
            return AIConnectionStatus(
                provider="builtin",
                success=True,
                message=f"Built-in AI is ready with profile '{self.settings.builtin_profile}'.",
                available_models=["rulepack-small", "rulepack-extended"],
            )

        if self.settings.mode == "ollama":
            return self._test_ollama_connection()

        return AIConnectionStatus(
            provider="unknown",
            success=False,
            message=f"Unsupported AI mode: {self.settings.mode}",
            available_models=[],
        )

    def pull_ollama_model(self, model_name: str) -> tuple[bool, str]:
        model_name = model_name.strip() or self.settings.ollama_model

        try:
            process = subprocess.run(
                ["ollama", "pull", model_name],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return False, "The 'ollama' command was not found on this system."
        except Exception as exc:
            return False, f"Ollama pull failed to start: {exc}"

        stdout = (process.stdout or "").strip()
        stderr = (process.stderr or "").strip()

        if process.returncode == 0:
            message = stdout if stdout else f"Model '{model_name}' pulled successfully."
            return True, message

        error_message = stderr or stdout or f"ollama pull exited with code {process.returncode}"
        return False, error_message

    def _test_ollama_connection(self) -> AIConnectionStatus:
        host = self.settings.ollama_host.rstrip("/")

        version_url = f"{host}/api/version"
        tags_url = f"{host}/api/tags"

        try:
            version_request = urllib.request.Request(version_url, method="GET")
            with urllib.request.urlopen(version_request, timeout=10) as response_obj:
                response_text = response_obj.read().decode("utf-8")
                version_json = json.loads(response_text)

            tags_request = urllib.request.Request(tags_url, method="GET")
            with urllib.request.urlopen(tags_request, timeout=15) as response_obj:
                response_text = response_obj.read().decode("utf-8")
                tags_json = json.loads(response_text)

            models = []
            for item in tags_json.get("models", []):
                model_name = item.get("name", "").strip()
                if model_name:
                    models.append(model_name)

            version = version_json.get("version", "unknown")

            return AIConnectionStatus(
                provider="ollama",
                success=True,
                message=f"Ollama is reachable. Version: {version}",
                available_models=models,
            )
        except urllib.error.URLError as exc:
            return AIConnectionStatus(
                provider="ollama",
                success=False,
                message=f"Ollama connection failed: {exc}",
                available_models=[],
            )
        except Exception as exc:
            return AIConnectionStatus(
                provider="ollama",
                success=False,
                message=f"Ollama test failed: {exc}",
                available_models=[],
            )

    def _generate_builtin_suggestions(
        self,
        project_name: str,
        request: HTTPRequest,
        response: HTTPResponse | None,
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        suggested_tags: list[str],
    ) -> str:
        lines: list[str] = []

        lines.append(f"Project: {project_name}")
        lines.append(f"Request: {request.method} {request.path}")
        lines.append(f"Overall risk: {scored_result.summary.overall_risk}")
        if response is not None:
            lines.append(f"Response status: {response.status_code}")
        else:
            lines.append("Response status: no response")
        lines.append("")

        lines.append("Suggested next actions:")
        if not scored_result.hypotheses:
            lines.append("- No strong issue class was found. Compare this request with a nearby endpoint or a modified identifier.")
        else:
            for hypothesis in scored_result.hypotheses[:5]:
                lines.append(f"- {hypothesis.title}")
                for test in hypothesis.recommended_tests[:3]:
                    lines.append(f"  • {test}")

        lines.append("")
        lines.append("What to compare next:")
        lines.append("- Compare this request with the same endpoint using another owned test object.")
        lines.append("- Compare authorized vs unauthorized-looking identifiers.")
        lines.append("- Compare response status, length, and returned JSON keys.")
        lines.append("- Save the interesting entries with notes and tags.")

        if suggested_tags:
            lines.append("")
            lines.append("Useful tags:")
            lines.append("- " + ", ".join(suggested_tags))

        return "\n".join(lines)

    def _generate_ollama_suggestions(
        self,
        project_name: str,
        request: HTTPRequest,
        response: HTTPResponse | None,
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        suggested_tags: list[str],
    ) -> AISuggestionResult:
        prompt = self._build_ollama_prompt(
            project_name=project_name,
            request=request,
            response=response,
            extraction=extraction,
            scored_result=scored_result,
            suggested_tags=suggested_tags,
        )

        host = self.settings.ollama_host.rstrip("/")
        url = f"{host}/api/generate"

        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
        }

        request_data = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            url=url,
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(http_request, timeout=120) as response_obj:
                response_text = response_obj.read().decode("utf-8")
                response_json = json.loads(response_text)
                content = response_json.get("response", "").strip()

                return AISuggestionResult(
                    enabled=True,
                    provider="ollama",
                    model_name=self.settings.ollama_model,
                    success=True,
                    content=content,
                    error_message="",
                )
        except urllib.error.URLError as exc:
            return AISuggestionResult(
                enabled=True,
                provider="ollama",
                model_name=self.settings.ollama_model,
                success=False,
                content="",
                error_message=f"Ollama connection failed: {exc}",
            )
        except Exception as exc:
            return AISuggestionResult(
                enabled=True,
                provider="ollama",
                model_name=self.settings.ollama_model,
                success=False,
                content="",
                error_message=f"Ollama generation failed: {exc}",
            )

    def _build_ollama_prompt(
        self,
        project_name: str,
        request: HTTPRequest,
        response: HTTPResponse | None,
        extraction: ExtractionResult,
        scored_result: ScoredAnalysisResult,
        suggested_tags: list[str],
    ) -> str:
        lines: list[str] = []

        lines.append("You are HuntPilot AI, an assistant for a bug bounty researcher reviewing captured web/API traffic.")
        lines.append("Your role is to suggest the next manual actions to test based on the current analysis.")
        lines.append("Do not claim a vulnerability is confirmed.")
        lines.append("Do not provide exploitation steps.")
        lines.append("Focus on safe analyst guidance: what to compare next, what to inspect, and what to prioritize.")
        lines.append("")
        lines.append(f"Project: {project_name}")
        lines.append(f"Request method: {request.method}")
        lines.append(f"Request path: {request.path}")
        lines.append(f"Overall risk: {scored_result.summary.overall_risk}")
        lines.append(f"Top issue titles: {', '.join(scored_result.summary.top_issue_titles) if scored_result.summary.top_issue_titles else 'none'}")
        lines.append(f"Suggested tags: {', '.join(suggested_tags) if suggested_tags else 'none'}")

        if response is not None:
            lines.append(f"Response status: {response.status_code}")
            lines.append(f"Response content-type: {response.content_type or 'none'}")
        else:
            lines.append("Response status: none")

        lines.append("")
        lines.append("Top hypotheses:")
        if scored_result.hypotheses:
            for hypothesis in scored_result.hypotheses[:5]:
                lines.append(
                    f"- {hypothesis.title} | issue_type={hypothesis.issue_type} | "
                    f"confidence={hypothesis.confidence} | priority={hypothesis.priority} | "
                    f"impact={hypothesis.impact} | effort={hypothesis.effort}"
                )
                if hypothesis.evidence:
                    lines.append(f"  evidence: {' ; '.join(hypothesis.evidence[:5])}")
        else:
            lines.append("- none")

        lines.append("")
        lines.append("Return a concise answer with these sections:")
        lines.append("1. Best next actions")
        lines.append("2. What to compare")
        lines.append("3. What would increase confidence")
        lines.append("4. Short priority recommendation")

        return "\n".join(lines)