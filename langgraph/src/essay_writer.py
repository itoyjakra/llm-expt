import os
from typing import List, TypedDict
from unittest import result

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.pydantic_v1 import BaseModel
from prompt_dictionary import PromptDictionary
from tavily import TavilyClient

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


class Queries(BaseModel):
    queries: List[str]


class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revision_number: int


class EssayWriter:
    def __init__(self, llm_model):
        self.model = llm_model
        self._essay_writer = None
        self.memory = SqliteSaver.from_conn_string(":memory:")
        self.prompts = PromptDictionary()

    def planner(self, state: AgentState) -> dict:
        messages = [
            SystemMessage(content=self.prompts.planner),
            HumanMessage(content=state["task"]),
        ]
        response = self.model.invoke(messages)

        return {"plan": response.content}

    def researcher(self, state: AgentState) -> dict:
        queries = self.model.with_structured_output(Queries).invoke(
            [
                SystemMessage(content=self.prompts.researcher),
                HumanMessage(content=state["plan"]),
            ]
        )

        content = state["content"] or []
        for query in queries.queries:
            response = tavily.search(query=query, max_results=2)
            for result in response["results"]:
                content.append(result["content"])

        return {"content": content}

    def writer(self, state: AgentState) -> dict:
        pass

    def critique(self, state: AgentState) -> dict:
        pass

    def evaluator(self, state: AgentState) -> dict:
        pass

    @staticmethod
    def should_continue(state: AgentState) -> bool | str:
        if state["revision_number"] > state["max_revision_number"]:
            return END

        return "evaluate"

    @property
    def essay_writer(self):
        if self._essay_writer is None:
            self._essay_writer = self.build_graph()
        return self._essay_writer

    def build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("Plan", self.planner)
        graph.add_node("Research", self.researcher)
        graph.add_node("Write", self.writer)
        graph.add_node("Critique", self.critique)
        graph.add_node("Evaluate", self.evaluator)

        # Direct Edges
        graph.add_edge("Plan", "Research")
        graph.add_edge("Research", "Write")
        graph.add_edge("Evaluate", "Critique")
        graph.add_edge("Critique", "Write")

        # Conditional Edges
        graph.add_conditional_edges(
            "Write", self.should_continue, {END: END, "Evaluate": "Evaluate"}
        )

        graph.set_entry_point("Plan")

        compiled_graph = graph.compile(checkpointer=self.memory)

        return compiled_graph
