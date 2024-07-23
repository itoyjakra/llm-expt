"""Test different types of Langchain memory."""

from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from loguru import logger
from sympy import content
from utils import (
    get_bedrock_llm,
    get_memory_chain,
    get_respond_prompt_template,
    get_template_with_context_01,
    get_template_with_history_01,
    get_template_with_history_02,
    knowledge_base_retriever,
)


def test_conv_buffer_memory():
    """Test the ConversationBufferMemory."""
    memory = ConversationBufferMemory()
    logger.info(memory.dict)

    memory.chat_memory.add_user_message("hi!")
    memory.chat_memory.add_ai_message("what's up?")
    logger.info(memory.load_memory_variables({}))
    print("=" * 80)

    # save the memory in a different key
    memory = ConversationBufferMemory(memory_key="chat_history")
    memory.chat_memory.add_user_message("What is LLM?")
    memory.chat_memory.add_ai_message("Large Language Model.")
    logger.info(memory.load_memory_variables({}))
    print("=" * 80)

    # return the full history
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    memory.chat_memory.add_user_message("What is LLM?")
    memory.chat_memory.add_ai_message("Large Language Model.")
    logger.info(memory.load_memory_variables({}))
    print("=" * 80)

    # conversation using LLM
    llm = get_bedrock_llm()

    # Notice that "chat_history" is present in the prompt template
    template = """You are a nice chatbot having a conversation with a human.

    Previous conversation:
    {chat_history}

    New human question: {question}
    Response:"""

    prompt = PromptTemplate.from_template(template)
    # Notice that we need to align the `memory_key`
    memory = ConversationBufferMemory(memory_key="chat_history")
    conversation = LLMChain(llm=llm, prompt=prompt, verbose=True, memory=memory)

    logger.debug(conversation)


def test_chat() -> LLMChain:
    """Returns a conversation chain"""
    template = get_template_with_history_01()
    prompt = PromptTemplate.from_template(template)
    llm = get_bedrock_llm()
    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, ai_prefix="Assistant"
    )
    conversation = LLMChain(llm=llm, prompt=prompt, verbose=True, memory=memory)

    return conversation


def get_chain(kb_id: str):
    prompt_template = get_template_with_context_01()
    prompt = ChatPromptTemplate.from_template(prompt_template)
    retriever = knowledge_base_retriever(kb_id=kb_id)
    llm = get_bedrock_llm()

    return (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


def test_rag(query: str, kb_id: str):
    answers = []
    contexts = []
    retriever = knowledge_base_retriever(kb_id=kb_id)

    rag_chain = get_chain(kb_id=kb_id)
    answer = rag_chain.invoke(query)
    answers.append(answer)
    contexts.append(
        [docs.page_content for docs in retriever.get_relevant_documents(query)]
    )


def get_qa_chain(kb_id: str):
    llm = get_bedrock_llm()
    retriever = knowledge_base_retriever(kb_id=kb_id)
    memory_chain = get_memory_chain()
    # chat_template = get_template_with_history_02()
    condense_prompt = PromptTemplate.from_template(get_template_with_history_02())
    respond_prompt = PromptTemplate.from_template(get_respond_prompt_template())

    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory_chain,
        condense_question_prompt=condense_prompt,  # this is the prompt for condensing user inputs
        verbose=False,  # change this to True in order to see the logs working in the background
    )

    qa.combine_docs_chain.llm_chain.prompt = (
        respond_prompt  # this is the prompt in order to respond to condensed questions
    )

    return qa


if __name__ == "__main__":
    # test_conv_buffer_memory()
    # test_chat()
    kb_id = "QM8AGLZRKO"
    question = "what is a 1-bit LLM?"
    # test_rag(question, kb_id=kb_id)
    qa = get_qa_chain(kb_id=kb_id)

    print(qa)
