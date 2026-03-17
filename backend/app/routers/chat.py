from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session history: session_id → list of LangChain messages
_session_history: Dict[str, List] = {}


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _run_agent_stream(session_id: str, message: str):
    """
    Run the LangGraph agent and yield SSE events.
    Sequence: status → (status) → tokens → citations → done
    """
    from app.agent.graph import compiled_graph
    from app.agent.state import AgentState

    history = _session_history.get(session_id, [])

    initial_state: AgentState = {
        "session_id": session_id,
        "messages": history,
        "current_query": message,
        "rewritten_query": None,
        "retrieved_chunks": [],
        "retry_count": 0,
        "is_trivial": False,
        "final_response": None,
        "citations": [],
    }

    # Status: searching
    yield _sse({"type": "status", "text": "Searching documents..."})

    try:
        # Run the full graph (non-streaming — collect result then stream tokens)
        result = await compiled_graph.ainvoke(initial_state)

        is_trivial = result.get("is_trivial", False)
        chunks = result.get("retrieved_chunks", [])

        if not is_trivial and chunks:
            yield _sse({"type": "status", "text": f"Analyzing {len(chunks)} excerpts..."})

        yield _sse({"type": "status", "text": "Generating response..."})

        final_text = result.get("final_response", "")
        citations_data = result.get("citations", [])

        # Stream response token by token (simulate streaming from collected text)
        words = final_text.split(" ")
        for i, word in enumerate(words):
            token = word if i == len(words) - 1 else word + " "
            yield _sse({"type": "token", "text": token})
            await asyncio.sleep(0)  # yield control

        # Emit citation events
        for i, citation in enumerate(citations_data):
            if isinstance(citation, dict):
                citation_payload = {
                    "id": citation.get("id", i + 1),
                    "source_filename": citation.get("source_filename", ""),
                    "page_number": citation.get("page_number"),
                    "section_heading": citation.get("section_heading"),
                    "excerpt": citation.get("excerpt", ""),
                }
            else:
                citation_payload = {
                    "id": i + 1,
                    "source_filename": str(citation),
                    "page_number": None,
                    "section_heading": None,
                    "excerpt": "",
                }
            yield _sse({"type": "citation", **citation_payload})

        # Done event
        yield _sse({"type": "done", "sources": citations_data})

        # Update session history
        _session_history[session_id] = list(result.get("messages", history)) + [
            HumanMessage(content=message),
            AIMessage(content=final_text),
        ]

    except Exception as exc:
        logger.error(f"Agent error for session {session_id}: {exc}", exc_info=True)
        yield _sse({"type": "error", "text": str(exc)})


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    session_id = request.session_id
    message = request.message

    async def event_generator():
        async for event in _run_agent_stream(session_id, message):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
