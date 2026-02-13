"""
Embedding service for vectorization endpoints.
"""
import os
import time
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)


@dataclass
class EmbeddingConfig:
    MODEL: str = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    DIMENSIONS: int = int(os.getenv('EMBEDDING_DIMENSIONS', 1024))
    MAX_RETRIES: int = int(os.getenv('OPENAI_EMBEDDING_MAX_RETRIES', 3))
    TIMEOUT_SECONDS: int = int(os.getenv('OPENAI_EMBEDDING_TIMEOUT_SECONDS', 60))


class EmbeddingService:
    """Service for generating embeddings using OpenAI."""

    def __init__(self, api_key: Optional[str] = None):
        self.config = EmbeddingConfig()
        self.api_key = api_key or self.config.API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        self.client = OpenAI(
            api_key=self.api_key,
            timeout=self.config.TIMEOUT_SECONDS,
            max_retries=self.config.MAX_RETRIES
        )

    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        target_dim = self.config.DIMENSIONS
        if len(embedding) == target_dim:
            return embedding
        if len(embedding) > target_dim:
            return embedding[:target_dim]
        return embedding + [0.0] * (target_dim - len(embedding))

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        cleaned = [(text or '').strip() for text in texts]
        safe_texts = [text if text else ' ' for text in cleaned]

        attempt = 0
        backoff = 1.0
        while attempt <= self.config.MAX_RETRIES:
            try:
                response = self.client.embeddings.create(
                    model=self.config.MODEL,
                    input=safe_texts,
                    dimensions=self.config.DIMENSIONS
                )
                embeddings = [item.embedding for item in response.data]
                while len(embeddings) < len(texts):
                    embeddings.append([0.0] * self.config.DIMENSIONS)
                return [self._normalize_embedding(emb) for emb in embeddings]
            except Exception:
                attempt += 1
                if attempt > self.config.MAX_RETRIES:
                    break
                time.sleep(backoff)
                backoff = min(backoff * 2, 10)

        return [[0.0] * self.config.DIMENSIONS for _ in texts]


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
