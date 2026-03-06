from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.schemas.tools import ToolExecution, ToolExecutionRequest
from app.services.tools import ToolService

router = APIRouter()


@router.post("/executions", response_model=ToolExecution, status_code=status.HTTP_202_ACCEPTED)
async def queue_tool_execution(
    request: ToolExecutionRequest,
    background_tasks: BackgroundTasks,
) -> ToolExecution:
    service = ToolService()
    execution = service.queue(
        conversation_id=request.conversation_id,
        tool_name=request.tool_name,
        input_text=request.input_text,
    )
    background_tasks.add_task(_run_tool_execution, execution.execution_id)
    return execution


@router.get("/executions", response_model=list[ToolExecution])
async def list_tool_executions(limit: int = Query(default=20, ge=1, le=100)) -> list[ToolExecution]:
    return ToolService().list(limit=limit)


@router.get("/executions/{execution_id}", response_model=ToolExecution)
async def get_tool_execution(execution_id: str) -> ToolExecution:
    try:
        return ToolService().get(execution_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _run_tool_execution(execution_id: str) -> None:
    service = ToolService()
    try:
        service.run(execution_id)
    except KeyError:
        return
