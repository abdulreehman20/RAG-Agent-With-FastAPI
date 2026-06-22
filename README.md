# FastAPI RAG Agent

An async **FastAPI** backend with **JWT authentication**, **PostgreSQL (Neon)**, and a full **Retrieval-Augmented Generation (RAG)** pipeline. Scrape website content with **Hyperbrowser**, store embeddings in **Qdrant**, and answer questions with **Google Gemini**. Includes a **Streamlit** chat UI that talks to the API over HTTP.

---

## What is this project?

This is a production-style API for building **AI assistants over your own data**:

1. **Ingest** — scrape a URL, split it into chunks, embed with Gemini, and upsert vectors into Qdrant.
2. **Query** — ask natural-language questions; the system retrieves relevant chunks and generates grounded answers.
3. **Authenticate** — signup, login, and user CRUD backed by Neon Postgres and JWT.

The Streamlit app (`src/streamlit/`) provides login/signup, a sidebar to ingest URLs, and a chat interface for RAG Q&A.

---

## Why use it?

| Benefit | Description |
|--------|-------------|
| **Grounded answers** | RAG reduces hallucinations by answering from ingested documents, not only the model’s training data. |
| **Fresh knowledge** | Re-ingest URLs anytime — no model retraining required. |
| **Modular stack** | Clear layers: API routes → services → agents → vector store / database. |
| **Async-first** | FastAPI + async SQLAlchemy for scalable I/O-bound workloads. |
| **Cloud-ready** | Neon Postgres, Qdrant Cloud, Google Gemini API, and Hyperbrowser scraping. |
| **Browser UI included** | Streamlit frontend for auth, ingestion, and chat without writing a separate client. |

---

## Tech stack

| Layer | Tools |
|-------|-------|
| **API** | FastAPI, Pydantic, Uvicorn |
| **Auth** | JWT (python-jose), bcrypt |
| **Database** | SQLModel / SQLAlchemy, asyncpg, Neon PostgreSQL |
| **RAG** | LangChain (LCEL), Google Gemini (chat + embeddings), Qdrant |
| **Ingestion** | HyperbrowserLoader, RecursiveCharacterTextSplitter |
| **UI** | Streamlit, httpx |
| **Tooling** | uv, pytest, ruff |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| [Python](https://www.python.org/downloads/) | **3.13+** |
| [uv](https://docs.astral.sh/uv/) | Recommended package manager |
| PostgreSQL | [Neon](https://neon.tech) or any Postgres with an `asyncpg` URL |
| Qdrant | [Qdrant Cloud](https://cloud.qdrant.io) or local Qdrant on port `6333` |
| Google AI API key | [Google AI Studio](https://aistudio.google.com/apikey) — Gemini chat + embeddings |
| Hyperbrowser API key | [Hyperbrowser](https://app.hyperbrowser.ai/) — **required for URL ingestion** |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/abdulreehman20/RAG-Agent-With-FastAPI.git
cd fastapi-rag-agent
```

### 2. Install dependencies

```bash
uv sync --extra dev
```

This installs the project in **editable** mode so `import app` works from anywhere in the repo.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` in the **project root**. Required variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Long random string for JWT signing |
| `GOOGLE_API_KEY` | Gemini API key (chat + embeddings) |
| `QDRANT_URL` | Qdrant endpoint (cloud: `https://xxx.cloud.qdrant.io` — **no `:6333`**) |
| `QDRANT_API_KEY` | Qdrant API key |
| `HYPERBROWSER_API_KEY` | Required for `POST /rag/ingest-data` |

Optional tuning (defaults shown in `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_MODEL` | `models/gemini-2.5-flash` | Chat model (retired `gemini-1.5-*` ids are auto-mapped) |
| `GEMINI_TEMPERATURE` | `0.2` | LLM temperature |
| `GEMINI_MAX_OUTPUT_TOKENS` | `2048` | Max tokens per answer |
| `EMBEDDING_MODEL` | `models/gemini-embedding-001` | Embedding model id |
| `EMBEDDING_OUTPUT_DIMENSIONALITY` | `768` | Must equal `VECTOR_SIZE` |
| `VECTOR_SIZE` | `768` | Qdrant dense vector dimensions |
| `COLLECTION_NAME` | `rag_collection` | Qdrant collection name |
| `DISTANCE` | `COSINE` | Qdrant distance metric |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `200` | Text splitter settings |
| `RAG_RETRIEVAL_K` | `4` | Top-k chunks retrieved per question |
| `QDRANT_TIMEOUT` | `120` | Qdrant HTTP timeout (seconds) |
| `QDRANT_UPSERT_BATCH_SIZE` | `16` | Points per upsert batch during ingest |
| `HYPERBROWSER_OPERATION` | `scrape` | `scrape` (one or many URLs) or `crawl` (single seed URL) |

> **Never commit `.env`.** It is listed in `.gitignore`.  
> **Restart the API** after changing `.env` — settings are loaded at startup.

Embedding defaults are defined as constants in `src/app/core/config.py`:

- `PROJECT_EMBEDDING_MODEL_ID` = `models/gemini-embedding-001`
- `PROJECT_EMBEDDING_VECTOR_DIMENSIONS` = `768`
- `PROJECT_GEMINI_CHAT_MODEL_ID` = `models/gemini-2.5-flash`

Keep `EMBEDDING_MODEL`, `EMBEDDING_OUTPUT_DIMENSIONALITY`, and `VECTOR_SIZE` aligned. If you change dimensions, delete the old Qdrant collection (or use a new `COLLECTION_NAME`) and re-ingest.

### 4. Qdrant collection

The app auto-creates the collection on first ingest via `ensure_collection_exists()` in `src/app/db/vector_store.py`.

---

## Run the API

From the project root:

```bash
uv run python -m uvicorn app.main:app --reload --app-dir src/app
```

Or, if your environment allows it:

```bash
fastapi dev src/app/main.py
```

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8000 | API root |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/health | Health check |

On Windows, if `fastapi.exe` / `uvicorn.exe` is blocked by Application Control, use the `uv run python -m uvicorn ...` command.

Tables are created automatically on startup via SQLModel (`init_db()` in the app lifespan).

---

## Streamlit UI

A browser UI lives in `src/streamlit/` and calls the FastAPI backend over HTTP.

### 1. Start the API (terminal 1)

```bash
uv run python -m uvicorn app.main:app --reload --app-dir src/app
```

### 2. Start Streamlit (terminal 2)

```bash
uv run streamlit run src/streamlit/app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

### UI flow

1. **Login / Sign up** — `POST /api/v1/auth/login` and `POST /api/v1/auth/signup`
2. **Sidebar → Ingest URL** — `POST /api/v1/rag/ingest-data` (scraping can take 1–3 minutes)
3. **Chat** — `POST /api/v1/rag/query-data`

Streamlit env vars (optional):

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_BASE_URL` | `http://127.0.0.1:8000` | FastAPI base URL |
| `STREAMLIT_INGEST_TIMEOUT` | `600` | HTTP timeout for ingestion (seconds) |
| `STREAMLIT_QUERY_TIMEOUT` | `120` | HTTP timeout for RAG answers (seconds) |
| `STREAMLIT_AUTH_TIMEOUT` | `30` | HTTP timeout for auth requests (seconds) |

---

## API overview

Base path: `/api/v1`

### Auth

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/signup` | No | Register a new user |
| `POST` | `/auth/login` | No | Login and receive JWT |
| `GET` | `/auth/me` | Bearer | Current user profile |

### Users (authenticated)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/users/list-users` | Bearer | List users (`skip`, `limit`) |
| `GET` | `/users/{user_id}` | Bearer | Get user by ID |
| `PUT` | `/users/{user_id}` | Bearer | Update user |
| `DELETE` | `/users/{user_id}` | Bearer | Soft-delete user (`is_active = false`) |

### RAG

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/rag/rag-test` | No | RAG router health check |
| `POST` | `/rag/ingest-data` | No | Scrape URL → chunk → embed → Qdrant |
| `POST` | `/rag/query-data` | No | RAG question answering |

> **Note:** RAG endpoints are currently **public** (no JWT required). The Streamlit UI sends a Bearer token, but the API does not enforce it on `/rag/*`. User routes and `/auth/me` do require authentication.

**Ingest request:**

```http
POST /api/v1/rag/ingest-data
Content-Type: application/json

{
  "url": "https://example.com/blog/your-article"
}
```

**Ingest response (201):**

```json
{
  "url": "https://example.com/blog/your-article",
  "documents_loaded": 1,
  "chunks_created": 12,
  "chunks_saved": 12,
  "collection": "rag_collection"
}
```

**Query request:**

```http
POST /api/v1/rag/query-data
Content-Type: application/json

{
  "question": "What is retrieval-augmented generation?"
}
```

**Query response (200):**

```json
{
  "question": "What is retrieval-augmented generation?",
  "answer": "..."
}
```

In Swagger, click **Authorize** → paste the `access_token` from `/auth/login` to call protected user endpoints.

---

## How RAG works

```
URL  →  HyperbrowserLoader (scrape / crawl)
     →  RecursiveCharacterTextSplitter (chunks)
     →  Google Gemini embeddings (768-dim)
     →  Qdrant upsert (batched)

Question  →  Qdrant similarity search (top-k)
          →  LCEL chain: prompt | Gemini chat | StrOutputParser
          →  Grounded answer
```

### Code layout

| File | Role |
|------|------|
| `src/app/agents/ingestion_pipline.py` | 3-stage ingest: load → chunk → embed + upsert |
| `src/app/agents/retrieval.py` | Qdrant retriever (`rag_retrieval_k`) |
| `src/app/agents/agent.py` | `ask_agent()` — retrieve + generate |
| `src/app/agents/prompts.py` | QA prompt template |
| `src/app/agents/llm.py` | `ChatGoogleGenerativeAI` factory |
| `src/app/agents/embeddings.py` | Gemini embedding model |
| `src/app/db/vector_store.py` | Qdrant client, collection creation, batched upsert |
| `src/app/services/rag_service.py` | Service layer for ingest + query |
| `src/app/api/v1/rag.py` | HTTP routes + Qdrant error handling |

### Run agent scripts directly

```bash
uv run python src/app/agents/ingestion_pipline.py
uv run python src/app/agents/agent.py
uv run python src/app/agents/embeddings.py
```

The ingestion script uses a hardcoded sample URL in its `__main__` block. For batch CLI ingest from `.env`, set `RAG_INGEST_URLS` (comma-separated) and extend the script as needed.

---

## Testing

```bash
uv run pytest tests/ -v
```

**17 tests** across auth, user CRUD, and RAG routes. Tests use an isolated SQLite database (`tests/conftest.py`) and mock external RAG calls — they do not require live Qdrant, Gemini, or Hyperbrowser.

---

## Project structure

```
fastapi-rag-agent/
├── src/
│   ├── app/                      # FastAPI backend (installable package)
│   │   ├── main.py               # App factory, CORS, lifespan, /health
│   │   ├── api/v1/
│   │   │   ├── router.py         # Mounts auth, users, rag routers
│   │   │   ├── auth.py           # Signup, login, /me, JWT dependency
│   │   │   ├── users.py          # User CRUD (authenticated)
│   │   │   └── rag.py            # Ingest + query endpoints
│   │   ├── agents/               # LangChain RAG pipeline
│   │   │   ├── ingestion_pipline.py
│   │   │   ├── agent.py
│   │   │   ├── retrieval.py
│   │   │   ├── embeddings.py
│   │   │   ├── llm.py
│   │   │   └── prompts.py
│   │   ├── core/
│   │   │   ├── config.py         # Settings + PROJECT_* constants
│   │   │   └── security.py       # JWT + password hashing
│   │   ├── db/
│   │   │   ├── session.py        # Async SQLAlchemy engine + init_db
│   │   │   └── vector_store.py   # Qdrant client + upsert
│   │   ├── models/user.py        # SQLModel User table
│   │   ├── schemas/              # Pydantic request/response models
│   │   └── services/             # Business logic (user, rag)
│   └── streamlit/
│       ├── app.py                # Login, ingest sidebar, chat UI
│       ├── api_client.py         # httpx client for FastAPI
│       └── config.py             # API URL + timeouts
├── tests/                        # pytest (auth, users, rag)
├── .env.example                  # Environment template
└── pyproject.toml                # uv / hatch / pytest config
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ValidationError` for missing env vars | Copy `.env.example` → `.env` in project root and fill required keys |
| `HYPERBROWSER_API_KEY is not set` on ingest | Add key from [Hyperbrowser](https://app.hyperbrowser.ai/) to `.env`, restart API |
| Qdrant timeout on ingest | Use cloud URL without `:6333`; increase `QDRANT_TIMEOUT`; lower `QDRANT_UPSERT_BATCH_SIZE` |
| `VECTOR_SIZE` / `EMBEDDING_OUTPUT_DIMENSIONALITY` mismatch | Set both to the same value (default `768`) or update `PROJECT_*` in `config.py` |
| Gemini `404` model not found | Set `GEMINI_MODEL=models/gemini-2.5-flash` |
| Empty or wrong RAG answers | Ingest a URL first; check Qdrant collection has points |
| `coroutine was never awaited` | Use `asyncio.run()` when calling async pipeline functions from scripts |
| Windows blocks `fastapi.exe` | Use `uv run python -m uvicorn app.main:app --reload --app-dir src/app` |
| Streamlit ingest fails but API works | Ensure API is running on `API_BASE_URL`; check `STREAMLIT_INGEST_TIMEOUT` for slow scrapes |

---

## License

See repository license. Use API keys responsibly and rotate any keys that were ever committed to git.
