from pydantic import Field

from crewai import Task


class GatherInfo(Task):

    description: str = (
        "As a local expert on this area you must compile an "
        "in-depth guide for someone traveling there and wanting "
        "to have THE BEST trip ever!"
        "Gather information about  key attractions, local customs,"
        "special events, and daily activity recommendations."
        "Find the best spots to go to, the kind of place only a"
        "local would know."
        "This guide should provide a thorough overview of what "
        "the area has to offer, including hidden gems, cultural"
        "hotspots, must-visit landmarks, weather forecasts, and"
        "high level costs."
    )
    expected_output: str = (
        "A comprehensive area guide, "
        "rich in cultural insights and practical tips, "
        "tailored to enhance the travel experience."
    )


class Plan(Task):

    description: str = (
        "Expand this guide into a full travel "
        "itinerary with detailed per-day plans, including "
        "weather forecasts, places to eat, packing suggestions, "
        "and a rough budget breakdown. "
        "You MUST suggest actual places to visit and the  "
        "associated activities and actual places to eat. "
    )
    expected_output: str = (
        "A complete expanded travel plan, "
        "formatted as markdown, encompassing a daily schedule, "
        "anticipated weather conditions, recommended clothing and "
        "items to pack, and a detailed budget, ensuring THE BEST "
        "TRIP EVER, Be specific and give it a reason why you picked "
        "up each place, what make them special! Add distances "
        "time estimates, origin and destination for each driving "
        "segment and make sure you have enough time to cover the itinerary."
    )


class GetWeatherInfo(Task):
    description: str = (
        "Provide a detailed weather forecast for the area "
        "during the days of the trip."
    )
    expected_output: str = (
        "A detailed weather forecast, "
        "including the date, temperature, precipitation, "
        "and other relevant information."
    )


class GetActivities(Task):
    description: str = "Provide a list of activities to do during the trip."
    expected_output: str = (
        "A list of activities to do during the trip, "
        "including the name, type, and duration."
    )


class GetActivitiesOutdoors(Task):
    description: str = "Provide a list of outdoors activities to do during the trip."
    expected_output: str = (
        "A list of activities to do during the trip, "
        "including the name, type, duration, required "
        "fitness level, considering the weather during the activity."
        "Hiking in the National and State parks is a preferred activity."
    )
