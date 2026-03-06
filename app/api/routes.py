from fastapi import APIRouter

from app.api.v1.endpoints import approvals, chat, documents, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
