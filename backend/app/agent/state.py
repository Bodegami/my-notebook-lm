from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    session_id: str
    messages: Annotated[List[Any], add_messages]
    current_query: str
    rewritten_query: Optional[str]
    retrieved_chunks: List[Any]   # List[SearchResult]
    retry_count: int
    is_trivial: bool
    final_response: Optional[str]
    citations: List[Dict]
