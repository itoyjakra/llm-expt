from enum import Enum

"""definition of different graders"""

from typing import Literal

from langchain_core.pydantic_v1 import BaseModel, Field


class GradeDocuments(BaseModel):
    """
    Binary score for document relevance in the answer.
    """

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


class GradeHallucinations(BaseModel):
    """Binary score for hallucinations in the answer."""

    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )


class GradeAnswer(BaseModel):
    """Binary score to assess whether answer addressed the question."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )


class DataSource(str, Enum):
    VECTOR_STORE = "vectorstore"
    WEBSEARCH = "websearch"


class RouteQuery(BaseModel):
    """
    Route user query to the most relevant data source.
    """

    data_source: DataSource = Field(
        ...,
        description="Given a user question route the query to either web search or vector store.",
    )
