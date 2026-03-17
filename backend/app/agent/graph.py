from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    classify_query,
    direct_reply,
    evaluate_context,
    generate_response,
    retrieve_context,
    rewrite_query,
    should_rewrite,
)
from app.agent.state import AgentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("classifier", classify_query)
    workflow.add_node("direct_reply", direct_reply)
    workflow.add_node("retriever", retrieve_context)
    workflow.add_node("evaluator", evaluate_context)
    workflow.add_node("rewriter", rewrite_query)
    workflow.add_node("generator", generate_response)

    # Entry point
    workflow.add_edge(START, "classifier")

    # Classifier branches
    workflow.add_conditional_edges(
        "classifier",
        lambda state: "direct" if state.get("is_trivial") else "rag",
        {
            "direct": "direct_reply",
            "rag": "retriever",
        },
    )

    # RAG path
    workflow.add_edge("retriever", "evaluator")
    workflow.add_conditional_edges(
        "evaluator",
        should_rewrite,
        {
            "rewrite": "rewriter",
            "generate": "generator",
        },
    )
    workflow.add_edge("rewriter", "retriever")

    # Terminal nodes
    workflow.add_edge("generator", END)
    workflow.add_edge("direct_reply", END)

    return workflow


# Compile once at module load
compiled_graph = build_graph().compile()
