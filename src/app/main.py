from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import init_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: database tables."""
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="FastAPI RAG Agent",
        version="0.1.0",
        description="Async FastAPI service with JWT auth, Neon/SQLModel, and LangChain RAG.",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["root"])
    async def home() -> dict[str, str]:
        return {"message": "Welcome to FastAPI RAG Agent"}

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
