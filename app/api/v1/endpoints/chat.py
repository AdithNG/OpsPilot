from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.workflow import WorkflowService

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    workflow = WorkflowService()
    return await workflow.handle_chat(request)
