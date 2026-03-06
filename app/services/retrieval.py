from app.schemas.chat import Citation

_RUNBOOK_SOURCE_ID = "runbook-rollback"
_RUNBOOK_SNIPPET = "Rollback steps: pause deploys, restore the last known good version, and verify health checks."


class RetrievalService:
    async def retrieve(self, query: str) -> list[Citation]:
        lowered = query.lower()
        if "rollback" in lowered or "runbook" in lowered:
            return [Citation(source_id=_RUNBOOK_SOURCE_ID, snippet=_RUNBOOK_SNIPPET)]
        return []
