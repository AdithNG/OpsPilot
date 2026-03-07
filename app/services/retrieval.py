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
        query_profile = self._infer_query_profile(query_terms)
        reranked: list[Citation] = []
        for candidate in candidates:
            lexical_score = self._lexical_overlap(
                query_terms,
                f"{candidate.title or ''} {candidate.snippet}",
            )
            prior_score = candidate.score or 0.0
            source_affinity = self._source_affinity(candidate, query_profile)
            score = (lexical_score * 2.0) + prior_score + source_affinity
            reranked.append(candidate.model_copy(update={"score": score}))
        reranked.sort(key=lambda citation: citation.score or 0.0, reverse=True)
        return reranked

    def _infer_query_profile(self, query_terms: set[str]) -> str:
        github_terms = {"github", "repo", "repository", "commit", "commits", "pull", "request", "requests", "pr", "readme"}
        ops_terms = {
            "deploy",
            "deployment",
            "rollback",
            "runbook",
            "incident",
            "outage",
            "health",
            "production",
            "service",
            "services",
            "stakeholders",
            "postmortem",
        }
        if query_terms & github_terms:
            return "github"
        if query_terms & ops_terms:
            return "ops"
        return "general"

    def _source_affinity(self, candidate: Citation, query_profile: str) -> float:
        title = (candidate.title or "").lower()
        source_url = (candidate.source_url or "").lower()
        source_id = candidate.source_id.lower()
        snippet = candidate.snippet.lower()
        combined = " ".join(part for part in (title, source_url, source_id, snippet) if part)

        is_github = "github.com" in source_url or "github" in source_id
        is_runbook = "runbook" in combined or "rollback" in combined
        is_internal_ops = any(marker in combined for marker in ("incident", "deployment", "deploy", "health check"))
        is_generic_readme = "readme" in combined and "github.com" in source_url

        if query_profile == "ops":
            score = 0.0
            if is_runbook:
                score += 1.25
            if is_internal_ops:
                score += 0.45
            if is_github:
                score -= 0.35
            if is_generic_readme:
                score -= 0.5
            return score

        if query_profile == "github":
            score = 0.0
            if is_github:
                score += 0.8
            if "commit" in combined or "pull request" in combined or "readme" in combined:
                score += 0.3
            if is_runbook:
                score -= 0.2
            return score

        return 0.0

    def _lexical_overlap(self, query_terms: set[str], haystack: str) -> float:
        if not query_terms:
            return 0.0
        haystack_terms = self._tokenize(haystack)
        return len(query_terms & haystack_terms) / len(query_terms)

    def _tokenize(self, text: str) -> set[str]:
        normalized = "".join(character.lower() if character.isalnum() else " " for character in text)
        return {term for term in normalized.split() if len(term) > 2}
