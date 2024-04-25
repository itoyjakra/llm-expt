"""Class definition of GraphState"""

from typing import List

from typing_extensions import TypedDict


class GraphState(TypedDict):
    """Represents the state of the grpah."""

    question: str
    generation: str
    web_search: str
    documents: List[str]
