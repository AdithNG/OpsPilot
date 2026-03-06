from app.schemas.chat import Citation
from app.core.config import settings
from app.core.storage import storage
from app.services.embeddings import embeddings_provider


class RetrievalService:
    async def retrieve(self, query: str) -> list[Citation]:
        query_embedding = embeddings_provider.embed_query(query)
        candidates = storage.documents.search(
            query=query,
            query_embedding=query_embedding,
            limit=settings.retrieval_candidate_limit,
        )
        return self._rerank(query, candidates)[: settings.retrieval_limit]

    def _rerank(self, query: str, candidates: list[Citation]) -> list[Citation]:
        query_terms = self._tokenize(query)
        reranked: list[Citation] = []
        for candidate in candidates:
            lexical_score = self._lexical_overlap(
                query_terms,
                f"{candidate.title or ''} {candidate.snippet}",
            )
            prior_score = candidate.score or 0.0
            score = (lexical_score * 2.0) + prior_score
            reranked.append(candidate.model_copy(update={"score": score}))
        reranked.sort(key=lambda citation: citation.score or 0.0, reverse=True)
        return reranked

    def _lexical_overlap(self, query_terms: set[str], haystack: str) -> float:
        if not query_terms:
            return 0.0
        haystack_terms = self._tokenize(haystack)
        return len(query_terms & haystack_terms) / len(query_terms)

    def _tokenize(self, text: str) -> set[str]:
        normalized = "".join(character.lower() if character.isalnum() else " " for character in text)
        return {term for term in normalized.split() if len(term) > 2}
