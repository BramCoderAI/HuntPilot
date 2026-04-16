from app.models.ai_models import AISuggestionResult


def ai_suggestion_result_to_dict(result: AISuggestionResult | None) -> dict | None:
    if result is None:
        return None

    return {
        "enabled": result.enabled,
        "provider": result.provider,
        "model_name": result.model_name,
        "success": result.success,
        "content": result.content,
        "error_message": result.error_message,
    }


def ai_suggestion_result_from_dict(data: dict | None) -> AISuggestionResult | None:
    if not data:
        return None

    return AISuggestionResult(
        enabled=data.get("enabled", False),
        provider=data.get("provider", ""),
        model_name=data.get("model_name", ""),
        success=data.get("success", False),
        content=data.get("content", ""),
        error_message=data.get("error_message", ""),
    )