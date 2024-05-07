from textwrap import dedent

from crewai import Agent
from crewai_tools import FileReadTool
from tools import ExaSearchTool

file_read_tool = FileReadTool(file_path='path/to/your/file.txt')

class DrawingAgents:
    """An agent to create Excalidraw diagrams."""
    def excalidraw_agent(self):
        return Agent(
            role="Software Development Engineer agent for Excalidraw",
            goal="Create Excalidraw diagrams",
            tools=[ExaSearchTool.tools(),file_read_tool],
            backstory=dedent(
                """\
                    As an expert on Excalidraw, your mission is to create an .excalidraw file
                    from a JSON document containing information about its nodes and edges."""
            ),
            verbose=True,
        )

    def json_agent(self):
        return Agent(
            role="Software Development Engineer agent for Lagchain",
            goal="Given a Langgraph graph, convert it to JSON",
            tools=ExaSearchTool.tools(),
            backstory=dedent(
                """\
                    As a Software Development Engineer, your mission is to study the langgraph
                    documentation and understand how to extract the elements of a graph like the
                    nodes and edges. Then, you will convert the graph to a JSON document."""
            ),
            verbose=True,
        )