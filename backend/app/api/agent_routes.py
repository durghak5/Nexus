"""
Agent API endpoints — SSE streaming chat.
"""

import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from app.agent.orchestrator import get_orchestrator, clear_session
from app.agent.prompts import QUICK_PROMPTS


router = APIRouter(prefix="/api/v1/agent", tags=["Agent"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the agent. Returns Server-Sent Events (SSE) stream.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = request.session_id or str(uuid.uuid4())
    agent = get_orchestrator()

    async def event_generator():
        # Send session ID first
        yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

        try:
            async for event in agent.chat_stream(session_id, request.message):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/quick-prompts")
async def get_quick_prompts():
    """Return suggested prompts for the empty chat state."""
    return {"prompts": QUICK_PROMPTS}


@router.post("/clear/{session_id}")
async def clear_chat(session_id: str):
    """Clear a session's conversation history."""
    clear_session(session_id)
    return {"success": True, "session_id": session_id}


@router.get("/health")
async def agent_health():
    """Check if the agent is available."""
    try:
        agent = get_orchestrator()
        return {"status": "ok", "model": agent.model}
    except Exception as e:
        return {"status": "error", "message": str(e)}