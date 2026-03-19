from typing import Any, Dict, List

import httpx
from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    qdrant_status = "unreachable"
    ollama_status = "unreachable"
    models_loaded: List[str] = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check Qdrant
        try:
            resp = await client.get(f"{settings.qdrant_host}/healthz")
            if resp.status_code == 200:
                qdrant_status = "connected"
        except Exception:
            pass

        # Check Ollama and list loaded models
        try:
            resp = await client.get(f"{settings.ollama_host}/api/tags")
            if resp.status_code == 200:
                ollama_status = "connected"
                data = resp.json()
                models_loaded = [m["name"] for m in data.get("models", [])]
        except Exception:
            pass

    overall = "ok" if qdrant_status == "connected" and ollama_status == "connected" else "degraded"

    return {
        "status": overall,
        "qdrant": qdrant_status,
        "ollama": ollama_status,
        "models_loaded": models_loaded,
    }
