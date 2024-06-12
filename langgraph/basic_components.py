import operator
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage

# from langchain_mistralai import ChatMistralAI
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI
from loguru import logger

from langgraph.graph import END, StateGraph

tavily_api_key = os.getenv("TAVILY_API_KEY")


def get_prompt() -> str:
    return (
        "You are a smart research assistant. "
        "Use the search engine to look up information. "
        "You are allowed to make multiple calls "
        "(either together or in sequence). "
        "Only look up information when you are sure of what you want. "
        "If you need to look up some information before asking "
        "a follow up question, you are allowed to do that!"
    )


def get_mistral_llm(
    model_name: str = "mistral-large-latest",
    # model_name: str = "mixtral-8x7b-32768",
    # model_name: str = "llama3-70b-8192",
    temp: float = 0.0,
):
    """Get the LLM."""
    return ChatMistralAI()


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class Agent:

    def __init__(self, model, tools, system="") -> None:
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm", self.exists_action, {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()
        self.tools = {t.name for t in tools}
        self.model = model.bind_tools(tools)
        # self._graph = None

    @property
    def grapha(self):
        if self._graph is None:
            graph = StateGraph(AgentState)
            graph.add_node("llm", self.call_openai)
            graph.add_node("action", self.take_action)
            graph.add_conditional_edges(
                "llm", self.exists_action, {True: "action", False: END}
            )
            graph.add_edge("action", "llm")
            graph.set_entry_point("llm")
            self._graph = graph.compile()

        return self._graph

    def exists_action(self, state: AgentState) -> bool:
        result = state["messages"][-1]
        logger.debug(f"\n In exists_action function, {result=}\n")
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState) -> dict:
        messages = state["messages"]
        logger.debug(f"In call_openai function, {messages=}")
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)

        logger.debug(f"Returning from call_openai function, {message=}")
        return {"messages": [message]}

    def take_action_orig(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t["name"] in self.tools:  # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t["name"]].invoke(t["args"])
            results.append(
                ToolMessage(tool_call_id=t["id"], name=t["name"], content=str(result))
            )
        print("Back to the model!")
        return {"messages": results}

    def take_action(self, state: AgentState) -> dict:
        logger.debug(f"In take_action function, {state=}")
        tool_calls = state["messages"][-1].tool_calls
        results = []

        for t in tool_calls:
            logger.debug(f"Calling {t}...")
            if not t["name"] in self.tools:
                logger.debug(f"Tool {t} not in tools")
                result = "bad tool name, retry"
            else:
                result = self.tools[t["name"]].invoke(t["args"])

            results.append(
                ToolMessage(tool_call_id=t["id"], name=t["name"], content=str(result))
            )

        print("Back to the model")

        return {"messages": results}


if __name__ == "__main__":
    load_dotenv()

    prompt = get_prompt()
    # model = get_mistral_llm()
    # model = ChatMistralAI(model="mistral-large-latest")
    model = ChatOpenAI(model="gpt-3.5-turbo")
    tool = TavilySearchResults(max_results=4)
    logger.info(type(tool))
    logger.info(tool.name)

    mybot = Agent(model=model, tools=[tool], system=prompt)
    print(mybot.graph.get_graph().draw_ascii())
    question = "What is the current temperature in Chanhassen, MN?"
    result = mybot.graph.invoke({"messages": [HumanMessage(content=question)]})

    logger.info(result)
