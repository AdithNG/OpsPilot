from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.tools import ToolExecution
from app.services.tools import ToolService

router = APIRouter()


@router.get("/executions", response_model=list[ToolExecution])
async def list_tool_executions(limit: int = Query(default=20, ge=1, le=100)) -> list[ToolExecution]:
    return ToolService().list(limit=limit)


@router.get("/executions/{execution_id}", response_model=ToolExecution)
async def get_tool_execution(execution_id: str) -> ToolExecution:
    try:
        return ToolService().get(execution_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
