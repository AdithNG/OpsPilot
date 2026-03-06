from fastapi import APIRouter, HTTPException, status

from app.core.storage import storage
from app.schemas.chat import ConversationMessage

router = APIRouter()


@router.get("/{conversation_id}", response_model=list[ConversationMessage])
async def get_conversation(conversation_id: str) -> list[ConversationMessage]:
    messages = storage.conversations.get_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return messages
