from pydantic import BaseModel, Field


class UserInputs(BaseModel):
    start_datetime: str = Field(default="2023-04-01T12:00:00")
    end_datetime: str = Field(default="2023-04-01T12:00:00")
    start_location: str = Field(min_length=3)
    end_location: str = Field(min_length=3)
    cities_of_interest: list[str] = Field(min_items=1)
    places_of_interest: list[str] = Field(min_items=1)
