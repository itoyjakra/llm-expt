"""Collection of agents for the RAG variants."""

from loguru import logger


def retrieve(state: dict, retriever) -> dict:
    """Retrieve documents from a vectordb"""
    logger.info("=== Retrieve ===")

    question = state["question"]
    documents = retriever.invoke(question)

    return {"documents": documents, "question": question}


def generate(state: dict, rag_chain) -> dict:
    """Generate an answer from a generator."""
    logger.info("=== Generate ===")

    documents = state["documents"]
    question = state["question"]

    generation = rag_chain.invoke(documents, question)
    return {"generation": generation, "documents": documents, "question": question}


def grade_documents(state: dict, retrieval_grader) -> dict:
    """Grade documents."""
    logger.info("=== Grade Documents ===")

    documents = state["documents"]
    question = state["question"]

    # score each doc
    filtered_docs = []
    web_search = "No"
    for doc in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": doc.page_content}
        )
        grade = score.binary_score

        if grade.lower() == "yes":  # Document is relevant
            logger.info("=== GRADE: Relevant Document ===")
            filtered_docs.append(doc)
        else:  # Document is not relevant
            logger.info("=== GRADE: Document not relevant ===")
            web_search = "Yes"
            continue

    return {"documents": filtered_docs, "question": question, "web_search": web_search}


def web_search(state: dict, web_search_tool) -> dict:
    """Perform a web search."""
    logger.info("=== Web Search ===")

    question = state["question"]
    documents = state["documents"]

    docs_from_search = web_search_tool.invoke({"query": question})
    web_results = "\n".join([doc["content"] for doc in docs_from_search])
    web_results = Document(page_content=web_results)

    if documents is not None:
        documents.append(web_results)
    else:
        documents = [web_results]

    return {"documents": documents, "question": question}


def decide_to_generate(state: dict) -> str:
    """Decide whether to generate an answer or add web search."""
    logger.info("=== Assess Graded Documents ===")

    question = state["question"]
    web_search = state["web_search"]
    filtered_documents = state["documents"]

    if web_search == "Yes":
        logger.info(
            "=== Decision: All Documents are not relevant, include Web Search ==="
        )
        return "websearch"
    else:
        logger.info("=== Decision: Generate ===")
        return "generate"


def main():
    """Entry point."""


if __name__ == "__main__":
    main()
