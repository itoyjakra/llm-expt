from asyncio import gather

from agents import (
    ActivitiesGuide,
    CityExpert,
    LocalExpert,
    NationalParkExpert,
    WeatherExpert,
)
from dotenv import load_dotenv
from tasks import GatherInfo, Plan
from utils.llms import LLMConfig

from crewai import Crew


class ConciergeCrew:

    def __init__(self, places, date_range, interests, arrival, departure, llm_model):
        self.places = places
        self.interests = interests
        self.date_range = date_range
        self.arrival = arrival
        self.departure = departure
        self.llm_model = llm_model

    def run(self):

        plan = Plan()
        gather_info = GatherInfo()

        crew = Crew(
            agents=[
                LocalExpert(),
                CityExpert(),
                ActivitiesGuide(),
                NationalParkExpert(),
                WeatherExpert(),
            ],
            tasks=[gather_info, plan],
            verbose=True,
        )

        return crew.kickoff()


if __name__ == "__main__":
    load_dotenv()
    llm_config = LLMConfig(platform="openai", model="gpt-4o", temperature=0.7)
    llm_model = llm_config.get_llm_model()

    act_gui = ActivitiesGuide(llm=llm_model)
    print(act_gui.role)
    print("=====================")
    print(act_gui.goal)
    print("=====================")
    print(act_gui.backstory)
    print("=====================")
