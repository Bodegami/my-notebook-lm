from __future__ import annotations

import json
import logging
import re
from typing import List

from langchain_core.messages import AIMessage, HumanMessage

from app.agent.state import AgentState

logger = logging.getLogger(__name__)

# ── Classifier Node ────────────────────────────────────────────────────────────

async def classify_query(state: AgentState) -> AgentState:
    """Classify the query as TRIVIAL or DOCUMENT question."""
    from app.services.ollama_client import ollama_client

    query = state["current_query"]
    classification_prompt = (
        "Is this message a greeting, thanks, or trivial off-topic comment, "
        "or is it a question about book/document content? "
        f'Message: "{query}"\n'
        "Reply with ONLY one word: TRIVIAL or DOCUMENT"
    )

    response_text = ""
    async for token in ollama_client.stream_chat(
        messages=[{"role": "user", "content": classification_prompt}],
        system_prompt="You are a message classifier. Reply with only TRIVIAL or DOCUMENT.",
    ):
        response_text += token

    is_trivial = "TRIVIAL" in response_text.upper() and "DOCUMENT" not in response_text.upper()
    logger.info(f"Classified query as {'TRIVIAL' if is_trivial else 'DOCUMENT'}: {query!r}")

    return {**state, "is_trivial": is_trivial}


# ── Retriever Node ─────────────────────────────────────────────────────────────

async def retrieve_context(state: AgentState) -> AgentState:
    """Retrieve relevant chunks from the vector store."""
    from app.config import settings
    from app.services.vector_store import search

    query = state.get("rewritten_query") or state["current_query"]
    logger.info(f"Retrieving context for query: {query!r}")

    chunks = search(query, top_k=settings.top_k_results)
    logger.info(f"Retrieved {len(chunks)} chunks.")

    return {**state, "retrieved_chunks": chunks}


# ── Context Evaluator Node ─────────────────────────────────────────────────────

SCORE_THRESHOLD = 0.3


async def evaluate_context(state: AgentState) -> AgentState:
    """
    Evaluate whether retrieved context is sufficient.
    Sets a flag via retry_count logic:
    - If insufficient AND retry_count < 2 → increment retry_count (triggers rewrite edge)
    - Otherwise → proceed to generation
    """
    chunks = state.get("retrieved_chunks", [])
    retry_count = state.get("retry_count", 0)

    sufficient = bool(chunks) and any(c.score >= SCORE_THRESHOLD for c in chunks)

    if not sufficient and retry_count < 2:
        logger.info(f"Context insufficient (retry {retry_count + 1}/2). Triggering rewrite.")
        return {**state, "retry_count": retry_count + 1}
    else:
        logger.info(f"Context {'sufficient' if sufficient else 'insufficient but max retries reached'}.")
        return {**state, "retry_count": retry_count + 1}


def should_rewrite(state: AgentState) -> str:
    """Conditional edge: determines if we should rewrite or generate."""
    chunks = state.get("retrieved_chunks", [])
    retry_count = state.get("retry_count", 0)
    sufficient = bool(chunks) and any(c.score >= SCORE_THRESHOLD for c in chunks)

    if not sufficient and retry_count <= 2:
        return "rewrite"
    return "generate"


# ── Query Rewriter Node ────────────────────────────────────────────────────────

async def rewrite_query(state: AgentState) -> AgentState:
    """Rephrase the query to improve retrieval."""
    from app.services.ollama_client import ollama_client

    original_query = state["current_query"]
    rewrite_prompt = (
        f"Rephrase this question to improve document search results. "
        f"Keep the same meaning but use different words and be more specific.\n"
        f"Original question: {original_query}\n"
        f"Rephrased question:"
    )

    rewritten = ""
    async for token in ollama_client.stream_chat(
        messages=[{"role": "user", "content": rewrite_prompt}],
        system_prompt="You are a query rewriter. Output only the rephrased question, nothing else.",
    ):
        rewritten += token

    rewritten = rewritten.strip()
    logger.info(f"Rewritten query: {rewritten!r}")
    return {**state, "rewritten_query": rewritten}


# ── Generator Node ─────────────────────────────────────────────────────────────

def _parse_citations(response_text: str) -> tuple[str, List[dict]]:
    """
    Extract the ```sources JSON block from the LLM response.
    Returns (clean_text, citations_list).
    """
    sources_pattern = re.compile(r"```sources\s*(.*?)```", re.DOTALL)
    match = sources_pattern.search(response_text)

    citations = []
    if match:
        try:
            raw = match.group(1).strip()
            citations = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse sources JSON block.")

    # Remove the sources block from the response text
    clean_text = sources_pattern.sub("", response_text).strip()
    return clean_text, citations


async def generate_response(state: AgentState) -> AgentState:
    """Generate a RAG response using retrieved context."""
    from app.agent.prompts import SYSTEM_PROMPT, build_context_block
    from app.services.ollama_client import ollama_client

    chunks = state.get("retrieved_chunks", [])
    context_block = build_context_block(chunks)

    # Build conversation messages: history + new context + query
    history_messages = [
        {"role": msg.type if hasattr(msg, "type") else "user", "content": msg.content}
        for msg in state.get("messages", [])
        if hasattr(msg, "content")
    ]

    current_message = {
        "role": "user",
        "content": f"{context_block}\n\nQuestion: {state['current_query']}",
    }
    messages = history_messages + [current_message]

    full_response = ""
    async for token in ollama_client.stream_chat(messages=messages, system_prompt=SYSTEM_PROMPT):
        full_response += token

    clean_text, citations = _parse_citations(full_response)
    logger.info(f"Generated response with {len(citations)} citations.")

    return {**state, "final_response": clean_text, "citations": citations}


async def direct_reply(state: AgentState) -> AgentState:
    """Handle trivial queries without RAG."""
    from app.agent.prompts import TRIVIAL_SYSTEM_PROMPT
    from app.services.ollama_client import ollama_client

    messages = [{"role": "user", "content": state["current_query"]}]

    full_response = ""
    async for token in ollama_client.stream_chat(
        messages=messages,
        system_prompt=TRIVIAL_SYSTEM_PROMPT,
    ):
        full_response += token

    return {**state, "final_response": full_response.strip(), "citations": []}
