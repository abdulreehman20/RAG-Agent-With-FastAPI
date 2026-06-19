# fastapi-rag-agent

Async FastAPI service with auth, Neon/SQLModel, and RAG (Qdrant + LangChain).

## Run

```bash
uv sync
uv run python -m uvicorn app.main:app --reload --app-dir src/app
```

With `uv sync`, the `app` package is installed in editable mode, so you can run any file under `src/app` with:

```bash
uv run python src/app/agents/embeddings.py
```

Copy `.env.example` to `.env` and fill in secrets.

## RAG embeddings + Qdrant

Defaults live in `src/app/core/config.py` as **`PROJECT_EMBEDDING_MODEL_ID`** and **`PROJECT_EMBEDDING_VECTOR_DIMENSIONS`**.  
Keep **`EMBEDDING_MODEL`**, **`EMBEDDING_OUTPUT_DIMENSIONALITY`**, and **`VECTOR_SIZE`** the same in `.env`.  
If you change dimensions, **delete and recreate** the Qdrant collection (or use a new `COLLECTION_NAME`).

## Hyperbrowser ingestion

URL/blog ingestion uses [HyperbrowserLoader](https://docs.langchain.com/oss/python/integrations/document_loaders/hyperbrowser) (`langchain-hyperbrowser`). Set **`HYPERBROWSER_API_KEY`** and optional **`RAG_INGEST_URLS`** (comma-separated) in `.env`.

`pyproject.toml` includes a **`[tool.uv] override-dependencies`** entry for `langchain-core` because `langchain-hyperbrowser` still declares an older `langchain-core` range while this app uses LangChain 1.x (`langchain-google-genai`).
