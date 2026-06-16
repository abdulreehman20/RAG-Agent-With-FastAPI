from __future__ import annotations

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import PROJECT_EMBEDDING_MODEL_ID, get_settings


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Google Generative AI embeddings configured from settings."""

    settings = get_settings()
    api_key = settings.google_api_key
    embedding_model = settings.embedding_model

    if isinstance(api_key, str) and api_key.strip() == "":
        raise ValueError("GOOGLE_API_KEY is not set")

    if isinstance(embedding_model, str) and embedding_model.strip() == "":
        raise ValueError(
            "EMBEDDING_MODEL is empty. Set EMBEDDING_MODEL in .env (default in code: "
            f"{PROJECT_EMBEDDING_MODEL_ID})."
        )

    dims = settings.embedding_output_dimensionality
    kwargs: dict[str, object] = {
        "model": embedding_model,
        "api_key": api_key,
        "output_dimensionality": dims,
    }
    return GoogleGenerativeAIEmbeddings(**kwargs)


# Test this function by generating embeddings for a test text
if __name__ == "__main__":
    print(f"Get embeddings: {get_embeddings().embed_query('Hello, world!')}")
