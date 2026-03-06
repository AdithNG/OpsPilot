import pytest

from app.services.approvals import ApprovalService
from app.services.document_store import document_store


@pytest.fixture(autouse=True)
def reset_in_memory_state() -> None:
    document_store.reset()
    ApprovalService().reset()
