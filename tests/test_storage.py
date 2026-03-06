from app.core.storage import storage


def test_storage_defaults_to_memory_backend() -> None:
    assert storage.backend == "memory"


def test_storage_reset_keeps_seed_runbook() -> None:
    storage.reset()

    citations = storage.documents.search("rollback runbook")

    assert citations
    assert citations[0].source_id == "runbook-rollback"
