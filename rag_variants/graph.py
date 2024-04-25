"""Create the graph of the RAG variants."""

from pprint import pprint

from agents import decide_to_generate, generate, grade_documents, retrieve, web_search
from graph_state import GraphState
from langgraph.graph import END, StateGraph


def create_graph_rag_variant():
    """Create the graph of the RAG variants."""
    workflow = StateGraph(GraphState)

    # Define nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("websearch", web_search)

    # Build the graph
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {"websearch": "websearch", "generate": "generate"},
    )
    workflow.add_edge("websearch", "generate")
    workflow.add_edge("generate", END)

    # Compile the graph
    app = workflow.compile()

    return app


def main():
    """Entry point."""
    app = create_graph_rag_variant()

    inputs = {"question": "What are the types of agent memory?"}
    for output in app.stream(inputs):
        for key, value in output.items():
            pprint(f"Finished running: {key}: ")
    pprint(value["generation"])


if __name__ == "__main__":
    main()
