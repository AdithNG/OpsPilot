from __future__ import annotations

import math
from hashlib import sha256

from langchain_core.embeddings import Embeddings

from app.core.config import settings


class LocalHashEmbeddings(Embeddings):
    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = self._tokenize(text)
        if not tokens:
            return vector
        for token in tokens:
            index = int(sha256(token.encode("utf-8")).hexdigest(), 16) % self.dimensions
            vector[index] += 1.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]

    def _tokenize(self, text: str) -> list[str]:
        normalized = "".join(character.lower() if character.isalnum() else " " for character in text)
        return [token for token in normalized.split() if len(token) > 2]


def get_embeddings_provider() -> Embeddings:
    # Cost-free by default. A paid provider can be added behind this switch later.
    if settings.embedding_provider == "local":
        return LocalHashEmbeddings(dimensions=settings.embedding_dimensions)
    return LocalHashEmbeddings(dimensions=settings.embedding_dimensions)


embeddings_provider = get_embeddings_provider()
