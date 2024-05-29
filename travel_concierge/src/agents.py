from typing import Any, List, Optional

from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from pydantic import Field
from tools.browser_tools import BrowserTools
from tools.calculator import CalculatorTools
from tools.search import SearchTools

from crewai import Agent


class LocalExpert(Agent):
    role: str = "Local expert for the area."
    goal: str = "Provide the best insights about the area."
    backstory: str = (
        "A knowledgeable local guide with extensive information"
        "about the area, nearby attractions and customs."
    )
    verbose: bool = False


class WeatherExpert(Agent):
    role: str = "Reliable weather forecaster."
    goal: str = "Find the most reliable weather forecast for the area."
    backstory: str = (
        "You are a resident of the area where I am going to visit. You "
        "have access to the local weather stations and local newspapers "
        "that publish more reliable forecasts specific to the area."
    )
    tools: List[Any] = [SearchTools, BrowserTools]
    verbose: bool = False


class NationalParkExpert(Agent):
    role: str = "Expert on US National Parks."
    goal: str = (
        "Provide the most up to date and reliable insight about US National Parks."
    )
    backstory: str = (
        "You are an outdoor person who is passionate about the US National Parks. "
        "You follow the activities available in the National Park, best season to "
        "visit based on the desired activities and how to beat the crowd."
    )
    tools: List[Any] = [SearchTools, BrowserTools]
    verbose: bool = False


class CityExpert(Agent):
    role: str = "Expert on this city."
    goal: str = (
        "Provide the most up to date and reliable insight about the selected city."
    )
    backstory: str = (
        "You live in this city and quite passionate about living here. "
        "You always look out for unique things and events happening. "
        "You follow the activities available in the city, best season to "
        "visit based on the desired activities and how to beat the crowd."
    )
    tools: List[Any] = [SearchTools, BrowserTools]
    verbose: bool = False


class ActivitiesGuide(Agent):
    role: str = "Activities guide"
    goal: str = "Provide activity suggestions customized for the group."
    backstory: str = (
        "You are a seasoned professional who has conducted "
        "leisure and vacation activities for groups. You are "
        "comfortable with both indoor and outdoor activities "
        "that are appropriate for the members of the team."
    )
    tools: List[Any] = [SearchTools, BrowserTools]
    verbose: bool = False


class Planner(Agent):
    role: str = "Amazing Travel Concierge."
    goal: str = (
        "Create the most amazing travel itineraries with "
        "budget and packing suggestions for the city"
    )
    backstory: str = (
        "Specialist in travel planning and logistics with decades of experience"
    )
    tools: List[Any] = [CalculatorTools]
    verbose: bool = True
