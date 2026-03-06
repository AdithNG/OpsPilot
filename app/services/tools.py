from uuid import uuid4

from app.core.storage import storage
from app.schemas.tools import ToolExecution


class ToolService:
    def execute(self, conversation_id: str, tool_name: str, input_text: str) -> ToolExecution:
        result = self._resolve_execution(tool_name, input_text)

        return storage.tools.create(
            conversation_id=conversation_id,
            tool_name=tool_name,
            status=result["status"],
            input_text=input_text,
            output_text=result["output"],
            metadata=result["metadata"],
        )

    def queue(self, conversation_id: str | None, tool_name: str, input_text: str) -> ToolExecution:
        return storage.tools.create(
            conversation_id=conversation_id or f"conv-{uuid4()}",
            tool_name=tool_name,
            status="queued",
            input_text=input_text,
            output_text="Queued for background execution.",
            metadata={"category": "queued"},
        )

    def run(self, execution_id: str) -> ToolExecution:
        execution = storage.tools.get(execution_id)
        if execution is None:
            raise KeyError("Tool execution not found")
        storage.tools.update(
            execution_id,
            status="running",
            output_text="Tool execution is running.",
            metadata={**execution.metadata, "phase": "running"},
        )
        result = self._resolve_execution(execution.tool_name, execution.input_text)
        updated = storage.tools.update(
            execution_id,
            status=result["status"],
            output_text=result["output"],
            metadata=result["metadata"],
        )
        if updated is None:
            raise KeyError("Tool execution not found")
        return updated

    def get(self, execution_id: str) -> ToolExecution:
        execution = storage.tools.get(execution_id)
        if execution is None:
            raise KeyError("Tool execution not found")
        return execution

    def list(self, limit: int = 20) -> list[ToolExecution]:
        return storage.tools.list(limit=limit)

    def _resolve_execution(self, tool_name: str, input_text: str) -> dict[str, str]:
        if tool_name == "incident_analyzer":
            return {
                "output": "Detected customer-facing incident context, probable rollback investigation, and follow-up owners.",
                "metadata": {"category": "incident"},
                "status": "completed",
            }
        if tool_name == "ticket_drafter":
            return {
                "output": "Generated draft ticket structure with title, impact, reproduction steps, and acceptance criteria.",
                "metadata": {"category": "ticket"},
                "status": "completed",
            }
        if tool_name == "jira_change_request":
            return {
                "output": "Execution blocked pending approval before creating an external ticket.",
                "metadata": {"category": "action"},
                "status": "blocked",
            }
        return {
            "output": f"No-op tool execution for input: {input_text[:80]}",
            "metadata": {"category": "generic"},
            "status": "completed",
        }
