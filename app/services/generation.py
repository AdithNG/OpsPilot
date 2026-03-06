from __future__ import annotations

from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.chat import Citation, IncidentSummary, TicketDraft
from app.services.llm import chat_model


class GenerationService:
    async def answer_question(self, message: str, citations: list[Citation]) -> str:
        context = self._context_from_citations(citations)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "TASK: answer_question\n"
                    "You are OpsPilot. Answer the user using only the retrieved context when it exists.",
                ),
                (
                    "human",
                    "User request:\n{message}\n\nRetrieved context:\n{context}\n\nFormatting instructions:\n"
                    "Respond with plain text only.",
                ),
            ]
        )
        chain = prompt | chat_model | StrOutputParser()
        return await chain.ainvoke({"message": message, "context": context})

    async def summarize_incident(self, message: str, citations: list[Citation]) -> IncidentSummary:
        parser = PydanticOutputParser(pydantic_object=IncidentSummary)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "TASK: incident_summary\n"
                    "You are OpsPilot. Produce a grounded incident summary as JSON only.\n"
                    "{format_instructions}",
                ),
                (
                    "human",
                    "User request:\n{message}\n\nRetrieved context:\n{context}\n\nFormatting instructions:\n"
                    "Return valid JSON only.",
                ),
            ]
        ).partial(format_instructions=parser.get_format_instructions())
        chain = prompt | chat_model | parser
        return await chain.ainvoke({"message": message, "context": self._context_from_citations(citations)})

    async def draft_ticket(self, message: str, citations: list[Citation]) -> TicketDraft:
        parser = PydanticOutputParser(pydantic_object=TicketDraft)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "TASK: ticket_draft\n"
                    "You are OpsPilot. Produce a grounded ticket draft as JSON only.\n"
                    "{format_instructions}",
                ),
                (
                    "human",
                    "User request:\n{message}\n\nRetrieved context:\n{context}\n\nFormatting instructions:\n"
                    "Return valid JSON only.",
                ),
            ]
        ).partial(format_instructions=parser.get_format_instructions())
        chain = prompt | chat_model | parser
        return await chain.ainvoke({"message": message, "context": self._context_from_citations(citations)})

    def _context_from_citations(self, citations: list[Citation]) -> str:
        if not citations:
            return "No relevant context found."
        return "\n".join(f"{citation.source_id}: {citation.snippet}" for citation in citations)
