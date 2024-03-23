from multiprocessing import context
from tkinter import Variable

import boto3
from click import prompt
from langchain.chains import ConversationChain, RetrievalQA
from langchain.llms.bedrock import Bedrock
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryBufferMemory,
)
from langchain.prompts import PromptTemplate
from langchain.retrievers.bedrock import AmazonKnowledgeBasesRetriever
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from loguru import logger

bedrock_agent_client = boto3.client("bedrock-agent-runtime")
bedrock_client = boto3.client("bedrock-runtime")


def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def retrieve(query: str, kbId: str, numberOfResults: int = 5):
    return bedrock_agent_client.retrieve(
        retrievalQuery={"text": query},
        knowledgeBaseId=kbId,
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": numberOfResults}
        },
    )


def get_contexts(retrievalResults):
    contexts = []
    for retrievedResult in retrievalResults:
        contexts.append(retrievedResult["content"]["text"])
    return " ".join(contexts)


def contextualized_question(input: dict):
    if input.get("chat_history"):
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )
        llm = get_bedrock_llm()
        contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()
        return contextualize_q_chain

    return input["question"]


def get_bedrock_llm(model_name: str = "anthropic.claude-v2:1"):
    """Returns the requested LLM through Bedrock"""
    return Bedrock(
        model_id=model_name,
        model_kwargs={"temperature": 0, "top_k": 10, "max_tokens_to_sample": 3000},
        client=bedrock_client,
    )


def get_prompt() -> str:
    return """
    Human: You are an AI system working on medical trial research, and provides answers to questions \
    by using fact based and statistical information when possible.
    Use the following pieces of information to provide a concise answer to the question enclosed in <question> tags.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    <context>
    {context_str}
    </context>

    <question>
    {query_str}
    </question>

    The response should be specific and use statistics or numbers when possible.

    Assistant:"""


def get_prompt_langchain_format() -> str:
    return """
    Human: You are an AI system working on large language model research.
    Use the following pieces of information to provide a concise answer to the question.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    Question: {question} 
    Context: {context} 

    The response should be specific and use statistics or numbers when possible.

    Assistant:"""


def get_prompt_for_chat() -> str:
    return """You are an assistant for question-answering tasks. \
    Use the following pieces of retrieved context to answer the question. \
    If you don't know the answer, just say that you don't know. \

    {context}"""


def get_system_prompt_for_context() -> str:
    return """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""


def get_prompt_with_context() -> ChatPromptTemplate:
    system_prompt_for_context = get_system_prompt_for_context()
    return ChatPromptTemplate.from_messages(
        [
            ("human", system_prompt_for_context),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )


def followup_question_with_langchain():
    """Get answer with a followup question"""
    prompt = get_prompt_with_context()
    llm = get_bedrock_llm()
    followup_chain = prompt | llm | StrOutputParser()

    qna = ["What does LLM stand for?", "Large language model"]
    q_followup = "What is meant by large?"

    chat_history = [HumanMessage(content=qna[0]), AIMessage(content=qna[1])]
    logger.debug(chat_history)

    return followup_chain.invoke({"chat_history": chat_history, "question": q_followup})


def qa_simple(question: str, kb_id: str) -> None:
    """Q&A (no chat) without memory"""
    llm = get_bedrock_llm()
    prompt = get_prompt()

    response = retrieve(question, kb_id, 3)
    retrieval_results = response["retrievalResults"]
    contexts = get_contexts(retrieval_results)

    prompt = prompt.format(context_str=contexts, query_str=question)
    response = llm(prompt)

    print(response)


def get_retriever() -> AmazonKnowledgeBasesRetriever:
    """Returns the document retriever"""
    return AmazonKnowledgeBasesRetriever(
        knowledge_base_id=kb_id,
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
    )


def qa_with_langchain(question: str, kb_id: str) -> RetrievalQA:
    """Q&A (no chat) without memory using Langchain"""
    llm = get_bedrock_llm()

    retriever = AmazonKnowledgeBasesRetriever(
        knowledge_base_id=kb_id,
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
    )

    langchain_prompt = get_prompt_langchain_format()
    prompt = PromptTemplate(
        template=langchain_prompt, input_variables=["question", "context"]
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )

    return qa


def chat_with_langchain(questions: list[str], kb_id: str) -> None:
    """Chat with memory using Langchain"""
    memory = ConversationBufferWindowMemory(k=5)
    llm = get_bedrock_llm()

    langchain_prompt = get_prompt_langchain_format()
    prompt = PromptTemplate(
        template=langchain_prompt, input_variables=["question", "context"]
    )

    qa_system_prompt = """You are an assistant for question-answering tasks. \
    Use the following pieces of retrieved context to answer the question. \
    If you don't know the answer, just say that you don't know. \
    Use the answer concise.\

    {context}"""

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )

    retriever = get_retriever()

    # rag_chain = (
    #     {"context": retriever | format_docs, "question": RunnablePassthrough()}
    #     | prompt
    #     | llm
    #     | StrOutputParser()
    # )

    rag_chain = (
        RunnablePassthrough.assign(
            context=contextualized_question | retriever | format_docs
        )
        | qa_prompt
        | llm
    )

    chat_history = []

    question = "what is a 1-bit LLM?"
    ai_msg = rag_chain.invoke({"question": question, "chat_history": chat_history})
    chat_history.extend([HumanMessage(content=question), ai_msg])
    print("=" * 80)
    print(ai_msg)
    return

    question = "what are some of its advantages?"
    rag_chain.invoke({"question": question, "chat_history": chat_history})
    chat_history.extend([HumanMessage(content=question), ai_msg])
    print("=" * 80)

    question = "Does 1-bit LLM work with MoE?"
    rag_chain.invoke({"question": question, "chat_history": chat_history})

    return

    rag_chain = (
        RunnablePassthrough.assign(context=... | retriever | format_docs)
        | qa_prompt
        | llm
    )
    conversation = ConversationChain(
        llm=llm,
        memory=memory,
        verbose=True,
        prompt=prompt,
    )
    answer = conversation.predict(input=questions[0])
    print(answer)
    assert 5 == 55

    for question in questions[1:]:
        qa = qa_with_langchain(question=question, kb_id=kb_id)
        answer = qa(question)["result"]


if __name__ == "__main__":
    kb_id = "QM8AGLZRKO"
    qq = "what is a 1-bit LLM?"
    qq = "what are some of the advantages of 1-bit LLM?"
    qq = "Does 1-bit LLM work with MoE?"
    qq = "what is a 1-bit LLM?"

    qa = qa_with_langchain(question=qq, kb_id=kb_id)
    print(type(qa))
    print(qa(qq)["result"])

    print("-" * 30)
    # chat_with_langchain([qq], kb_id=kb_id)
    # answer = followup_question_with_langchain()
    # print(answer)
