"""Create a vector store for the RAG variants."""

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_mistralai import MistralAIEmbeddings

load_dotenv()


def get_doc_from_url(url: str):
    """Get document from a URL."""
    return WebBaseLoader(url).load()


def get_text_splitter(chunk_size: int = 250, chunk_overlap: int = 0):
    """Get a text splitter."""
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )


def create_vector_store_from_web_docs(urls: list[str], text_splitter):
    """Create a vector store from the documents."""
    docs = [get_doc_from_url(url) for url in urls]

    docs_list = [item for sublist in docs for item in sublist]
    doc_splits = text_splitter.split_documents(docs_list)

    vector_store = Chroma.from_documents(
        documents=doc_splits,
        collection_name="test-collection-mistral-embeddings",
        embedding=MistralAIEmbeddings(),
    )

    return vector_store


def get_retriever(vector_store):
    """Get a retriever from the vector store."""
    return vector_store.as_retriever()
