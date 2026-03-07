from pydantic import BaseModel, Field


class GetResponse(BaseModel):
    classes: list[str]
    rooms: list[str]


class HourModel(BaseModel):
    room: str
    class_: str = Field(alias="class")
    subject: str
    teacher: str | None


class ScheduleModel(BaseModel):
    monday: list[HourModel]
    tuesday: list[HourModel]
    wednesday: list[HourModel]
    thursday: list[HourModel]
    friday: list[HourModel]
