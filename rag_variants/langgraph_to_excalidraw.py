from pydoc import doc

import langgraph
from dotenv import load_dotenv

load_dotenv()

from crewai import Crew
from crewai_agents import DrawingAgents
from tasks import StudyTasks


def main():
    load_dotenv()

    print("## Welcome to the Crew that converts your LangGraph graph to Excalidraw!")
    print("-------------------------------")

    langgraph_document = input()
    participants = input(
        "What are the emails for the participants (other than you) in the meeting?\n"
    )
    context = input("What is the context of the meeting?\n")
    objective = input("What is your objective for this meeting?\n")

    # Available Agents
    agents = DrawingAgents()
    json_agent = agents.json_agent()
    excal_agent = agents.excalidraw_agent()

    # Create Tasks
    tasks = StudyTasks()
    study_lg = tasks.langgraph_document_study_task(json_agent)
    study_excal = tasks.excal_document_study_task(excal_agent)

    # Create contexts for the tasks
    study_lg.context = []
    study_excal.context = []

    # Create Crew
    crew = Crew(
        agents=[
            excal_agent,
            json_agent,
        ],
        tasks=[study_lg, study_excal],
    )

    play = crew.kickoff()

    # Print results
    print("\n\n################################################")
    print("## Here is the result")
    print("################################################\n")
    print(play)


if __name__ == "__main__":
    main()
