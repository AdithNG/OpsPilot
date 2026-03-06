from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import BaseMessage

from app.core.config import settings


class LocalRuleBasedChatModel(SimpleChatModel):
    @property
    def _llm_type(self) -> str:
        return "local-rule-based"

    def _call(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> str:
        prompt = "\n\n".join(
            message.content if isinstance(message.content, str) else str(message.content)
            for message in messages
        )
        lowered = prompt.lower()
        if "task: incident_summary" in lowered:
            return self._incident_summary_response(prompt)
        if "task: ticket_draft" in lowered:
            return self._ticket_draft_response(prompt)
        if "task: answer_question" in lowered:
            return self._question_response(prompt)
        return "I can help with runbooks, incident summaries, and drafting structured follow-up actions."

    def _question_response(self, prompt: str) -> str:
        context = self._extract_section(prompt, "Retrieved context:", "Formatting instructions:")
        message = self._extract_section(prompt, "User request:", "Retrieved context:")
        if context and context != "No relevant context found.":
            return f"Relevant guidance: {context.splitlines()[0].strip()}"
        if message:
            return f"I could not find supporting context for: {message.strip()}"
        return "I can help with runbooks, incident summaries, and drafting structured follow-up actions."

    def _incident_summary_response(self, prompt: str) -> str:
        context = self._extract_section(prompt, "Retrieved context:", "Formatting instructions:")
        title_hint = self._extract_section(prompt, "User request:", "Retrieved context:")
        return json.dumps(
            {
                "title": "Production incident follow-up",
                "impact": context or "Customer-facing errors were detected and require recovery validation.",
                "severity": "sev2",
                "suspected_cause": "A recent deploy, dependency regression, or infrastructure change should be investigated first.",
                "next_steps": [
                    {
                        "owner": "oncall-engineer",
                        "action": "Confirm impact window and affected systems from the incident notes.",
                        "priority": "high",
                    },
                    {
                        "owner": "service-owner",
                        "action": f"Review evidence and document likely root cause for: {title_hint or 'the incident'}.",
                        "priority": "high",
                    },
                ],
            }
        )

    def _ticket_draft_response(self, prompt: str) -> str:
        context = self._extract_section(prompt, "Retrieved context:", "Formatting instructions:")
        request = self._extract_section(prompt, "User request:", "Retrieved context:")
        return json.dumps(
            {
                "title": "Investigate production issue after deploy",
                "summary": request or "Users are experiencing a production issue that needs triage and a fix plan.",
                "impact": context or "The issue affects normal user workflows and should be prioritized for engineering follow-up.",
                "reproduction_steps": [
                    "Identify the failing workflow or endpoint.",
                    "Compare behavior before and after the latest deploy.",
                    "Capture logs, metrics, and any error responses.",
                ],
                "acceptance_criteria": [
                    "Root cause is identified and documented.",
                    "A fix is verified in the target environment.",
                    "Monitoring confirms the issue no longer reproduces.",
                ],
            }
        )

    def _extract_section(self, prompt: str, start_marker: str, end_marker: str) -> str:
        if start_marker not in prompt:
            return ""
        section = prompt.split(start_marker, maxsplit=1)[1]
        if end_marker in section:
            section = section.split(end_marker, maxsplit=1)[0]
        return section.strip()


def get_chat_model():
    if settings.llm_provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "llm_provider=openai requires langchain-openai to be installed."
            ) from exc
        return ChatOpenAI(model=settings.openai_model)
    return LocalRuleBasedChatModel()


chat_model = get_chat_model()
