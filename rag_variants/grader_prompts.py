"""A set of prompts for different graders in the graph."""


def get_hallucination_grader_prompt():
    return """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts. \n 
     Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts."""


def get_document_grader_prompt():
    return """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""


def get_relevance_grader_prompt() -> str:
    """
    Returns a string prompt for a grader assessing whether
    an answer addresses or resolves a question.
    """
    return """You are a grader assessing whether an answer addresses / resolves a question.\n
    Give a binary score 'yes' or 'no'. 'Yes' means that the answer resolves the question."""


def get_router_prompt() -> str:
    """
    Returns a string that provides instructions to an expert
    on how to route a user question to either a vectorstore
    or a web search, depending on the topic of the question.
    """
    return """You are an expert at routing a user question to a vectorstore or web search.
    The vectorstore contains documents related to agents, prompt engineering, and adversarial attacks.
    Use the vectorstore for questions on these topics. For all else, use web-search."""
