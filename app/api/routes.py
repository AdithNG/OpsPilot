from fastapi import APIRouter, Depends

from app.api.v1.endpoints import approvals, chat, conversations, documents, evals, health, observability, tools, traces
from app.core.security import enforce_api_protection

api_router = APIRouter(dependencies=[Depends(enforce_api_protection)])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"])
api_router.include_router(observability.router, prefix="/observability", tags=["observability"])
api_router.include_router(evals.router, prefix="/evals", tags=["evals"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
