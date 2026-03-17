from __future__ import annotations

import logging
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Singleton service for generating text embeddings using FastEmbed (nomic-embed-text)."""

    _instance: "EmbeddingService | None" = None
    _model = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_model(self):
        if self._model is None:
            logger.info("Loading nomic-embed-text embedding model (first call)...")
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name="nomic-embed-text")
            logger.info("Embedding model loaded and cached.")
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        model = self._get_model()
        embeddings = list(model.embed(texts))
        return [list(e) for e in embeddings]

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query string."""
        return self.embed_texts([text])[0]


# Module-level singleton
embedding_service = EmbeddingService()
