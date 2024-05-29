from asyncio import gather

from agents import (
    ActivitiesGuide,
    CityExpert,
    LocalExpert,
    NationalParkExpert,
    Planner,
    WeatherExpert,
)
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from dotenv import load_dotenv
from inputs import UserInputs
from tasks import GatherInfo, GetActivities, GetActivitiesOutdoors, GetWeatherInfo, Plan
from tools import calculator
from tools.calculator import CalculatorTools
from utils.llms import LLMConfig

from crewai import Crew


class ConciergeCrew:

    def __init__(self, inputs: UserInputs, llm_model):
        self.cities = inputs.cities_of_interest
        self.places = inputs.places_of_interest
        self.date_start = inputs.start_datetime
        self.date_end = inputs.end_datetime
        self.arrival = inputs.start_location
        self.departure = inputs.end_location
        self.llm_model = llm_model

    @property
    def date_range(self) -> str:
        return f"{self.date_start} to {self.date_end}"

    @property
    def input_config(self):
        return {
            "date_range": self.date_range,
            "arrival": self.arrival,
            "departure": self.departure,
            "cities": self.cities,
            "places": self.places,
        }

    @property
    def input_story(self):
        return (
            "We are a family of three going onto a trip from "
            f"during {self.date_range}. We shall start the trip "
            f"from {self.arrival} and end the trip at {self.departure}. "
            f"We shall stay at {self.cities} during this time and "
            f"visit {self.places}."
        )

    def run(self):

        search_tool = SerperDevTool()
        scrape_tool = ScrapeWebsiteTool()
        calculator_tool = CalculatorTools.calculate

        # agents
        local_expert = LocalExpert(llm=self.llm_model, tools=[scrape_tool, search_tool])
        planner = Planner(
            llm=self.llm_model, tools=[scrape_tool, search_tool, calculator_tool]
        )
        weather_expert = WeatherExpert(
            llm=self.llm_model, tools=[search_tool, scrape_tool]
        )

        np_expert = NationalParkExpert(
            llm=self.llm_model, tools=[search_tool, scrape_tool]
        )

        city_expert = CityExpert(llm=self.llm_model, tools=[search_tool, scrape_tool])

        # -------- tasks -----------

        # Weather Information
        weather_info = GetWeatherInfo(agent=weather_expert, async_execution=True)
        weather_info.description += (
            f"Focus on {self.cities} and {self.places} "
            f"during {self.date_range} when gathering your info."
        )

        # NP Activities Information
        np_activity_info = GetActivitiesOutdoors(
            agent=np_expert, context=[weather_info], async_execution=True
        )
        np_activity_info.description += (
            f"Focus on {self.places} "
            f"during {self.date_range} when gathering your info."
        )

        # City Activities Information
        city_activity_info = GetActivities(
            agent=city_expert, context=[weather_info], async_execution=True
        )
        city_activity_info.description += (
            f"Focus on {self.cities} "
            f"during {self.date_range} when gathering your info."
        )

        gather_info = GatherInfo(
            agent=local_expert,
            context=[weather_info, np_activity_info, city_activity_info],
            human_input=True,
        )
        # gather_info.description += (
        #     f"Focus on {self.cities} and {self.places} when gathering your info."
        # )

        plan = Plan(config=self.input_config, context=[gather_info], agent=planner)

        crew = Crew(
            agents=[
                weather_expert,
                np_expert,
                city_expert,
                local_expert,
                planner,
            ],
            tasks=[
                weather_info,
                np_activity_info,
                city_activity_info,
                gather_info,
                plan,
            ],
            verbose=True,
        )

        return crew.kickoff(inputs={"story": self.input_story})


if __name__ == "__main__":
    load_dotenv()
    llm_config = LLMConfig(platform="openai", model="gpt-4o", temperature=0.7)
    llm_model = llm_config.get_llm_model()

    # capture the user inputs
    user_inputs = UserInputs(
        start_datetime="2024-05-30T21:00:00",
        start_location="PHX",
        end_datetime="2024-06-02T16:00:00",
        end_location="PHX",
        cities_of_interest=["Tucson, AZ"],
        places_of_interest=["Saguaro National Park"],
    )

    trip_crew = ConciergeCrew(user_inputs, llm_model=llm_model)
    result = trip_crew.run()
    print("=" * 20)
    print(result)
