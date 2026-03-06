from app.core.storage import storage
from app.schemas.tools import ToolExecution


class ToolService:
    def execute(self, conversation_id: str, tool_name: str, input_text: str) -> ToolExecution:
        if tool_name == "incident_analyzer":
            output = "Detected customer-facing incident context, probable rollback investigation, and follow-up owners."
            metadata = {"category": "incident"}
            status = "completed"
        elif tool_name == "ticket_drafter":
            output = "Generated draft ticket structure with title, impact, reproduction steps, and acceptance criteria."
            metadata = {"category": "ticket"}
            status = "completed"
        elif tool_name == "jira_change_request":
            output = "Execution blocked pending approval before creating an external ticket."
            metadata = {"category": "action"}
            status = "blocked"
        else:
            output = "No-op tool execution."
            metadata = {"category": "generic"}
            status = "completed"

        return storage.tools.create(
            conversation_id=conversation_id,
            tool_name=tool_name,
            status=status,
            input_text=input_text,
            output_text=output,
            metadata=metadata,
        )

    def get(self, execution_id: str) -> ToolExecution:
        execution = storage.tools.get(execution_id)
        if execution is None:
            raise KeyError("Tool execution not found")
        return execution

    def list(self, limit: int = 20) -> list[ToolExecution]:
        return storage.tools.list(limit=limit)
