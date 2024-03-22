"""Collection of utility functions."""

import boto3
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.retrievers.bedrock import AmazonKnowledgeBasesRetriever

bedrock_client = boto3.client("bedrock-runtime")


def get_template_with_history_01() -> str:
    return """You are a nice chatbot having a conversation with a human. \
    You always provide concise answers, preferably in 3 sentences or less.

    Previous conversation:
    {chat_history}

    New human question: {question}
    Response:"""


def get_template_with_context_01():
    return """
    Human: You are AI system who provides answers only based on references.
    Use the following pieces of information to provide a concise answer to the question enclosed in <question> tags. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    <context>
    {context}
    </context>

    <question>
    {question}
    </question>

    The response should be specific and use statistics or numbers when possible.

    Assistant:"""


def get_template_with_history_02():
    return """\
    <chat-history>
    {chat_history}
    </chat-history>

    <follow-up-message>
    {question}
    <follow-up-message>

    Human: Given the conversation above (between Human and Assistant) and the follow up message from Human, \
    rewrite the follow up message to be a standalone question that captures all relevant context \
    from the conversation. Answer only with the new question and nothing else.

    Assistant: Standalone Question:"""


def get_respond_prompt_template():
    return """\
    <context>
    {context}
    </context>

    Human: Given the context above, answer the question inside the <q></q> XML tags.

    <q>{question}</q>

    If the answer is not in the context say "Sorry, I don't know as the answer was not found in the context". Do not use any XML tags in the answer.

    Assistant:"""


def get_bedrock_llm(model_name: str = "anthropic.claude-v2:1"):
    """Returns the requested LLM through Bedrock"""
    return Bedrock(
        model_id=model_name,
        model_kwargs={"temperature": 0, "top_k": 10, "max_tokens_to_sample": 3000},
        client=bedrock_client,
    )


def knowledge_base_retriever(kb_id: str) -> AmazonKnowledgeBasesRetriever:
    return AmazonKnowledgeBasesRetriever(
        knowledge_base_id=kb_id,
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
    )


def get_memory_chain() -> ConversationBufferMemory:
    memory_chain = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        human_prefix="Human",
        ai_prefix="Assistant",
    )
    memory_chain.chat_memory.add_user_message("Hello, what are you able to do?")
    memory_chain.chat_memory.add_ai_message(
        "Hi! I am a help chat assistant which can answer questions about your documents."
    )

    return memory_chain
