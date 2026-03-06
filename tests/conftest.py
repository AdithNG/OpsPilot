import pytest

from app.core.storage import storage


@pytest.fixture(autouse=True)
def reset_in_memory_state() -> None:
    storage.reset()
