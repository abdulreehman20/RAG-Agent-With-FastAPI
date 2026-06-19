from __future__ import annotations

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings


def get_chat_model() -> ChatGoogleGenerativeAI:
    """Gemini Chat Model configured from settings."""

    settings = get_settings()
    model = settings.gemini_model
    google_api_key = settings.google_api_key
    temperature = settings.gemini_temperature
    max_output_tokens = settings.gemini_max_output_tokens

    if isinstance(google_api_key, str) and google_api_key.strip() == "":
        raise ValueError("GOOGLE_API_KEY is not set")

    if isinstance(model, str) and model.strip() == "":
        raise ValueError("GEMINI_MODEL is not set")

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=google_api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
