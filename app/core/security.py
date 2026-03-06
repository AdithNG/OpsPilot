from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from time import time

from fastapi import HTTPException, Request, status

from app.core.config import settings


@dataclass(slots=True)
class InMemoryRateLimiter:
    buckets: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        if limit <= 0:
            return True
        now = time()
        bucket = self.buckets[key]
        while bucket and (now - bucket[0]) >= window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    def reset(self) -> None:
        self.buckets.clear()


rate_limiter = InMemoryRateLimiter()


async def enforce_api_protection(request: Request) -> None:
    protected_prefixes = (settings.api_prefix, settings.graphql_path)
    if not request.url.path.startswith(protected_prefixes):
        return
    if request.url.path == f"{settings.api_prefix}/health":
        return

    if settings.api_key:
        provided_key = request.headers.get("x-api-key")
        if provided_key != settings.api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")

    client = request.client.host if request.client else "unknown"
    path_key = f"{client}:{request.url.path}"
    allowed = rate_limiter.allow(
        key=path_key,
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded.")
