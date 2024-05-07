from textwrap import dedent

from crewai import Task


class StudyTasks:
    def excal_document_study_task(self, agent):
        return Task(
            description=dedent(
                """\
                Study the document provided to understand the structure and components
                of an Excalidraw diagram."""
            ),
            expected_output=dedent(
                """\
                A detailed analysis of the essential elements the every Excalidraw diagram
                must contain and how they are structured."""
            ),
            agent=agent,
            async_execution=True,
        )

    def langgraph_document_study_task(self, agent):
        return Task(
            description=dedent(
                """\
                Study the LangGraph documentation to understand the structure of a graph
                and how different components like nodes and edges can be accessed from a graph."""
            ),
            expected_output=dedent(
                """\
                A comprehensive understanding of the LangGraph graph structure and how it
                can be converted to a JSON document."""
            ),
            agent=agent,
            async_execution=True,
        )