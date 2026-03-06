import pytest

from app.core.config import settings
from app.core.security import rate_limiter
from app.core.storage import storage


@pytest.fixture(autouse=True)
def reset_in_memory_state() -> None:
    storage.reset()
    rate_limiter.reset()
    settings.api_key = None
    settings.rate_limit_requests = 60
    settings.rate_limit_window_seconds = 60
