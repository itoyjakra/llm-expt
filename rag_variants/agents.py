"""Collection of agents for the RAG variants."""

from grader_prompts import (
    get_document_grader_prompt,
    get_hallucination_grader_prompt,
    get_relevance_grader_prompt,
    get_router_prompt,
)
from graders import GradeAnswer, GradeDocuments, GradeHallucinations, RouteQuery
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


def get_mistral_llm(model_name: str = "mistral-large-latest", temp: float = 0.0):
    """Get the LLM."""
    return ChatMistralAI(model=model_name, temperature=temp)


def get_rag_chain():
    """Get the RAG chain."""
    prompt = hub.pull("rlm/rag-prompt")
    return prompt | get_mistral_llm() | StrOutputParser()


def get_query_router():
    """Get a query router."""
    # LLM with function call
    llm = get_mistral_llm()
    structured_llm_grader = llm.with_structured_output(RouteQuery)

    # prompt
    system = get_router_prompt()

    query_router_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "{question}"),
        ]
    )
    return query_router_prompt | structured_llm_grader


def get_document_grader():
    """Get a retrieval grader."""

    # LLM with function call
    llm = get_mistral_llm()
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    # prompt
    system = get_document_grader_prompt()

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


def get_hallucination_grader():
    """Get a hallucination grader."""
    # LLM with function call
    llm = get_mistral_llm()
    structured_llm_grader = llm.with_structured_output(GradeHallucinations)

    # prompt
    system = get_hallucination_grader_prompt()

    hallucination_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "Set of facts: \n\n {documents} \n\n LLM generation: {generation}",
            ),
        ]
    )
    return hallucination_prompt | structured_llm_grader


def get_relevance_grader():
    """Get a grader for relevance of answers against questions."""
    # LLM with function call
    llm = get_mistral_llm()
    structured_llm_grader = llm.with_structured_output(GradeAnswer)

    # prompt
    system = get_relevance_grader_prompt()

    relevance_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "human",
                "User question: \n\n {question} \n\n LLM generation: {generation}",
            ),
        ]
    )

    return relevance_prompt | structured_llm_grader


def route_query(state: dict) -> str:
    """Route the query to either web search or RAG."""
    logger.info("=== Route Query ===")

    question = state["question"]
    query_router = get_query_router()
    answer_source = query_router.invoke({"question": question})

    if answer_source.data_source.value == "vectorstore":
        logger.info("=== Route query to RAG ===")
        return "vectorstore"
    elif answer_source.data_source.value == "websearch":
        logger.info("=== Route query to Web Search ===")
        return "websearch"


def retrieve(state: dict) -> dict:
    """Retrieve documents from a vectordb"""
    logger.info("=== Retrieve ===")

    question = state["question"]
    documents = retriever.invoke(question)

    return {"documents": documents, "question": question}


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

    document_grader = get_document_grader()

    # score each doc
    filtered_docs = []
    web_search = "No"
    for doc in documents:
        score = document_grader.invoke(
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


def check_for_hallucinations_and_relevance(state: dict) -> str:
    """Check for hallucinations and relevance."""
    logger.info("=== Check for Hallucinations ===")

    question = state["question"]
    generation = state["generation"]
    documents = state["documents"]

    hallucination_grader = get_hallucination_grader()
    relevance_grader = get_relevance_grader()

    hallucination_score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )
    grade = hallucination_score.binary_score

    if grade.lower() == "yes":  # Answer is grounded
        logger.info("=== DECISION: Answer is grounded IN DOCUMENTS ===")
        logger.info("=== GRADE ANSWER FOR RELEVANCE TO QUESTION ===")
        score = relevance_grader.invoke(
            {"question": question, "generation": generation}
        )
        grade = score.binary_score

        if grade.lower() == "yes":
            logger.info("=== DECISION: Answer is relevant to the question ===")
            return "useful"
        else:
            logger.info("=== DECISION: Answer is not relevant to the question ===")
            return "not useful"
    else:
        logger.info("=== DECISION: Answer is not grounded in documents, Re-try ===")
        return "not supported"


def test_agents():
    """Test specific agents."""
    question = "Who was the father of Kublai Khan?"
    query_router = get_query_router()
    answer = query_router.invoke({"question": question})
    print(answer)


if __name__ == "__main__":
    test_agents()
