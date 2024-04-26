"""Collection of agents for the RAG variants."""

from grade_documents import GradeDocuments
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_mistralai import ChatMistralAI
from loguru import logger
from tools import web_search_tool
from vector_store import (
    create_vector_store_from_web_docs,
    get_retriever,
    get_text_splitter,
)

from langchain import hub

urls = [
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
    "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]
text_splitter = get_text_splitter()
vector_store = create_vector_store_from_web_docs(urls, text_splitter)
retriever = get_retriever(vector_store)


def retrieve(state: dict) -> dict:
    """Retrieve documents from a vectordb"""
    logger.info("=== Retrieve ===")

    question = state["question"]
    documents = retriever.invoke(question)

    return {"documents": documents, "question": question}


def get_mistral_llm(model_name: str = "mistral-large-latest", temp: float = 0.0):
    """Get the LLM."""
    return ChatMistralAI(model=model_name, temperature=temp)


def get_rag_chain():
    """Get the RAG chain."""
    prompt = hub.pull("rlm/rag-prompt")
    return prompt | get_mistral_llm() | StrOutputParser()


def get_retrieval_grader():
    """Get a retrieval grader."""

    # LLM with function call
    llm = get_mistral_llm()
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    # prompt
    system = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Retrieved document: \n\n {document} \n\n User question: {question}",
            ),
        ]
    )
    return grade_prompt | structured_llm_grader


def generate(state: dict) -> dict:
    """Generate an answer from a generator."""
    logger.info("=== Generate ===")

    documents = state["documents"]
    question = state["question"]
    rag_chain = get_rag_chain()

    generation = rag_chain.invoke({"context": documents, "question": question})

    return {"generation": generation, "documents": documents, "question": question}


def grade_documents(state: dict) -> dict:
    """Grade documents."""
    logger.info("=== Grade Documents ===")

    documents = state["documents"]
    question = state["question"]

    retrieval_grader = get_retrieval_grader()

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


def web_search(state: dict) -> dict:
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
