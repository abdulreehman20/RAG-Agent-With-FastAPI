# FastAPI RAG Agent

An async **FastAPI** backend that combines **JWT authentication**, **PostgreSQL (Neon)**, and a full **Retrieval-Augmented Generation (RAG)** stack. Ingest content from websites, store vector embeddings in **Qdrant**, and answer user questions with **Google Gemini** using retrieved context.

---

## What is this project?

This is a production-style API for building **AI assistants over your own data**. You can:

1. **Ingest** a website or blog URL — scrape content, split it into chunks, embed it, and save vectors to Qdrant.
2. **Query** — ask natural-language questions; the system retrieves relevant chunks and generates grounded answers with Gemini.

It also includes **user signup/login** and **CRUD** for user accounts, so RAG features can sit behind authenticated APIs in real applications.

---

## Why use it?

| Benefit | Description |
|--------|-------------|
| **Grounded answers** | RAG reduces hallucinations by answering from your ingested documents, not only the model’s training data. |
| **Fresh knowledge** | Add or re-ingest URLs anytime; no need to retrain a model. |
| **Modular stack** | Clear separation: API routes → services → agents → vector store. |
| **Async-first** | FastAPI + async SQLAlchemy for scalable I/O-bound workloads. |
| **Cloud-ready** | Works with Neon Postgres, Qdrant Cloud, Google Gemini API, and Hyperbrowser for scraping. |

---

## Tech stack

- **API:** FastAPI, Pydantic, Uvicorn  
- **Auth:** JWT (python-jose), bcrypt  
- **Database:** SQLModel / SQLAlchemy, asyncpg, Neon PostgreSQL  
- **RAG:** LangChain, Google Gemini (chat + embeddings), Qdrant  
- **Ingestion:** HyperbrowserLoader (web scraping)  
- **Tooling:** uv, pytest  

---

## Prerequisites

Before you start, install:

| Requirement | Version / notes |
|-------------|-----------------|
| [Python](https://www.python.org/downloads/) | **3.13+** |
| [uv](https://docs.astral.sh/uv/) | Package manager (recommended) |
| PostgreSQL | [Neon](https://neon.tech) serverless Postgres (or any Postgres with `asyncpg` URL) |
| Qdrant | [Qdrant Cloud](https://cloud.qdrant.io) or local Qdrant on port `6333` |
| Google AI API key | [Google AI Studio](https://aistudio.google.com/apikey) — Gemini chat + embeddings |
| Hyperbrowser API key | [Hyperbrowser](https://app.hyperbrowser.ai/) — required for URL ingestion |

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

Edit `.env` in the **project root** and set at minimum:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Long random string for JWT signing |
| `GOOGLE_API_KEY` | Gemini API key |
| `QDRANT_URL` | Qdrant endpoint (cloud: `https://xxx.cloud.qdrant.io` — **no `:6333`**) |
| `QDRANT_API_KEY` | Qdrant API key |
| `HYPERBROWSER_API_KEY` | Required for `/rag/ingest-data` |

> **Never commit `.env`.** It is listed in `.gitignore`.

### 4. (Optional) Create the Qdrant collection

The app auto-creates the collection on first ingest. If you change `VECTOR_SIZE` or embedding model dimensions, delete the old collection in Qdrant and ingest again.

---

## Run the server

From the project root:

```bash
uv run python -m uvicorn app.main:app --reload --app-dir src/app
```

- **API:** http://127.0.0.1:8000  
- **Swagger UI:** http://127.0.0.1:8000/docs  
- **Health check:** http://127.0.0.1:8000/health  

On Windows, if `fastapi dev` is blocked by Application Control, use the `uvicorn` command above.

---

## Streamlit UI

A browser UI lives in `src/streamlit/` and talks to the FastAPI backend over HTTP.

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

1. **Login / Sign up** — uses `POST /api/v1/auth/login` and `POST /api/v1/auth/signup`
2. **Sidebar** — paste a website URL and click **Ingest URL** (`POST /api/v1/rag/ingest-data`)
3. **Chat** — ask questions in the main area (`POST /api/v1/rag/query-data`)

Optional env var (in `.env` or shell):

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_BASE_URL` | `http://127.0.0.1:8000` | FastAPI base URL for the UI |
| `STREAMLIT_INGEST_TIMEOUT` | `600` | Seconds to wait for ingestion |
| `STREAMLIT_QUERY_TIMEOUT` | `120` | Seconds to wait for RAG answers |

### Run agent scripts directly

```bash
uv run python src/app/agents/embeddings.py
uv run python src/app/agents/agent.py
uv run python src/app/agents/ingestion_pipline.py
```

---

## API overview

Base path: `/api/v1`

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/signup` | Register a new user |
| `POST` | `/auth/login` | Login and receive JWT |
| `GET` | `/auth/me` | Current user (Bearer token) |

### Users (authenticated)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/list-users` | List users |
| `GET` | `/users/{user_id}` | Get user by ID |
| `PUT` | `/users/{user_id}` | Update user |
| `DELETE` | `/users/{user_id}` | Soft-delete user |

### RAG

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/rag/rag-test` | Health check for RAG router |
| `POST` | `/rag/ingest-data` | Ingest a URL into Qdrant |
| `POST` | `/rag/query-data` | Ask a question (RAG answer) |

**Ingest example:**

```json
POST /api/v1/rag/ingest-data
{
  "url": "https://example.com/blog/your-article"
}
```

**Query example:**

```json
POST /api/v1/rag/query-data
{
  "question": "What is retrieval-augmented generation?"
}
```

---

## How RAG works in this project

```
URL  →  HyperbrowserLoader (scrape)
     →  RecursiveCharacterTextSplitter (chunks)
     →  Google embeddings (768-dim)
     →  Qdrant vector store

Question  →  Similarity search (top-k chunks)
          →  Gemini + context prompt
          →  Grounded answer
```

**Embedding defaults** live in `src/app/core/config.py`:

- `PROJECT_EMBEDDING_MODEL_ID` = `models/gemini-embedding-001`
- `PROJECT_EMBEDDING_VECTOR_DIMENSIONS` = `768`

Keep these aligned in `.env`:

- `EMBEDDING_MODEL`
- `EMBEDDING_OUTPUT_DIMENSIONALITY`
- `VECTOR_SIZE`

If you change dimensions, **delete and recreate** the Qdrant collection (or use a new `COLLECTION_NAME`).

---

## Testing

```bash
uv run pytest tests/ -v
```

Tests use an isolated SQLite database and mock RAG external calls — they do not require live Qdrant or Gemini for the API route tests.

---

## Project structure

```
src/
├── app/             # FastAPI backend
│   ├── api/v1/      # Routes (auth, users, rag)
│   ├── agents/      # LangChain: ingestion, retrieval, LLM, agent
│   └── ...
└── streamlit/       # Streamlit UI (app.py, api_client.py, config.py)
tests/               # pytest suite
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ValidationError` for missing env vars | Create `.env` from `.env.example` in project root |
| Qdrant timeout on ingest | Use cloud URL without `:6333`; increase `QDRANT_TIMEOUT`; lower `QDRANT_UPSERT_BATCH_SIZE` |
| Gemini `404` model not found | Set `GEMINI_MODEL=models/gemini-2.5-flash` |
| `coroutine was never awaited` | Use `asyncio.run()` when calling async pipeline functions from scripts |
| Windows blocks `fastapi.exe` | Use `uv run python -m uvicorn ...` |

---

## License

See repository license. Use API keys responsibly and rotate any keys that were ever committed to git.
