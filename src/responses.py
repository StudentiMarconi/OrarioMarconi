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
    monday: dict[int, HourModel]
    tuesday: dict[int, HourModel]
    wednesday: dict[int, HourModel]
    thursday: dict[int, HourModel]
    friday: dict[int, HourModel]
