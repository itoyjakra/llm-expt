"""definition of the GradeDocuments class"""

from langchain_core.pydantic_v1 import BaseModel, Field


class GradeDocuments(BaseModel):
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )
