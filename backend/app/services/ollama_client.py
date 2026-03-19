from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Dict, List

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Async client for the Ollama LLM service."""

    def __init__(self):
        self.base_url = settings.ollama_host
        self.model = settings.llm_model

    async def check_health(self) -> Dict:
        """GET /api/tags — returns info about loaded models."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            return resp.json()

    async def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available in Ollama."""
        try:
            data = await self.check_health()
            loaded = [m["name"] for m in data.get("models", [])]
            return any(model_name in m for m in loaded)
        except Exception:
            return False

    async def stream_chat(
        self,
        messages: List[Dict],
        system_prompt: str = "",
    ) -> AsyncIterator[str]:
        """
        POST /api/chat with stream=true.
        Yields text tokens as they arrive (parsed from NDJSON response).
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue


# Module-level singleton
ollama_client = OllamaClient()
