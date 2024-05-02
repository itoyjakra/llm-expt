"""Create the graph of the RAG variants."""

from pprint import pprint

from agents import (
    check_for_hallucinations_and_relevance,
    decide_to_generate,
    generate,
    grade_documents,
    retrieve,
    web_search,
)
from dotenv import load_dotenv
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
    workflow.add_conditional_edges(
        "generate",
        check_for_hallucinations_and_relevance,
        {"useful": END, "not useful": "websearch", "not supported": "generate"},
    )
    # workflow.add_edge("generate", END)

    # Compile the graph
    app = workflow.compile()

    return app


def main():
    """Entry point."""
    load_dotenv()
    app = create_graph_rag_variant()
    app.get_graph().print_ascii()
    print(app.get_graph().draw_mermaid())

    # inputs = {"question": "What are the types of agent memory?"}
    # inputs = {"question": "What is the capital of Suriname?"}
    inputs = {"question": "What is Long Short Term Memory?"}
    # inputs = {"question": "What is chain of thought?"}
    # inputs = {"question": "What is 1-bit LLM?"}
    # inputs = {"question": "Give me a summary of the AlphaCodium work"}
    inputs = {
        "question": "How does the concept of adversarial attack work in the LLM space?"
    }

    for output in app.stream(inputs):
        for key, value in output.items():
            pprint(f"Finished running: {key}: ")
    pprint(value["generation"])


if __name__ == "__main__":
    main()
