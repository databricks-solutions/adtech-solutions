"""API routes for agent-powered segment building."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.config.constants import GENERIC_ERROR_MESSAGE
from backend.models.segment import SegmentDefinition
from backend.services.agent_service import AgentService, get_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class AgentParseRequest(BaseModel):
    """Request to parse natural language to segment rules."""
    input: str = Field(..., description="User's natural language input")
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    current_segment: SegmentDefinition | None = Field(
        None,
        description="Current segment state to modify"
    )


class AgentParseResponse(BaseModel):
    """Response from agent parsing."""
    response_text: str = Field(..., description="Agent's response text")
    segment: dict[str, Any] | None = Field(None, description="Generated segment definition")
    preview: dict[str, int] | None = Field(None, description="Preview counts")
    sql: str | None = Field(None, description="Generated SQL query")


class AgentSummarizeRequest(BaseModel):
    """Request to generate a short segment description from chat context."""
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Chat messages that led to this segment",
    )
    segment: SegmentDefinition = Field(..., description="Current segment definition")


class AgentSummarizeResponse(BaseModel):
    """Response with a 1-2 sentence segment summary and optional suggested name."""
    summary: str = Field(..., description="Short description for the segment")
    suggested_name: str = Field("", description="Suggested segment/campaign name (identifier-friendly)")


@router.post("/parse", response_model=AgentParseResponse)
async def parse_input(
    request: AgentParseRequest,
    agent: AgentService = Depends(get_agent_service),
):
    """Parse natural language input to segment rules using LLM."""
    try:
        # Convert chat messages to dict format
        history = [{"role": m.role, "content": m.content} for m in request.conversation_history]

        result = agent.parse_input(
            user_input=request.input,
            conversation_history=history,
            current_segment=request.current_segment,
        )

        return AgentParseResponse(
            response_text=result.get("response_text", ""),
            segment=result.get("segment"),
            preview=result.get("preview"),
            sql=result.get("sql"),
        )

    except Exception as e:
        logger.exception(
            "Agent parse error",
            extra={"error": str(e), "endpoint": "parse"},
        )
        raise HTTPException(status_code=500, detail=GENERIC_ERROR_MESSAGE)


@router.post("/summarize", response_model=AgentSummarizeResponse)
async def summarize_segment(
    request: AgentSummarizeRequest,
    agent: AgentService = Depends(get_agent_service),
):
    """Generate a 1-2 sentence segment description and suggested name from the conversation using the LLM."""
    try:
        history = [{"role": m.role, "content": m.content} for m in request.conversation_history]
        summary, suggested_name = agent.summarize_segment(request.segment, history)
        return AgentSummarizeResponse(
            summary=summary or request.segment.description or "",
            suggested_name=suggested_name or "",
        )
    except Exception as e:
        logger.warning(
            "Agent summarize error",
            extra={"error": str(e), "endpoint": "summarize"},
        )
        return AgentSummarizeResponse(
            summary=request.segment.description or "",
            suggested_name="",
        )
