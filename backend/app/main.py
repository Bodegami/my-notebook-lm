from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_db_and_tables

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up RAG Library backend...")
    create_db_and_tables()
    logger.info("Database initialized.")

    # Verify Qdrant connection
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.qdrant_host}/healthz")
            resp.raise_for_status()
        logger.info("Qdrant connection verified.")
    except Exception as e:
        logger.warning(f"Qdrant not reachable at startup: {e}")

    # Verify Ollama connection
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_host}/api/tags")
            resp.raise_for_status()
        logger.info("Ollama connection verified.")
    except Exception as e:
        logger.warning(f"Ollama not reachable at startup: {e}")

    # Initialize Qdrant collection
    try:
        from app.services.vector_store import initialize_collection
        await initialize_collection()
        logger.info("Qdrant collection ready.")
    except Exception as e:
        logger.warning(f"Could not initialize Qdrant collection at startup: {e}")

    yield

    # Shutdown
    logger.info("Shutting down RAG Library backend.")


app = FastAPI(
    title="RAG Library API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import documents, chat, health  # noqa: E402

app.include_router(health.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
