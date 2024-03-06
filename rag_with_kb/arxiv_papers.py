import boto3
from langchain.chains import RetrievalQA
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate
from langchain.retrievers.bedrock import AmazonKnowledgeBasesRetriever

bedrock_agent_client = boto3.client("bedrock-agent-runtime")
bedrock_client = boto3.client("bedrock-runtime")


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
    Human: You are an AI system working on medical trial research, and provides answers to questions \
    by using fact based and statistical information when possible.
    Use the following pieces of information to provide a concise answer to the question.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    Question: {question} 
    Context: {context} 

    The response should be specific and use statistics or numbers when possible.

    Assistant:"""


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


def qa_with_langchain(question: str, kb_id: str) -> None:
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

    print(qa(question)["result"])


if __name__ == "__main__":
    kb_id = "QM8AGLZRKO"
    qq = "what is a 1-bit LLM?"
    qq = "what are some of the advantages of 1-bit LLM?"
    qq = "Does 1-bit LLM work with MoE?"
    qq = "what is a 1-bit LLM?"

    qa_simple(question=qq, kb_id=kb_id)
    qa_with_langchain(question=qq, kb_id=kb_id)
