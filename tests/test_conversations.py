from app.core.storage import storage


def test_conversation_repository_stores_messages_in_order() -> None:
    conversation_id = storage.conversations.ensure()
    storage.conversations.append(conversation_id, "user", "first")
    storage.conversations.append(conversation_id, "assistant", "second")

    messages = storage.conversations.get_messages(conversation_id)

    assert [message.role for message in messages] == ["user", "assistant"]
    assert [message.content for message in messages] == ["first", "second"]
