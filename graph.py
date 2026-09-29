from langgraph.graph import END, START, StateGraph

from nodes import (
    answer_node,
    api_node,
    classifier_node,
    database_node,
    general_node,
    rag_node,
    route_by_category,
)
from state import ChatState


def build_graph():
    builder = StateGraph(ChatState)

    builder.add_node("classifier", classifier_node)
    builder.add_node("database", database_node)
    builder.add_node("rag", rag_node)
    builder.add_node("api", api_node)
    builder.add_node("general", general_node)
    builder.add_node("answer", answer_node)

    builder.add_edge(START, "classifier")

    builder.add_conditional_edges(
        "classifier",
        route_by_category,
        {
            "payment": "database",
            "course": "rag",
            "api_status": "api",
            "general": "general",
        },
    )

    for node in ("database", "rag", "api", "general"):
        builder.add_edge(node, "answer")

    builder.add_edge("answer", END)

    return builder.compile()


graph = build_graph()